# Clinical Reasoning Agent

面向康复医学的可解释临床推理 Agent — 结合知识图谱与 RAG 技术，以下腰痛康复为主领域，生成结构化 SOAP 报告。

## 快速开始

```bash
# 1. 创建 conda 环境
conda create -n clinical_reasoning python=3.11 -y
conda activate clinical_reasoning

# 2. 安装依赖
pip install -r deploy/requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 4. 运行演示
python -m src.orchestrator
# 或打开 notebooks/ 中的 Jupyter Notebook
```

## 项目结构

参见 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) 获取完整的目录树、准入规则和依赖约束。

## 架构概览

```
用户输入 → 实体抽取 → 图谱检索 → 向量检索 → LLM 生成 → SOAP 报告
                                         ↘ 图谱路径 ↗
```

- **实体抽取**: 基于医学词典 + 知识图谱的双源实体识别
- **图谱检索**: 递归 CTE 在知识图谱中查找推理路径
- **向量检索**: FAISS 语义相似度检索文献片段
- **LLM 生成**: 整合图谱证据 + 文献证据，生成结构化 SOAP 报告

## 领域范围

当前专注：
- **下腰痛 (Low Back Pain)**: 椎间盘突出、腰椎管狭窄、肌肉劳损等

## 许可证

MIT