"""
MCP Server Registry and Tool Discovery Index.
"""

from typing import Dict, List, Optional, Tuple
from core.mcp.models import MCPServerConfig, MCPToolMetadata, MCPToolCapabilities
from core.mcp.client import MCPClient
from core.logger import get_logger

logger = get_logger("mcp_registry")


class MCPServerRegistry:
    """Central registry managing MCP servers, clients, and unified tool metadata."""

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._clients: Dict[str, MCPClient] = {}
        self._tools: Dict[str, Tuple[str, MCPToolMetadata]] = {}  # tool_name -> (server_id, metadata)
        self._register_default_mcp_servers()

    def _register_default_mcp_servers(self) -> None:
        """Initialize standard default MCP servers in registry."""
        default_servers = [
            MCPServerConfig(
                server_id="network_mcp_server",
                name="Network Recon MCP Subsystem",
                transport="stdio",
                command=["python3", "-m", "network_mcp"],
                enabled=True
            ),
            MCPServerConfig(
                server_id="web_mcp_server",
                name="Web Assessment MCP Hub",
                transport="http",
                url="http://localhost:8000/mcp",
                enabled=True
            ),
            MCPServerConfig(
                server_id="analysis_mcp_server",
                name="AI Triage & Analysis MCP Server",
                transport="stdio",
                command=["python3", "-m", "analysis_mcp"],
                enabled=True
            ),
        ]

        for s_cfg in default_servers:
            self._servers[s_cfg.server_id] = s_cfg
            self._clients[s_cfg.server_id] = MCPClient(s_cfg)

        # Register standard default MCP tools into index
        default_mcp_tools = [
            MCPToolMetadata(
                name="mcp_network_scanner",
                description="MCP Network scanner tool module.",
                category="network_recon",
                version="1.0.0",
                capabilities=MCPToolCapabilities(supports_async=True, supports_auth=True),
                input_schema={"target": {"type": "string"}},
                output_schema={"raw": {"type": "string"}},
                health="HEALTHY",
                enabled=True,
                server_id="network_mcp_server"
            ),
            MCPToolMetadata(
                name="mcp_web_analyzer",
                description="MCP Web application security assessment module.",
                category="web_assessment",
                version="1.0.0",
                capabilities=MCPToolCapabilities(supports_async=True, supports_auth=True),
                input_schema={"target": {"type": "string"}},
                output_schema={"raw": {"type": "string"}},
                health="HEALTHY",
                enabled=True,
                server_id="web_mcp_server"
            ),
            MCPToolMetadata(
                name="mcp_evidence_triage",
                description="MCP Evidence analysis and vulnerability triage module.",
                category="ai_analysis",
                version="1.0.0",
                capabilities=MCPToolCapabilities(supports_async=True, supports_auth=True),
                input_schema={"target": {"type": "string"}},
                output_schema={"raw": {"type": "string"}},
                health="HEALTHY",
                enabled=True,
                server_id="analysis_mcp_server"
            ),
        ]

        for t_meta in default_mcp_tools:
            self.register_tool(t_meta)

    def register_server(self, config: MCPServerConfig, client: Optional[MCPClient] = None) -> bool:
        """Register an MCP server and discover its exposed tools."""
        sid = config.server_id
        self._servers[sid] = config
        mcp_client = client or MCPClient(config)
        self._clients[sid] = mcp_client

        if not config.enabled:
            logger.info(f"Registered MCP server '{sid}' (Disabled).")
            return True

        # Discover tools exposed by server
        try:
            discovered = mcp_client.list_tools()
            for tool_meta in discovered:
                self.register_tool(tool_meta)
            logger.info(f"Registered MCP server '{sid}' with {len(discovered)} discovered tools.")
            return True
        except Exception as e:
            logger.warning(f"Failed to discover tools for MCP server '{sid}': {str(e)}")
            return False

    def unregister_server(self, server_id: str) -> None:
        """Remove a server and its tools from the registry."""
        self._servers.pop(server_id, None)
        self._clients.pop(server_id, None)
        to_remove = [name for name, (sid, _) in self._tools.items() if sid == server_id]
        for name in to_remove:
            self._tools.pop(name, None)
        logger.info(f"Unregistered MCP server '{server_id}' and removed {len(to_remove)} associated tools.")

    def register_tool(self, metadata: MCPToolMetadata) -> None:
        """Register or update a tool metadata entry in the unified index."""
        self._tools[metadata.name] = (metadata.server_id, metadata)
        logger.debug(f"Registered MCP tool: '{metadata.name}' on server '{metadata.server_id}'.")

    def get_server(self, server_id: str) -> Optional[MCPServerConfig]:
        """Retrieve server configuration by ID."""
        return self._servers.get(server_id)

    def get_client(self, server_id: str) -> Optional[MCPClient]:
        """Retrieve MCP client instance by server ID."""
        return self._clients.get(server_id)

    def get_tool(self, tool_name: str) -> Optional[MCPToolMetadata]:
        """Retrieve metadata for a registered MCP tool."""
        entry = self._tools.get(tool_name)
        return entry[1] if entry else None

    def get_tool_location(self, tool_name: str) -> Optional[Tuple[str, MCPToolMetadata]]:
        """Retrieve (server_id, metadata) tuple for a tool."""
        return self._tools.get(tool_name)

    def list_servers(self) -> Dict[str, MCPServerConfig]:
        """Return dict of registered server configs."""
        return self._servers.copy()

    def list_tools(self) -> List[MCPToolMetadata]:
        """Return list of all unified MCP tool metadata models."""
        return [meta for _, meta in self._tools.values()]


# Global Singleton Registry Instance
_mcp_registry: Optional[MCPServerRegistry] = None


def get_mcp_registry() -> MCPServerRegistry:
    """Retrieve global MCPServerRegistry singleton instance."""
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPServerRegistry()
    return _mcp_registry
