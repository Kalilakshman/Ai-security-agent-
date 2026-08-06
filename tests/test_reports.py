"""
Unit tests for multi-format report generators (reports/).
"""

import pytest
from pathlib import Path
from core.analyzer import AnalysisReport, ObservedFact, AIInference
from reports.markdown import MarkdownReportGenerator
from reports.html import HTMLReportGenerator
from reports.pdf import PDFReportGenerator


@pytest.fixture
def sample_analysis_report():
    return AnalysisReport(
        target="example.com",
        timestamp="2026-08-06T11:00:00Z",
        executive_summary="Target assessment completed.",
        observed_services=[
            ObservedFact(source_tool="nmap", finding_type="open_port", details={"port": 80, "service": "http"})
        ],
        interesting_findings=[],
        potential_risks=[
            AIInference(category="risk_hypothesis", fact_references=["nmap"], inference="HTTP unencrypted traffic risk.")
        ],
        recommendations=[
            AIInference(category="mitigation_step", fact_references=[], inference="Enforce HTTPS.")
        ],
        confidence=0.9,
        unknowns=["No internal network access."]
    )


def test_markdown_report_generator(sample_analysis_report, tmp_path):
    """Test generating Markdown report."""
    gen = MarkdownReportGenerator()
    out_file = tmp_path / "test_report.md"
    content = gen.generate(sample_analysis_report, output_path=out_file)

    assert "# 🛡️ Security Assessment Report" in content
    assert "example.com" in content
    assert "Enforce HTTPS" in content
    assert out_file.exists()


def test_html_report_generator(sample_analysis_report, tmp_path):
    """Test generating HTML report."""
    gen = HTMLReportGenerator()
    out_file = tmp_path / "test_report.html"
    content = gen.generate(sample_analysis_report, output_path=out_file)

    assert "<!DOCTYPE html>" in content
    assert "example.com" in content
    assert out_file.exists()


def test_pdf_report_generator(sample_analysis_report, tmp_path):
    """Test generating PDF report."""
    gen = PDFReportGenerator()
    out_file = tmp_path / "test_report.pdf"
    content_bytes = gen.generate(sample_analysis_report, output_path=out_file)

    assert len(content_bytes) > 0
