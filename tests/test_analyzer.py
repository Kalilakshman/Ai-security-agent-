"""
Unit tests for AI Results Analyzer (core/analyzer.py).
"""

import pytest
from core.analyzer import AIResultsAnalyzer, AnalysisReport


def test_analyzer_distinguishes_facts_and_inferences():
    """Test AIResultsAnalyzer produces structured AnalysisReport distinguishing facts from inferences."""
    sample_scan_json = {
        "target": "127.0.0.1",
        "timestamp": "2026-08-06T11:00:00Z",
        "step_results": [
            {
                "tool": "nmap",
                "findings": [
                    {"port_proto": "80/tcp", "service": "http", "version": "Apache 2.4.41"}
                ]
            }
        ]
    }

    analyzer = AIResultsAnalyzer()
    report = analyzer.analyze_json(sample_scan_json)

    assert isinstance(report, AnalysisReport)
    assert report.target == "127.0.0.1"
    assert len(report.observed_services) > 0
    assert report.observed_services[0].source_tool == "nmap"
    assert isinstance(report.potential_risks, list)
    assert isinstance(report.recommendations, list)
    assert 0.0 <= report.confidence <= 1.0
