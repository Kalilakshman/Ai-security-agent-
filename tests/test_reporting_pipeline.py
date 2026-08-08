"""
Unit tests for Upgraded Evidence, Analysis, and Multi-Format Reporting Pipeline.
"""

import json
import pytest
from pathlib import Path

from core.analyzer import (
    NormalizedToolResult,
    EvidenceModel,
    ObservedFact,
    AIInference,
    AnalysisReport,
    AIResultsAnalyzer,
)
from reports.markdown import MarkdownReportGenerator
from reports.html import HTMLReportGenerator
from reports.pdf import PDFReportGenerator


@pytest.fixture
def sample_analysis_report():
    return AnalysisReport(
        target="127.0.0.1",
        timestamp="2026-08-08T12:00:00Z",
        scope="Authorized Localhost Scope",
        profile="deep",
        executive_summary="Security assessment of 127.0.0.1 completed cleanly with open HTTP and HTTPS ports.",
        timeline=[
            {"step": 1, "tool": "nmap", "status": "COMPLETED", "duration_seconds": 2.5},
            {"step": 2, "tool": "whatweb", "status": "COMPLETED", "duration_seconds": 1.2}
        ],
        tool_summary=[
            {"tool": "nmap", "version": "7.94", "status": "COMPLETED", "duration_seconds": 2.5, "findings_count": 2},
            {"tool": "whatweb", "version": "0.5.5", "status": "COMPLETED", "duration_seconds": 1.2, "findings_count": 1}
        ],
        evidence_list=[
            EvidenceModel(
                source_tool="nmap",
                observation="Port 80/tcp open (http Apache httpd 2.4.41)",
                evidence_type="open_port",
                confidence=1.0,
                reference="nmap_127.0.0.1_80_tcp"
            )
        ],
        observed_facts=[
            ObservedFact(
                source_tool="nmap",
                finding_type="open_port",
                details={"port": 80, "service": "http", "version": "Apache 2.4.41"},
                reference="nmap_127.0.0.1_80_tcp"
            )
        ],
        ai_inferences=[
            AIInference(
                category="analytical_hypothesis",
                fact_references=["nmap_127.0.0.1_80_tcp"],
                inference="Apache 2.4.41 is an older version requiring security baseline review.",
                severity="medium"
            )
        ],
        potential_risks=[
            AIInference(
                category="risk_hypothesis",
                fact_references=["nmap_127.0.0.1_80_tcp"],
                inference="Unencrypted HTTP service on port 80 allows plain text transport.",
                severity="high"
            )
        ],
        recommendations=[
            AIInference(
                category="remediation",
                fact_references=["nmap_127.0.0.1_80_tcp"],
                inference="Enforce HTTP to HTTPS redirect.",
                severity="info"
            )
        ],
        confidence=0.90,
        coverage=85.0,
        unknowns=["Authenticated vulnerability scan required for deeper CVE discovery."],
        appendix_json={"raw_test": "data"}
    )


def test_normalized_tool_result_model():
    """Test NormalizedToolResult serialization and schema defaults."""
    res = NormalizedToolResult(
        tool="nmap",
        target="127.0.0.1",
        status="COMPLETED",
        findings=[{"port": 80}]
    )
    assert res.tool == "nmap"
    assert res.duration == 0.0
    assert res.findings == [{"port": 80}]


def test_evidence_model_serialization():
    """Test EvidenceModel serialization."""
    ev = EvidenceModel(
        source_tool="nmap",
        observation="Port 80 open",
        evidence_type="port_scan",
        confidence=1.0,
        reference="nmap_1"
    )
    assert ev.source_tool == "nmap"
    assert ev.confidence == 1.0


def test_ai_results_analyzer_deterministic_fallback():
    """Test AIResultsAnalyzer generates deterministic report from raw scan JSON without AI synthesis."""
    analyzer = AIResultsAnalyzer()
    raw_data = {
        "target": "127.0.0.1",
        "profile": "standard",
        "step_results": [
            {
                "tool": "nmap",
                "status": "COMPLETED",
                "findings": [{"port_proto": "80/tcp", "service": "http"}],
                "errors": [],
                "metadata": {"execution_time_ms": 1500.0, "tool_version": "7.94"}
            }
        ]
    }

    report = analyzer._build_deterministic_fallback("127.0.0.1", "2026-08-08T12:00:00Z", "standard", [], [], [], raw_data)
    assert isinstance(report, AnalysisReport)
    assert report.target == "127.0.0.1"
    assert report.confidence == 0.85
    assert len(report.observed_facts) == 1


def test_markdown_report_generator(sample_analysis_report, tmp_path):
    """Test Markdown report generation with GFM tables and risk summary."""
    out_file = tmp_path / "report.md"
    gen = MarkdownReportGenerator()
    content = gen.generate(sample_analysis_report, output_path=out_file)

    assert out_file.exists()
    assert "# 🛡️ Comprehensive Security Assessment Report — `127.0.0.1`" in content
    assert "Observed Facts (Verifiable Data)" in content
    assert "Extracted Evidence Repository" in content
    assert "Potential Risks & Contextual Hypotheses (AI Inferences)" in content
    assert "Appendix — Raw Normalized JSON Execution Data" in content


def test_html_report_generator(sample_analysis_report, tmp_path):
    """Test HTML report generation with embedded CSS and SVG chart."""
    out_file = tmp_path / "report.html"
    gen = HTMLReportGenerator()
    content = gen.generate(sample_analysis_report, output_path=out_file)

    assert out_file.exists()
    assert "🛡️ AI Security Assessment Report" in content
    assert "Observed Services (Facts)" in content
    assert "<svg" in content
    assert "Raw Normalized JSON Data" in content


def test_pdf_report_generator(sample_analysis_report, tmp_path):
    """Test PDF report generation or print fallback."""
    out_file = tmp_path / "report.pdf"
    gen = PDFReportGenerator()
    pdf_bytes = gen.generate(sample_analysis_report, output_path=out_file)

    assert isinstance(pdf_bytes, bytes)
    assert out_file.exists() or (tmp_path / "report.html").exists()
