# Batch 3 · 07_multillm — 讨论原始记录
> 生成时间: 2026-05-14T07:00:41.553968
> 模型: primary=gemini-2.5-flash, critic=gpt-4.1-mini, convergence=deepseek-v4-flash
---
## Phase 1: 发散 — 各角色回答
### critic
1. **复杂度引入过大**  
   - **严重性**：High  
   - **具体说明**：多模型集成固然能带来结果多样性，但在系统层面引入三套模型调用、管理、错误处理和结果融合，极大增加了配置复杂度和代码维护难度。尤其是 latency 叠加，响应时间可能变成单模型的多倍，影响用户体验。  
   - **修改建议**：建议先从单模型或双模型入手，验证多模型融合的实际收益，再评估是否值得引入第三模型。避免一开始就默认启用多模型集成，保持系统简洁，降低调试难度。

2. **MVP 阶段收益不足**  
   - **严重性**：High  
   - **具体说明**：MVP 阶段产品快速迭代，需求和模型策略频繁变动。此时多模型交叉验证带来的收益有限，反而增加了开发和测试成本。单人或小团队开发时，“问三次 AI”耗时成本线性增长，影响开发效率。  
   - **修改建议**：MVP 阶段优先采用单一模型，快速验证核心功能。多模型交叉验证作为后期优化手段，待业务稳定后逐步引入。

3. **边际效益递减未考虑**  
   - **严重性**：Medium  
   - **具体说明**：从 1 个模型到 2 个模型通常带来显著性能提升，但从 2 到 3 个模型的提升往往较小，甚至可能因融合策略不当导致结果不稳定。默认固定启用三模型，缺乏动态调整机制，可能浪费计算资源。  
   - **修改建议**：设计动态模型数量调整机制，根据实际任务复杂度和性能需求，灵活选择 1 至 3 个模型。避免一刀切默认三模型。

4. **维护负担与诊断复杂度高**  
   - **严重性**：High  
   - **具体说明**：多模型意味着多套 API 依赖，模型版本更新、API 变更、价格调整等都会增加维护难度。更严重的是，当多个模型结果发生矛盾时，定位问题根源变得极其困难，调试成本爆炸。  
   - **修改建议**：建立统一的模型管理和监控平台，自动跟踪各模型状态和性能。设计清晰的冲突解决和日志记录机制，方便快速定位问题。必要时允许单独关闭某个模型，降低风险。

---

综上，当前多模型集成激活方案存在较大风险和成本，建议逐步推进，结合业务实际，确保复杂度与收益匹配。

### primary
好的，资深架构师已就位。MCRM 项目的多模型集成策略，从 `optional` 到 `默认启用`，这正是提升系统智能和鲁棒性的关键一步。我们将围绕 Tier 2+ 任务的自动化交叉验证，设计一套兼顾智能、成本与可扩展性的方案。

---

## Batch 3 · 维度 1 — 多模型集成激活路线

### 1. 自动触发策略

**核心思想：** 基于任务的“重要性”和“复杂性”来决定是否启用多模型交叉验证。Tier 2+ 任务通常涉及更深度的推理、更关键的决策，因此需要更高的验证强度。

**触发规则设计：**

1.  **基于任务优先级（Tier 2+ 自动启用，Tier 1 跳过）**
    *   **定义 Tier：** 在 `src/reasoning/` 模块中，为不同的推理任务或函数明确标记其 Tier。
    *   **配置映射：** 在 `config.yaml` 中定义哪些 Tier 自动启用多模型。
    *   **运行时检查：** 在调用推理核心逻辑前，检查当前任务的 Tier。

2.  **基于用户手动标记（PR 描述含 `[multi]` 标签）**
    *   这更多是针对开发/测试阶段的强制触发或特定场景的实验，不作为生产环境的默认自动触发。可以在 CI/CD 流程中用于集成测试。

3.  **默认始终启用但降低 critic 模型等级**
    *   这是一种成本控制策略，而非触发策略。可以作为 Tier 1 任务的“轻量级”多模型模式，即始终启用，但只用一个廉价的 critic 模型进行快速验证。

**具体方案与配置：**

**`config.yaml` 示例：**

```yaml
# config.yaml
multi_model:
  enabled_by_default: false # 默认不启用，由任务Tier决定
  tier_activation_map:
    Tier1:
      enabled: false # 默认Tier1不启用多模型交叉验证，或可配置为 'light' 模式
      mode: single_primary # single_primary, light_multi, deep_multi
    Tier2:
      enabled: true
      mode: standard_multi # standard_multi, deep_multi
    Tier3:
      enabled: true
      mode: deep_multi
  default_mode: single_primary # 当未明确指定Tier时，默认模式
  # ... 其他多模型配置
```

**`src/reasoning/task_manager.py` 或相关模块伪代码：**

```python
# src/reasoning/task_manager.py

from functools import wraps
from typing import Callable, Any
from config import ConfigManager # 假设有一个ConfigManager来加载config.yaml
from multi_llm import MultiLLM # 假设MultiLLM是核心多模型调用接口

config = ConfigManager.get_config()

def multi_model_task(tier: str = "Tier1") -> Callable:
    """
    装饰器，用于标记需要多模型处理的任务，并根据Tier自动启用交叉验证。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            task_config = config.multi_model.tier_activation_map.get(tier, {})
            is_multi_enabled = task_config.get("enabled", False)
            multi_mode = task_config.get("mode", config.multi_model.default_mode)

            if is_multi_enabled:
                print(f"Tier {tier} 任务 '{func.__name__}' 自动启用多模型交叉验证 ({multi_mode} 模式).")
                # 在这里调用 MultiLLM.ask_all 或 MultiLLM.converge
                # 伪代码：将原始任务逻辑包装在多模型调用中
                llm_agent = MultiLLM(mode=multi_mode) # 根据mode初始化MultiLLM
                
                # 假设 func(*args, **kwargs) 返回的是需要LLM处理的prompt或上下文
                # 实际集成可能需要更复杂的包装，例如将任务分解为子步骤，
                # 并将LLM调用嵌入到这些子步骤中。
                
                # 示例：直接将任务的输入作为prompt进行多模型处理
                # 假设 func 的第一个参数是主要输入
                primary_input = args[0] if args else kwargs.get('prompt', 'default_prompt')
                
                # 实际应用中，func 内部可能已经包含了对单个LLM的调用
                # 这里的集成意味着将 func 内部的 LLM 调用替换为 MultiLLM
                # 或者将 func 的输出作为 MultiLLM 的输入进行验证
                
                # 更合理的集成方式：
                # 1. func 内部不直接调用 LLM，而是返回一个“待处理的Prompt”和“上下文”
                # 2. wrapper 接收这些，然后调用 MultiLLM
                # 3. MultiLLM 返回最终决策，wrapper 再将决策传递给 func 的后续逻辑
                
                # 简化示例：假设 func 是一个直接返回 LLM 结果的函数
                # 我们需要的是对 func 内部的 LLM 调用进行替换或增强
                
                # 假设 func 内部会调用一个 `_get_llm_response(prompt)`
                # 我们可以通过依赖注入或上下文管理器来替换这个调用
                
                # 另一种集成方式：将 func 的输出作为 MultiLLM 的输入进行验证
                # 这种方式更接近 cross_validate() 的设计
                
                # 步骤1: 获取 primary 模型的结果
                primary_result = func(*args, **kwargs) # 假设 func 默认使用 primary 模型
                
                # 步骤2: 使用 MultiLLM 进行交叉验证
                # cross_validate 需要原始 prompt 和 primary_result
                # 假设 func 的输入可以被转换为 cross_validate 的 prompt
                validation_prompt = f"请评估以下临床推理结果：\n{primary_result}" # 示例
                
                # 假设 cross_validate 接受 primary_result 和原始上下文
                final_decision, divergences, risks, confidence = llm_agent.cross_validate(
                    original_input=args[0] if args else kwargs, # 原始任务输入
                    primary_output=primary_result,
                    task_type=func.__name__, # 任务类型用于模型路由和提示词选择
                    mode=multi_mode
                )
                
                # 返回交叉验证后的结果
                return final_decision, divergences, risks, confidence
            else:
                print(f"Tier {tier} 任务 '{func.__name__}' 跳过多模型交叉验证.")
                # 直接执行原始任务逻辑，可能内部使用单一 primary 模型
                return func(*args, **kwargs)
        return wrapper
    return decorator

# 示例应用
@multi_model_task(tier="Tier2")
def analyze_patient_case(patient_data: dict, question: str) -> str:
    """
    这是一个Tier2任务，分析患者病例并给出初步临床推理。
    内部可能调用 primary LLM。
    """
    # 假设这里是调用 primary LLM 的逻辑
    # 例如：primary_llm = GPTsAPI.get_model('primary_gpt')
    # result = primary_llm.ask(f"分析病例：{patient_data}，问题：{question}")
    # return result
    
    # 为了演示，直接返回一个模拟结果
    print(f"--- 内部执行 analyze_patient_case ---")
    return f"初步推理结果：患者可能患有XXX，建议进一步检查YYY。基于数据：{patient_data.get('symptoms')}"

# 调用示例
# patient_case = {"symptoms": ["发热", "咳嗽"], "history": "无"}
# final_decision, divergences, risks, confidence = analyze_patient_case(patient_case, "请给出初步诊断和治疗建议。")
# print(f"\n最终决策: {final_decision}")
# print(f"分歧: {divergences}")
# print(f"风险: {risks}")
# print(f"置信度: {confidence}")
```

### 2. primary 模型选择策略

**核心思想：** 针对不同维度的任务，选择在该维度表现最优的模型作为 primary，以最大化初始输出质量。同时，引入自动 fallback 机制增强鲁棒性。

**具体方案：**

1.  **维度-模型映射：**
    *   **架构设计 → Gemini/Grok：** Gemini 在复杂推理、多模态理解方面表现突出，适合架构设计。Grok 以其“叛逆”和创新思维，可能在打破常规、提出新颖架构方案时有优势。可以配置为 Gemini 为主，Grok 为辅或作为特定创新场景的 primary。
    *   **代码实现 → Claude/GPT：** Claude 3 Opus 和 GPT-4 系列在代码生成、理解和重构方面表现卓越，尤其是在遵循复杂指令和生成高质量代码方面。
    *   **测试方案 → GPT-4.1-mini/Claude Sonnet：** 需要细致、全面的思考。GPT-4.1-mini (假设其存在且性能优异) 或 Claude Sonnet 可以在成本和质量之间取得良好平衡，生成详细且覆盖全面的测试用例。
    *   **医学知识查询 → DeepSeek：** 针对中文医学知识，DeepSeek 在中文语境下表现优异，且成本较低。

2.  **固定 primary 还是多 primary：**
    *   不应固定一个 primary。应根据任务的 `task_type` 或 `dimension` 动态选择。
    *   `MultiLLM` 内部应维护一个 `primary_model_map`。

3.  **自动 fallback：**
    *   当 primary 模型调用失败（API 错误、超时、返回空/无效内容）时，自动切换到预设的 fallback 模型重试。
    *   可以配置一个 `fallback_chain`，例如 `[model_A, model_B, model_C]`。

**`config.yaml` 示例：**

```yaml
# config.yaml
multi_model:
  # ...
  primary_model_selection:
    default: gpt-4o # 默认 primary 模型
    by_task_type:
      architecture_design:
        primary: gemini-1.5-pro # 或 grok-1
        fallback_chain: [gpt-4o, claude-3-opus]
      code_implementation:
        primary: claude-3-opus
        fallback_chain: [gpt-4o, deepseek-coder]
      test_plan_generation:
        primary: gpt-4o # 假设 GPT-4.1-mini 尚未稳定
        fallback_chain: [claude-3-sonnet, gemini-1.5-flash]
      medical_query:
        primary: deepseek-chat # 针对中文医学知识
        fallback_chain: [gpt-4o, gemini-1.5-pro]
    # ... 更多任务类型
```

**`multi_llm.py` 伪代码：**

```python
# multi_llm.py

from gpts_api import GPTsAPI # 聚合API
from deepseek_api import DeepSeekAPI # DeepSeek API

class MultiLLM:
    def __init__(self, mode: str = "standard_multi"):
        self.config = ConfigManager.get_config().multi_model
        self.mode = mode
        self.primary_model_map = self.config.primary_model_selection.by_task_type
        self.default_primary = self.config.primary_model_selection.default
        self.api_clients = {
            "gpt": GPTsAPI(), # 聚合了 GPT, Claude, Gemini, Grok
            "deepseek": DeepSeekAPI()
        }
        self._initialize_critics_and_convergers()

    def _get_model_client(self, model_name: str):
        # 根据模型名称判断使用哪个API客户端
        if "deepseek" in model_name:
            return self.api_clients["deepseek"]
        else:
            return self.api_clients["gpt"] # GPTsAPI 聚合了其他模型

    def _get_primary_model_config(self, task_type: str):
        return self.primary_model_map.get(task_type, {
            "primary": self.default_primary,
            "fallback_chain": []
        })

    def _ask_primary(self, prompt: str, task_type: str) -> str:
        model_config = self._get_primary_model_config(task_type)
        primary_model_name = model_config["primary"]
        fallback_chain = model_config["fallback_chain"]

        models_to_try = [primary_model_name] + fallback_chain

        for model_name in models_to_try:
            try:
                client = self._get_model_client(model_name)
                print(f"尝试使用 primary 模型: {model_name} for task_type: {task_type}")
                response = client.ask(model_name, prompt) # 假设 client.ask(model_name, prompt)
                if response:
                    return response
            except Exception as e:
                print(f"Primary model {model_name} failed: {e}. Trying fallback...")
        raise Exception("All primary and fallback models failed to generate a response.")

    def cross_validate(self, original_input: Any, primary_output: str, task_type: str, mode: str):
        # ... (现有 cross_validate 逻辑)
        # 确保 cross_validate 内部调用 _ask_primary 获取 primary_output
        # 或者在外部调用 _ask_primary 后，将结果传入 cross_validate
        
        # 根据 mode (light_multi, standard_multi, deep_multi) 选择 critic/converger 模型
        critic_models = self.config.critic_models.get(mode, [])
        converger_model = self.config.converger_model.get(mode, self.default_primary)
        
        # ... 调用 critic_models 和 converger_model
        
        # 示例：
        # critic_responses = []
        # for critic_model in critic_models:
        #     critic_prompt = self._generate_critic_prompt(original_input, primary_output)
        #     critic_client = self._get_model_client(critic_model)
        #     critic_responses.append(critic_client.ask(critic_model, critic_prompt))
        
        # converger_prompt = self._generate_converger_prompt(original_input, primary_output, critic_responses)
        # converger_client = self._get_model_client(converger_model)
        # final_decision_raw = converger_client.ask(converger_model, converger_prompt)
        
        # ... 解析 final_decision_raw 为 consensus, divergences, risks, final_decision, confidence
        
        return "final_decision", "divergences", "risks", "confidence_score"
```

### 3. 成本控制

**核心思想：** 在保证质量的前提下，通过分级模式、预检和智能模型选择来优化成本。

**具体方案：**

1.  **分级模式（"普通模式 x 2 模型" vs "深度模式 x 3 模型"）**
    *   **`light_multi` (Tier 1/低优先级):** 1 Primary + 1 Low-cost Critic (如 DeepSeek-chat/Gemini-Flash)。用于快速验证，成本最低。
    *   **`standard_multi` (Tier 2/中优先级):** 1 Primary + 2 Mid-cost Critics (如 Claude-Sonnet/GPT-4o) + 1 Converger (GPT-4o/Gemini-Pro)。平衡质量与成本。
    *   **`deep_multi` (Tier 3/高优先级):** 1 Primary + 2-3 High-cost Critics (如 Claude-Opus/GPT-4o) + 1 High-cost Converger (Claude-Opus/GPT-4o)。最高质量，最高成本。
    *   这些模式与 `tier_activation_map` 中的 `mode` 字段对应。

2.  **Pre-flight Token 预算检查：**
    *   在调用任何 LLM 之前，估算输入 Prompt 和预期输出的 Token 数量。
    *   根据当前模式 (`light_multi`, `standard_multi`, `deep_multi`) 和配置的每个模型的 Token 价格，计算预估成本。
    *   与预设的 `max_cost_per_task` 进行比较。如果超出，则降级模式（例如从 `deep_multi` 降到 `standard_multi`），或发出警告/拒绝执行。

**`config.yaml` 示例：**

```yaml
# config.yaml
multi_model:
  # ...
  cost_control:
    max_cost_per_task_usd: 0.5 # 单次任务最大允许成本
    token_cost_map: # 假设的每千Token价格
      gpt-4o:
        input: 0.005
        output: 0.015
      claude-3-opus:
        input: 0.015
        output: 0.075
      claude-3-sonnet:
        input: 0.003
        output: 0.015
      gemini-1.5-pro:
        input: 0.0035
        output: 0.0105
      gemini-1.5-flash:
        input: 0.00035
        output: 0.000525
      deepseek-chat: # 假设人民币价格转换为美元
        input: 0.00028 # 0.2元/M tokens -> 0.028 USD/M tokens -> 0.000028 USD/k tokens
        output: 0.00056 # 0.5元/M tokens -> 0.056 USD/M tokens -> 0.000056 USD/k tokens
    
  model_configs_by_mode:
    light_multi:
      primary: gpt-4o # 仍可使用高质量primary
      critics: [deepseek-chat] # 仅一个廉价critic
      converger: deepseek-chat
    standard_multi:
      primary: gpt-4o
      critics: [claude-3-sonnet, gemini-1.5-flash]
      converger: gpt-4o
    deep_multi:
      primary: claude-3-opus
      critics: [gpt-4o, gemini-1.5-pro, claude-3-opus]
      converger: claude-3-opus
```

**`multi_llm.py` 伪代码 (Token 预算检查):**

```python
# multi_llm.py (在 MultiLLM 类中)

import tiktoken # 假设使用 tiktoken 或其他库进行token估算

class MultiLLM:
    # ... (__init__ 和其他方法)

    def _estimate_tokens(self, text: str, model_name: str) -> int:
        # 这是一个简化示例，实际需要根据模型编码器进行精确估算
        # 对于非 GPT 模型，可能需要使用其他库或API
        try:
            encoding = tiktoken.encoding_for_model(model_name)
            return len(encoding.encode(text))
        except Exception:
            # Fallback for non-tiktoken models or unknown models
            return len(text) // 4 # Rough estimate: 1 token ~ 4 chars

    def _calculate_estimated_cost(self, prompt: str, expected_output_len: int, mode: str) -> float:
        mode_config = self.config.model_configs_by_mode.get(mode)
        if not mode_config:
            raise ValueError(f"Unknown multi-model mode: {mode}")

        total_cost = 0.0
        token_cost_map = self.config.cost_control.token_cost_map

        # Primary model cost
        primary_model = mode_config["primary"]
        input_tokens = self._estimate_tokens(prompt, primary_model)
        output_tokens = expected_output_len # 假设我们能预估输出长度
        total_cost += (input_tokens / 1000 * token_cost_map[primary_model]["input"] +
                       output_tokens / 1000 * token_cost_map[primary_model]["output"])

        # Critic models cost
        for critic_model in mode_config["critics"]:
            # Critic prompt is usually based on original prompt + primary output
            critic_input_tokens = self._estimate_tokens(prompt + primary_output, critic_model) # 简化
            critic_output_tokens = expected_output_len # 简化
            total_cost += (critic_input_tokens / 1000 * token_cost_map[critic_model]["input"] +
                           critic_output_tokens / 1000 * token_cost_map[critic_model]["output"])

        # Converger model cost
        converger_model = mode_config["converger"]
        converger_input_tokens = self._estimate_tokens(prompt + primary_output + "critic_responses_summary", converger_model) # 简化
        converger_output_tokens = expected_output_len # 简化
        total_cost += (converger_input_tokens / 1000 * token_cost_map[converger_model]["input"] +
                       converger_output_tokens / 1000 * token_cost_map[converger_model]["output"])

        return total_cost

    def cross_validate(self, original_input: Any, primary_output: str, task_type: str, mode: str):
        # 1. 估算预期输出长度 (需要根据任务类型和历史数据进行更精确的估算)
        expected_output_len = len(primary_output) * 1.2 # 假设输出会略长

        # 2. 成本预算检查
        estimated_cost = self._calculate_estimated_cost(original_input, expected_output_len, mode)
        max_allowed_cost = self.config.cost_control.max_cost_per_task_usd

        if estimated_cost > max_allowed_cost:
            print(f"警告: 预估成本 ${estimated_cost:.4f} 超出预算 ${max_allowed_cost:.4f}。尝试降级模式...")
            # 尝试降级模式
            if mode == "deep_multi":
                new_mode = "standard_multi"
            elif mode == "standard_multi":
                new_mode = "light_multi"
            else:
                raise Exception(f"成本超出预算且无法降级模式。当前模式: {mode}")
            
            print(f"降级到 {new_mode} 模式。")
            self.mode = new_mode # 更新当前实例的模式
            # 重新计算成本，如果仍超，则继续降级或报错
            estimated_cost = self._calculate_estimated_cost(original_input, expected_output_len, new_mode)
            if estimated_cost > max_allowed_cost:
                raise Exception(f"即使降级到 {new_mode} 模式，成本 ${estimated_cost:.4f} 仍超出预算 ${max_allowed_cost:.4f}。任务中止。")
            
        print(f"预估成本: ${estimated_cost:.4f} (模式: {self.mode})")
        
        # ... 实际的 cross_validate 逻辑继续
        # 确保在实际调用模型时，使用 self.mode 对应的模型配置
```

### 4. 输出整合

**核心思想：** 增强 `cross_validate()` 的输出，提供更全面的决策支持信息，并实现与架构文档的自动化集成。

**当前 `cross_validate()` 返回：`consensus/divergences/risks/final_decision`。**

**增强方案：**

1.  **置信度评分（`confidence_score`）：**
    *   **计算方式：** 可以基于以下因素综合计算：
        *   **共识度（Consensus Strength）：** 参与模型的意见一致性程度。例如，所有 critic 模型都同意 primary 模型的结论，则置信度高。
        *   **分歧程度（Divergence Magnitude）：** 如果存在严重分歧，置信度降低。
        *   **风险评估（Risk Severity）：** 识别出的风险越多/越严重，置信度越低。
        *   **模型自身置信度：** 部分 LLM API 会返回其自身的置信度分数，可以作为参考。
    *   **输出格式：** 0-1 之间的浮点数，或百分比。

2.  **记录“被否决的替代方案”（`discarded_alternatives`）：**
    *   **内容：** 记录 critic 模型提出的与 `final_decision` 不同的、但有一定合理性的替代方案，以及它们被否决的原因（由 converger 模型总结）。
    *   **价值：** 提供决策过程的透明度，有助于后续审计、学习和改进。在某些情况下，被否决的方案可能在特定上下文下仍有价值。

3.  **输出如何自动写入架构文档：**
    *   **结构化输出：** `cross_validate()` 的完整输出应是一个结构化的 JSON 或 Pydantic 模型对象。
    *   **文档生成器集成：**
        *   **API Endpoint：** 提供一个内部 API endpoint (例如 `/docs/update_reasoning_log`)，接收 `cross_validate` 的结构化输出。
        *   **Markdown/RST 转换：** 内部服务将 JSON 转换为预定义的 Markdown 或 reStructuredText 格式。
        *   **版本控制：** 将生成的文档文件提交到 Git 仓库（例如 `docs/reasoning_logs/`），与代码版本保持一致。
        *   **触发机制：** 在关键的 Tier 2+ 任务完成后，如果 `final_decision` 影响到架构或关键设计，则自动触发文档更新。

**`multi_llm.py` `cross_validate()` 增强伪代码：**

```python
# multi_llm.py (在 MultiLLM 类中)

import json
from pydantic import BaseModel # 假设使用 Pydantic 定义输出结构

class MultiModelDecision(BaseModel):
    task_id: str # 任务唯一ID
    task_type: str
    original_input: Any
    primary_output: str
    final_decision: str
    consensus: str # 总结共识
    divergences: list[dict] # 详细分歧点，包含模型、观点、理由
    risks: list[str] # 识别出的风险
    confidence_score: float # 置信度评分 (0.0 - 1.0)
    discarded_alternatives: list[dict] # 被否决的替代方案及其理由
    timestamp: str
    multi_model_mode: str # 使用的模式 (light_multi, standard_multi, deep_multi)
    models_used: dict # 记录每个角色使用的具体模型

class MultiLLM:
    # ...

    def cross_validate(self, original_input: Any, primary_output: str, task_type: str, mode: str) -> MultiModelDecision:
        # ... (现有逻辑，包括调用 primary, critics, converger)

        # 假设我们已经收集了所有 critic 模型的响应和 converger 的最终决策
        # critic_responses = [...]
        # converger_raw_output = "..." # converger 模型的原始输出，需要解析

        # --- 解析 converger_raw_output ---
        # converger 模型需要被设计成输出一个结构化的 JSON 字符串
        # 包含 final_decision, consensus, divergences, risks, confidence, discarded_alternatives
        
        # 示例解析 (实际需要更健壮的解析逻辑)
        try:
            parsed_converger_output = json.loads(converger_raw_output)
            final_decision = parsed_converger_output.get("final_decision", "N/A")
            consensus = parsed_converger_output.get("consensus", "N/A")
            divergences = parsed_converger_output.get("divergences", [])
            risks = parsed_converger_output.get("risks", [])
            raw_confidence = parsed_converger_output.get("confidence", 0.0)
            discarded_alternatives = parsed_converger_output.get("discarded_alternatives", [])
        except json.JSONDecodeError:
            print("警告: Converger 模型输出非JSON格式，进行回退处理。")
            final_decision = converger_raw_output # 回退到原始输出
            consensus = "部分共识"
            divergences = [{"model": "N/A", "view": "无法解析", "reason": "Converger输出格式错误"}]
            risks = ["Converger输出格式错误"]
            raw_confidence = 0.3 # 默认低置信度
            discarded_alternatives = []

        # --- 计算最终置信度分数 ---
        # 结合 converger 自身的置信度、共识度、分歧和风险
        # 这是一个示例计算，实际可能需要更复杂的加权逻辑
        final_confidence_score = raw_confidence * (1 - len(divergences) * 0.1) # 简单扣分
        if len(risks) > 0:
            final_confidence_score *= 0.8 # 有风险则降低置信度
        final_confidence_score = max(0.0, min(1.0, final_confidence_score)) # 确保在0-1之间

        # --- 记录使用的模型 ---
        models_used = {
            "primary": self._get_primary_model_config(task_type)["primary"],
            "critics": self.config.model_configs_by_mode[mode]["critics"],
            "converger": self.config.model_configs_by_mode[mode]["converger"]
        }

        decision_output = MultiModelDecision(
            task_id=str(uuid.uuid4()), # 生成唯一任务ID
            task_type=task_type,
            original_input=original_input,
            primary_output=primary_output,
            final_decision=final_decision,
            consensus=consensus,
            divergences=divergences,
            risks=risks,
            confidence_score=final_confidence_score,
            discarded_alternatives=discarded_alternatives,
            timestamp=

---
## Phase 2: 收敛 — final_decision
采用primary提出的分层自动触发策略作为框架，但融合critic的谨慎建议：默认启用范围限定为Tier2+任务，初始默认模式为light_multi（1 primary + 1 low-cost critic），并支持成本预算检查和自动降级。MVP阶段允许通过配置完全关闭多模型（保持optional），待业务稳定后逐步提升默认强度。这样既实现了“从optional到默认启用”的路线，又通过分级控制和渐进式部署控制了复杂度和成本。

### consensus
- 多模型交叉验证能提升结果多样性和鲁棒性，但增加系统复杂度、成本及维护难度。
- 需要控制成本和复杂度，避免一刀切默认启用。
- 应采取分阶段、分层的策略逐步引入多模型集成。

### divergences
- 是否默认启用多模型交叉验证: majority=primary主张默认启用，但基于任务层级（Tier）进行自动触发，并辅以成本控制与降级机制。 / minority=critic认为当前默认启用的风险和成本过高，建议先单模型验证效果，MVP阶段不应启用，后期再逐步引入。 → 折中方案：默认启用多模型，但仅针对Tier2+任务（优先级较高）；Tier1任务保持单模型（optional）。同时实现动态成本预算检查和模式降级（light_

### risk_notes
- 多模型调用可能显著增加响应延迟，需设计异步或缓存机制缓解。
- 成本预算检查中token估算可能不准确，需预留余量或采用实时监控。
- 模型API依赖增多，单个模型故障可能导致整体流程受阻，需完善fallback和重试策略。
- 不同模型的输出融合（converger）可能引入新的不一致性，需迭代优化提示词和解析逻辑。