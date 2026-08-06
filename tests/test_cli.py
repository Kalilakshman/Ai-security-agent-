"""
Unit tests for Typer CLI commands (app/cli.py).
"""

import pytest
from app.cli import app


def test_cli_help(cli_runner):
    """Test displaying global CLI help menu."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AI Security Orchestrator CLI" in result.output
    assert "doctor" in result.output
    assert "plugins" in result.output
    assert "config" in result.output


def test_cli_doctor(cli_runner):
    """Test running 'security-ai doctor' diagnostic command."""
    result = cli_runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "AI Security Orchestrator Doctor Diagnostic" in result.output
    assert "Python Runtime" in result.output
    assert "Subprocess Executor" in result.output


def test_cli_config(cli_runner):
    """Test running 'security-ai config' settings command."""
    result = cli_runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "Active Configuration Settings" in result.output
    assert "OpenRouter LLM Backend" in result.output
    assert "nvidia/llama-3.1-nemotron-70b-instruct:free" in result.output


def test_cli_plugins(cli_runner):
    """Test running 'security-ai plugins' command."""
    result = cli_runner.invoke(app, ["plugins"])
    assert result.exit_code == 0
    assert "Registered Security Plugins" in result.output


def test_cli_scan_placeholder(cli_runner):
    """Test placeholder 'scan' command."""
    result = cli_runner.invoke(app, ["scan", "192.168.1.1"])
    assert result.exit_code == 0
    assert "Command 'scan' is a placeholder for Future Phases" in result.output
    assert "192.168.1.1" in result.output


def test_cli_orchestrate_placeholder(cli_runner):
    """Test placeholder 'orchestrate' command."""
    result = cli_runner.invoke(app, ["orchestrate", "playbook.yaml"])
    assert result.exit_code == 0
    assert "Command 'orchestrate' is a placeholder for Future Phases" in result.output


def test_cli_analyze_placeholder(cli_runner):
    """Test placeholder 'analyze' command."""
    result = cli_runner.invoke(app, ["analyze", "scan.json"])
    assert result.exit_code == 0
    assert "Command 'analyze' is a placeholder for Future Phases" in result.output
