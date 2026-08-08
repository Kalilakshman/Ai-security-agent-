"""
MCP Health Monitor checking server connectivity and tool availability.
"""

import time
from typing import Dict, Any, Optional
from core.mcp.registry import MCPServerRegistry, get_mcp_registry
from core.logger import get_logger

logger = get_logger("mcp_health")


class MCPHealthMonitor:
    """Monitors health, connectivity, and latency of registered MCP servers and tools."""

    def __init__(self, registry: Optional[MCPServerRegistry] = None):
        self.registry = registry or get_mcp_registry()

    def check_server(self, server_id: str) -> Dict[str, Any]:
        """Perform health check against a specific registered MCP server."""
        server_cfg = self.registry.get_server(server_id)
        client = self.registry.get_client(server_id)

        if not server_cfg or not client:
            return {
                "server_id": server_id,
                "status": "UNHEALTHY",
                "reason": f"Server '{server_id}' not found in registry.",
                "latency_ms": 0.0
            }

        if not server_cfg.enabled:
            return {
                "server_id": server_id,
                "status": "DISABLED",
                "reason": "Server is disabled in configuration.",
                "latency_ms": 0.0
            }

        start_time = time.perf_counter()
        is_alive = client.ping()
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        status = "HEALTHY" if is_alive else "UNHEALTHY"
        logger.debug(f"MCP Health Check for '{server_id}': {status} ({latency_ms:.1f}ms)")

        # Update health status of all tools associated with this server
        for name, meta in self.registry._tools.values():
            if meta.server_id == server_id:
                meta.health = status

        return {
            "server_id": server_id,
            "status": status,
            "latency_ms": round(latency_ms, 2),
            "transport": server_cfg.transport
        }

    def check_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks across all registered servers."""
        results = {}
        for sid in self.registry.list_servers().keys():
            results[sid] = self.check_server(sid)
        return results
