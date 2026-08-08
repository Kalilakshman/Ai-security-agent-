"""
MCP Transport Client implementing JSON-RPC 2.0 protocol over stdio and HTTP/SSE transports.
"""

import json
import asyncio
import subprocess
import httpx
from typing import Dict, Any, List, Optional
from core.mcp.models import MCPServerConfig, MCPToolMetadata, MCPToolCapabilities
from core.executor import SafeExecutor
from core.logger import get_logger

logger = get_logger("mcp_client")


class MCPClient:
    """Client communicating with an MCP Server over stdio or HTTP/SSE transports."""

    def __init__(self, config: MCPServerConfig, executor: Optional[SafeExecutor] = None):
        self.config = config
        self.executor = executor or SafeExecutor()
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def list_tools(self) -> List[MCPToolMetadata]:
        """Discover tools exposed by the MCP server."""
        if self.config.transport == "http" or self.config.transport == "sse":
            return self._list_tools_http()
        return self._list_tools_stdio()

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], timeout_seconds: Optional[float] = None) -> Dict[str, Any]:
        """Invoke an MCP tool with JSON-RPC arguments."""
        timeout = timeout_seconds if timeout_seconds is not None else self.config.timeout_seconds
        if self.config.transport == "http" or self.config.transport == "sse":
            return self._call_tool_http(tool_name, arguments, timeout)
        return self._call_tool_stdio(tool_name, arguments, timeout)

    def ping((self)) -> bool:
        """Ping the MCP server connection."""
        try:
            if self.config.transport in ("http", "sse"):
                url = f"{self.config.url.rstrip('/')}/ping" if self.config.url else ""
                if not url:
                    return False
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(url, headers=self.config.headers)
                    return resp.status_code == 200
            else:
                # stdio ping via executable presence
                if self.config.command:
                    res = self.executor.execute([self.config.command[0], "--version"], timeout_seconds=3.0)
                    return res.is_success or res.exit_code != 127
                return False
        except Exception as e:
            logger.debug(f"MCP server ping failed for '{self.config.server_id}': {str(e)}")
            return False

    # ─── STDIO TRANSPORT ──────────────────────────────────────────────────

    def _list_tools_stdio(self) -> List[MCPToolMetadata]:
        if not self.config.command:
            return []

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {}
        }
        res = self._exec_stdio_rpc(payload)
        if not res or "result" not in res:
            return []

        tools_data = res.get("result", {}).get("tools", [])
        discovered = []
        for t in tools_data:
            caps = t.get("capabilities", {})
            metadata = MCPToolMetadata(
                name=t.get("name", "unknown"),
                description=t.get("description", ""),
                category=t.get("category", "reconnaissance"),
                version=t.get("version", "1.0.0"),
                capabilities=MCPToolCapabilities(
                    can_async=caps.get("can_async", True),
                    supports_streaming=caps.get("supports_streaming", False),
                    requires_auth=caps.get("requires_auth", True),
                    is_read_only=caps.get("is_read_only", True),
                    is_destructive=caps.get("is_destructive", False),
                ),
                input_schema=t.get("inputSchema", t.get("input_schema", {})),
                output_schema=t.get("outputSchema", t.get("output_schema", {})),
                health="HEALTHY",
                enabled=True,
                server_id=self.config.server_id
            )
            discovered.append(metadata)
        return discovered

    def _call_tool_stdio(self, tool_name: str, arguments: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        if not self.config.command:
            raise ValueError(f"No stdio command configured for server '{self.config.server_id}'")

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        return self._exec_stdio_rpc(payload, timeout=timeout)

    def _exec_stdio_rpc(self, payload: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
        if not self.config.command:
            return {}

        cmd = list(self.config.command)
        input_str = json.dumps(payload)
        timeout_val = timeout if timeout is not None else self.config.timeout_seconds

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False
            )
            stdout_data, stderr_data = process.communicate(input=input_str, timeout=timeout_val)
            if stdout_data and stdout_data.strip():
                # Attempt to parse last JSON line
                for line in reversed(stdout_data.splitlines()):
                    if line.strip().startswith("{") and line.strip().endswith("}"):
                        try:
                            return json.loads(line.strip())
                        except json.JSONDecodeError:
                            continue
            return {"error": {"code": -32603, "message": stderr_data or "No valid JSON-RPC output"}}
        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError(f"MCP stdio server '{self.config.server_id}' timed out after {timeout_val}s")
        except Exception as e:
            logger.error(f"MCP stdio execution failed for '{self.config.server_id}': {str(e)}")
            raise RuntimeError(f"MCP stdio connection error: {str(e)}") from e

    # ─── HTTP TRANSPORT ───────────────────────────────────────────────────

    def _list_tools_http(self) -> List[MCPToolMetadata]:
        if not self.config.url:
            return []

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {}
        }
        url = f"{self.config.url.rstrip('/')}/rpc"
        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                resp = client.post(url, headers=self.config.headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                tools_data = data.get("result", {}).get("tools", [])
                discovered = []
                for t in tools_data:
                    discovered.append(MCPToolMetadata(
                        name=t.get("name"),
                        description=t.get("description", ""),
                        category=t.get("category", "reconnaissance"),
                        version=t.get("version", "1.0.0"),
                        capabilities=MCPToolCapabilities(**t.get("capabilities", {})),
                        input_schema=t.get("inputSchema", {}),
                        output_schema=t.get("outputSchema", {}),
                        health="HEALTHY",
                        enabled=True,
                        server_id=self.config.server_id
                    ))
                return discovered
        except Exception as e:
            logger.error(f"HTTP list_tools failed for server '{self.config.server_id}': {str(e)}")
            return []

    def _call_tool_http(self, tool_name: str, arguments: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        if not self.config.url:
            raise ValueError(f"No HTTP URL configured for server '{self.config.server_id}'")

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        url = f"{self.config.url.rstrip('/')}/rpc"
        with httpx.Client(timeout=timeout) as client:
            try:
                resp = client.post(url, headers=self.config.headers, json=payload)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"HTTP call_tool failed for '{tool_name}' on '{self.config.server_id}': {str(e)}")
                raise RuntimeError(f"MCP HTTP request error: {str(e)}") from e
