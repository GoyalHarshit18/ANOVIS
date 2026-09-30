"""Component and Lot endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.services.screening_service import screen_component
from app.ml.model_registry import registry
from app.db.session import get_db
from app.db.models import Component, ScreeningResult, Measurement, Prediction

logger = logging.getLogger("sih26170.component_api")

router = APIRouter(tags=["components"])


def store_result(result: dict):
    """Store a screening result for later retrieval (kept for legacy demo seed compat)."""
    # Note: DB persisting is mostly handled in screening routes now.
    pass


def format_predicted_168h(pred_raw):
    if not pred_raw:
        return None
    
    def get_val(key1, key2):
        val = pred_raw.get(key1)
        return val if val is not None else pred_raw.get(key2)

    return {
        "leakage": get_val("Leakage_nA", "Leakage_nA_168h"),
        "Iddq_uA": get_val("Iddq_uA", "Iddq_uA_168h"),
        "Leakage_nA": get_val("Leakage_nA", "Leakage_nA_168h"),
        "PropDelay_ns": get_val("PropDelay_ns", "PropDelay_ns_168h"),
        "interval": pred_raw.get("interval", []),
    }


@router.get("/components")
async def list_components(lot_id: str = None, db: Session = Depends(get_db)):
    """
    List all stored screening results with summary statistics.
    Used by the Dashboard to load seeded/screened data.
    """
    query = db.query(ScreeningResult, Component).join(Component)
    if lot_id:
        query = query.filter(Component.lot_id == lot_id)
    results_db = query.order_by(ScreeningResult.created_at.desc()).all()

    summary = {
        "pass": 0, "monitor": 0, "review": 0, "reject": 0,
        "repeat_measurement": 0, "data_unavailable": 0,
    }
    
    results = []
    
    for r, c in results_db:
        decision = r.decision.upper() if r.decision else "DATA_UNAVAILABLE"
        if decision == "PASS":
            summary["pass"] += 1
        elif decision == "MONITOR":
            summary["monitor"] += 1
        elif decision == "REVIEW_REQUIRED":
            summary["review"] += 1
        elif decision == "REJECT":
            summary["reject"] += 1
        elif decision == "REPEAT_MEASUREMENT":
            summary["repeat_measurement"] += 1
        else:
            summary["data_unavailable"] += 1
            
        ev = r.evidence or {}
        results.append({
            "component_id": r.component_id,
            "lot": c.lot_id,
            "device_type": c.device_type,
            "decision": r.decision,
            "a_score": r.a_score,
            "ldi": r.ldi,
            "prediction_risk": r.prediction_risk,
            "predicted_168h": format_predicted_168h(ev.get("predicted_168h")),
            "stage": r.stage,
            "test_integrity_flag": ev.get("integrity_flag", False),
            "evidence": r.evidence,
        })

    latest_run_id = results_db[0][0].run_id if results_db else None
    return {"summary": summary, "results": results, "latest_run_id": latest_run_id}


@router.get("/component/{component_id}")
async def get_component(component_id: str, db: Session = Depends(get_db)):
    """
    Get component screening result and history.
    Returns the latest screening result if available.
    """
    result_db = db.query(ScreeningResult).filter(ScreeningResult.component_id == component_id).order_by(ScreeningResult.created_at.desc()).first()
    comp_db = db.query(Component).filter(Component.component_id == component_id).first()
    
    if result_db and comp_db:
        # Reconstruct the expected dict
        ev = result_db.evidence or {}
        run_id = result_db.run_id
        
        measurements = db.query(Measurement).filter_by(run_id=run_id, component_id=component_id).all()
        history = []
        meas_dict = {}
        for m in measurements:
            chk = f"{m.checkpoint_hour}h"
            if m.iddq_ua is not None:
                history.append({"stage": chk, "value": round(float(m.iddq_ua), 4), "parameter": "Iddq_uA"})
                meas_dict[f"Iddq_uA_{chk}"] = m.iddq_ua
            if m.leakage_na is not None:
                history.append({"stage": chk, "value": round(float(m.leakage_na), 4), "parameter": "Leakage_nA"})
                meas_dict[f"Leakage_nA_{chk}"] = m.leakage_na
            if m.prop_delay_ns is not None:
                history.append({"stage": chk, "value": round(float(m.prop_delay_ns), 4), "parameter": "PropDelay_ns"})
                meas_dict[f"PropDelay_ns_{chk}"] = m.prop_delay_ns
                
        from app.db.models import SafetyEnvelope, PredictionInterval

        predictions_db = db.query(Prediction).filter(
            Prediction.run_id == run_id,
            Prediction.component_id == component_id
        ).all()
        
        pred_map = {p.model_name: p for p in predictions_db}
        b_models = {}
        expected_models = [
            ("B0", "0h"),
            ("B1", "24h"),
            ("B2-Early", "24h"),
            ("B2-96h", "96h")
        ]
        
        for m_name, exp_stage in expected_models:
            if m_name in pred_map:
                p = pred_map[m_name]
                b_models[m_name] = {
                    "prediction": p.predicted_168h,
                    "stage": p.prediction_stage,
                    "available": p.available,
                    "status": p.status,
                    "model_version": p.model_version
                }
            else:
                b_models[m_name] = {
                    "prediction": None,
                    "stage": exp_stage,
                    "available": False,
                    "status": "UNAVAILABLE",
                    "model_version": None
                }
                
        selected_p = None
        for m_name, _ in reversed(expected_models):
            if m_name in pred_map and pred_map[m_name].available:
                selected_p = pred_map[m_name]
                break
                
        basis_ev = ev.get("basis") if isinstance(ev.get("basis"), dict) else {}
        
        intervals_db = []
        if selected_p:
            intervals_db = db.query(PredictionInterval).filter_by(prediction_id=selected_p.id).all()
            
        pred_intervals = {}
        is_calibrated = False
        for inv in intervals_db:
            if inv.calibrated:
                is_calibrated = True
            pred_intervals[inv.parameter] = {
                "lower": inv.lower,
                "upper": inv.upper,
                "calibrated": inv.calibrated
            }
            
        basis = {
            "mode": basis_ev.get("mode"),
            "b_model": selected_p.model_name if selected_p else None,
            "safety_score_calibrated": is_calibrated,
            "safety_score_type": basis_ev.get("safety_score_type"),
            "calibrated_probability_available": is_calibrated
        }
        model_version = selected_p.model_version if selected_p else None
        
        safety_envelopes = db.query(SafetyEnvelope).filter_by(run_id=run_id, component_id=component_id).all()
        formatted_pred = format_predicted_168h(ev.get("predicted_168h"))
        details = {}
        
        has_any_envelope = len(safety_envelopes) > 0
        
        for param in ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]:
            details[param] = {"status": "UNAVAILABLE"}
            if formatted_pred and formatted_pred.get(param) is not None:
                details[param]["predicted_168h"] = formatted_pred[param]
                
        for env in safety_envelopes:
            if env.parameter in details:
                details[env.parameter]["engineering_limit_upper"] = env.upper
                details[env.parameter]["engineering_limit_lower"] = env.lower
                val = details[env.parameter].get("predicted_168h")
                if val is not None and env.upper is not None:
                    details[env.parameter]["status"] = "EXCEEDS_LIMIT" if val > env.upper else "WITHIN_LIMIT"
                
        # Top level safety
        s_score = result_db.s_score
        prediction_risk = result_db.prediction_risk
        uncertainty_risk = result_db.uncertainty_risk
        
        if not has_any_envelope:
            s_score = None
            prediction_risk = None
            uncertainty_risk = None
            
        safety = {
            "prediction_risk": prediction_risk,
            "s_score": s_score,
            "uncertainty_risk": uncertainty_risk,
            "details": details
        }

        return {
            "component_id": result_db.component_id,
            "lot": comp_db.lot_id,
            "device_type": comp_db.device_type,
            "station": comp_db.station_id,
            "decision": result_db.decision,
            "ldi": result_db.ldi,
            "a_score": result_db.a_score,
            "s_score": result_db.s_score,
            "prediction_risk": result_db.prediction_risk,
            "uncertainty_risk": result_db.uncertainty_risk,
            "predicted_168h": format_predicted_168h(ev.get("predicted_168h")),
            "test_integrity_flag": ev.get("integrity_flag", False),
            "screening_stage": result_db.stage,
            "basis": basis,
            "evidence": result_db.evidence,
            "test_integrity": ev.get("test_integrity"),
            "history": history,
            "safety": safety,
            "b_models": b_models,
            "intervals": pred_intervals,
            "shap": ev.get("shap", []),
            "model_version": model_version,
            "warnings": ev.get("warnings", []),
            "explanation": ev.get("explanation"),
            "run_id": result_db.run_id
        }

    # If not stored, return a not-found error
    raise HTTPException(
        status_code=404,
        detail={
            "error_code": "COMPONENT_NOT_FOUND",
            "message": f"Component {component_id} not found. Run screening first.",
            "component_id": component_id,
        },
    )
