"""
规则匹配引擎 — 基于 M-rule 的确定性推理引擎。

依赖规则: 可依赖 infrastructure、knowledge_graph、retrieval。

M-rule 结构:
    rule = {
        "id": str,                    # 规则唯一 ID
        "category": str,              # diagnosis | treatment | referral
        "trigger": list[str],         # 触发实体节点名列表（AND 逻辑）
        "suggests": str,              # 建议的诊断/干预
        "mechanism_path": list[str],  # 推理路径节点名列表
        "confidence": float,          # 规则置信度 (0-1)
        "source": str,                # 证据来源
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class MRule:
    """M-rule 数据类。"""
    id: str
    category: str  # diagnosis | treatment | referral
    trigger: list[str]
    suggests: str
    mechanism_path: list[str] = field(default_factory=list)
    confidence: float = 0.5
    source: str = ""


class RuleEngine:
    """规则匹配引擎 — 输入实体列表，输出匹配的 M-rule 列表。"""

    def __init__(self, rules: Optional[list[MRule]] = None):
        """初始化引擎。

        Args:
            rules: 初始规则列表（可选，可通过 load_rules 追加）。
        """
        self._rules: list[MRule] = rules or []

    def load_rules(self, path: str | Path):
        """从 JSON 文件加载 M-rule 列表。

        Args:
            path: JSON 文件路径。格式: {"rules": [{rule}, ...]}
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("rules", []):
            self._rules.append(MRule(**item))

    def add_rule(self, rule: MRule):
        """添加单条规则。"""
        self._rules.append(rule)

    def match(self, entity_names: list[str]) -> list[tuple[MRule, float]]:
        """匹配规则 — 基于触发实体列表返回匹配的规则及匹配度。

        Args:
            entity_names: 已抽取的实体节点名列表。

        Returns:
            匹配的 (规则, 匹配度) 列表，按匹配度降序排列。
            匹配度 = 命中 trigger 数 / trigger 总数 ∈ [0, 1]。
        """
        entity_set = set(entity_names)
        scored: list[tuple[MRule, float]] = []

        for rule in self._rules:
            trigger_set = set(rule.trigger)
            if not trigger_set:
                continue
            hits = len(trigger_set & entity_set)
            if hits == 0:
                continue
            score = hits / len(trigger_set)
            scored.append((rule, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def match_by_category(
        self, entity_names: list[str], category: str
    ) -> list[tuple[MRule, float]]:
        """按类别过滤匹配结果。

        Args:
            entity_names: 实体节点名列表。
            category: 规则类别（diagnosis | treatment | referral）。

        Returns:
            匹配的 (规则, 匹配度) 列表。
        """
        all_matches = self.match(entity_names)
        return [(r, s) for r, s in all_matches if r.category == category]

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def export_rules(self, path: str | Path):
        """将当前规则导出为 JSON。"""
        data = {"rules": [asdict(r) for r in self._rules]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)