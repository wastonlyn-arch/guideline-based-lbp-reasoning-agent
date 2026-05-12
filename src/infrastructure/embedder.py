"""
sentence-transformers 嵌入封装。

依赖:
    - sentence-transformers

用法:
    embedder = Embedder(model_name="all-MiniLM-L6-v2")
    vector = embedder.encode("患者腰部疼痛")
"""

from typing import Optional

import numpy as np


class Embedder:
    """文本嵌入生成器，封装 sentence-transformers。"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """初始化嵌入模型。

        Args:
            model_name: HuggingFace 模型名称。
        """
        self.model_name = model_name
        self._model = None

    def _lazy_load(self):
        """延迟加载模型（首次调用时初始化）。"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)

    def encode(self, text: str) -> np.ndarray:
        """将单条文本编码为向量。

        Args:
            text: 输入文本。

        Returns:
            numpy 数组，shape (embedding_dim,)。
        """
        self._lazy_load()
        return self._model.encode(text, normalize_embeddings=True)

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """批量编码。

        Args:
            texts: 文本列表。

        Returns:
            numpy 数组，shape (n, embedding_dim)。
        """
        self._lazy_load()
        return self._model.encode(texts, normalize_embeddings=True)

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度。"""
        sample = self.encode("")
        return sample.shape[0]