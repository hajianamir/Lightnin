import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from aegislps_domain.models import Project, SeparationCalculationResult

class ReportRenderer:
    @staticmethod
    def render_pdf_report(project: Project, results: list[SeparationCalculationResult]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        story = []

        # Title Block
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#1E3A8A'))
        story.append(Paragraph("AegisLPS - Separation Distance Calculation Report", title_style))
        story.append(Paragraph("<b>Status:</b> AegisLPS Engineering Prototype - Unverified Standards Data", styles['Normal']))
        story.append(Spacer(1, 12))

        # Project Info
        info_data = [
            ["Project Name:", project.name, "LPS Class:", f"Class {project.lps_class}"],
            ["Building Size:", f"{project.building.length_m}m x {project.building.width_m}m x {project.building.height_m}m", "Standard Baseline:", "IEC 62305-3:2024"]
        ]
        t_info = Table(info_data, colWidths=[100, 180, 100, 150])
        t_info.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#111827')),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 16))

        # Warning
        warning_style = ParagraphStyle('WarnStyle', parent=styles['Normal'], textColor=colors.HexColor('#B91C1C'), fontSize=9)
        story.append(Paragraph("<b>WARNING:</b> Standards parameters represent unverified prototype baseline values and require independent engineering verification against licensed standards.", warning_style))
        story.append(Spacer(1, 12))

        # Results Table
        story.append(Paragraph("<b>Separation Distance Assessment Results:</b>", styles['Heading2']))

        table_data = [["Point ID", "Medium", "Req. Distance (s)", "Actual Dist.", "Margin", "Status"]]
        for r in results:
            status_str = "PASS" if r.pass_compliance else "FAIL"
            table_data.append([
                r.separation_point_id[:8],
                f"Medium ({r.km_used})",
                f"{r.required_distance_s_m:.3f} m",
                f"{r.actual_distance_m:.3f} m",
                f"{r.safety_margin_m:+.3f} m",
                status_str
            ])

        t_results = Table(table_data, colWidths=[80, 80, 110, 90, 90, 80])
        t_results.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
            ('ALIGN', (2,1), (-1,-1), 'CENTER'),
        ]))
        story.append(t_results)
        story.append(Spacer(1, 16))

        # Step Trace
        story.append(Paragraph("<b>Calculation Trace Details:</b>", styles['Heading3']))
        for r in results:
            story.append(Paragraph(f"• <b>{r.separation_point_id[:8]}:</b> {r.formula_trace}", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
