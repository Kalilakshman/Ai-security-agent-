"""
LLM Provider Factory and Registry management.
"""

from typing import Dict, Type, Optional, List
from core.llm.base import LLMProvider
from core.llm.openrouter import OpenRouterLLMProvider
from core.llm.openai import OpenAICompatibleProvider
from core.llm.ollama import OllamaLLMProvider
from core.config import AppConfig, load_config
from core.logger import get_logger

logger = get_logger("llm_factory")

_PROVIDER_REGISTRY: Dict[str, Type[LLMProvider]] = {
    "openrouter": OpenRouterLLMProvider,
    "openai": OpenAICompatibleProvider,
    "ollama": OllamaLLMProvider,
}


def register_llm_provider(name: str, provider_cls: Type[LLMProvider]) -> None:
    """Register a custom LLMProvider class implementation."""
    key = name.lower().strip()
    _PROVIDER_REGISTRY[key] = provider_cls
    logger.info(f"Registered LLM Provider: {key}")


def list_registered_providers() -> List[str]:
    """List all registered LLM provider key names."""
    return list(_PROVIDER_REGISTRY.keys())


def get_llm_provider(
    provider_name: Optional[str] = None,
    config: Optional[AppConfig] = None
) -> LLMProvider:
    """Factory function to resolve and instantiate configured LLMProvider.

    Args:
        provider_name: Explicit provider name override ('openrouter', 'openai', 'ollama').
        config: Optional AppConfig instance.

    Returns:
        Instantiated concrete LLMProvider instance.
    """
    cfg = config or load_config()
    key = (provider_name or cfg.llm.provider or "openrouter").lower().strip()

    provider_cls = _PROVIDER_REGISTRY.get(key)
    if not provider_cls:
        logger.warning(f"Unknown LLM provider '{key}'. Falling back to 'openrouter'.")
        provider_cls = OpenRouterLLMProvider

    return provider_cls(config=cfg)
