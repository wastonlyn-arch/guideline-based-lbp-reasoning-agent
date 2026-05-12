"""
置信度聚合器 — 将规则匹配度、规则置信度等合并为最终诊断/建议的置信度。

依赖规则: 可依赖 infrastructure、knowledge_graph、retrieval。

聚合策略:
    - max: 取所有匹配规则的最高置信度
    - weighted_sum: 按匹配度加权平均
    - product: 乘积归一化
"""

from __future__ import annotations

from typing import Optional

from src.reasoning.rule_engine import MRule


class ConfidenceAggregator:
    """置信度聚合器 — 多规则置信度融合。"""

    def __init__(self, strategy: str = "weighted_sum"):
        """初始化聚合器。

        Args:
            strategy: 聚合策略。可选: "max", "weighted_sum", "product"。

        Raises:
            ValueError: 当 strategy 不支持时。
        """
        if strategy not in ("max", "weighted_sum", "product"):
            raise ValueError(f"不支持的置信度聚合策略: {strategy}")
        self.strategy = strategy

    def aggregate(
        self,
        matched_rules: list[tuple[MRule, float]],
    ) -> tuple[float, str]:
        """聚合给定匹配规则的置信度。

        Args:
            matched_rules: 匹配的 (规则, 匹配度) 列表。

        Returns:
            (聚合置信度, 策略描述) 元组。
        """
        if not matched_rules:
            return (0.0, "无匹配规则")

        if self.strategy == "max":
            return self._max(matched_rules)
        elif self.strategy == "weighted_sum":
            return self._weighted_sum(matched_rules)
        elif self.strategy == "product":
            return self._product(matched_rules)

        return (0.0, "未知策略")

    def _max(self, matched_rules: list[tuple[MRule, float]]) -> tuple[float, str]:
        """取最高置信度。"""
        best = max(matched_rules, key=lambda x: x[0].confidence * x[1])
        rule, match_score = best
        combined = rule.confidence * match_score
        return (combined, f"max策略: 规则 {rule.id} (置信度={rule.confidence:.2f}, 匹配度={match_score:.2f})")

    def _weighted_sum(
        self, matched_rules: list[tuple[MRule, float]]
    ) -> tuple[float, str]:
        """按匹配度加权平均。"""
        total_weight = 0.0
        weighted_sum = 0.0
        for rule, match_score in matched_rules:
            w = match_score
            weighted_sum += rule.confidence * w
            total_weight += w

        if total_weight == 0:
            return (0.0, "加权求和: 总权重为 0")

        result = weighted_sum / total_weight
        return (result, f"加权平均策略: {len(matched_rules)} 条规则, 聚合置信度={result:.2f}")

    def _product(self, matched_rules: list[tuple[MRule, float]]) -> tuple[float, str]:
        """乘积归一化。"""
        product = 1.0
        for rule, match_score in matched_rules:
            product *= rule.confidence * match_score

        # 使用 n 次根归一化（n = 规则数）
        n = len(matched_rules)
        normalized = product ** (1.0 / n) if n > 0 else 0.0
        return (normalized, f"乘积归一化策略: {n} 条规则, 聚合置信度={normalized:.2f}")