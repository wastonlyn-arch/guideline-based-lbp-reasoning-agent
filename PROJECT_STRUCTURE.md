# Project Structure — clinical_reasoning_agent (v0.3 MVP)

## 目录树

```
clinical_reasoning_agent/
├── docs/                          # 设计文档、对话归档
│   └── conversations/             # AI 对话归档子目录
├── data/                          # 数据资产
│   ├── raw/                       # 原始数据（指南PDF等）
│   ├── processed/                 # 清洗后数据
│   └── ontology/                  # 本体设计Excel / M-rule 规则文件
├── src/                           # 核心代码
│   ├── __init__.py
│   ├── infrastructure/            # 共享基础设施层（无业务逻辑）
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite 通用连接与CRUD
│   │   ├── embedder.py            # sentence-transformers 封装
│   │   ├── vector_store.py        # FAISS 索引管理
│   │   ├── llm_client.py          # DeepSeek/Ollama 调用
│   │   └── config.py              # 配置加载（yaml+env）
│   ├── knowledge_graph/           # 知识图谱层
│   │   ├── __init__.py
│   │   ├── schema.sql             # 建表语句（nodes, edges, aliases, chunks, diagnostic_rules, inference_log）
│   │   ├── models.py              # 节点/边/别名/路径数据类
│   │   ├── repository.py          # 图谱CRUD封装
│   │   └── path_retriever.py      # 递归CTE路径查询
│   ├── extraction/                # 实体抽取
│   │   ├── __init__.py
│   │   └── entity_extractor.py    # 规则/词典实体抽取
│   ├── reasoning/                 # 推理引擎层（v0.3 新增）
│   │   ├── __init__.py
│   │   ├── rule_engine.py         # M-rule 规则匹配引擎
│   │   ├── path_builder.py        # 可解释推理路径构建
│   │   └── confidence.py          # 置信度聚合（max/weighted_sum/product）
│   ├── retrieval/                 # 检索管道
│   │   ├── __init__.py
│   │   ├── graph_searcher.py      # 图谱路径检索
│   │   └── chunk_searcher.py      # 向量文献检索
│   ├── generation/                # 生成层
│   │   ├── __init__.py
│   │   ├── prompt_templates.py    # SOAP提示词模板（含 M-rule 推理路径段）
│   │   └── soap_generator.py      # LLM生成 SOAP 报告
│   └── orchestrator.py            # 主流程编排（实体抽取 → M-rule 推理 → 检索 → SOAP 生成）
├── notebooks/                     # 演示Notebook
├── tests/                         # 测试目录
├── deploy/                        # 部署文件
│   └── requirements.txt
├── .env.example                   # 环境变量示例
├── .gitignore                     # Git忽略规则
├── config.yaml                    # 项目配置模板（含 reasoning / soap 配置段）
├── PROJECT_STRUCTURE.md           # 项目结构说明（本文档）
└── README.md                      # 项目说明
```

## 准入规则

| 目录 | 允许放什么 | 禁止放什么 |
|------|-----------|-----------|
| `docs/` | Markdown、PDF、设计图 | 代码、数据库 |
| `data/` | 静态数据文件、数据库 | 源代码、日志 |
| `src/infrastructure/` | 可复用的底层工具（无业务逻辑） | 引用 knowledge_graph、extraction、reasoning、retrieval、generation 模块 |
| `src/knowledge_graph/` | 图谱schema、CRUD、查询逻辑 | 依赖 extraction、reasoning、retrieval、generation |
| `src/extraction/` | 实体抽取逻辑 | 依赖 retrieval、generation |
| `src/reasoning/` | M-rule 规则引擎、推理路径、置信度 | 依赖 generation、orchestrator |
| `src/generation/` | 提示词模板、LLM调用、推理路径消费 | 直接操作数据库（通过 infrastructure） |
| `notebooks/` | Jupyter 文件 | 核心业务逻辑 |
| `deploy/` | Dockerfile、requirements.txt | 源代码 |

## 模块依赖规则

依赖方向必须是**单向**的：

```
infrastructure  ←  knowledge_graph  ←  retrieval  ←  generation  ←  orchestrator
                        ↑                ↑
                    extraction       reasoning
```

具体约束：

- **infrastructure**：不依赖项目中任何其他模块
- **knowledge_graph**：可依赖 infrastructure
- **extraction**：可依赖 infrastructure 和 knowledge_graph
- **reasoning**（v0.3 MVP）：可依赖 infrastructure、knowledge_graph、retrieval，不可依赖 generation 或 orchestrator
- **retrieval**：可依赖 infrastructure 和 knowledge_graph
- **generation**：可依赖 infrastructure、retrieval、reasoning
- **orchestrator**：可依赖所有模块（但有义务协调下层，避免循环依赖）

> **注意**: v0.3 MVP 中 generation/soap_generator.py 从 reasoning 导入 ReasoningPath 是合规的（向下依赖），不属于违规。

## 推理管线流程 (v0.3 MVP)

```
患者输入文本
    │
    ▼
┌──────────────────┐
│  实体抽取         │  EntityExtractor.extract()
│  (规则/词典匹配)  │
└────────┬─────────┘
         │ 实体列表
         ▼
┌──────────────────┐
│  M-rule 规则匹配  │  RuleEngine.match()
│  (确定性推理引擎) │
└────────┬─────────┘
         │ 匹配规则
         ▼
┌──────────────────┐
│  推理路径构建     │  PathBuilder.build_from_entities()
│  (可解释链路)    │
└────────┬─────────┘
         │ 推理路径摘要
         ▼
┌──────────────────┐  ┌──────────────────┐
│  图谱路径检索     │  │  向量文献检索     │
│  GraphSearcher   │  │  ChunkSearcher   │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └────────┬────────────┘
                  │ 检索结果
                  ▼
┌──────────────────┐
│  SOAP 报告生成    │  SOAPGenerator.generate()
│  (LLM + 推理路径) │
└──────────────────┘
```

## 技术栈

| 层 | 技术选择 |
|----|---------|
| 数据库 | SQLite (WAL mode, FK enabled) |
| 向量索引 | FAISS (IndexFlatIP 余弦相似度) |
| 文本嵌入 | sentence-transformers (all-MiniLM-L6-v2) |
| LLM API | DeepSeek / Ollama (OpenAI 兼容接口) |
| 推理引擎 | M-rule 规则引擎（确定性匹配） |
| 配置管理 | PyYAML + 环境变量 |
| 编程语言 | Python 3.11+ |
| 测试 | pytest |

## 文件数统计

| 层 | Python 文件 | SQL 文件 | 其他 |
|----|------------|---------|------|
| infrastructure | 5 | 0 | 0 |
| knowledge_graph | 3 | 1 | 0 |
| extraction | 1 | 0 | 0 |
| reasoning | 3 | 0 | 0 |
| retrieval | 2 | 0 | 0 |
| generation | 2 | 0 | 0 |
| 编排 | 1 | 0 | 0 |
| 文档 docs/ | 0 | 0 | 6 |
| 根目录配置 | 0 | 0 | 6 |
| **合计** | **17** | **1** | **12** |

## 设计文档索引

| 文档 | 位置 | 作用 | 读者 |
|:----|:----|:----|:----:|
| `ARCHITECTURE_SPEC.md` | `docs/` | **架构规范** — 模块职责、API 签名、配置项、数据流 | 开发者、代码审查 |
| `ARCHITECTURE_CONVERGENCE.md` | `docs/` | **三家 AI 对比** — ChatGPT / Gemini / DeepSeek 共识与分歧 | 项目所有者（决策前参考） |
| `ARCHITECTURE_DECISIONS.md` | `docs/` | **决策记录** — 每个议题的最终决策、理由、备选方案 | 新人 onboarding、回顾 |
| `conversations/architecture/` | `docs/` | **AI 原始回复归档** — 三家的完整对话记录 | 回溯原始上下文 |

### 文档层次关系

```
conversations/architecture/  (三家 AI 的原始回复)
        │
        ▼
 ARCHITECTURE_CONVERGENCE.md  (对比分析：共识/分歧/独家观点)
        │
        ▼
  ARCHITECTURE_SPEC.md  (架构规范定义：模块、API、配置)
        │
        ▼
 ARCHITECTURE_DECISIONS.md  (决策记录：每个议题的最终决定)
```
