"""
Professional PDF Report Generation Service for QA Inspector Reports.
Uses ReportLab to build high-quality printable PDF documents.
"""
import io
import time
import logging
from typing import Any, Dict, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

logger = logging.getLogger("sih26170.pdf_service")


def generate_qa_report_pdf(
    explanation: Dict[str, Any],
    gemini_report: Dict[str, Any],
    predictions_168h: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Generates a professional PDF report for semiconductor burn-in screening & QA inspection.
    Returns the PDF as raw bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY_COLOR = colors.HexColor("#0F172A") # Dark slate
    SECONDARY_COLOR = colors.HexColor("#2563EB") # Royal Blue
    ACCENT_RED = colors.HexColor("#DC2626") # Anomaly Red
    ACCENT_GREEN = colors.HexColor("#16A34A") # Normal Green
    BG_LIGHT = colors.HexColor("#F8FAFC")
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=PRIMARY_COLOR,
        fontName="Helvetica-Bold",
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#64748B"),
        fontName="Helvetica-Bold",
        spaceAfter=12
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=14,
        textColor=SECONDARY_COLOR,
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=PRIMARY_COLOR,
        fontName="Helvetica"
    )

    bold_body_style = ParagraphStyle(
        "BodyDarkBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    caption_style = ParagraphStyle(
        "CaptionStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748B"),
        fontName="Helvetica-Oblique"
    )

    story = []

    comp_id = explanation.get("component_id", "UNKNOWN")
    lot_id = explanation.get("lot_id", "LOT-UNKNOWN")
    report_id = f"RPT-{comp_id}-{int(time.time())}"
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    status = explanation.get("predicted_status", "NORMAL")
    prob = explanation.get("anomaly_probability", 0.0)

    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------
    story.append(Paragraph("Anovis — AI-Assisted QA Inspection Report", title_style))
    story.append(Paragraph(f"REPORT ID: {report_id}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY_COLOR, spaceAfter=10))

    # Meta Table
    meta_data = [
        [
            Paragraph("<b>Component ID:</b>", body_style), Paragraph(comp_id, bold_body_style),
            Paragraph("<b>Lot ID:</b>", body_style), Paragraph(lot_id, body_style),
        ],
        [
            Paragraph("<b>Generated Date:</b>", body_style), Paragraph(timestamp_str, body_style),
            Paragraph("<b>Model Version:</b>", body_style), Paragraph(explanation.get("model_version", "catboost-96h-v1.0"), body_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 1: CLASSIFICATION RESULT
    # -------------------------------------------------------------------------
    story.append(Paragraph("Section 1: 96h Anomaly Classification Result", section_heading))
    
    status_color = ACCENT_RED if status == "ANOMALY" else ACCENT_GREEN
    status_text = f"<font color='{status_color.hexval()}'><b>{status}</b></font>"

    result_data = [
        [
            Paragraph("<b>Predicted Status:</b>", body_style), Paragraph(status_text, body_style),
            Paragraph("<b>Anomaly Probability:</b>", body_style), Paragraph(f"<b>{prob*100:.2f}%</b>", body_style),
        ],
        [
            Paragraph("<b>Classification Threshold:</b>", body_style), Paragraph(f"{explanation.get('threshold', 0.5)*100:.0f}%", body_style),
            Paragraph("<b>Human Review Disposition:</b>", body_style), Paragraph("PENDING QA INSPECTOR SIGN-OFF", body_style),
        ]
    ]
    result_table = Table(result_data, colWidths=[1.5*inch, 2.0*inch, 1.6*inch, 1.9*inch])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 2: MEASUREMENT SUMMARY
    # -------------------------------------------------------------------------
    story.append(Paragraph("Section 2: Observed Sensor Measurements vs Limits", section_heading))
    
    meas_headers = [Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>0h</b>", body_style), Paragraph("<b>24h</b>", body_style), Paragraph("<b>96h</b>", body_style), Paragraph("<b>Upper Limit</b>", body_style), Paragraph("<b>Limit Status</b>", body_style)]
    meas_rows = [meas_headers]

    limits_info = explanation.get("limit_analysis", {})
    assessments = {a["key"]: a for a in limits_info.get("assessments", [])}

    for param in ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]:
        v0 = assessments.get(f"{param}_0h", {}).get("value", "N/A")
        v24 = assessments.get(f"{param}_24h", {}).get("value", "N/A")
        a96 = assessments.get(f"{param}_96h", {})
        v96 = a96.get("value", "N/A")
        upper = a96.get("upper_limit", "N/A")
        st = a96.get("status", "WITHIN_LIMIT")
        
        st_text = f"<font color='red'>EXCEEDED</font>" if st == "EXCEEDED" else "<font color='green'>OK</font>"

        meas_rows.append([
            Paragraph(param, body_style),
            Paragraph(str(v0), body_style),
            Paragraph(str(v24), body_style),
            Paragraph(str(v96), body_style),
            Paragraph(str(upper), body_style),
            Paragraph(st_text, body_style)
        ])

    meas_table = Table(meas_rows, colWidths=[1.5*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.2*inch, 1.3*inch])
    meas_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(meas_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 3: SHAP EXPLAINABILITY BREAKDOWN
    # -------------------------------------------------------------------------
    story.append(Paragraph("Section 3: Top Feature Attributions (SHAP Explanation)", section_heading))
    story.append(Paragraph("SHAP baseline value: <b>{:.4f}</b> | Output Unit: Probability Attribution".format(explanation.get("base_value", 0.5)), caption_style))
    story.append(Spacer(1, 4))

    shap_headers = [Paragraph("<b>Feature Name</b>", body_style), Paragraph("<b>Actual Value</b>", body_style), Paragraph("<b>SHAP Value</b>", body_style), Paragraph("<b>Risk Evidence Effect</b>", body_style)]
    shap_rows = [shap_headers]

    top_overall = explanation.get("top_overall_contributors", [])[:6]
    for item in top_overall:
        s_val = item["shap_value"]
        effect = item["effect"]
        eff_color = "red" if s_val > 0 else "green"
        eff_label = "Increases Risk (+)" if s_val > 0 else "Decreases Risk (-)"
        
        shap_rows.append([
            Paragraph(item["feature"], body_style),
            Paragraph(str(item["actual_value"] if item["actual_value"] is not None else "N/A"), body_style),
            Paragraph(f"{s_val:+.6f}", body_style),
            Paragraph(f"<font color='{eff_color}'>{eff_label}</font>", body_style)
        ])

    shap_table = Table(shap_rows, colWidths=[2.2*inch, 1.3*inch, 1.3*inch, 2.2*inch])
    shap_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(shap_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 4: AI-GENERATED NARRATIVE REPORT (GEMINI)
    # -------------------------------------------------------------------------
    story.append(Paragraph("Section 4: AI-Assisted QA Inspection Findings (Gemini Grounded Analysis)", section_heading))
    
    exec_text = gemini_report.get("executive_summary", "")
    class_text = gemini_report.get("classification_explanation", "")
    limit_text = gemini_report.get("engineering_limit_assessment", "")
    trends_text = gemini_report.get("measurement_trends", "")
    limitation_text = gemini_report.get("limitations", "")

    story.append(Paragraph("<b>Executive Summary:</b>", bold_body_style))
    story.append(Paragraph(exec_text, body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Classification Narrative:</b>", bold_body_style))
    story.append(Paragraph(class_text, body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Engineering Limit Assessment:</b>", bold_body_style))
    story.append(Paragraph(limit_text, body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Recommended QA Verification Steps:</b>", bold_body_style))
    steps = gemini_report.get("recommended_inspection_steps", [])
    for idx, step in enumerate(steps, 1):
        story.append(Paragraph(f"• {step}", body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Model Limitations:</b>", bold_body_style))
    story.append(Paragraph(limitation_text, caption_style))
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 5: 168h PREDICTIVE ANALYTICS (IF AVAILABLE)
    # -------------------------------------------------------------------------
    if predictions_168h and predictions_168h.get("predicted_168h"):
        story.append(Paragraph("Section 5: Predictive Analytics (Predicted 168h Measurements)", section_heading))
        pred_dict = predictions_168h["predicted_168h"]
        
        pred_rows = [
            [Paragraph("<b>Predicted Parameter (168h)</b>", body_style), Paragraph("<b>Predicted Value</b>", body_style), Paragraph("<b>Unit</b>", body_style)],
            [Paragraph("IDDQ at 168h", body_style), Paragraph(str(pred_dict.get("Iddq_uA", "N/A")), body_style), Paragraph("µA", body_style)],
            [Paragraph("Leakage at 168h", body_style), Paragraph(str(pred_dict.get("Leakage_nA", "N/A")), body_style), Paragraph("nA", body_style)],
            [Paragraph("Propagation Delay at 168h", body_style), Paragraph(str(pred_dict.get("PropDelay_ns", "N/A")), body_style), Paragraph("ns", body_style)],
        ]
        pred_table = Table(pred_rows, colWidths=[3.0*inch, 2.0*inch, 2.0*inch])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(pred_table)
        story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 6: INSPECTOR REVIEW & SIGN-OFF BLOCK
    # -------------------------------------------------------------------------
    story.append(Paragraph("Section 6: QA Inspector Review & Approval", section_heading))
    
    sign_data = [
        [Paragraph("<b>Inspector Name:</b>", body_style), Paragraph("___________________________", body_style), Paragraph("<b>Inspection Date:</b>", body_style), Paragraph("____ / ____ / 2026", body_style)],
        [Paragraph("<b>Disposition Decision:</b>", body_style), Paragraph("[  ] APPROVED   [  ] REJECTED   [  ] RE-TEST", body_style), Paragraph("<b>Inspector Signature:</b>", body_style), Paragraph("___________________________", body_style)],
        [Paragraph("<b>Inspector Comments:</b>", body_style), Paragraph("__________________________________________________________________________", body_style), "", ""]
    ]
    sign_table = Table(sign_data, colWidths=[1.5*inch, 2.2*inch, 1.5*inch, 1.8*inch])
    sign_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('SPAN', (1,2), (3,2)),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sign_table)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # FOOTER DISCLAIMER
    # -------------------------------------------------------------------------
    footer_text = (
        "AI-generated explanations support quality inspection and do not independently establish a physical defect cause. "
        "Final disposition requires authorized QA review."
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=6))
    story.append(Paragraph(footer_text, caption_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
