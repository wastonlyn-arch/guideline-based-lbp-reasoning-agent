# CONTEXT — clinical_reasoning_agent

## 项目一句话定位

面向康复医学的可解释临床推理 Agent。结合知识图谱（KG）+ M-rule 确定性规则引擎 + RAG 检索，以下腰痛和 ACL 康复为主领域，生成结构化 SOAP 报告。

## 快速入口

```bash
conda create -n clinical_reasoning python=3.11 -y
conda activate clinical_reasoning
pip install -r deploy/requirements.txt
cp .env.example .env   # 填入 DEEPSEEK_API_KEY
python -m src.orchestrator
```

详情参见 [README.md](../README.md)。

## 目录速览

```
clinical_reasoning_agent/
├── src/
│   ├── infrastructure/      # 基础设施：数据库、嵌入、向量索引、LLM 客户端、配置
│   ├── knowledge_graph/     # 知识图谱：schema、模型、CRUD、CTE 路径检索
│   ├── extraction/          # 实体抽取：基于词典+图谱的医学实体识别
│   ├── reasoning/           # 推理引擎：M-rule 规则匹配、推理路径构建、置信度聚合
│   ├── retrieval/           # 检索管道：图谱路径检索、向量文献检索（FAISS）
│   ├── generation/          # 生成层：SOAP 提示词模板、LLM 报告生成
│   └── orchestrator.py      # 主编排器：串联 5 步推理管线
├── data/                    # 数据资产（原始数据、清洗数据、本体规则）
├── docs/                    # 设计文档与归档
├── notebooks/               # 演示 Notebook
└── deploy/                  # 部署配置与依赖
```

## 核心概念词汇表

| 术语 | 含义 |
|------|------|
| **KG** | 知识图谱（Knowledge Graph）。节点 = 医学实体（症状、疾病、治疗），边 = 关系 |
| **M-rule** | 确定性规则引擎。每条规则含前提条件 + 结论 + 置信度，用于可解释推理 |
| **SOAP** | 临床报告格式：Subjective（主观）→ Objective（客观）→ Assessment（评估）→ Plan（计划） |
| **CTE** | Common Table Expression。SQLite 递归查询，用于知识图谱中的路径搜索 |
| **FAISS** | Facebook AI 向量相似度搜索引擎，用于语义检索文献 |
| **RAG** | 检索增强生成（Retrieval-Augmented Generation） |

## 推理管线（5 步）

```
患者输入 → 实体抽取 → M-rule 规则匹配 → 推理路径构建 → 图谱检索 + 向量检索 → SOAP 生成
```

每步的入参出参参见各模块 docstring 和 [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) 中的依赖规则。

## 关键约束（必须遵守）

- **依赖方向严格单向**：infrastructure ← knowledge_graph ← retrieval ← generation ← orchestrator
- **extraction/reasoning** 可跨过 retrieval 直连 knowledge_graph 和 infrastructure
- **generation** 不得直接操作数据库（必须通过 infrastructure）
- 所有 `__init__.py` 保持空白或仅含 docstring，不引入 import 语句

## 相关文档

| 文档 | 用途 |
|------|------|
| [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) | 完整目录树、准入规则、依赖规则 |
| [README.md](../README.md) | 项目简介、快速开始 |
| [config.yaml](../config.yaml) | 项目配置模板（LLM、数据库、向量索引、推理策略） |