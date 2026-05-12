"""
主流程编排器 (v0.3 MVP) — 串联实体抽取 → M-rule 推理 → 知识图谱检索 → 向量检索 → LLM SOAP 生成。

依赖规则: 可依赖所有下层模块（infrastructure, knowledge_graph, extraction, retrieval, reasoning, generation）。
"""

from dataclasses import dataclass, field
from typing import Optional

from src.infrastructure.config import Config
from src.infrastructure.database import Database
from src.infrastructure.embedder import Embedder
from src.infrastructure.vector_store import VectorStore
from src.infrastructure.llm_client import LLMClient
from src.knowledge_graph.repository import KnowledgeGraphRepository
from src.knowledge_graph.models import EntityNode, Path
from src.extraction.entity_extractor import EntityExtractor
from src.reasoning.rule_engine import RuleEngine, MRule
from src.reasoning.path_builder import PathBuilder, ReasoningPath
from src.reasoning.confidence import ConfidenceAggregator
from src.retrieval.graph_searcher import GraphSearcher
from src.retrieval.chunk_searcher import ChunkSearcher
from src.generation.soap_generator import SOAPGenerator


@dataclass
class ClinicalContext:
    """临床推理上下文 (v0.3 MVP) — 管线输入的完整数据。"""
    subjective: str = ""                         # 主诉
    objective: str = ""                          # 客观检查
    entities: list[EntityNode] = field(default_factory=list)
    matched_rules: list[tuple[MRule, float]] = field(default_factory=list)
    reasoning_paths: list[ReasoningPath] = field(default_factory=list)
    reasoning_summary: str = ""
    graph_paths: list[Path] = field(default_factory=list)
    chunks: list[dict] = field(default_factory=list)
    soap_report: str = ""


class ClinicalReasoningOrchestrator:
    """康复医学临床推理 Agent 的主流程编排器 (v0.3 MVP)。"""

    def __init__(self, config: Optional[Config] = None):
        """初始化编排器及所有子模块。

        Args:
            config: 项目配置（可选，默认从 config.yaml + 环境变量加载）。
        """
        self.config = config or Config()

        # ── 基础设施 ──
        self.db = Database(self.config.db_path)
        self.embedder = Embedder(self.config.embedding_model)
        self.vector_store = VectorStore(
            dimension=384,
            index_path=self.config.vector_db_path,
        )
        self.llm = LLMClient(
            api_key=self.config.llm_api_key,
            model=self.config.llm_model,
        )

        # ── 业务模块 ──
        self.repo = KnowledgeGraphRepository(self.db)
        self.extractor = EntityExtractor(self.repo)
        self.graph_searcher = GraphSearcher(self.db)
        self.chunk_searcher = ChunkSearcher(self.embedder, self.vector_store)
        self.rule_engine = RuleEngine()
        self.path_builder = PathBuilder()
        self.confidence = ConfidenceAggregator(
            strategy=self.config.reasoning.get("confidence_strategy", "weighted_sum"),
        )
        self.soap_generator = SOAPGenerator(
            llm_client=self.llm,
            graph_searcher=self.graph_searcher,
            chunk_searcher=self.chunk_searcher,
        )

    def run(
        self,
        subjective: str,
        objective: str = "",
        top_k_paths: int = 5,
        top_k_chunks: int = 5,
    ) -> ClinicalContext:
        """执行完整推理管线 (v0.3 MVP)。

        步骤:
            1. 实体抽取（从 subjective 文本中识别医学实体）
            2. M-rule 规则匹配 + 推理路径构建
            3. 图谱路径检索（实体间推理路径）
            4. 向量文献检索（语义相关的文献片段）
            5. SOAP 报告生成（LLM 生成结构化报告）

        Args:
            subjective: 患者主观资料（主诉、病史等）。
            objective: 客观检查结果（可选）。
            top_k_paths: 图谱路径返回数量。
            top_k_chunks: 文献片段返回数量。

        Returns:
            ClinicalContext 包含整条管线的中间和最终输出。
        """
        ctx = ClinicalContext(subjective=subjective, objective=objective)

        # 1. 实体抽取
        ctx.entities = self.extractor.extract(subjective)
        entity_names = [e.name for e in ctx.entities]

        # 2. M-rule 推理引擎
        ctx.matched_rules = self.rule_engine.match(entity_names)
        ctx.reasoning_paths = self.path_builder.build_from_entities(
            ctx.entities, ctx.matched_rules
        )
        ctx.reasoning_summary = self.path_builder.summarize(ctx.reasoning_paths)

        # 3. 图谱路径检索
        if len(entity_names) >= 2:
            ctx.graph_paths = self.graph_searcher.search_by_keywords(
                keywords=entity_names,
                top_k=top_k_paths,
            )
        path_texts = [p.to_text() for p in ctx.graph_paths]

        # 4. 向量文献检索
        search_queries = [subjective] + entity_names
        ctx.chunks = self.chunk_searcher.batch_search(
            queries=search_queries,
            top_k_per_query=top_k_chunks,
        )

        # 5. SOAP 报告生成（含推理路径）
        ctx.soap_report = self.soap_generator.generate(
            subjective=subjective,
            objective=objective,
            reasoning_paths=ctx.reasoning_paths,
            context_chunks=ctx.chunks,
        )

        return ctx

    def load_rules(self, rules_path: str):
        """加载 M-rule 规则文件到推理引擎。"""
        self.rule_engine.load_rules(rules_path)

    def add_custom_rule(self, rule: MRule):
        """添加自定义规则。"""
        self.rule_engine.add_rule(rule)

    def close(self):
        """释放资源（关闭数据库连接等）。"""
        self.db.close()
