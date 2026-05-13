# Batch 1 · MVP → Alpha → Beta → v1.0 各阶段目标、里程碑、时间线 — 讨论原始记录
> 生成时间: 2026-05-14T06:24:38.266451
---
## Phase 1: 发散 — 各角色回答
### critic
```
您好，您提出的“从架构师和审查员的角度，给出工程蓝图规划”的需求较为宽泛。为了更好地满足您的需求，我将基于典型的AI工程项目，结合架构师视角的规划要点和审查员视角的审查重点，给出一份示范性的工程蓝图规划框架，并附带审查要点，供您参考。

---

## 一、工程蓝图规划（架构师视角）

### 1. 项目目标与范围定义
- 明确项目目标（如构建基于知识图谱的智能问答系统）
- 确定项目范围和边界，避免范围蔓延

### 2. 分阶段交付路线图设计
- **阶段1：数据准备与基础设施搭建**
  - 数据采集、清洗、存储设计（数据湖/仓库）
  - 基础硬件资源与计算平台搭建（GPU集群、分布式存储）
  - 里程碑示例：执行`python scripts/import_data.py`后，数据库中节点数达到预期

- **阶段2：知识图谱构建与存储**
  - 实体抽取、关系抽取模块开发
  - 知识图谱存储设计（如Neo4j、JanusGraph）
  - 里程碑示例：运行`kg_build.py`后，查询`MATCH (n) RETURN COUNT(n)`返回节点数>10000

- **阶段3：大语言模型（LLM）集成与微调**
  - 选择合适的LLM模型
  - 微调策略设计（数据格式、训练脚本）
  - 里程碑示例：完成模型微调后，评测指标达到预设阈值

- **阶段4：应用层开发与接口设计**
  - 智能问答接口开发
  - 前端展示与交互设计
  - 里程碑示例：调用API接口返回合理答案，覆盖率达到80%

- **阶段5：测试与部署**
  - 单元测试、集成测试、性能测试
  - 部署自动化脚本与监控方案
  - 里程碑示例：部署后系统稳定运行72小时无重大故障

### 3. 关键设计考虑
- 数据质量保障与版本管理
- 模型更新与回滚机制
- 风险管理与应急预案

---

## 二、审查员视角的审查重点与示例

### 1. 过度乐观
- 是否低估了数据清洗、模型微调的时间和复杂度？
- 是否考虑了多团队协作时的沟通成本？

### 2. 依赖遗漏
- 是否遗漏了数据准备必须先于模型训练？
- 是否遗漏了测试用例设计应先于代码重构？

### 3. 里程碑模糊
- 里程碑是否具体且可验证？例如“完成数据导入”应具体到“执行import_data.py后，数据库节点数达到预期”

### 4. 风险低估
- 是否考虑了LLM幻觉、知识图谱不完整导致的结果不准确风险？
- 是否有数据获取延迟导致进度滞后的应对方案？

### 5. 替代方案
- 如果模型微调失败，是否有使用预训练模型的fallback？
- 如果数据采集延迟，是否有使用公开数据集的parallel track？

---

## 三、总结

以上是一个示范性的工程蓝图规划框架和审查重点。若您能提供具体的分阶段交付路线图方案，我可以基于此进行详细的逐条审查，指出存在的具体问题及改进建议。

期待您的进一步信息！
```
### primary
```
# Clinical Reasoning Agent — MCRM 工程蓝图规划

> 从 v0.3 MVP → v1.0 演示系统的分阶段交付路线图
> 视角：架构师 + 交付审查员 | 单人开发 | 每周 10–15 小时

---

## 1. 阶段划分建议

### 总览表

| 阶段 | 代号 | 目标 | 预计工时 | 里程碑命令 |
|------|------|------|----------|------------|
| P1 | **Code Alignment** | 代码完全对齐架构规范 v0.3 | 16–20h | `python -m pytest tests/smoke/ -v` 全绿 |
| P2 | **Data Engineering** | 下腰痛知识图谱完整导入并可查询 | 24–32h | `python scripts/validate_kg.py --report` 覆盖率 ≥ 85% |
| P3 | **Quality Gate** | 单元测试覆盖率 ≥ 70%，CI 可运行 | 12–16h | `pytest --cov=src --cov-report=term` ≥ 70% |
| P4 | **Extension & Polish** | 多模型支持 + 演示 UI 就绪 | 10–14h | `python demo.py --model gpt-4o` 无异常 |

**总计：62–82 小时 ≈ 5–7 周（@12h/周均值）**

---

### P1 — Code Alignment（代码对齐）⏱ 16–20h

**目标：** 消除代码与 ARCHITECTURE_SPEC.md v0.3 的所有结构性偏差，建立可信的模块边界。

#### 子任务清单

| 优先级 | 文件/模块 | 工作内容 | 估时 |
|--------|-----------|----------|------|
| P1.1 | `schema.sql` | 新增 `term_mappings`、`diagnostic_rules`、`session_context` 表；加 migration script | 2h |
| P1.2 | `term_mapping.py` | 按规范重构为 `TermMapper` 类，接口 `map(raw_term) → NormalizedTerm` | 3h |
| P1.3 | `rule_engine.py` → `diagnostic_matcher.py` | 重命名 + 接口对齐，旧文件保留 deprecation shim 1个版本 | 2h |
| P1.4 | `knowledge_graph.py` | 确认 NetworkX 图加载路径符合规范；增加 `GraphValidator.validate()` | 2h |
| P1.5 | `reasoning_pipeline.py` | 依赖注入重构：`Pipeline(matcher, mapper, graph)` 构造器注入 | 3h |
| P1.6 | `config.py` / `settings.py` | 统一配置入口，env var 优先，YAML fallback | 1h |
| P1.7 | Smoke tests | `tests/smoke/test_pipeline_end2end.py`：输入一个 case，断言有推理输出 | 3h |

**可验证里程碑：**
```bash
python -c "from src.diagnostic_matcher import DiagnosticMatcher; print('OK')"
python -m pytest tests/smoke/ -v --tb=short
```

**前置依赖：** 无（本阶段是其他所有阶段的前置）

---

### P2 — Data Engineering（数据工程）⏱ 24–32h

**目标：** 下腰痛（LBP）临床指南知识图谱完整导入，推理管线可基于真实数据工作。

#### 子任务清单

| 优先级 | 文件/脚本 | 工作内容 | 估时 |
|--------|-----------|----------|------|
| P2.1 | `data/raw/lbp_guidelines/` | 收集/整理指南原始文本（CPG、NICE、临床路径 PDF） | 4h |
| P2.2 | `scripts/parse_guidelines.py` | 结构化解析：症状→诊断规则提取，输出 `lbp_rules.json` | 6h |
| P2.3 | `scripts/build_kg.py` | 将规则 JSON 导入 NetworkX + SQLite，实体去重，关系权重标注 | 6h |
| P2.4 | `scripts/embed_terms.py` | 用 sentence-transformers 对所有术语生成 embedding，写入 FAISS index | 4h |
| P2.5 | `scripts/validate_kg.py` | 验证脚本：节点数、边数、孤立节点、规则覆盖率报告 | 3h |
| P2.6 | `tests/data/test_kg_integrity.py` | 断言图不为空、关键诊断节点存在、FAISS 可检索 | 3h |
| P2.7 | `data/seed/lbp_test_cases.json` | 手写 5–10 个标注测试用例（症状→预期诊断） | 4h |

**可验证里程碑：**
```bash
python scripts/validate_kg.py --report
# 期望输出：节点 ≥ 200, 规则覆盖率 ≥ 85%, 孤立节点 = 0
python -m pytest tests/data/ -v
```

**前置依赖：** P1 全部完成（特别是 `schema.sql` 新表、`knowledge_graph.py` 接口）

---

### P3 — Quality Gate（质量门控）⏱ 12–16h

**目标：** 建立自动化测试体系，确保 v1.0 演示时无重大回归。

#### 子任务清单

| 优先级 | 文件 | 工作内容 | 估时 |
|--------|------|----------|------|
| P3.1 | `tests/unit/test_term_mapper.py` | 参数化测试：边界术语、同义词映射、未知术语处理 | 2h |
| P3.2 | `tests/unit/test_diagnostic_matcher.py` | Mock 图数据，测试规则匹配逻辑的 5 类 case | 3h |
| P
```
---
## Phase 2: 收敛 — 仲裁结果
### 共识
- 工程蓝图应包含分阶段交付路线图
- 每个阶段需要有可验证的里程碑
- 质量保证和测试是关键
- 数据准备和知识图谱构建是核心步骤

### 分歧
- **路线图的具体划分**: 多数=按 P1-P4 四阶段划分（Code Alignment, Data Engineering, Quality Gate, Extension & Polish）... | 少数=未给出具体阶段，仅提供审查框架...
- **审查视角的侧重点**: 多数=primary 的方案隐含了依赖关系与里程碑验证... | 少数=critic 强调了过度乐观、依赖遗漏、里程碑模糊、风险低估等审查点...

### 最终决策
采用 primary 的分阶段路线图（P1-P4），并在每个阶段执行前加入 critic 建议的审查检查点，例如：审查数据准备的时间估算是否合理、是否有 fallback 方案、里程碑是否可量化验证等。同时，在 P3 中强化测试覆盖率和自动化 CI，与 critic 的质量门控一致。

### 风险提示
- P2 数据工程可能低估了指南文本解析和知识图谱构建的复杂度，需准备公开数据集作为并行 track
- P3 质量门控的测试覆盖率目标可能受限于单人开发时间，需优先保证核心逻辑测试
- P4 多模型支持可能存在集成风险，建议先锁定一个稳定模型后再扩展
- 整体工时估算基于每周 10-15 小时，若实际投入不足需调整阶段顺序或范围

### 原始收敛 JSON
```json
{
  "consensus": [
    "工程蓝图应包含分阶段交付路线图",
    "每个阶段需要有可验证的里程碑",
    "质量保证和测试是关键",
    "数据准备和知识图谱构建是核心步骤"
  ],
  "divergences": [
    {
      "topic": "路线图的具体划分",
      "majority_view": "按 P1-P4 四阶段划分（Code Alignment, Data Engineering, Quality Gate, Extension & Polish）",
      "minority_view": "未给出具体阶段，仅提供审查框架",
      "resolution": "采纳 primary 的具体阶段划分，因为其可操作性更强，且与 critic 的审查要点可自然融合。"
    },
    {
      "topic": "审查视角的侧重点",
      "majority_view": "primary 的方案隐含了依赖关系与里程碑验证",
      "minority_view": "critic 强调了过度乐观、依赖遗漏、里程碑模糊、风险低估等审查点",
      "resolution": "在 primary 方案基础上，补充 critic 的风险提示作为风险池，并确保里程碑足够具体。"
    }
  ],
  "final_decision": "采用 primary 的分阶段路线图（P1-P4），并在每个阶段执行前加入 critic 建议的审查检查点，例如：审查数据准备的时间估算是否合理、是否有 fallback 方案、里程碑是否可量化验证等。同时，在 P3 中强化测试覆盖率和自动化 CI，与 critic 的质量门控一致。",
  "risk_notes": [
    "P2 数据工程可能低估了指南文本解析和知识图谱构建的复杂度，需准备公开数据集作为并行 track",
    "P3 质量门控的测试覆盖率目标可能受限于单人开发时间，需优先保证核心逻辑测试",
    "P4 多模型支持可能存在集成风险，建议先锁定一个稳定模型后再扩展",
    "整体工时估算基于每周 10-15 小时，若实际投入不足需调整阶段顺序或范围"
  ]
}
```
