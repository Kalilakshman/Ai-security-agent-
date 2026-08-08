"""
OpenRouter LLM Provider implementation.
"""

import os
import httpx
from typing import List, Optional
from core.llm.base import LLMProvider
from core.config import AppConfig, load_config
from core.logger import get_logger

logger = get_logger("llm_openrouter")


class OpenRouterLLMProvider(LLMProvider):
    """LLM Provider implementation connecting to OpenRouter API endpoints."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.llm_cfg = self.config.llm

        api_key = self.llm_cfg.get_resolved_api_key()
        if not api_key:
            api_key = self.config.openrouter.api_key.get_secret_value()

        self.api_key = (api_key or "").strip()
        self.base_url = (self.llm_cfg.api_endpoint or self.config.openrouter.base_url).rstrip("/")
        self.model = self.llm_cfg.model or self.config.openrouter.default_model
        self.fallback_model = self.llm_cfg.fallback_model or self.config.openrouter.fallback_model
        self.timeout = self.llm_cfg.timeout_seconds or self.config.openrouter.timeout_seconds
        self.temperature = self.llm_cfg.temperature or self.config.openrouter.temperature
        self.max_tokens = self.llm_cfg.max_tokens or self.config.openrouter.max_tokens

        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.llm_cfg.site_url or self.config.openrouter.site_url,
            "X-Title": self.llm_cfg.app_name or self.config.openrouter.app_name,
            "Content-Type": "application/json",
        }

    def provider_name(self) -> str:
        return "openrouter"

    def available_models(self) -> List[str]:
        """Fetch list of available models from OpenRouter API or return standard default set."""
        default_models = [
            self.model,
            self.fallback_model,
            "qwen/qwen-2.5-coder-32b-instruct:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1:free",
        ]
        url = f"{self.base_url}/models"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=self._headers)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                    if models:
                        return models
        except Exception as e:
            logger.debug(f"Failed to fetch live OpenRouter models: {str(e)}")

        return default_models

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send completion request to OpenRouter API with automatic fallback."""
        selected_model = model or self.model
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        logger.debug(f"OpenRouter generate request (Model: {selected_model})")

        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(url, headers=self._headers, json=payload)
                if response.status_code != 200:
                    logger.warning(
                        f"OpenRouter primary model '{selected_model}' returned status {response.status_code}: {response.text}"
                    )
                    if selected_model != self.fallback_model:
                        logger.info(f"Attempting fallback model: {self.fallback_model}")
                        payload["model"] = self.fallback_model
                        response = client.post(url, headers=self._headers, json=payload)

                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return str(choices[0].get("message", {}).get("content", ""))
                return ""
            except Exception as e:
                logger.error(f"OpenRouter API generate failed: {str(e)}")
                raise RuntimeError(f"OpenRouter API request error: {str(e)}") from e

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Asynchronously send completion request to OpenRouter API."""
        selected_model = model or self.model
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._headers, json=payload)
                if response.status_code != 200 and selected_model != self.fallback_model:
                    payload["model"] = self.fallback_model
                    response = await client.post(url, headers=self._headers, json=payload)

                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return str(choices[0].get("message", {}).get("content", ""))
                return ""
            except Exception as e:
                logger.error(f"Async OpenRouter API generate failed: {str(e)}")
                raise RuntimeError(f"Async OpenRouter API request error: {str(e)}") from e

    def health_check(self) -> bool:
        """Perform API health check against OpenRouter API."""
        url = f"{self.base_url}/models"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=self._headers)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenRouter health check failed: {str(e)}")
            return False

    async def health_check_async(self) -> bool:
        url = f"{self.base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self._headers)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Async OpenRouter health check failed: {str(e)}")
            return False
