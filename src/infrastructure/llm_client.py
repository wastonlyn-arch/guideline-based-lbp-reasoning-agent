"""
通用 LLM 调用客户端 — 基于 openai SDK，支持 DeepSeek / Ollama。

支持参数：
- reasoning_effort (low | medium | high) — 控制模型思考链深度
- json_mode — 让模型返回 JSON 格式响应

用法:
    from src.infrastructure.llm_client import LLMClient
    client = LLMClient()
    reply = client.chat([{"role": "user", "content": "你好"}])
    reply_json = client.chat(messages, json_mode=True)
"""

import json
import logging
import os
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """通用 LLM 调用客户端，支持 DeepSeek / Ollama。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-v4-flash",
        base_url: str = "https://api.deepseek.com",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        reasoning_effort: str = "medium",
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def chat(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        reasoning_effort: Optional[str] = None,
    ) -> str:
        """通用 chat 调用。

        Args:
            messages: [{"role": "user", "content": "..."}]
            temperature: 采样温度（覆盖默认）
            max_tokens: 最大输出 token（覆盖默认）
            json_mode: 是否启用 JSON 响应模式
            reasoning_effort: 思考链深度（覆盖默认）

        Returns:
            str: 模型回复文本。

        Raises:
            RuntimeError: API 调用失败 / 无有效响应。
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        # 启用 reasoning（DeepSeek v4 专用）
        effort = reasoning_effort or self.reasoning_effort
        if effort in ("low", "medium", "high"):
            kwargs["reasoning_effort"] = effort
            # extra_body 传递 thinking 参数
            kwargs.setdefault("extra_body", {})
            kwargs["extra_body"]["thinking"] = {"type": "enabled"}

        # JSON mode：通过 response_format 控制
        if json_mode:
            # 兼容 OpenAI SDK 和 DeepSeek
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = self._client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content
            if content is None:
                # 检查是否有 reasoning_content
                reasoning = getattr(resp.choices[0].message, "reasoning_content", None)
                if reasoning:
                    # thinking 模式下 content 可能为空，但 reasoning_content 有值
                    logger.info("响应为空但含 reasoning_content (%d chars)", len(reasoning))
                raise RuntimeError("模型返回空响应")
            return content.strip()
        except Exception as e:
            logger.error("LLM 调用失败: %s", e)
            raise RuntimeError(f"LLM 调用失败: {e}") from e