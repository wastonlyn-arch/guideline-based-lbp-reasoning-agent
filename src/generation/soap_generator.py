"""
SOAP 报告生成器 — 基于推理路径和 LLM 生成 SOAP 格式的临床推理报告。

依赖规则: 可依赖 infrastructure、retrieval、reasoning。

SOAP 结构:
    - S (Subjective): 患者主观信息
    - O (Objective): 客观检查发现
    - A (Assessment): 评估与推理（含推理路径）
    - P (Plan): 治疗/康复计划
"""

from __future__ import annotations

from typing import Optional

from src.infrastructure.llm_client import LLMClient
from src.retrieval.chunk_searcher import ChunkSearcher
from src.retrieval.graph_searcher import GraphSearcher
from src.reasoning.path_builder import ReasoningPath


class SOAPGenerator:
    """SOAP 报告生成器 — 组装患者数据 + 检索结果 + 推理路径，调用 LLM 生成 SOAP。"""

    def __init__(
        self,
        llm_client: LLMClient,
        graph_searcher: Optional[GraphSearcher] = None,
        chunk_searcher: Optional[ChunkSearcher] = None,
    ):
        """初始化生成器。

        Args:
            llm_client: LLM 调用客户端。
            graph_searcher: 图谱路径检索器（可选）。
            chunk_searcher: 向量文献检索器（可选）。
        """
        self.llm = llm_client
        self.graph_searcher = graph_searcher
        self.chunk_searcher = chunk_searcher

    def generate(
        self,
        subjective: str,
        objective: str,
        reasoning_paths: list[ReasoningPath],
        context_chunks: Optional[list[dict]] = None,
    ) -> str:
        """生成完整 SOAP 报告文本。

        Args:
            subjective: 患者主观描述（主诉、病史等）。
            objective: 客观检查结果。
            reasoning_paths: 推理引擎输出的推理路径列表。
            context_chunks: 检索到的文献片段列表（可选）。

        Returns:
            SOAP 格式的完整报告文本。
        """
        # 组装推理摘要
        path_summaries = "\n\n".join(
            p.summarize([p]) if hasattr(p, "summarize") else str(p)
            for p in reasoning_paths
        )

        # 组装检索上下文
        retrieval_context = ""
        if context_chunks:
            retrieval_context = "\n".join(
                f"- [{c.get('score', 0):.2f}] {c.get('text', '')}"
                for c in context_chunks[:5]
            )

        # 构建 prompt
        prompt = self._build_prompt(
            subjective=subjective,
            objective=objective,
            reasoning_paths=path_summaries,
            retrieval_context=retrieval_context,
        )

        return self.llm.generate(prompt)

    def _build_prompt(
        self,
        subjective: str,
        objective: str,
        reasoning_paths: str,
        retrieval_context: str,
    ) -> str:
        """构建 LLM prompt 模板。"""
        sections = [
            "请根据以下信息生成 SOAP 格式的临床推理报告。\n",
            "## S — 主观（Subjective）",
            subjective,
            "",
            "## O — 客观（Objective）",
            objective,
            "",
            "## A — 评估（Assessment）",
            "推理路径:",
            reasoning_paths,
            "",
        ]
        if retrieval_context:
            sections.extend([
                "参考证据:",
                retrieval_context,
                "",
            ])
        sections.extend([
            "## P — 计划（Plan）",
            "请基于上述评估生成康复治疗计划。\n",
        ])
        return "\n".join(sections)

    def generate_subjective(self, raw_input: str) -> str:
        """从原始输入中提取 S 段结构化信息。

        Args:
            raw_input: 患者原始输入文本。

        Returns:
            结构化的 S 段文本。
        """
        prompt = (
            "请将以下患者原始描述整理为结构化 SOAP 的 S（主观）段：\n\n"
            f"{raw_input}\n"
        )
        return self.llm.generate(prompt)

    def generate_plan(
        self, assessment: str, reasoning_paths: list[ReasoningPath]
    ) -> str:
        """基于评估生成 P 段治疗计划。

        Args:
            assessment: A 段评估文本。
            reasoning_paths: 推理路径列表。

        Returns:
            结构化的 P 段文本。
        """
        path_summary = "\n".join(
            p.summarize([p]) for p in reasoning_paths
        ) if reasoning_paths else "无推理路径"
        prompt = (
            "请根据以下评估和推理路径生成康复治疗计划（SOAP 的 P 段）：\n\n"
            f"## 评估\n{assessment}\n\n"
            f"## 推理路径\n{path_summary}\n"
        )
        return self.llm.generate(prompt)