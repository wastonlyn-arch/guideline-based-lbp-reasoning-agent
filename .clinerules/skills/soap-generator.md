---
name: SOAP报告生成
description: 从患者主诉生成结构化 SOAP 报告
---

# SOAP Report Generation Skill

## Context

SOAP 是医疗记录的标准化格式：
- **S**ubjective：患者主诉（患者自述症状、病史）
- **O**bjective：客观检查数据（体征、实验室结果、影像学）
- **A**ssessment：评估与诊断（鉴别诊断、推理依据）
- **P**lan：治疗计划（药物、检查、随访）

本项目使用知识图谱 + LLM 的混合架构：
1. 实体抽取 → 图谱检索 → 向量检索 → LLM 生成
2. 图谱路径提供推理依据（M-rules）
3. LLM 消费推理路径生成自然语言报告

## Instructions

1. 首先完成实体抽取（检查 `src/extraction/` 是否已实现）
2. 执行图谱检索（`src/knowledge_graph/`）获取相关医学知识路径
3. 执行向量检索（`src/retrieval/`）获取文献支持
4. 调用 LLM 生成 SOAP 格式报告（`src/generation/`）
5. 验证：
   - 报告包含所有 4 个部分（S/O/A/P）
   - 无患者真实姓名（使用 session_id 替代）
   - 推理路径有图谱证据支撑（引用 M-rule）

## Output Format

```markdown
## SOAP 报告 — Patient #[session_id]

### Subjective
[患者主诉摘要]

### Objective
[客观检查数据]

### Assessment
[诊断评估 + 推理依据]
- 图谱路径：[引用]

### Plan
[治疗计划]
```

## Validation

- [ ] 包含 S/O/A/P 四个部分
- [ ] 无 PHI（患者身份信息）
- [ ] 每个评估有推理路径引用
- [ ] Plan 部分可执行（具体药物/检查名称）