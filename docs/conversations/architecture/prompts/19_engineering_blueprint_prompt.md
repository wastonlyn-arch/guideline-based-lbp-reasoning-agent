# 19 — 工程蓝图多方讨论 Prompt

将此 prompt 分别发送给 ChatGPT、DeepSeek（及其他你想咨询的 AI），**每次使用全新对话**，然后将各家的回答保存为：

- `19_chatgpt_response.md`
- `19_deepseek_response.md`
- `19_gemini_response.md`（可选）

---

## 发送提示词（复制以下全部内容）

```
你是一位资深软件架构师和全栈工程师。以下项目已经完成了架构规范的定义（见附件 ARCHITECTURE_SPEC.md v0.3），现在需要将规范落地为可执行的代码。请基于规范文档，从以下 10 个维度给出工程蓝图建议。每个维度请给出 **具体到文件级** 的结论，而非泛泛的原则。

---

## 项目背景

- **项目名称**: Clinical Reasoning Agent — MCRM 物理治疗临床推理教学辅助
- **技术栈**: Python 3.11、SQLite、NetworkX、FAISS、sentence-transformers、DeepSeek API、Streamlit（未来前端）
- **当前状态**: v0.2 代码已存在于 `src/` 下（见下方目录树），架构规范已收敛到 v0.3（MCRM 模型），需要改造代码以对齐新规范
- **定位**: MVP 演示阶段，非生产系统
- **当前图谱规模**: 单份 McGill 指南 900 页已超 2000 节点，未来 2-3 本指南可达 5000-8000 节点，完整课纲可能 15000+ 节点

## 当前实际代码结构

```
src/
├── __init__.py
├── orchestrator.py                    # 主流程 (Class: ClinicalReasoningOrchestrator)
├── infrastructure/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── embedder.py
│   ├── llm_client.py
│   └── vector_store.py
├── extraction/
│   ├── __init__.py
│   └── entity_extractor.py            # 规则实体抽取（词典+正则）
├── knowledge_graph/
│   ├── __init__.py
│   ├── schema.sql                     # nodes/edges/chunks 表 + term_mapping 表
│   ├── models.py                      # 数据类定义
│   ├── repository.py                  # 图谱 CRUD + term_mapping 查询
│   ├── path_retriever.py              # NetworkX 路径检索
│   └── term_mapping.py                # 独立术语映射服务
├── reasoning/
│   ├── __init__.py
│   ├── rule_engine.py                 # M-rule 规则匹配引擎
│   ├── path_builder.py                # 推理路径构建器
│   └── confidence.py                  # 置信度聚合器
├── retrieval/
│   ├── __init__.py
│   ├── graph_searcher.py              # 图谱检索封装
│   └── chunk_searcher.py              # FAISS 向量检索
└── generation/
    ├── __init__.py
    ├── prompt_templates.py            # SOAP 提示词模板
    └── soap_generator.py              # 模板填充 + LLM 润色

scripts/
├── build_term_map.py
├── list_missing_edges.py
├── migrate_existing_kg.py
└── verify_migration.py

deploy/
└── requirements.txt

tests/
└── test_connectivity.py
```

## 规范 v0.3 的核心变更（对比当前代码）

1. **数据库**: `term_mapping` 表 → `aliases` 表（含 `language` 字段: zh/en/zh_synonym），新增 `diagnostic_rules` 表和 `inference_log` 表
2. **新模块**: `src/reasoning/diagnostic_matcher.py`（替代 `rule_engine.py`，接口简化为 `match(symptom_nodes) -> list[dict]`）
3. **删除模块**: `path_builder.py`（路径构建逻辑并入 `path_retriever.py`）、`confidence.py`（置信度并入 diagnostic_rules 表）
4. **新数据文件**: `src/reasoning/diagnostic_rules.yaml`（诊断规则定义）
5. **主流程重构**: `ClinicalContext` → `AgentState`（新增 `diagnosis`、`grading_factors`、`path_type` 字段）；`run(subjective, objective)` → `run_pipeline(user_input, demo_mode)`
6. **config.yaml 扩展**: 新增 `graph`、`diagnosis`、`rag`、`grading` 等配置段
7. **repository.py 新增方法**: `resolve_entities()`、`get_grading_indicator()`

---

## 问题 1：变更清单（可迁移 / 要删除 / 要修改 / 要新建）

基于规范，逐文件给出结论（四选一），并解释理由。

| 文件 | 你的判断 | 理由 |
|------|---------|------|
| `src/orchestrator.py` | 改什么？ | |
| `src/knowledge_graph/schema.sql` | 改什么？ | |
| `src/knowledge_graph/term_mapping.py` | 迁/删/改？ | |
| `src/reasoning/rule_engine.py` | 迁/删/改？ | |
| `src/reasoning/path_builder.py` | 迁/删/改？ | |
| `src/reasoning/confidence.py` | 迁/删/改？ | |
| `src/knowledge_graph/repository.py` | 改什么？ | |
| `config.yaml` | 改什么？ | |
| 你认为其他需要改的文件 | ... | |

## 问题 2：模块间依赖顺序

按编译依赖（import 链）列出所有模块的自底向上顺序。即：不依赖任何其他业务模块的基础设施在最下面，orchestrator 在最上面。中间哪些环可能出现循环依赖风险？

## 问题 3：逻辑 vs 数据分离

哪些逻辑依赖临床指南数据，哪些是纯代码逻辑？

请区分以下两类，并给出每类的最佳实施时点：

- **A 类（纯代码逻辑）**: 算法、接口、流程控制——不依赖具体医学内容，可以立即用假数据开发和测试
- **B 类（数据内容）**: 节点名、边关系、诊断规则、术语映射、证据片段——必须从临床指南抽取或手工录入

具体到每个文件/函数属于哪一类？

## 问题 4：图谱规模与路径组合爆炸

单份指南 900 页已超 2000 节点。当前 MVP 基于 SQLite + NetworkX 内存图：

1. 2000-3000 节点时，NetworkX 全图 BFS 遍历和路径枚举的性能是否可接受？
2. 路径组合爆炸（`list_all_paths(u,v)` 可能返回百万条）如何防范？规范已设 `MAX_PATHS=10` + `MAX_LENGTH=4`，是否足够？
3. 什么触发条件（节点数？查询延迟阈值？）决定从 SQLite + NetworkX 迁移到专用图数据库（Neo4j / FalkorDB）？
4. 如果 MVP 阶段就必须容纳 5000+ 节点，是否需要从一开始就设计抽象接口层（如 `GraphBackend`），让 SQLite/NetworkX 和 Neo4j 可互换？

## 问题 5：可测试性设计

规范 §13 定义了 Phase A-B-C-D 的验证方式（`run_pipeline("腰痛")` 打印 SOAP）。你认为每个模块的最小可测试单元是什么？如何设计 mock/fake 数据使得每个模块可以独立测试而不依赖完整管线？

## 问题 6：错误处理策略

LLM 调用失败、FAISS 索引为空、图谱路径无结果、实体未识别时，系统应该优雅降级还是中断？是否需要 fallback 链（如：图谱路径为空时只走向量检索，SOAP 中标注"无图谱证据"）？

## 问题 7：状态持久化与调试

`AgentState` 是否需要序列化到 `inference_log` 表？日志表的设计是否支持调试回放（即：给定同一个输入+log，能否复现推理过程）？

## 问题 8：嵌入模型选择

当前使用 `all-MiniLM-L6-v2`。它对医学文本的语义理解是否足够？是否需要医学领域微调模型（如 BioBERT、PubMedBERT）？需要定量评估标准（如: 在 50 条专家标注的检索 query 上做 recall@10 对比）吗？

## 问题 9：并发安全

Streamlit 是多用户并发的。SQLite 的写锁（WAL 模式是否能缓解？）和 FAISS 的内存索引是否安全？是否需要为每个用户会话重建索引？还是设计读写分离？

## 问题 10：推荐的执行顺序与 Timebox

假设有 2 个工作日（~16 小时）完成 Phase A（纯工程改造，用假数据跑通），你会如何安排实施顺序？

请按优先级分出 3 个批次（P0/P1/P2），每个批次给出：
- 涉及的文件列表
- 每个文件的具体改动（函数签名变更、增删字段等）
- 完成后的可验证里程碑（如：`pytest tests/ 全绿` / `run_pipeline("腰痛") 打印完整 SOAP`）

---

## 附件：ARCHITECTURE_SPEC.md 完整内容

[在此粘贴 d:\cline_control\clinical_reasoning_agent\docs\ARCHITECTURE_SPEC.md 的完整内容]
```

---

## 使用说明

| 步骤 | 动作 |
|------|------|
| 1 | 在 ChatGPT 的新对话中粘贴完整 prompt（含 ARCHITECTURE_SPEC.md 全文） |
| 2 | 在 DeepSeek 的新对话中粘贴完整 prompt（含 ARCHITECTURE_SPEC.md 全文） |
| 3 | 将两家回答分别保存为 `19_chatgpt_response.md` 和 `19_deepseek_response.md` |
| 4 | 可选：在 Gemini 的新对话中同样操作，保存为 `19_gemini_response.md` |
| 5 | 通知我，我来做收敛比对 |

---

### 关于"是否开启新对话"

**是的，强烈建议每个 AI 都开全新对话。** 理由：

1. **避免上下文污染**: 之前的对话有该 AI 之前的回答记忆，可能偏袒自己之前的结论
2. **公平对比**: 每家 AI 看到的起点相同，回答才有可比性
3. **收敛方法论**: 此前 18 轮架构对话一直是"独立提问 → 分别保存 → 我来收敛"的模式，保持一致性