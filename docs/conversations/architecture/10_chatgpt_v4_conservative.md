# ChatGPT 抽取策略建议（v4 — 工程保守版）

> **来源**：ChatGPT（第二次迭代）
> **日期**：2026-05-11
> **核心观点**："7层主结构 + 2个弱扩展维度"，反对"层爆炸"，反对独立 Diagnostic_logic 层

---

## 一、最终结论

**✅ 推荐采用："7层主结构 + 2个弱扩展维度"**

| 层级 | 内容 |
|:----:|:------|
| L0 | 行为 / 动作 |
| L1 | 生物力学负荷（细化） |
| L2 | 组织 / 病理过程 |
| L3 | 神经机制 |
| L4 | 症状（主观） |
| L5 | 体征 / 检查（客观） |
| L6 | 干预（拆分子类型） |
| L7 | 预后 |

**关键点**：
- ❌ 不采用 L1.5 / L3.5 / L4.5 这种"层爆炸方案"
- ❌ 不引入独立 Diagnostic_logic 层（DeepSeek建议 → 不采纳）
- ❌ 不新增独立 Anatomical layer
- ✅ 干预必须内部拆分（强制执行）

---

## 二、逐项决策

### 🔴 决策1：层结构
**✅ A改良版（7层 → 实际8层）**

为什么不选 L0–L8（DeepSeek）？临床医生不会这样思考"现在进入L4.5诊断逻辑层"。真实过程是症状+体征→假设→验证→干预，不是一个显式层，而是推理过程。

### 🔴 决策2：L1 细化
**✅ 必须细化，但不增加层 → 用 type 体系解决**

L1 内部分类：Compression_load / Shear_load / Flexion_moment / Torsional_load / Repetitive_loading / Sustained_loading

### 🔴 决策3：Diagnostic_logic 层
**❌ 不加（明确反对 DeepSeek）**

诊断不是"知识节点"，而是推理行为。如果加 L4.5，会出现"SLR → Diagnostic_logic → Disc_herniation"的错误模式。正确做法是用"边+路径"表达推理，而不是层。

### 🔴 决策4：L3/L4 拆分
**✅ 必须拆（支持 DeepSeek）**

这是康复医学最基本三分法：机制(objective) / 症状(subjective) / 体征(objective test)。

### 🔴 决策5：干预拆分
**✅ 必须拆**

康复治疗第一原则：先去除致病因素，再训练。

### 🟡 决策6：Anatomical Variation
**✅ 保留但不作为层**

作为节点属性，如 `{"name": "Deep_Hip_Socket", "type": "anatomy_variation"}`。

### 🟡 决策7：错误知识
**✅ 必须保留（强烈建议提升优先级）**

必须明确表达：`Sit_up → increases disc load`，`Sit_up → contraindicated_for disc_herniation`。

---

## 三、一句话总结

一个合格的康复推理系统，必须满足：能解释为什么这个动作会痛 → 能判断是哪一类损伤 → 能验证用什么测试确认 → 能干预先停什么再练什么。

🥇 最关键3个决策：L3/L4/L5三分 / 干预拆分(Remove cause vs Exercise) / L1细化但不增加层
❌ 最应该拒绝的：Diagnostic_logic 层
