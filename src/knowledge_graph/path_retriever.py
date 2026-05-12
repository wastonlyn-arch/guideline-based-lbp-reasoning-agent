"""
递归 CTE 路径查询 — 知识图谱中的推理路径检索。

依赖规则: 可依赖 infrastructure（database.py）和 models.py，不可依赖更上层模块。
"""

from typing import Optional

from src.infrastructure.database import Database
from src.knowledge_graph.models import EntityNode, Relation, Path


class PathRetriever:
    """图谱路径检索器，使用递归 CTE 查询节点间路径。"""

    def __init__(self, db: Database):
        self.db = db

    def find_paths(
        self,
        source_name: str,
        target_name: str,
        max_depth: int = 5,
        limit: int = 10,
    ) -> list[Path]:
        """查找两个节点之间的所有推理路径。

        Args:
            source_name: 起始节点名称。
            target_name: 目标节点名称。
            max_depth: 最大递归深度。
            limit: 返回路径数量上限。

        Returns:
            Path 对象列表，每个 Path 包含路径上的节点和边。
        """
        # 先用名称查出 ID
        source = self.db.fetchone("SELECT id, name, layer, type FROM nodes WHERE name=?", (source_name,))
        target = self.db.fetchone("SELECT id, name, layer, type FROM nodes WHERE name=?", (target_name,))
        if not source or not target:
            return []

        sql = """
        WITH RECURSIVE path_cte AS (
            -- 初始：从源节点出发的所有出边
            SELECT
                e.id AS edge_id,
                e.source_id,
                e.target_id,
                e.relation,
                e.confidence,
                CAST(e.source_id AS TEXT) || ',' || CAST(e.target_id AS TEXT) AS node_chain,
                1 AS depth
            FROM edges e
            WHERE e.source_id = ?

            UNION ALL

            -- 递归：沿着出边继续
            SELECT
                e.id,
                e.source_id,
                e.target_id,
                e.relation,
                e.confidence,
                p.node_chain || ',' || CAST(e.target_id AS TEXT),
                p.depth + 1
            FROM edges e
            JOIN path_cte p ON e.source_id = p.target_id
            WHERE p.depth < ?
              AND instr(',' || p.node_chain || ',', ',' || CAST(e.target_id AS TEXT) || ',') = 0
        )
        SELECT edge_id, source_id, target_id, relation, confidence, node_chain, depth
        FROM path_cte
        WHERE target_id = ?
        ORDER BY depth, confidence DESC
        LIMIT ?
        """

        rows = self.db.fetchall(sql, (source["id"], max_depth, target["id"], limit))
        return [self._build_path(row) for row in rows]

    def find_paths_by_id(
        self,
        source_id: int,
        target_id: int,
        max_depth: int = 5,
        limit: int = 10,
    ) -> list[Path]:
        """按节点 ID 查找路径（跳过名称解析步骤）。"""
        sql = """
        WITH RECURSIVE path_cte AS (
            SELECT
                e.id AS edge_id,
                e.source_id,
                e.target_id,
                e.relation,
                e.confidence,
                CAST(e.source_id AS TEXT) || ',' || CAST(e.target_id AS TEXT) AS node_chain,
                1 AS depth
            FROM edges e
            WHERE e.source_id = ?

            UNION ALL

            SELECT
                e.id,
                e.source_id,
                e.target_id,
                e.relation,
                e.confidence,
                p.node_chain || ',' || CAST(e.target_id AS TEXT),
                p.depth + 1
            FROM edges e
            JOIN path_cte p ON e.source_id = p.target_id
            WHERE p.depth < ?
              AND instr(',' || p.node_chain || ',', ',' || CAST(e.target_id AS TEXT) || ',') = 0
        )
        SELECT edge_id, source_id, target_id, relation, confidence, node_chain, depth
        FROM path_cte
        WHERE target_id = ?
        ORDER BY depth, confidence DESC
        LIMIT ?
        """
        rows = self.db.fetchall(sql, (source_id, max_depth, target_id, limit))
        return [self._build_path(row) for row in rows]

    def _build_path(self, row: dict) -> Path:
        """从 CTE 结果行构建 Path 对象。"""
        # node_chain 格式: "id1,id2,...,idN"
        node_ids = [int(x) for x in row["node_chain"].split(",")]
        path = Path(total_score=row["confidence"])

        # 查询节点详情
        for nid in node_ids:
            node_row = self.db.fetchone(
                "SELECT id, name, layer, type, description, is_core FROM nodes WHERE id=?",
                (nid,),
            )
            if node_row:
                path.nodes.append(EntityNode(
                    id=node_row["id"],
                    name=node_row["name"],
                    layer=node_row["layer"],
                    type=node_row["type"],
                    description=node_row["description"],
                    is_core=bool(node_row["is_core"]),
                ))

        # 边信息
        path.edges.append(Relation(
            id=row["edge_id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation=row["relation"],
            confidence=row["confidence"],
        ))

        return path