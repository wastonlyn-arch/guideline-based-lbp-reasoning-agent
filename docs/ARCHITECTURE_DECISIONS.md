# Clinical Reasoning Agent — 架构决策记录

> **用途**：记录每个关键架构议题的决策、理由和备选方案，供未来回顾和新人 onboarding。
> **日期**：2026-05-11
> **迁移至**：clinical_reasoning_agent 项目

---

## 决策索引

| # | 议题 | 决策 | 日期 |
|:-:|:----|:----|:----:|
| 1 | KG 存储选型 | SQLite + NetworkX | 2026-05-11 |
| 2 | 实体抽取方案 | 规则 + 词典（演示模式）；JSON 输入（专家模式） | 2026-05-11 |
| 3 | 路径搜索策略 | 层级约束 + 关系白名单 + 深度限制 | 2026-05-11 |
| 4 | 图谱-RAG 融合 | Graph-steered 串行（node_id 关联） | 2026-05-11 |
| 5 | LLM 角色 | 结构化输出 + JSON Schema 校验（Narrator 而非 Reasoner） | 2026-05-11 |
| 6 | 工作流编排 | 函数链 + Notebook 演示 | 2026-05-11 |
| 7 | 证据可信度 | 引用标记 source_ref + confidence | 2026-05-11 |
| 8 | 诊断逻辑层 | ✅ 新增 reasoning/ 模块，L4+L5 → L2/L3 模式匹配 | 2026-05-11 |

---

## 详细决策记录

### 决策 #1：KG 存储选型

**状态**：✅ 已采纳（三家共识）

| 选项 | 优点 | 缺点 |
|:----|:----|:----:|
| **SQLite + NetworkX（选中）** | 零运维，嵌入式，NetworkX 路径算法成熟 | 不适合大规模图谱（>10⁵节点） |
| Neo4j | 原生图查询，适合生产 | 运维复杂，超出 MVP 范围 |

**实现**：`src/knowledge_graph/repository.py` 负责 SQLite CRUD，`path_retriever.py` 使用 NetworkX 做路径查询。

---

### 决策 #2：实体抽取方案

**状态**：✅ 已采纳（双入口架构）

**决策**：
- **专家模式**（DEMO_MODE=false）：接收结构化 JSON 输入，不走 NLP
- **演示模式**（DEMO_MODE=true）：基于词典+正则的轻量规则抽取

**理由**：
- 避免引入 LLM API 的成本和不确定性
- 核心推理链不受 NLP 质量影响
- 面试演示时预定义几个典型输入即可展示效果

**实现**：`src/extraction/entity_extractor.py`

---

### 决策 #3：路径搜索策略

**状态**：✅ 已采纳

| 约束 | 实现 |
|:----|:----:|
| 关系白名单 | mech_path / diag_path / inter_path 三组 |
| 深度限制 | mech_path ≤3, inter_path ≤2 |
| 层级单调性 | `check_layer_validity()` 不回退超过 1 级 |
| 路径类型分治 | 按终点 layer 分流 |
| 循环检测 | NetworkX `all_simple_paths` 自动去重 |

---

### 决策 #8：诊断逻辑层

**状态**：✅ 已采纳（三家均为独家提及，但判断为必须）

**设计**：`src/reasoning/` 模块，包含：
- `diagnostic_matcher.py`：症状+体征 → 模式匹配 → 推断机制
- `diagnostic_rules.yaml`：诊断规则定义（演示场景数据）

**规则表示**：
```json
{
  "pattern": ["Flexion_Pain", "Sitting_Intolerance", "SLR_Positive"],
  "suggests": "Discogenic_Pain",
  "mechanism_path": ["Flexion_Compression", "Annulus_Tear", "Disc_Herniation"],
  "confidence": 0.8
}
```

**匹配算法**：Overlap ≥ 0.6，按 confidence × overlap 排序

**理由**：
- 临床推理的核心是"症状+体征 → 推断机制"的模式识别
- 没有这一层，系统只能回答"这是什么"，不能回答"这是为什么"

---

## 附录：参考来源

- 三家 AI 原始回复：`docs/conversations/architecture/`
- 架构规范全文：`ARCHITECTURE_SPEC.md`
- 三家对比分析：`ARCHITECTURE_CONVERGENCE.md`