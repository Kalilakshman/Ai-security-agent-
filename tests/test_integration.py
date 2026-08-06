"""
End-to-End Integration tests.
"""

import pytest
import tempfile
from pathlib import Path
from core.config import AppConfig
from core.registry import PluginRegistry
from core.planner import AIPlanner
from core.workflow import WorkflowEngine
from core.analyzer import AIResultsAnalyzer
from memory.database import DatabaseEngine
from reports.markdown import MarkdownReportGenerator


def test_full_pipeline_end_to_end():
    """Test full pipeline integration: Config -> Planner -> Workflow -> DB -> Report Generator."""
    # 1. Config & Registry
    cfg = AppConfig()
    registry = PluginRegistry()

    # 2. Planning
    planner = AIPlanner(registry=registry)
    plan = planner.generate_plan("127.0.0.1")
    assert plan.target == "127.0.0.1"

    # 3. Workflow Execution
    engine = WorkflowEngine(registry=registry)
    workflow_result = engine.execute_plan(plan, authorized=True)
    assert workflow_result.authorized is True

    # 4. Database Persistence
    with tempfile.NamedTemporaryFile("w", suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    db = DatabaseEngine(db_url=f"sqlite:///{db_path}")

    scan_rec = db.save_scan(
        target=workflow_result.target,
        plugins_used=plan.selected_plugins,
        execution_time_ms=workflow_result.total_duration_ms,
        status="COMPLETED",
        raw_results=workflow_result.model_dump(),
        summary=workflow_result.summary
    )
    assert scan_rec is not None
    assert len(db.get_recent_scans()) == 1

    # 5. AI Results Analysis & Report Generation
    analyzer = AIResultsAnalyzer()
    analysis_report = analyzer.analyze(workflow_result)
    assert analysis_report.target == "127.0.0.1"

    md_gen = MarkdownReportGenerator()
    out_md = tmp_file = db_path.with_suffix(".md")
    md_content = md_gen.generate(analysis_report, output_path=out_md)

    assert "# 🛡️ Security Assessment Report" in md_content
    assert out_md.exists()

    # Cleanup
    try:
        db_path.unlink(missing_ok=True)
        out_md.unlink(missing_ok=True)
    except Exception:
        pass
