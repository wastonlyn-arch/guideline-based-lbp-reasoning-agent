#!/usr/bin/env python3
"""验证迁移后的数据库内容。"""

import sqlite3
import sys
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.db"
print(f"Verifying database: {db_path}")

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

print(f"\n{'Table':25s} {'Rows':>8s}")
print("-" * 35)
for r in rows:
    name = r["name"]
    count = conn.execute(f"SELECT COUNT(*) as cnt FROM [{name}]").fetchone()["cnt"]
    print(f"  {name:25s} {count:>8d}")

# 额外验证
print("\n--- Spot checks ---")

# 检查几个已知节点
for sample in ["Spinal_Hinge", "Back_Pain", "Stabilization_Exercises"]:
    row = conn.execute(
        "SELECT name, layer, type, subtype FROM nodes WHERE name=?", (sample,)
    ).fetchone()
    status = f"✓ layer={row['layer']} type={row['type']}" if row else "✗ NOT FOUND"
    print(f"  {sample:30s} {status}")

# 检查边的数量
edge_count = conn.execute("SELECT COUNT(*) as cnt FROM edges").fetchone()["cnt"]
diag_count = conn.execute(
    "SELECT COUNT(*) as cnt FROM diagnostic_rules"
).fetchone()["cnt"]
print(f"\n  Edges: {edge_count}")
print(f"  Diagnostic rules: {diag_count}")

# 检查一个诊断规则
rule = conn.execute(
    "SELECT pattern, suggests, mechanism_path FROM diagnostic_rules LIMIT 1"
).fetchone()
print(f"\n  Sample rule -> suggests: {rule['suggests']}")
print(f"    pattern: {rule['pattern']}")
print(f"    mechanism_path: {rule['mechanism_path']}")

conn.close()
print("\n✅ Verification complete")