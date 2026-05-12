"""
SOAP 提示词模板 — 用于生成康复医学 SOAP 报告 (v0.3 MVP)。

依赖规则: 可依赖 infrastructure、retrieval、reasoning，不直接操作数据库。

用法:
    templates = PromptTemplates()
    soap_prompt = templates.build_soap_prompt(
        subjective="患者腰痛 3 周",
        objective="腰椎活动度受限",
        graph_paths=["腰痛 → 椎间盘突出 → 保守治疗"],
        reasoning_summary="推理路径摘要...",
        chunks=["指南片段1", "指南片段2"],
    )
    print(soap_prompt["system"])   # 系统提示
    print(soap_prompt["user"])     # 用户提示
"""

from typing import Optional


class PromptTemplates:
    """SOAP 报告生成的提示词模板集合 (v0.3 MVP)。"""

    SYSTEM_PROMPT = """你是一位资深的康复医学专家。请基于以下临床信息，按照 SOAP 格式生成一份结构化的康复评估报告。

要求：
1. **Subjective (主观资料)**：整理患者的主诉、病史、疼痛情况。
2. **Objective (客观检查)**：列出体格检查、功能评估、影像学发现。
3. **Assessment (评估)**：结合 M-rule 推理路径、知识图谱路径和文献证据，给出诊断分析和可解释的临床推理过程。
4. **Plan (计划)**：提出具体的康复治疗方案，包括治疗目标、干预手段、随访计划。

请使用专业但易懂的语言，在适当位置引用证据来源。如果信息不足，请明确指出不确定之处。"""

    USER_TEMPLATE = """## 主观资料
{subjective}

## 客观检查
{objective}

## M-rule 推理路径
{reasoning_summary}

## 知识图谱路径
{graph_paths_text}

## 相关文献证据
{chunks_text}

请生成 SOAP 报告："""

    def build_soap_prompt(
        self,
        subjective: str = "",
        objective: str = "",
        graph_paths: Optional[list[str]] = None,
        reasoning_summary: str = "",
        chunks: Optional[list[dict]] = None,
    ) -> dict[str, str]:
        """构建 SOAP 生成的完整提示词 (v0.3 MVP)。

        Args:
            subjective: 患者主观资料文本。
            objective: 客观检查结果文本。
            graph_paths: 图谱推理路径文本列表。
            reasoning_summary: 推理引擎输出的推理路径摘要文本。
            chunks: 检索到的文献片段列表（每项含 text 字段）。

        Returns:
            {"system": str, "user": str} 提示词对。
        """
        # 格式化推理路径
        reasoning_text = reasoning_summary or "无"

        # 格式化图谱路径
        paths_text = "无"
        if graph_paths:
            paths_lines = [f"{i+1}. {p}" for i, p in enumerate(graph_paths)]
            paths_text = "\n".join(paths_lines)

        # 格式化文献片段
        chunks_text = "无"
        if chunks:
            chunk_lines = []
            for i, c in enumerate(chunks):
                source = c.get("metadata", {}).get("source", "未知来源")
                text = c.get("text", str(c))
                chunk_lines.append(f"[{i+1}] 来源: {source}\n{text}")
            chunks_text = "\n\n".join(chunk_lines)

        user_prompt = self.USER_TEMPLATE.format(
            subjective=subjective or "（未提供）",
            objective=objective or "（未提供）",
            reasoning_summary=reasoning_text,
            graph_paths_text=paths_text,
            chunks_text=chunks_text,
        )

        return {
            "system": self.SYSTEM_PROMPT,
            "user": user_prompt,
        }
