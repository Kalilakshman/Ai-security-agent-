"""
PDF Report Generator.

Generates PDF security reports using ReportLab if available, or structured print-ready document fallback.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from core.analyzer import AnalysisReport
from core.logger import get_logger

logger = get_logger("pdf_reporter")


class PDFReportGenerator:
    """Renders AnalysisReport object into PDF (.pdf) documents."""

    def generate(
        self,
        report: AnalysisReport,
        scan_data: Optional[Dict[str, Any]] = None,
        output_path: Optional[str | Path] = None
    ) -> bytes:
        """Generate PDF document content bytes and optionally write to file."""
        target_path = Path(output_path) if output_path else Path(f"security_report_{report.target}.pdf")

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            doc = SimpleDocTemplate(str(target_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor('#0284c7')
            )

            story.append(Paragraph(f"AI Security Assessment Report: {report.target}", title_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>Timestamp:</b> {report.timestamp} | <b>Confidence:</b> {report.confidence * 100:.1f}%", styles['Normal']))
            story.append(Spacer(1, 15))

            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            story.append(Paragraph(report.executive_summary, styles['Normal']))
            story.append(Spacer(1, 15))

            # Observed Services
            story.append(Paragraph("Observed Services (Facts)", styles['Heading2']))
            svc_data = [["Source Tool", "Finding Type", "Details"]]
            for svc in report.observed_services:
                svc_data.append([svc.source_tool, svc.finding_type, str(svc.details)[:60]])

            if len(svc_data) > 1:
                t = Table(svc_data, colWidths=[100, 120, 280])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ]))
                story.append(t)
            else:
                story.append(Paragraph("No open network services observed.", styles['Normal']))
            story.append(Spacer(1, 15))

            # Potential Risks
            story.append(Paragraph("Potential Risks (AI Inferences)", styles['Heading2']))
            for risk in report.potential_risks:
                story.append(Paragraph(f"• <b>{risk.category}</b>: {risk.inference}", styles['Normal']))
                story.append(Spacer(1, 4))
            story.append(Spacer(1, 15))

            # Recommendations
            story.append(Paragraph("Recommendations", styles['Heading2']))
            for rec in report.recommendations:
                story.append(Paragraph(f"• <b>[{rec.category.upper()}]</b>: {rec.inference}", styles['Normal']))
                story.append(Spacer(1, 4))

            doc.build(story)
            logger.info(f"PDF report generated at '{target_path}' using ReportLab.")

            if target_path.exists():
                return target_path.read_bytes()

        except ImportError:
            logger.warning("ReportLab package not installed. Generating HTML-PDF print document fallback.")
            from reports.html import HTMLReportGenerator
            html_gen = HTMLReportGenerator()
            # If reportlab is not installed, output HTML file with .html extension
            fallback_path = target_path.with_suffix(".html")
            html_gen.generate(report, scan_data=scan_data, output_path=fallback_path)
            return fallback_path.read_bytes()

        return b""
