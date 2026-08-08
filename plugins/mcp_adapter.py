"""
MCP Plugin Adapter bridging MCP Tools into the Security Orchestrator BasePlugin system.
"""

from typing import Dict, List, Any, Optional
from plugins.base import BasePlugin, StandardPluginOutput
from core.mcp.gateway import MCPGateway
from core.mcp.models import MCPToolMetadata, MCPExecutionEvidence
from core.logger import get_logger

logger = get_logger("mcp_adapter")


class MCPPluginAdapter(BasePlugin):
    """Adapter class enabling MCP tools to act as native BasePlugin implementations."""

    def __init__(self, metadata: MCPToolMetadata, gateway: Optional[MCPGateway] = None):
        super().__init__()
        self.metadata_info = metadata
        self.gateway = gateway or MCPGateway()

    @property
    def name(self) -> str:
        return self.metadata_info.name

    @property
    def description(self) -> str:
        return self.metadata_info.description

    def is_installed(self) -> bool:
        return self.metadata_info.enabled and self.metadata_info.health != "UNHEALTHY"

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        # MCP tools use JSON-RPC rather than command vector strings directly
        return ["mcp-tool-call", self.name, target]

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        return []

    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> StandardPluginOutput:
        """Execute MCP tool via MCPGateway and return StandardPluginOutput schema."""
        opts = options or {}
        timeout = float(opts.get("timeout", 60.0))
        authorized = bool(opts.get("authorized", True))

        evidence: MCPExecutionEvidence = self.gateway.execute_tool(
            tool_name=self.name,
            arguments=opts,
            target=target,
            authorized=authorized,
            timeout_seconds=timeout
        )

        status = "COMPLETED" if evidence.success else ("TIMED_OUT" if evidence.status_code == 408 else "FAILED")
        findings = [evidence.data] if evidence.data else []

        return StandardPluginOutput(
            tool=self.name,
            target=target,
            status=status,
            findings=findings,
            errors=evidence.errors,
            metadata={
                "server_id": evidence.server_id,
                "execution_time_ms": evidence.execution_time_ms,
                "status_code": evidence.status_code,
                "logs": evidence.logs,
            }
        )
