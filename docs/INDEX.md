# Clinical Reasoning Agent — 文档导航

> 文档结构按 L0-L4 分层组织，方便快速定位

---

## L0 — 导航入口（本文档）

| 文件 | 位置 | 说明 |
|:----|:----|:----:|
| `INDEX.md` | `docs/` | **本文档** — 文档系统索引 |

---

## L1 — 正式架构产出（决定性文档）

| 文档 | 位置 | 说明 |
|:----|:----|:----|
| `01_CONVERGENCE.md` | `docs/architecture/` | 三家 AI 架构师对比收敛过程 |
| `02_DECISIONS.md` | `docs/architecture/` | 架构决策记录（ADR） |
| `03_SPEC.md` | `docs/architecture/` | **架构规范** — 模块职责、API 签名、配置项、数据流 |
| `05_ENGINEERING_BLUEPRINT.md` | `docs/architecture/` | **工程蓝图** — 分阶段路线图、测试策略、风险矩阵、部署方案、多模型集成 |

---

## L2 — 项目文档

| 文档 | 位置 | 说明 |
|:----|:----|:----|
| `CONTEXT.md` | `docs/project/` | 项目上下文总览、快速入口、核心概念词汇 |
| `DEVELOPMENT_LOG.md` | `docs/project/` | 开发日志与待办管理 |
| `SCENARIOS.md` | `docs/project/` | 场景设计与开发阶段说明 |

---

## L3 — 工具说明

| 文档 | 位置 | 说明 |
|:----|:----|:----|
| `CLINE_CONFIG_GUIDE.md` | `docs/tooling/` | Cline 配置指南 |
| `CLINE_KANBAN_GUIDE.md` | `docs/tooling/` | 看板管理模式指南 |

---

## L4 — 原始对话归档

| 目录 | 位置 | 说明 |
|:----|:----|:----|
| `architecture/` | `docs/conversations/` | 架构相关 AI 对话记录（01-20） |
| `architecture/20_model_cross_eval.md` | `docs/conversations/architecture/` | **多模型横评报告** — 5 家模型价格/性能/架构/代码/功能边界对比 |
| `architecture/prompts/` | `docs/conversations/architecture/` | 工程蓝图提示词等归档 |
| `engineering_blueprint/` | `docs/conversations/` | 工程蓝图 MultiLLM 批处理提示词（batch1-3） |