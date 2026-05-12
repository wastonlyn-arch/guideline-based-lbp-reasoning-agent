# 指南抽取结果 — 四组对比分析

> **来源**：DeepSeek(v1) / ChatGPT(v1) / ChatGPT(v2) / DeepSeek(v2)
> **指南**：McGill《Low Back Disorders》
> **日期**：2026-05-11

---

## 1. 量级概览

| 维度 | DeepSeek v1 | ChatGPT v1 | ChatGPT v2 | **DeepSeek v2** |
|:----:|:-----------:|:----------:|:----------:|:---------------:|
| 实体 | 25 | 22 | 19 | **34** |
| 边 | 20 | 19 | 16 | **24** |
| 诊断规则 | **3** | 1 | 1 | **4** |
| 分级指标 | 0 | 0 | 0 | **1** (SLR分度) |

**DeepSeek v2 在量和深度上都最优**，覆盖了其他三组的所有核心内容，还额外包含了 Central_Sensitization、Big_Three_Exercises、Prone_Extension 等特有概念。

---

## 2. 核心概念覆盖率

| 概念 | D v1 | C v1 | C v2 | **D v2** |
|:----|:----:|:----:|:----:|:--------:|
| L0: Repeated_Flexion | ✅ | ✅ | ✅ | ✅ |
| L0: Prolonged_Sitting | ✅ | ✅ | ✅ | ✅ |
| L0: Sit_Up (错误知识) | ✅ | ❌ | ✅ | ✅ |
| L0: Morning_Flexion | ✅ | ❌ | ❌ | ✅ |
| L1: Flexion_Compression | ✅ | ✅ | ✅ | ✅ |
| L1: Shear_Load | ✅ | ❌ | ❌ | ❌ |
| L1: Repetitive_Low_Load | ✅ | ✅ | ✅ | ✅ |
| L2: Annular_Delamination | ✅ | ❌ | ❌ | ✅ |
| L2: Disc_Herniation | ✅ | ✅ | ✅ | ✅ |
| L2: Spondylolisthesis | ✅ | ❌ | ❌ | ❌ |
| L2: Endplate_Fracture | ✅ | ❌ | ❌ | ✅ |
| L3: Nerve_Root_Compression | ✅ | ✅ | ✅ | ✅ |
| L3: Inflammation | ❌ | ✅ | ✅ | ✅ |
| L3: Central_Sensitization | ❌ | ❌ | ❌ | ✅⭐ |
| L3: Instability | ✅ | ✅ | ❌ | ❌ |
| L4: Radicular_Pain | ✅ | ✅ | ✅ | ✅ |
| L4: Low_Back_Pain | ❌ | ✅ | ✅ | ✅ |
| L4: Sitting_Intolerance | ✅ | ✅ | ✅ | ✅ |
| L4: Morning_Pain_Stiffness | ❌ | ❌ | ❌ | ✅⭐ |
| L5: SLR_Positive | ✅ | ❌ | ✅ | ✅ |
| L5: Prone_Extension_Relief | ❌ | ❌ | ❌ | ✅⭐ |
| L6: Flexion_Intolerance | ❌ | ❌ | ❌ | ✅⭐ |
| L7: Remove_Cause | ✅ | ✅ | ✅ | ✅ |
| L7: Neutral_Spine | ❌ | ✅ | ❌ | ✅ |
| L7: Big_Three_Exercises | ❌ | ❌ | ❌ | ✅⭐ |
| L7: Cat_Camel | ✅ | ❌ | ❌ | ✅ |
| L7: Sit_Up (禁忌) | ✅ | ❌ | ✅ | ✅ |
| L8: Pain_Relief | ✅ | ✅ | ✅ | ✅ |
| L8: Functional_Recovery | ❌ | ✅ | ❌ | ✅ |

> ⭐ = **仅 DeepSeek v2 独有**，但临床价值高

---

## 3. 诊断规则对比

| 规则 | D v1 | C v1 | C v2 | **D v2** |
|:----|:----:|:----:|:----:|:--------:|
| Flexion_Pain + Sitting_Intolerance + SLR+ → Discogenic | ✅ | ✅ | ✅ | ✅(扩展版) |
| Flexion_Pain + Sitting_Intolerance → Flexion_Intolerance | ❌ | ❌ | ❌ | ✅⭐ |
| Radicular_Pain + SLR+ → Nerve_Root_Compression | ❌ | ❌ | ❌ | ✅⭐ |
| Standing_Extension_Relief → Posterior_Disc | ✅ | ❌ | ❌ | ❌(被替代) |
| Morning_Stiffness + Flexion_Pain → Discogenic | ❌ | ❌ | ❌ | ✅ |
| Prone_Extension_Relief → Discogenic | ❌ | ❌ | ❌ | ✅⭐ |

**DeepSeek v2 的诊断规则最完整**，覆盖了从简单（屈曲不耐受）到复杂（俯卧后伸缓解）的推理场景。

---

## 4. 问题标注

### 4.1 命名不一致（需统一）

| 问题 | 出现位置 | 建议统一为 |
|:----|:---------|:----------|
| `Lumbar_Flexion` vs `Lumbar_Flexion_Movement` | Cv1 + Cv2 vs Dv2 | `Lumbar_Flexion` |
| `Discogenic_Pain` 在 L4 vs L6 | Dv1(L4) vs Dv2(L6) | **L6**（诊断逻辑层） |
| `Sitting_Intolerance` 在 L4 vs L5 | Dv1(L4) vs Dv2(L5) | **L4**（症状） |
| `Avoid_Spine_Flexion` vs `Avoid_Flexion` | Dv1 vs Cv2 | 统一为 `Avoid_Spine_Flexion` |
| `Core_Stabilization_Exercise` vs `Core_Stability_Training` | Dv1 vs Cv1 | 统一命名 |

### 4.2 层分配错误

| 实体 | 建议层 | 实际层 | 来源 |
|:----|:------:|:------:|:----:|
| `Sit_Up` (仰卧起坐) | L0（动作） | L7（干预） | Cv2, Dv2 |
| `Sit_Ups` | L0 | L7 | Cv2 |
| `Discogenic_Pain` | **L6**（诊断） | L4（症状） | Dv1, Cv2 |
| `Sitting_Intolerance` | **L4**（症状） | L5（检查） | Dv2 |

### 4.3 缺失的关键链条

| 缺失内容 | 临床意义 | 建议补充 |
|:---------|:---------|:---------|
| **Extension 路径** | 小关节综合征（facets）是常见鉴别诊断 | 增加 Extension_Compression(L1) → Facet_Irritation(L2) |
| **Shear → Spondylolisthesis** | 只有 Dv1 抽取了这条链 | 保留 Dv1 的结果 |
| **Stoop_Lifting → Shear_Load** | 同上 | 保留 Dv1 的结果 |
| **NSAIDs / Medication** | 干预五分类中 medication 完全缺失 | 需人工补充 |
| **Passive Therapy** | 同上 | 需人工补充 |

---

## 5. 推荐合并方案

### 5.1 主数据源：DeepSeek v2

理由：
- 实体最多（34 vs 19-25）
- 诊断规则最完整（4条 vs 1-3条）
- 唯一包含分级指标
- 唯一包含 Central_Sensitization、Big_Three、Prone_Extension 等高价值概念

### 5.2 从 DeepSeek v1 补充

| 内容 | 原因 |
|:----|:----|
| `Shear_Load` → `Spondylolisthesis` 链 | Dv2 漏了这条关键路径 |
| `Stoop_Lifting` | 动作层的补充 |
| `Hip_Hinge_Lifting` → `decreases` → `Flexion_Compression` | 正向干预示例 |
| `Standing_Extension_Pain_Relief` 诊断规则 | 虽然被 Prone_Extension_Relief 替代，但保留参考 |

### 5.3 需要人工补充

| 缺失项 | 工作量 |
|:-------|:------:|
| Extension 路径（Facet syndrome） | 5-10条边 |
| 干预的 medication + passive_therapy 子类 | 3-5个节点 |
| 命名统一（见 §4.1） | 10分钟 |
| Layer 分配修正（见 §4.2） | 5分钟 |

---

## 6. 下一步

1. **你确认合并方案**（以 Dv2 为主 + Dv1 补充）
2. **我执行合并** → 命名统一 + layer 修正 → 生成 `init_data.py`
3. **你审核最终数据** → 确认后开始编码

要我开始合并生成 `init_data.py` 吗？
