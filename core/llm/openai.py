"""
OpenAI-Compatible LLM Provider implementation.
"""

import os
import httpx
from typing import List, Optional
from core.llm.base import LLMProvider
from core.config import AppConfig, load_config
from core.logger import get_logger

logger = get_logger("llm_openai")


class OpenAICompatibleProvider(LLMProvider):
    """LLM Provider implementation connecting to OpenAI-compatible API endpoints.
    
    Compatible with OpenAI API, LM Studio, vLLM, Azure OpenAI, and LocalAI.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.llm_cfg = self.config.llm

        base_url = self.llm_cfg.api_endpoint
        if not base_url or base_url.startswith("https://openrouter.ai"):
            base_url = "https://api.openai.com/v1"

        self.base_url = base_url.rstrip("/")
        self.api_key = (self.llm_cfg.get_resolved_api_key() or os.getenv("OPENAI_API_KEY", "")).strip()
        self.model = self.llm_cfg.model if self.llm_cfg.model and not self.llm_cfg.model.startswith("nvidia/") else "gpt-4o-mini"
        self.timeout = self.llm_cfg.timeout_seconds
        self.temperature = self.llm_cfg.temperature
        self.max_tokens = self.llm_cfg.max_tokens

        self._headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self._headers["Authorization"] = f"Bearer {self.api_key}"

    def provider_name(self) -> str:
        return "openai"

    def available_models(self) -> List[str]:
        """Fetch list of available models from OpenAI-compatible endpoint or return defaults."""
        default_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", self.model]
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
            logger.debug(f"Failed to fetch live OpenAI models: {str(e)}")

        return list(dict.fromkeys(default_models))

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send chat completion request to OpenAI-compatible endpoint."""
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

        logger.debug(f"OpenAI-compatible generate request to {url} (Model: {selected_model})")

        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(url, headers=self._headers, json=payload)
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return str(choices[0].get("message", {}).get("content", ""))
                return ""
            except Exception as e:
                logger.error(f"OpenAI-compatible API generate failed: {str(e)}")
                raise RuntimeError(f"OpenAI API request error: {str(e)}") from e

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Asynchronously send completion request to OpenAI-compatible endpoint."""
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
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return str(choices[0].get("message", {}).get("content", ""))
                return ""
            except Exception as e:
                logger.error(f"Async OpenAI-compatible API generate failed: {str(e)}")
                raise RuntimeError(f"Async OpenAI API request error: {str(e)}") from e

    def health_check(self) -> bool:
        """Perform health check against OpenAI-compatible endpoint."""
        url = f"{self.base_url}/models"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=self._headers)
                return response.status_code in (200, 401)  # 401 indicates server is up but auth needed
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {str(e)}")
            return False

    async def health_check_async(self) -> bool:
        url = f"{self.base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self._headers)
                return response.status_code in (200, 401)
        except Exception as e:
            logger.warning(f"Async OpenAI health check failed: {str(e)}")
            return False
