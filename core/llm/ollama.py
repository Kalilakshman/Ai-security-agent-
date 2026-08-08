"""
Ollama Local LLM Provider implementation.
"""

import os
import httpx
from typing import List, Optional
from core.llm.base import LLMProvider
from core.config import AppConfig, load_config
from core.logger import get_logger

logger = get_logger("llm_ollama")


class OllamaLLMProvider(LLMProvider):
    """LLM Provider implementation connecting to local Ollama instances."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.llm_cfg = self.config.llm

        base_url = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or self.llm_cfg.api_endpoint
        if not base_url or base_url.startswith("https://openrouter.ai") or base_url.startswith("https://api.openai.com"):
            base_url = "http://localhost:11434"

        self.base_url = base_url.rstrip("/")
        self.model = self.llm_cfg.model if self.llm_cfg.model and not ("/" in self.llm_cfg.model and ":" in self.llm_cfg.model) else "llama3.2"
        self.timeout = self.llm_cfg.timeout_seconds
        self.temperature = self.llm_cfg.temperature
        self.max_tokens = self.llm_cfg.max_tokens

    def provider_name(self) -> str:
        return "ollama"

    def available_models(self) -> List[str]:
        """Fetch list of pulled local models from Ollama server or return standard defaults."""
        default_models = ["llama3.2", "llama3.1", "mistral", "qwen2.5-coder", "codellama", "deepseek-r1:8b", self.model]
        url = f"{self.base_url}/api/tags"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    if models:
                        return models
        except Exception as e:
            logger.debug(f"Failed to fetch local Ollama models: {str(e)}")

        return list(dict.fromkeys(default_models))

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send completion request to Ollama local endpoint."""
        selected_model = model or self.model
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Priority 1: Ollama native /api/chat endpoint
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": tokens,
            }
        }

        logger.debug(f"Ollama generate request to {url} (Model: {selected_model})")

        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return str(data.get("message", {}).get("content", ""))

                # Fallback to OpenAI compatible endpoint on Ollama /v1/chat/completions
                v1_url = f"{self.base_url}/v1/chat/completions"
                v1_payload = {
                    "model": selected_model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": tokens,
                }
                v1_resp = client.post(v1_url, json=v1_payload)
                v1_resp.raise_for_status()
                data = v1_resp.json()
                choices = data.get("choices", [])
                if choices:
                    return str(choices[0].get("message", {}).get("content", ""))

                return ""
            except Exception as e:
                logger.error(f"Ollama local API generate failed: {str(e)}")
                raise RuntimeError(f"Ollama local API request error: {str(e)}") from e

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Asynchronously send completion request to Ollama local endpoint."""
        selected_model = model or self.model
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": tokens,
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return str(data.get("message", {}).get("content", ""))

                v1_url = f"{self.base_url}/v1/chat/completions"
                v1_payload = {
                    "model": selected_model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": tokens,
                }
                v1_resp = await client.post(v1_url, json=v1_payload)
                v1_resp.raise_for_status()
                data = v1_resp.json()
                choices = data.get("choices", [])
                if choices:
                    return str(choices[0].get("message", {}).get("content", ""))

                return ""
            except Exception as e:
                logger.error(f"Async Ollama API generate failed: {str(e)}")
                raise RuntimeError(f"Async Ollama API request error: {str(e)}") from e

    def health_check(self) -> bool:
        """Perform health check against Ollama local instance."""
        url = f"{self.base_url}/api/version"
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {str(e)}")
            return False

    async def health_check_async(self) -> bool:
        url = f"{self.base_url}/api/version"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Async Ollama health check failed: {str(e)}")
            return False
