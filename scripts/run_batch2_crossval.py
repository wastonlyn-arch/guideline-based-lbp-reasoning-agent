"""
Batch 2 交叉验证执行脚本 — 对 3 个维度执行 cross_validate。
用法: cd clinical_reasoning_agent && python scripts/run_batch2_crossval.py
"""

import sys, os, json, re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 加载 .env 文件
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for _line in open(_env_path, encoding="utf-8"):
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _key, _val = _line.split("=", 1)
        os.environ.setdefault(_key.strip(), _val.strip())
    print(f"✅ 已加载环境变量: {_env_path}")

from src.convergence import cross_validate

BASE = Path("docs/conversations/engineering_blueprint/batch2")
OUT  = BASE


def parse_prompt(path: str):
    """从 prompt 文件中提取 question 和 roles (primary, critic)。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    parts = text.split("## Role:")

    # core question: first section before ## Role:
    question_lines = []
    for line in parts[0].split("\n"):
        stripped = line.strip().lstrip("#").strip()
        if stripped.startswith("核心问题"):
            # remove leading "核心问题：" or "核心问题"
            q = stripped.replace("核心问题：", "").replace("核心问题", "").strip()
            question_lines.append(q)

    question = " ".join(question_lines) if question_lines else parts[0].strip()
    if len(question) > 300:
        question = question[:300] + "..."

    roles = {}
    for block in parts[1:]:
        lines = block.strip().split("\n", 1)
        if len(lines) < 2:
            continue
        first_line = lines[0].strip()
        role_name = first_line.split()[0] if first_line else ""
        prompt = lines[1].strip()
        if role_name in ("primary", "critic"):
            roles[role_name] = prompt

    return question, roles


def save_responses(dim_id: str, result, model_meta: str):
    """保存发散阶段原始回答。"""
    ts = datetime.now().isoformat()
    lines = [
        f"# Batch 2 · {dim_id} — 讨论原始记录",
        f"> 生成时间: {ts}",
        f"> 模型: {model_meta}",
        "---",
        "## Phase 1: 发散 — 各角色回答",
    ]
    for role, answer in result.responses.items():
        lines.append(f"### {role}")
        lines.append(answer)
        lines.append("")

    lines.append("---")
    lines.append("## Phase 2: 收敛 — final_decision")
    lines.append(result.final_decision)
    lines.append("")
    lines.append("### consensus")
    lines.append(
        "\n".join(f"- {c}" for c in result.consensus)
        if result.consensus
        else "- (none)"
    )
    lines.append("")
    lines.append("### divergences")
    if result.divergences:
        for d in result.divergences:
            lines.append(
                f"- {d.get('topic', '?')}: majority={d.get('majority_view', '?')[:60]}"
                f" / minority={d.get('minority_view', '?')[:60]}"
                f" → {d.get('resolution', '?')[:80]}"
            )
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("### risk_notes")
    lines.append(
        "\n".join(f"- {r}" for r in result.risk_notes)
        if result.risk_notes
        else "- (none)"
    )

    out_path = OUT / f"{dim_id}_raw.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✅ 已写入 {out_path}")


def main():
    dimensions = {
        "04_test": "测试策略",
        "05_perf": "性能基线 & 可扩展性",
        "06_risk": "风险矩阵",
    }

    for dim_id, dim_label in dimensions.items():
        print(f"\n{'='*60}")
        print(f"维度: {dim_id} — {dim_label}")
        print(f"{'='*60}")

        prompt_path = BASE / f"{dim_id}_prompt.md"
        if not prompt_path.exists():
            print(f"  ❌ prompt 文件不存在: {prompt_path}")
            continue

        question, roles = parse_prompt(str(prompt_path))
        print(f"  📋 question: {question[:80]}...")
        print(f"  👥 roles: {list(roles.keys())}")

        result = cross_validate(question=question, roles=roles)
        print(f"  ✅ 完成")
        print(f"  📊 共识: {len(result.consensus)} 条")
        print(f"  🔀 分歧: {len(result.divergences)} 条")
        print(f"  ⚠️  风险: {len(result.risk_notes)} 条")

        model_meta = "primary=gemini-2.5-flash, critic=gpt-4.1-mini, convergence=deepseek-v4-flash"
        save_responses(dim_id, result, model_meta)

    print(f"\n{'='*60}")
    print("Batch 2 全部完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()