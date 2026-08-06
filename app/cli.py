"""
CLI UI Implementation using Typer and Rich.

Commands implemented:
- security-ai doctor
- security-ai plugins
- security-ai config

Placeholder commands:
- security-ai scan
- security-ai orchestrate
- security-ai analyze
"""

import sys
import asyncio
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

from core.config import load_config, AppConfig
from core.logger import setup_logger, get_logger, get_console
from core.executor import SafeExecutor
from core.llm_openrouter import OpenRouterLLMProvider
from plugins.manager import PluginManager

app = typer.Typer(
    name="security-ai",
    help="🤖 AI Security Orchestrator CLI — DevSecOps Automation & Security Assessment Engine",
    add_completion=False,
    no_args_is_help=True
)

console = get_console()
logger = get_logger("cli")


def _init_context(ctx: typer.Context, config_path: Optional[str] = None, json_logs: bool = False, verbose: bool = False):
    """Initialize application context, logger, and settings."""
    log_level = "DEBUG" if verbose else "INFO"
    setup_logger(level=log_level, json_format=json_logs)
    
    cfg = load_config(config_path)
    ctx.obj = {"config": cfg, "verbose": verbose}


@app.callback()
def main(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to custom config.yaml file."),
    json_logs: bool = typer.Option(False, "--json-logs", help="Enable structured JSON log output."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug level verbose output.")
):
    """Global CLI options callback."""
    _init_context(ctx, config_path=config, json_logs=json_logs, verbose=verbose)


@app.command("doctor")
def doctor(ctx: typer.Context):
    """Run environment, configuration, executor, and OpenRouter API diagnostic checks."""
    console.print("\n[bold cyan]🔍 AI Security Orchestrator Doctor Diagnostic[/bold cyan]\n")

    cfg: AppConfig = ctx.obj["config"]
    table = Table(title="System & Component Diagnostics", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan", width=25)
    table.add_column("Status", width=12)
    table.add_column("Details", style="dim")

    # 1. Python Environment Check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 12):
        table.add_row("Python Runtime", "[bold green]PASS[/bold green]", f"Python {py_ver}")
    else:
        table.add_row("Python Runtime", "[bold yellow]WARN[/bold yellow]", f"Python {py_ver} (3.12+ recommended)")

    # 2. Config Loading Check
    table.add_row("Configuration Loader", "[bold green]PASS[/bold green]", f"Loaded default model: {cfg.openrouter.default_model}")

    # 3. Subprocess Executor Check
    try:
        executor = SafeExecutor(default_timeout_seconds=5.0)
        res = executor.execute(["python", "--version"] if sys.platform != "win32" else ["cmd", "/c", "ver"])
        if res.is_success:
            table.add_row("Subprocess Executor", "[bold green]PASS[/bold green]", "Safe execution engine operational")
        else:
            table.add_row("Subprocess Executor", "[bold red]FAIL[/bold red]", f"Execution failed: {res.stderr.strip()}")
    except Exception as e:
        table.add_row("Subprocess Executor", "[bold red]FAIL[/bold red]", str(e))

    # 4. OpenRouter API Health Check
    llm = OpenRouterLLMProvider(cfg.openrouter)
    api_ok = asyncio.run(llm.health_check())
    if api_ok:
        table.add_row("OpenRouter API", "[bold green]PASS[/bold green]", f"Connected to OpenRouter API (Model: {cfg.openrouter.default_model})")
    else:
        table.add_row("OpenRouter API", "[bold red]FAIL[/bold red]", "Unable to reach OpenRouter API or invalid API key")

    console.print(table)
    console.print("\n[dim]Diagnostic check completed.[/dim]\n")


@app.command("config")
def show_config(ctx: typer.Context):
    """Display active application configuration parameters (sanitized)."""
    cfg: AppConfig = ctx.obj["config"]

    console.print(Panel("[bold cyan]Active Configuration Settings[/bold cyan]", expand=False))
    
    tree = Tree("[bold magenta]AppConfig[/bold magenta]")
    
    # OpenRouter Node
    or_node = tree.add("[bold yellow]OpenRouter LLM Backend[/bold yellow]")
    or_node.add(f"[cyan]Base URL:[/cyan] {cfg.openrouter.base_url}")
    or_node.add(f"[cyan]Default Free Model:[/cyan] {cfg.openrouter.default_model}")
    or_node.add(f"[cyan]Fallback Model:[/cyan] {cfg.openrouter.fallback_model}")
    or_node.add(f"[cyan]Max Tokens:[/cyan] {cfg.openrouter.max_tokens}")
    or_node.add(f"[cyan]Temperature:[/cyan] {cfg.openrouter.temperature}")
    masked_key = "sk-or-v1-***" + cfg.openrouter.api_key.get_secret_value()[-6:] if cfg.openrouter.api_key else "Not Set"
    or_node.add(f"[cyan]API Key:[/cyan] {masked_key}")

    # Executor Node
    exec_node = tree.add("[bold yellow]Safe Subprocess Executor[/bold yellow]")
    exec_node.add(f"[cyan]Default Timeout:[/cyan] {cfg.executor.default_timeout_seconds}s")
    exec_node.add(f"[cyan]Max Timeout:[/cyan] {cfg.executor.max_timeout_seconds}s")
    exec_node.add(f"[cyan]Safelisted Env Vars:[/cyan] {', '.join(cfg.executor.safe_environment_vars)}")

    # Logging Node
    log_node = tree.add("[bold yellow]Logging System[/bold yellow]")
    log_node.add(f"[cyan]Level:[/cyan] {cfg.logging.level}")
    log_node.add(f"[cyan]JSON Output:[/cyan] {cfg.logging.json_format}")
    log_node.add(f"[cyan]Log File:[/cyan] {cfg.logging.log_file or 'None'}")

    console.print(tree)
    console.print()


@app.command("plugins")
def list_plugins(ctx: typer.Context):
    """List registered security plugins, binary installation state, and health status."""
    from core.registry import get_registry

    registry = get_registry()
    all_plugins = registry.list_plugins()

    console.print("\n[bold cyan]🧩 Registered Security Plugins & System Tool Status[/bold cyan]\n")

    if not all_plugins:
        console.print("[yellow]No dynamic plugins discovered in plugins directory.[/yellow]\n")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Plugin / Tool", style="cyan", width=18)
    table.add_column("Binary Status", width=16)
    table.add_column("Operational State", width=18)
    table.add_column("Description", style="dim")

    for name, plugin in sorted(all_plugins.items()):
        is_inst = plugin.is_installed()
        binary_status = "[bold green]INSTALLED[/bold green]" if is_inst else "[bold yellow]NOT INSTALLED[/bold yellow]"
        op_state = "[bold green]AVAILABLE[/bold green]" if is_inst else "[bold red]UNAVAILABLE[/bold red]"

        table.add_row(plugin.name, binary_status, op_state, plugin.description)

    console.print(table)
    console.print()


# Placeholder Commands for Future Phases
@app.command("scan")
def scan_placeholder(
    target: str = typer.Argument(..., help="Target host, network block, or repository URI.")
):
    """[Placeholder] Run automated security scanning workflows against authorized targets."""
    console.print(f"[bold yellow]🚧 Command 'scan' is a placeholder for Future Phases.[/bold yellow]")
    console.print(f"Target specified: [cyan]{target}[/cyan]")
    console.print("[dim]Phase 1 foundation build complete. Automated scanning module scheduled for next phase.[/dim]")


@app.command("orchestrate")
def orchestrate_placeholder(
    playbook: str = typer.Argument(..., help="Path to assessment playbook YAML definition.")
):
    """[Placeholder] Execute multi-step AI security orchestration playbooks."""
    console.print(f"[bold yellow]🚧 Command 'orchestrate' is a placeholder for Future Phases.[/bold yellow]")
    console.print(f"Playbook specified: [cyan]{playbook}[/cyan]")
    console.print("[dim]Phase 1 foundation build complete. Orchestration module scheduled for next phase.[/dim]")


@app.command("analyze")
def analyze_placeholder(
    file_path: str = typer.Argument(..., help="Path to security scan log or artifact for AI analysis.")
):
    """[Placeholder] Perform AI-assisted vulnerability and triage analysis."""
    console.print(f"[bold yellow]🚧 Command 'analyze' is a placeholder for Future Phases.[/bold yellow]")
    console.print(f"Artifact specified: [cyan]{file_path}[/cyan]")
    console.print("[dim]Phase 1 foundation build complete. AI analysis engine scheduled for next phase.[/dim]")


@app.command("plan")
def plan_assessment(
    ctx: typer.Context,
    target: str = typer.Argument(..., help="Target IP address, hostname, domain, or URL."),
    execute_now: bool = typer.Option(False, "--execute", "-e", help="Prompt for authorization and execute planned workflow immediately.")
):
    """Generate an AI-driven security assessment plan for a target using OpenRouter."""
    from core.planner import AIPlanner
    from core.workflow import WorkflowEngine

    console.print(f"\n[bold cyan]🧠 Formulating AI Security Assessment Plan for:[/bold cyan] [yellow]{target}[/yellow]\n")

    cfg: AppConfig = ctx.obj["config"]
    planner = AIPlanner()
    engine = WorkflowEngine()

    if not engine.validate_target(target):
        console.print(f"[bold red]ERROR:[/bold red] Target string '{target}' is invalid format.")
        raise typer.Exit(code=1)

    with console.status("[bold green]Querying OpenRouter LLM and building plan...[/bold green]"):
        plan = planner.generate_plan(target)

    # Display Scope Summary & Target
    console.print(Panel(f"[cyan]Target:[/cyan] {plan.target}\n[cyan]Scope Assessment:[/cyan] {plan.scope_summary}", title="🎯 Target Scope", expand=False))

    # Display Selected Plugins
    plugins_str = ", ".join(f"[bold green]{p}[/bold green]" for p in plan.selected_plugins)
    console.print(f"\n[bold magenta]Selected Tool Plugins:[/bold magenta] {plugins_str}")
    console.print(f"[bold magenta]Estimated Execution Time:[/bold magenta] [yellow]~{plan.estimated_duration_seconds:.1f} seconds[/yellow]\n")

    # Display Execution Steps Table
    table = Table(title="📋 Planned Execution Order", show_header=True, header_style="bold magenta")
    table.add_column("Step", style="cyan", width=6)
    table.add_column("Tool", style="green", width=15)
    table.add_column("Objective & Purpose")

    for step in plan.execution_order:
        table.add_row(str(step.step_number), step.tool, step.purpose)

    console.print(table)

    # Display Strategic AI Reasoning
    console.print(Panel(plan.reasoning, title="💡 Strategic AI Reasoning", expand=False))
    console.print()

    if execute_now:
        confirm = typer.confirm("⚠️ Do you have explicit written authorization to scan this target system?")
        if not confirm:
            console.print("[bold red]Scan cancelled: Target authorization rejected.[/bold red]\n")
            raise typer.Exit(code=1)

        with console.status("[bold green]Executing security workflow steps...[/bold green]"):
            result = engine.execute_plan(plan, authorized=True)

        # Save Scan Record to SQLite Persistence
        from memory.database import get_db_engine
        db = get_db_engine(cfg.database.db_url)
        db.save_scan(
            target=result.target,
            plugins_used=plan.selected_plugins,
            execution_time_ms=result.total_duration_ms,
            status="COMPLETED",
            raw_results=result.model_dump(),
            summary=result.summary
        )

        console.print(Panel(
            f"[green]Workflow Execution Completed Successfully![/green]\n"
            f"Target: {result.target}\n"
            f"Steps Executed: {result.summary['steps_executed']}\n"
            f"Total Wall-Clock Time: {result.total_duration_ms:.2f} ms\n"
            f"Total Findings Discovered: {result.summary['total_findings']}\n"
            f"[dim]Scan record persisted to SQLite database.[/dim]",
            title="✅ Scan Complete",
            expand=False
        ))
        console.print()


@app.command("history")
def show_history(
    ctx: typer.Context,
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of historical scan records to display.")
):
    """View historical scan records, targets, execution durations, and generated reports."""
    from memory.database import get_db_engine

    cfg: AppConfig = ctx.obj["config"]
    db = get_db_engine(cfg.database.db_url)

    scans = db.get_recent_scans(limit=limit)

    console.print("\n[bold cyan]📜 Security Assessment History[/bold cyan]\n")

    if not scans:
        console.print("[yellow]No historical scan records found in database.[/yellow]")
        console.print(f"[dim]Database URL: {cfg.database.db_url}[/dim]\n")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Date / Timestamp", style="cyan", width=22)
    table.add_column("Target", style="yellow", width=20)
    table.add_column("Status", width=12)
    table.add_column("Plugins Used", style="green")
    table.add_column("Duration", width=12)

    for scan in scans:
        status_style = "[bold green]COMPLETED[/bold green]" if scan.status == "COMPLETED" else f"[bold red]{scan.status}[/bold red]"
        date_str = scan.date.strftime("%Y-%m-%d %H:%M:%S") if scan.date else "N/A"
        plugins_str = ", ".join(scan.plugins_used) if scan.plugins_used else "None"
        dur_str = f"{scan.execution_time_ms / 1000.0:.1f}s"

        table.add_row(
            str(scan.id),
            date_str,
            scan.target,
            status_style,
            plugins_str,
            dur_str
        )

    console.print(table)
    console.print()


@app.command("report")
def generate_reports(
    ctx: typer.Context,
    file_path: str = typer.Argument(..., help="Path to normalized scan result JSON file."),
    md: bool = typer.Option(True, "--md", help="Generate Markdown report (.md)."),
    html: bool = typer.Option(False, "--html", help="Generate HTML report (.html)."),
    pdf: bool = typer.Option(False, "--pdf", help="Generate PDF report (.pdf)."),
    out_dir: str = typer.Option("reports_output", "--out-dir", "-o", help="Output directory path for generated reports.")
):
    """Analyze normalized scan JSON results and generate multi-format security reports."""
    import json
    from pathlib import Path
    from core.analyzer import AIResultsAnalyzer
    from reports.markdown import MarkdownReportGenerator
    from reports.html import HTMLReportGenerator
    from reports.pdf import PDFReportGenerator

    p = Path(file_path)
    if not p.is_file():
        console.print(f"[bold red]ERROR:[/bold red] Scan result JSON file '{file_path}' does not exist.")
        raise typer.Exit(code=1)

    try:
        with open(p, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        console.print(f"[bold red]ERROR:[/bold red] Failed to parse JSON file '{file_path}': {str(e)}")
        raise typer.Exit(code=1)

    analyzer = AIResultsAnalyzer()
    with console.status("[bold green]Analyzing scan findings and distinguishing facts vs AI inferences...[/bold green]"):
        analysis = analyzer.analyze_json(raw_data)

    console.print(f"\n[bold cyan]📊 AI Analysis Complete for Target:[/bold cyan] [yellow]{analysis.target}[/yellow]")
    console.print(f"[cyan]Confidence Score:[/cyan] [bold green]{analysis.confidence * 100:.1f}%[/bold green]\n")

    output_directory = Path(out_dir)
    output_directory.mkdir(parents=True, exist_ok=True)
    target_clean = analysis.target.replace("://", "_").replace("/", "_").replace(":", "_")

    generated_files = []

    if md:
        md_path = output_directory / f"report_{target_clean}.md"
        md_gen = MarkdownReportGenerator()
        md_gen.generate(analysis, scan_data=raw_data, output_path=md_path)
        generated_files.append(f"Markdown: {md_path}")

    if html:
        html_path = output_directory / f"report_{target_clean}.html"
        html_gen = HTMLReportGenerator()
        html_gen.generate(analysis, scan_data=raw_data, output_path=html_path)
        generated_files.append(f"HTML: {html_path}")

    if pdf:
        pdf_path = output_directory / f"report_{target_clean}.pdf"
        pdf_gen = PDFReportGenerator()
        pdf_gen.generate(analysis, scan_data=raw_data, output_path=pdf_path)
        generated_files.append(f"PDF: {pdf_path}")

    console.print(Panel(
        "\n".join(f"• {f}" for f in generated_files),
        title="📄 Security Reports Generated",
        expand=False
    ))
    console.print()


if __name__ == "__main__":
    app()
