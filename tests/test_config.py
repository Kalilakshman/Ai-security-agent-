"""
Unit tests for configuration system (core/config.py).
"""

import os
import pytest
from core.config import AppConfig, load_config


def test_default_config_loading():
    """Test loading default configuration settings."""
    cfg = AppConfig()
    assert cfg.openrouter.default_model == "nvidia/llama-3.1-nemotron-70b-instruct:free"
    assert cfg.openrouter.fallback_model == "google/gemini-2.0-flash-exp:free"
    assert cfg.executor.default_timeout_seconds == 60.0
    assert cfg.logging.level == "INFO"


def test_yaml_config_loading(temp_yaml_file):
    """Test parsing settings from temporary YAML configuration file."""
    cfg = load_config(str(temp_yaml_file))

    assert cfg.openrouter.api_key.get_secret_value() == "sk-or-v1-yamlkey999"
    assert cfg.openrouter.default_model == "nvidia/llama-3.1-nemotron-70b-instruct:free"
    assert cfg.openrouter.temperature == 0.5
    assert cfg.executor.default_timeout_seconds == 15.0
    assert cfg.logging.level == "DEBUG"


def test_env_var_override(monkeypatch):
    """Test overriding configuration settings via environment variables."""
    monkeypatch.setenv("SECURITY_AI_OPENROUTER__DEFAULT_MODEL", "qwen/qwen-2.5-coder-32b-instruct:free")
    monkeypatch.setenv("SECURITY_AI_EXECUTOR__DEFAULT_TIMEOUT_SECONDS", "120.0")

    cfg = AppConfig()
    assert cfg.openrouter.default_model == "qwen/qwen-2.5-coder-32b-instruct:free"
    assert cfg.executor.default_timeout_seconds == 120.0
