# MVP 产品形态与最终收敛 — ChatGPT vs DeepSeek 对比（R5-R6）

> **来源**：R5-R6 对话 — 分别向 ChatGPT 和 DeepSeek 完整披露项目现状后，
> 要求给出"在资金有限的真实条件下，如何收缩为可演示的 MVP 产品"的工程建议。
> **日期**：2026-05-14
> **背景**：这是六轮对话的最终章。ChatGPT 从理论驱动，DeepSeek 从工程落地驱动。

---

## 一、产品定位与场景

| 维度 | ChatGPT | DeepSeek |
|:---|:---|:---|
| **场景数量** | 3 类（门诊+教学+研究） | 3 类（教学演示+单人推理+大屏教学） |
| **优先场景** | 临床教学（强推荐优先做） | 临床教学 |
| **核心价值定义** | "让临床决策过程可见" | "外化和加速治疗师的推理过程" |
| **产品本质** | Clinical Reasoning Explanation System | 物理治疗临床推理教学与决策辅助演示 |
| **不是** | 不是 AI 诊断、不是医疗助手、不是 KG 系统 | 不是替代治疗师思考 |
| **目标用户** | 物理治疗师/康复医生/学生 | 物理治疗学生+带教老师+临床治疗师 |

---

## 二、系统架构方案

### 2.1 ChatGPT：4 层重构

```
┌──────────────────────────────┐
│ 1. Input Layer               │
│ (structured + text)          │
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│ 2. Entity + Evidence Layer   │
│ - extraction                 │
│ - KG lookup                 │
│ - RAG evidence              │
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│ 3. Hypothesis Engine        │  ← 核心（必须重写）
│ - generate hypotheses       │
│ - score support/contra      │
│ - rank                      │
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│ 4. Explanation Output Layer  │
│ - SOAP / report            │
│ - evidence map            │
│ - intervention mapping    │
└──────────────────────────────┘
```

**核心观点**：砍掉 L0-L8 作为运行时，重构为 Hypothesis Engine

### 2.2 DeepSeek：3 层单体演化

```
┌─────────────────────────────────────────────┐
│                  浏览器 (Streamlit)            │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  │
│  │ 病例输入 │  │ SOAP报告 │  │ 图谱可视化 │  │
│  └────┬────┘  └────┬─────┘  └─────┬─────┘  │
└───────┼────────────┼──────────────┼────────┘
        │            │              │
        ▼            ▼              ▼
┌─────────────────────────────────────────────┐
│          REST API (FastAPI)                   │
│  /api/extract        /api/soap               │
│  /api/reasoning-path /api/evidence            │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│           Clinical Reasoning Engine           │
│  orchestrator.run_pipeline()                  │
│  ├─ entity_extractor                         │
│  ├─ diagnostic_matcher (M-rule)              │
│  ├─ path_retriever (NetworkX)                │
│  ├─ graph_searcher + chunk_searcher (FAISS)   │
│  └─ soap_generator (template + LLM polish)    │
└─────────────────────────────────────────────┘
```

**核心观点**：保留现有引擎，用 API 层包装，加前端

### 2.3 裁决：采纳 DeepSeek 的单体演化方案

**理由**：

1. 资金有限 → 不应推倒重写
2. 现有 KG 数据是核心资产 → 不应废弃
3. 封装 API 比重构推理架构更可控
4. L0-L8 作为元数据保留，不暴露给用户

---

## 三、技术栈选择

| 层次 | ChatGPT | DeepSeek | 最终选择 |
|:---|:---|:---|:---:|
| **前端** | Streamlit（推荐）或 Next.js | Streamlit 或 HTML+HTMX+Alpine.js | **Streamlit** |
| **后端** | FastAPI | FastAPI | **FastAPI** |
| **推理引擎** | 重构为 Hypothesis Engine | orchestrator.run_pipeline() | **保留现有 orchestrator** |
| **KG 数据库** | SQLite | SQLite + NetworkX 内存图 | **SQLite** |
| **向量检索** | sentence-transformers | FAISS CPU 版 | **FAISS CPU** |
| **LLM** | DeepSeek > OpenAI > Ollama | DeepSeek API 或 Ollama+Qwen2.5 | **DeepSeek API + Ollama 降级** |
| **图谱可视化** | 未指定 | streamlit-agraph 或 Cytoscape.js | **Cytoscape.js (vis-network)** |
| **部署方式** | 未指定 | Docker + Hugging Face Spaces 免费层 | **Docker + HF Spaces** |
| **演示方式** | 未指定 | 本地笔记本或 ngrok | **Stable: HF Spaces / Dev: 本地** |

---

## 四、成本分析对比

| 成本项 | ChatGPT 估价 | DeepSeek 估价 |
|:------|:----------:|:------------:|
| **LLM API（月）** | $5-20 | ¥0-50（Ollama 可归零） |
| **服务器（月）** | $0-10（VPS） | ¥0（HF Spaces 免费） |
| **域名** | 未提 | ¥0（Spaces URL） |
| **数据** | 未提 | ¥0（开源指南） |
| **总月成本** | **$10-30** | **¥0-100** |

---

## 五、工期对比

| 阶段 | ChatGPT | DeepSeek |
|:---|:---:|:---:|
| P0 安全/核心推理 | — | 1 周 |
| Phase 1 核心 MVP | 5-7 天 | 1 周 |
| Phase 2 增强 | 7-10 天 | 1 周 |
| Phase 3 可演示 | 3-5 天 | 1.5 周 |
| 部署 | — | 0.5 周 |
| **总计** | **2-3 周** | **4.5 周（约 1 个月）** |

---

## 六、六轮对比如下对照总表

| 轮次 | 主题 | ChatGPT 核心 | DeepSeek 核心 | 融合采纳 |
|:---:|:---|:-------------|:-------------|:--------:|
| R1 | 初始架构评估 | Hypothesis Engine 范式 | 结构合理，可增强 | 两者各半 |
| R2 | 深化评估 | 概率推理引入 | MDT 状态机 + L1 负荷剂量 | 以 DeepSeek 的 MDT 为主 |
| R3 | 理论模型重建 | MOCR-LBP（5 模块闭环） | MCRM（9 层 + 3 路径） | 以 DeepSeek 的 MCRM 为主 |
| R4 | 重构 vs 继承 | 部分重构 | 继承增强 | 继承为主 + 关键增强 |
| R5 | MVP 产品形态 | Hypothesis Engine 重构 | API 封装 + Streamlit 前端 | API 封装方案 |
| R6 | 最终收敛 | "不是 AI 诊断"定位 | ¥0 成本路径 + HF Spaces | 保留引擎 + Streamlit + 零成本 |

### 六轮综合胜出统计

| 维度 | 胜出方 |
|:---|:------:|
| **推理范式** | 并列（v0 用 DeepSeek 确定性，v1 切 ChatGPT 概率） |
| **理论模型命名** | DeepSeek（MCRM） |
| **架构策略** | DeepSeek（继承增强） |
| **L1 负荷层** | DeepSeek（subtype + 剂量） |
| **Edges 关系** | ChatGPT（contradicts/weakens 延迟至 v1.0） |
| **概率推理** | ChatGPT（延迟至 v1.0） |
| **MDT 动态评估** | DeepSeek（v1.0 方向） |
| **前端方案** | 并列（Streamlit 共识） |
| **部署方案** | DeepSeek（HF Spaces 零成本） |
| **成本控制** | DeepSeek（¥0-100/月路径） |
| **工期估计** | ChatGPT（2-3 周更激进） |
| **产品定义** | 并列（两者共识） |
| **总分** | **DeepSeek 7 : ChatGPT 3（3 项并列）** |

---

## 七、最终产品收敛决议

### 7.1 什么不做

| 被否决方案 | 否决理由 |
|:----------|:--------:|
| 从零重建整个系统 | 有现有 kg_system 资产，不应废弃 |
| L0-L8 运行时重构为 Hypothesis Engine | 复杂度高，资金有限下不可行 |
| 概率推理（贝叶斯） | v1.0 方向，当前 MVP 不需要 |
| MDT 完整动态评估状态机 | 需要真实测试场景才能验证 |
| 采购商业医疗指南数据库 | 免费公开指南已足够 |
| React/Next.js 复杂前端 | 人力成本高，Streamlit 足够 |

### 7.2 什么必须做

| 必须事项 | 优先级 | 说明 |
|:--------|:-----:|:----|
| 红旗征硬编码筛查规则 | P0 | 患者安全 |
| diagnostic_matcher 实现 | P0 | 核心推理 |
| diagnostic_rules 表 | P0 | 规则存储 |
| validated_by 关系类型 | P0 | McKenzie 验证 |
| Streamlit 前端 | P1 | 可演示性 |
| FastAPI 封装 | P1 | 接口标准化 |
| 3 个经典病例预设 | P2 | 演示场景 |
| Docker + HF Spaces 部署 | P2 | 可访问性 |
| Ollama 切换能力 | P3 | 离线降级 |

---

## 8. 决策记录

| 决策 | 内容 | 日期 |
|:---|:----|:----:|
| D-017 | 最终产品定位为"临床推理教学与决策辅助演示"，不定位为"AI 诊断" | 2026-05-14 |
| D-018 | 采用 DeepSeek 的单体演化方案（保留现有引擎 + API 封装 + Streamlit） | 2026-05-14 |
| D-019 | 总月成本控制在 ¥0-100 以内 | 2026-05-14 |
| D-020 | 工期估计 4-5 周（采用融合 P0-P3 方案） | 2026-05-14 |
| D-021 | Hypothesis Engine 范式推迟至 v1.0 | 2026-05-14 |
| D-022 | MDT 动态评估推迟至 v1.0 | 2026-05-14 |