"""
Workflow Execution Engine.

Validates input target format, enforces mandatory authorization acknowledgement,
executes planned steps sequentially, collects JSON outputs, and returns unified results.
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.planner import ExecutionPlan
from core.registry import get_registry, PluginRegistry
from plugins.base import StandardPluginOutput
from core.logger import get_logger

logger = get_logger("workflow")


class UnifiedScanResult(BaseModel):
    """Unified JSON scan result aggregating output across all workflow steps."""
    target: str = Field(..., description="Target evaluated.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Execution completion timestamp."
    )
    authorized: bool = Field(..., description="Target authorization acknowledgement flag.")
    total_duration_ms: float = Field(..., description="Total wall-clock duration in milliseconds.")
    step_results: List[StandardPluginOutput] = Field(default_factory=list, description="Plugin outputs.")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Aggregated finding counts.")


class WorkflowEngine:
    """Orchestrates security scanning workflows and aggregates JSON results."""

    def __init__(self, registry: Optional[PluginRegistry] = None):
        self.registry = registry or get_registry()

    def validate_target(self, target: str) -> bool:
        """Validate target string format (IP, Domain, URL)."""
        if not target or not target.strip():
            return False

        t = target.strip()
        # Basic URL check
        if t.startswith("http://") or t.startswith("https://"):
            return True

        # IP address or domain regex pattern
        domain_or_ip = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}|"  # Domain
            r"^(?:\d{1,3}\.){3}\d{1,3}$"  # IPv4
        )
        return bool(domain_or_ip.match(t))

    def require_authorization_acknowledgement(self, target: str, confirmed: bool) -> bool:
        """Enforce strict authorization guardrail check."""
        if not confirmed:
            logger.error(f"Authorization denied for target '{target}'. Execution halted.")
            return False
        logger.info(f"Authorization confirmed for target '{target}'.")
        return True

    def execute_plan(self, plan: ExecutionPlan, authorized: bool) -> UnifiedScanResult:
        """Execute planned steps sequentially, collect JSON results, and return unified scan output."""
        if not self.validate_target(plan.target):
            raise ValueError(f"Invalid target format: '{plan.target}'")

        if not self.require_authorization_acknowledgement(plan.target, authorized):
            raise PermissionError(f"Execution aborted: Target '{plan.target}' not authorized.")

        logger.info(f"Executing workflow plan for target '{plan.target}' ({len(plan.execution_order)} steps)...")

        step_outputs: List[StandardPluginOutput] = []
        total_time_ms = 0.0

        for step in plan.execution_order:
            tool_name = step.tool
            plugin = self.registry.get_plugin(tool_name)

            if not plugin:
                logger.warning(f"Plugin '{tool_name}' not found in registry. Skipping step {step.step_number}.")
                step_outputs.append(StandardPluginOutput(
                    tool=tool_name,
                    target=plan.target,
                    status="FAILED",
                    errors=[f"Plugin '{tool_name}' not found in registry."]
                ))
                continue

            logger.info(f"Running step {step.step_number}/{len(plan.execution_order)}: {tool_name}")
            output = plugin.execute(plan.target, step.options)
            step_outputs.append(output)

            duration = output.metadata.get("execution_time_ms", 0.0)
            total_time_ms += duration

        total_findings = sum(len(out.findings) for out in step_outputs)
        total_errors = sum(len(out.errors) for out in step_outputs)

        return UnifiedScanResult(
            target=plan.target,
            authorized=authorized,
            total_duration_ms=round(total_time_ms, 2),
            step_results=step_outputs,
            summary={
                "steps_executed": len(step_outputs),
                "total_findings": total_findings,
                "total_errors": total_errors,
            }
        )
