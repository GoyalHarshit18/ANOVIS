"""Screening endpoints: /screen, /predict, /batch-screen."""
import csv
import io
import json
import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.config import MAX_BATCH_SIZE
from app.schemas.input_schema import ComponentMeasurements, PredictRequest
from app.schemas.output_schema import UnifiedPredictionResponse
from app.services.screening_service import screen_component
from app.services.validation_service import validate_component, validate_csv_data
from app.services.ingestion_service import process_csv_upload
from app.services.model_manager import model_manager
from app.ml.prediction_engine import predict_168h
from app.ml.model_registry import registry
from app.db.session import get_db
from app.db.models import Lot, Component, Measurement, ScreeningResult, ScreeningRun

logger = logging.getLogger("sih26170.screening_api")

router = APIRouter(tags=["screening"])

def _save_screening_result(db: Session, measurements: dict, result: dict, run_id: str = None, commit: bool = True):
    lot_id = measurements.get("lot_id", "LOT-2026-091")
    comp_id = measurements.get("component_id", "UNKNOWN")
    
    lot = db.query(Lot).filter(Lot.lot_id == lot_id).first()
    if not lot:
        lot = Lot(lot_id=lot_id)
        db.add(lot)
        db.flush()

    comp = db.query(Component).filter(Component.component_id == comp_id).first()
    if not comp:
        comp = Component(
            component_id=comp_id,
            device_type=measurements.get("device_type"),
            lot_id=lot_id,
            station_id=measurements.get("station"),
        )
        db.add(comp)
        db.flush()
        
    for chk in [0, 24, 96, 168]:
        chk_str = f"{chk}h"
        v_iddq = measurements.get(f"Iddq_uA_{chk_str}")
        if v_iddq is None: v_iddq = measurements.get(f"iddq_ua_{chk_str}")
        
        v_leak = measurements.get(f"Leakage_nA_{chk_str}")
        if v_leak is None: v_leak = measurements.get(f"leakage_na_{chk_str}")
        
        v_prop = measurements.get(f"PropDelay_ns_{chk_str}")
        if v_prop is None: v_prop = measurements.get(f"prop_delay_ns_{chk_str}")
        
        def safe_float(val):
            if val is None or str(val).strip() == "": return None
            try: return float(val)
            except ValueError: return None

        if safe_float(v_iddq) is not None or safe_float(v_leak) is not None or safe_float(v_prop) is not None:
            meas = Measurement(
                run_id=run_id,
                component_id=comp_id,
                checkpoint_hour=chk,
                temperature=measurements.get("temperature"),
                voltage=measurements.get("voltage"),
                iddq_ua=safe_float(v_iddq),
                leakage_na=safe_float(v_leak),
                prop_delay_ns=safe_float(v_prop),
            )
            db.add(meas)

    evidence_data = result.get("evidence", {})
    if not isinstance(evidence_data, dict):
        evidence_data = {}
        
    evidence_data.update({
        "predicted_168h": result.get("predicted_168h"),
        "integrity_flag": result.get("test_integrity_flag", False),
        "test_integrity": result.get("test_integrity"),
        "basis": result.get("basis"),
        "history": result.get("history"),
        "b_models": result.get("b_models"),
        "shap": result.get("shap"),
        "warnings": result.get("warnings"),
        "explanation": result.get("explanation")
    })

    def _native_float(v):
        if v is None: return None
        return float(v)

    sr = ScreeningResult(
        run_id=run_id,
        component_id=comp_id,
        ldi=_native_float(result.get("ldi")),
        a_score=_native_float(result.get("a_score")),
        s_score=_native_float(result.get("s_score")),
        prediction_risk=_native_float(result.get("prediction_risk")),
        uncertainty_risk=_native_float(result.get("uncertainty_risk")),
        decision=result.get("decision"),
        stage=result.get("screening_stage"),
        integrity_status=result.get("test_integrity_flag", False),
        evidence=jsonable_encoder(evidence_data),
        warnings=jsonable_encoder(result.get("warnings", [])),
        model_version=result.get("model_version")
    )
    db.add(sr)
    if commit:
        db.commit()
    else:
        db.flush()

@router.post("/screen")
async def screen_single(payload: ComponentMeasurements, db: Session = Depends(get_db)):
    """Screen a single component through the full pipeline."""
    measurements = payload.model_dump()

    # Validate
    validation = validate_component(measurements)
    if not validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "component_id": measurements.get("component_id"),
                "details": validation,
            },
        )

    # Screen
    try:
        result = screen_component(measurements)
        _save_screening_result(db, measurements, result)
        return result
    except Exception as e:
        db.rollback()
        logger.error("Screening error for %s: %s", measurements.get("component_id"), e)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INFERENCE_ERROR",
                "message": str(e),
                "component_id": measurements.get("component_id"),
            },
        )


@router.post("/predict")
async def predict_only(payload: PredictRequest):
    """Prediction-only endpoint — predicted 168h values."""
    measurements = payload.model_dump()

    if not registry.get("b0_models"):
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "MODEL_UNAVAILABLE",
                "message": "B0 prediction models not loaded",
                "component_id": measurements.get("component_id"),
            },
        )

    try:
        result = predict_168h(measurements)
        # Add envelope
        envelope = registry.get("future_envelope")
        env_data = {}
        if envelope:
            for key, val in envelope.items():
                param = key.replace("_168h", "")
                env_data[param] = {
                    "lower": round(val["lower"], 4),
                    "upper": round(val["upper"], 4),
                }

        return {
            "component_id": measurements["component_id"],
            "predicted_168h": result["predicted_168h"],
            "envelope": env_data,
            "model_used": result.get("model_used", "B0"),
            "model_version": result.get("model_version", "b0-baseline-v1.0"),
            "stage": "24h",
            "warnings": result.get("warnings", []),
            "available": result.get("available", False),
        }
    except Exception as e:
        logger.error("Prediction error: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INFERENCE_ERROR",
                "message": str(e),
                "component_id": measurements.get("component_id"),
            },
        )


@router.post("/api/predict", response_model=UnifiedPredictionResponse)
async def unified_predict(payload: ComponentMeasurements):
    """
    Production unified prediction endpoint.
    Returns 96h anomaly probability, status, and 168h parameter predictions (IDDQ, Leakage, Delay).
    """
    measurements = payload.model_dump()
    comp_id = measurements.get("component_id", "UNKNOWN")
    lot_id = measurements.get("lot_id") or measurements.get("lot") or "LOT-UNKNOWN"

    try:
        # 1. 96h CatBoost Anomaly Detection
        anom_res = model_manager.predict_anomaly(measurements)
        prob = float(anom_res.get("anomaly_probability", 0.0))
        status_val = anom_res.get("predicted_status", "NORMAL")

        # 2. 168h B-Series Regression
        pred_res = model_manager.predict_168h(measurements)
        preds_168 = pred_res.get("predicted_168h", {}) if pred_res.get("available") else {}

        return UnifiedPredictionResponse(
            component_id=comp_id,
            lot_id=lot_id,
            anomaly_probability_96h=round(prob, 4),
            anomaly_status_96h=status_val,
            predicted_iddq_168h=preds_168.get("Iddq_uA"),
            predicted_leakage_168h=preds_168.get("Leakage_nA"),
            predicted_delay_168h=preds_168.get("PropDelay_ns"),
            threshold=float(anom_res.get("threshold", 0.50)),
            model_version=anom_res.get("model_version", "catboost-96h-v1.0")
        )
    except Exception as e:
        logger.error("Unified prediction error for %s: %s", comp_id, e)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INFERENCE_ERROR",
                "message": str(e),
                "component_id": comp_id,
            }
        )



@router.post("/upload")
def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Phase 2: Strict CSV ingestion and validation."""
    content = file.file.read()
    filename = file.filename
    
    result = process_csv_upload(content, filename, db)
    
    if "error" in result:
        status_code = result.pop("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result)
        
    return JSONResponse(status_code=200, content=result)


@router.post("/batch-screen")
def batch_screen(file: UploadFile = File(None), records: str = None, db: Session = Depends(get_db)):
    """
    Batch screen from CSV/JSON upload or inline records.
    """
    all_records: List[Dict[str, Any]] = []

    if file is not None:
        content = file.file.read()
        filename = file.filename or "upload"
        try:
            if filename.lower().endswith(".json"):
                data = json.loads(content.decode("utf-8"))
                if isinstance(data, list):
                    all_records = data
                elif isinstance(data, dict) and "records" in data:
                    all_records = data["records"]
                elif isinstance(data, dict):
                    all_records = [data]
                else:
                    raise HTTPException(status_code=422, detail={"error_code": "INVALID_FORMAT", "message": "JSON must be a list, {records: [...]}, or a single object"})
            elif filename.lower().endswith(".csv"):
                text = content.decode("utf-8")
                reader = csv.DictReader(io.StringIO(text))
                for row in reader:
                    record = {}
                    for key, val in row.items():
                        key = key.strip()
                        if val and val.strip():
                            try:
                                record[key] = float(val.strip())
                            except ValueError:
                                record[key] = val.strip()
                        else:
                            record[key] = None
                    all_records.append(record)
            else:
                text = content.decode("utf-8").strip()
                if text.startswith("[") or text.startswith("{"):
                    data = json.loads(text)
                    all_records = data if isinstance(data, list) else data.get("records", [data])
                else:
                    reader = csv.DictReader(io.StringIO(text))
                    for row in reader:
                        record = {}
                        for key, val in row.items():
                            key = key.strip()
                            if val and val.strip():
                                try:
                                    record[key] = float(val.strip())
                                except ValueError:
                                    record[key] = val.strip()
                            else:
                                record[key] = None
                        all_records.append(record)
        except Exception as e:
            raise HTTPException(status_code=422, detail={"error_code": "FILE_PARSE_ERROR", "message": str(e)})

    if not all_records:
        raise HTTPException(status_code=422, detail={"error_code": "EMPTY_DATASET", "message": "No records provided"})

    key_mapping = {
        "iddq_ua_0h": "Iddq_uA_0h",
        "iddq_ua_24h": "Iddq_uA_24h",
        "iddq_ua_96h": "Iddq_uA_96h",
        "iddq_ua_168h": "Iddq_uA_168h",
        "leakage_na_0h": "Leakage_nA_0h",
        "leakage_na_24h": "Leakage_nA_24h",
        "leakage_na_96h": "Leakage_nA_96h",
        "leakage_na_168h": "Leakage_nA_168h",
        "prop_delay_ns_0h": "PropDelay_ns_0h",
        "prop_delay_ns_24h": "PropDelay_ns_24h",
        "prop_delay_ns_96h": "PropDelay_ns_96h",
        "prop_delay_ns_168h": "PropDelay_ns_168h",
        "propdelay_0h": "PropDelay_ns_0h",
        "propdelay_24h": "PropDelay_ns_24h",
        "propdelay_96h": "PropDelay_ns_96h",
        "propdelay_168h": "PropDelay_ns_168h",
    }
    
    mapped_records = []
    for r in all_records:
        mapped = {}
        for k, v in r.items():
            mapped_key = key_mapping.get(k.lower(), k)
            mapped[mapped_key] = v
        mapped_records.append(mapped)
    all_records = mapped_records

    if len(all_records) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=422, detail={"error_code": "BATCH_TOO_LARGE", "message": f"Max batch size is {MAX_BATCH_SIZE}"})

    validation = validate_csv_data(all_records)

    results = []
    summary = {
        "pass": 0, "monitor": 0, "review": 0, "reject": 0,
        "repeat_measurement": 0, "data_unavailable": 0,
    }

    run_id = str(uuid.uuid4())
    run_record = ScreeningRun(run_id=run_id, component_count=len(all_records))
    db.add(run_record)
    db.commit()

    for record in all_records:
        if not record.get("component_id"):
            record["component_id"] = f"ROW-{all_records.index(record)+1}"

        try:
            result = screen_component(record)
            results.append(result)

            decision = result.get("decision", "DATA_UNAVAILABLE").upper()
            if decision == "PASS": summary["pass"] += 1
            elif decision == "MONITOR": summary["monitor"] += 1
            elif decision == "REVIEW_REQUIRED": summary["review"] += 1
            elif decision == "REJECT": summary["reject"] += 1
            elif decision == "REPEAT_MEASUREMENT": summary["repeat_measurement"] += 1
            else: summary["data_unavailable"] += 1

            _save_screening_result(db, record, result, run_id=run_id, commit=False)
        except Exception as e:
            db.rollback()
            logger.error("Batch screening error for %s: %s", record.get("component_id"), e)
            results.append({
                "component_id": record.get("component_id", "UNKNOWN"),
                "decision": "DATA_UNAVAILABLE",
                "warnings": [str(e)],
                "explanation": f"Screening error: {e}",
            })
            summary["data_unavailable"] += 1

    run_record.pass_count = summary["pass"]
    run_record.monitor_count = summary["monitor"]
    run_record.review_count = summary["review"]
    run_record.reject_count = summary["reject"]
    run_record.repeat_measurement_count = summary["repeat_measurement"]
    run_record.data_unavailable_count = summary["data_unavailable"]
    db.commit()

    return {
        "summary": summary,
        "results": results,
        "validation": validation,
    }


@router.post("/screening-runs/{run_id}/module-a")
def execute_module_a(run_id: str, db: Session = Depends(get_db)):
    """Phase 3: Execute Module A for a specific screening run."""
    from app.services.module_a_service import run_module_a_for_run
    
    try:
        result = run_module_a_for_run(run_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Module A execution failed for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "MODULE_A_EXECUTION_FAILED", "message": str(e)})

@router.post("/screening-runs/{run_id}/anomaly-analysis")
def execute_anomaly_analysis(run_id: str, db: Session = Depends(get_db)):
    """Phase 4: Execute Device, Lot, and Station Anomaly Analysis."""
    from app.services.anomaly_analysis_service import run_anomaly_analysis_for_run
    
    # Verify run exists
    run = db.query(ScreeningRun).filter_by(run_id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    try:
        result = run_anomaly_analysis_for_run(run_id, db)
        return result
    except Exception as e:
        logger.error(f"Anomaly analysis failed for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "ANOMALY_ANALYSIS_FAILED", "message": str(e)})

@router.post("/screening-runs/{run_id}/module-b")
def execute_module_b(run_id: str, db: Session = Depends(get_db)):
    """Phase 5: Execute Module B predictive modeling."""
    from app.services.module_b_service import run_module_b_for_run
    
    # Verify run exists
    run = db.query(ScreeningRun).filter_by(run_id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    try:
        result = run_module_b_for_run(run_id, db)
        return result
    except Exception as e:
        logger.error(f"Module B execution failed for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "MODULE_B_EXECUTION_FAILED", "message": str(e)})

@router.post("/screening-runs/{run_id}/risk-fusion")
def execute_risk_fusion(run_id: str, db: Session = Depends(get_db)):
    """Phase 6: Execute Risk Fusion Engine."""
    from app.services.risk_fusion_service import run_risk_fusion_for_run
    from app.db.models import RiskFusionResult
    
    # Verify run exists
    run = db.query(ScreeningRun).filter_by(run_id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    try:
        summary = run_risk_fusion_for_run(run_id, db)
        results_db = db.query(RiskFusionResult).filter_by(run_id=run_id).all()
        summary["results"] = [
            {
                "run_id": r.run_id,
                "component_id": r.component_id,
                "a_score": r.a_score,
                "s_score": r.s_score,
                "prediction_risk": r.prediction_risk,
                "uncertainty_risk": r.uncertainty_risk,
                "ldi": r.ldi,
                "fusion_score": r.fusion_score,
                "final_decision": r.final_decision,
                "decision_basis": r.decision_basis,
                "model_version": r.model_version
            } for r in results_db
        ]
        return summary
    except Exception as e:
        logger.error(f"Risk fusion failed for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": "RISK_FUSION_FAILED", "message": str(e)})
