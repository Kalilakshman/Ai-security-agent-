"""
CLI UI Implementation using Typer and Rich with Hacker Cyberpunk Framework Aesthetics.
"""

import sys
import asyncio
import typer
from typing import Optional
from rich import box
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

from core.config import load_config, AppConfig
from core.logger import setup_logger, get_logger, get_console
from core.executor import SafeExecutor
from core.llm_openrouter import OpenRouterLLMProvider

CYBER_BANNER = """[bold green]
███████╗███████╗██╗   ██╗██████╗  ██████╗██╗   ██╗██████╗  ██████╗ ██████╗  ██████╗ 
██╔════╝██╔════╝██║   ██║██╔══██╗██╔════╝╚██╗ ██╔╝██╔══██╗██╔═══██╗██╔══██╗██╔════╝ 
███████╗█████╗  ██║   ██║██████╔╝██║      ╚████╔╝ ██████╔╝██║   ██║██████╔╝██║  ███╗
╚════██║██╔══╝  ██║   ██║██╔══██╗██║       ╚██╔╝  ██╔══██╗██║   ██║██╔══██╗██║   ██║
███████║███████╗╚██████╔╝██║  ██║╚██████╗   ██║   ██║  ██║╚██████╔╝██║  ██║╚██████╔╝
╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ 
[/bold green][bold cyan]               ⚡ AI SECURITY ORCHESTRATION FRAMEWORK v0.1.0 ⚡[/bold cyan]
[dim]========================================================================================[/dim]"""

app = typer.Typer(
    name="security-ai",
    help="🤖 AI Security Orchestrator CLI — Cyberpunk Security Automation Engine",
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
    ctx.obj = {"config": cfg, "verbose": verbose, "json_logs": json_logs}


@app.callback()
def main(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to custom config.yaml file."),
    json_logs: bool = typer.Option(False, "--json-logs", help="Enable structured JSON log output."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug level verbose output.")
):
    """Global CLI options callback."""
    _init_context(ctx, config_path=config, json_logs=json_logs, verbose=verbose)
    if not json_logs:
        console.print(CYBER_BANNER)


@app.command("doctor")
def doctor(ctx: typer.Context):
    """Run environment, configuration, executor, and OpenRouter API diagnostic checks."""
    console.print("[bold #00ffff]┌──[ SYSTEM DIAGNOSTICS & CORE SUBSYSTEM AUDIT ]──┐[/]\n")

    cfg: AppConfig = ctx.obj["config"]
    table = Table(
        title="[bold #00ff66]CYBER SUBSYSTEM STATUS[/]",
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Subsystem Component", style="#00ffff", width=25)
    table.add_column("State", width=12)
    table.add_column("Diagnostic Output", style="dim")

    # 1. Python Environment Check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 12):
        table.add_row("Python Core Runtime", "[bold #00ff66][ONLINE][/]", f"Python {py_ver}")
    else:
        table.add_row("Python Core Runtime", "[bold #ffff00][DEGRADED][/]", f"Python {py_ver} (3.12+ recommended)")

    # 2. Config Loading Check
    table.add_row("YAML Config Engine", "[bold #00ff66][ONLINE][/]", f"Loaded default model: {cfg.openrouter.default_model}")

    # 3. Subprocess Executor Check
    try:
        executor = SafeExecutor(default_timeout_seconds=5.0)
        res = executor.execute(["python", "--version"] if sys.platform != "win32" else ["cmd", "/c", "ver"])
        if res.is_success:
            table.add_row("Subprocess Sandbox", "[bold #00ff66][ONLINE][/]", "Safe execution engine operational")
        else:
            table.add_row("Subprocess Sandbox", "[bold #ff0055][OFFLINE][/]", f"Execution failed: {res.stderr.strip()}")
    except Exception as e:
        table.add_row("Subprocess Sandbox", "[bold #ff0055][OFFLINE][/]", str(e))

    # 4. LLM Subsystem Health Check
    from core.llm import get_llm_provider
    prov = get_llm_provider(config=cfg)
    p_name = prov.provider_name().upper()
    api_ok = prov.health_check()
    if api_ok:
        table.add_row(f"LLM Hub ({p_name})", "[bold #00ff66][ONLINE][/]", f"Connected to {prov.provider_name()} API (Model: {cfg.llm.model})")
    else:
        table.add_row(f"LLM Hub ({p_name})", "[bold #ff0055][OFFLINE][/]", f"Unable to reach {prov.provider_name()} API or invalid credentials")

    console.print(table)
    console.print("\n[dim #00ffff]Diagnostic check sequence completed.[/]\n")


@app.command("config")
def show_config(ctx: typer.Context):
    """Display active application configuration parameters (sanitized)."""
    cfg: AppConfig = ctx.obj["config"]

    console.print(Panel(
        "[bold #00ffff]⚙️ ACTIVE FRAMEWORK CONFIGURATION & BOUNDARIES[/]",
        border_style="#00ff66",
        box=box.DOUBLE,
        expand=False
    ))
    
    tree = Tree("[bold #ff007f]AppConfig Core Root[/]")
    
    # LLM Subsystem Node
    llm_node = tree.add("[bold #ffff00]Provider-Independent LLM Neural Hub[/]")
    llm_node.add(f"[#00ffff]Provider:[/] {cfg.llm.provider.upper()}")
    llm_node.add(f"[#00ffff]Active Model:[/] {cfg.llm.model}")
    llm_node.add(f"[#00ffff]API Endpoint:[/] {cfg.llm.api_endpoint}")
    llm_node.add(f"[#00ffff]Max Tokens:[/] {cfg.llm.max_tokens}")
    llm_node.add(f"[#00ffff]Temperature:[/] {cfg.llm.temperature}")
    raw_key = cfg.llm.get_resolved_api_key()
    masked_key = "sk-***" + raw_key[-6:] if raw_key and len(raw_key) > 6 else ("Set" if raw_key else "Not Set / Local")
    llm_node.add(f"[#00ffff]API Key:[/] [dim]{masked_key}[/]")

    # Executor Node
    exec_node = tree.add("[bold #ffff00]Safe Subprocess Sandbox[/]")
    exec_node.add(f"[#00ffff]Default Timeout:[/] {cfg.executor.default_timeout_seconds}s")
    exec_node.add(f"[#00ffff]Max Timeout:[/] {cfg.executor.max_timeout_seconds}s")
    exec_node.add(f"[#00ffff]Safelisted Env Vars:[/] {', '.join(cfg.executor.safe_environment_vars)}")

    # Timeouts Node
    timeout_node = tree.add("[bold #ffff00]Assessment Profile Timeouts[/]")
    for tool in ["nmap", "whatweb", "nikto", "gobuster", "nuclei"]:
        t_fast = cfg.timeouts.get_timeout(tool, "fast")
        t_std = cfg.timeouts.get_timeout(tool, "standard")
        t_deep = cfg.timeouts.get_timeout(tool, "deep")
        timeout_node.add(f"[#00ffff]{tool}:[/] Fast={t_fast:.0f}s | Standard={t_std:.0f}s | Deep={t_deep:.0f}s")

    # Logging Node
    log_node = tree.add("[bold #ffff00]Telemetry & Logging[/]")
    log_node.add(f"[#00ffff]Level:[/] {cfg.logging.level}")
    log_node.add(f"[#00ffff]JSON Output:[/] {cfg.logging.json_format}")
    log_node.add(f"[#00ffff]Log File:[/] {cfg.logging.log_file or 'None'}")

    console.print(tree)
    console.print()


@app.command("plugins")
def list_plugins(ctx: typer.Context):
    """List registered security plugins, binary installation state, and health status."""
    from core.registry import get_registry

    registry = get_registry()
    all_plugins = registry.list_plugins()

    console.print("[bold #00ffff]┌──[ DYNAMIC SECURITY TOOL MATRIX ]──┐[/]\n")

    if not all_plugins:
        console.print("[#ffff00]No dynamic plugins discovered in plugins directory.[/]\n")
        return

    table = Table(
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Plugin / Tool", style="#00ffff", width=18)
    table.add_column("Binary Status", width=16)
    table.add_column("Operational State", width=18)
    table.add_column("Description", style="dim")

    for name, plugin in sorted(all_plugins.items()):
        is_inst = plugin.is_installed()
        binary_status = "[bold #00ff66][INSTALLED][/]" if is_inst else "[bold #ffff00][MISSING][/]"
        op_state = "[bold #00ff66][READY][/]" if is_inst else "[bold #ff0055][DISABLED][/]"

        table.add_row(plugin.name, binary_status, op_state, plugin.description)

    console.print(table)
    console.print()


@app.command("scan")
def scan_command(
    ctx: typer.Context,
    target: str = typer.Argument(..., help="Target IP address, hostname, domain, or URL."),
    profile: str = typer.Option("standard", "--profile", "-p", help="Assessment profile: fast, standard, deep, or custom."),
    concurrency: int = typer.Option(3, "--concurrency", "-c", help="Maximum worker threads for parallel DAG execution."),
    retries: int = typer.Option(0, "--retries", "-r", help="Maximum retry attempts for transient step failures."),
    resume: Optional[str] = typer.Option(None, "--resume", help="Optional assessment ID or 'latest' to resume from checkpoint."),
    auto_approve: bool = typer.Option(False, "--yes", "-y", help="Automatically confirm target authorization.")
):
    """Run automated resilient security scanning workflow against an authorized target."""
    from core.planner import AIPlanner
    from core.workflow import WorkflowEngine
    from memory.database import get_db_engine
    import json

    console.print(f"\n[bold #00ffff]┌──[ 🚀 INITIATING AUTOMATED CYBER SCANNER ]──┐[/]")
    console.print(f"[bold #00ffff]Target:[/] [bold #ffff00]{target}[/] | [bold #00ffff]Profile:[/] [bold #ff007f]{profile.upper()}[/] | [bold #00ffff]Concurrency:[/] {concurrency}\n")

    cfg: AppConfig = ctx.obj["config"]
    planner = AIPlanner()
    engine = WorkflowEngine(config=cfg)

    if not engine.validate_target(target):
        console.print(f"[bold #ff0055]CRITICAL ERROR:[/] Target string '{target}' is invalid format.")
        raise typer.Exit(code=1)

    if not auto_approve:
        confirm = typer.confirm("⚠️ AUTHORIZATION CHECK: Do you have explicit written permission to scan this target?")
        if not confirm:
            console.print("[bold #ff0055]SCAN ABORTED: Target authorization rejected.[/]\n")
            raise typer.Exit(code=1)

    resume_id = None
    if resume:
        resume_id = None if resume.lower() == "latest" else resume

    with console.status(f"[bold #00ff66]⚡ Formulating AI Execution Plan (Profile: {profile.upper()})...[/]"):
        plan = planner.generate_plan(target)

    # Display steps table with resolved timeout per plugin
    table = Table(
        title=f"[bold #00ff66]EXECUTION SEQUENCE MATRIX ({profile.upper()} PROFILE)[/]",
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Step", style="#00ffff", width=6)
    table.add_column("Tool", style="#00ff66", width=15)
    table.add_column("Timeout", style="#ffff00", width=12)
    table.add_column("Objective & Purpose")

    for step in plan.execution_order:
        timeout_val = cfg.timeouts.get_timeout(step.tool, profile=profile)
        table.add_row(str(step.step_number), step.tool, f"{timeout_val:.0f}s", step.purpose)

    console.print(table)
    console.print()

    # Execute resilient workflow plan
    scan_result = engine.execute_plan(
        plan=plan,
        authorized=True,
        profile=profile,
        max_concurrency=concurrency,
        max_retries=retries,
        resume_checkpoint_id=resume_id
    )

    db = get_db_engine(cfg.database.db_url)
    raw_results = scan_result.model_dump()

    db.save_scan(
        assessment_id=scan_result.assessment_id,
        target=target,
        target_scope=target,
        profile=profile,
        llm_provider=cfg.llm.provider,
        llm_model=cfg.llm.model,
        mcp_servers=[s for s in getattr(cfg, "mcp_servers", [])],
        plugins_used=plan.selected_plugins,
        tool_executions=[r.model_dump() for r in scan_result.step_results],
        execution_time_ms=scan_result.total_duration_ms,
        retries_count=retries,
        evidence_count=sum(len(r.evidence) for r in scan_result.step_results),
        findings_count=scan_result.summary.get("total_findings", 0),
        status="COMPLETED",
        raw_results=raw_results,
        summary=scan_result.summary
    )

    clean_target = target.replace("://", "_").replace("/", "_").replace(":", "_")
    json_filename = f"scan_{clean_target}.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(raw_results, f, indent=2)

    console.print(Panel(
        f"[bold #00ff66]RESILIENT WORKFLOW EXECUTION COMPLETE[/]\n"
        f"Target: [bold #ffff00]{target}[/]\n"
        f"Profile: [bold #ff007f]{profile.upper()}[/]\n"
        f"Assessment Checkpoint: [cyan]{scan_result.assessment_id}[/]\n"
        f"Steps Executed: {scan_result.summary.get('steps_executed', 0)}\n"
        f"Total Duration: {scan_result.total_duration_ms / 1000.0:.2f} s\n"
        f"Findings Discovered: [bold #00ff66]{scan_result.summary.get('total_findings', 0)}[/]\n"
        f"[dim]Record persisted to SQLite DB & saved to '{json_filename}'.[/dim]",
        title="[bold #00ffff]✅ EXECUTION SUMMARY[/]",
        border_style="#00ff66",
        box=box.DOUBLE,
        expand=False
    ))
    console.print()


@app.command("orchestrate")
def orchestrate_placeholder(
    playbook: str = typer.Argument(..., help="Path to assessment playbook YAML definition.")
):
    """[Placeholder] Execute multi-step AI security orchestration playbooks."""
    console.print(f"[bold #ffff00]🚧 Command 'orchestrate' is a placeholder for Future Phases.[/]")
    console.print(f"Playbook specified: [cyan]{playbook}[/]")


@app.command("analyze")
def analyze_placeholder(
    file_path: str = typer.Argument(..., help="Path to security scan log or artifact for AI analysis.")
):
    """[Placeholder] Perform AI-assisted vulnerability and triage analysis."""
    console.print(f"[bold #ffff00]🚧 Command 'analyze' is a placeholder for Future Phases.[/]")
    console.print(f"Artifact specified: [cyan]{file_path}[/]")


@app.command("plan")
def plan_assessment(
    ctx: typer.Context,
    target: str = typer.Argument(..., help="Target IP address, hostname, domain, or URL."),
    profile: str = typer.Option("standard", "--profile", "-p", help="Assessment profile: fast, standard, or deep."),
    execute_now: bool = typer.Option(False, "--execute", "-e", help="Prompt for authorization and execute planned workflow immediately.")
):
    """Generate an AI-driven security assessment plan for a target using OpenRouter."""
    from core.planner import AIPlanner
    from core.workflow import WorkflowEngine

    console.print(f"\n[bold #00ffff]┌──[ 🧠 FORMULATING AI STRATEGIC PLAN ]──┐[/]")
    console.print(f"[bold #00ffff]Target:[/] [bold #ffff00]{target}[/] | [bold #00ffff]Profile:[/] [bold #ff007f]{profile.upper()}[/]\n")

    cfg: AppConfig = ctx.obj["config"]
    planner = AIPlanner()
    engine = WorkflowEngine()

    if not engine.validate_target(target):
        console.print(f"[bold #ff0055]CRITICAL ERROR:[/] Target string '{target}' is invalid format.")
        raise typer.Exit(code=1)

    with console.status(f"[bold #00ff66]⚡ Querying OpenRouter Neural AI Engine...[/]"):
        plan = planner.generate_plan(target)

    # Display Scope Summary & Target
    console.print(Panel(
        f"[#00ffff]Target:[/] {plan.target}\n[#00ffff]Scope Assessment:[/] {plan.scope_summary}",
        title="[bold #00ffff]🎯 TARGET SCOPE & FOOTPRINT[/]",
        border_style="#00ffff",
        box=box.ROUNDED,
        expand=False
    ))

    # Display Selected Plugins
    plugins_str = ", ".join(f"[bold #00ff66]{p}[/]" for p in plan.selected_plugins)
    console.print(f"\n[bold #ff007f]Selected Tool Modules:[/] {plugins_str}")
    console.print(f"[bold #ff007f]Assessment Profile:[/] [yellow]{profile.upper()}[/]")

    # Display Execution Steps Table with Timeout
    table = Table(
        title=f"[bold #00ff66]PLANNED EXECUTION MATRIX ({profile.upper()} PROFILE)[/]",
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Step", style="#00ffff", width=6)
    table.add_column("Tool", style="#00ff66", width=15)
    table.add_column("Timeout", style="#ffff00", width=12)
    table.add_column("Objective & Purpose")

    for step in plan.execution_order:
        timeout_val = cfg.timeouts.get_timeout(step.tool, profile=profile)
        table.add_row(str(step.step_number), step.tool, f"{timeout_val:.0f}s", step.purpose)

    console.print(table)

    # Display Strategic AI Reasoning
    console.print(Panel(
        plan.reasoning,
        title="[bold #ffff00]💡 STRATEGIC NEURAL REASONING[/]",
        border_style="#ffff00",
        box=box.ROUNDED,
        expand=False
    ))
    console.print()

    if execute_now:
        confirm = typer.confirm("⚠️ AUTHORIZATION CHECK: Do you have explicit written permission to scan this target?")
        if not confirm:
            console.print("[bold #ff0055]SCAN ABORTED: Target authorization rejected.[/]\n")
            raise typer.Exit(code=1)

        step_outputs = []
        total_time_ms = 0.0

        for step in plan.execution_order:
            tool_name = step.tool
            timeout_val = cfg.timeouts.get_timeout(tool_name, profile=profile)
            plugin = engine.registry.get_plugin(tool_name)

            if not plugin:
                continue

            step_options = dict(step.options or {})
            step_options["timeout"] = timeout_val
            step_options["profile"] = profile

            with console.status(f"[bold #00ff66]⚡ RUNNING TOOL STEP {step.step_number}/{len(plan.execution_order)}: {tool_name} (Timeout: {timeout_val:.0f}s | Profile: {profile.upper()})...[/]"):
                output = plugin.execute(target, step_options)
                step_outputs.append(output)
                duration = output.metadata.get("execution_time_ms", 0.0)
                total_time_ms += duration

                if output.status == "TIMED_OUT":
                    console.print(f"  [bold #ffff00]⏱️ {tool_name} TIMED OUT after {timeout_val:.0f}s (Partial findings preserved).[/]")
                elif output.status == "COMPLETED":
                    console.print(f"  [bold #00ff66]✓ {tool_name} COMPLETED in {duration/1000.0:.2f}s ({len(output.findings)} findings).[/]")

        # Save Scan Record to SQLite Persistence & Write JSON File
        from memory.database import get_db_engine
        import json

        db = get_db_engine(cfg.database.db_url)
        total_findings = sum(len(out.findings) for out in step_outputs)
        raw_results = {"target": plan.target, "profile": profile, "step_results": [s.model_dump() for s in step_outputs]}

        db.save_scan(
            target=plan.target,
            plugins_used=plan.selected_plugins,
            execution_time_ms=total_time_ms,
            status="COMPLETED",
            raw_results=raw_results,
            summary={"steps_executed": len(step_outputs), "total_findings": total_findings, "profile": profile}
        )

        clean_target = plan.target.replace("://", "_").replace("/", "_").replace(":", "_")
        json_filename = f"scan_{clean_target}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(raw_results, f, indent=2)

        console.print(Panel(
            f"[bold #00ff66]WORKFLOW EXECUTION COMPLETE[/]\n"
            f"Target: [bold #ffff00]{plan.target}[/]\n"
            f"Profile: [bold #ff007f]{profile.upper()}[/]\n"
            f"Steps Executed: {len(step_outputs)}\n"
            f"Total Duration: {total_time_ms / 1000.0:.2f} s\n"
            f"Findings Discovered: [bold #00ff66]{total_findings}[/]\n"
            f"[dim]Persisted to SQLite DB & saved to '{json_filename}'.[/dim]",
            title="[bold #00ffff]✅ EXECUTION SUMMARY[/]",
            border_style="#00ff66",
            box=box.DOUBLE,
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

    console.print("[bold #00ffff]┌──[ PERSISTENT SCAN AUDIT LOG ]──┐[/]\n")

    if not scans:
        console.print("[#ffff00]No historical scan records found in database.[/]")
        console.print(f"[dim]Database URL: {cfg.database.db_url}[/dim]\n")
        return

    table = Table(
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("ID", style="dim", width=5)
    table.add_column("Date / Timestamp", style="#00ffff", width=22)
    table.add_column("Target", style="#ffff00", width=20)
    table.add_column("Status", width=12)
    table.add_column("Plugins Used", style="#00ff66")
    table.add_column("Duration", width=12)

    for scan in scans:
        status_style = "[bold #00ff66]COMPLETED[/]" if scan.status == "COMPLETED" else f"[bold #ff0055]{scan.status}[/]"
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
        console.print(f"[bold #ff0055]CRITICAL ERROR:[/] Scan result JSON file '{file_path}' does not exist.")
        raise typer.Exit(code=1)

    try:
        with open(p, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        console.print(f"[bold #ff0055]CRITICAL ERROR:[/] Failed to parse JSON file '{file_path}': {str(e)}")
        raise typer.Exit(code=1)

    analyzer = AIResultsAnalyzer()
    with console.status("[bold #00ff66]⚡ Analyzing scan findings & segregating facts vs AI inferences...[/]"):
        analysis = analyzer.analyze_json(raw_data)

    console.print(f"\n[bold #00ffff]┌──[ AI ANALYSIS COMPLETE ]──┐[/]")
    console.print(f"Target: [bold #ffff00]{analysis.target}[/] | Confidence: [bold #00ff66]{analysis.confidence * 100:.1f}%[/]\n")

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
        title="[bold #00ffff]📄 SECURITY REPORTS GENERATED[/]",
        border_style="#00ff66",
        box=box.DOUBLE,
        expand=False
    ))
    console.print()


@app.command("dashboard")
def dashboard_command(
    ctx: typer.Context,
    target: str = typer.Option("127.0.0.1", "--target", "-t", help="Target scope for dashboard view."),
    profile: str = typer.Option("deep", "--profile", "-p", help="Assessment profile.")
):
    """Render interactive cybersecurity operations terminal dashboard."""
    from app.ui import create_ops_dashboard_layout

    cfg: AppConfig = ctx.obj["config"]
    layout = create_ops_dashboard_layout(
        config=cfg,
        target=target,
        profile=profile,
        evidence_count=42,
        findings_count=8,
        coverage_pct=76.0,
        elapsed_seconds=45.2
    )

    console.clear()
    console.print(layout)


# ─── LLM SUBCOMMAND GROUP ───────────────────────────────────────────────────

llm_app = typer.Typer(
    name="llm",
    help="🤖 Provider-Independent LLM Architecture Management Commands",
    no_args_is_help=True
)
app.add_typer(llm_app, name="llm")


@llm_app.command("providers")
def llm_list_providers(ctx: typer.Context):
    """List supported LLM providers, active endpoint configuration, and health status."""
    from core.llm import get_llm_provider, list_registered_providers

    cfg: AppConfig = ctx.obj["config"]
    active_provider_name = cfg.llm.provider.lower().strip()

    console.print("[bold #00ffff]┌──[ PROVIDER-INDEPENDENT LLM MATRIX ]──┐[/]\n")

    table = Table(
        title="[bold #00ff66]REGISTERED LLM PROVIDER BACKENDS[/]",
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Provider", style="#00ffff", width=16)
    table.add_column("Active State", width=15)
    table.add_column("Configured Endpoint", style="#ffff00")
    table.add_column("Health Check", width=14)

    for name in sorted(list_registered_providers()):
        prov = get_llm_provider(name, config=cfg)
        is_active = (name == active_provider_name)
        active_str = "[bold #00ff66][SELECTED][/]" if is_active else "[dim][AVAILABLE][/]"
        
        endpoint = getattr(prov, "base_url", cfg.llm.api_endpoint)
        health_ok = prov.health_check()
        health_str = "[bold #00ff66][ONLINE][/]" if health_ok else "[bold #ff0055][OFFLINE][/]"

        table.add_row(name, active_str, endpoint, health_str)

    console.print(table)
    console.print()


@llm_app.command("models")
def llm_list_models(
    ctx: typer.Context,
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Specify provider to query models for (openrouter, openai, ollama).")
):
    """List available LLM models for the active or specified provider."""
    from core.llm import get_llm_provider

    cfg: AppConfig = ctx.obj["config"]
    prov_name = provider or cfg.llm.provider
    prov = get_llm_provider(prov_name, config=cfg)

    console.print(f"\n[bold #00ffff]┌──[ AVAILABLE MODELS FOR PROVIDER: {prov.provider_name().upper()} ]──┐[/]\n")

    with console.status(f"[bold #00ff66]⚡ Fetching model list from {prov.provider_name()}...[/]"):
        models = prov.available_models()

    table = Table(
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Index", style="dim", width=6)
    table.add_column("Model Identifier", style="#00ff66")
    table.add_column("Status", width=16)

    for idx, model_id in enumerate(models, 1):
        is_default = (model_id == cfg.llm.model)
        status_str = "[bold #ffff00][ACTIVE DEFAULT][/]" if is_default else "[dim][AVAILABLE][/]"
        table.add_row(str(idx), model_id, status_str)

    console.print(table)
    console.print()


@llm_app.command("test")
def llm_test_connection(
    ctx: typer.Context,
    prompt: str = typer.Option("Return a single line status statement confirming LLM operational health.", "--prompt", help="Custom test prompt text.")
):
    """Run connectivity health check and test completion prompt against active LLM provider."""
    import time
    from core.llm import get_llm_provider

    cfg: AppConfig = ctx.obj["config"]
    prov = get_llm_provider(config=cfg)

    console.print(f"\n[bold #00ffff]┌──[ LLM PROVIDER DIAGNOSTIC & BENCHMARK TEST ]──┐[/]")
    console.print(f"[bold #00ffff]Provider:[/] [bold #ffff00]{prov.provider_name()}[/] | [bold #00ffff]Model:[/] [bold #ff007f]{cfg.llm.model}[/]\n")

    health_ok = prov.health_check()
    if not health_ok:
        console.print(f"[bold #ff0055]HEALTH CHECK WARNING:[/] Provider '{prov.provider_name()}' health check returned offline or unauthenticated state.")
        console.print(f"[dim]Endpoint: {getattr(prov, 'base_url', cfg.llm.api_endpoint)}[/dim]\n")

    with console.status(f"[bold #00ff66]⚡ Executing test completion request...[/]"):
        start_time = time.perf_counter()
        try:
            response_text = prov.generate(prompt=prompt, temperature=0.2, max_tokens=200)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            console.print(Panel(
                f"[#00ffff]Response Text:[/]\n{response_text.strip()}\n\n"
                f"[dim]Latency: {latency_ms:.2f} ms | Provider: {prov.provider_name()} | Model: {cfg.llm.model}[/dim]",
                title="[bold #00ff66]✅ TEST COMPLETION SUCCESSFUL[/]",
                border_style="#00ff66",
                box=box.DOUBLE,
                expand=False
            ))
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            console.print(Panel(
                f"[bold #ff0055]Completion Error:[/]\n{str(e)}\n\n"
                f"[dim]Failed after {latency_ms:.2f} ms[/dim]",
                title="[bold #ff0055]❌ TEST COMPLETION FAILED[/]",
                border_style="#ff0055",
                box=box.DOUBLE,
                expand=False
            ))
    console.print()


@llm_app.command("select")
def llm_select_provider(
    ctx: typer.Context,
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Provider name (openrouter, openai, ollama)."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model identifier to set as active default.")
):
    """Switch active LLM provider and model settings."""
    from core.llm import list_registered_providers, get_llm_provider

    cfg: AppConfig = ctx.obj["config"]

    selected_provider = provider
    if not selected_provider:
        providers = list_registered_providers()
        console.print(f"[bold #00ffff]Available Providers:[/] {', '.join(providers)}")
        selected_provider = typer.prompt("Select LLM Provider", default=cfg.llm.provider)

    selected_provider = selected_provider.lower().strip()
    if selected_provider not in list_registered_providers():
        console.print(f"[bold #ff0055]ERROR:[/] Unknown provider '{selected_provider}'. Valid choices: {', '.join(list_registered_providers())}")
        raise typer.Exit(code=1)

    prov = get_llm_provider(selected_provider, config=cfg)

    selected_model = model
    if not selected_model:
        avail_models = prov.available_models()
        default_m = avail_models[0] if avail_models else cfg.llm.model
        console.print(f"[bold #00ffff]Available Models for {selected_provider}:[/] {', '.join(avail_models[:5])}...")
        selected_model = typer.prompt("Select LLM Model", default=default_m)

    cfg.llm.provider = selected_provider
    cfg.llm.model = selected_model

    console.print(Panel(
        f"[bold #00ff66]ACTIVE LLM SELECTION UPDATED[/]\n"
        f"Provider: [bold #ffff00]{selected_provider}[/]\n"
        f"Model: [bold #ff007f]{selected_model}[/]\n"
        f"Endpoint: {getattr(prov, 'base_url', cfg.llm.api_endpoint)}",
        title="[bold #00ffff]⚙️ CONFIGURATION CHANGED[/]",
        border_style="#00ff66",
        box=box.DOUBLE,
        expand=False
    ))
    console.print()


# ─── SECURITY TOOLS SUBCOMMAND GROUP ─────────────────────────────────────────

tools_app = typer.Typer(
    name="tools",
    help="🛠️ Extensible Security-Tool Adapter Subsystem Commands",
    no_args_is_help=True
)
app.add_typer(tools_app, name="tools")


@tools_app.command("list")
def tools_list_cmd(ctx: typer.Context):
    """List all integrated security tool adapters, native plugins, and MCP tools."""
    from core.adapters import get_adapter_registry
    from core.registry import get_registry
    from core.mcp import get_mcp_registry

    adapter_reg = get_adapter_registry()
    plugin_reg = get_registry()
    mcp_reg = get_mcp_registry()

    adapters = adapter_reg.list_adapters()
    plugins = plugin_reg.list_plugins()
    mcp_tools = mcp_reg.list_tools()

    console.print("[bold #00ffff]┌──[ SECURITY TOOL MATRIX (ADAPTERS, PLUGINS & MCP) ]──┐[/]\n")

    table = Table(
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Tool Name", style="#00ffff", width=22)
    table.add_column("Category", style="#ffff00", width=22)
    table.add_column("Installation Status", width=20)
    table.add_column("Source / Version", style="dim")

    seen = set()

    # 1. Tool Adapters
    for name, adapter in sorted(adapters.items()):
        seen.add(name.lower())
        is_inst = adapter.is_installed()
        status_str = "[bold #00ff66][INSTALLED][/]" if is_inst else "[bold #ffff00][NOT INSTALLED][/]"
        ver_str = f"Adapter ({adapter.detect_version()})"
        table.add_row(adapter.name, adapter.category, status_str, ver_str)

    # 2. Native Plugins (whatweb, nikto, gobuster, nuclei)
    for name, plugin in sorted(plugins.items()):
        if name.lower() not in seen:
            seen.add(name.lower())
            is_inst = plugin.is_installed()
            status_str = "[bold #00ff66][INSTALLED][/]" if is_inst else "[bold #ffff00][NOT INSTALLED][/]"
            category = getattr(plugin, "category", "security_assessment")
            table.add_row(plugin.name, category, status_str, "Native Plugin")

    # 3. MCP Tools
    for tool in sorted(mcp_tools, key=lambda x: x.name):
        if tool.name.lower() not in seen:
            seen.add(tool.name.lower())
            status_str = "[bold #00ff66][INSTALLED][/]" if tool.enabled else "[bold #ff0055][DISABLED][/]"
            table.add_row(tool.name, tool.category, status_str, f"MCP ({tool.server_id})")

    console.print(table)
    console.print()


@tools_app.command("info")
def tools_info_cmd(
    ctx: typer.Context,
    tool_name: str = typer.Argument(..., help="Security tool identifier name (e.g. nmap, whatweb, nikto, gobuster, nuclei, zap, burp).")
):
    """Display detailed capability discovery, supported configuration options, and health metrics for a tool."""
    from core.adapters import get_adapter_registry
    from core.registry import get_registry
    from core.mcp import get_mcp_registry

    adapter_reg = get_adapter_registry()
    plugin_reg = get_registry()
    mcp_reg = get_mcp_registry()

    t_key = tool_name.lower().strip()
    adapter = adapter_reg.get_adapter(t_key)
    plugin = plugin_reg.get_plugin(t_key)
    mcp_tool = mcp_reg.get_tool(t_key)

    if not adapter and not plugin and not mcp_tool:
        all_tools = sorted(list(adapter_reg.list_adapters().keys()) + list(plugin_reg.list_plugins().keys()) + [t.name for t in mcp_reg.list_tools()])
        console.print(f"[bold #ff0055]ERROR:[/] Unknown security tool '{tool_name}'.")
        console.print(f"[dim]Available tools: {', '.join(all_tools)}[/dim]\n")
        raise typer.Exit(code=1)

    name = tool_name
    category = "security_assessment"
    description = "Security Tool Module"
    is_inst = False
    version = "Unknown"
    health_ok = False
    caps_api = False
    caps_async = True
    caps_auth = True
    categories = []
    options_schema = {}

    if adapter:
        name = adapter.name
        category = adapter.category
        description = adapter.description
        is_inst = adapter.is_installed()
        version = adapter.detect_version()
        health_ok = adapter.health_check()
        caps = adapter.discover_capabilities()
        caps_api = caps.supports_api
        caps_async = caps.supports_async
        caps_auth = caps.supports_auth
        categories = caps.categories
        options_schema = caps.supported_options
    elif plugin:
        name = plugin.name
        description = plugin.description
        category = getattr(plugin, "category", "security_assessment")
        is_inst = plugin.is_installed()
        version = "Native Subprocess Plugin"
        health_ok = is_inst
        categories = [category]
        options_schema = {"target": "Target host or URL"}
    elif mcp_tool:
        name = mcp_tool.name
        description = mcp_tool.description
        category = mcp_tool.category
        is_inst = mcp_tool.enabled
        version = f"MCP v{mcp_tool.version} ({mcp_tool.server_id})"
        health_ok = (mcp_tool.health == "HEALTHY")
        categories = [category]
        options_schema = mcp_tool.input_schema

    console.print(f"\n[bold #00ffff]┌──[ TOOL METADATA: {name.upper()} ]──┐[/]\n")

    tree = Tree(f"[bold #ff007f]{name}[/] [dim]({description})[/dim]")
    tree.add(f"[#00ffff]Category:[/] {category}")
    tree.add(f"[#00ffff]Installation Status:[/] {'[bold #00ff66]Installed[/]' if is_inst else '[bold #ffff00]Not Installed / Offline[/]'}")
    tree.add(f"[#00ffff]Detected Version:[/] {version}")
    tree.add(f"[#00ffff]Health Check:[/] {'[bold #00ff66][HEALTHY][/]' if health_ok else '[bold #ff0055][UNHEALTHY / OFFLINE][/]'}")

    cap_node = tree.add("[bold #ffff00]Capabilities & Protocol Support[/]")
    cap_node.add(f"[#00ffff]REST / RPC API Support:[/] {caps_api}")
    cap_node.add(f"[#00ffff]Asynchronous Execution:[/] {caps_async}")
    cap_node.add(f"[#00ffff]Target Authorization Check:[/] {caps_auth}")
    cap_node.add(f"[#00ffff]Assessment Categories:[/] {', '.join(categories)}")

    opt_node = tree.add("[bold #ffff00]Supported Options Schema[/]")
    for opt_k, opt_v in options_schema.items():
        opt_node.add(f"[#00ff66]{opt_k}:[/] {opt_v}")

    console.print(tree)
    console.print()


@tools_app.command("health")
def tools_health_cmd(ctx: typer.Context):
    """Perform real-time operational health checks across all registered adapters, plugins, and MCP tools."""
    from core.adapters import get_adapter_registry
    from core.registry import get_registry
    from core.mcp import get_mcp_registry

    adapter_reg = get_adapter_registry()
    plugin_reg = get_registry()
    mcp_reg = get_mcp_registry()

    adapters = adapter_reg.list_adapters()
    plugins = plugin_reg.list_plugins()
    mcp_tools = mcp_reg.list_tools()

    console.print("[bold #00ffff]┌──[ FULL SECURITY TOOL HEALTH DIAGNOSTICS ]──┐[/]\n")

    table = Table(
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Tool", style="#00ffff", width=22)
    table.add_column("Category", style="#ffff00", width=22)
    table.add_column("Operational Health", width=22)
    table.add_column("Version / Source", style="dim")

    seen = set()

    # 1. Tool Adapters
    for name, adapter in sorted(adapters.items()):
        seen.add(name.lower())
        health_ok = adapter.health_check()
        health_str = "[bold #00ff66][HEALTHY / ONLINE][/]" if health_ok else "[bold #ff0055][UNHEALTHY / OFFLINE][/]"
        ver_str = adapter.detect_version()
        table.add_row(adapter.name, adapter.category, health_str, ver_str)

    # 2. Native Plugins (whatweb, nikto, gobuster, nuclei)
    for name, plugin in sorted(plugins.items()):
        if name.lower() not in seen:
            seen.add(name.lower())
            is_inst = plugin.is_installed()
            health_str = "[bold #00ff66][HEALTHY / ONLINE][/]" if is_inst else "[bold #ff0055][UNHEALTHY / OFFLINE][/]"
            category = getattr(plugin, "category", "security_assessment")
            table.add_row(plugin.name, category, health_str, "Native Plugin")

    # 3. MCP Tools
    for tool in sorted(mcp_tools, key=lambda x: x.name):
        if tool.name.lower() not in seen:
            seen.add(tool.name.lower())
            health_ok = (tool.health == "HEALTHY" and tool.enabled)
            health_str = "[bold #00ff66][HEALTHY / ONLINE][/]" if health_ok else "[bold #ff0055][UNHEALTHY / OFFLINE][/]"
            table.add_row(tool.name, tool.category, health_str, f"MCP ({tool.server_id})")

    console.print(table)
    console.print()


# ─── MCP SUBCOMMAND GROUP ───────────────────────────────────────────────────

mcp_app = typer.Typer(
    name="mcp",
    help="🔌 Model Context Protocol (MCP) Integration Commands",
    no_args_is_help=True
)
app.add_typer(mcp_app, name="mcp")


@mcp_app.command("servers")
def mcp_servers_cmd(ctx: typer.Context):
    """List registered MCP servers and transport statuses."""
    from core.mcp import get_mcp_registry

    registry = get_mcp_registry()
    servers = registry.list_servers()

    console.print("[bold #00ffff]┌──[ MODEL CONTEXT PROTOCOL (MCP) SERVERS ]──┐[/]\n")

    table = Table(
        title="[bold #00ff66]REGISTERED MCP SERVER MATRIX[/]",
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Server ID", style="#00ffff", width=22)
    table.add_column("Server Name", style="bold white", width=32)
    table.add_column("Transport", style="#ffff00", width=12)
    table.add_column("Status", width=16)

    for sid, scfg in sorted(servers.items()):
        status_str = "[bold #00ff66][ENABLED][/]" if scfg.enabled else "[bold #ff0055][DISABLED][/]"
        table.add_row(sid, scfg.name, scfg.transport.upper(), status_str)

    console.print(table)
    console.print()


@mcp_app.command("tools")
def mcp_tools_cmd(ctx: typer.Context):
    """List exposed MCP tools and capability metadata."""
    from core.mcp import get_mcp_registry

    registry = get_mcp_registry()
    tools = registry.list_tools()

    console.print("[bold #00ffff]┌──[ UNIFIED MCP TOOL INDEX ]──┐[/]\n")

    table = Table(
        box=box.DOUBLE_EDGE,
        header_style="bold #ff007f",
        border_style="#00ffff"
    )
    table.add_column("Tool Name", style="#00ffff", width=24)
    table.add_column("Category", style="#ffff00", width=20)
    table.add_column("Server ID", style="bold white", width=22)
    table.add_column("Health Status", width=16)

    for tool in sorted(tools, key=lambda x: x.name):
        health_str = "[bold #00ff66][HEALTHY][/]" if tool.health == "HEALTHY" else "[bold #ff0055][UNHEALTHY][/]"
        table.add_row(tool.name, tool.category, tool.server_id, health_str)

    console.print(table)
    console.print()


@mcp_app.command("register")
def mcp_register_cmd(
    ctx: typer.Context,
    server_id: str = typer.Option(..., "--id", "-i", help="Unique MCP server ID (e.g. custom_mcp)."),
    name: str = typer.Option(..., "--name", "-n", help="Human-readable server name."),
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport mode (stdio, http, sse)."),
    command: Optional[str] = typer.Option(None, "--command", "-c", help="Process command for stdio transport."),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="HTTP URL for http/sse transport.")
):
    """Register a new MCP server in the orchestrator registry."""
    from core.mcp import get_mcp_registry, MCPServerConfig

    registry = get_mcp_registry()
    cmd_list = command.split() if command else []

    server_cfg = MCPServerConfig(
        server_id=server_id,
        name=name,
        transport=transport.lower(),
        command=cmd_list,
        url=url,
        enabled=True
    )

    success = registry.register_server(server_cfg)
    if success:
        console.print(f"[bold #00ff66]✓ Successfully registered MCP Server '{server_id}' ({name}).[/]")
    else:
        console.print(f"[bold #ff0055]✗ Failed to register MCP Server '{server_id}'. Check logs or connection.[/]")


if __name__ == "__main__":
    app()
