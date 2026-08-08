"""
Observability and Telemetry Subsystem.

Tracks execution metrics, tool health metrics, LLM latency & token metrics,
report generation metrics, and security policy decision statistics.
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.logger import get_logger

logger = get_logger("metrics")


class MetricsSnapshot(BaseModel):
    """Snapshot of active system telemetry metrics."""
    total_assessments: int = Field(default=0, description="Total scan assessments executed.")
    successful_assessments: int = Field(default=0, description="Successful scan assessments.")
    failed_assessments: int = Field(default=0, description="Failed scan assessments.")
    total_tool_executions: int = Field(default=0, description="Total tool invocations.")
    tool_failures: int = Field(default=0, description="Tool execution failures.")
    tool_timeouts: int = Field(default=0, description="Tool execution timeouts.")
    llm_calls_count: int = Field(default=0, description="Total LLM API completion requests.")
    llm_total_latency_ms: float = Field(default=0.0, description="Cumulative LLM latency in milliseconds.")
    reports_generated_count: int = Field(default=0, description="Total security reports generated.")
    policy_blocks_count: int = Field(default=0, description="Total execution requests blocked by policy.")


class MetricsCollector:
    """Thread-safe telemetry and observability metrics collector."""

    def __init__(self):
        self._snapshot = MetricsSnapshot()

    def record_assessment(self, success: bool = True) -> None:
        self._snapshot.total_assessments += 1
        if success:
            self._snapshot.successful_assessments += 1
        else:
            self._snapshot.failed_assessments += 1

    def record_tool_execution(self, status: str = "COMPLETED") -> None:
        self._snapshot.total_tool_executions += 1
        if status == "TIMED_OUT":
            self._snapshot.tool_timeouts += 1
        elif status == "FAILED":
            self._snapshot.tool_failures += 1

    def record_llm_call(self, latency_ms: float) -> None:
        self._snapshot.llm_calls_count += 1
        self._snapshot.llm_total_latency_ms += latency_ms

    def record_report_generated(self) -> None:
        self._snapshot.reports_generated_count += 1

    def record_policy_block(self) -> None:
        self._snapshot.policy_blocks_count += 1

    def get_snapshot(self) -> MetricsSnapshot:
        return self._snapshot.model_copy()


# Global Singleton Collector Instance
_metrics_instance: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
