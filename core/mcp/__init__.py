"""
Model Context Protocol (MCP) Integration Layer Package.
"""

from core.mcp.models import (
    MCPToolCapabilities,
    MCPToolMetadata,
    MCPServerConfig,
    MCPRequestPayload,
    MCPExecutionEvidence,
)
from core.mcp.policy import MCPPolicyEngine, PolicyCheckResult
from core.mcp.client import MCPClient
from core.mcp.registry import MCPServerRegistry, get_mcp_registry
from core.mcp.health import MCPHealthMonitor
from core.mcp.gateway import MCPGateway

__all__ = [
    "MCPToolCapabilities",
    "MCPToolMetadata",
    "MCPServerConfig",
    "MCPRequestPayload",
    "MCPExecutionEvidence",
    "MCPPolicyEngine",
    "PolicyCheckResult",
    "MCPClient",
    "MCPServerRegistry",
    "get_mcp_registry",
    "MCPHealthMonitor",
    "MCPGateway",
]
