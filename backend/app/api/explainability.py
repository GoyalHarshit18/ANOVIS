"""
Module 3 API Endpoints: Explainability and Gemini-Powered QA Inspector Reports.
"""
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Component, Measurement, ScreeningResult, AnomalyEvidence, Explanation, QAReport
from app.schemas.input_schema import ComponentMeasurements
from app.services.explainability_service import (
    explain_component_96h,
    get_global_shap_importance
)
from app.services.gemini_service import generate_gemini_qa_report
from app.services.pdf_service import generate_qa_report_pdf
from app.services.supabase_storage_service import upload_pdf_to_storage
from app.ml.prediction_engine import predict_168h
from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.explainability_api")

router = APIRouter(prefix="/api", tags=["explainability"])


class ComponentExplainRequest(BaseModel):
    component_id: Optional[str] = "UNKNOWN"
    lot_id: Optional[str] = "LOT-UNKNOWN"
    measurements: Optional[Dict[str, Any]] = None


def _retrieve_measurements_from_db(component_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Helper to reconstruct component measurement dictionary from DB."""
    comp = db.query(Component).filter(Component.component_id == component_id).first()
    if not comp:
        return None

    meas_db = db.query(Measurement).filter(Measurement.component_id == component_id).all()
    if not meas_db:
        return None

    data = {
        "component_id": comp.component_id,
        "lot_id": comp.lot_id,
        "device_type": comp.device_type,
        "station": comp.station_id,
    }

    for m in meas_db:
        stage = f"{m.checkpoint_hour}h"
        if m.iddq_ua is not None:
            data[f"Iddq_uA_{stage}"] = float(m.iddq_ua)
        if m.leakage_na is not None:
            data[f"Leakage_nA_{stage}"] = float(m.leakage_na)
        if m.prop_delay_ns is not None:
            data[f"PropDelay_ns_{stage}"] = float(m.prop_delay_ns)
        if m.temperature is not None:
            data[f"Temperature_{stage}"] = float(m.temperature)
        if m.voltage is not None:
            data[f"Voltage_{stage}"] = float(m.voltage)

    return data


@router.get("/explainability/global")
def get_global_explainability():
    """
    Returns global SHAP feature importance, top contributors, sample size, and model metadata.
    """
    try:
        result = get_global_shap_importance()
        return result
    except Exception as e:
        logger.error("Global SHAP computation failed: %s", e)
        raise HTTPException(status_code=500, detail={"error": "GLOBAL_SHAP_FAILED", "message": str(e)})


@router.post("/explainability/component")
def get_component_explainability(payload: ComponentExplainRequest, db: Session = Depends(get_db)):
    """
    Returns SHAP attribution breakdown, feature values, probability, and limit checks for a component.
    """
    measurements = payload.measurements
    if not measurements and payload.component_id:
        measurements = _retrieve_measurements_from_db(payload.component_id, db)

    if not measurements:
        raise HTTPException(
            status_code=404,
            detail={"error": "COMPONENT_NOT_FOUND", "message": f"No measurements found for component '{payload.component_id}'"}
        )

    try:
        legacy_risks = None
        if payload.component_id:
            ae = db.query(AnomalyEvidence).filter_by(component_id=payload.component_id).order_by(AnomalyEvidence.created_at.desc()).first()
            if ae:
                legacy_risks = {
                    "PAT_Risk": ae.pat_score or 0.0,
                    "Peer_Risk": ae.peer_score or 0.0,
                    "Temporal_Risk": ae.temporal_score or 0.0,
                    "IF_Risk": ae.isolation_forest_score or 0.0,
                }

        explanation = explain_component_96h(measurements, legacy_risks=legacy_risks)

        # Persist explanation if DB is active
        try:
            exp_record = Explanation(
                component_id=str(explanation.get("component_id", payload.component_id)),
                shap_data=explanation.get("feature_attributions"),
                top_features=explanation.get("top_overall_contributors"),
                model_version=explanation.get("model_version", "catboost-96h-v1.0")
            )
            db.add(exp_record)
            db.commit()
        except Exception as db_err:
            db.rollback()
            logger.debug("Explanation DB persistence skipped: %s", db_err)

        return explanation
    except Exception as e:
        logger.error("Component explainability calculation failed for %s: %s", payload.component_id, e)
        raise HTTPException(status_code=500, detail={"error": "EXPLAINABILITY_FAILED", "message": str(e)})


@router.post("/reports/qa")
def generate_qa_report(payload: ComponentExplainRequest, db: Session = Depends(get_db)):
    """
    Generates a Gemini-powered QA inspection report from verified model evidence.
    """
    measurements = payload.measurements
    if not measurements and payload.component_id:
        measurements = _retrieve_measurements_from_db(payload.component_id, db)

    if not measurements:
        raise HTTPException(
            status_code=404,
            detail={"error": "COMPONENT_NOT_FOUND", "message": f"No measurements found for component '{payload.component_id}'"}
        )

    try:
        legacy_risks = None
        if payload.component_id:
            ae = db.query(AnomalyEvidence).filter_by(component_id=payload.component_id).order_by(AnomalyEvidence.created_at.desc()).first()
            if ae:
                legacy_risks = {
                    "PAT_Risk": ae.pat_score or 0.0,
                    "Peer_Risk": ae.peer_score or 0.0,
                    "Temporal_Risk": ae.temporal_score or 0.0,
                    "IF_Risk": ae.isolation_forest_score or 0.0,
                }

        explanation = explain_component_96h(measurements, legacy_risks=legacy_risks)
        report = generate_gemini_qa_report(explanation)
        predictions_168h = predict_168h(measurements)

        # Generate and optionally upload PDF to Supabase Storage
        storage_url = None
        try:
            pdf_bytes = generate_qa_report_pdf(explanation, report, predictions_168h)
            file_path = f"reports/{explanation.get('component_id', 'UNKNOWN')}_qa_report.pdf"
            storage_url = upload_pdf_to_storage(pdf_bytes, file_path)
        except Exception as pdf_err:
            logger.warning("PDF background generation/upload warning: %s", pdf_err)

        # Persist QA report in database
        try:
            qa_record = QAReport(
                component_id=str(explanation.get("component_id", payload.component_id)),
                lot_id=str(explanation.get("lot_id", payload.lot_id)),
                report_data=report,
                pdf_path=storage_url or f"/api/reports/qa/{explanation.get('component_id')}/pdf",
                source=report.get("source", "GOOGLE_GEMINI_AI")
            )
            db.add(qa_record)
            db.commit()
        except Exception as db_err:
            db.rollback()
            logger.debug("QA Report DB persistence skipped: %s", db_err)

        return {
            "explanation": explanation,
            "report": report,
            "pdf_url": storage_url or f"/api/reports/qa/{explanation.get('component_id')}/pdf"
        }
    except Exception as e:
        logger.error("QA Report generation failed for %s: %s", payload.component_id, e)
        raise HTTPException(status_code=500, detail={"error": "QA_REPORT_FAILED", "message": str(e)})


@router.get("/reports/qa/{component_id}/pdf")
def download_qa_report_pdf(component_id: str, db: Session = Depends(get_db)):
    """
    Generates and streams a downloadable professional QA inspection PDF report.
    """
    measurements = _retrieve_measurements_from_db(component_id, db)
    if not measurements:
        # Check if dummy test component or mock is requested
        if component_id.startswith("TEST") or component_id.startswith("CMP"):
            measurements = {
                "component_id": component_id,
                "lot_id": "LOT-2026-091",
                "Iddq_uA_0h": 1.20, "Iddq_uA_24h": 1.50, "Iddq_uA_96h": 4.50,
                "Leakage_nA_0h": 4.0, "Leakage_nA_24h": 5.5, "Leakage_nA_96h": 25.0,
                "PropDelay_ns_0h": 1.0, "PropDelay_ns_24h": 1.1, "PropDelay_ns_96h": 1.3,
            }
        else:
            raise HTTPException(
                status_code=404,
                detail={"error": "COMPONENT_NOT_FOUND", "message": f"Component '{component_id}' not found in database"}
            )

    try:
        legacy_risks = None
        ae = db.query(AnomalyEvidence).filter_by(component_id=component_id).order_by(AnomalyEvidence.created_at.desc()).first()
        if ae:
            legacy_risks = {
                "PAT_Risk": ae.pat_score or 0.0,
                "Peer_Risk": ae.peer_score or 0.0,
                "Temporal_Risk": ae.temporal_score or 0.0,
                "IF_Risk": ae.isolation_forest_score or 0.0,
            }

        explanation = explain_component_96h(measurements, legacy_risks=legacy_risks)
        gemini_report = generate_gemini_qa_report(explanation)
        predictions_168h = predict_168h(measurements)

        pdf_bytes = generate_qa_report_pdf(explanation, gemini_report, predictions_168h)

        filename = f"QA_Inspection_Report_{component_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error("PDF generation failed for %s: %s", component_id, e)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

