"""连通性测试：验证核心基础设施模块可正常导入。"""

from src.infrastructure.config import Config
from src.infrastructure.llm_client import LLMClient
import logging

logger = logging.getLogger(__name__)


def test_config_loads() -> None:
    """Config 类能正常加载配置，不抛出异常。"""
    c = Config()
    assert c.llm_provider is not None
    assert c.llm_model is not None
    assert c.db_path is not None
    logger.info("provider=%s, model=%s, db=%s", c.llm_provider, c.llm_model, c.db_path)


def test_llm_client_importable() -> None:
    """LLMClient 类可正常导入，不验证构造（需要 API key）。"""
    from src.infrastructure.llm_client import LLMClient
    assert LLMClient is not None
    logger.info("LLMClient 类可导入")
