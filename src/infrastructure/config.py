"""
配置管理模块 — 从 config.yaml 和 .env 加载项目配置。

用法:
    config = Config()
    config.llm_api_key      # → str
    config.llm_model        # → str
    config.db_path          # → str
    config.vector_db_path   # → str
    config.embedding_model  # → str
    config.log_level        # → str
    
    # 多模型交叉验证配置
    config.multi_model_enabled        # → bool
    config.multi_model_models         # → dict
    config.multi_model_convergence    # → dict
    config.multi_model_timeout        # → int
    
    # 简化访问
    config.multi_model_config()       # → dict，完整配置
"""

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class Config:
    """项目全局配置，由 config.yaml + 环境变量合并加载。"""

    # LLM 配置
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-v4-flash"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    llm_reasoning_effort: str = "medium"

    # 数据库配置
    db_path: str = "data/knowledge_base.db"

    # 向量存储配置
    vector_db_path: str = "data/faiss_index"
    embedding_model: str = "all-MiniLM-L6-v2"

    # 日志配置
    log_level: str = "INFO"

    # 其他可选配置
    ollama_base_url: str = "http://localhost:11434"

    # ── 多模型交叉验证配置 ──
    multi_model_enabled: bool = False
    multi_model_models: dict = field(default_factory=dict)
    multi_model_convergence: dict = field(default_factory=dict)
    multi_model_max_parallel: int = 3
    multi_model_timeout: int = 30

    def __init__(self, config_path: str = "config.yaml"):
        """加载配置。

        Args:
            config_path: config.yaml 路径，相对于项目根目录。
        """
        self._load_from_yaml(config_path)
        self._load_from_env()

    def multi_model_config(self) -> dict:
        """获取完整的多模型配置字典（兼容 multi_llm.MultiLLM.from_config）。"""
        return {
            "enabled": self.multi_model_enabled,
            "models": self.multi_model_models,
            "convergence": self.multi_model_convergence,
            "max_parallel": self.multi_model_max_parallel,
            "timeout": self.multi_model_timeout,
        }

    def _load_from_yaml(self, path: str):
        """从 YAML 文件加载配置。"""
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        # LLM
        llm = cfg.get("llm", {})
        self.llm_provider = llm.get("provider", self.llm_provider)
        self.llm_model = llm.get("model", self.llm_model)
        self.llm_base_url = llm.get("base_url", self.llm_base_url)
        self.llm_temperature = llm.get("temperature", self.llm_temperature)
        self.llm_max_tokens = llm.get("max_tokens", self.llm_max_tokens)
        self.llm_reasoning_effort = llm.get("reasoning_effort", self.llm_reasoning_effort)

        # Database
        db = cfg.get("database", {})
        self.db_path = db.get("path", self.db_path)

        # Vector store
        vs = cfg.get("vector_store", {})
        self.vector_db_path = vs.get("path", self.vector_db_path)
        self.embedding_model = vs.get("embedding_model", self.embedding_model)

        # Logging
        log = cfg.get("logging", {})
        self.log_level = log.get("level", self.log_level)

        # ── 多模型交叉验证 ──
        mm = cfg.get("multi_model", {})
        self.multi_model_enabled = mm.get("enabled", self.multi_model_enabled)
        self.multi_model_models = mm.get("models", self.multi_model_models)
        self.multi_model_convergence = mm.get("convergence", self.multi_model_convergence)
        self.multi_model_max_parallel = mm.get("max_parallel", self.multi_model_max_parallel)
        self.multi_model_timeout = mm.get("timeout", self.multi_model_timeout)

    def _load_from_env(self):
        """从环境变量覆盖配置（优先于 YAML）。"""
        self.llm_api_key = os.environ.get(
            "DEEPSEEK_API_KEY",
            os.environ.get("LLM_API_KEY", ""),
        )
        self.ollama_base_url = os.environ.get(
            "OLLAMA_BASE_URL",
            self.ollama_base_url,
        )
