"""
知识图谱 CRUD 封装 — 节点、边、别名、诊断规则、分度指标的增删改查。

依赖规则: 可依赖 infrastructure（database.py），不可依赖 extraction/retrieval/generation。
"""

import json
from typing import Optional

from src.infrastructure.database import Database
from src.knowledge_graph.models import (
    EntityNode, Relation, Alias, TermMapping,
    DiagnosticRule, GradingIndicator, GradingThreshold,
)


class KnowledgeGraphRepository:
    """知识图谱数据访问层。"""

    def __init__(self, db: Database):
        self.db = db

    # ════════════════════════════════════════════
    # 节点操作
    # ════════════════════════════════════════════

    def create_node(self, node: EntityNode) -> int:
        """插入新节点，返回自增 ID。"""
        cursor = self.db.execute(
            """INSERT INTO nodes (name, layer, type, subtype, description, is_core)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (node.name, node.layer, node.type, node.subtype, node.description, int(node.is_core)),
        )
        return cursor.lastrowid

    def upsert_node(self, node: EntityNode) -> int:
        """插入或更新节点（按 name 去重），返回节点 ID。"""
        existing = self.get_node_by_name(node.name)
        if existing:
            self.db.execute(
                """UPDATE nodes SET layer=?, type=?, subtype=?, description=?, is_core=?,
                   updated_at=datetime('now') WHERE id=?""",
                (node.layer, node.type, node.subtype, node.description, int(node.is_core), existing.id),
            )
            return existing.id
        return self.create_node(node)

    def get_node_by_id(self, node_id: int) -> Optional[EntityNode]:
        """按 ID 查询节点。"""
        row = self.db.fetchone("SELECT * FROM nodes WHERE id = ?", (node_id,))
        return self._row_to_node(row) if row else None

    def get_node_by_name(self, name: str) -> Optional[EntityNode]:
        """按名称查询节点。"""
        row = self.db.fetchone("SELECT * FROM nodes WHERE name = ?", (name,))
        return self._row_to_node(row) if row else None

    def search_nodes(self, keyword: str, limit: int = 20) -> list[EntityNode]:
        """模糊搜索节点名称。"""
        rows = self.db.fetchall(
            "SELECT * FROM nodes WHERE name LIKE ? LIMIT ?",
            (f"%{keyword}%", limit),
        )
        return [self._row_to_node(r) for r in rows]

    def update_node(self, node: EntityNode) -> bool:
        """更新节点信息。"""
        if node.id is None:
            return False
        self.db.execute(
            """UPDATE nodes SET name=?, layer=?, type=?, subtype=?, description=?, is_core=?,
               updated_at=datetime('now') WHERE id=?""",
            (node.name, node.layer, node.type, node.subtype, node.description, int(node.is_core), node.id),
        )
        return True

    def delete_node(self, node_id: int) -> bool:
        """删除节点及其关联的边和别名。"""
        self.db.execute("DELETE FROM edges WHERE source_id=? OR target_id=?", (node_id, node_id))
        self.db.execute("DELETE FROM aliases WHERE node_id=?", (node_id,))
        self.db.execute("DELETE FROM nodes WHERE id=?", (node_id,))
        return True

    # ════════════════════════════════════════════
    # 边操作
    # ════════════════════════════════════════════

    def create_edge(self, edge: Relation) -> int:
        """插入新边，返回自增 ID。"""
        cursor = self.db.execute(
            """INSERT INTO edges (source_id, target_id, relation, confidence, source_ref, evidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (edge.source_id, edge.target_id, edge.relation, edge.confidence, edge.source_ref, edge.evidence),
        )
        return cursor.lastrowid

    def upsert_edge(self, edge: Relation) -> int:
        """插入或更新边（按 source_id+target_id+relation 去重），返回边 ID。"""
        existing = self.db.fetchone(
            "SELECT id FROM edges WHERE source_id=? AND target_id=? AND relation=?",
            (edge.source_id, edge.target_id, edge.relation),
        )
        if existing:
            self.db.execute(
                """UPDATE edges SET confidence=?, source_ref=?, evidence=?, created_at=datetime('now')
                   WHERE id=?""",
                (edge.confidence, edge.source_ref, edge.evidence, existing["id"]),
            )
            return existing["id"]
        return self.create_edge(edge)

    def get_edges_by_node(self, node_id: int, direction: str = "both") -> list[Relation]:
        """查询与某节点关联的边。

        Args:
            node_id: 节点 ID。
            direction: "outgoing" (出边), "incoming" (入边), "both" (双向)。
        """
        if direction == "outgoing":
            rows = self.db.fetchall("SELECT * FROM edges WHERE source_id=?", (node_id,))
        elif direction == "incoming":
            rows = self.db.fetchall("SELECT * FROM edges WHERE target_id=?", (node_id,))
        else:
            rows = self.db.fetchall(
                "SELECT * FROM edges WHERE source_id=? OR target_id=?", (node_id, node_id),
            )
        return [self._row_to_edge(r) for r in rows]

    def delete_edge(self, edge_id: int) -> bool:
        """删除边。"""
        self.db.execute("DELETE FROM edges WHERE id=?", (edge_id,))
        return True

    # ════════════════════════════════════════════
    # 别名操作
    # ════════════════════════════════════════════

    def create_alias(self, alias: Alias) -> int:
        """插入别名。"""
        cursor = self.db.execute(
            "INSERT INTO aliases (node_id, language, display_name, is_preferred) VALUES (?, ?, ?, ?)",
            (alias.node_id, alias.language, alias.display_name, int(alias.is_preferred)),
        )
        return cursor.lastrowid

    def get_aliases(self, node_id: int) -> list[Alias]:
        """查询某节点的所有别名。"""
        rows = self.db.fetchall("SELECT * FROM aliases WHERE node_id=?", (node_id,))
        return [self._row_to_alias(r) for r in rows]

    # ════════════════════════════════════════════
    # 诊断规则操作
    # ════════════════════════════════════════════

    def insert_diagnostic_rule(self, rule: DiagnosticRule) -> int:
        """插入诊断规则，返回自增 ID。"""
        cursor = self.db.execute(
            """INSERT INTO diagnostic_rules (pattern, suggests, mechanism_path, confidence, category)
               VALUES (?, ?, ?, ?, ?)""",
            (json.dumps(rule.pattern, ensure_ascii=False),
             rule.suggests,
             json.dumps(rule.mechanism_path, ensure_ascii=False),
             rule.confidence,
             rule.category),
        )
        return cursor.lastrowid

    def get_diagnostic_rules(self, suggests: Optional[str] = None,
                             category: Optional[str] = None) -> list[DiagnosticRule]:
        """查询诊断规则，可按建议诊断或类别过滤。"""
        conditions = []
        params = []
        if suggests:
            conditions.append("suggests = ?")
            params.append(suggests)
        if category:
            conditions.append("category = ?")
            params.append(category)
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self.db.fetchall(f"SELECT * FROM diagnostic_rules WHERE {where}", tuple(params))
        return [self._row_to_diagnostic_rule(r) for r in rows]

    # ════════════════════════════════════════════
    # 分度指标操作
    # ════════════════════════════════════════════

    def upsert_grading_indicator(self, indicator: GradingIndicator) -> int:
        """插入或更新分度指标（按 name 去重），返回 ID。"""
        existing = self.db.fetchone(
            "SELECT id FROM grading_indicators WHERE name=?", (indicator.name,)
        )
        if existing:
            indicator_id = existing["id"]
        else:
            cursor = self.db.execute(
                "INSERT INTO grading_indicators (name) VALUES (?)", (indicator.name,),
            )
            indicator_id = cursor.lastrowid

        # 同步阈值：先删后插
        self.db.execute("DELETE FROM grading_thresholds WHERE indicator_id=?", (indicator_id,))
        for t in indicator.thresholds:
            self.db.execute(
                "INSERT INTO grading_thresholds (indicator_id, level, range_desc, node_name) VALUES (?, ?, ?, ?)",
                (indicator_id, t.level, t.range_desc, t.node_name),
            )
        return indicator_id

    # ════════════════════════════════════════════
    # 术语映射操作
    # ════════════════════════════════════════════

    def upsert_term_mapping(self, mapping: TermMapping) -> int:
        """插入或更新术语映射（按 node_name+zh_term 去重），返回 ID。"""
        existing = self.db.fetchone(
            "SELECT id FROM term_mapping WHERE node_name=? AND zh_term=?",
            (mapping.node_name, mapping.zh_term),
        )
        if existing:
            self.db.execute(
                """UPDATE term_mapping SET layer=?, node_type=?, node_subtype=?, description=?
                   WHERE id=?""",
                (mapping.layer, mapping.node_type, mapping.node_subtype, mapping.description, existing["id"]),
            )
            return existing["id"]
        cursor = self.db.execute(
            """INSERT INTO term_mapping (node_name, zh_term, layer, node_type, node_subtype, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (mapping.node_name, mapping.zh_term, mapping.layer, mapping.node_type, mapping.node_subtype, mapping.description),
        )
        return cursor.lastrowid

    def get_term_mapping_by_zh(self, zh_term: str) -> Optional[TermMapping]:
        """按中文术语查询映射。"""
        row = self.db.fetchone("SELECT * FROM term_mapping WHERE zh_term=?", (zh_term,))
        return self._row_to_term_mapping(row) if row else None

    def get_term_mapping_by_node(self, node_name: str) -> list[TermMapping]:
        """按节点名查询所有中文术语。"""
        rows = self.db.fetchall("SELECT * FROM term_mapping WHERE node_name=?", (node_name,))
        return [self._row_to_term_mapping(r) for r in rows]

    def search_term_mapping(self, keyword: str, limit: int = 20) -> list[TermMapping]:
        """模糊搜索中文术语。"""
        rows = self.db.fetchall(
            "SELECT * FROM term_mapping WHERE zh_term LIKE ? OR node_name LIKE ? LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", limit),
        )
        return [self._row_to_term_mapping(r) for r in rows]

    # ════════════════════════════════════════════
    # 内部工具
    # ════════════════════════════════════════════

    @staticmethod
    def _row_to_node(row: dict) -> EntityNode:
        return EntityNode(
            id=row["id"],
            name=row["name"],
            layer=row["layer"],
            type=row["type"],
            subtype=row.get("subtype", ""),
            description=row["description"],
            is_core=bool(row["is_core"]),
        )

    @staticmethod
    def _row_to_edge(row: dict) -> Relation:
        return Relation(
            id=row["id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation=row["relation"],
            confidence=row["confidence"],
            source_ref=row["source_ref"],
            evidence=row["evidence"],
        )

    @staticmethod
    def _row_to_alias(row: dict) -> Alias:
        return Alias(
            id=row["id"],
            node_id=row["node_id"],
            language=row["language"],
            display_name=row["display_name"],
            is_preferred=bool(row["is_preferred"]),
        )

    @staticmethod
    def _row_to_diagnostic_rule(row: dict) -> DiagnosticRule:
        return DiagnosticRule(
            id=row["id"],
            pattern=json.loads(row["pattern"]) if isinstance(row["pattern"], str) else row["pattern"],
            suggests=row["suggests"],
            mechanism_path=json.loads(row["mechanism_path"]) if isinstance(row["mechanism_path"], str) else row["mechanism_path"],
            confidence=row["confidence"],
            category=row.get("category", "general"),
        )

    @staticmethod
    def _row_to_term_mapping(row: dict) -> TermMapping:
        return TermMapping(
            id=row["id"],
            node_name=row["node_name"],
            zh_term=row["zh_term"],
            layer=row["layer"],
            node_type=row.get("node_type", "generic"),
            node_subtype=row.get("node_subtype", ""),
            description=row.get("description", ""),
        )
