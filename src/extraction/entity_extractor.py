"""
实体抽取器 — 基于规则/词典的医学实体识别。

依赖规则: 可依赖 infrastructure 和 knowledge_graph，不可依赖 retrieval 或 generation。

用法:
    extractor = EntityExtractor(repo)
    entities = extractor.extract("患者腰部疼痛伴右下肢放射痛")
"""

import re
from typing import Optional

from src.knowledge_graph.models import EntityNode
from src.knowledge_graph.repository import KnowledgeGraphRepository


class EntityExtractor:
    """基于规则和词典的实体抽取器。"""

    def __init__(self, repo: Optional[KnowledgeGraphRepository] = None):
        """初始化实体抽取器。

        Args:
            repo: 知识图谱仓库（可选，用于从图谱加载词典）。
        """
        self.repo = repo
        # 内置词典（下腰痛/ACL 领域）
        self._builtin_dict: dict[str, str] = {}  # term → layer

    def load_dictionary(self, dict_path: str):
        """从文件加载词典。

        格式: 每行 "term,layer[,type]"
        """
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(",")
                term = parts[0].strip()
                layer = parts[1].strip() if len(parts) > 1 else "L0"
                self._builtin_dict[term] = layer

    def extract(self, text: str) -> list[EntityNode]:
        """从文本中抽取实体。

        Args:
            text: 用户输入文本（如主诉、病史描述）。

        Returns:
            抽取到的实体节点列表。
        """
        found: list[EntityNode] = []
        seen: set[str] = set()

        # 1. 词典匹配（最长优先）
        sorted_terms = sorted(self._builtin_dict.keys(), key=len, reverse=True)
        for term in sorted_terms:
            if term in text and term not in seen:
                layer = self._builtin_dict[term]
                found.append(EntityNode(name=term, layer=layer))
                seen.add(term)

        # 2. 图谱匹配（如果 repo 可用）
        if self.repo:
            # 尝试用连续双字词 + 单字词组合搜索
            tokens = self._tokenize(text)
            for token in tokens:
                if token not in seen and len(token) >= 2:
                    node = self.repo.get_node_by_name(token)
                    if node:
                        found.append(node)
                        seen.add(token)

        return found

    def _tokenize(self, text: str) -> list[str]:
        """中文分词辅助（简单滑动窗口）。"""
        # 先用标点符号和空格分割
        segments = re.split(r"[，。！？、；：""''（）\s]+", text)
        tokens = []
        for seg in segments:
            if not seg:
                continue
            # 生成长度 2-4 的滑动窗口词
            for length in range(min(4, len(seg)), 0, -1):
                for start in range(0, len(seg) - length + 1):
                    token = seg[start:start + length]
                    if len(token) >= 2:
                        tokens.append(token)
        return list(set(tokens))