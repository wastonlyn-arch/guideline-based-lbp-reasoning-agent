"""
术语映射服务 — 批量导入 / 查询 term_map.json ↔ SQLite term_mapping 表。

依赖规则: 可依赖 infrastructure 和 knowledge_graph.models/repository，不可依赖 retrieval/generation。

用法:
    from src.knowledge_graph.term_mapping import TermMappingService
    service = TermMappingService(repo)
    service.import_from_json("scripts/term_map.json")
"""

import json
import logging
from pathlib import Path
from typing import Optional

from src.knowledge_graph.models import TermMapping
from src.knowledge_graph.repository import KnowledgeGraphRepository

logger = logging.getLogger(__name__)


class TermMappingService:
    """术语映射服务：JSON ↔ 数据库的双向同步。"""

    def __init__(self, repo: KnowledgeGraphRepository):
        self.repo = repo

    def import_from_json(self, json_path: str | Path) -> int:
        """从 term_map.json 批量导入术语映射到数据库。

        Args:
            json_path: term_map.json 文件路径。

        Returns:
            int: 导入的记录数。

        Raises:
            FileNotFoundError: 文件不存在。
            json.JSONDecodeError: JSON 格式错误。
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"术语映射文件不存在: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        count = 0

        # 支持两种格式：
        # 1. {node_name: zh_term} 平面字典
        # 2. [{node_name, zh_term, layer, ...}] 对象列表
        if isinstance(data, list):
            for item in data:
                mapping = TermMapping(
                    node_name=item["node_name"],
                    zh_term=item["zh_term"],
                    layer=item.get("layer", ""),
                    node_type=item.get("node_type", "generic"),
                    node_subtype=item.get("node_subtype", ""),
                    description=item.get("description", ""),
                )
                self.repo.upsert_term_mapping(mapping)
                count += 1
        elif isinstance(data, dict):
            # 平面字典格式: { "Spinal_Hinge": "脊柱铰链", ... }
            # 需要从 nodes 表反查 layer
            for node_name, zh_term in data.items():
                node = self.repo.get_node_by_name(node_name)
                layer = node.layer if node else ""
                mapping = TermMapping(
                    node_name=node_name,
                    zh_term=zh_term,
                    layer=layer,
                )
                self.repo.upsert_term_mapping(mapping)
                count += 1

        logger.info("术语映射导入完成: %d 条记录", count)
        return count

    def lookup(self, zh_term: str) -> Optional[TermMapping]:
        """按中文术语查找对应的节点映射。"""
        return self.repo.get_term_mapping_by_zh(zh_term)

    def lookup_node(self, node_name: str) -> list[TermMapping]:
        """按节点名查找所有中文术语。"""
        return self.repo.get_term_mapping_by_node(node_name)

    def search(self, keyword: str, limit: int = 20) -> list[TermMapping]:
        """模糊搜索中文术语。"""
        return self.repo.search_term_mapping(keyword, limit)