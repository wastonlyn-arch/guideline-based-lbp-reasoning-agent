# 跨模型架构评估对比 — 综合对比总表（R1-R4）

> **来源**：ChatGPT (v1) + DeepSeek (v1) 两轮独立架构评估
> **日期**：2026-05-14
> **背景**：第一阶段中，两轮对话分别向 ChatGPT 和 DeepSeek 告知项目架构，
> 收集独立反馈后做双向对比分析。

---

## 1. 量级概览

| 维度 | ChatGPT v1 | DeepSeek v1 |
|:----:|:----------:|:-----------:|
| 评估轮次 | 2 轮（初始 + 深化/重构） | 2 轮（初始 + 深化/重构） |
| 核心立场 | Hypothesis Engine 范式（概率/贝叶斯） | MDT 多步状态机范式（确定性/规则） |
| v0 架构认可度 | 中度（认为推理架构需要重构） | 高度（认为结构合理，可增强） |
| 理论模型产出 | MOCR-LBP（5 模块闭环） | MCRM（9 层 + 3 路径） |
| 重构/继承建议 | 两者都有 | 两者都有 |
| 工期估算 | 2-4 周（MVP） | 6 周（MVP） |
| 指南清单 | 6 项 | 10 项 |

---

## 2. 核心分歧分析

### 2.1 推理范式

| 维度 | ChatGPT | DeepSeek |
|:---|:---|:---|
| 当前架构的问题 | 确定性 edges 路径无法表达"似是而非" | 缺少动态评估状态机（如 McKenzie 的"施加伸展→再评估→确认"） |
| 推荐方案 | **Hypothesis Engine**：Top-3 假设 + 支持/反证/不确定性分数 | **MDT 状态机**：McKenzie 三步循环（评估→干预→再评估→分类） |
| 概率需求 | ❗必须引入（贝叶斯或置信度加权） | 现在不需要；edges.confidence 字段已够用 |
| 融合裁决 | v0.4 确定性，v1.0 概率 | v0.4 确定性，v1.0 概率（两者在此一致） |

### 2.2 模型结构

| 维度 | ChatGPT（MOCR-LBP） | DeepSeek（MCRM） |
|:---|:---|:---|
| 层数 | 5 模块（无固定层级） | 9 层（L0-L8） |
| 推理方向 | 闭环（症状→机制→干预→反馈→症状） | 线性+分叉（行为→负荷→损伤→症状→检查→诊断→干预→预后） |
| 中枢层 | ✅ 必须新增中枢整合层 | 未提（不认为是当前痛点） |
| Vicious Cycle | ✅ 核心机制 | 未明确提及 |
| 动态评估（MDT） | 未体现 | ✅ 核心特征 |

### 2.3 Edges 关系类型

| 关系 | ChatGPT 是否认可 | DeepSeek 是否认可 |
|:---|:---:|:---:|
| causes | ✅ | ✅ |
| increases/decreases | ✅ | ✅ |
| treats | ✅ | ✅ |
| contraindicated_for | ✅ | ✅ |
| **contradicts** | ✅ **必须新增**（排除诊断的关键） | ❌ 未提 |
| **weakens/supports** | ✅ **必须新增**（evidence 驱动的推理） | ❌ 未提 |
| **validated_by** | 未明确 | ✅ **必须新增**（McKenzie 动态验证的核心） |
| **precedes** | ✅ 已有可用 | ✅ 已有可用 |
| **prevents** | ✅ 已有可用 | ✅ 已有可用 |
| **indicated_for** | ✅ 已有可用 | ✅ 已有可用 |

### 2.4 L1 负荷层

| 问题 | ChatGPT | DeepSeek |
|:---|:---|:---|
| L1 是否需要内部 subtype | 未提（在 MOCR 中被压缩） | ✅ **必须引入**：Flexion_compression, Shear, Repetitive_low_load, Extension_compression, Sustained_posture |
| 负荷剂量概念 | 未提 | ✅ **必须引入**（总负荷积累的量化） |
| 与 L0 的关系 | 未提 | L0(动作) → L1_subtype(负荷类型) → L2(损伤) |

### 2.5 L5-L6 诊断层

| 问题 | ChatGPT | DeepSeek |
|:---|:---|:---|
| L5 运动反应检查 | ❌ 未提（MOCR 没有"检查-再评估"循环） | ✅ **核心诉求**：动态再评估（如后伸测试→中心化→锁定诊断） |
| L6 诊断逻辑层 | ✅ 支持 | ✅ 支持但建议从"静态规则匹配"改为"动态假设验证" |

### 2.6 干预层

| 问题 | ChatGPT | DeepSeek |
|:---|:---|:---|
| L7 五分类 | ✅ 支持 | ✅ 支持 |
| 祛因优先 | ✅ | ✅（两者一致） |
| Medication 缺失 | ✅ 标注 | ✅ 标注 |
| Passive Therapy 缺失 | 未提 | ✅ 标注 |

---

## 3. 融合方案（第一轮收敛）

### 3.1 立即采纳

| 条目 | 来源 | 优先级 |
|:---|:---|:---:|
| L1 内部 subtype 细分 | DeepSeek | P0 |
| validated_by 关系类型 | DeepSeek | P0 |
| 负荷剂量概念 | DeepSeek | P1 |
| diagnostic_rules 表（症状+体征 → 推断机制） | 两者共识 | P0 |
| 红旗征硬编码筛查 | 两者共识 | P0 |

### 3.2 延迟至 v1.0

| 条目 | 来源 | 原因 |
|:---|:---|:---|
| 概率推理（贝叶斯/置信度） | ChatGPT | 架构复杂度高，当前 MVP 不需要 |
| contradictions/weakens/supports 关系 | ChatGPT | edges 系统扩展，需更多数据支撑 |
| 中枢整合层 | ChatGPT | 模型当前规模无需中枢层 |
| MDT 动态评估状态机 | DeepSeek | 需要真实临床测试场景才值得实现 |

### 3.3 命名决策

ChatGPT 提议的论文命名 **MOCR-LBP** 被否决，改为 DeepSeek 的 **MCRM**（Mechanism-based Clinical Reasoning Model）。

---

## 4. 当前 v0.3 版本状态（基于此融合）

| 模块 | 状态 | 来源 |
|:---|:---|:---|
| L0-L8 层级 | ✅ 已定稿（L6 新增诊断逻辑层） | 两者共识 |
| diagnostic_matcher | ✅ 已设计（见 ARCHITECTURE_SPEC.md §7） | 两者共识 |
| validated_by 关系 | ⏳ 待实现 | DeepSeek |
| L1 subtype | ⏳ 待实现 | DeepSeek |
| contradiction/weakens | 📋 排入 v1.0 | ChatGPT |
| 概率推理 | 📋 排入 v1.0 | ChatGPT |
| 红旗征硬编码 | ✅ 已计划（P0） | 两者共识 |

---

## 5. 决策记录

| 决策 | 决策内容 | 日期 |
|:---|:--------|:----:|
| D-001 | 采用 DeepSeek 的 MCRM 命名而非 ChatGPT 的 MOCR-LBP | 2026-05-11 |
| D-002 | L0-L8 确定为 8 层（L6 新增诊断逻辑层） | 2026-05-11 |
| D-003 | L1 内部按 subtype 细分（5 类机械负荷） | 2026-05-11 |
| D-004 | 新增 validated_by 关系类型 | 2026-05-11 |
| D-005 | 概率推理延迟至 v1.0 | 2026-05-11 |
| D-006 | contradiction/weakens/supports 关系延迟至 v1.0 | 2026-05-11 |