"""
OpenRouter LLM Provider implementation.

Implements ILLMProvider interface using httpx to communicate with OpenRouter API endpoints.
Supports free models on OpenRouter with automatic fallback.
"""

import httpx
from typing import Optional
from core.interfaces import ILLMProvider
from core.config import OpenRouterConfig
from core.logger import get_logger

logger = get_logger("openrouter")


class OpenRouterLLMProvider(ILLMProvider):
    """LLM Provider implementation connecting to OpenRouter API endpoints."""

    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self._api_key = config.api_key.get_secret_value()
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": config.site_url,
            "X-Title": config.app_name,
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "OpenRouter API"

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send completion request to OpenRouter API."""
        selected_model = model or self.config.default_model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.post(url, headers=self._headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        return str(choices[0].get("message", {}).get("content", ""))
                    return ""

                # Handle failure and attempt fallback free model if primary model failed
                logger.warning(
                    f"OpenRouter primary model '{selected_model}' returned status {response.status_code}: {response.text}"
                )

                if selected_model != self.config.fallback_model:
                    logger.info(f"Attempting fallback model: {self.config.fallback_model}")
                    payload["model"] = self.config.fallback_model
                    fallback_resp = await client.post(url, headers=self._headers, json=payload)
                    if fallback_resp.status_code == 200:
                        data = fallback_resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return str(choices[0].get("message", {}).get("content", ""))

                response.raise_for_status()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from OpenRouter API: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"OpenRouter API returned error status {e.response.status_code}") from e
            except Exception as e:
                logger.exception(f"Failed to communicate with OpenRouter API: {str(e)}")
                raise RuntimeError(f"OpenRouter communication error: {str(e)}") from e

        return ""

    async def health_check(self) -> bool:
        """Perform lightweight health check against OpenRouter API."""
        if not self._api_key or self._api_key.startswith("sk-or-v1-placeholder"):
            logger.warning("OpenRouter API key is missing or default placeholder.")

        url = f"{self.config.base_url.rstrip('/')}/models"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self._headers)
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"OpenRouter health check failed: {str(e)}")
                return False
