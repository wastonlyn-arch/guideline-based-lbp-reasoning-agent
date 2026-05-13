# Project Context — clinical_reasoning_agent

---

## Agent 启动检查清单

当接手此项目时，按以下顺序执行前置操作：

```powershell
# 1. 读机器档案 — 了解硬件/OS/GPU 约束
#    文件：.clinerules/machine_profile.md

# 2. 激活环境
conda activate clinical_reasoning

# 3. 验证环境无 user-site 泄漏
python -c "import sys; assert 'Roaming' not in str(sys.path), 'user-site leakage detected!'"

# 4. 验证核心依赖已安装（首次安装用）
python -c "import openai; import yaml; import faiss; print('All core deps OK')"

# 5. 运行测试确认基线通过
python -m pytest tests/ -v

# 6. 开始实现模块（按依赖顺序，详见下方模块依赖规则）
```

**注意**：首次从 git clone 后，需要手动执行 `conda env create -f environment.yml` 创建环境。之后每次只需 `conda activate clinical_reasoning`。

---

## 项目标识

- **项目名**：clinical_reasoning_agent
- **根目录**：`d:\cline_control\clinical_reasoning_agent`
- **Python 版本**：3.13（conda env: `clinical_reasoning`）
- **包管理**：双锁文件 — `deploy/requirements.txt` (pip lock) + `environment.yml` (conda lock)

---

## 环境策略

### 关键 Windows 规则（必须遵守）

- `PYTHONNOUSERSITE=1` 已在 `clinical_reasoning` 环境设为 conda env config var
- **每次必须先用** `conda activate clinical_reasoning` 激活环境，此环境变量才会生效
- **禁止** 直接使用裸 `pip install`。正确命令：

```powershell
$env:PYTHONNOUSERSITE=1; python -m pip install <package>
```

- **禁止** 使用 `pip install --user`
- 安装包后应验证安装位置：

```powershell
python -c "import <pkg>; print(<pkg>.__file__)"
```

期望前缀：`C:\Users\WINDOWS\.conda\envs\clinical_reasoning\Lib\site-packages\`
如果看到 `AppData\Roaming\Python\...`，说明包装错了位置。

### 常用命令

```powershell
# 激活环境
conda activate clinical_reasoning

# 运行测试
python -m pytest tests/ -v

# 安装/更新依赖
$env:PYTHONNOUSERSITE=1; python -m pip install -r deploy/requirements.txt

# 更新锁文件（添加新依赖后）
conda env export -n clinical_reasoning --no-builds > environment.yml
python -m pip freeze > deploy/requirements.txt

# 验证无 user-site 泄漏
python -c "import sys; print('Roaming' in str(sys.path))"
```

### 从零复现环境

```powershell
conda env create -f environment.yml
conda activate clinical_reasoning
```

---

## 模块依赖规则（严格单向）

```
infrastructure  ←  knowledge_graph  ←  retrieval  ←  generation  ←  orchestrator
                        ↑                ↑
                    extraction       reasoning
```

| 层 | 可依赖 | 禁止依赖 |
|----|--------|---------|
| `infrastructure/` | 无 | 任何其他 src/ 模块 |
| `knowledge_graph/` | infrastructure | extraction, reasoning, retrieval, generation |
| `extraction/` | infrastructure, knowledge_graph | reasoning, retrieval, generation |
| `reasoning/` | infrastructure, knowledge_graph, extraction, retrieval | generation, orchestrator |
| `retrieval/` | infrastructure, knowledge_graph | generation |
| `generation/` | infrastructure, retrieval, reasoning | 直接操作数据库 |
| `orchestrator.py` | 全部 | 无 |

### 各层职责

- `infrastructure/`：可复用的底层工具（database, embedder, vector store, LLM client, config）。**无业务逻辑。**
- `knowledge_graph/`：图谱 schema、models、CRUD、路径查询
- `extraction/`：实体抽取（规则/词典）
- `reasoning/`（v0.3 MVP）：M-rule 规则匹配引擎、可解释推理路径构建、置信度聚合
- `retrieval/`：图谱路径检索 + 向量文献检索
- `generation/`：提示词模板 + LLM 报告生成（消费 reasoning 输出的推理路径）
- `orchestrator.py`：主流程编排

---

## 关键路径

| 用途 | 路径 |
|------|------|
| 测试 | `tests/` |
| 配置模板 | `config.yaml`, `.env.example` |
| 图谱 schema | `src/knowledge_graph/schema.sql` |
| SQLite 数据库 | `data/knowledge_base.db`（自动创建） |
| FAISS 索引 | `data/faiss_index/`（自动创建） |

## Agent 工作流规范

每次用 Agent（如 Cline）完成任务后，必须按以下顺序执行，不可跳过：

1. **更新开发日志**
   - 在 `docs/DEVELOPMENT_LOG.md` 追加记录
   - 内容模板：**做了什么 → 产出物 → 卡住问题 → 决策**
   - 更新状态看板中对应阶段的状态标记

2. **Git 提交**
   - `git add` + `git commit`（commit message 格式：`<scope>: <简短描述>`）
   - 提交前执行检查清单确认无敏感文件

3. **报告完成 + 列出下一步**
   - 输出本次完成内容摘要（含 commit hash）
   - 查看 `DEVELOPMENT_LOG.md` 待办池，列出下一优先级任务及简要计划
   - **等待用户确认后再开始下一项**，禁止自动推进

4. **检查待办池中的"新增"项**
   - 每次完成阶段任务后，查看待办池是否有伴随产生的"新增"子任务（如单元测试、文档补全等）
   - 如有，在报告中一并列出，由用户决定是否优先处理

---

## Git 工作流

### 核心原则：用一条 Git 时间线讲故事

| 资产类型 | 提交时机 | commit 示例 | 理由 |
| ---|---|---|---|
| 🏛️ **架构决策** | 决策验证后立即独立提交，一决策一 commit | `docs(arch): 选择 M-rule 作为推理引擎` | 高价值低频，独立高亮，方便追溯 v0.1→v1.0 演化 |
| 📓 **开发日志** | 当日工作收尾时集中一次提交 | `docs: 补录阶段 7 开发日志` | 内容杂但重要，一天一次安全不污染历史 |
| 🔬 **实验 Notebook (dev/)** | 跑通且结论有效时，清理输出后提交 | `feat(notebook): 验证图谱路径 CTE 查询` | 有保留价值的快照，跑崩的永远不提交 |
| 🎯 **演示 Notebook (demo/)** | 代码和界面稳定后才提交，每次更新审慎 | `docs(demo): 更新 ACL 推理演示场景` | 精选链路，确保可完整运行 |
| ❌ **跑飞的实验** | 永不提交 | — | 只留噪音，污染 Git 历史 |

### Notebook 提交前清理规范

提交 `.ipynb` 前必须执行：
```powershell
# 1. 清除所有单元格输出（防止敏感数据/乱图入库）
python -m jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace notebooks/dev/<name>.ipynb
# 2. 在第一个单元格添加元数据块：
#    ## 实验元数据
#    - 日期：YYYY-MM-DD
#    - 结论：成功 / 失败（原因） / 搁置
#    - 关联文档：docs/xxx.md
```

### 每次 commit 前的检查清单

1. **敏感文件检查**：`git status --short` 确认以下文件未被误 add：
   - `.env`（含真实 API key）
   - `*.db` / `*.sqlite`（数据库文件）
   - `__pycache__` / `*.pyc`（缓存）
   - `.pytest_cache/`（测试缓存）
   - `*.ipynb` 已清除输出
2. **项目标识**：commit message 首行以 scope 开头（如 `docs:`, `feat:`, `fix:`, `refactor:`）

### commit message 格式

```
<scope>: <简短描述>
```

示例：`docs(arch): 选择 M-rule 作为推理引擎` / `docs: 补录阶段 7 开发日志` / `feat(notebook): 验证图谱路径 CTE 查询`

### 远程仓库

- 远程仓库：`git@github.com:wastonlyn-arch/guideline-based-lbp-reasoning-agent.git`
- 已推送 4 个 commit 到 `origin/master`
- 推送前二次确认无敏感文件泄漏

---

## 架构流程

```
用户输入 → 实体抽取 → 图谱检索 → 向量检索 → LLM 生成 → SOAP 报告
                                          ↘ 图谱路径 ↗