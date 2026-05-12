#!/usr/bin/env python3
"""
列出 full_book.json 中因实体不存在而无法入库的边。

输出：每行一条缺失边，格式：
  编号 | 方向 | 关系 | 缺失实体 | 边信息

用法:
    python scripts/list_missing_edges.py [--json-path PATH]
"""

import argparse
import json
import sys
from pathlib import Path


def load_term_map(term_map_path: str | None) -> dict[str, str]:
    """加载术语映射文件（node_name → zh_term）。"""
    if not term_map_path:
        return {}
    path = Path(term_map_path)
    if not path.exists():
        print(f"  ⚠️ 术语映射文件不存在: {path}，跳过中文标注")
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {item["node_name"]: item["zh_term"] for item in data if "node_name" in item and "zh_term" in item}
    return {}


def main():
    parser = argparse.ArgumentParser(
        description="列出 JSON 中因实体缺失而无法入库的边，支持 term_map 中文对照"
    )
    parser.add_argument(
        "--json-path",
        default=r"D:\kg_system\medical\data\full_book.json",
        help="输入 JSON 文件路径",
    )
    parser.add_argument(
        "--term-map",
        default=r"scripts\term_map.json",
        help="术语映射 JSON 文件路径（可选，用于显示中文名称）",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"❌ JSON file not found: {json_path}")
        sys.exit(1)

    term_map = load_term_map(args.term_map)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    entities = {e["name"] for e in data.get("entities", [])}
    edges = data.get("edges", [])

    def fmt_node(name: str) -> str:
        """格式化节点名，附加中文术语（如果有）。"""
        zh = term_map.get(name)
        if zh:
            return f"{name} ({zh})"
        return name

    missing_source = []
    missing_target = []

    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        rel = edge.get("relation", "?")
        if src not in entities:
            missing_source.append((src, tgt, rel))
        if tgt not in entities:
            missing_target.append((src, tgt, rel))

    total_missing = len(missing_source) + len(missing_target)

    print("=" * 80)
    print("  无法入库的边诊断报告")
    print(f"  JSON 实体数: {len(entities)}    边总数: {len(edges)}")
    print(f"  缺失源节点: {len(missing_source)}    缺失目标节点: {len(missing_target)}")
    if term_map:
        print(f"  术语映射已加载: {len(term_map)} 条")
    print("=" * 80)

    if missing_source:
        print(f"\n{'─' * 80}")
        print(f"  一、源节点 (source) 缺失的边 (共 {len(missing_source)} 条)")
        print(f"{'─' * 80}")
        print(f"  {'#':>3s} | {'缺失的源节点':40s} | {'→ 目标节点':40s} | 关系")
        print(f"  {'─' * 3}─┼─{'─' * 40}─┼─{'─' * 40}─┼─{'─' * 10}")
        for i, (src, tgt, rel) in enumerate(missing_source, 1):
            print(f"  {i:>3d} | {fmt_node(src):40s} | {fmt_node(tgt):40s} | {rel}")

    if missing_target:
        print(f"\n{'─' * 80}")
        print(f"  二、目标节点 (target) 缺失的边 (共 {len(missing_target)} 条)")
        print(f"{'─' * 80}")
        print(f"  {'#':>3s} | {'源节点':40s} | {'缺失的目标节点':40s} | 关系")
        print(f"  {'─' * 3}─┼─{'─' * 40}─┼─{'─' * 40}─┼─{'─' * 10}")
        for i, (src, tgt, rel) in enumerate(missing_target, 1):
            print(f"  {i:>3d} | {fmt_node(src):40s} | {fmt_node(tgt):40s} | {rel}")

    # 汇总
    all_missing_nodes = sorted(
        set(s for s, _, _ in missing_source) | set(t for _, t, _ in missing_target)
    )
    print(f"\n{'─' * 80}")
    print(f"  三、缺失实体汇总 (共 {len(all_missing_nodes)} 个)")
    print(f"{'─' * 80}")
    for i, node in enumerate(all_missing_nodes, 1):
        print(f"  {i:>3d}. {fmt_node(node)}")

    print(f"\n{'=' * 80}")
    print(f"  结论：{total_missing} 条边无法入库（去重后 {len(missing_source)} 源缺失 + {len(missing_target)} 目标缺失）")
    print(f"  原因：这些实体存在于 edges 中，但不在 JSON 的 entities 列表里。")
    print(f"  处理：源数据问题，需补充 entities 列表或清理 edges。")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
