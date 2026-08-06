"""
Pytest shared fixtures.
"""

import sys
import tempfile
import pytest
from pathlib import Path
from typer.testing import CliRunner
from core.config import AppConfig, OpenRouterConfig, ExecutorConfig, LoggingConfig
from core.executor import SafeExecutor

# Ensure project root is in sys.path during pytest execution
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def cli_runner():
    """Return Typer CliRunner for testing CLI commands."""
    return CliRunner()


@pytest.fixture
def sample_config():
    """Return default AppConfig instance for testing."""
    return AppConfig(
        openrouter=OpenRouterConfig(
            api_key="sk-or-v1-testkey1234567890",
            default_model="meta-llama/llama-3.3-70b-instruct:free",
        ),
        executor=ExecutorConfig(default_timeout_seconds=5.0),
        logging=LoggingConfig(level="DEBUG")
    )


@pytest.fixture
def safe_executor():
    """Return initialized SafeExecutor instance."""
    return SafeExecutor(default_timeout_seconds=5.0)


@pytest.fixture
def temp_yaml_file():
    """Create temporary YAML config file fixture."""
    content = """
openrouter:
  api_key: "sk-or-v1-yamlkey999"
  default_model: "meta-llama/llama-3.3-70b-instruct:free"
  temperature: 0.5

executor:
  default_timeout_seconds: 15.0

logging:
  level: "DEBUG"
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(content)
        f.flush()
        yield Path(f.name)

    # Cleanup
    try:
        Path(f.name).unlink(missing_ok=True)
    except Exception:
        pass
