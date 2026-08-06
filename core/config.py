"""
Strongly typed configuration management module using Pydantic v2 and PyYAML.

Supports expanded settings for Database, Reports, Plugins, OpenRouter, Executor, and Logging.
Reads from YAML configuration files and environment variable overrides (SECURITY_AI_*).
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenRouterConfig(BaseModel):
    """Configuration schema for OpenRouter LLM backend provider."""
    api_key: SecretStr = Field(
        default=SecretStr("YOUR_OPENROUTER_API_KEY_HERE"),
        description="OpenRouter API Key."
    )
    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API v1 base endpoint."
    )
    default_model: str = Field(
        default="nvidia/llama-3.1-nemotron-70b-instruct:free",
        description="Default free model to use on OpenRouter."
    )
    fallback_model: str = Field(
        default="google/gemini-2.0-flash-exp:free",
        description="Fallback free model if primary model is unavailable."
    )
    timeout_seconds: float = Field(
        default=45.0,
        description="API request timeout in seconds."
    )
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature for LLM outputs."
    )
    max_tokens: int = Field(
        default=2048,
        description="Maximum tokens allowed in API completion response."
    )
    site_url: str = Field(
        default="https://github.com/security-ai-orchestrator",
        description="HTTP Referer header required by OpenRouter."
    )
    app_name: str = Field(
        default="AI Security Orchestrator CLI",
        description="X-Title header required by OpenRouter."
    )


class ExecutorConfig(BaseModel):
    """Configuration schema for safe command execution engine."""
    default_timeout_seconds: float = Field(
        default=60.0,
        description="Default execution timeout for child processes."
    )
    max_timeout_seconds: float = Field(
        default=600.0,
        description="Absolute maximum allowable timeout limit."
    )
    allow_environment_pass_through: bool = Field(
        default=False,
        description="Whether to pass current process env variables to child process."
    )
    safe_environment_vars: List[str] = Field(
        default_factory=lambda: ["PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME", "USER", "LANG"],
        description="Safelist of environment keys allowed in process execution environment."
    )


class DatabaseConfig(BaseModel):
    """Configuration schema for SQLite database persistence."""
    db_url: str = Field(
        default="sqlite:///security_orchestrator.db",
        description="SQLAlchemy database connection URL string."
    )
    echo: bool = Field(
        default=False,
        description="Enable verbose SQL query logging."
    )


class ReportConfig(BaseModel):
    """Configuration schema for report generation defaults."""
    output_dir: str = Field(
        default="reports_output",
        description="Default output directory for generated reports."
    )
    default_formats: List[str] = Field(
        default_factory=lambda: ["md", "html", "pdf"],
        description="Default report formats to generate."
    )


class PluginSettingsConfig(BaseModel):
    """Configuration schema for dynamic plugin settings."""
    plugins_dir: str = Field(
        default="plugins",
        description="Directory path containing dynamic security plugins."
    )
    enabled_plugins: List[str] = Field(
        default_factory=lambda: ["nmap", "whatweb", "nikto", "gobuster", "nuclei"],
        description="Safelist of enabled tool plugins."
    )


class LoggingConfig(BaseModel):
    """Configuration schema for application logging."""
    level: str = Field(
        default="INFO",
        description="Logging level threshold (DEBUG, INFO, WARNING, ERROR)."
    )
    json_format: bool = Field(
        default=False,
        description="Output structured JSON logs instead of rich console output."
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Optional file path destination for append log output."
    )


class AppConfig(BaseSettings):
    """Top-level application settings container combining YAML and Environment inputs."""
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_AI_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    executor: ExecutorConfig = Field(default_factory=ExecutorConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    reports: ReportConfig = Field(default_factory=ReportConfig)
    plugins: PluginSettingsConfig = Field(default_factory=PluginSettingsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def load_from_yaml(cls, yaml_path: str | Path) -> "AppConfig":
        """Load settings from YAML file with fallback to environment defaults."""
        path = Path(yaml_path)
        if not path.is_file():
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML configuration at '{yaml_path}': {str(e)}") from e


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Helper function to discover and load AppConfig."""
    if config_path:
        return AppConfig.load_from_yaml(config_path)

    env_config = os.getenv("SECURITY_AI_CONFIG")
    if env_config:
        return AppConfig.load_from_yaml(env_config)

    default_candidates = [
        Path("config/config.yaml"),
        Path("config.yaml"),
    ]

    for candidate in default_candidates:
        if candidate.is_file():
            return AppConfig.load_from_yaml(candidate)

    return AppConfig()
