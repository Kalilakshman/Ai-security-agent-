# Provider-Independent LLM Architecture Guide

The **AI Security Orchestrator CLI** features a decoupled, provider-independent LLM subsystem (`core/llm/`) supporting OpenRouter, OpenAI-compatible endpoints (OpenAI API, LM Studio, vLLM, Azure OpenAI), and Ollama local models.

---

## 🤖 Supported Providers

| Provider ID | Provider Class | Base URL / Default Endpoint | Secret Environment Key |
| :--- | :--- | :--- | :--- |
| **`openrouter`** | `OpenRouterLLMProvider` | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| **`openai`** | `OpenAICompatibleProvider` | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| **`ollama`** | `OllamaLLMProvider` | `http://localhost:11434` | `OLLAMA_HOST` / `OLLAMA_BASE_URL` |

---

## ⚙️ Configuration (`config/config.yaml`)

```yaml
llm:
  provider: "openrouter"
  model: "nvidia/nemotron-3-ultra-550b-a55b:free"
  api_endpoint: "https://openrouter.ai/api/v1"
  api_key: "sk-or-v1-your-key-here"
  temperature: 0.7
  max_tokens: 2048
  timeout_seconds: 45.0
  fallback_model: "google/gemini-2.0-flash-exp:free"
```

---

## 💻 CLI Commands

```bash
# List registered LLM providers and operational health
security-ai llm providers

# Discover available models for active provider
security-ai llm models

# Test LLM provider connection and measure latency
security-ai llm test

# Switch active provider and model
security-ai llm select --provider openai --model gpt-4o
```
