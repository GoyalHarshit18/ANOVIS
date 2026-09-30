import io
import csv
import logging
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models import ScreeningRun, Component, ScreeningResult
from fpdf import FPDF

logger = logging.getLogger("sih26170.export_api")

router = APIRouter(tags=["export"])

def _get_run_data(run_id: str, db: Session):
    run = db.query(ScreeningRun).filter_by(run_id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    results = db.query(ScreeningResult, Component).join(Component).filter(ScreeningResult.run_id == run_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="No component results found for this run")
        
    return run, results

@router.get("/screening-runs/{run_id}/export/csv")
async def export_csv(run_id: str, db: Session = Depends(get_db)):
    run, results = _get_run_data(run_id, db)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "run_id", "lot_id", "component_id", "device_type", "station_id",
        "A_SCORE", "PAT", "Peer", "Temporal", "IF",
        "device_anomaly", "lot_anomaly", "station_anomaly",
        "B0_Iddq", "B1_Iddq", "B2_Early_Iddq", "B2_96h_Iddq",
        "B0_Leakage", "B1_Leakage", "B2_Early_Leakage", "B2_96h_Leakage",
        "B0_Delay", "B1_Delay", "B2_Early_Delay", "B2_96h_Delay",
        "prediction_risk", "uncertainty_risk", "s_score", "ldi", "fusion_score",
        "final_decision", "decision_basis", "model_version"
    ]
    writer.writerow(headers)
    
    for r, c in results:
        def render_val(val):
            return "" if val is None else str(val)
        
        # Parse Module A evidence
        ev = r.evidence or {}
        mod_a = ev.get("module_a", {})
        pat = mod_a.get("pat_score")
        peer = mod_a.get("peer_residual")
        temp = mod_a.get("early_temporal")
        iforest = mod_a.get("isolation_forest")
        
        # Parse anomalies
        anom = ev.get("anomalies", {})
        device_anom = anom.get("device_anomaly")
        lot_anom = anom.get("lot_anomaly")
        station_anom = anom.get("station_anomaly")
        
        # Parse predictions (B models)
        b_models = ev.get("b_models", {})
        
        def get_pred(model_key, param):
            m = b_models.get(model_key)
            if not m or not m.get("available") or m.get("prediction") is None:
                return None
            # The current backend model only predicts Leakage in some stages, but let's just return prediction if it matches param
            # Actually, standardizing: prediction applies to leakage in most cases. If we have specifics, we use them.
            # Currently backend returns scalar 'prediction' under B models for leakage usually.
            if param == "Leakage": return m.get("prediction")
            return None
        
        writer.writerow([
            r.run_id, c.lot_id, r.component_id, c.device_type, c.station_id,
            render_val(r.a_score), render_val(pat), render_val(peer), render_val(temp), render_val(iforest),
            render_val(device_anom), render_val(lot_anom), render_val(station_anom),
            render_val(get_pred("B0", "Iddq")), render_val(get_pred("B1", "Iddq")), render_val(get_pred("B2-Early", "Iddq")), render_val(get_pred("B2-96h", "Iddq")),
            render_val(get_pred("B0", "Leakage")), render_val(get_pred("B1", "Leakage")), render_val(get_pred("B2-Early", "Leakage")), render_val(get_pred("B2-96h", "Leakage")),
            render_val(get_pred("B0", "Delay")), render_val(get_pred("B1", "Delay")), render_val(get_pred("B2-Early", "Delay")), render_val(get_pred("B2-96h", "Delay")),
            render_val(r.prediction_risk), render_val(r.uncertainty_risk), render_val(r.s_score), render_val(r.ldi), render_val(r.ldi),
            r.decision, ev.get("basis", {}).get("mode", "Unknown"), r.model_version
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=QA_Report_{run_id}.csv"}
    )

class QAPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(10, 20, 60)
        self.cell(0, 10, 'Anovis Engineering QA Report', 0, 1, 'C')
        self.set_draw_color(10, 20, 60)
        self.line(10, 22, 200, 22)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

@router.get("/screening-runs/{run_id}/export/pdf")
async def export_pdf(run_id: str, db: Session = Depends(get_db)):
    run, results = _get_run_data(run_id, db)
    
    pdf = QAPDF()
    pdf.add_page()
    
    # PAGE 1: Executive QA Summary
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Executive QA Summary', 0, 1)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f'Screening Run ID: {run.run_id}', 0, 1)
    pdf.cell(0, 8, f'Timestamp: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC', 0, 1)
    
    total_components = len(results)
    decisions = {"PASS": 0, "MONITOR": 0, "REVIEW_REQUIRED": 0, "REJECT": 0, "REPEAT_MEASUREMENT": 0}
    for r, _ in results:
        dec = r.decision if r.decision else "DATA_UNAVAILABLE"
        decisions[dec] = decisions.get(dec, 0) + 1
        
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, f'Total Components: {total_components}', 0, 1)
    for k, v in decisions.items():
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'- {k}: {v}', 0, 1)
        
    # Following pages per component (compact)
    for r, c in results:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f'Component Evidence: {r.component_id}', 0, 1)
        
        def render_val(val):
            return "UNAVAILABLE" if val is None else str(val)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'Lot ID: {render_val(c.lot_id)}', 0, 1)
        pdf.cell(0, 6, f'Device Type: {render_val(c.device_type)}', 0, 1)
        pdf.cell(0, 6, f'Station ID: {render_val(c.station_id)}', 0, 1)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, 'Anomaly Analysis', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'A_SCORE: {render_val(r.a_score)}', 0, 1)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, 'Predictive & Safety', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'Prediction Risk: {render_val(r.prediction_risk)}', 0, 1)
        pdf.cell(0, 6, f'Uncertainty Risk: {render_val(r.uncertainty_risk)}', 0, 1)
        pdf.cell(0, 6, f'S_SCORE: {render_val(r.s_score)}', 0, 1)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, 'Risk Fusion & Final Decision', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'LDI: {render_val(r.ldi)}', 0, 1)
        pdf.cell(0, 6, f'Final Decision: {render_val(r.decision)}', 0, 1)
        pdf.cell(0, 6, f'Model Version: {render_val(r.model_version)}', 0, 1)
        
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 6, 'Decision Basis:', 0, 1)
        pdf.set_font('Arial', '', 9)
        basis = r.evidence.get("basis", {}).get("mode", "Unknown") if r.evidence else "Unknown"
        pdf.multi_cell(0, 5, render_val(basis))

    # Output
    try:
        pdf_bytes = bytes(pdf.output(dest='S'))
    except TypeError:
        pdf_bytes = pdf.output(dest='S').encode('latin1')
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=QA_Report_{run_id}.pdf"}
    )
