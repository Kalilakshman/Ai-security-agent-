"""
Unit tests for Typer CLI commands (app/cli.py).
"""

import pytest
from unittest.mock import patch
from app.cli import app


def test_cli_help(cli_runner):
    """Test displaying global CLI help menu."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AI Security Orchestrator CLI" in result.output
    assert "doctor" in result.output
    assert "plugins" in result.output
    assert "config" in result.output
    assert "llm" in result.output


def test_cli_doctor(cli_runner):
    """Test running 'security-ai doctor' diagnostic command."""
    result = cli_runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "SYSTEM DIAGNOSTICS & CORE SUBSYSTEM AUDIT" in result.output
    assert "Python Core Runtime" in result.output
    assert "Subprocess Sandbox" in result.output


def test_cli_config(cli_runner):
    """Test running 'security-ai config' settings command."""
    result = cli_runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "ACTIVE FRAMEWORK CONFIGURATION & BOUNDARIES" in result.output
    assert "Provider-Independent LLM Neural Hub" in result.output


def test_cli_plugins(cli_runner):
    """Test running 'security-ai plugins' command."""
    result = cli_runner.invoke(app, ["plugins"])
    assert result.exit_code == 0
    assert "DYNAMIC SECURITY TOOL MATRIX" in result.output


def test_cli_scan_workflow(cli_runner):
    """Test 'scan' command with auto-approval flag."""
    with patch("core.planner.AIPlanner.generate_plan") as mock_plan:
        from core.planner import ExecutionPlan
        mock_plan.return_value = ExecutionPlan(
            target="127.0.0.1",
            scope_summary="Localhost test",
            selected_plugins=[],
            execution_order=[],
            estimated_duration_seconds=5.0,
            reasoning="Test reasoning"
        )
        result = cli_runner.invoke(app, ["scan", "127.0.0.1", "-y"])
        assert result.exit_code == 0
        assert "INITIATING AUTOMATED CYBER SCANNER" in result.output
        assert "127.0.0.1" in result.output


def test_cli_orchestrate_placeholder(cli_runner):
    """Test placeholder 'orchestrate' command."""
    result = cli_runner.invoke(app, ["orchestrate", "playbook.yaml"])
    assert result.exit_code == 0
    assert "Command 'orchestrate' is a placeholder" in result.output


def test_cli_analyze_placeholder(cli_runner):
    """Test placeholder 'analyze' command."""
    result = cli_runner.invoke(app, ["analyze", "scan.json"])
    assert result.exit_code == 0
    assert "Command 'analyze' is a placeholder" in result.output
