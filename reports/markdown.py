"""
Markdown Report Generator.

Generates structured GFM security reports including Scope, Timestamp, Execution, Findings, Recommendations, and Appendix.
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
        """Generate Markdown document text and optionally write to file."""
        lines = []

        # Title & Disclaimer Header
        lines.append(f"# 🛡️ Security Assessment Report — `{report.target}`")
        lines.append("")
        lines.append("> **IMPORTANT DISCLAIMER**: This report contains security assessment observations performed under authorized testing scope.")
        lines.append("")

        # Section 1: Scope & Metadata
        lines.append("## 1. Scope & Execution Metadata")
        lines.append("")
        lines.append(f"- **Target System**: `{report.target}`")
        lines.append(f"- **Assessment Timestamp**: `{report.timestamp}`")
        lines.append(f"- **AI Analysis Confidence Score**: `{report.confidence * 100:.1f}%`")
        lines.append("")

        # Section 2: Executive Summary
        lines.append("## 2. Executive Summary")
        lines.append("")
        lines.append(report.executive_summary)
        lines.append("")

        # Section 3: Observed Services (Facts)
        lines.append("## 3. Observed Services (Verifiable Facts)")
        lines.append("")
        if report.observed_services:
            lines.append("| Source Tool | Finding Type | Details |")
            lines.append("| :--- | :--- | :--- |")
            for svc in report.observed_services:
                details_str = ", ".join(f"{k}={v}" for k, v in svc.details.items())
                lines.append(f"| `{svc.source_tool}` | `{svc.finding_type}` | {details_str} |")
        else:
            lines.append("*No open network services or ports were directly observed during this assessment.*")
        lines.append("")

        # Section 4: Interesting Findings (Facts)
        lines.append("## 4. Notable Findings & Observations (Verifiable Facts)")
        lines.append("")
        if report.interesting_findings:
            for idx, find in enumerate(report.interesting_findings, 1):
                lines.append(f"### 4.{idx}. Observation (`{find.source_tool}`)")
                lines.append(f"- **Category**: `{find.finding_type}`")
                lines.append("```json")
                lines.append(json.dumps(find.details, indent=2))
                lines.append("```")
                lines.append("")
        else:
            lines.append("*No additional security findings observed.*")
        lines.append("")

        # Section 5: Potential Risks (AI Inferences)
        lines.append("## 5. Potential Risks & Contextual Hypotheses (AI Inferences)")
        lines.append("")
        lines.append("> [!NOTE]")
        lines.append("> The items in this section represent contextual AI analytical inferences derived from observed facts.")
        lines.append("")
        if report.potential_risks:
            for idx, risk in enumerate(report.potential_risks, 1):
                refs = ", ".join(risk.fact_references) if risk.fact_references else "General Context"
                lines.append(f"### 5.{idx}. {risk.category.replace('_', ' ').title()}")
                lines.append(f"- **Supported by Evidence**: {refs}")
                lines.append(f"- **Analysis**: {risk.inference}")
                lines.append("")
        else:
            lines.append("*No immediate high-risk conditions inferred from current observation data.*")
        lines.append("")

        # Section 6: Actionable Recommendations (AI Inferences)
        lines.append("## 6. Strategic Recommendations")
        lines.append("")
        if report.recommendations:
            for idx, rec in enumerate(report.recommendations, 1):
                lines.append(f"{idx}. **[{rec.category.upper()}]**: {rec.inference}")
        else:
            lines.append("*Maintain current security controls and continuous patch management.*")
        lines.append("")

        # Section 7: Assessment Unknowns & Limitations
        lines.append("## 7. Unknowns & Assessment Limitations")
        lines.append("")
        if report.unknowns:
            for unk in report.unknowns:
                lines.append(f"- ⚠️ {unk}")
        else:
            lines.append("- Assessment completed within standard non-destructive scope.")
        lines.append("")

        # Section 8: Appendix
        lines.append("## 8. Appendix — Raw Normalized Execution Data")
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Click to expand Raw Execution Data JSON</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(scan_data or report.model_dump(), indent=2))
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
