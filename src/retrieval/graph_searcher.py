"""
图谱路径检索器 — 包装 PathRetriever，集成实体抽取结果进行图谱搜索。

依赖规则: 可依赖 infrastructure 和 knowledge_graph。
"""

from src.infrastructure.database import Database
from src.knowledge_graph.path_retriever import PathRetriever
from src.knowledge_graph.models import EntityNode, Path


class GraphSearcher:
    """图谱检索器 — 根据实体列表在图谱中查找推理路径。"""

    def __init__(self, db: Database):
        """初始化图谱检索器。

        Args:
            db: 数据库连接。
        """
        self.db = db
        self._retriever = PathRetriever(db)

    def search_from_entities(
        self,
        entities: list[EntityNode],
        max_depth: int = 4,
        top_k: int = 10,
    ) -> list[Path]:
        """根据抽取的实体，检索实体间的推理路径。

        策略: 对实体列表两两配对，查找节点间最短路径。

        Args:
            entities: 已抽取的实体列表。
            max_depth: 最大路径深度。
            top_k: 返回路径数量上限。

        Returns:
            检索到的推理路径列表。
        """
        if len(entities) < 2:
            return []

        paths: list[Path] = []
        seen_paths: set[str] = set()

        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                src, tgt = entities[i], entities[j]
                for pair in [(src, tgt), (tgt, src)]:
                    found = self._retriever.find_paths(
                        source_name=pair[0].name,
                        target_name=pair[1].name,
                        max_depth=max_depth,
                        limit=top_k,
                    )
                    for path in found:
                        key = path.to_text()
                        if key and key not in seen_paths:
                            paths.append(path)
                            seen_paths.add(key)

        # 按路径长度和置信度排序
        paths.sort(key=lambda p: (len(p), -p.total_score))
        return paths[:top_k]

    def search_by_keywords(
        self,
        keywords: list[str],
        max_depth: int = 4,
        top_k: int = 10,
    ) -> list[Path]:
        """直接根据关键词列表检索路径。

        Args:
            keywords: 关键词列表（如 ["腰痛", "椎间盘突出"]）。
            max_depth: 最大路径深度。
            top_k: 返回路径数量上限。

        Returns:
            检索到的推理路径列表。
        """
        from src.knowledge_graph.repository import KnowledgeGraphRepository
        repo = KnowledgeGraphRepository(self.db)

        entities: list[EntityNode] = []
        for kw in keywords:
            node = repo.get_node_by_name(kw)
            if node:
                entities.append(node)

        return self.search_from_entities(entities, max_depth, top_k)