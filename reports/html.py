"""
HTML Report Generator.

Generates self-contained, responsive HTML security reports with embedded modern dark-mode styling and print support.
"""

import json
import html
from pathlib import Path
from typing import Optional, Dict, Any
from core.analyzer import AnalysisReport


class HTMLReportGenerator:
    """Renders AnalysisReport object into self-contained HTML (.html) documents."""

    def generate(
        self,
        report: AnalysisReport,
        scan_data: Optional[Dict[str, Any]] = None,
        output_path: Optional[str | Path] = None
    ) -> str:
        target_esc = html.escape(report.target)
        timestamp_esc = html.escape(report.timestamp)
        exec_summary_esc = html.escape(report.executive_summary)

        # Build Services Table HTML
        svc_rows = []
        for svc in report.observed_services:
            tool = html.escape(svc.source_tool)
            ftype = html.escape(svc.finding_type)
            details = html.escape(json.dumps(svc.details))
            svc_rows.append(f"<tr><td><code>{tool}</code></td><td><code>{ftype}</code></td><td>{details}</td></tr>")
        svc_table_html = "".join(svc_rows) if svc_rows else "<tr><td colspan='3'>No open network services observed.</td></tr>"

        # Build Risks HTML
        risk_cards = []
        for risk in report.potential_risks:
            cat = html.escape(risk.category.replace("_", " ").title())
            inf = html.escape(risk.inference)
            refs = html.escape(", ".join(risk.fact_references))
            risk_cards.append(f"""
            <div class="card risk-card">
                <h4>⚠️ {cat}</h4>
                <p><strong>Evidence Reference:</strong> {refs}</p>
                <p>{inf}</p>
            </div>
            """)
        risks_html = "".join(risk_cards) if risk_cards else "<p>No immediate risks inferred.</p>"

        # Build Recommendations HTML
        rec_items = []
        for rec in report.recommendations:
            cat = html.escape(rec.category.upper())
            inf = html.escape(rec.inference)
            rec_items.append(f"<li><strong>[{cat}]</strong> {inf}</li>")
        recs_html = "".join(rec_items) if rec_items else "<li>Maintain security baselines.</li>"

        # Build Unknowns HTML
        unk_items = []
        for unk in report.unknowns:
            unk_items.append(f"<li>⚠️ {html.escape(unk)}</li>")
        unknowns_html = "".join(unk_items) if unk_items else "<li>None reported.</li>"

        raw_json_esc = html.escape(json.dumps(scan_data or report.model_dump(), indent=2))

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Assessment Report - {target_esc}</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --accent-cyan: #38bdf8;
            --accent-green: #4ade80;
            --accent-yellow: #facc15;
            --accent-red: #f87171;
            --border-color: #334155;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{ color: var(--accent-cyan); margin-bottom: 5px; }}
        .badge {{
            display: inline-block;
            background: #0284c7;
            color: #fff;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .risk-card {{ border-left: 4px solid var(--accent-yellow); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{ background: #0f172a; color: var(--accent-cyan); }}
        code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; font-family: monospace; }}
        pre {{ background: #0f172a; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 0.85rem; }}
        @media print {{
            body {{ background: #fff; color: #000; }}
            .card {{ background: #fff; border: 1px solid #ccc; color: #000; }}
            th {{ background: #eee; color: #000; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ AI Security Assessment Report</h1>
            <p>Target: <code>{target_esc}</code> | Timestamp: <code>{timestamp_esc}</code></p>
            <span class="badge">AI Confidence: {report.confidence * 100:.1f}%</span>
        </header>

        <section class="card">
            <h2>Executive Summary</h2>
            <p>{exec_summary_esc}</p>
        </section>

        <section class="card">
            <h2>Observed Services (Facts)</h2>
            <table>
                <thead>
                    <tr><th>Source Tool</th><th>Finding Type</th><th>Observation Details</th></tr>
                </thead>
                <tbody>
                    {svc_table_html}
                </tbody>
            </table>
        </section>

        <section class="card">
            <h2>Potential Risks & Hypotheses (AI Inferences)</h2>
            {risks_html}
        </section>

        <section class="card">
            <h2>Actionable Recommendations</h2>
            <ul>
                {recs_html}
            </ul>
        </section>

        <section class="card">
            <h2>Unknowns & Limitations</h2>
            <ul>
                {unknowns_html}
            </ul>
        </section>

        <section class="card">
            <h2>Appendix - Raw Scan JSON</h2>
            <pre>{raw_json_esc}</pre>
        </section>
    </div>
</body>
</html>
"""

        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(html_content, encoding="utf-8")

        return html_content
