# 医学知识图谱抽取 Prompt（v2 — 基于 L0-L8 最终架构）

> **用途**：粘贴到 DeepSeek Web / ChatGPT，上传指南 PDF 后运行
> **架构版本**：v0.3（L0-L8 九层 + 诊断逻辑层 + 干预五分类）

---

我已上传一份临床指南 PDF。请你扮演医学知识图谱构建专家，帮我做结构化抽取。

## 项目背景

我正在构建一个**康复医学推理系统**，使用分层知识图谱解析从发病机制到治疗干预的完整路径。系统以下腰痛/腰椎间盘突出症为核心领域，基于 Stuart McGill 的生物力学范式。

知识图谱内部使用**英文 ID**（如 `Lumbar_Flexion`），通过别名表映射中文。

## 层结构（必须严格遵守）

| 层级 | 名称 | 内容 | 示例 |
|:----:|:----|:-----|:-----|
| **L0** | Behavior / Exposure | 动作、行为模式、暴露 | `Lumbar_Flexion`, `Prolonged_Sitting`, `Repeated_Bending` |
| **L1** | Mechanical Load | 生物力学负荷（按损伤路径细分） | `Flexion_Compression`, `Disc_Shear`, `Repetitive_Low_Load` |
| **L2** | Tissue Pathology | 组织/病理损伤 | `Disc_Herniation`, `Annulus_Tear`, `Facet_Irritation` |
| **L3** | Pathophysiology | 病理生理机制（客观） | `Nerve_Root_Compression`, `Inflammation`, `Instability` |
| **L4** | Symptoms | 主观症状体验 | `Low_Back_Pain`, `Radicular_Pain`, `Numbness` |
| **L5** | Clinical Evidence | 体征/检查（客观） | `SLR_40deg_mild`, `MRI_Disc_Protrusion`, `Flexion_Test_Positive` |
| **L6** | Diagnostic Logic | 模式识别与推理规则 | `Flexion_Pain + SLR+ → Discogenic_Pain` |
| **L7** | Intervention | 干预 | 见下方五分类 |
| **L8** | Outcome | 预后结局 | `Pain_Relief`, `Return_To_Work`, `Recurrence` |

### L7 干预五分类

| 子类 | 含义 | 示例 |
|:----|:-----|:-----|
| `remove_cause` | 消除诱因（第一步） | `Avoid_Flexion`, `Modify_Lifting_Pattern` |
| `exercise_therapy` | 康复训练 | `Core_Stabilization`, `Bird_Dog`, `Curl_Up` |
| `passive_therapy` | 被动治疗 | `Manual_Therapy`, `Traction`, `Heat` |
| `medication` | 药物 | `NSAIDs`, `Muscle_Relaxants` |
| `surgery` | 手术 | `Microdiscectomy`, `Fusion` |

### L1 内部分类（subtype）

| subtype | 含义 | 对应损伤 |
|:--------|:-----|:---------|
| `flexion_compression` | 屈曲+压缩 | Posterior disc herniation |
| `shear` | 剪切力 | Spondylolisthesis |
| `repetitive_low_load` | 重复低负荷 | Disc degeneration / Creep |
| `extension_compression` | 后伸+压缩 | Facet irritation |
| `sustained_posture` | 持续姿势 | Disc nutrition deficit |

## 抽取任务

### 任务 A：抽取实体（Entities）

每个实体必须包含：

```json
{
  "name": "Lumbar_Flexion",
  "layer": "L0",
  "type": "action",
  "subtype": null,
  "description": "腰椎屈曲动作，增加椎间盘后部负荷",
  "negated": false
}
```

**命名规则**：
- PascalCase + 下划线，如 `SLR_40deg_Mild`
- 概念名用英文
- 如果是阴性/否认的描述，设置 `negated: true`（如 `SLR_Negative`）

**类型集合**：action / load / exposure / pathology / mechanism / symptom / sign / test / intervention / outcome / anatomy_variation

### 任务 B：抽取关系（Edges）

每条关系必须包含：

```json
{
  "source": "Lumbar_Flexion",
  "target": "Disc_Posterior_Stress",
  "relation": "increases",
  "confidence": 0.85,
  "evidence": "屈曲动作增加椎间盘后部应力（原文20-50字）"
}
```

**允许的关系类型**（严格限制，只使用这些）：
- `causes` — 因果关系
- `increases` / `decreases` — 增减关系（核心）
- `associated_with` — 统计关联（弱关系）
- `indicated_for` / `contraindicated_for` — 适应/禁忌
- `precedes` — 时间顺序
- `treated_by` — 治疗关系
- `suggests` / `indicates` — 诊断指示关系（用于 L5→L6 或 L4/L5→L2）

**关系方向必须固定**：
- L0 → L1（动作→负荷）
- L1 → L2（负荷→病理）
- L2 → L3（病理→机制）
- L3 → L4（机制→症状）
- L4/L5 → L6（症状/体征→诊断）
- L6 → L7（诊断→干预）
- L7 → L8（干预→预后）

### 任务 C：抽取诊断规则（Diagnostic Rules）

这是本系统的核心差异化组件。提取指南中出现的**模式识别逻辑**：

```json
{
  "pattern": ["Flexion_Pain", "Sitting_Intolerance", "SLR_Positive"],
  "suggests": "Discogenic_Pain",
  "mechanism_path": ["Flexion_Compression", "Annulus_Tear", "Disc_Herniation"],
  "confidence": 0.8,
  "source_ref": "原文章节"
}
```

<!-- 哪些症状+体征的组合 → 推断什么机制 -->

### 任务 D：抽取分级指标（Grading Indicators）

如果指南提到定量分级标准：

```json
{
  "name": "Straight_Leg_Raise",
  "thresholds": [
    {"level": "mild", "range": "30-50°", "node": "SLR_40deg_Mild"},
    {"level": "moderate", "range": "50-70°", "node": "SLR_60deg_Moderate"},
    {"level": "severe", "range": ">70°", "node": "SLR_80deg_Severe"}
  ]
}
```

### 任务 E：标注错误知识（常见误区）

如果指南明确指出某种常见做法是错误的或没有证据支持的，请在关系中标注并在 evidence 中说明。

## 置信度标准

| 分值 | 含义 |
|:----:|:------|
| 0.9 | 明确机制 + 原文多次强调 |
| 0.7 | 明确陈述 |
| 0.5 | 相关性 / 弱证据 |
| <0.4 | 不建议纳入 |

## 输出格式

只输出以下 JSON，不要任何额外文字：

```json
{
  "entities": [...],
  "edges": [...],
  "diagnostic_rules": [...],
  "grading_indicators": [...]
}
```

如果找不到任何信息，返回空列表。

## 抽取优先级

优先抽取：
1. **动作→负荷→病理→症状**（基础机制链）
2. **体征+症状→诊断**（诊断推理规则）
3. **干预→作用/禁忌**（治疗决策）

其次：
4. 影像→病理（弱关系）
5. 非特异性描述

开始提取。
