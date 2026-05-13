# 大模型横评：Claude vs OpenAI vs Gemini vs Grok vs DeepSeek

> 面向 clinical_reasoning_agent 项目开发的多维度对比，支撑多模型融合决策。
> 2026-05-14 编译，价格数据来源：GPTs API 定价明细 + DeepSeek 官方文档。

---

## 目录

1. [总览：项目需求与选择框架](#1-总览项目需求与选择框架)
2. [价格对比（原始数据）](#2-价格对比原始数据)
3. [六维评分矩阵](#3-六维评分矩阵)
4. [各系列深入分析](#4-各系列深入分析)
   - [4.1 Claude](#41-claude)
   - [4.2 OpenAI](#42-openai)
   - [4.3 DeepSeek](#43-deepseek)
   - [4.4 Gemini](#44-gemini)
   - [4.5 Grok](#45-grok)
5. [项目集成建议](#5-项目集成建议)
6. [推荐组合方案](#6-推荐组合方案)

---

## 1. 总览：项目需求与选择框架

### 项目核心需求

| 维度 | 需求 |
|------|------|
| 知识图谱推理 | M-rule 引擎需要辅助验证规则正确性 |
| 实体抽取 | 准确的医学实体识别，不需要私有数据训练 |
| SOAP 报告生成 | 长文本生成，医学专业术语准确 |
| 跨模型交叉验证 | 多模型对同一问题给出意见再收敛（已有 `multi_llm.py`） |
| 代码开发 | 代码完成度、架构设计能力、调试辅助 |

### 选择框架：三个角色 + 一个收敛层

```
primary (主架构师) → 给出完整方案
critic (审查员)    → 找出漏洞、提出替代方案
specialist (领域专家) → 医学知识专项校验
        ↓
收敛模型 (仲裁者) → 综合三家意见做出最终决策
```

---

## 2. 价格对比（原始数据）

### 2.1 Claude 系列（via GPTs API）

| 模型 | 输入/百万Token | 输出/百万Token | 思考模式 |
|------|:---:|:---:|:--------:|
| claude-sonnet-4-6 | $3.00 | $15.00 | ❌ |
| claude-sonnet-4-6-thinking | $3.00 | $15.00 | ✅ |
| claude-opus-4-7 | $5.00 | $25.00 | ❌ |
| claude-opus-4-6 | $5.00 | $25.00 | ❌ |
| claude-haiku-4-5-20251001 | $1.00 | $5.00 | ❌ |

### 2.2 OpenAI 系列（via GPTs API）

| 模型 | 输入/百万Token | 输出/百万Token | 备注 |
|------|:---:|:---:|:------|
| gpt-5.5 | $5.00 | $30.00 | 旗舰 |
| o4-mini | $1.10 | $4.40 | 推理优化 |
| gpt-4o | $2.50 | $10.00 | 均衡 |
| gpt-4o-mini | $0.15 | $0.60 | 低成本 |
| o3-mini | $1.10 | $4.40 | 推理优化 |
| gpt-4.1-mini | $0.40 | $1.60 | 中端 |
| gpt-4.1-nano | $0.10 | $0.40 | 极低成本 |
| text-embedding-3-large | $0.13 | - | 嵌入 |

### 2.3 Gemini 系列（via GPTs API）

| 模型 | 输入/百万Token | 输出/百万Token | 备注 |
|------|:---:|:---:|:------|
| gemini-3.1-pro-preview | $2.00 | $12.00 | 旗舰 |
| gemini-2.5-flash | $0.30 | $2.50 | 高速 |
| gemini-2.5-flash-lite | $0.10 | $0.40 | 极低成本 |

### 2.4 Grok 系列（via GPTs API）

| 模型 | 输入/百万Token | 输出/百万Token | 备注 |
|------|:---:|:---:|:------|
| grok-4 | $3.00 | $15.00 | 旗舰 |
| grok-4-1-fast-non-reasoning | $0.20 | $0.50 | 高速 |
| grok-4-1-fast-reasoning | $0.20 | $0.50 | 推理优化 |
| grok-code-fast-1 | $0.20 | $1.50 | 代码专用 |
| grok-3-mini | $0.30 | $0.50 | 低成本 |

### 2.5 DeepSeek 系列（官方）

| 模型 | 输入（缓存命中） | 输入（未命中） | 输出 |
|------|:---:|:---:|:---:|
| deepseek-v4-flash | 0.02元 | 1元 | 2元 |
| deepseek-v4-pro | 0.025元（2.5折）| 3元（2.5折→12元）| 6元（2.5折→24元）|

> DeepSeek 以人民币计价。按 1 USD ≈ 7.2 RMB 换算：
> - deepseek-v4-flash 输出：2元 ≈ $0.28/百万Token — **极低成本**
> - deepseek-v4-pro 原价输出：24元 ≈ $3.33/百万Token（2.5折期：$0.83）

### 2.6 价格核心结论

```
最便宜：DeepSeek-v4-flash ($0.28 输出) > Gemini 2.5-flash-lite ($0.40)
性价比王：DeepSeek-v4-pro 2.5折期 ($0.83 输出) ≈ gpt-4.1-mini ($1.60)
最贵旗舰：gpt-5.5 ($30.00 输出) > claude-opus ($25.00) > grok-4 ($15.00)
```

---

## 3. 六维评分矩阵

| 维度 | Claude | OpenAI | Gemini | Grok | DeepSeek |
|:-----|:------:|:------:|:------:|:----:|:--------:|
| **💰 价格竞争力** | ★★★☆☆ | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ★★★★★ |
| **🧠 推理深度** | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ★★★★☆ |
| **🏗️ 架构设计** | ★★★★★ | ★★★★★ | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ |
| **📝 代码完成度** | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| **🔬 医学领域** | ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ |
| **🔄 系统集成** | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★★★ |

**评分说明**：
- ★★★★★：该领域已证实有显著优势或极低成本
- ★★★★☆：优秀，可作为主力
- ★★★☆☆：可用但非首选
- ★★☆☆☆：有明显短板

---

## 4. 各系列深入分析

### 4.1 Claude

**推荐模型**：`claude-sonnet-4-6-thinking` / `claude-opus-4-7`

**优势**：
- **推理能力业界顶级**：Sonnet 的链式推理在复杂逻辑任务上表现最优，适合 M-rule 规则校验
- **长上下文处理**：200K token 窗口，适合完整 SOAP 报告分析
- **医学领域对齐**：在医疗文本摘要、诊断推理基准上持续领先
- **谨慎性**：倾向在不确定时给出低置信度标记，与 M-rule 的置信度聚合理念一致

**劣势**：
- 价格中等偏上（$3/$15 vs DeepSeek 的 $0.28）
- OpenAI 兼容 API 可能不支持所有高级功能

**项目定位**：**primary（主架构师）** — 负责复杂的推理链路构建和架构设计

---

### 4.2 OpenAI

**推荐模型**：`gpt-4.1-mini`（中端通用）/ `o4-mini`（推理优化）/ `gpt-4o`（均衡旗舰）

**优势**：
- **ecosystem 最完整**：Function Calling、Structured Output、JSON Mode 等工程特性最成熟
- **代码生成能力顶尖**：尤其在 Python + 软件架构层面，GPT-4 系列在 SWE-bench 持续领先
- **价格梯度最细**：从 nano ($0.10/$0.40) 到 5.5 ($5/$30)，可按场景精确选型
- **嵌入模型成熟**：`text-embedding-3-large` 可与 FAISS 无缝集成

**劣势**：
- 推理链透明度不如 Claude（尤其非 o-series 模型）
- 高端模型价格高

**项目定位**：**critic（审查员）** — 代码审查、架构评估、结构化输出

---

### 4.3 DeepSeek

**推荐模型**：`deepseek-v4-flash`（默认）/ `deepseek-v4-pro`（2.5折期）

**优势**：
- **价格绝对领先**：v4-flash 输出仅 $0.28/百万Token，是 Claude Sonnet 的 1/50
- **1M 上下文**：远超其他所有模型，适合完整病历 + 知识图谱的全量分析
- **思考/非思考双模式**：可用 `deepseek-chat`（非思考）vs `deepseek-reasoner`（思考）对应不同场景
- **FIM 补全（Beta）**：对代码生成场景特有优势
- **中国网络友好**：无 API 访问延迟问题

**劣势**：
- 架构设计能力不如 Claude/OpenAI
- 医学领域准确性需要验证
- 2.5 折优惠有截止期（2026-05-31）

**项目定位**：**convergence（仲裁者）** + **低成本批量调用** — 已有 `multi_llm.py` 默认使用 DeepSeek 做收敛

---

### 4.4 Gemini

**推荐模型**：`gemini-2.5-flash`（高速）/ `gemini-3.1-pro-preview`（旗舰）

**优势**：
- **多模态原生**：原生支持图像、音频输入，未来可扩展 X 光片/影像分析
- **速度优秀**：Flash 系列适合高吞吐量场景
- **性价比良好**：2.5-flash $0.30/$2.50，比 Claude Sonnet 便宜约 6 倍

**劣势**：
- 非 OpenAI 兼容 API 可能需要适配
- 代码质量不如 Claude/OpenAI
- 在复杂推理任务上不够稳定

**项目定位**：**specialist（领域专家）** — 影像解读、快速初筛、高吞吐批量处理

---

### 4.5 Grok

**推荐模型**：`grok-code-fast-1`（代码）/ `grok-4-1-fast-reasoning`（推理）

**优势**：
- **代码专用模型**：`grok-code-fast-1` $0.20/$1.50，性价比极佳
- **Fast 系列速度快**：适合对延迟敏感的迭代开发
- 低端模型成本友好（`grok-3-mini` $0.30/$0.50）

**劣势**：
- 高端模型（grok-4）与 Claude/OpenAI 同价但能力有差距
- 医学领域和架构设计能力未证实
- 生态不如 OpenAI/Claude 成熟

**项目定位**：**辅助代码生成** — 低成本代码编码和 debug

---

## 5. 项目集成建议

### 5.1 当前 `multi_llm.py` 架构兼容性

`multi_llm.py` 已设计为：
- 通过 `ModelConfig` 指定 `provider`、`model`、`api_key_env`、`base_url`
- 所有供应商均通过 OpenAI 兼容 API 接入（部分可能需要特殊适配）
- 支持并发调用（`max_parallel=3`）+ 收敛仲裁

### 5.2 供应商接入清单

| 供应商 | API 兼容性 | 接入方式 | 备注 |
|--------|:---------:|:---------|:-----|
| GPTs API | ✅ OpenAI 兼容 | `base_url=https://api.gptsapi.net/v1` | Claude/OpenAI/Gemini/Grok 全部可用 |
| DeepSeek | ✅ OpenAI 兼容 | `base_url=https://api.deepseek.com/v1` | 直接官方 |
| DeepSeek Anthropic | Anthropic 格式 | `base_url=https://api.deepseek.com/anthropic` | 需额外适配 |

> 由于 GPTs API 统一了 Claude/OpenAI/Gemini/Grok 的接口，项目可只维护两套接入：
> - `gptsapi` → Claude + OpenAI + Gemini + Grok
> - `deepseek` → DeepSeek 官方

### 5.3 场景-模型映射矩阵

| 场景 | 推荐模型 | 备选 | 理由 |
|:-----|:---------|:-----|:-----|
| M-rule 规则校验与推理路径 (primary) | **claude-sonnet-4-6-thinking** | claude-opus-4-7 | 推理深度最高，链式推理透明 |
| 代码架构评审 (critic) | **gpt-4.1-mini** | o4-mini | 代码理解 + 结构化输出成熟 |
| SOAP 报告生成 (generation) | **deepseek-v4-flash** | gpt-4.1-mini | 1M 上下文 + 极低价格，长文档优势 |
| 医学知识专项 (specialist) | **claude-haiku-4-5** | gemini-2.5-flash | 医学领域对齐好，价格可接受 |
| 收敛/仲裁 (convergence) | **deepseek-v4-flash** | gpt-4o | 已有默认配置，低成本 |
| 代码自动补全 (FIM) | **deepseek-v4-flash** | grok-code-fast-1 | FIM 模式独家支持 |
| 高吞吐批量处理 | **gemini-2.5-flash-lite** | gpt-4.1-nano | 速度 + 成本最优 |
| 向量嵌入 | **text-embedding-3-large** | - | FAISS 标准搭配 |

---

## 6. 推荐组合方案

### 方案 A：三模型铁三角（推荐，成本可控）

```
角色         模型                      成本/百万Token(输出)
──────────────────────────────────────────────────────────
primary      claude-sonnet-4-6        $15.00
critic       gpt-4.1-mini             $1.60  
specialist   claude-haiku-4-5         $5.00
────── 收敛 ──────────────────────────────────────────────
convergence  deepseek-v4-flash        ~$0.28 (2元)
```

**适用**：复杂推理 + 代码审核 + 医学知识，覆盖项目核心三需求

### 方案 B：极致性价比（DeepSeek 主力）

```
角色         模型                      成本/百万Token(输出)
──────────────────────────────────────────────────────────
primary      deepseek-v4-pro          ~$0.83 (2.5折)
critic       deepseek-v4-flash        ~$0.28
specialist   gemini-2.5-flash         $2.50
────── 收敛 ──────────────────────────────────────────────
convergence  deepseek-v4-flash        ~$0.28
```

**适用**：研发预算有限、重批量验证、2.5折优惠期内

### 方案 C：全能力旗舰（质量优先）

```
角色         模型                      成本/百万Token(输出)
──────────────────────────────────────────────────────────
primary      claude-opus-4-7          $25.00
critic       gpt-5.5                  $30.00
specialist   gemini-3.1-pro-preview   $12.00
────── 收敛 ──────────────────────────────────────────────
convergence  gpt-4o                   $10.00
```

**适用**：关键决策节点、上线前最终审查

---

## 附录：config.yaml 配置参考

```yaml
multi_model:
  enabled: true
  max_parallel: 3
  timeout: 60

  models:
    primary:
      provider: gptsapi
      model: claude-sonnet-4-6
      api_key_env: GPTS_API_KEY
      base_url: https://api.gptsapi.net/v1
      temperature: 0.3
      max_tokens: 8192
      reasoning_effort: high

    critic:
      provider: gptsapi
      model: gpt-4.1-mini
      api_key_env: GPTS_API_KEY
      base_url: https://api.gptsapi.net/v1
      temperature: 0.5
      max_tokens: 4096

    specialist:
      provider: gptsapi
      model: claude-haiku-4-5-20251001
      api_key_env: GPTS_API_KEY
      base_url: https://api.gptsapi.net/v1
      temperature: 0.2
      max_tokens: 4096

  convergence:
    provider: deepseek
    model: deepseek-v4-flash
    api_key_env: DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com/v1
    temperature: 0.1
    max_tokens: 4096
    reasoning_effort: medium
```

---

## 附录：版本记录

| 日期 | 版本 | 变更 |
|------|:----:|:-----|
| 2026-05-14 | v1.0 | 初版：基于 GPTs API 定价 + DeepSeek 官方文档 |