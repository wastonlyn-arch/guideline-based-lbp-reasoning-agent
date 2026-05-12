"""
FAISS 向量索引管理。

依赖:
    - faiss-cpu (或 faiss-gpu)
    - numpy

用法:
    store = VectorStore(dimension=384, index_path="data/faiss_index")
    store.add(vectors, metadata_ids)
    results = store.search(query_vector, top_k=5)
"""

import os
import pickle
from typing import Optional

import faiss
import numpy as np


class VectorStore:
    """FAISS 向量索引管理器。"""

    def __init__(self, dimension: int, index_path: str = "data/faiss_index"):
        """初始化向量存储。

        Args:
            dimension: 向量维度（须与嵌入模型一致）。
            index_path: FAISS 索引文件的持久化路径。
        """
        self.dimension = dimension
        self.index_path = index_path
        self.index: Optional[faiss.Index] = None
        self._metadata: list[dict] = []  # id → metadata 映射

    def create_index(self, metric: str = "cosine"):
        """创建新索引（覆盖已有）。"""
        if metric == "cosine":
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
        self._metadata = []

    def load(self):
        """从磁盘加载已有索引。"""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        meta_path = self.index_path + ".meta.pkl"
        if os.path.exists(meta_path):
            with open(meta_path, "rb") as f:
                self._metadata = pickle.load(f)

    def save(self):
        """将索引保存到磁盘。"""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
        with open(self.index_path + ".meta.pkl", "wb") as f:
            pickle.dump(self._metadata, f)

    def add(self, vectors: np.ndarray, metadata: list[dict]):
        """添加向量及其元数据到索引。

        Args:
            vectors: shape (n, dimension) 的向量数组。
            metadata: 与向量一一对应的元数据列表。
        """
        if self.index is None:
            self.create_index()
        self.index.add(vectors)
        self._metadata.extend(metadata)

    def search(self, query: np.ndarray, top_k: int = 5) -> list[dict]:
        """检索最相似的 top_k 条记录。

        Args:
            query: shape (dimension,) 的查询向量。
            top_k: 返回结果数。

        Returns:
            [{"score": float, "metadata": dict}, ...]
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        if query.ndim == 1:
            query = query.reshape(1, -1)

        scores, indices = self.index.search(query, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append({
                "score": float(score),
                "metadata": self._metadata[idx],
            })
        return results

    @property
    def size(self) -> int:
        """返回索引中的向量数量。"""
        return self.index.ntotal if self.index else 0