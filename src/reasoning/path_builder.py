"""
可解释推理路径构建器 — 将匹配的 M-rule 转化为人类可读的推理路径。

依赖规则: 可依赖 infrastructure、knowledge_graph、retrieval。

推理路径结构:
    {
        "summary": str,                    # 路径摘要
        "steps": [ExecutionStep, ...],     # 执行步骤列表
        "sources": [str, ...],             # 证据来源列表
    }

    ExecutionStep:
        {
            "order": int,                  # 步骤序号
            "action": str,                 # 操作描述
            "detail": str,                 # 详细说明
            "source": str,                 # 这一步的来源
        }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.reasoning.rule_engine import MRule
from src.knowledge_graph.models import EntityNode


@dataclass
class ExecutionStep:
    """推理执行步骤。"""
    order: int
    action: str
    detail: str
    source: str = ""


@dataclass
class ReasoningPath:
    """完整推理路径。"""
    summary: str
    steps: list[ExecutionStep] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


class PathBuilder:
    """推理路径构建器 — 将实体 + 匹配规则组装为可解释的推理路径。"""

    def __init__(self):
        self._paths: list[ReasoningPath] = []

    def build_from_rule(
        self,
        rule: MRule,
        matched_entities: list[str],
        score: float,
    ) -> ReasoningPath:
        """从单条匹配规则构建推理路径。

        Args:
            rule: 匹配的 M-rule。
            matched_entities: 命中规则的实体名列表。
            score: 匹配度。

        Returns:
            结构化的推理路径。
        """
        steps: list[ExecutionStep] = []
        order = 1

        # Step 1: 实体匹配
        steps.append(ExecutionStep(
            order=order,
            action="实体匹配",
            detail=f"输入文本中识别到触发实体: {', '.join(matched_entities)}",
            source=rule.source,
        ))
        order += 1

        # Step 2: 规则激活
        steps.append(ExecutionStep(
            order=order,
            action="规则激活",
            detail=f"命中规则 [{rule.id}] ({rule.category}): {rule.suggests}",
            source=rule.source,
        ))
        order += 1

        # Step 3: 推理路径（如果有 mechanism_path）
        if rule.mechanism_path:
            path_str = " → ".join(rule.mechanism_path)
            steps.append(ExecutionStep(
                order=order,
                action="推理解释",
                detail=f"推理链路: {path_str}",
                source=rule.source,
            ))
            order += 1

        # Step 4: 置信度
        steps.append(ExecutionStep(
            order=order,
            action="置信度评估",
            detail=f"匹配度: {score:.2f}, 规则置信度: {rule.confidence:.2f}",
            source=rule.source,
        ))

        sources = [rule.source] if rule.source else []

        return ReasoningPath(
            summary=f"规则 [{rule.id}] 推断: {rule.suggests}",
            steps=steps,
            sources=sources,
        )

    def build_from_entities(
        self,
        entities: list[EntityNode],
        rules: list[tuple[MRule, float]],
    ) -> list[ReasoningPath]:
        """从实体列表和匹配规则列表批量构建推理路径。

        Args:
            entities: 抽取到的实体节点列表。
            rules: 匹配的 (规则, 匹配度) 列表。

        Returns:
            推理路径列表。
        """
        entity_names = [e.name for e in entities]
        paths: list[ReasoningPath] = []

        for rule, score in rules:
            matched = [e for e in entity_names if e in set(rule.trigger)]
            path = self.build_from_rule(rule, matched, score)
            paths.append(path)

        return paths

    def summarize(self, paths: list[ReasoningPath]) -> str:
        """将推理路径列表汇总为人类可读的文本摘要。

        Args:
            paths: 推理路径列表。

        Returns:
            文本摘要，适合放入 SOAP 的 Assessment 段。
        """
        lines = ["## 推理路径摘要", ""]
        for i, path in enumerate(paths, 1):
            lines.append(f"### 路径 {i}: {path.summary}")
            for step in path.steps:
                lines.append(f"  [{step.order}] {step.action}: {step.detail}")
            if path.sources:
                lines.append(f"  来源: {', '.join(path.sources)}")
            lines.append("")
        return "\n".join(lines)