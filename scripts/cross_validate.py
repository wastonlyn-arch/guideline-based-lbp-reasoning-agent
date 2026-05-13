#!/usr/bin/env python3
"""
多模型交叉验证 CLI 工具

在同一问题上并发调用 Claude（主方案）、Grok（审查/竞品方案），
然后用 DeepSeek 收敛裁决，输出 JSON 格式的验证报告。

用法:
    # 启用交叉验证（设置 API Key 后）
    export GPTS_API_KEY=sk-your-key
    export DEEPSEEK_API_KEY=your-deepseek-key

    # 交互模式
    python scripts/cross_validate.py

    # 直接提问
    python scripts/cross_validate.py --question "如何设计诊断规则引擎？"

    # 指定输出文件
    python scripts/cross_validate.py -q "..." -o report.json

    # 仅显示最终决策摘要
    python scripts/cross_validate.py -q "..." --summary

    # 添加第三个角色（更多异见）
    python scripts/cross_validate.py -q "..." --extra-role gemini "你是安全审查员"
"""

import argparse
import json
import logging
import sys
import os

# 确保能 import src (脚本从项目根目录执行)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.convergence import cross_validate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cross_validate")


def main():
    parser = argparse.ArgumentParser(
        description="多模型交叉验证 — 调用多个 LLM 对同一问题进行评审与收敛",
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default=None,
        help="待验证的问题（不提供则进入交互模式）",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出 JSON 报告文件路径",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="仅输出最终决策摘要（不打印完整 JSON）",
    )
    parser.add_argument(
        "--extra-role",
        nargs=2,
        metavar=("ROLE_NAME", "SYSTEM_PROMPT"),
        action="append",
        default=None,
        help="添加额外的验证角色（可多次使用）",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用 DEBUG 级别日志",
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # ── 获取问题 ──
    question = args.question
    if not question:
        print("=" * 60)
        print("  🧠 多模型交叉验证工具")
        print("=" * 60)
        print()
        question = input("请输入你的问题/待验证方案: ").strip()
        if not question:
            print("❌ 问题不能为空")
            sys.exit(1)

    # ── 配置角色 ──
    roles = {
        "primary": (
            "你是临床推理系统的资深架构师。"
            "你的任务是为当前问题给出完整、结构化的设计方案。"
            "要穷尽可能的技术路径，充分考虑可扩展性和维护性。"
        ),
        "critic": (
            "你是极具批判精神的技术审查员。"
            "你的任务是对主方案进行严格的审查，找出逻辑漏洞、边界情况、安全隐患和性能瓶颈。"
            "同时请给出一个与你审查思路不同的替代方案——哪怕你觉得主方案很好，也要故意提出一个"
            "不同角度的备选方案作为对比。"
        ),
    }

    # 额外角色
    if args.extra_role:
        for role_name, prompt in args.extra_role:
            roles[role_name] = prompt

    # ── 环境检查 ──
    gpts_key = os.environ.get("GPTS_API_KEY", "")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")

    if not gpts_key:
        logger.warning("未设置 GPTS_API_KEY，Claude / Grok 调用将失败")
    if not deepseek_key:
        logger.warning("未设置 DEEPSEEK_API_KEY，收敛阶段将失败")

    print(f"\n📋 问题: {question[:100]}{'...' if len(question) > 100 else ''}")
    print(f"👥 角色: {', '.join(roles.keys())}")
    print(f"⚡ 开始交叉验证（可能需要 10-30 秒）...\n")

    # ── 执行交叉验证 ──
    try:
        result = cross_validate(question=question, roles=roles)
    except Exception as e:
        logger.error("交叉验证失败: %s", e)
        sys.exit(1)

    # ── 输出 ──
    print("\n" + "=" * 60)
    print("  ✅ 交叉验证完成")
    print("=" * 60)

    if args.summary:
        _print_summary(result)
    else:
        _print_full(result)

    # ── 写入文件 ──
    if args.output:
        report = _build_report(result, question, list(roles.keys()))
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📁 报告已保存到: {args.output}")


def _print_summary(result):
    """仅输出决策摘要。"""
    print(f"\n📌 共识 ({len(result.consensus)} 条):")
    for i, point in enumerate(result.consensus, 1):
        print(f"   {i}. {point[:120]}{'...' if len(point) > 120 else ''}")

    if result.divergences:
        print(f"\n⚠️  分歧 ({len(result.divergences)} 处):")
        for d in result.divergences:
            topic = d.get("topic", "未知")
            print(f"   • {topic[:80]}")

    print(f"\n🏆 最终决策:")
    print(f"   {result.final_decision[:200]}{'...' if len(result.final_decision) > 200 else ''}")

    if result.risk_notes:
        print(f"\n⚠️  风险提示:")
        for note in result.risk_notes:
            print(f"   ⚡ {note[:100]}{'...' if len(note) > 100 else ''}")


def _print_full(result):
    """打印完整结果。"""
    print(f"\n📌 共识 ({len(result.consensus)} 条):")
    for i, point in enumerate(result.consensus, 1):
        print(f"\n   {i}. {point}")

    if result.divergences:
        print(f"\n⚠️  分歧 ({len(result.divergences)} 处):")
        for d in result.divergences:
            print(f"\n   ● 主题: {d.get('topic', '未知')}")
            print(f"     多数意见: {d.get('majority_view', '')}")
            print(f"     少数意见: {d.get('minority_view', '')}")
            print(f"     裁决: {d.get('resolution', '')}")

    print(f"\n🏆 最终决策:")
    print(f"   {result.final_decision}")

    if result.risk_notes:
        print(f"\n⚠️  风险提示:")
        for note in result.risk_notes:
            print(f"   ⚡ {note}")

    # 显示原始回答
    print(f"\n{'='*60}")
    print("  📜 各模型原始回答")
    print("=" * 60)
    for role, resp in result.responses.items():
        print(f"\n--- [{role}] ---")
        print(resp[:500])
        if len(resp) > 500:
            print("   ...（截断，查看完整报告请使用 -o 参数输出文件）")


def _build_report(result, question, role_names):
    """构建完整的 JSON 报告。"""
    return {
        "meta": {
            "question": question,
            "roles": role_names,
            "all_agree": result.all_agree,
            "consensus_count": len(result.consensus),
            "divergence_count": len(result.divergences),
        },
        "responses": result.responses,
        "consensus": result.consensus,
        "divergences": result.divergences,
        "final_decision": result.final_decision,
        "risk_notes": result.risk_notes,
        "raw_convergence": result.raw_convergence,
    }


if __name__ == "__main__":
    main()