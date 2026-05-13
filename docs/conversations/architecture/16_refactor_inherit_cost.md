# 重构/继承/成本分析 — 四家 AI 综合对比（R4）

> **来源**：R4 对话 — 收集 ChatGPT 和 DeepSeek 关于"在现有 kg_system 基础上继承还是从零重构"的建议，
> 加入时间/成本/风险三角考量。
> **日期**：2026-05-14

---

## 1. 继承 vs 重构量表

| 维度 | ChatGPT | DeepSeek |
|:---|:---|:---|
| 总体立场 | **部分重构** | **继承增强** |
| 核心建议 | "在现有架构上做 Hypothesis Engine" | "用你现有的，加东西不拆东西" |
| 继承比例 | ~40%（保留 KG + RAG 基础设施） | ~80%（保留全部，增强核心模块） |
| 重构范围 | L0-L8 层级弱化 → 重新设计 reasoning | 仅新增 diagnostic_matcher + validated_by |
| backbone 策略 | 用你的 data 和 infra，不用你的 architecture | 用你的 architecture，强化薄弱环节 |
| 风险偏好 | 中高（重构可能偏离现有数据模式） | 低（逐步演进，可回退） |

---

## 2. 继承内容表（共识）

| 继承内容 | ChatGPT | DeepSeek | 状态 |
|:--------|:------:|:--------:|:----:|
| SQLite + nodes/edges/chunks 表 | ✅ | ✅ | ✅ 保留 |
| FAISS 索引 + vector store | ✅ | ✅ | ✅ 保留 |
| embedder (sentence-transformers) | ✅ | ✅ | ✅ 保留 |
| LLM client (DeepSeek) | ✅ | ✅ | ✅ 保留 |
| entity_extractor + zh_to_en dict | ✅ | ✅ | ✅ 保留 |
| repository (aliases 映射) | ✅ | ✅ | ✅ 保留 |
| path_retriever (NetworkX) | ✅ (但建议简化) | ✅ (增强非重构) | ✅ 保留 |
| soap_generator (模板) | ✅ | ✅ | ✅ 保留 |
| orchestrator (run_pipeline) | ✅ | ✅ | ✅ 保留 |
| config.yaml | ✅ | ✅ | ✅ 保留 |
| L0-L8 层级 | ✅ (但建议弱化运行时角色) | ✅ (保留为核心) | ✅ 保留为元数据 |

---

## 3. 增强内容（必须在继承基础上新增）

| 新增模块 | ChatGPT | DeepSeek | 优先级 |
|:--------|:------:|:--------:|::----:|
| diagnostic_matcher (L4+L5→L6) | ✅ 必须 | ✅ 必须 | P0 |
| diagnostic_rules 表 | ✅ 必须 | ✅ 必须 | P0 |
| validated_by 关系 | ❌ 未提 | ✅ 必须 | P0 |
| L1 subtype 细分 | ❌ 未提 | ✅ 必须 | P1 |
| 红旗征硬编码 | ✅ 必须 | ✅ 必须 | P0 |
| 负荷剂量概念 | ❌ 未提 | ✅ 必须 | P1 |
| edges contradicts/weakens/supports | ✅ 必须 | ❌ 未提 | 排入 v1.0 |
| 概率推理（贝叶斯） | ✅ 必须 | ❌ 不需要 | 排入 v1.0 |

---

## 4. 成本分析（双方共识）

| 成本项 | ChatGPT 估价 | DeepSeek 估价 |
|:------|:----------:|:------------:|
| **开发时间（MVP）** | 2-4 周 | 6 周（分 P0-P3） |
| **开发人力** | 你（全职）+ Cline（加速） | 你（全职）+ Cline（加速） |
| **DeepSeek API（月）** | ~$5-20 | ¥0-50/月（Ollama 可归零） |
| **医疗指南采购** | 0（用免费公开指南） | 0（免费开源资源） |
| **服务器** | $0（本地） | ¥0（本地或 HF Spaces 免费） |
| **总月成本** | $10-30 | ¥0-100 |

---

## 5. 工期对比（细化到周）

### ChatGPT 方案

| 阶段 | 时间 | 产出 |
|:---|:---:|:----|
| Phase 1: 核心 MVP | 5-7 天 | input→hypothesis→ranking→UI |
| Phase 2: 增强 | 7-10 天 | evidence scoring + KG + contradiction |
| Phase 3: 可演示 | 3-5 天 | case demo + UI 优化 + report |
| **总计** | **2-3 周** | |

### DeepSeek 方案

| 阶段 | 时间 | 产出 |
|:---|:---:|:----|
| P0: 安全+基础重构 | 1 周 | 红旗征 + L5 + L6 |
| P1: API+前端 | 1 周 | FastAPI + Streamlit |
| P2: 证据库填充 | 1 周 | 指南摘要 + FAISS 索引 |
| P3: 集成+部署 | 2.5 周 | 3 个病例调试 + Docker + Spaces |
| **总计** | **~6 周** | |

### 融合工期

| 阶段 | 时间 | 内容 |
|:---|:---:|:----|
| P0: 安全+核心推理 | 1 周 | 红旗征(L6) + diagnostic_rules + validated_by |
| P1: 图谱增强 | 1 周 | L1 subtype + 负荷剂量 + 更多 edges |
| P2: API+前端 | 1 周 | FastAPI 封装 + Streamlit 面板 |
| P3: 证据+部署 | 1-2 周 | FAISS 文献填充 + 3 病例 + Docker 部署 |
| **总计** | **4-5 周** | |

---

## 6. 关键决策点

### 6.1 资金有限下的最优选择

| 决策 | 选择 | 理由 |
|:---|:---|:---|
| API 还是本地 LLM | **先 API，Ollama 并行** | DeepSeek API 非常便宜，Ollama 作为降级备用 |
| 服务器采购 | **不采购，本地+Hugging Face Spaces 免费层** | CPU 足够，无需 GPU |
| 指南数据 | **公开免费指南** | NICE, APTA, McKenzie Institute 均有免费资源 |
| 前端框架 | **Streamlit** | 与 Python 后端天然一体，开发最快 |
| 容器化 | **Docker** | 确保可复现性，同时兼容 HF Spaces 部署 |

### 6.2 风险-收益权衡

| 方案 | 风险 | 收益 | 适合 |
|:---|:---|:---|:---:|
| ChatGPT（2-3 周，部分重构） | 中高（可能偏离现有数据模式） | 高（Hypothesis Engine 架构更灵活） | 资金充足，时间紧 |
| DeepSeek（6 周，继承增强） | 低（逐步演进，可回退） | 中（保留现有投资，可预测性高） | 资金有限，风险规避 |
| **融合方案（4-5 周，继承为主+关键重构）** | **中低** | **高** | ✅ **最终采用** |

---

## 7. 决策记录

| 决策 | 内容 | 日期 |
|:---|:----|:----:|
| D-011 | 采用"继承为主+关键增强"策略，不搞从零重构 | 2026-05-14 |
| D-012 | 工期估计为 4-5 周（融合方案），采用 P0-P3 优先级体系 | 2026-05-14 |
| D-013 | 月成本控制在 ¥0-100 以内（使用 DeepSeek API + 本地/HF Spaces） | 2026-05-14 |
| D-014 | 前端采用 Streamlit，不引入复杂前端框架 | 2026-05-14 |
| D-015 | Docker 化部署，兼容 Hugging Face Spaces 免费层 | 2026-05-14 |
| D-016 | 指南数据使用免费公开资源（NICE/APTA/McKenzie），不采购商业数据库 | 2026-05-14 |