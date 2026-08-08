"""
Unit tests for Provider-Independent LLM Architecture and CLI commands.
"""

import pytest
import httpx
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from core.config import AppConfig, LLMConfig
from core.llm import (
    LLMProvider,
    OpenRouterLLMProvider,
    OpenAICompatibleProvider,
    OllamaLLMProvider,
    get_llm_provider,
    list_registered_providers,
    OpenRouterClient,
)
from core.planner import AIPlanner
from core.analyzer import AIResultsAnalyzer
from app.cli import app


class DummyMockProvider(LLMProvider):
    """Mock LLMProvider implementation for testing."""

    def provider_name(self) -> str:
        return "dummy_mock"

    def available_models(self) -> list[str]:
        return ["dummy-model-v1", "dummy-model-v2"]

    def generate(self, prompt: str, system_prompt=None, model=None, temperature=None, max_tokens=None) -> str:
        if "plan" in prompt.lower() or "planner" in system_prompt.lower():
            return '{"target": "127.0.0.1", "scope_summary": "Test scope", "selected_plugins": ["nmap"], "execution_order": [{"step_number": 1, "tool": "nmap", "options": {}, "purpose": "Scan ports"}], "estimated_duration_seconds": 10.0, "reasoning": "Mock reasoning"}'
        elif "analyze" in system_prompt.lower():
            return '{"target": "127.0.0.1", "timestamp": "2026-08-08T00:00:00Z", "executive_summary": "Mock analysis summary", "observed_services": [{"source_tool": "nmap", "finding_type": "open_port", "details": {"port": 80}}], "interesting_findings": [], "potential_risks": [{"category": "risk_hypothesis", "fact_references": ["nmap"], "inference": "Mock risk"}], "recommendations": [{"category": "mitigation_step", "fact_references": [], "inference": "Mock recommendation"}], "confidence": 0.95, "unknowns": []}'
        return "Mock generated completion response"

    def health_check(self) -> bool:
        return True


def test_provider_factory_resolution():
    """Test get_llm_provider resolves configured provider classes."""
    cfg_or = AppConfig(llm=LLMConfig(provider="openrouter"))
    p_or = get_llm_provider(config=cfg_or)
    assert p_or.provider_name() == "openrouter"

    cfg_oa = AppConfig(llm=LLMConfig(provider="openai"))
    p_oa = get_llm_provider(config=cfg_oa)
    assert p_oa.provider_name() == "openai"

    cfg_ol = AppConfig(llm=LLMConfig(provider="ollama"))
    p_ol = get_llm_provider(config=cfg_ol)
    assert p_ol.provider_name() == "ollama"

    assert set(["openrouter", "openai", "ollama"]).issubset(set(list_registered_providers()))


def test_openrouter_provider_generate(httpx_mock):
    """Test OpenRouterLLMProvider generate and fallback logic."""
    cfg = AppConfig(llm=LLMConfig(provider="openrouter", api_key="sk-or-testkey"))
    provider = OpenRouterLLMProvider(config=cfg)
    assert provider.provider_name() == "openrouter"

    with patch("httpx.Client.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OpenRouter test response"}}]
        }
        mock_post.return_value = mock_response

        res = provider.generate("Test prompt")
        assert res == "OpenRouter test response"
        assert mock_post.called


def test_openai_compatible_provider_generate():
    """Test OpenAICompatibleProvider generate method."""
    cfg = AppConfig(llm=LLMConfig(provider="openai", api_endpoint="https://api.openai.com/v1", api_key="sk-test"))
    provider = OpenAICompatibleProvider(config=cfg)
    assert provider.provider_name() == "openai"

    with patch("httpx.Client.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OpenAI test response"}}]
        }
        mock_post.return_value = mock_response

        res = provider.generate("Test prompt")
        assert res == "OpenAI test response"


def test_ollama_provider_generate():
    """Test OllamaLLMProvider generate method."""
    cfg = AppConfig(llm=LLMConfig(provider="ollama", api_endpoint="http://localhost:11434"))
    provider = OllamaLLMProvider(config=cfg)
    assert provider.provider_name() == "ollama"

    with patch("httpx.Client.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Ollama test response"}
        }
        mock_post.return_value = mock_response

        res = provider.generate("Test prompt")
        assert res == "Ollama test response"


def test_ai_planner_with_generic_llm_provider():
    """Test AIPlanner works seamlessly with generic LLMProvider abstraction."""
    mock_provider = DummyMockProvider()
    planner = AIPlanner(llm_provider=mock_provider)

    plan = planner.generate_plan("127.0.0.1")
    assert plan.target == "127.0.0.1"
    assert len(plan.execution_order) == 1
    assert plan.selected_plugins == ["nmap"]


def test_ai_analyzer_with_generic_llm_provider():
    """Test AIResultsAnalyzer works seamlessly with generic LLMProvider abstraction."""
    mock_provider = DummyMockProvider()
    analyzer = AIResultsAnalyzer(llm_provider=mock_provider)

    report = analyzer.analyze_json({"target": "127.0.0.1", "timestamp": "2026-08-08T00:00:00Z"})
    assert report.target == "127.0.0.1"
    assert report.executive_summary == "Mock analysis summary"


def test_cli_llm_providers_command(cli_runner):
    """Test 'security-ai llm providers' CLI command."""
    result = cli_runner.invoke(app, ["llm", "providers"])
    assert result.exit_code == 0
    assert "REGISTERED LLM PROVIDER BACKENDS" in result.output
    assert "openrouter" in result.output
    assert "openai" in result.output
    assert "ollama" in result.output


def test_cli_llm_models_command(cli_runner):
    """Test 'security-ai llm models' CLI command."""
    result = cli_runner.invoke(app, ["llm", "models"])
    assert result.exit_code == 0
    assert "AVAILABLE MODELS FOR PROVIDER" in result.output


def test_cli_llm_test_command(cli_runner):
    """Test 'security-ai llm test' CLI command."""
    with patch("core.llm.openrouter.OpenRouterLLMProvider.generate", return_value="Mock health OK"):
        result = cli_runner.invoke(app, ["llm", "test"])
        assert result.exit_code == 0
        assert "LLM PROVIDER DIAGNOSTIC" in result.output


def test_cli_llm_select_command(cli_runner):
    """Test 'security-ai llm select' CLI command."""
    result = cli_runner.invoke(app, ["llm", "select", "--provider", "openai", "--model", "gpt-4o"])
    assert result.exit_code == 0
    assert "ACTIVE LLM SELECTION UPDATED" in result.output
    assert "openai" in result.output
    assert "gpt-4o" in result.output
