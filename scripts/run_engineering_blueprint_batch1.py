"""
工程蓝图 Batch 1 — 三方讨论执行脚本

用法:
    cd d:/cline_control && python clinical_reasoning_agent/scripts/run_engineering_blueprint_batch1.py

此脚本:
  1. 读取 batch1/ 下三个 prompt 文件，提取 role 段的系统提示词
  2. 对每个维度分别执行 cross_validate() → MultiLLM 调用 primary + critic → convergence 仲裁
  3. 将结果写入 batch1/ 下对应的归档文件
"""

import json
import logging
import os
import sys
from pathlib import Path

# 确保 src 可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.convergence import cross_validate, CrossValidateResult
from src.infrastructure.multi_llm import MultiLLM

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = PROJECT_ROOT / "docs" / "conversations" / "engineering_blueprint" / "batch1"


def extract_role_prompts(prompt_file: str | Path) -> tuple[str, dict[str, str]]:
    """从 markdown prompt 文件中提取各角色的系统提示词。

    Args:
        prompt_file: 如 01_roadmap_prompt.md

    Returns:
        (维度名称, {"primary": "提示词", "critic": "提示词"})
    """
    text = Path(prompt_file).read_text(encoding="utf-8")

    # 提取维度名称（从文件开头的 Batch 1 · 维度 X — 名称）
    dimension = "unknown"
    for line in text.splitlines():
        if line.startswith("# Batch 1"):
            # 提取 > 核心问题：后面的内容
            for next_line in text.splitlines():
                if next_line.startswith("> 核心问题"):
                    dimension = next_line.replace("> 核心问题：", "").strip()
                    break
            break

    # 提取每个 Role: xxx 标题和 ``` 代码块
    roles = {}
    current_role = None
    in_code_block = False
    code_lines = []

    for line in text.splitlines():
        stripped = line.strip()

        # 检测 "## Role: xxx" 标题
        if stripped.startswith("## Role:"):
            if current_role and code_lines:
                roles[current_role] = "\n".join(code_lines).strip()
                code_lines = []
            current_role = stripped.replace("## Role:", "").strip().lower()
            in_code_block = False
            continue

        # 检测 "**model**" 行 — 跳过
        if stripped.startswith("**model**") or stripped.startswith("**temperature**") or stripped.startswith("**max_tokens**"):
            continue

        # 检测代码块
        if stripped == "```":
            if in_code_block:
                # 代码块结束
                if current_role:
                    roles[current_role] = "\n".join(code_lines).strip()
                    code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block and current_role:
            code_lines.append(line)

    # 最后一个角色
    if current_role and code_lines:
        roles[current_role] = "\n".join(code_lines).strip()

    return dimension, roles


def save_result(
    dimension_name: str,
    prompt_file: str,
    result: CrossValidateResult,
    suffix: str = "",
) -> str:
    """将讨论结果保存到归档文件。

    Returns:
        str: 保存的文件路径
    """
    file_label = Path(prompt_file).stem.replace("_prompt", "")
    out_path = BATCH_DIR / f"{file_label}_raw{suffix}.md"

    lines = []
    lines.append(f"# Batch 1 · {dimension_name} — 讨论原始记录\n")
    lines.append(f"> 生成时间: {__import__('datetime').datetime.now().isoformat()}\n")
    lines.append("---\n")

    # Phase 1: 发散结果
    lines.append("## Phase 1: 发散 — 各角色回答\n")
    for role, answer in result.responses.items():
        lines.append(f"### {role}\n")
        lines.append(f"```\n{answer}\n```\n")

    # Phase 2: 收敛结果
    lines.append("---\n")
    lines.append("## Phase 2: 收敛 — 仲裁结果\n")

    if result.consensus:
        lines.append("### 共识\n")
        for c in result.consensus:
            lines.append(f"- {c}\n")

    if result.divergences:
        lines.append("\n### 分歧\n")
        for d in result.divergences:
            lines.append(f"- **{d.get('topic', '')}**: "
                          f"多数={d.get('majority_view', '')[:100]}... | "
                          f"少数={d.get('minority_view', '')[:100]}...\n")

    lines.append(f"\n### 最终决策\n{result.final_decision}\n")

    if result.risk_notes:
        lines.append("\n### 风险提示\n")
        for r in result.risk_notes:
            lines.append(f"- {r}\n")

    lines.append("\n### 原始收敛 JSON\n")
    lines.append(f"```json\n{result.raw_convergence}\n```\n")

    out_path.write_text("".join(lines), encoding="utf-8")
    logger.info("归档写入: %s", out_path)
    return str(out_path)


def main():
    logger.info("=" * 60)
    logger.info("工程蓝图 Batch 1 — 开始三方讨论")
    logger.info("=" * 60)

    # 检查环境变量
    required_envs = ["GPTS_API_KEY", "DEEPSEEK_API_KEY"]
    missing = [e for e in required_envs if not os.environ.get(e)]
    if missing:
        logger.error("缺少环境变量: %s。请在 .env 中设置后运行", missing)
        sys.exit(1)

    # 查找 prompt 文件
    prompt_files = sorted(BATCH_DIR.glob("*_prompt.md"))
    if not prompt_files:
        logger.error("未找到 prompt 文件: %s/*_prompt.md", BATCH_DIR)
        sys.exit(1)

    # 运行每个维度
    for prompt_file in prompt_files:
        dimension_name, roles = extract_role_prompts(prompt_file)
        logger.info("\n--- 维度: %s ---", dimension_name)
        logger.info("从 %s 提取到角色: %s", prompt_file.name, list(roles.keys()))

        if "primary" not in roles or "critic" not in roles:
            logger.warning("缺少 primary 或 critic 角色，跳过: %s", prompt_file.name)
            continue

        # 只取 primary + critic 用于发散阶段；convergence 角色由内部收敛阶段处理
        role_prompts = {"primary": roles["primary"], "critic": roles["critic"]}
        if "convergence" in roles:
            logger.info("额外提取了 convergence 角色提示词（%d 字符），保留供收敛使用",
                         len(roles["convergence"]))

        # 构造 question（简单描述即可，角色 prompt 中已含完整上下文）
        question = f"请从架构师和审查员的角度，给出工程蓝图规划。"

        # 执行交叉验证
        logger.info("开始交叉验证: primary=%s, critic=%s",
                     role_prompts["primary"][:40] + "...",
                     role_prompts["critic"][:40] + "...")
        try:
            # 创建配置（指定正确路径，避免 CWD 问题）
            from src.infrastructure.config import Config
            cfg = Config(config_path=str(PROJECT_ROOT / "config.yaml"))
            result = cross_validate(
                question=question,
                roles=role_prompts,
                engine=None,
                config=cfg.multi_model_config(),
            )
            logger.info("交叉验证完成。共识点数=%d, 分歧点数=%d, 风险数=%d",
                         len(result.consensus),
                         len(result.divergences),
                         len(result.risk_notes))

            # 归档
            save_result(dimension_name, prompt_file, result)

        except Exception as e:
            logger.error("维度 [%s] 执行失败: %s", dimension_name, e, exc_info=True)
            continue

    # 生成收敛摘要
    logger.info("\n" + "=" * 60)
    logger.info("Batch 1 全部完成！")
    logger.info("结果已写入: %s/", BATCH_DIR)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()