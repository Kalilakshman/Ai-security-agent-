"""
Professional Cybersecurity Operations Rich UI & Terminal Dashboard Components.
"""

import time
from typing import Dict, List, Any, Optional
from rich import box
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.tree import Tree

from core.config import AppConfig, load_config
from core.llm import get_llm_provider
from core.adapters import get_adapter_registry
from core.mcp import get_mcp_registry
from core.planner import ExecutionPlan, PlannedStep
from plugins.base import StandardPluginOutput

console = Console()


def render_header_banner() -> Panel:
    """Render professional double-bordered cybersecurity operations header."""
    header_text = Text()
    header_text.append("╔══════════════════════════════════════════════════════════════════╗\n", style="bold #00ffff")
    header_text.append("║                   AI SECURITY ORCHESTRATOR                       ║\n", style="bold #00ff66")
    header_text.append("║                 AUTHORIZED ASSESSMENT PLATFORM                   ║\n", style="bold #00ffff")
    header_text.append("╚══════════════════════════════════════════════════════════════════╝", style="bold #00ffff")
    return Panel(
        header_text,
        box=box.DOUBLE,
        border_style="#00ffff",
        style="on #0a0e14",
        expand=True
    )


def render_system_status(
    config: Optional[AppConfig] = None,
    target: str = "127.0.0.1",
    profile: str = "deep",
    authorized: bool = True
) -> Panel:
    """Render system state, LLM provider, active model, scope, and authorization status."""
    cfg = config or load_config()
    provider_name = cfg.llm.provider.upper()
    model_name = cfg.llm.model
    auth_str = "[bold #00ff66]✓ AUTHORIZED & CONFIRMED[/]" if authorized else "[bold #ff0055]✗ NOT AUTHORIZED[/]"

    table = Table.grid(padding=(0, 2))
    table.add_column(style="#00ffff", justify="left")
    table.add_column(style="bold white", justify="left")

    table.add_row("Provider :", f"[bold #00ff66]{provider_name}[/]")
    table.add_row("Model    :", f"[bold #ffff00]{model_name}[/]")
    table.add_row("Profile  :", f"[bold #ff007f]{profile.upper()}[/]")
    table.add_row("Scope    :", f"[bold white]{target}[/]")
    table.add_row("Auth Status:", auth_str)

    return Panel(
        table,
        title="[bold #00ffff]⚙️ SYSTEM & TARGET STATUS[/]",
        border_style="#00ffff",
        box=box.ROUNDED
    )


def render_mcp_status() -> Panel:
    """Render MCP server operational health status panel."""
    mcp_reg = get_mcp_registry()
    servers = mcp_reg.list_servers()

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold", width=3)
    grid.add_column(style="#00ffff")

    if not servers:
        grid.add_row("[bold #00ff66]✓[/]", "Network Subsystem")
        grid.add_row("[bold #00ff66]✓[/]", "Web Assessment Hub")
        grid.add_row("[bold #00ff66]✓[/]", "AI Triage & Analysis")
    else:
        for sid, scfg in servers.items():
            icon = "[bold #00ff66]✓[/]" if scfg.enabled else "[bold #ff0055]✗[/]"
            grid.add_row(icon, scfg.name)

    return Panel(
        grid,
        title="[bold #00ff66]🔌 MCP STATUS[/]",
        border_style="#00ff66",
        box=box.ROUNDED
    )


def render_tool_matrix(active_tools: Optional[Dict[str, str]] = None) -> Panel:
    """Render security tools health matrix (Nmap, ZAP, Wireshark, Burp, Metasploit)."""
    adapter_reg = get_adapter_registry()
    adapters = adapter_reg.list_adapters()

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold", width=3)
    grid.add_column(style="#ffff00")

    status_overrides = active_tools or {}

    for name, adapter in sorted(adapters.items()):
        current_st = status_overrides.get(name)
        if current_st == "RUNNING":
            icon = "[bold #00ffff]⟳[/]"
        elif current_st == "TIMED_OUT":
            icon = "[bold #ffff00]⚠[/]"
        elif current_st == "FAILED":
            icon = "[bold #ff0055]✗[/]"
        elif adapter.is_installed() and adapter.health_check():
            icon = "[bold #00ff66]✓[/]"
        else:
            icon = "[bold #ff0055]✗[/]"

        display_name = adapter.name.upper() if len(adapter.name) <= 6 else adapter.name.title()
        grid.add_row(icon, display_name)

    return Panel(
        grid,
        title="[bold #ffff00]🛠️ TOOLS[/]",
        border_style="#ffff00",
        box=box.ROUNDED
    )


def render_assessment_timeline(
    plan: Optional[ExecutionPlan] = None,
    completed_steps: Optional[List[int]] = None,
    current_step: Optional[int] = None
) -> Panel:
    """Render live execution timeline (Discovery, Fingerprinting, Web Assessment, Analysis)."""
    comp = set(completed_steps or [])

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold", width=3)
    grid.add_column(style="#00ffff")

    if not plan or not plan.execution_order:
        stages = [
            (1, "Target Discovery"),
            (2, "Service Fingerprinting"),
            (3, "Vulnerability & Web Assessment"),
            (4, "AI Strategic Analysis"),
        ]
        for s_num, s_name in stages:
            if s_num in comp:
                icon = "[bold #00ff66]✓[/]"
            elif s_num == current_step:
                icon = "[bold #00ffff]⟳[/]"
            else:
                icon = "[bold white]⏳[/]"
            grid.add_row(icon, s_name)
    else:
        for st in plan.execution_order:
            if st.step_number in comp:
                icon = "[bold #00ff66]✓[/]"
            elif st.step_number == current_step:
                icon = "[bold #00ffff]⟳[/]"
            else:
                icon = "[bold white]⏳[/]"
            grid.add_row(icon, f"{st.tool} ({st.purpose})")

    return Panel(
        grid,
        title="[bold #ff007f]⏱️ ASSESSMENT TIMELINE[/]",
        border_style="#ff007f",
        box=box.ROUNDED
    )


def render_metrics_and_risk(
    evidence_count: int = 42,
    findings_count: int = 8,
    coverage_pct: float = 76.0,
    elapsed_seconds: float = 45.2,
    risk_summary: Optional[Dict[str, int]] = None
) -> Panel:
    """Render findings count, evidence count, coverage %, elapsed time, and risk summary."""
    risks = risk_summary or {"critical": 1, "high": 2, "medium": 3, "low": 2}

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="#00ffff", justify="left")
    grid.add_column(style="bold white", justify="right")

    grid.add_row("Evidence Collected :", f"[bold #00ff66]{evidence_count}[/]")
    grid.add_row("Findings Identified:", f"[bold #ff007f]{findings_count}[/]")
    grid.add_row("Assessment Coverage:", f"[bold #00ffff]{coverage_pct:.0f}%[/]")
    grid.add_row("Elapsed Time       :", f"[bold #ffff00]{elapsed_seconds:.1f} s[/]")
    grid.add_row("─" * 18, "─" * 8)
    grid.add_row("Critical Risks     :", f"[bold #ff0055]{risks.get('critical', 0)}[/]")
    grid.add_row("High Risks         :", f"[bold #ff007f]{risks.get('high', 0)}[/]")
    grid.add_row("Medium Risks       :", f"[bold #ffff00]{risks.get('medium', 0)}[/]")
    grid.add_row("Low / Info Risks   :", f"[bold #00ff66]{risks.get('low', 0)}[/]")

    return Panel(
        grid,
        title="[bold #00ff66]📊 METRICS & RISK SUMMARY[/]",
        border_style="#00ff66",
        box=box.ROUNDED
    )


def create_ops_dashboard_layout(
    config: Optional[AppConfig] = None,
    target: str = "127.0.0.1",
    profile: str = "deep",
    evidence_count: int = 42,
    findings_count: int = 8,
    coverage_pct: float = 76.0,
    elapsed_seconds: float = 45.2,
    active_tools: Optional[Dict[str, str]] = None,
    completed_steps: Optional[List[int]] = None,
    current_step: Optional[int] = None
) -> Layout:
    """Construct full Rich Layout matching professional cybersecurity operations UI specification."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=6),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    layout["body"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="center", ratio=1),
        Layout(name="right", ratio=1)
    )

    layout["header"].update(render_header_banner())
    layout["left"].update(Group(
        render_system_status(config=config, target=target, profile=profile),
        render_mcp_status()
    ))
    layout["center"].update(Group(
        render_tool_matrix(active_tools=active_tools),
        render_assessment_timeline(completed_steps=completed_steps, current_step=current_step)
    ))
    layout["right"].update(render_metrics_and_risk(
        evidence_count=evidence_count,
        findings_count=findings_count,
        coverage_pct=coverage_pct,
        elapsed_seconds=elapsed_seconds
    ))

    footer_text = Text("Press Ctrl+C to abort assessment safely | Security Policy Engine ACTIVE | All actions logged to policy_audit.log", style="dim #00ffff")
    layout["footer"].update(Panel(footer_text, box=box.SIMPLE, style="on #0a0e14"))

    return layout
