# Model Context Protocol (MCP) Integration Guide

The **AI Security Orchestrator CLI** features a secure Model Context Protocol (MCP) Integration Layer (`core/mcp/`) sitting between the AI Planner and external tool servers.

---

## 🔌 Architecture Flow

```
AI Planner -> Policy Engine -> MCP Gateway -> MCP Server (stdio/HTTP) -> Tool -> Evidence
```

The AI Planner never executes arbitrary shell strings directly. All tool calls route through JSON-RPC 2.0 requests managed by `MCPGateway`.

---

## 🛠️ MCP Components

1. **`MCPToolMetadata` (`core/mcp/models.py`)**:
   - Unified MCP tool model containing `name`, `description`, `category`, `version`, `capabilities`, `input_schema`, `output_schema`, `health`, `enabled`, and `server_id`.

2. **`MCPServerConfig` (`core/mcp/models.py`)**:
   - Configures server transport (`stdio`, `http`, `sse`), process command vectors, or HTTP endpoints.

3. **`MCPClient` (`core/mcp/client.py`)**:
   - JSON-RPC 2.0 transport client communicating over subprocess stdio pipes or HTTP endpoints (`tools/list`, `tools/call`, `ping`, `initialize`).

4. **`MCPServerRegistry` (`core/mcp/registry.py`)**:
   - Central registry for server registration and unified tool discovery.

5. **`MCPHealthMonitor` (`core/mcp/health.py`)**:
   - Conducts periodic health checks (`ping`) updating server and tool operational states (`HEALTHY`, `UNHEALTHY`).

6. **`MCPGateway` (`core/mcp/gateway.py`)**:
   - Intercepts AI tool invocation requests, validates guardrails via `MCPPolicyEngine`, dispatches requests to `MCPClient`, and returns structured `MCPExecutionEvidence`.

---

## 💻 Registering an MCP Server

MCP servers can be registered programmatically or via configuration:

```python
from core.mcp import get_mcp_registry, MCPServerConfig

registry = get_mcp_registry()

# Register stdio transport server
server_cfg = MCPServerConfig(
    server_id="nmap_mcp_server",
    name="Nmap Security MCP Server",
    transport="stdio",
    command=["python", "-m", "nmap_mcp_server"],
    timeout_seconds=60.0
)

registry.register_server(server_cfg)
```
