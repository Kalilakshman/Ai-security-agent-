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


class LLMConfig(BaseModel):
    """Configuration schema for provider-independent LLM subsystem."""
    provider: str = Field(
        default="openrouter",
        description="Active LLM provider backend ('openrouter', 'openai', 'ollama')."
    )
    model: str = Field(
        default="nvidia/nemotron-3-ultra-550b-a55b:free",
        description="Active LLM model identifier."
    )
    api_endpoint: str = Field(
        default="https://openrouter.ai/api/v1",
        description="Base API endpoint URL."
    )
    api_key: SecretStr = Field(
        default=SecretStr(""),
        description="API Key secret string."
    )
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature for LLM outputs."
    )
    max_tokens: int = Field(
        default=2048,
        description="Maximum tokens allowed in completion response."
    )
    timeout_seconds: float = Field(
        default=45.0,
        description="API request timeout in seconds."
    )
    fallback_model: str = Field(
        default="google/gemini-2.0-flash-exp:free",
        description="Fallback free model for OpenRouter."
    )
    site_url: str = Field(
        default="https://github.com/security-ai-orchestrator",
        description="HTTP Referer header required by OpenRouter."
    )
    app_name: str = Field(
        default="AI Security Orchestrator CLI",
        description="X-Title header required by OpenRouter."
    )

    def get_resolved_api_key(self) -> str:
        """Resolve API key from explicit setting, env vars, or fallback."""
        direct_key = self.api_key.get_secret_value() if self.api_key else ""
        if direct_key and direct_key != "YOUR_OPENROUTER_API_KEY_HERE":
            return direct_key.strip()

        if self.provider == "openai":
            env_key = os.getenv("OPENAI_API_KEY")
            if env_key:
                return env_key.strip()
        elif self.provider == "openrouter":
            env_key = os.getenv("OPENROUTER_API_KEY")
            if env_key:
                return env_key.strip()

        env_generic = os.getenv("SECURITY_AI_LLM__API_KEY")
        if env_generic:
            return env_generic.strip()

        return direct_key.strip()


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
        default="nvidia/nemotron-3-ultra-550b-a55b:free",
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


class PluginTimeoutProfile(BaseModel):
    """Timeout configuration in seconds per assessment profile for a specific plugin."""
    fast: float = Field(default=120.0, description="Fast profile timeout in seconds.")
    standard: float = Field(default=600.0, description="Standard profile timeout in seconds.")
    deep: float = Field(default=1800.0, description="Deep profile timeout in seconds.")


class TimeoutsConfig(BaseModel):
    """Container for plugin-specific profile timeout settings."""
    nmap: PluginTimeoutProfile = Field(
        default_factory=lambda: PluginTimeoutProfile(fast=120.0, standard=600.0, deep=1800.0)
    )
    whatweb: PluginTimeoutProfile = Field(
        default_factory=lambda: PluginTimeoutProfile(fast=60.0, standard=300.0, deep=900.0)
    )
    nikto: PluginTimeoutProfile = Field(
        default_factory=lambda: PluginTimeoutProfile(fast=180.0, standard=900.0, deep=2400.0)
    )
    gobuster: PluginTimeoutProfile = Field(
        default_factory=lambda: PluginTimeoutProfile(fast=180.0, standard=1200.0, deep=3600.0)
    )
    nuclei: PluginTimeoutProfile = Field(
        default_factory=lambda: PluginTimeoutProfile(fast=300.0, standard=1800.0, deep=7200.0)
    )

    def get_timeout(self, plugin_name: str, profile: str = "standard") -> float:
        """Resolve execution timeout in seconds for a specific plugin and assessment profile."""
        profile_key = (profile or "standard").lower().strip()
        plugin_key = plugin_name.lower().strip()

        plugin_config = getattr(self, plugin_key, None)
        if not plugin_config or not isinstance(plugin_config, PluginTimeoutProfile):
            # Generic fallback for unlisted tools
            plugin_config = PluginTimeoutProfile(fast=120.0, standard=600.0, deep=1800.0)

        if profile_key == "fast":
            return plugin_config.fast
        elif profile_key == "deep":
            return plugin_config.deep
        return plugin_config.standard


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


class PolicyConfig(BaseModel):
    """Configuration schema for Authorization and Security Policy Engine."""
    allowed_targets: List[str] = Field(
        default_factory=lambda: ["127.0.0.1", "localhost", "192.168.*", "10.*", "*.local", "*"],
        description="Glob/Regex patterns of targets explicitly permitted for scanning."
    )
    denied_targets: List[str] = Field(
        default_factory=lambda: ["*.gov", "*.mil", "169.254.169.254"],
        description="Glob/Regex patterns of targets strictly prohibited from scanning."
    )
    tool_allowlist: List[str] = Field(
        default_factory=lambda: ["nmap", "whatweb", "nikto", "gobuster", "nuclei", "owasp_zap", "burp_suite", "tshark", "metasploit"],
        description="Safelist of tools allowed for execution."
    )
    tool_denylist: List[str] = Field(
        default_factory=list,
        description="Blocklist of tools explicitly prohibited from execution."
    )
    allowed_profiles: List[str] = Field(
        default_factory=lambda: ["fast", "standard", "deep"],
        description="Assessment profiles permitted for user selection."
    )
    max_execution_time_seconds: float = Field(
        default=3600.0,
        description="Absolute maximum execution time limit across all steps."
    )
    require_explicit_auth: bool = Field(
        default=True,
        description="Require explicit user authorization acknowledgement before execution."
    )
    allow_destructive_tools: bool = Field(
        default=False,
        description="Allow tools marked with destructive capabilities."
    )
    audit_log_file: Optional[str] = Field(
        default="policy_audit.log",
        description="Log file path for security policy decision audit entries."
    )


class AppConfig(BaseSettings):
    """Top-level application settings container combining YAML and Environment inputs."""
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_AI_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    executor: ExecutorConfig = Field(default_factory=ExecutorConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    reports: ReportConfig = Field(default_factory=ReportConfig)
    plugins: PluginSettingsConfig = Field(default_factory=PluginSettingsConfig)
    timeouts: TimeoutsConfig = Field(default_factory=TimeoutsConfig)
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

            # Sync openrouter config with llm config if llm section is not explicitly in YAML
            if "openrouter" in data and "llm" not in data:
                or_data = data["openrouter"]
                data["llm"] = {
                    "provider": "openrouter",
                    "model": or_data.get("default_model", "nvidia/nemotron-3-ultra-550b-a55b:free"),
                    "api_endpoint": or_data.get("base_url", "https://openrouter.ai/api/v1"),
                    "api_key": or_data.get("api_key", ""),
                    "temperature": or_data.get("temperature", 0.7),
                    "max_tokens": or_data.get("max_tokens", 2048),
                    "timeout_seconds": or_data.get("timeout_seconds", 45.0),
                    "fallback_model": or_data.get("fallback_model", "google/gemini-2.0-flash-exp:free"),
                    "site_url": or_data.get("site_url", "https://github.com/security-ai-orchestrator"),
                    "app_name": or_data.get("app_name", "AI Security Orchestrator CLI"),
                }

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
