"""
Pydantic Data Models for Model Context Protocol (MCP) Integration Layer.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class MCPToolCapabilities(BaseModel):
    """Capabilities exposed by an MCP tool."""
    can_async: bool = Field(default=True, description="Supports asynchronous execution.")
    supports_streaming: bool = Field(default=False, description="Supports real-time output streaming.")
    requires_auth: bool = Field(default=True, description="Requires explicit target authorization.")
    is_read_only: bool = Field(default=True, description="Tool performs non-destructive read/scan operations.")
    is_destructive: bool = Field(default=False, description="Tool performs state-modifying actions.")


class MCPToolMetadata(BaseModel):
    """Unified MCP Tool Model exposing required tool metadata."""
    name: str = Field(..., description="Tool identifier name.")
    description: str = Field(..., description="Capability description.")
    category: str = Field(default="reconnaissance", description="Tool category (network_recon, web_assessment, vuln_scan).")
    version: str = Field(default="1.0.0", description="Semantic version string.")
    capabilities: MCPToolCapabilities = Field(default_factory=MCPToolCapabilities, description="Tool capabilities.")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for input arguments.")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for output data.")
    health: str = Field(default="HEALTHY", description="Operational health (HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN).")
    enabled: bool = Field(default=True, description="Tool enabled status flag.")
    server_id: str = Field(..., description="ID of the hosting MCP Server.")


class MCPServerConfig(BaseModel):
    """Configuration for an MCP Server connection."""
    server_id: str = Field(..., description="Unique server identifier.")
    name: str = Field(..., description="Human-readable server name.")
    transport: str = Field(default="stdio", description="Transport layer ('stdio', 'sse', 'http').")
    command: Optional[List[str]] = Field(default=None, description="Command vector for stdio transport.")
    url: Optional[str] = Field(default=None, description="Endpoint URL for SSE or HTTP transport.")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for remote transports.")
    timeout_seconds: float = Field(default=60.0, description="Server response timeout in seconds.")
    enabled: bool = Field(default=True, description="Server enabled flag.")


class MCPRequestPayload(BaseModel):
    """Structured request payload for invoking an MCP tool."""
    server_id: str = Field(..., description="Target MCP server identifier.")
    tool_name: str = Field(..., description="MCP tool name to invoke.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool input arguments.")
    target: Optional[str] = Field(default=None, description="Target host, domain, IP, or URL.")
    timeout_seconds: Optional[float] = Field(default=None, description="Execution timeout override.")


class MCPExecutionEvidence(BaseModel):
    """Structured execution result and evidence produced by an MCP tool."""
    tool_name: str = Field(..., description="Executed tool name.")
    server_id: str = Field(..., description="Hosting server identifier.")
    success: bool = Field(..., description="Execution success flag.")
    status_code: int = Field(default=0, description="Return status code (0 for success).")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured output payload data.")
    logs: List[str] = Field(default_factory=list, description="Execution log entries.")
    errors: List[str] = Field(default_factory=list, description="Captured error messages.")
    execution_time_ms: float = Field(..., description="Wall-clock duration in milliseconds.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Execution timestamp."
    )
