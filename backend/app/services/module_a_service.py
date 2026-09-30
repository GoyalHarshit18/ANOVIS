import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.db.models import Measurement, Component, ScreeningRun, ScreeningResult, AnomalyEvidence
from app.ml.model_registry import registry
from app.ml.pat_engine import compute_pat
from app.ml.peer_engine import compute_peer_analysis
from app.ml.temporal_engine import compute_temporal_analysis
from app.ml.isolation_forest_engine import compute_isolation_forest
from app.ml.risk_fusion import compute_a_score
from app.inference.feature_builder import build_component_24h_vector
import numpy as np

logger = logging.getLogger("sih26170.services.module_a")

_run_cache_meas = {}
def get_component_measurements(run_id: str, component_id: str, db: Session) -> Dict[str, Any]:
    global _run_cache_meas
    if run_id not in _run_cache_meas:
        measurements = db.query(Measurement).filter(Measurement.run_id == run_id).all()
        comps = db.query(Component).filter(Component.component_id.in_([m.component_id for m in measurements])).all()
        comp_map = {c.component_id: c for c in comps}
        _run_cache_meas[run_id] = {}
        for m in measurements:
            cid = m.component_id
            if cid not in _run_cache_meas[run_id]:
                _run_cache_meas[run_id][cid] = {
                    "component_id": cid, "run_id": run_id,
                    "lot_id": comp_map[cid].lot_id if cid in comp_map else None,
                    "device_type": comp_map[cid].device_type if cid in comp_map else None,
                    "station": comp_map[cid].station_id if cid in comp_map else None,
                }
            chk = m.checkpoint_hour
            _run_cache_meas[run_id][cid][f"Iddq_uA_{chk}h"] = m.iddq_ua
            _run_cache_meas[run_id][cid][f"Leakage_nA_{chk}h"] = m.leakage_na
            _run_cache_meas[run_id][cid][f"PropDelay_ns_{chk}h"] = m.prop_delay_ns
            _run_cache_meas[run_id][cid][f"Temperature_{chk}h"] = m.temperature
            _run_cache_meas[run_id][cid][f"Voltage_{chk}h"] = m.voltage
            _run_cache_meas[run_id][cid][f"Temperature_C_{chk}h"] = m.temperature
    return _run_cache_meas[run_id].get(component_id, {"component_id": component_id, "run_id": run_id})

def run_module_a_for_component(run_id: str, component_id: str, db: Session) -> Dict[str, Any]:
    """Execute Legacy Module A and Component 24h Classifier for a single component."""
    meas = get_component_measurements(run_id, component_id, db)

    has_0h = any(meas.get(f"{p}_0h") is not None for p in ["Iddq_uA", "Leakage_nA", "PropDelay_ns"])
    has_24h = any(meas.get(f"{p}_24h") is not None for p in ["Iddq_uA", "Leakage_nA", "PropDelay_ns"])

    if not (has_0h and has_24h):
        return {
            "component_id": component_id,
            "run_id": run_id,
            "status": "UNAVAILABLE",
            "warnings": ["Required 0h or 24h checkpoint missing"]
        }

    # Execute Legacy Module A
    pat_result = compute_pat(meas)
    peer_result = compute_peer_analysis(meas)
    temporal_result = compute_temporal_analysis(meas)
    if_result = compute_isolation_forest(meas)

    a_score = compute_a_score(pat_result, peer_result, temporal_result, if_result)

    # Prepare risks for feature builder
    legacy_risks = {
        "PAT_Risk": pat_result.get("score") if pat_result else None,
        "Peer_Risk": peer_result.get("score") if peer_result else None,
        "Temporal_Risk": temporal_result.get("score") if temporal_result else None,
        "IF_Risk": if_result.get("score") if if_result else None
    }

    vector = build_component_24h_vector(meas, legacy_risks)

    comp_24h_res = {}
    if vector is None:
        comp_24h_res = {"status": "INFERENCE_ERROR", "reason": "Feature construction failed or invalid contract"}
    else:
        model = registry.get("component_24h_classifier")
        if not model:
            comp_24h_res = {"status": "UNAVAILABLE", "reason": "Model artifact not loaded"}
        else:
            try:
                X = np.array(vector).reshape(1, -1)
                prediction_class = int(model.predict(X)[0])
                comp_24h_res = {"prediction_class": prediction_class}

                if hasattr(model, "predict_proba"):
                    probs = model.predict_proba(X)[0]
                    prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
                    comp_24h_res["prediction_probability"] = prob

                comp_24h_res["status"] = "SUCCESS"
            except Exception as e:
                comp_24h_res = {"status": "INFERENCE_ERROR", "reason": str(e)}

    return {
        "component_id": component_id,
        "run_id": run_id,
        "status": "AVAILABLE",
        "pat": pat_result,
        "peer": peer_result,
        "temporal": temporal_result,
        "isolation_forest": if_result,
        "a_score": a_score,
        "component_24h": comp_24h_res,
        "model_versions": {
            "component_24h_classifier": "component_24h_classifier.pkl"
        }
    }

def save_module_a_evidence(db: Session, result: Dict[str, Any], existing_ae_map: Dict[str, Any] = None, existing_sr_map: Dict[str, Any] = None):
    """Persist the generated Module A evidence into the DB (Idempotent)."""
    run_id = result["run_id"]
    cid = result["component_id"]

    if existing_sr_map is not None:
        sr = existing_sr_map.get(cid)
    else:
        sr = db.query(ScreeningResult).filter_by(run_id=run_id, component_id=cid).first()

    if result["status"] == "UNAVAILABLE":
        if not sr:
            sr = ScreeningResult(run_id=run_id, component_id=cid)
            db.add(sr)
            if existing_sr_map is not None:
                existing_sr_map[cid] = sr
        sr.stage = "MODULE_A"
        sr.decision = "UNAVAILABLE"
        sr.warnings = result.get("warnings", [])
        return

    # Idempotent Evidence Saving
    if existing_ae_map is not None:
        ae = existing_ae_map.get(cid)
    else:
        ae = db.query(AnomalyEvidence).filter_by(run_id=run_id, component_id=cid).first()

    if not ae:
        ae = AnomalyEvidence(run_id=run_id, component_id=cid)
        db.add(ae)
        if existing_ae_map is not None:
            existing_ae_map[cid] = ae

    def safe_float(val):
        if val is None:
            return None
        return float(val)

    ae.pat_score = safe_float(result["pat"].get("score")) if result.get("pat") else None
    ae.pat_evidence = result.get("pat")
    ae.peer_score = safe_float(result["peer"].get("score")) if result.get("peer") else None
    ae.peer_evidence = result.get("peer")
    ae.temporal_score = safe_float(result["temporal"].get("score")) if result.get("temporal") else None
    ae.temporal_evidence = result.get("temporal")
    ae.isolation_forest_score = safe_float(result["isolation_forest"].get("score")) if result.get("isolation_forest") else None
    ae.isolation_forest_evidence = result.get("isolation_forest")
    ae.a_score = safe_float(result.get("a_score"))

    if not sr:
        sr = ScreeningResult(run_id=run_id, component_id=cid)
        db.add(sr)
        if existing_sr_map is not None:
            existing_sr_map[cid] = sr

    sr.stage = "MODULE_A"
    sr.a_score = safe_float(result.get("a_score"))
    sr.model_version = result.get("model_versions", {}).get("component_24h_classifier")
    sr.evidence = result.get("component_24h")
    
    comp_24h_status = result.get("component_24h", {}).get("status")
    if comp_24h_status == "SUCCESS":
        sr.decision = "AVAILABLE"
    else:
        sr.decision = "INFERENCE_ERROR"
        
    sr.warnings = result.get("warnings", [])

def run_module_a_for_run(run_id: str, db: Session) -> Dict[str, Any]:
    """Orchestrate Module A for an entire run."""
    run = db.query(ScreeningRun).filter_by(run_id=run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found.")

    if run.status not in ["READY_FOR_INFERENCE", "MODULE_A_COMPLETED", "MODULE_A_COMPLETED_WITH_WARNINGS"]:
        pass
        
    run.status = "MODULE_A_RUNNING"
    db.commit()

    # Pre-fetch existing evidence and screening results in batch
    existing_ae_map = {ae.component_id: ae for ae in db.query(AnomalyEvidence).filter_by(run_id=run_id).all()}
    existing_sr_map = {sr.component_id: sr for sr in db.query(ScreeningResult).filter_by(run_id=run_id).all()}

    # Get all distinct components in this run
    comp_ids = [r[0] for r in db.query(Measurement.component_id).filter_by(run_id=run_id).distinct().all()]

    processed = 0
    unavailable = 0
    failed = 0
    results = []

    for cid in comp_ids:
        try:
            res = run_module_a_for_component(run_id, cid, db)
            save_module_a_evidence(db, res, existing_ae_map, existing_sr_map)

            if res["status"] == "UNAVAILABLE":
                unavailable += 1
            elif res.get("component_24h", {}).get("status") != "SUCCESS":
                failed += 1
            else:
                processed += 1
                
            results.append(res)
        except Exception as e:
            logger.error("Component %s failed in Module A: %s", cid, str(e))
            failed += 1
            results.append({
                "component_id": cid,
                "run_id": run_id,
                "status": "SYSTEM_ERROR",
                "warnings": [str(e)]
            })

    if failed > 0 or unavailable > 0:
        run.status = "MODULE_A_COMPLETED_WITH_WARNINGS"
    else:
        run.status = "MODULE_A_COMPLETED"
        
    db.commit()

    return {
        "run_id": run_id,
        "status": run.status,
        "total_components": len(comp_ids),
        "processed_components": processed,
        "unavailable_components": unavailable,
        "failed_components": failed,
        "results": results
    }
