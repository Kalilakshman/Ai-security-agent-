"""
Unit tests for Rich Terminal Dashboard and UI Components (app/ui.py).
"""

import pytest
from rich.panel import Panel
from rich.layout import Layout

from core.config import AppConfig
from app.ui import (
    render_header_banner,
    render_system_status,
    render_mcp_status,
    render_tool_matrix,
    render_assessment_timeline,
    render_metrics_and_risk,
    create_ops_dashboard_layout,
)
from app.cli import app


def test_render_header_banner():
    """Test header banner rendering."""
    banner = render_header_banner()
    assert isinstance(banner, Panel)


def test_render_system_status():
    """Test system status panel rendering with custom settings."""
    cfg = AppConfig()
    panel = render_system_status(config=cfg, target="192.168.1.1", profile="deep", authorized=True)
    assert isinstance(panel, Panel)


def test_render_mcp_status():
    """Test MCP status panel rendering."""
    panel = render_mcp_status()
    assert isinstance(panel, Panel)


def test_render_tool_matrix():
    """Test tool matrix rendering with active tool overrides."""
    active = {"nmap": "RUNNING", "gobuster": "TIMED_OUT"}
    panel = render_tool_matrix(active_tools=active)
    assert isinstance(panel, Panel)


def test_render_assessment_timeline():
    """Test assessment timeline rendering."""
    panel = render_assessment_timeline(completed_steps=[1], current_step=2)
    assert isinstance(panel, Panel)


def test_render_metrics_and_risk():
    """Test metrics & risk summary panel rendering."""
    panel = render_metrics_and_risk(
        evidence_count=50,
        findings_count=12,
        coverage_pct=85.0,
        elapsed_seconds=120.5
    )
    assert isinstance(panel, Panel)


def test_create_ops_dashboard_layout():
    """Test creating full operations dashboard layout."""
    layout = create_ops_dashboard_layout(
        target="example.com",
        profile="fast"
    )
    assert isinstance(layout, Layout)
    assert "header" in layout
    assert "body" in layout
    assert "footer" in layout


def test_cli_dashboard_command(cli_runner):
    """Test 'security-ai dashboard' CLI command."""
    res = cli_runner.invoke(app, ["dashboard", "--target", "127.0.0.1", "--profile", "deep"])
    assert res.exit_code == 0
    assert "AI SECURITY ORCHESTRATOR" in res.output
    assert "AUTHORIZED ASSESSMENT PLATFORM" in res.output
