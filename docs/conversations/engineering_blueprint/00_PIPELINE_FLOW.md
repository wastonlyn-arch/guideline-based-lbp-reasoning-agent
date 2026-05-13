# 工程蓝图多方讨论流水线 — 新工作流

> 取代旧的 `19_engineering_blueprint_prompt.md` 手动粘贴模式。现在：Cline 通过 MultiLLM 自动调用 3 模型，按 primary/critic/convergence 角色分化 prompt，逐批次讨论后收敛。

---

## 流水线架构

```
┌─────────────────────────────────────────────────────────────┐
│                   00_PIPELINE_FLOW.md                        │
│                  （本文档 — 流程说明）                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Batch 1: 核心骨架                                          │
│   ├── 01_roadmap_prompt.md    → 分阶段交付路线图             │
│   ├── 02_priority_prompt.md   → 实现优先级矩阵               │
│   └── 03_data_prompt.md       → 数据工程路线                 │
│                                                             │
│   Batch 2: 质量保障                                          │
│   ├── 04_test_prompt.md       → 测试策略                     │
│   ├── 05_perf_prompt.md       → 性能基线 & 可扩展性           │
│   └── 06_risk_prompt.md       → 风险矩阵                     │
│                                                             │
│   Batch 3: 扩展                                              │
│   ├── 07_multillm_prompt.md   → 多模型集成激活路线            │
│   ├── 08_deploy_prompt.md     → 部署方案                     │
│   └── 09_doc_prompt.md        → 文档与迭代机制               │
│                                                             │
│   收敛产出                                                   │
│   └── 05_ENGINEERING_BLUEPRINT.md  → 最终蓝图文档              │
│                                     （写入 docs/architecture/）│
└─────────────────────────────────────────────────────────────┘
```

## 角色分化说明

每个 prompt 文件内含结构化系统提示词，按角色分化为三段：

| 角色 | 模型 | 职责 | 输出要求 |
|:----|:----|:-----|:---------|
| **primary** | `gemini-2.5-flash` | 架构设计 + 主方案提出者，给出完整方案 | 结构化，带优先级、文件级方案、timebox |
| **critic** | `gpt-4.1-mini` | 审查 primary 方案，找出漏洞/遗漏/风险 | 逐点列出问题 + 替代方案建议 |
| **convergence** | `deepseek-v4-flash` | 对比 primary 和 critic 的差异，仲裁收敛为单一方案 | 逐项说明最终选择并解释理由 |

> **模型选择理由**: Primary 从 claude-sonnet-4-6 切换为 gemini-2.5-flash 可降低约 50 倍成本，而质量在架构设计场景可接受。
>
> **可选项 — Design Review**: 对于关键架构决策，可额外调用 `claude-sonnet-4-6` 做独立评审，预计每月 5-10 次，增加约 $12/月。

## 执行流程

```
Step 1: 由 Cline 读取对应维度的 prompt 文件
Step 2: 用 MultiLLM.ask_all() 同时调用 primary + critic
Step 3: 收集两家回答后，用 MultiLLM.converge() 调用 convergence 仲裁
Step 4: 将 3 家回答 + 收敛结论分别归档
Step 5: 收敛结论写入 docs/conversations/engineering_blueprint/batch{N}/{NN}_convergence.md
Step 6: 所有批次完成后，汇总到 docs/architecture/05_ENGINEERING_BLUEPRINT.md
```

## 批次优先级

| 优先级 | 批次 | 维度 | 启动条件 |
|:------|:-----|:-----|:---------|
| P0 | Batch 1 | 路线图、优先级、数据工程 | 立即启动 |
| P1 | Batch 2 | 测试策略、性能基线、风险矩阵 | Batch 1 收敛完成后 |
| P2 | Batch 3 | 多模型集成、部署、文档管理 | Batch 2 收敛完成后 |

---

> 📅 创建日期: 2026-05-14