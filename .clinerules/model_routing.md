# Task-Aware Model Routing Rules

> 任务感知模型路由：根据任务类型自动选择模型组合，在性能和成本之间取得最优平衡。
> 策略：日常任务 → DeepSeek-v4-flash（极低成本），架构/核心代码 → 启用三方讨论。

---

## 基本原则

1. **默认走 DeepSeek**：95% 的日常任务（Bug 修复、小功能实现、文档、测试、数据操作）使用 `deepseek-v4-flash` 单模型，够用且极便宜（$0.28/百万Token 输出）
2. **仅在关键节点启用三方讨论**：系统架构设计、核心模块代码编写、跨模块接口定义等高风险决策，启用 primary + critic + convergence 三模型交叉验证
3. **医学推理默认 DeepSeek**：虽然 Claude 医学评分更高，但 DeepSeek 的 1M 上下文窗口对完整病历分析更有优势，且成本仅 1/50

---

## 任务分类与模型选择

| 层级 | 任务标签 | 触发关键词 | 模型策略 | 理由 |
|:-----|:---------|:-----------|:---------|:-----|
| 🟢 **Tier 1** | `daily_dev` | 实现、写代码、修改、添加功能、修复、Bug | **deepseek-v4-flash** 单模型 | 成本 $0.28，1M 上下文，日常够用 |
| 🟢 Tier 1 | `test` | 测试、单元测试、pytest | **deepseek-v4-flash** 单模型 | 测试代码不需要顶级推理 |
| 🟢 Tier 1 | `docs` | 文档、注释、README | **deepseek-v4-flash** 单模型 | 文本生成 DeepSeek 足够 |
| 🟢 Tier 1 | `data` | 数据、SQL、导入、迁移 | **deepseek-v4-flash** 单模型 | 数据操作不需要多模型 |
| 🟢 Tier 1 | `refactor` | 重构、重写、优化 | **deepseek-v4-flash** 单模型 | 简单重构单模型够，大型重构升 Tier 2 |
| 🟡 **Tier 2** | `architecture` | 架构、系统设计、模块拆分、接口定义 | **三方讨论** primary=claude, critic=gpt, convergence=deepseek | 架构错误成本高，值得多模型验证 |
| 🟡 Tier 2 | `core_code` | 核心逻辑、关键算法、推理引擎、规则引擎 | **三方讨论** primary=claude, critic=gpt, convergence=deepseek | 核心模块出错影响整个系统 |
| 🟡 Tier 2 | `large_refactor` | 大规模重构、模块重写、跨层修改 | **三方讨论** primary=claude, critic=gpt, convergence=deepseek | 影响面大，需要多视角审查 |
| 🟡 Tier 2 | `clinical_core` | M-rule 规则设计、推理路径、置信度策略 | **三方讨论** primary=claude, critic=deepseek, convergence=deepseek | 医学推理核心用 Claude，critic 用 DeepSeek 降本 |
| 🔴 **Tier 3** | `final_review` | 上线前审查、发布前、最终检查 | **旗舰组合** primary=claude-opus, critic=gpt-5.5, convergence=gpt-4o | 上线前最高质量标准 |

---

## 路由流程

当你（Cline）接收到任务时，按以下流程执行：

### Step 1: 识别任务类型

1. 扫描用户消息，匹配上表的 `触发关键词`
2. 如果同时匹配多个标签，**以最高 Tier 为准**
   - 例如：同时包含"架构"和"实现" → 走 Tier 2
3. 如果不确定，默认 Tier 1（DeepSeek 单模型），告知用户可升 Tier 2

### Step 2: 选择调用方式

```python
# 🔵 Tier 1 — 单模型 DeepSeek（默认）
from src.infrastructure.llm_client import LLMClient
client = LLMClient()  # 自动用 deepseek-v4-flash
reply = client.chat(messages)

# 🟡 Tier 2 — 三方讨论
from src.infrastructure.multi_llm import MultiLLM
engine = MultiLLM.from_config()  # 从 config.yaml 读取 multi_model 配置
responses = engine.ask_all(
    system_prompts={"primary": "...", "critic": "..."},
    user_prompt="用户需求",
)
final = engine.converge(question="用户需求", responses=responses, role_labels={...})
```

### Step 3: 生成系统提示词

Tier 2 调用时，根据任务类型生成对应的角色提示词：

#### architecture — 架构设计
```
primary: "你是一位资深软件架构师，精通 Python 项目模块拆分和接口设计。
         请基于以下需求给出完整架构方案，包括：模块划分、数据流、接口定义、
         错误处理策略。请同时考虑可扩展性和可测试性。"

critic: "你是一位代码审查专家，擅长发现架构设计中的潜在问题。
        请从以下角度审查方案：循环依赖风险、过度设计、单点故障、
        性能瓶颈、边界情况遗漏。提出至少 2 个替代方案。"
```

#### core_code — 核心代码
```
primary: "你是一位高级 Python 工程师，编写高质量、类型安全的生产代码。
         请实现以下功能，包含：完整的类型注解、错误处理、日志记录、
         边界情况处理。代码应遵循项目的单向模块依赖规则。"

critic: "你是一位代码审查专家，审查以下实现。
        检查点：类型安全、异常处理完整性、性能效率、
        与现有架构的兼容性、测试覆盖建议。"
```

---

## config.yaml 参考（推荐配置）

日常使用 `config.yaml` 默认配置（单模型 DeepSeek），Tier 2 时由 Cline 动态调用 `MultiLLM.from_config()` 加载 `multi_model` 段。

```yaml
# ── 默认配置（日常） ──
llm:
  provider: deepseek
  model: deepseek-v4-flash
  api_key_env: DEEPSEEK_API_KEY
  base_url: https://api.deepseek.com
  temperature: 0.1
  max_tokens: 4096
  reasoning_effort: medium

# ── 三方讨论配置（架构/核心代码时使用） ──
multi_model:
  enabled: false  # 默认关闭，Cline 在 Tier 2 任务时手动启用
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
  convergence:
    provider: deepseek
    model: deepseek-v4-flash
    api_key_env: DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com/v1
    temperature: 0.1
    max_tokens: 4096
    reasoning_effort: medium
  max_parallel: 2
  timeout: 60