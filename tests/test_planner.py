"""
Unit tests for Phase 3 OpenRouter client, AI Planner, and Workflow engine.
"""

import pytest
from core.llm import OpenRouterClient
from core.planner import AIPlanner, ExecutionPlan
from core.workflow import WorkflowEngine, UnifiedScanResult


def test_workflow_engine_target_validation():
    """Test target string validation for domains, IPs, and URLs."""
    engine = WorkflowEngine()

    assert engine.validate_target("example.com") is True
    assert engine.validate_target("http://192.168.1.1") is True
    assert engine.validate_target("10.0.0.1") is True
    assert engine.validate_target("https://scanme.nmap.org") is True
    assert engine.validate_target("invalid target with spaces") is False


def test_workflow_engine_authorization_enforcement():
    """Test target authorization acknowledgement guardrail."""
    engine = WorkflowEngine()

    assert engine.require_authorization_acknowledgement("example.com", confirmed=True) is True
    assert engine.require_authorization_acknowledgement("example.com", confirmed=False) is False


def test_ai_planner_plan_structure(sample_config):
    """Test AI Planner produces structured ExecutionPlan."""
    planner = AIPlanner()
    plan = planner.generate_plan("scanme.nmap.org")

    assert isinstance(plan, ExecutionPlan)
    assert plan.target == "scanme.nmap.org"
    assert isinstance(plan.selected_plugins, list)
    assert isinstance(plan.execution_order, list)
    assert len(plan.execution_order) > 0
    assert len(plan.reasoning) > 0


def test_workflow_execution_integration():
    """Test complete workflow plan execution."""
    planner = AIPlanner()
    engine = WorkflowEngine()

    plan = planner.generate_plan("127.0.0.1")
    result = engine.execute_plan(plan, authorized=True)

    assert isinstance(result, UnifiedScanResult)
    assert result.target == "127.0.0.1"
    assert result.authorized is True
    assert len(result.step_results) == len(plan.execution_order)
    assert "total_findings" in result.summary
