"""
Unit tests for Model Context Protocol (MCP) Integration Layer using mocked MCP servers.
"""

import pytest
from unittest.mock import MagicMock, patch

from core.mcp.models import (
    MCPToolCapabilities,
    MCPToolMetadata,
    MCPServerConfig,
    MCPExecutionEvidence,
)
from core.mcp.policy import MCPPolicyEngine
from core.mcp.client import MCPClient
from core.mcp.registry import MCPServerRegistry
from core.mcp.health import MCPHealthMonitor
from core.mcp.gateway import MCPGateway
from plugins.mcp_adapter import MCPPluginAdapter


@pytest.fixture
def mock_server_config():
    return MCPServerConfig(
        server_id="mock_mcp_server",
        name="Mock Assessment MCP Server",
        transport="stdio",
        command=["python", "-m", "mock_server"],
        timeout_seconds=5.0,
        enabled=True
    )


@pytest.fixture
def sample_tool_metadata(mock_server_config):
    return MCPToolMetadata(
        name="mcp_nmap_scanner",
        description="Port scanner exposed via MCP server",
        category="network_recon",
        version="1.0.0",
        capabilities=MCPToolCapabilities(
            can_async=True,
            supports_streaming=False,
            requires_auth=True,
            is_read_only=True,
            is_destructive=False
        ),
        input_schema={"type": "object", "properties": {"target": {"type": "string"}}},
        output_schema={"type": "object"},
        health="HEALTHY",
        enabled=True,
        server_id=mock_server_config.server_id
    )


def test_mcp_tool_metadata_model(sample_tool_metadata):
    """Test unified MCP tool metadata model serialization and fields."""
    assert sample_tool_metadata.name == "mcp_nmap_scanner"
    assert sample_tool_metadata.category == "network_recon"
    assert sample_tool_metadata.capabilities.is_read_only is True
    assert sample_tool_metadata.capabilities.is_destructive is False
    assert sample_tool_metadata.health == "HEALTHY"


def test_mcp_policy_engine_shell_injection_blocking(sample_tool_metadata):
    """Test Policy Engine prevents arbitrary shell command execution and dangerous characters."""
    policy = MCPPolicyEngine()

    # Safe request
    res_safe = policy.evaluate(
        tool_metadata=sample_tool_metadata,
        target="127.0.0.1",
        arguments={"target": "127.0.0.1", "ports": "80,443"},
        authorized=True
    )
    assert res_safe.allowed is True

    # Dangerous request with command chaining
    res_danger1 = policy.evaluate(
        tool_metadata=sample_tool_metadata,
        target="127.0.0.1",
        arguments={"target": "127.0.0.1; rm -rf /"},
        authorized=True
    )
    assert res_danger1.allowed is False
    assert "forbidden shell meta-characters" in res_danger1.reason

    # Dangerous request with subshell substitution
    res_danger2 = policy.evaluate(
        tool_metadata=sample_tool_metadata,
        target="127.0.0.1",
        arguments={"target": "127.0.0.1 $(whoami)"},
        authorized=True
    )
    assert res_danger2.allowed is False


def test_mcp_policy_engine_authorization_check(sample_tool_metadata):
    """Test Policy Engine enforces target authorization requirement."""
    policy = MCPPolicyEngine()

    res_unauth = policy.evaluate(
        tool_metadata=sample_tool_metadata,
        target="example.com",
        arguments={"target": "example.com"},
        authorized=False
    )
    assert res_unauth.allowed is False
    assert "authorization not acknowledged" in res_unauth.reason


def test_mcp_registry_server_and_tool_discovery(mock_server_config, sample_tool_metadata):
    """Test server registration and tool index discovery."""
    registry = MCPServerRegistry()
    mock_client = MagicMock(spec=MCPClient)
    mock_client.list_tools.return_value = [sample_tool_metadata]

    ok = registry.register_server(mock_server_config, client=mock_client)
    assert ok is True

    tool = registry.get_tool("mcp_nmap_scanner")
    assert tool is not None
    assert tool.name == "mcp_nmap_scanner"
    assert tool.server_id == "mock_mcp_server"


def test_mcp_gateway_execution(mock_server_config, sample_tool_metadata):
    """Test MCPGateway processes, validates, and routes tool calls to client returning evidence."""
    registry = MCPServerRegistry()
    mock_client = MagicMock(spec=MCPClient)
    mock_client.call_tool.return_value = {
        "result": {"open_ports": [80, 443], "status": "scan complete"}
    }

    registry.register_server(mock_server_config, client=mock_client)
    gateway = MCPGateway(registry=registry)

    evidence: MCPExecutionEvidence = gateway.execute_tool(
        tool_name="mcp_nmap_scanner",
        arguments={"ports": "80,443"},
        target="127.0.0.1",
        authorized=True
    )

    assert evidence.success is True
    assert evidence.tool_name == "mcp_nmap_scanner"
    assert evidence.server_id == "mock_mcp_server"
    assert evidence.data["open_ports"] == [80, 443]


def test_mcp_health_monitor(mock_server_config, sample_tool_metadata):
    """Test MCPHealthMonitor checks server connectivity and updates tool health."""
    registry = MCPServerRegistry()
    mock_client = MagicMock(spec=MCPClient)
    mock_client.ping.return_value = True
    mock_client.list_tools.return_value = [sample_tool_metadata]

    registry.register_server(mock_server_config, client=mock_client)
    monitor = MCPHealthMonitor(registry=registry)

    res = monitor.check_server("mock_mcp_server")
    assert res["status"] == "HEALTHY"
    assert res["latency_ms"] >= 0.0
    assert sample_tool_metadata.health == "HEALTHY"


def test_mcp_plugin_adapter_integration(sample_tool_metadata):
    """Test MCPPluginAdapter bridges MCP tool to native BasePlugin architecture."""
    mock_gateway = MagicMock(spec=MCPGateway)
    mock_gateway.execute_tool.return_value = MCPExecutionEvidence(
        tool_name="mcp_nmap_scanner",
        server_id="mock_mcp_server",
        success=True,
        data={"ports": [80, 443]},
        execution_time_ms=120.0
    )

    adapter = MCPPluginAdapter(metadata=sample_tool_metadata, gateway=mock_gateway)

    assert adapter.name == "mcp_nmap_scanner"
    assert adapter.is_installed() is True

    output = adapter.execute("127.0.0.1", options={"authorized": True})
    assert output.tool == "mcp_nmap_scanner"
    assert output.target == "127.0.0.1"
    assert output.status == "COMPLETED"
    assert output.findings[0]["ports"] == [80, 443]


def test_mcp_cli_commands(cli_runner):
    """Test 'security-ai mcp' CLI subcommands (servers, tools, register)."""
    from app.cli import app

    res_servers = cli_runner.invoke(app, ["mcp", "servers"])
    assert res_servers.exit_code == 0
    assert "REGISTERED MCP SERVER MATRIX" in res_servers.output

    res_tools = cli_runner.invoke(app, ["mcp", "tools"])
    assert res_tools.exit_code == 0
    assert "UNIFIED MCP TOOL INDEX" in res_tools.output

    res_reg = cli_runner.invoke(app, ["mcp", "register", "-i", "test_server", "-n", "Test Server", "-t", "http", "-u", "http://localhost:9000"])
    assert res_reg.exit_code == 0
    assert "Successfully registered MCP Server" in res_reg.output

