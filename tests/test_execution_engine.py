"""
Unit tests for Advanced Resilient Execution Engine, Checkpointing, and DAG Scheduling.
"""

import time
import pytest
from unittest.mock import MagicMock, patch

from core.config import AppConfig, TimeoutsConfig, PluginTimeoutProfile
from core.planner import ExecutionPlan, PlannedStep
from core.checkpoint import CheckpointManager, AssessmentCheckpoint
from core.scheduler import DependencyScheduler
from core.workflow import WorkflowEngine, UnifiedScanResult
from plugins.base import BasePlugin, StandardPluginOutput


class DummyTimingOutPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "timing_out_tool"

    @property
    def description(self) -> str:
        return "Tool that times out"

    def is_installed(self) -> bool:
        return True

    def build_command(self, target, options=None):
        return ["sleep", "10"]

    def parse(self, stdout, stderr):
        return []

    def execute(self, target, options=None) -> StandardPluginOutput:
        return StandardPluginOutput(
            tool=self.name,
            target=target,
            status="TIMED_OUT",
            findings=[{"finding": "partial_finding_before_timeout"}],
            errors=["Timeout occurred"],
            metadata={"execution_time_ms": 5000.0}
        )


class DummySuccessfulPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "success_tool"

    @property
    def description(self) -> str:
        return "Tool that succeeds"

    def is_installed(self) -> bool:
        return True

    def build_command(self, target, options=None):
        return ["echo", "ok"]

    def parse(self, stdout, stderr):
        return []

    def execute(self, target, options=None) -> StandardPluginOutput:
        return StandardPluginOutput(
            tool=self.name,
            target=target,
            status="COMPLETED",
            findings=[{"finding": "success_finding"}],
            errors=[],
            metadata={"execution_time_ms": 100.0}
        )


def test_independent_timeouts_resolution():
    """Test independent timeouts resolution across fast, standard, and deep profiles."""
    cfg = AppConfig(
        timeouts=TimeoutsConfig(
            nmap=PluginTimeoutProfile(fast=120, standard=600, deep=1800),
            nuclei=PluginTimeoutProfile(fast=300, standard=1800, deep=7200)
        )
    )
    assert cfg.timeouts.get_timeout("nmap", profile="fast") == 120
    assert cfg.timeouts.get_timeout("nmap", profile="deep") == 1800
    assert cfg.timeouts.get_timeout("nuclei", profile="fast") == 300
    assert cfg.timeouts.get_timeout("nuclei", profile="deep") == 7200


def test_dag_scheduler_tiers():
    """Test DependencyScheduler generates topological execution tiers."""
    plan = ExecutionPlan(
        target="127.0.0.1",
        scope_summary="DAG test",
        selected_plugins=["nmap", "whatweb", "nikto"],
        execution_order=[
            PlannedStep(step_number=1, tool="nmap", purpose="Recon"),
            PlannedStep(step_number=2, tool="whatweb", purpose="Fingerprint", depends_on=[1]),
            PlannedStep(step_number=3, tool="nikto", purpose="Scan", depends_on=[1]),
            PlannedStep(step_number=4, tool="report_aggregator", purpose="Report", depends_on=[2, 3]),
        ],
        estimated_duration_seconds=10.0,
        reasoning="DAG test reasoning"
    )

    tiers = DependencyScheduler.build_execution_tiers(plan)
    assert len(tiers) == 3
    assert [s.tool for s in tiers[0]] == ["nmap"]
    assert sorted([s.tool for s in tiers[1]]) == ["nikto", "whatweb"]
    assert [s.tool for s in tiers[2]] == ["report_aggregator"]


def test_independent_step_execution_and_partial_result_preservation(tmp_path):
    """Test tool timeout on step 1 does NOT stop step 2, and preserves partial findings."""
    cp_mgr = CheckpointManager(checkpoints_dir=str(tmp_path / "checkpoints"))
    engine = WorkflowEngine(checkpoint_manager=cp_mgr)

    engine.registry.register(DummyTimingOutPlugin())
    engine.registry.register(DummySuccessfulPlugin())

    plan = ExecutionPlan(
        target="127.0.0.1",
        scope_summary="Fault isolation test",
        selected_plugins=["timing_out_tool", "success_tool"],
        execution_order=[
            PlannedStep(step_number=1, tool="timing_out_tool", purpose="Step 1 timeout"),
            PlannedStep(step_number=2, tool="success_tool", purpose="Step 2 success"),
        ],
        estimated_duration_seconds=5.0,
        reasoning="Test"
    )

    res: UnifiedScanResult = engine.execute_plan(plan, authorized=True, profile="fast")

    assert len(res.step_results) == 2
    assert res.step_results[0].status == "TIMED_OUT"
    assert res.step_results[0].findings[0]["finding"] == "partial_finding_before_timeout"
    assert res.step_results[1].status == "COMPLETED"
    assert res.step_results[1].findings[0]["finding"] == "success_finding"


def test_checkpointing_and_resumption(tmp_path):
    """Test saving checkpoint and resuming from previously completed steps."""
    cp_mgr = CheckpointManager(checkpoints_dir=str(tmp_path / "checkpoints"))
    engine = WorkflowEngine(checkpoint_manager=cp_mgr)

    engine.registry.register(DummySuccessfulPlugin())

    plan = ExecutionPlan(
        target="127.0.0.1",
        scope_summary="Checkpoint test",
        selected_plugins=["success_tool"],
        execution_order=[
            PlannedStep(step_number=1, tool="success_tool", purpose="Step 1"),
            PlannedStep(step_number=2, tool="success_tool", purpose="Step 2"),
        ],
        estimated_duration_seconds=5.0,
        reasoning="Test"
    )

    # Initial execution
    res1 = engine.execute_plan(plan, authorized=True)
    assert len(res1.step_results) == 2
    cp_id = res1.assessment_id

    # Verify checkpoint saved on disk
    cp_loaded = cp_mgr.load_checkpoint(cp_id)
    assert cp_loaded is not None
    assert len(cp_loaded.completed_step_numbers) == 2

    # Resume execution with same checkpoint
    res2 = engine.execute_plan(plan, authorized=True, resume_checkpoint_id=cp_id)
    assert len(res2.step_results) == 2
    assert res2.assessment_id == cp_id
