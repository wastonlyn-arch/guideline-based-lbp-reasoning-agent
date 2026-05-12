#!/usr/bin/env python3
"""
迁移已有 JSON 知识图谱到 SQLite 数据库。

读取 D:\kg_system\medical\data\full_book.json，将 entities / edges /
diagnostic_rules / grading_indicators 写入 data/knowledge_base.db。

用法:
    python scripts/migrate_existing_kg.py [--json-path PATH]

依赖:
    - 项目根目录下的 src/ 模块
    - 需先 pip install -r deploy/requirements.txt
"""

import argparse
import json
import sys
import time
from pathlib import Path

# 将项目根目录加入 sys.path（兼容直接运行 scripts/ 下的脚本）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.infrastructure.database import Database
from src.knowledge_graph.models import (
    EntityNode, Relation, DiagnosticRule, GradingIndicator, GradingThreshold,
)
from src.knowledge_graph.repository import KnowledgeGraphRepository


def load_json(path: str) -> dict:
    """加载 JSON 文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def migrate_entities(repo: KnowledgeGraphRepository, entities: list[dict]) -> dict:
    """迁移实体节点，返回 {name: node_id} 映射。"""
    name_to_id = {}
    count = 0
    for ent in entities:
        node = EntityNode(
            name=ent["name"],
            layer=ent.get("layer", "L0"),
            type=ent.get("type", "generic"),
            subtype=ent.get("subtype", ""),
            description=ent.get("description", ""),
            is_core=False,
        )
        node_id = repo.upsert_node(node)
        name_to_id[node.name] = node_id
        count += 1
        if count % 500 == 0:
            print(f"  entities: {count}/{len(entities)}")
    print(f"  entities: {count}/{len(entities)} ✓")
    return name_to_id


def migrate_edges(repo: KnowledgeGraphRepository, edges: list[dict],
                  name_to_id: dict) -> int:
    """迁移关系边。"""
    count = 0
    missing_source = set()
    missing_target = set()
    for edge in edges:
        source_id = name_to_id.get(edge["source"])
        target_id = name_to_id.get(edge["target"])
        if source_id is None:
            missing_source.add(edge["source"])
            continue
        if target_id is None:
            missing_target.add(edge["target"])
            continue
        rel = Relation(
            source_id=source_id,
            target_id=target_id,
            relation=edge.get("relation", "related_to"),
            confidence=edge.get("confidence", 1.0),
            source_ref=edge.get("source_ref", ""),
            evidence=edge.get("evidence", ""),
        )
        repo.upsert_edge(rel)
        count += 1
        if count % 500 == 0:
            print(f"  edges: {count}/{len(edges)}")
    print(f"  edges: {count}/{len(edges)} ✓")
    if missing_source:
        print(f"  ⚠  {len(missing_source)} source nodes not found (e.g., {list(missing_source)[:3]})")
    if missing_target:
        print(f"  ⚠  {len(missing_target)} target nodes not found (e.g., {list(missing_target)[:3]})")
    return count


def migrate_diagnostic_rules(repo: KnowledgeGraphRepository,
                             rules: list[dict]) -> int:
    """迁移诊断规则。"""
    count = 0
    for rule in rules:
        d_rule = DiagnosticRule(
            pattern=rule.get("pattern", []),
            suggests=rule.get("suggests", ""),
            mechanism_path=rule.get("mechanism_path", []),
            confidence=rule.get("confidence", 0.5),
            category=rule.get("category", "general"),
        )
        repo.insert_diagnostic_rule(d_rule)
        count += 1
    print(f"  diagnostic_rules: {count} ✓")
    return count


def migrate_grading_indicators(repo: KnowledgeGraphRepository,
                               indicators: list[dict]) -> int:
    """迁移分度指标。"""
    count = 0
    for ind in indicators:
        thresholds = [
            GradingThreshold(
                level=t.get("level", ""),
                range_desc=t.get("range", ""),
                node_name=t.get("node", ""),
            )
            for t in ind.get("thresholds", [])
        ]
        indicator = GradingIndicator(
            name=ind["name"],
            thresholds=thresholds,
        )
        repo.upsert_grading_indicator(indicator)
        count += 1
    print(f"  grading_indicators: {count} ✓")
    return count


def main():
    parser = argparse.ArgumentParser(description="迁移 JSON 知识图谱到 SQLite")
    parser.add_argument(
        "--json-path",
        default=r"D:\kg_system\medical\data\full_book.json",
        help="输入 JSON 文件路径",
    )
    parser.add_argument(
        "--db-path",
        default="data/knowledge_base.db",
        help="输出 SQLite 数据库路径（相对于项目根目录）",
    )
    parser.add_argument(
        "--schema-path",
        default="src/knowledge_graph/schema.sql",
        help="schema.sql 路径（相对于项目根目录）",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"❌ JSON file not found: {json_path}")
        sys.exit(1)

    db_path = str(PROJECT_ROOT / args.db_path)
    schema_path = str(PROJECT_ROOT / args.schema_path)

    print(f"📦 Loading JSON: {json_path}")
    data = load_json(str(json_path))
    print(f"   entities: {len(data.get('entities', []))}")
    print(f"   edges: {len(data.get('edges', []))}")
    print(f"   diagnostic_rules: {len(data.get('diagnostic_rules', []))}")
    print(f"   grading_indicators: {len(data.get('grading_indicators', []))}")

    print(f"\n🗄️  Initializing database: {db_path}")
    db = Database(db_path)
    db.connect()
    db.init_schema(schema_path)

    repo = KnowledgeGraphRepository(db)

    # ── 开始事务 ──
    t0 = time.time()
    db.conn.execute("BEGIN TRANSACTION")

    try:
        print("\n🔹 Migrating entities...")
        name_to_id = migrate_entities(repo, data.get("entities", []))

        print("\n🔹 Migrating edges...")
        migrate_edges(repo, data.get("edges", []), name_to_id)

        print("\n🔹 Migrating diagnostic rules...")
        migrate_diagnostic_rules(repo, data.get("diagnostic_rules", []))

        print("\n🔹 Migrating grading indicators...")
        migrate_grading_indicators(repo, data.get("grading_indicators", []))

        db.conn.commit()
        elapsed = time.time() - t0
        print(f"\n✅ Migration complete in {elapsed:.1f}s")
        print(f"   Database: {db_path}")

    except Exception as e:
        db.conn.rollback()
        print(f"\n❌ Migration failed, rolled back: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()