"""
向量文献检索器 — 使用向量存储检索相关文献片段。

依赖规则: 可依赖 infrastructure（embedder, vector_store）和 knowledge_graph（models）。
"""

from typing import Optional

import numpy as np

from src.infrastructure.embedder import Embedder
from src.infrastructure.vector_store import VectorStore


class ChunkSearcher:
    """文献片段检索器 — 基于语义相似度的向量检索。"""

    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        """初始化检索器。

        Args:
            embedder: 文本嵌入模型。
            vector_store: FAISS 向量索引。
        """
        self.embedder = embedder
        self.vector_store = vector_store

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> list[dict]:
        """搜索与查询最相关的文献片段。

        Args:
            query: 查询文本（如患者症状描述）。
            top_k: 返回结果数量。
            score_threshold: 最低相似度阈值，低于此值的将被过滤。

        Returns:
            [{"score": float, "metadata": dict, "text": str}, ...]
        """
        query_vec = self.embedder.encode(query)
        results = self.vector_store.search(query_vec, top_k=top_k * 2)

        # 过滤低分结果
        filtered = [r for r in results if r["score"] >= score_threshold]

        # 补充 text 字段（从 metadata 中提取）
        for r in filtered:
            r["text"] = r.get("metadata", {}).get("text", "")

        return filtered[:top_k]

    def batch_search(
        self,
        queries: list[str],
        top_k_per_query: int = 3,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        """批量搜索（多查询合并结果并去重）。

        Args:
            queries: 查询文本列表。
            top_k_per_query: 每个查询返回结果数。
            score_threshold: 相似度阈值。

        Returns:
            合并去重后的结果列表。
        """
        seen_texts: set[str] = set()
        merged: list[dict] = []

        for query in queries:
            results = self.search(query, top_k=top_k_per_query, score_threshold=score_threshold)
            for r in results:
                text = r.get("text", "")
                if text and text not in seen_texts:
                    merged.append(r)
                    seen_texts.add(text)

        # 按分数降序排列
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged