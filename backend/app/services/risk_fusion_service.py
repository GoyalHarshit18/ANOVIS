import logging
from typing import Dict, Any, List, Optional
import numpy as np

from sqlalchemy.orm import Session

from app.db.models import (
    ScreeningRun,
    Component,
    Measurement,
    AnomalyEvidence,
    ScreeningResult,
    AnomalyOrigins,
    LotAnalysis,
    StationAnalysis,
    Prediction,
    RiskFusionResult,
    AuditEvent
)
from app.ml.model_registry import registry
from app.ml.risk_fusion import compute_ldi, determine_decision
from app.inference.feature_builder import (
    build_b2_96h_vector,
    build_latent_specialist_vector,
    build_fusion_vector
)
from app.ml.safety_engine import compute_safety_analysis

logger = logging.getLogger("sih26170.services.risk_fusion")

_run_cache_meas_rf = {}
def get_component_measurements(run_id: str, component_id: str, db: Session) -> Dict[str, Any]:
    global _run_cache_meas_rf
    if run_id not in _run_cache_meas_rf:
        measurements = db.query(Measurement).filter(Measurement.run_id == run_id).all()
        _run_cache_meas_rf[run_id] = {}
        for m in measurements:
            cid = m.component_id
            if cid not in _run_cache_meas_rf[run_id]:
                _run_cache_meas_rf[run_id][cid] = {"component_id": cid, "run_id": run_id}
            chk = m.checkpoint_hour
            _run_cache_meas_rf[run_id][cid][f"Iddq_uA_{chk}h"] = m.iddq_ua
            _run_cache_meas_rf[run_id][cid][f"Leakage_nA_{chk}h"] = m.leakage_na
            _run_cache_meas_rf[run_id][cid][f"PropDelay_ns_{chk}h"] = m.prop_delay_ns
            _run_cache_meas_rf[run_id][cid][f"Temperature_{chk}h"] = m.temperature
            _run_cache_meas_rf[run_id][cid][f"Voltage_{chk}h"] = m.voltage
            _run_cache_meas_rf[run_id][cid][f"Temperature_C_{chk}h"] = m.temperature
    return _run_cache_meas_rf[run_id].get(component_id, {"component_id": component_id, "run_id": run_id})

def run_risk_fusion_for_component(
    run_id: str, 
    component_id: str, 
    db: Session,
    ae_map: Dict[str, Any] = None,
    sr_map: Dict[str, Any] = None,
    preds_map: Dict[str, List[Any]] = None,
    origin_map: Dict[str, Any] = None,
    rf_map: Dict[str, Any] = None
) -> Dict[str, Any]:
    meas = get_component_measurements(run_id, component_id, db)
    
    # 1. Load Module A evidence
    if ae_map is not None:
        ae = ae_map.get(component_id)
    else:
        ae = db.query(AnomalyEvidence).filter_by(run_id=run_id, component_id=component_id).first()

    legacy_risks = {}
    if ae:
        legacy_risks = {
            "PAT_Risk": ae.pat_score,
            "Peer_Risk": ae.peer_score,
            "Temporal_Risk": ae.temporal_score,
            "IF_Risk": ae.isolation_forest_score
        }
        
    a_score = ae.a_score if ae else None

    # Module A ScreeningResult (to get Supervised_Score)
    if sr_map is not None:
        sr = sr_map.get(component_id)
    else:
        sr = db.query(ScreeningResult).filter_by(run_id=run_id, component_id=component_id).first()

    supervised_score = None
    if sr and sr.evidence:
        if sr.stage == "MODULE_A":
            supervised_score = sr.evidence.get("prediction_probability")
            if supervised_score is None and "prediction_class" in sr.evidence:
                supervised_score = float(sr.evidence["prediction_class"])
        elif sr.stage == "FINAL":
            supervised_score = sr.evidence.get("current_state", {}).get("supervised_score")
            
    # 2. Load Module B evidence
    if preds_map is not None:
        preds = preds_map.get(component_id, [])
    else:
        preds = db.query(Prediction).filter_by(run_id=run_id, component_id=component_id).all()

    prediction_risk = None
    uncertainty_risk = None
    s_score = None
    b2_96h_available = False
    
    best_pred_val = None
    
    for p in preds:
        if p.prediction_stage == "B2-96h" and p.available:
            b2_96h_available = True
            
    # Find best prediction for safety engine
    for stage in ["B2-96h", "B2-Early", "B1", "B0"]:
        for p in preds:
            if p.prediction_stage == stage and p.available and p.predicted_168h:
                best_pred_val = p.predicted_168h
                break
        if best_pred_val:
            break

    if best_pred_val:
        translated_pred = {}
        for param in ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]:
            if f"{param}_168h" in best_pred_val:
                translated_pred[param] = best_pred_val[f"{param}_168h"]
            elif param in best_pred_val:
                translated_pred[param] = best_pred_val[param]

        safety = compute_safety_analysis(predicted_168h=translated_pred, measurements=meas)
        prediction_risk = safety.get("prediction_risk")
        s_score = safety.get("s_score")
        uncertainty_risk = safety.get("uncertainty_risk")
            
    # 3. Load Device / Lot / Station Evidence
    if origin_map is not None:
        origin = origin_map.get(component_id)
    else:
        origin = db.query(AnomalyOrigins).filter_by(run_id=run_id, component_id=component_id).first()

    test_integrity_flag = False
    static_result = "PASS"
    if origin:
        if origin.device_status == "REJECT" or origin.device_status == "FAIL":
            static_result = "FAIL"
        if origin.station_status == "DISTURBANCE":
            test_integrity_flag = True

    # 4. Construct Exact Fusion Feature Vector
    component_96h_score = None
    b2_96h_vec = build_b2_96h_vector(meas, legacy_risks)
    c96_model = registry.get("component_96h_classifier")
    if b2_96h_vec and c96_model:
        X = np.array([b2_96h_vec])
        try:
            if hasattr(c96_model, "predict_proba"):
                probs = c96_model.predict_proba(X)[0]
                component_96h_score = float(probs[1]) if len(probs) > 1 else float(probs[0])
            else:
                component_96h_score = float(c96_model.predict(X)[0])
        except Exception:
            pass

    late_drift_risk = None
    ls_vec = build_latent_specialist_vector(meas)
    ls_model = registry.get("latent_specialist")
    if ls_vec and ls_model:
        X = np.array([ls_vec])
        try:
            if hasattr(ls_model, "predict_proba"):
                probs = ls_model.predict_proba(X)[0]
                late_drift_risk = float(probs[1]) if len(probs) > 1 else float(probs[0])
            else:
                late_drift_risk = float(ls_model.predict(X)[0])
        except Exception:
            pass

    fusion_model = registry.get("fusion_96h_classifier")
    fusion_score = None
    fusion_available = False
    warnings = []
    
    if supervised_score is None or component_96h_score is None or late_drift_risk is None:
        warnings.append("Missing required fusion inputs")
        fusion_status = "UNAVAILABLE"
    else:
        if not fusion_model:
            warnings.append("Fusion model not loaded")
            fusion_status = "UNAVAILABLE"
        else:
            fusion_vector = build_fusion_vector(supervised_score, component_96h_score, late_drift_risk)
            if not fusion_vector:
                warnings.append("Fusion feature vector validation failed")
                fusion_status = "UNAVAILABLE"
            else:
                X_fusion = np.array([fusion_vector])
                try:
                    if hasattr(fusion_model, "predict_proba"):
                        probs = fusion_model.predict_proba(X_fusion)[0]
                        fusion_score = float(probs[1]) if len(probs) > 1 else float(probs[0])
                    else:
                        fusion_score = float(fusion_model.predict(X_fusion)[0])
                    fusion_available = True
                    fusion_status = "AVAILABLE"
                except Exception as e:
                    warnings.append(f"Fusion inference failed: {e}")
                    fusion_status = "UNAVAILABLE"

    # LDI
    ldi = compute_ldi(a_score, prediction_risk, s_score, uncertainty_risk)

    # Final QA Decision
    data_available = fusion_available and b2_96h_available
    decision_dict = determine_decision(
        static_result=static_result,
        a_score=a_score,
        prediction_risk=prediction_risk,
        s_score=s_score,
        uncertainty_risk=uncertainty_risk,
        test_integrity_flag=test_integrity_flag,
        ldi=ldi,
        data_available=data_available,
        fusion_score=fusion_score
    )

    decision = decision_dict["decision"]
    explanation = decision_dict["explanation"]

    # Save to RiskFusionResult
    if rf_map is not None:
        rf_res = rf_map.get(component_id)
    else:
        rf_res = db.query(RiskFusionResult).filter_by(run_id=run_id, component_id=component_id).first()

    if not rf_res:
        rf_res = RiskFusionResult(run_id=run_id, component_id=component_id)
        db.add(rf_res)
        if rf_map is not None:
            rf_map[component_id] = rf_res

    rf_res.a_score = a_score
    rf_res.s_score = s_score
    rf_res.prediction_risk = prediction_risk
    rf_res.uncertainty_risk = uncertainty_risk
    rf_res.ldi = ldi
    rf_res.fusion_score = fusion_score
    rf_res.final_decision = decision
    rf_res.decision_basis = {
        "current_state": {"a_score": a_score, "supervised_score": supervised_score},
        "future_state": {"prediction_risk": prediction_risk, "s_score": s_score},
        "fusion_state": {
            "component_96h_score": component_96h_score,
            "late_drift_risk": late_drift_risk,
            "fusion_score": fusion_score,
            "fusion_status": fusion_status
        },
        "test_integrity": {"integrity_flag": test_integrity_flag},
        "explanation": explanation,
        "pat": ae.pat_evidence if ae else None,
        "peer_residual": ae.peer_evidence if ae else None,
        "early_temporal": ae.temporal_evidence if ae else None,
        "isolation_forest": ae.isolation_forest_evidence if ae else None,
        "predicted_168h": best_pred_val,
        "integrity_flag": test_integrity_flag
    }
    rf_res.model_version = "fusion_96h_classifier.pkl"
    
    # Audit Event
    audit = AuditEvent(
        run_id=run_id,
        component_id=component_id,
        event_type="RISK_FUSION",
        message=f"Risk Fusion executed. Decision: {decision}",
        severity="INFO" if decision in ["PASS", "MONITOR"] else "WARNING",
        metadata_={
            "fusion_status": fusion_status,
            "final_decision": decision,
            "warnings": warnings
        }
    )
    db.add(audit)
    
    # Update ScreeningResult for FINAL
    if sr_map is not None:
        sr_final = sr_map.get(component_id)
    else:
        sr_final = db.query(ScreeningResult).filter_by(run_id=run_id, component_id=component_id).first()

    if not sr_final:
        sr_final = ScreeningResult(run_id=run_id, component_id=component_id)
        db.add(sr_final)
        if sr_map is not None:
            sr_map[component_id] = sr_final

    sr_final.stage = "FINAL"
    sr_final.decision = decision
    sr_final.ldi = ldi
    sr_final.a_score = a_score
    sr_final.s_score = s_score
    sr_final.prediction_risk = prediction_risk
    sr_final.uncertainty_risk = uncertainty_risk
    sr_final.warnings = warnings
    sr_final.evidence = rf_res.decision_basis
    
    return {
        "component_id": component_id,
        "fusion_available": fusion_available,
        "decision": decision
    }

def run_risk_fusion_for_run(run_id: str, db: Session) -> Dict[str, Any]:
    run = db.query(ScreeningRun).filter_by(run_id=run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found.")

    comp_ids = [r[0] for r in db.query(Measurement.component_id).filter_by(run_id=run_id).distinct().all()]

    # Pre-fetch existing records in batch
    ae_map = {ae.component_id: ae for ae in db.query(AnomalyEvidence).filter_by(run_id=run_id).all()}
    sr_map = {sr.component_id: sr for sr in db.query(ScreeningResult).filter_by(run_id=run_id).all()}
    origin_map = {o.component_id: o for o in db.query(AnomalyOrigins).filter_by(run_id=run_id).all()}
    rf_map = {rf.component_id: rf for rf in db.query(RiskFusionResult).filter_by(run_id=run_id).all()}
    
    preds_map = {}
    for p in db.query(Prediction).filter_by(run_id=run_id).all():
        preds_map.setdefault(p.component_id, []).append(p)

    fusion_available_count = 0
    fusion_unavailable_count = 0
    
    decision_counts = {
        "PASS": 0,
        "MONITOR": 0,
        "REVIEW_REQUIRED": 0,
        "REPEAT_MEASUREMENT": 0,
        "INVESTIGATE": 0,
        "REJECT": 0,
        "DATA_UNAVAILABLE": 0
    }

    for cid in comp_ids:
        try:
            res = run_risk_fusion_for_component(
                run_id, cid, db,
                ae_map=ae_map,
                sr_map=sr_map,
                preds_map=preds_map,
                origin_map=origin_map,
                rf_map=rf_map
            )
            
            if res["fusion_available"]:
                fusion_available_count += 1
            else:
                fusion_unavailable_count += 1
                
            dec = res["decision"]
            if dec in decision_counts:
                decision_counts[dec] += 1
                
        except Exception as e:
            logger.error("Component %s failed in Risk Fusion: %s", cid, str(e))
            fusion_unavailable_count += 1
            decision_counts["DATA_UNAVAILABLE"] += 1

    run.status = "COMPLETED"
    db.commit()

    return {
        "run_id": run_id,
        "total_components": len(comp_ids),
        "fusion_available": fusion_available_count,
        "fusion_unavailable": fusion_unavailable_count,
        "decision_counts": decision_counts
    }
