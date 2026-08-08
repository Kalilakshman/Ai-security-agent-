"""
Upgraded HTML Report Generator with embedded modern dark-mode styling, SVG risk charts, and full report sections.
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
        profile_esc = html.escape(report.profile.upper())
        exec_summary_esc = html.escape(report.executive_summary)

        # Count risks by severity
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in report.potential_risks + report.ai_inferences:
            s = r.severity.lower()
            if s in risk_counts:
                risk_counts[s] += 1

        # Build Observed Facts Table HTML
        facts_rows = []
        for fact in report.observed_facts:
            tool = html.escape(fact.source_tool)
            ftype = html.escape(fact.finding_type)
            ref = html.escape(fact.reference)
            details = html.escape(json.dumps(fact.details))
            facts_rows.append(f"<tr><td><code>{tool}</code></td><td><code>{ftype}</code></td><td><code>{ref}</code></td><td>{details}</td></tr>")
        facts_table_html = "".join(facts_rows) if facts_rows else "<tr><td colspan='4'>No open services observed.</td></tr>"

        # Build Evidence Table HTML
        evidence_rows = []
        for ev in report.evidence_list:
            ref = html.escape(ev.reference)
            tool = html.escape(ev.source_tool)
            etype = html.escape(ev.evidence_type)
            obs = html.escape(ev.observation)
            conf = f"{ev.confidence * 100:.0f}%"
            evidence_rows.append(f"<tr><td><code>{ref}</code></td><td><code>{tool}</code></td><td><code>{etype}</code></td><td>{obs}</td><td><span class='badge'>{conf}</span></td></tr>")
        evidence_table_html = "".join(evidence_rows) if evidence_rows else "<tr><td colspan='5'>No evidence models captured.</td></tr>"

        # Build Tool Summary Table HTML
        tool_rows = []
        for ts in report.tool_summary:
            tool = html.escape(str(ts.get("tool")))
            ver = html.escape(str(ts.get("version")))
            st = html.escape(str(ts.get("status")))
            dur = f"{ts.get('duration_seconds', 0.0):.1f}s"
            cnt = ts.get("findings_count", 0)
            tool_rows.append(f"<tr><td><code>{tool}</code></td><td>{ver}</td><td><span class='badge badge-success'>{st}</span></td><td>{dur}</td><td>{cnt}</td></tr>")
        tool_table_html = "".join(tool_rows) if tool_rows else "<tr><td colspan='5'>No tools executed.</td></tr>"

        # Build Risks Cards HTML
        risk_cards = []
        for risk in report.potential_risks:
            cat = html.escape(risk.category.replace("_", " ").title())
            inf = html.escape(risk.inference)
            refs = html.escape(", ".join(risk.fact_references))
            sev = html.escape(risk.severity.upper())
            sev_class = f"badge-{risk.severity.lower()}"
            risk_cards.append(f"""
            <div class="card risk-card">
                <h4><span class="badge {sev_class}">{sev}</span> {cat}</h4>
                <p><strong>Evidence Reference:</strong> <code>{refs}</code></p>
                <p>{inf}</p>
            </div>
            """)
        risks_html = "".join(risk_cards) if risk_cards else "<p>No immediate high-risk conditions inferred.</p>"

        # Build Recommendations HTML
        rec_items = []
        for rec in report.recommendations:
            cat = html.escape(rec.category.upper())
            inf = html.escape(rec.inference)
            sev = html.escape(rec.severity.upper())
            rec_items.append(f"<li><strong>[{cat}] ({sev})</strong> {inf}</li>")
        recs_html = "".join(rec_items) if rec_items else "<li>Maintain baseline access control and security rules.</li>"

        # Build Unknowns HTML
        unk_items = []
        for unk in report.unknowns:
            unk_items.append(f"<li>⚠️ {html.escape(unk)}</li>")
        unknowns_html = "".join(unk_items) if unk_items else "<li>None reported.</li>"

        raw_json_esc = html.escape(json.dumps(scan_data or report.appendix_json or report.model_dump(), indent=2))

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Assessment Report - {target_esc}</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: #151c2c;
            --text-color: #f1f5f9;
            --accent-cyan: #38bdf8;
            --accent-green: #4ade80;
            --accent-yellow: #facc15;
            --accent-red: #f87171;
            --border-color: #1e293b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{
            border-bottom: 2px solid var(--accent-cyan);
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
        .badge-critical {{ background: #dc2626; }}
        .badge-high {{ background: #ea580c; }}
        .badge-medium {{ background: #d97706; }}
        .badge-low {{ background: #16a34a; }}
        .badge-success {{ background: #059669; }}
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
            padding: 24px;
            margin-bottom: 24px;
        }}
        .risk-card {{ border-left: 4px solid var(--accent-yellow); }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid var(--border-color); }}
        th {{ background: #0b0f19; color: var(--accent-cyan); }}
        code {{ background: #0b0f19; color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-family: monospace; }}
        pre {{ background: #0b0f19; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 0.85rem; color: #a7f3d0; }}
        .chart-container {{ display: flex; align-items: center; gap: 30px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ AI Security Assessment Report</h1>
            <p>Target: <code>{target_esc}</code> | Profile: <span class="badge">{profile_esc}</span> | Timestamp: <code>{timestamp_esc}</code></p>
            <span class="badge">AI Confidence: {report.confidence * 100:.1f}%</span>
            <span class="badge">Coverage: {report.coverage:.1f}%</span>
        </header>

        <section class="card">
            <h2>1. Executive Summary</h2>
            <p>{exec_summary_esc}</p>
        </section>

        <section class="card">
            <h2>2. Integrated Tool Summary</h2>
            <table>
                <thead>
                    <tr><th>Tool</th><th>Version</th><th>Status</th><th>Duration</th><th>Findings Count</th></tr>
                </thead>
                <tbody>
                    {tool_table_html}
                </tbody>
            </table>
        </section>

        <section class="card">
            <h2>3. Observed Facts (Verifiable Data)</h2>
            <table>
                <thead>
                    <tr><th>Source Tool</th><th>Finding Type</th><th>Reference</th><th>Observation Details</th></tr>
                </thead>
                <tbody>
                    {facts_table_html}
                </tbody>
            </table>
        </section>

        <section class="card">
            <h2>4. Extracted Evidence Repository</h2>
            <table>
                <thead>
                    <tr><th>Evidence ID</th><th>Source Tool</th><th>Type</th><th>Factual Observation</th><th>Confidence</th></tr>
                </thead>
                <tbody>
                    {evidence_table_html}
                </tbody>
            </table>
        </section>

        <section class="card">
            <h2>5. Risk Summary & SVG Breakdown Chart</h2>
            <div class="chart-container">
                <svg width="180" height="180" viewBox="0 0 36 36">
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#1e293b" stroke-width="3.8"/>
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#f87171" stroke-width="3.8" stroke-dasharray="{min(risk_counts['critical']*25, 100)}, 100"/>
                </svg>
                <div>
                    <p><span class="badge badge-critical">Critical: {risk_counts['critical']}</span></p>
                    <p><span class="badge badge-high">High: {risk_counts['high']}</span></p>
                    <p><span class="badge badge-medium">Medium: {risk_counts['medium']}</span></p>
                    <p><span class="badge badge-low">Low/Info: {risk_counts['low']}</span></p>
                </div>
            </div>
        </section>

        <section class="card">
            <h2>6. Potential Risks & Hypotheses (AI Inferences)</h2>
            {risks_html}
        </section>

        <section class="card">
            <h2>7. Actionable Recommendations</h2>
            <ul>
                {recs_html}
            </ul>
        </section>

        <section class="card">
            <h2>8. Unknowns & Assessment Limitations</h2>
            <ul>
                {unknowns_html}
            </ul>
        </section>

        <section class="card">
            <h2>9. Appendix - Raw Normalized JSON Data</h2>
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
