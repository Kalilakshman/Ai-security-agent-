"""
MCP Gateway Component — Intercepts and routes AI planner tool requests through Policy Engine to MCP Servers.
"""

import time
from typing import Dict, Any, Optional
from core.mcp.models import (
    MCPRequestPayload,
    MCPExecutionEvidence,
    MCPToolMetadata,
)
from core.mcp.policy import MCPPolicyEngine, PolicyCheckResult
from core.mcp.registry import MCPServerRegistry, get_mcp_registry
from core.logger import get_logger

logger = get_logger("mcp_gateway")


class MCPGateway:
    """Gateway layer enforcing security policy, timeout handling, error isolation, and evidence packaging.
    
    Guarantees:
    - Sits strictly between AI Planner/Workflow Engine and external tools.
    - Prevents arbitrary shell command execution via Policy Engine validation.
    - Wraps output into structured MCPExecutionEvidence.
    """

    def __init__(
        self,
        policy_engine: Optional[MCPPolicyEngine] = None,
        registry: Optional[MCPServerRegistry] = None
    ):
        self.policy_engine = policy_engine or MCPPolicyEngine()
        self.registry = registry or get_mcp_registry()

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        target: Optional[str] = None,
        authorized: bool = False,
        timeout_seconds: Optional[float] = None
    ) -> MCPExecutionEvidence:
        """Process, validate, route, and execute an MCP tool invocation request.

        Args:
            tool_name: Registered MCP tool identifier.
            arguments: Tool input parameters.
            target: Optional target host, domain, IP, or URL.
            authorized: Authorization acknowledgement flag.
            timeout_seconds: Hard execution timeout override.

        Returns:
            Structured MCPExecutionEvidence container.
        """
        start_time = time.perf_counter()

        # Step 1: Resolve tool and hosting server from registry
        tool_entry = self.registry.get_tool_location(tool_name)
        if not tool_entry:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"MCP Gateway Error: Tool '{tool_name}' not found in registry.")
            return MCPExecutionEvidence(
                tool_name=tool_name,
                server_id="unknown",
                success=False,
                status_code=404,
                errors=[f"Tool '{tool_name}' is not registered in the MCP Registry."],
                execution_time_ms=round(duration_ms, 2)
            )

        server_id, tool_metadata = tool_entry

        # Step 2: Enforce security policy check (Prevents shell injection & arbitrary commands)
        policy_res: PolicyCheckResult = self.policy_engine.evaluate(
            tool_metadata=tool_metadata,
            target=target,
            arguments=arguments,
            authorized=authorized
        )

        if not policy_res.allowed:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"MCP Policy Violation for '{tool_name}': {policy_res.reason}")
            return MCPExecutionEvidence(
                tool_name=tool_name,
                server_id=server_id,
                success=False,
                status_code=403,
                errors=[f"Policy Error: {policy_res.reason}"],
                execution_time_ms=round(duration_ms, 2)
            )

        # Step 3: Resolve server client
        client = self.registry.get_client(server_id)
        if not client:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return MCPExecutionEvidence(
                tool_name=tool_name,
                server_id=server_id,
                success=False,
                status_code=500,
                errors=[f"Client connection for server '{server_id}' not available."],
                execution_time_ms=round(duration_ms, 2)
            )

        # Step 4: Dispatch tool call to MCP server with timeout & error handling
        sanitized_args = policy_res.sanitized_arguments
        if target and "target" not in sanitized_args:
            sanitized_args["target"] = target

        logger.info(f"MCP Gateway dispatching '{tool_name}' to server '{server_id}'")

        try:
            raw_result = client.call_tool(
                tool_name=tool_name,
                arguments=sanitized_args,
                timeout_seconds=timeout_seconds
            )

            duration_ms = (time.perf_counter() - start_time) * 1000.0

            if "error" in raw_result:
                err_msg = raw_result["error"].get("message", "MCP Tool Execution Error")
                logger.error(f"MCP Tool '{tool_name}' execution error: {err_msg}")
                return MCPExecutionEvidence(
                    tool_name=tool_name,
                    server_id=server_id,
                    success=False,
                    status_code=raw_result["error"].get("code", 500),
                    errors=[err_msg],
                    execution_time_ms=round(duration_ms, 2)
                )

            data_content = raw_result.get("result", raw_result)

            return MCPExecutionEvidence(
                tool_name=tool_name,
                server_id=server_id,
                success=True,
                status_code=0,
                data=data_content if isinstance(data_content, dict) else {"content": data_content},
                logs=[f"Successfully executed tool '{tool_name}' via MCP Gateway."],
                execution_time_ms=round(duration_ms, 2)
            )

        except TimeoutError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"MCP Gateway timeout executing '{tool_name}': {str(e)}")
            return MCPExecutionEvidence(
                tool_name=tool_name,
                server_id=server_id,
                success=False,
                status_code=408,
                errors=[str(e)],
                execution_time_ms=round(duration_ms, 2)
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception(f"MCP Gateway unhandled error executing '{tool_name}': {str(e)}")
            return MCPExecutionEvidence(
                tool_name=tool_name,
                server_id=server_id,
                success=False,
                status_code=500,
                errors=[f"MCP Gateway execution error: {str(e)}"],
                execution_time_ms=round(duration_ms, 2)
            )
