"""
Provider-Independent LLM Subsystem Package.
"""

from core.llm.base import LLMProvider, LLMResponse
from core.llm.openrouter import OpenRouterLLMProvider
from core.llm.openai import OpenAICompatibleProvider
from core.llm.ollama import OllamaLLMProvider
from core.llm.factory import get_llm_provider, register_llm_provider, list_registered_providers


class OpenRouterClient:
    """Backward compatibility wrapper around OpenRouterLLMProvider matching legacy OpenRouterClient API."""

    def __init__(self, api_key=None, model=None, config=None):
        self.provider = OpenRouterLLMProvider(config=config)
        if model:
            self.provider.model = model
        if api_key:
            self.provider.api_key = api_key
            self.provider._headers["Authorization"] = f"Bearer {api_key}"
        self.model = self.provider.model

    def complete(self, prompt, system_prompt=None, model_override=None, temperature=0.2, max_tokens=2048) -> LLMResponse:
        content = self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model_override,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMResponse(content=content, model=model_override or self.model)

    async def complete_async(self, prompt, system_prompt=None, model_override=None, temperature=0.2, max_tokens=2048) -> LLMResponse:
        content = await self.provider.generate_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model_override,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMResponse(content=content, model=model_override or self.model)


__all__ = [
    "LLMProvider",
    "LLMResponse",
    "OpenRouterLLMProvider",
    "OpenAICompatibleProvider",
    "OllamaLLMProvider",
    "get_llm_provider",
    "register_llm_provider",
    "list_registered_providers",
    "OpenRouterClient",
]
