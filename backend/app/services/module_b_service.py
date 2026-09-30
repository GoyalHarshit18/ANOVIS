import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.db.models import Measurement, Component, ScreeningRun, Prediction, AnomalyEvidence
from app.ml.model_registry import registry
from app.inference.feature_builder import (
    build_b0_vector,
    build_b1_vector,
    build_b2_early_vector,
    build_b2_96h_vector
)
import numpy as np

logger = logging.getLogger("sih26170.services.module_b")

_run_cache_meas_b = {}
def get_component_measurements(run_id: str, component_id: str, db: Session) -> Dict[str, Any]:
    global _run_cache_meas_b
    if run_id not in _run_cache_meas_b:
        measurements = db.query(Measurement).filter(Measurement.run_id == run_id).all()
        comps = db.query(Component).filter(Component.component_id.in_([m.component_id for m in measurements])).all()
        comp_map = {c.component_id: c for c in comps}
        _run_cache_meas_b[run_id] = {}
        for m in measurements:
            cid = m.component_id
            if cid not in _run_cache_meas_b[run_id]:
                _run_cache_meas_b[run_id][cid] = {
                    "component_id": cid, "run_id": run_id,
                    "lot_id": comp_map[cid].lot_id if cid in comp_map else None,
                    "device_type": comp_map[cid].device_type if cid in comp_map else None,
                    "station": comp_map[cid].station_id if cid in comp_map else None,
                }
            chk = m.checkpoint_hour
            _run_cache_meas_b[run_id][cid][f"Iddq_uA_{chk}h"] = m.iddq_ua
            _run_cache_meas_b[run_id][cid][f"Leakage_nA_{chk}h"] = m.leakage_na
            _run_cache_meas_b[run_id][cid][f"PropDelay_ns_{chk}h"] = m.prop_delay_ns
            _run_cache_meas_b[run_id][cid][f"Temperature_{chk}h"] = m.temperature
            _run_cache_meas_b[run_id][cid][f"Voltage_{chk}h"] = m.voltage
            _run_cache_meas_b[run_id][cid][f"Temperature_C_{chk}h"] = m.temperature
    return _run_cache_meas_b[run_id].get(component_id, {"component_id": component_id, "run_id": run_id})

_run_cache_ae = {}
def get_module_a_evidence(run_id: str, component_id: str, db: Session) -> Dict[str, float]:
    global _run_cache_ae
    if run_id not in _run_cache_ae:
        aes = db.query(AnomalyEvidence).filter_by(run_id=run_id).all()
        _run_cache_ae[run_id] = {ae.component_id: ae for ae in aes}
    ae = _run_cache_ae[run_id].get(component_id)
    if not ae:
        return {}
    return {
        "PAT_Risk": ae.pat_score,
        "Peer_Risk": ae.peer_score,
        "Temporal_Risk": ae.temporal_score,
        "IF_Risk": ae.isolation_forest_score
    }

def _run_stage_inference(stage_name: str, vector: List[float], targets: List[str]) -> Dict[str, Any]:
    predictions = {}
    warnings = []
    
    if vector is None:
        return {
            "available": False,
            "prediction": {},
            "model_version": None,
            "status": "UNAVAILABLE",
            "reason": f"Missing inputs or invalid vector for {stage_name}"
        }
        
    X = np.array([vector])
    
    has_success = False
    
    for target in targets:
        model_key = f"{stage_name}_{target}"
        loaded_obj = registry.get(model_key)
        
        param_name = f"{target}_168h" if target != "Delay" else "PropDelay_ns_168h"
        if target == "IDDQ":
            param_name = "Iddq_uA_168h"
        elif target == "Leakage":
            param_name = "Leakage_nA_168h"
            
        if loaded_obj is None:
            predictions[param_name] = None
            warnings.append(f"Model artifact not loaded for {model_key}")
            continue
            
        model = loaded_obj
        if isinstance(loaded_obj, dict):
            model = loaded_obj.get("model", loaded_obj.get("pipeline", list(loaded_obj.values())[0] if loaded_obj else None))
            
        if model is None or not hasattr(model, "predict"):
            predictions[param_name] = None
            warnings.append(f"Invalid model artifact structure for {model_key}")
            continue
            
        try:
            pred = model.predict(X)[0]
            predictions[param_name] = round(float(pred), 4)
            has_success = True
        except Exception as e:
            predictions[param_name] = None
            warnings.append(f"Inference error for {model_key}: {e}")
            logger.error("Inference error for %s: %s", model_key, e)
            
    if not has_success:
        return {
            "available": False,
            "prediction": {},
            "model_version": None,
            "status": "ERROR",
            "warnings": warnings,
            "reason": "All parameter models failed"
        }
        
    return {
        "available": True,
        "prediction": predictions,
        "model_version": "v1.0", # Replace if dynamic versioning exists
        "status": "AVAILABLE",
        "warnings": warnings
    }

def run_module_b_for_component(run_id: str, component_id: str, db: Session) -> Dict[str, Any]:
    meas = get_component_measurements(run_id, component_id, db)
    legacy_risks = get_module_a_evidence(run_id, component_id, db)
    
    has_0h = any(meas.get(f"{p}_0h") is not None for p in ["Iddq_uA", "Leakage_nA", "PropDelay_ns"])
    has_24h = any(meas.get(f"{p}_24h") is not None for p in ["Iddq_uA", "Leakage_nA", "PropDelay_ns"])
    has_96h = any(meas.get(f"{p}_96h") is not None for p in ["Iddq_uA", "Leakage_nA", "PropDelay_ns"])
    
    response = {
        "component_id": component_id,
        "run_id": run_id,
        "prediction_stages": {}
    }
    
    targets = ["IDDQ", "Leakage", "Delay"]
    
    # B0
    b0_vector = build_b0_vector(meas)
    response["prediction_stages"]["B0"] = _run_stage_inference("B0", b0_vector, targets)
    
    # B1
    b1_vector = build_b1_vector(meas)
    response["prediction_stages"]["B1"] = _run_stage_inference("B1", b1_vector, targets)
    
    # B2-Early
    # B2-Early requires Module-A evidence which is only computed if 24h data is present
    if not legacy_risks or not legacy_risks.get("PAT_Risk"):
        response["prediction_stages"]["B2-Early"] = {
            "available": False, "prediction": {}, "model_version": None, "status": "UNAVAILABLE", "reason": "Missing Module-A evidence"
        }
    else:
        b2_early_vector = build_b2_early_vector(meas, legacy_risks)
        response["prediction_stages"]["B2-Early"] = _run_stage_inference("B2_Early", b2_early_vector, targets)
        
    # B2-96h
    if not has_96h or not legacy_risks or not legacy_risks.get("PAT_Risk"):
        response["prediction_stages"]["B2-96h"] = {
            "available": False, "prediction": {}, "model_version": None, "status": "UNAVAILABLE", "reason": "Missing 96h data or Module-A evidence"
        }
    else:
        b2_96h_vector = build_b2_96h_vector(meas, legacy_risks)
        response["prediction_stages"]["B2-96h"] = _run_stage_inference("B2_96h", b2_96h_vector, targets)
        
    return response

def save_module_b_predictions(db: Session, result: Dict[str, Any], existing_preds_map: Dict[tuple, Any] = None):
    run_id = result["run_id"]
    component_id = result["component_id"]
    
    for stage_name, stage_data in result["prediction_stages"].items():
        key = (component_id, stage_name)
        if existing_preds_map is not None:
            pred = existing_preds_map.get(key)
        else:
            pred = db.query(Prediction).filter_by(
                run_id=run_id, component_id=component_id, prediction_stage=stage_name
            ).first()
        
        if not pred:
            pred = Prediction(
                run_id=run_id,
                component_id=component_id,
                prediction_stage=stage_name
            )
            db.add(pred)
            if existing_preds_map is not None:
                existing_preds_map[key] = pred
            
        pred.model_name = stage_name
        pred.model_version = stage_data.get("model_version")
        pred.available = stage_data.get("available", False)
        pred.status = stage_data.get("status")
        pred.predicted_168h = stage_data.get("prediction", {})
        pred.warnings = stage_data.get("warnings", [])
        
        if "reason" in stage_data:
            pred.evidence = {"reason": stage_data["reason"]}

def run_module_b_for_run(run_id: str, db: Session) -> Dict[str, Any]:
    run = db.query(ScreeningRun).filter_by(run_id=run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found.")

    comp_ids = [r[0] for r in db.query(Measurement.component_id).filter_by(run_id=run_id).distinct().all()]

    # Pre-fetch all existing predictions for this run in one batch query
    existing_preds = db.query(Prediction).filter_by(run_id=run_id).all()
    existing_preds_map = {(p.component_id, p.prediction_stage): p for p in existing_preds}

    processed = 0
    unavailable = 0
    results = []
    
    stages_counts = {
        "B0": 0,
        "B1": 0,
        "B2-Early": 0,
        "B2-96h": 0
    }

    for cid in comp_ids:
        try:
            res = run_module_b_for_component(run_id, cid, db)
            save_module_b_predictions(db, res, existing_preds_map)

            any_available = False
            for stage_name, stage_data in res["prediction_stages"].items():
                if stage_data.get("available"):
                    stages_counts[stage_name] += 1
                    any_available = True
                    
            if any_available:
                processed += 1
            else:
                unavailable += 1
                
            results.append(res)
        except Exception as e:
            logger.error("Component %s failed in Module B: %s", cid, str(e))
            unavailable += 1

    db.commit()

    return {
        "run_id": run_id,
        "total_components": len(comp_ids),
        "components_with_predictions": processed,
        "components_unavailable": unavailable,
        "stages": stages_counts,
        "results": results
    }
