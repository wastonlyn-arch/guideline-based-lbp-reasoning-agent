# DeepSeek 抽取策略建议

> **来源**：DeepSeek 系统架构师
> **日期**：2026-05-11
> **核心观点**：框架"方向正确，但还不够可计算"；最强烈建议增加"Diagnostic logic"层

---

先直接给结论：你的分层框架是"方向正确，但还不够可计算"。
它已经具备临床语义，但如果目标是"推理系统 + 初学者工具书"，需要做三类强化：
1. 层级边界收紧
2. 跨层机制显式化
3. 诊断逻辑结构化

---

## 一、你当前7层结构的逐层评价

### ✅ L0–L2（机制链）— 设计正确，核心优势

优点：完全符合机械致病模型，非常适合因果推理和风险预测。

**⚠ 问题：L1 现在太粗了**

`Disc pressure` 和 `Shear force` 在 McGill 体系里对应不同损伤路径：

| Biomechanical | 对应损伤 |
|:-------------|:---------|
| Flexion + compression | Posterior disc herniation |
| Shear | Spondylolisthesis |
| Repeated low load | Creep / disc degeneration |

**建议**：L1 必须细化为"可区分损伤机制的力学模式"

### ⚠ L3（神经/症状）— 现在是混层

你把神经机制和主观症状放在一起。这在临床语义上OK，但在推理系统里是问题——神经根受压 ≠ 疼痛一定出现。

**建议拆分**：
- L3 = Pathophysiology（机制）：`Nerve_root_compression`
- L4 = Symptoms（体验）：`Radicular_pain`

### ⚠ L4（体征/检查）— 需要拆成两类

直腿抬高（功能性 provocation test）和 MRI（静态结构观察）本质不同。McGill 非常批判静态影像与症状的相关性差。

**建议**：L4 = "Evidence layer"，加 type 字段：provocation / imaging / functional

### ⚠ L5（干预）— 缺一个关键层

缺了 McGill 最强调的一点：**"Remove the cause first"**。

**建议增加 L5a = Exposure / Load modification（去除诱因）**：
- `Avoid flexion in morning`
- `Reduce repeated bending`
- `Modify lifting pattern`

### ⚠ L6（预后）— 定义过于粗糙

Mcgill 体系是 mechanism resolution → load tolerance ↑ → function ↑ → pain ↓。

**建议拆为**：Functional_capacity / Pain_level / Load_tolerance / Recurrence_risk

---

## 二、最关键的缺失：缺"诊断逻辑层"

**Mcgill 核心不是诊断结果，而是 Diagnosis by hypothesis testing**。

**建议新增一层：L4.5 = Diagnostic_logic**

示例：
- `SLR positive + leg pain` → indicates nerve root irritation
- `Flexion pain + sitting worse` → suggests discogenic pain
- `Extension pain` → suggests facet involvement

---

## 三、优化后的推荐结构

| 层级 | 内容 |
|:----:|:----:|
| L0 | Behavior / Exposure |
| L1 | Mechanical loading pattern（细化） |
| L2 | Tissue pathology |
| L3 | Pathophysiology |
| L4 | Symptoms |
| L5 | Clinical evidence（含 provocation/imaging 分类） |
| **L6** | **Diagnostic logic（新增关键层）** |
| L7 | Intervention（Remove cause + Exercise + Surgery） |
| L8 | Outcome |

---

## 四、结论

必改三点（优先级从高到低）：

1. ⭐⭐⭐ **加一层：Diagnostic logic** — 否则只是知识库，不是推理系统
2. ⭐⭐ **拆分 L3（机制）vs L4（症状），L4 检查内部分类**
3. ⭐ **增加"Remove cause"层** — McGill 核心思想
