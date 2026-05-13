"""
收敛引擎 — 封装多模型发散+收敛的完整流程。

用法:
    from src.convergence import cross_validate

    result = cross_validate(
        question="如何设计诊断规则引擎的匹配算法？",
        roles={
            "primary":   "你是临床推理系统架构师，给出完整设计。",
            "critic":    "你是医学审查员，审查主方案的正确性和完整性。",
        },
    )
    print(result.final_decision)
    print(result.consensus)
    print(result.divergences)
"""

import json
import logging
from dataclasses import dataclass, field

from src.infrastructure.multi_llm import MultiLLM

logger = logging.getLogger(__name__)


@dataclass
class CrossValidateResult:
    """一次交叉验证的完整结果。"""

    question: str
    responses: dict[str, str] = field(default_factory=dict)
    consensus: list[str] = field(default_factory=list)
    divergences: list[dict] = field(default_factory=list)
    final_decision: str = ""
    risk_notes: list[str] = field(default_factory=list)
    raw_convergence: str = ""

    @property
    def all_agree(self) -> bool:
        """是否无分歧（所有专家完全一致）。"""
        return len(self.divergences) == 0


def cross_validate(
    question: str,
    roles: dict[str, str],
    engine: MultiLLM | None = None,
    config: dict | None = None,
) -> CrossValidateResult:
    """执行一次完整的交叉验证流程。

    流程：
        Phase 1 — 发散：同时向多个角色模型提问，收集各个回答
        Phase 2 — 收敛：将回答汇总，让收敛模型做出最终裁决

    Args:
        question: 需要决策的问题
        roles: {"角色名": "系统提示词", ...}
               例如 {"primary": "你是架构师", "critic": "你是审查员"}
        engine: 多模型引擎（None 则从 config 自动创建）
        config: 配置字典（仅当 engine 为 None 时使用，见 MultiLLM.from_config）

    Returns:
        CrossValidateResult: 包含共识、分歧、最终决策

    Raises:
        ValueError: roles 为空
        RuntimeError: 所有模型调用失败
    """
    if not roles:
        raise ValueError("roles 不能为空")

    if engine is None:
        engine = MultiLLM.from_config(config)

    result = CrossValidateResult(question=question)

    # Phase 1: 发散
    logger.info("Phase 1: 发散 — 同时询问 %d 个模型", len(roles))
    result.responses = engine.ask_all(
        system_prompts=roles,
        user_prompt=question,
    )

    # Phase 2: 收敛
    logger.info("Phase 2: 收敛 — 综合 %d 个回答", len(result.responses))
    try:
        role_labels = {role: prompt[:60] for role, prompt in roles.items()}
        converge_raw = engine.converge(question, result.responses, role_labels)
        result.raw_convergence = converge_raw

        # 尝试 JSON 解析；失败时保留原始文本
        converge_data = _try_parse_json(converge_raw)
        if converge_data:
            result.consensus = converge_data.get("consensus", [])
            result.divergences = converge_data.get("divergences", [])
            result.final_decision = converge_data.get("final_decision", "")
            result.risk_notes = converge_data.get("risk_notes", [])
        else:
            logger.warning("收敛结果 JSON 解析失败，使用原始文本作为 final_decision")
            result.final_decision = converge_raw

    except Exception as e:
        logger.error("收敛阶段失败: %s", e)
        result.final_decision = (
            "收敛失败，以下为原始模型回答：\n"
            + "\n---\n".join(
                f"## {role}\n{resp}"
                for role, resp in result.responses.items()
            )
        )

    return result


def _try_parse_json(text: str) -> dict | None:
    """安全尝试解析 JSON，支持去除可能的 markdown 代码块包装。"""
    # 去掉 ```json ... ``` 包装
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # 找到第一个换行后的内容，去掉末尾的 ```
        lines = cleaned.splitlines()
        start = 1 if lines and lines[0].startswith("```") else 0
        end = -1 if lines and lines[-1].strip() == "```" else len(lines)
        cleaned = "\n".join(lines[start:end]).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None