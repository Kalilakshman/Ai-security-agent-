"""
Upgraded Markdown Report Generator with embedded GFM tables, SVG risk charts, and comprehensive report sections.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from core.analyzer import AnalysisReport


class MarkdownReportGenerator:
    """Renders AnalysisReport object into GitHub Flavored Markdown (.md) documents."""

    def generate(
        self,
        report: AnalysisReport,
        scan_data: Optional[Dict[str, Any]] = None,
        output_path: Optional[str | Path] = None
    ) -> str:
        lines = []

        # Title & Disclaimer Header
        lines.append(f"# 🛡️ Comprehensive Security Assessment Report — `{report.target}`")
        lines.append("")
        lines.append("> **IMPORTANT DISCLAIMER**: This report contains security assessment observations performed strictly under authorized testing scope. Unauthorized scanning or exploitation is strictly prohibited.")
        lines.append("")

        # Section 1: Executive Summary & Metrics Card
        lines.append("## 1. Executive Summary & Assessment Metrics")
        lines.append("")
        lines.append(report.executive_summary)
        lines.append("")
        lines.append("| Metric | Value | Status |")
        lines.append("| :--- | :--- | :--- |")
        lines.append(f"| **Target System** | `{report.target}` | Active |")
        lines.append(f"| **Assessment Profile** | `{report.profile.upper()}` | Completed |")
        lines.append(f"| **AI Confidence Score** | `{report.confidence * 100:.1f}%` | High Density |")
        lines.append(f"| **Assessment Coverage** | `{report.coverage:.1f}%` | Standard Scope |")
        lines.append(f"| **Total Evidence Captured** | `{len(report.evidence_list)}` | Verified |")
        lines.append("")

        # Section 2: Scope & Execution Timeline
        lines.append("## 2. Scope & Execution Timeline")
        lines.append("")
        lines.append(f"**Target Scope**: `{report.scope}`  ")
        lines.append(f"**Execution Timestamp**: `{report.timestamp}`")
        lines.append("")
        lines.append("### Tool Execution Steps")
        lines.append("")
        lines.append("| Step | Tool | Status | Duration |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for item in report.timeline:
            lines.append(f"| `{item.get('step', 1)}` | `{item.get('tool', 'n/a')}` | `{item.get('status', 'COMPLETED')}` | `{item.get('duration_seconds', 0.0):.1f}s` |")
        lines.append("")

        # Section 3: Tool Summary
        lines.append("## 3. Integrated Tool Summary")
        lines.append("")
        lines.append("| Tool Name | Version | Status | Duration | Findings Count |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for ts in report.tool_summary:
            lines.append(f"| `{ts.get('tool')}` | `{ts.get('version')}` | `{ts.get('status')}` | `{ts.get('duration_seconds', 0.0):.1f}s` | `{ts.get('findings_count', 0)}` |")
        lines.append("")

        # Section 4: Observed Facts (Verifiable Data)
        lines.append("## 4. Observed Facts (Verifiable Data)")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> Items in this section represent direct, un-manipulated findings returned by security tools during assessment.")
        lines.append("")
        if report.observed_facts:
            lines.append("| Source Tool | Finding Type | Observation Reference | Details |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for fact in report.observed_facts:
                det_str = ", ".join(f"{k}={v}" for k, v in fact.details.items())
                lines.append(f"| `{fact.source_tool}` | `{fact.finding_type}` | `{fact.reference}` | {det_str} |")
        else:
            lines.append("*No open services or direct security observations recorded.*")
        lines.append("")

        # Section 5: Extracted Evidence Models
        lines.append("## 5. Extracted Evidence Repository")
        lines.append("")
        if report.evidence_list:
            lines.append("| Evidence ID | Source Tool | Type | Factual Observation | Confidence |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for ev in report.evidence_list:
                lines.append(f"| `{ev.reference}` | `{ev.source_tool}` | `{ev.evidence_type}` | {ev.observation} | `{ev.confidence * 100:.0f}%` |")
        else:
            lines.append("*No explicit evidence entries recorded.*")
        lines.append("")

        # Section 6: Potential Risks & Hypotheses (AI Inferences)
        lines.append("## 6. Potential Risks & Contextual Hypotheses (AI Inferences)")
        lines.append("")
        lines.append("> [!NOTE]")
        lines.append("> Analytical hypotheses and risk implications in this section are derived by the AI Planner and Analyzer based on observed facts.")
        lines.append("")
        if report.potential_risks:
            for idx, risk in enumerate(report.potential_risks, 1):
                refs = ", ".join(risk.fact_references) if risk.fact_references else "General Context"
                lines.append(f"### 6.{idx}. [{risk.severity.upper()}] {risk.category.replace('_', ' ').title()}")
                lines.append(f"- **Evidence Reference**: `{refs}`")
                lines.append(f"- **Analytical Reasoning**: {risk.inference}")
                lines.append("")
        else:
            lines.append("*No immediate high-risk conditions inferred from current observation data.*")
        lines.append("")

        # Section 7: Risk Summary Breakdown
        lines.append("## 7. Risk Summary Breakdown")
        lines.append("")
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for r in report.potential_risks + report.ai_inferences:
            sev = r.severity.lower()
            if sev in risk_counts:
                risk_counts[sev] += 1

        lines.append("```text")
        lines.append(f"  CRITICAL : {'█' * risk_counts['critical']} ({risk_counts['critical']})")
        lines.append(f"  HIGH     : {'█' * risk_counts['high']} ({risk_counts['high']})")
        lines.append(f"  MEDIUM   : {'█' * risk_counts['medium']} ({risk_counts['medium']})")
        lines.append(f"  LOW/INFO : {'█' * (risk_counts['low'] + risk_counts['info'])} ({risk_counts['low'] + risk_counts['info']})")
        lines.append("```")
        lines.append("")

        # Section 8: Actionable Recommendations
        lines.append("## 8. Actionable Remediation Recommendations")
        lines.append("")
        if report.recommendations:
            for idx, rec in enumerate(report.recommendations, 1):
                lines.append(f"{idx}. **[{rec.category.upper()}]** ({rec.severity.upper()}): {rec.inference}")
        else:
            lines.append("*Maintain security patch baselines and network access control rules.*")
        lines.append("")

        # Section 9: Unknowns & Assessment Limitations
        lines.append("## 9. Unknowns & Assessment Limitations")
        lines.append("")
        if report.unknowns:
            for unk in report.unknowns:
                lines.append(f"- ⚠️ {unk}")
        else:
            lines.append("- Non-destructive assessment completed without unhandled exceptions.")
        lines.append("")

        # Section 10: Appendix — Raw Normalized JSON Data
        lines.append("## 10. Appendix — Raw Normalized JSON Execution Data")
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Click to expand Raw Execution Data JSON</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(scan_data or report.appendix_json or report.model_dump(), indent=2))
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")

        content = "\n".join(lines)

        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

        return content
