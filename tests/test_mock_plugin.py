"""
Integration tests using isolated mock plugins.
"""

import pytest
from plugins.base import BasePlugin, StandardPluginOutput
from core.registry import PluginRegistry
from core.planner import AIPlanner
from core.workflow import WorkflowEngine


class MockScannerPlugin(BasePlugin):
    """Isolated mock scanner plugin for testing workflows without system tool dependencies."""

    @property
    def name(self) -> str:
        return "mock_scanner"

    @property
    def description(self) -> str:
        return "Mock security scanner plugin for automated testing."

    def is_installed(self) -> bool:
        return True

    def build_command(self, target: str, options=None) -> list[str]:
        return ["echo", f"Scanning {target}"]

    def parse(self, stdout: str, stderr: str):
        return [{"mock_metric": "port 80 open", "raw_output": stdout.strip()}]


def test_mock_plugin_execution():
    """Test executing mock plugin returns valid StandardPluginOutput."""
    plugin = MockScannerPlugin()
    output = plugin.execute("127.0.0.1")

    assert isinstance(output, StandardPluginOutput)
    assert output.tool == "mock_scanner"
    assert output.target == "127.0.0.1"
    assert output.status == "COMPLETED"
    assert len(output.findings) == 1
    assert output.findings[0]["mock_metric"] == "port 80 open"


def test_mock_plugin_registry_integration():
    """Test registering and executing mock plugin via PluginRegistry and WorkflowEngine."""
    registry = PluginRegistry()
    mock_plugin = MockScannerPlugin()
    registry.register(mock_plugin)

    assert registry.get_plugin("mock_scanner") is not None

    engine = WorkflowEngine(registry=registry)
    plan = AIPlanner(registry=registry)._build_fallback_plan("127.0.0.1", registry.list_plugins())

    result = engine.execute_plan(plan, authorized=True)
    assert result.target == "127.0.0.1"
    assert result.authorized is True
    assert len(result.step_results) > 0
