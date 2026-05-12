# 开发日志

> 按阶段记录项目进展，每个阶段包含：做了什么 → 产出物 → 卡住问题 → 下一步。
> 同团队讨论、Cline 协作、已知问题留痕。

---

## 状态看板

| # | 阶段 | 状态 | 日期 | 备注 |
|---|------|------|------|------|
| 0 | 项目骨架初始化 | ✅ | 05-12 | 目录结构、配置文件、README |
| 1 | 配置与数据库基础 | ✅ | 05-12 | config.py, database.py |
| 2 | 知识图谱层 | ✅ | 05-12 | schema, models, repository, path_retriever |
| 3 | 实体抽取器 | ✅ | 05-12 | entity_extractor |
| 4 | 路径检索 | ✅ | 05-12 | graph_searcher (图谱路径) |
| 5 | 向量检索 | ✅ | 05-12 | chunk_searcher (FAISS 向量) |
| 6 | 推理引擎 (reasoning) | ✅ | 05-12 | rule_engine, path_builder, confidence |
| 7 | 生成与编排 | ✅ | 05-12 | soap_generator, orchestrator |
| 8 | 依赖合规性审计 | ✅ | 05-12 | reasoning/ 层合规检查 + project_context.mdc 更新 |
| 9 | Git 初始化 & 开发日志 | ✅ | 05-12 | git init, .gitignore 补全, 开发日志创建 |
| 10 | 数据导入 (下腰痛 KG) | ❌ | — | 下一步 |
| 11 | 端到端集成测试 | ❌ | — | |
| 12 | 演示 Notebook | ❌ | — | |

标记：✅ 完成  🔶 进行中  ⚠️ 卡住  ❌ 未开始

---

## 详细记录

### 阶段 0: 项目骨架初始化

**日期**：2026-05-12

**做了什么**：
- 创建 clinical_reasoning_agent 根目录及完整子目录（docs, data, src, notebooks, tests, deploy 等）
- 创建所有 `__init__.py` 占位文件
- 写入配置模板：config.yaml, .env.example, .gitignore
- 写入 README.md（快速开始指引）和 PROJECT_STRUCTURE.md（目录树 + 准入规则 + 依赖图）

**产出物**：
- 完整目录骨架
- 配置文件模板
- 项目结构文档

**卡住问题**：无

**决策**：
- 空骨架阶段不涉及任何业务逻辑
- `infrastructure/` 按初始化 Briefing 要求创建 5 个文件（database, embedder, vector_store, llm_client, config）

**下一步**：实现 config.py + database.py

---

### 阶段 1: 配置与数据库基础

**日期**：2026-05-12

**做了什么**：
- 实现 `src/infrastructure/config.py`：Config 数据类，从 config.yaml + .env 加载，含 llm_api_key, llm_model, db_path, vector_db_path, embedding_model 等属性
- 实现 `src/infrastructure/database.py`：SQLite 连接池管理，参数化查询 CRUD

**产出物**：
- `config.py` — 配置加载（yaml + 环境变量覆盖）
- `database.py` — 数据库连接管理

**卡住问题**：无

**决策**：
- Config 设计为 dataclass 而非字典，IDE 自动补全更好
- database.py 每次使用时惰性连接（with ... connect）

**下一步**：知识图谱层

---

### 阶段 2: 知识图谱层

**日期**：2026-05-12

**做了什么**：
- schema.sql：节点表 (nodes)、边表 (edges)、别名表 (aliases)，含索引和外键
- models.py：Node, Edge, Alias 数据类，EntityType 枚举
- repository.py：图谱 CRUD（节点/边/别名增删查）、批量导入
- path_retriever.py：递归 CTE 路径查询（有向、可设最大深度、支持双向）

**产出物**：
- 完整知识图谱 CRUD + 路径查询

**卡住问题**：无

**决策**：
- 使用 dataclass 而非 ORM，保持轻量
- path_retriever 递归 CTE 适配 SQLite 的 `WITH RECURSIVE` 语法
- term_mapping.py 处理原文/中文术语对

**下一步**：实体抽取器

---

### 阶段 3: 实体抽取器

**日期**：2026-05-12

**做了什么**：
- 实现 `EntityExtractor` 类，基于词典匹配从症状文本中抽取实体
- 支持 strict / fuzzy 匹配模式
- 支持多词实体（如"anterior cruciate ligament"）

**产出物**：
- entity_extractor.py — 规则/词典实体抽取

**卡住问题**：
- 从 kg_system 迁移 term_map 时有些术语对需要手工确认归属（下腰痛 vs ACL）

**决策**：
- 初期只用 exact + case-insensitive 匹配，后续加拼音模糊
- 术语词典为 JSON 文件嵌入 data/ontology/term_map.json

**下一步**：路径检索（图谱）和向量检索

---

### 阶段 4: 路径检索

**日期**：2026-05-12

**做了什么**：
- GraphSearcher：图谱路径检索封装（调用 path_retriever）
- 支持实体 → 路径 → 路径链 的返回格式

**产出物**：
- graph_searcher.py — 图谱路径检索

**卡住问题**：无

**决策**：
- GraphSearcher 依赖 knowledge_graph.repository 和 path_retriever
- 检索结果格式设计为 `{start_node, path, end_node, depth}`

**下一步**：向量检索

---

### 阶段 5: 向量检索

**日期**：2026-05-12

**做了什么**：
- ChunkSearcher：FAISS 向量检索封装
- 支持文本分块、向量化、近似最近邻搜索
- embedding 通过 embedder.py 调用 sentence-transformers

**产出物**：
- chunk_searcher.py — 向量文献检索

**卡住问题**：
- FAISS 索引持久化路径需匹配 config.yaml 中的 vector_db_path

**决策**：
- ChunkSearcher 初始化时自动检查/创建 FAISS 索引目录
- embedding 模型默认 all-MiniLM-L6-v2，可通过 config 切换

**下一步**：推理引擎

---

### 阶段 6: 推理引擎 (reasoning)

**日期**：2026-05-12

**做了什么**：
- `rule_engine.py`：M-rule 规则匹配引擎。从 JSON 文件（data/ontology 或配置路径）加载规则，支持多条件组合匹配（AND/OR）
- `path_builder.py`：将匹配的规则 + 图谱路径 + 向量结果聚合力结构化推理路径 `ReasoningPath`。含子步骤列表、证据来源分类、覆盖率打分
- `confidence.py`：基于支持规则数、证据覆盖度、路径深度的聚合置信度评分 (`ConfidenceScore`)

**产出物**：
- `src/reasoning/` 完整模块（3 个文件）

**卡住问题**：无

**决策**：
- reasoning 层位于 `infrastructure ← knowledge_graph ← reasoning ← generation` 链中
- rules JSON 通过 Config 路径加载，不硬编码

**下一步**：生成与编排

---

### 阶段 7: 生成与编排

**日期**：2026-05-12

**做了什么**：
- `soap_generator.py`：SOAP 报告生成器，接收 `ReasoningPath` + 患者上下文 → LLM SOAP 报告
- `prompt_templates.py`：SOAP 各段（S/O/A/P）提示词模板
- `orchestrator.py`：主流程编排。接收文本 → entity_extractor → graph_searcher + chunk_searcher → rule_engine → path_builder → soap_generator → 输出

**产出物**：
- 完整管线编排

**卡住问题**：
- orchestrator 的异常处理策略需要权衡：一个子步骤失败时整体失败还是 partial result

**决策**：
- 使用 partial result 模式：非关键失败（如 chunk_searcher 无结果）不影响整体管线，仅在 A 段注明"向量检索无匹配"
- 关键失败（如实体抽取全部失败）直接 raise

**下一步**：依赖合规性审计

---

### 阶段 8: 依赖合规性审计

**日期**：2026-05-12
**Commit**：`1c32d14`

**做了什么**：
- 对 reasoning/ 三文件（rule_engine, path_builder, confidence）逐一做 import 审计
- 搜索全项目对 reasoning 的反向依赖（找到 2 处：orchestrator ✅, soap_generator ✅）
- 更新 `PROJECT_STRUCTURE.md` 模块依赖图（加入 `reasoning` 层）
- 更新 `.cline/rules/project_context.mdc` 同步依赖规则表
- 排除 search 工具的一个假阳性（报告 confidence.py 导入了 extraction 模块，实际是 soap_generator.py 的上下文匹配）

**产出物**：
- 依赖规则文档已同步更新
- 确认零违规

**卡住问题**：
- search 工具返回了上下文匹配的假阳性结果，经人工确认 `confidence.py` 只有 `from src.reasoning.rule_engine import MRule`

**决策**：
- reasoning 层位于 knowledge_graph → reasoning → generation 链中，方向正确
- soap_generator.py 从 reasoning 导 `ReasoningPath` 符合新版依赖规则
- 不需要修改代码

**下一步**：Git 初始化 & 开发日志

---

### 阶段 9: Git 初始化 & 开发日志

**日期**：2026-05-12
**Commit**：`1c32d14`（首 commit，已含全部阶段）

**做了什么**：
- `.gitignore` 补全：追加 `.pytest_cache/`、`data/*.db`（双保险）
- `git init`，确认所有安全文件（不含 .env, .db, __pycache__, .pytest_cache）已纳入暂存
- 首 commit：64 files, 7222 insertions
- 创建本开发日志 `docs/DEVELOPMENT_LOG.md`

**产出物**：
- 本地 git 仓库（master, commit 1c32d14）
- `.gitignore` 完整覆盖敏感/缓存/数据文件
- 本开发日志

**卡住问题**：
- 初始 `.gitignore` 缺少 `.pytest_cache/` 规则（已补）

**决策**：
- .env 中的真实 API key 不进 git（.gitignore 已覆盖）
- `.cline/rules/` 提交到仓库，确保跨机器恢复项目规则
- 每个大阶段结束做一次 git commit + 日志更新

**下一步**：数据导入（下腰痛知识图谱节点和边 → schema.sql）

---

### 远程仓库接入

**日期**：2026-05-13

**做了什么**：
- 验证 SSH 连通性（`ssh -T git@github.com`）→ 成功
- 添加远程仓库：`git@github.com:wastonlyn-arch/guideline-based-lbp-reasoning-agent.git`
- 推送本地 3 个 commit 到 GitHub（92 objects, 123 KiB）
- 本地 master 已跟踪 origin/master

**产出物**：
- GitHub 仓库已同步：`https://github.com/wastonlyn-arch/guideline-based-lbp-reasoning-agent`

**下一步**：阶段 10 — 从 kg_system 白名单迁移下腰痛知识图谱节点和边数据

---

## 待办池

- [ ] 阶段 10: 从 kg_system 白名单迁移下腰痛知识图谱节点和边数据
- [ ] 阶段 11: 端到端集成测试（实体抽取 → 推理 → 生成）
- [ ] 阶段 12: 演示 Notebook
- [ ] 新增: 单元测试覆盖 reaching/rule_engine（规则加载/匹配）
- [ ] 新增: 单元测试覆盖 reaching/confidence（评分聚合）
- [ ] 新增: 单元测试覆盖 orchestrator（编排逻辑）

---

## 编码规则（硬性）— 若有违反，先修规则再写代码

> 以下规则来自项目 Context 文档，超出当前阶段范围，要求各 Agent 在实现阶段 10+ 前先重温这几条：
> 
> - 数据安全：先写 .gitignore 再创建敏感文件
> - 依赖方向：生成层不能反向依赖 extraction/knowledge_graph
> - 模块职责：infrastructure 无业务逻辑；knowledge_graph 不依赖 extraction
> - 每次 git commit 后，必须在 DEVELOPMENT_LOG 中追加或更新对应阶段的记录

---

*最后更新：2026-05-12, commit `1c32d14`*