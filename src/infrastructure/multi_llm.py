"""
多模型并发调用引擎 — 同时调用多个 LLM 并收集结果。

用法:
    from src.infrastructure.multi_llm import MultiLLM
    engine = MultiLLM.from_config()
    
    responses = engine.ask_all(
        system_prompts={
            "primary": "你是架构师，给出完整方案",
            "critic": "你是审查员，找出方案漏洞",
        },
        user_prompt="如何设计临床诊断规则引擎？",
    )
    # responses = {"primary": "...", "critic": "..."}
"""

import concurrent.futures
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from src.infrastructure.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """单个模型在交叉验证中的配置。"""

    provider: str = "gptsapi"
    model: str = "claude-sonnet-4-6"
    api_key_env: str = "GPTS_API_KEY"
    base_url: str = "https://api.gptsapi.net/v1"
    temperature: float = 0.5
    max_tokens: int = 4096
    reasoning_effort: str = "medium"


class MultiLLM:
    """多模型并发调用引擎。

    同时调用多个不同厂商的 LLM，收集各自回答用于交叉验证。
    """

    def __init__(
        self,
        models: dict[str, ModelConfig],
        convergence_config: ModelConfig,
        max_parallel: int = 3,
        timeout: int = 30,
    ):
        """
        Args:
            models: 角色名 → ModelConfig，例如
                    {"primary": ModelConfig(...), "critic": ModelConfig(...)}
            convergence_config: 收敛阶段使用的模型配置
            max_parallel: 最大并发数
            timeout: 每个模型调用的超时秒数
        """
        self._max_parallel = max_parallel
        self._timeout = timeout

        # 为每个角色创建 LLMClient 实例
        self._clients: dict[str, LLMClient] = {}
        for role, cfg in models.items():
            api_key = os.environ.get(cfg.api_key_env, "")
            self._clients[role] = LLMClient(
                api_key=api_key,
                model=cfg.model,
                base_url=cfg.base_url,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                reasoning_effort=cfg.reasoning_effort,
            )

        # 收敛模型
        conv_cfg = convergence_config
        conv_api_key = os.environ.get(conv_cfg.api_key_env, "")
        self._convergence_client = LLMClient(
            api_key=conv_api_key,
            model=conv_cfg.model,
            base_url=conv_cfg.base_url,
            temperature=conv_cfg.temperature,
            max_tokens=conv_cfg.max_tokens,
            reasoning_effort=conv_cfg.reasoning_effort,
        )

        # 保存角色名列表
        self._roles = list(self._clients.keys())

    @classmethod
    def from_config(cls, config: Optional[dict] = None):
        """从配置字典创建 MultiLLM 实例。

        Args:
            config: 配置字典，格式同 config.yaml:multi_model
                    如果为 None，则从 Config 自动加载。

        用法:
            # 从 config.yaml 自动加载
            engine = MultiLLM.from_config()

            # 或传入自定义配置
            engine = MultiLLM.from_config({
                "enabled": True,
                "models": {
                    "primary": {...},
                    "critic": {...},
                },
                "convergence": {...},
                "max_parallel": 3,
                "timeout": 30,
            })
        """
        if config is None:
            from src.infrastructure.config import Config
            cfg = Config()
            config = cfg.multi_model_config()

        models = {}
        for role, mcfg in config.get("models", {}).items():
            models[role] = ModelConfig(
                provider=mcfg.get("provider", "gptsapi"),
                model=mcfg.get("model", "claude-sonnet-4-6"),
                api_key_env=mcfg.get("api_key_env", "GPTS_API_KEY"),
                base_url=mcfg.get("base_url", "https://api.gptsapi.net/v1"),
                temperature=mcfg.get("temperature", 0.5),
                max_tokens=mcfg.get("max_tokens", 4096),
                reasoning_effort=mcfg.get("reasoning_effort", "medium"),
            )

        conv = config.get("convergence", {})
        convergence_config = ModelConfig(
            provider=conv.get("provider", "deepseek"),
            model=conv.get("model", "deepseek-v4-flash"),
            api_key_env=conv.get("api_key_env", "DEEPSEEK_API_KEY"),
            base_url=conv.get("base_url", "https://api.deepseek.com"),
            temperature=conv.get("temperature", 0.1),
            max_tokens=conv.get("max_tokens", 4096),
            reasoning_effort=conv.get("reasoning_effort", "medium"),
        )

        return cls(
            models=models,
            convergence_config=convergence_config,
            max_parallel=config.get("max_parallel", 3),
            timeout=config.get("timeout", 30),
        )

    def ask_all(
        self,
        system_prompts: dict[str, str],
        user_prompt: str,
    ) -> dict[str, str]:
        """并发向所有角色模型提问，返回各自回答。

        Args:
            system_prompts: 角色 → 系统提示词，例如
                            {"primary": "你是架构师", "critic": "你是审查员"}
                            未指定的角色使用空字符串。
            user_prompt: 用户问题（所有模型共享）

        Returns:
            {"primary": "回答文本", "critic": "回答文本", ...}

        Raises:
            RuntimeError: 所有模型全部失败时抛出
        """
        results: dict[str, str] = {}

        def _ask(role: str) -> tuple[str, str]:
            """单个模型调用任务。"""
            try:
                client = self._clients[role]
                sys_prompt = system_prompts.get(role, "")
                messages = [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                reply = client.chat(messages)
                return role, reply
            except Exception as e:
                logger.error("模型 [%s] 调用失败: %s", role, e)
                return role, f"[ERROR: {role} 调用失败: {e}]"

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_parallel
        ) as executor:
            future_map = {
                executor.submit(_ask, role): role
                for role in self._roles
            }
            for future in concurrent.futures.as_completed(
                future_map, timeout=self._timeout
            ):
                try:
                    role, reply = future.result()
                    results[role] = reply
                    logger.info("模型 [%s] 已返回 %d 字符", role, len(reply))
                except concurrent.futures.TimeoutError:
                    # 某个线程超时，跳过
                    pass
                except Exception as e:
                    logger.warning("获取模型结果时出错: %s", e)

        if not results:
            raise RuntimeError("所有模型调用均失败")

        return results

    def converge(
        self,
        question: str,
        responses: dict[str, str],
        role_labels: dict[str, str],
    ) -> str:
        """收敛阶段：将所有模型的回答汇总，让收敛模型做出最终裁决。

        Args:
            question: 原始问题
            responses: {"primary": "回答", "critic": "回答"}
            role_labels: 角色的人类可读标签，用于构建 prompt
                        {"primary": "架构师", "critic": "审查员"}

        Returns:
            str: 收敛后的 JSON 字符串（含 consensus / divergences / final_decision）
        """
        parts = [f"## 原始问题\n{question}\n"]

        if responses:
            parts.append("## 各专家回答\n")
            for role, answer in responses.items():
                label = role_labels.get(role, role)
                parts.append(f"### {role}（{label}）\n{answer}\n")

        parts.append("""
## 收敛任务
请你作为中立的仲裁者，完成以下任务：
1. 提取所有专家一致的结论（共识）
2. 标注分歧点并分析各方推理链的质量
3. 给出最终融合方案，解释为何优于任何单一方案
4. 对少数派意见给出保留建议（如有）

请严格按以下 JSON 格式输出，不要包含 markdown 代码块标记：
{
  "consensus": ["共识点1", "共识点2", ...],
  "divergences": [
    {
      "topic": "分歧点名称",
      "majority_view": "多数意见",
      "minority_view": "少数意见",
      "resolution": "裁决结果"
    }
  ],
  "final_decision": "最终融合方案",
  "risk_notes": ["潜在风险1", "潜在风险2"]
}
""")
        converge_prompt = "\n".join(parts)
        messages = [
            {
                "role": "system",
                "content": (
                    "你是项目技术仲裁者。"
                    "你需要综合多位专家的意见，做出最终裁决。"
                    "请严格按 JSON 格式输出，不要使用 markdown 代码块标记。"
                ),
            },
            {"role": "user", "content": converge_prompt},
        ]

        return self._convergence_client.chat(messages, json_mode=True)