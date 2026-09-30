import logging
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import Component, Measurement, AnomalyEvidence, ScreeningResult, AnomalyOrigins, LotAnalysis, StationAnalysis, Lot
from app.ml.model_registry import registry
from app.inference.feature_builder import build_station_vector

logger = logging.getLogger("sih26170.anomaly_analysis")

def run_anomaly_analysis_for_run(run_id: str, db: Session) -> Dict[str, Any]:
    """Orchestrates Device, Lot, and Station anomaly analysis for a run."""
    # 1. Device Analysis
    device_summary = _run_device_analysis(run_id, db)
    
    # 2. Lot Analysis
    lot_summary = _run_lot_analysis(run_id, db)
    
    # 3. Station Analysis
    station_summary = _run_station_analysis(run_id, db)
    
    db.commit()
    
    return {
        "run_id": run_id,
        "status": "ANOMALY_ANALYSIS_COMPLETED",
        "device_analysis": device_summary,
        "lot_analysis": lot_summary,
        "station_analysis": station_summary
    }

def _run_device_analysis(run_id: str, db: Session) -> Dict[str, Any]:
    """Persist independent device anomaly evidence originating from Phase 3 Module A."""
    evidence_records = db.query(AnomalyEvidence).filter_by(run_id=run_id).all()
    results_records = db.query(ScreeningResult).filter_by(run_id=run_id).all()
    
    comp_map = {sr.component_id: sr for sr in results_records}
    comp_ids = [ev.component_id for ev in evidence_records]
    
    # Pre-fetch components and existing origins in batch
    comps = db.query(Component).filter(Component.component_id.in_(comp_ids)).all()
    comp_db_map = {c.component_id: c for c in comps}
    existing_origins = {o.component_id: o for o in db.query(AnomalyOrigins).filter_by(run_id=run_id).all()}
    
    processed = 0
    unavailable = 0
    
    for ev in evidence_records:
        comp_id = ev.component_id
        sr = comp_map.get(comp_id)
        
        if not sr:
            continue
            
        status = "NORMAL"
        if sr.decision == "UNAVAILABLE":
            status = "UNAVAILABLE"
            unavailable += 1
        elif sr.decision == "ANOMALOUS":
            status = "ANOMALOUS"
            processed += 1
        else:
            processed += 1
            
        # Get lot and station from pre-fetched map
        comp = comp_db_map.get(comp_id)
        if not comp:
            continue
            
        # Idempotent upsert with pre-fetched map
        origin = existing_origins.get(comp_id)
        if not origin:
            origin = AnomalyOrigins(run_id=run_id, component_id=comp_id)
            db.add(origin)
            existing_origins[comp_id] = origin
            
        origin.lot_id = comp.lot_id
        origin.station_id = comp.station_id
        origin.device_status = status
        origin.device_score = sr.a_score
        
        # Pull component_24h prediction if available
        comp_pred = None
        if sr.evidence:
            comp_pred = sr.evidence.get("prediction_class")
            
        origin.evidence = {
            "a_score": sr.a_score,
            "component_24h_prediction": comp_pred,
            "pat_status": ev.pat_evidence.get("status") if ev.pat_evidence else None,
            "peer_status": ev.peer_evidence.get("status") if ev.peer_evidence else None,
            "temporal_status": ev.temporal_evidence.get("status") if ev.temporal_evidence else None,
            "if_status": ev.isolation_forest_evidence.get("status") if ev.isolation_forest_evidence else None,
        }
        
    db.flush()
    return {
        "processed_components": processed,
        "unavailable_components": unavailable
    }

def _run_lot_analysis(run_id: str, db: Session) -> Dict[str, Any]:
    """Analyzes the lot population against the historical healthy reference limits."""
    ref_limits = registry.get("reference_limits")
    
    if not ref_limits:
        return {"status": "UNAVAILABLE", "reason": "Reference limits artifact missing"}
        
    # Get all components in the run
    components = db.query(Component).join(Measurement, Component.component_id == Measurement.component_id).filter(Measurement.run_id == run_id).all()
    # Group by lot
    lots = {}
    for c in components:
        lots.setdefault(c.lot_id, []).append(c.component_id)
        
    lot_summaries = {}
    for lot_id, comp_ids in lots.items():
        # Get 0h and 24h measurements
        measurements = db.query(Measurement).filter(
            Measurement.run_id == run_id,
            Measurement.component_id.in_(comp_ids),
            Measurement.checkpoint_hour.in_([0, 24])
        ).all()
        
        data = {"Iddq_uA_0h": [], "Leakage_nA_0h": [], "PropDelay_ns_0h": [],
                "Iddq_uA_24h": [], "Leakage_nA_24h": [], "PropDelay_ns_24h": []}
                
        for m in measurements:
            hour = m.checkpoint_hour
            if m.iddq_ua is not None: data[f"Iddq_uA_{hour}h"].append(m.iddq_ua)
            if m.leakage_na is not None: data[f"Leakage_nA_{hour}h"].append(m.leakage_na)
            if m.prop_delay_ns is not None: data[f"PropDelay_ns_{hour}h"].append(m.prop_delay_ns)
            
        shift_evidence = {}
        shift_detected = False
        
        for param, values in data.items():
            if not values or param not in ref_limits:
                continue
            median_val = float(np.median(values))
            ref = ref_limits[param]
            
            if median_val < ref["lower"] or median_val > ref["upper"]:
                shift_detected = True
                shift_evidence[param] = {
                    "lot_median": median_val,
                    "ref_median": float(ref["median"]),
                    "ref_lower": float(ref["lower"]),
                    "ref_upper": float(ref["upper"]),
                    "status": "SHIFT_DETECTED"
                }
            else:
                shift_evidence[param] = {
                    "lot_median": median_val,
                    "ref_median": float(ref["median"]),
                    "status": "NORMAL"
                }
                
        status = "SHIFT_DETECTED" if shift_detected else "NORMAL"
        
        # Idempotent upsert
        lot_analysis = db.query(LotAnalysis).filter_by(run_id=run_id, lot_id=lot_id).first()
        if not lot_analysis:
            lot_analysis = LotAnalysis(run_id=run_id, lot_id=lot_id)
            db.add(lot_analysis)
            
        lot_analysis.status = status
        lot_analysis.total_component_count = len(comp_ids)
        lot_analysis.affected_component_count = len(comp_ids) if shift_detected else 0
        lot_analysis.parameter_evidence = shift_evidence
        
        lot_summaries[lot_id] = status
        
        # Update AnomalyOrigins
        origins = db.query(AnomalyOrigins).filter_by(run_id=run_id, lot_id=lot_id).all()
        for org in origins:
            org.lot_status = status
            
    return {"lots_processed": len(lot_summaries), "details": lot_summaries}

def _run_station_analysis(run_id: str, db: Session) -> Dict[str, Any]:
    """Runs the station disturbance classifier on stations within the run."""
    station_model = registry.get("station_disturbance_classifier")
    
    if not station_model:
        return {"status": "UNAVAILABLE", "reason": "Station classifier artifact missing"}
        
    # Get all components and their measurements in the run
    measurements = db.query(Measurement).filter(Measurement.run_id == run_id).all()
    comp_ids = list(set([m.component_id for m in measurements]))
    components = db.query(Component).filter(Component.component_id.in_(comp_ids)).all()
    
    comp_stations = {c.component_id: (c.station_id, c.lot_id) for c in components}
    
    # Group measurements by component
    comp_meas = {}
    for m in measurements:
        comp_meas.setdefault(m.component_id, {})[m.checkpoint_hour] = m
        
    stations = {}
    for comp_id, chkpts in comp_meas.items():
        if 0 in chkpts and 24 in chkpts:
            station_id, lot_id = comp_stations.get(comp_id, (None, None))
            if station_id:
                stations.setdefault(station_id, []).append((comp_id, chkpts[0], chkpts[24], lot_id))
                
    processed = 0
    unavailable = 0
    station_summaries = {}
    
    for station_id, comps in stations.items():
        if not comps:
            continue
            
        disturbance_count = 0
        valid_comps = 0
        
        for comp_id, m0, m24, lot_id in comps:
            # Build measurement dict
            m_dict = {
                "Iddq_uA_0h": m0.iddq_ua,
                "Leakage_nA_0h": m0.leakage_na,
                "PropDelay_ns_0h": m0.prop_delay_ns,
                "Temperature_0h": m0.temperature,
                "Temperature_C_0h": m0.temperature,
                "Voltage_0h": m0.voltage,
                
                "Iddq_uA_24h": m24.iddq_ua,
                "Leakage_nA_24h": m24.leakage_na,
                "PropDelay_ns_24h": m24.prop_delay_ns,
                "Temperature_24h": m24.temperature,
                "Temperature_C_24h": m24.temperature,
                "Voltage_24h": m24.voltage,
            }
            
            vector = build_station_vector(m_dict)
            if vector is None:
                continue
                
            valid_comps += 1
            
            # Predict
            try:
                X = np.array(vector).reshape(1, -1)
                pred = int(station_model.predict(X)[0])
                if pred == 1:
                    disturbance_count += 1
                    
                # Update AnomalyOrigins for this component
                origin = db.query(AnomalyOrigins).filter_by(run_id=run_id, component_id=comp_id).first()
                if not origin:
                    origin = AnomalyOrigins(run_id=run_id, component_id=comp_id)
                    db.add(origin)
                
                origin.station_id = station_id
                origin.station_status = "DISTURBANCE" if pred == 1 else "NORMAL"
                if not origin.evidence:
                    origin.evidence = {}
                origin.evidence["station_disturbance"] = pred
                
                        # Removed db.flush()
            except Exception as e:
                logger.error(f"Station inference failed for component {comp_id}: {e}")
                
        if valid_comps == 0:
            unavailable += 1
            status = "UNAVAILABLE"
        else:
            processed += 1
            prop = disturbance_count / valid_comps
            # No authoritative station-level aggregation rule exists in the project
            status = "UNAVAILABLE"
            
        # Upsert StationAnalysis
        station_analysis = db.query(StationAnalysis).filter_by(run_id=run_id, station_id=station_id).first()
        if not station_analysis:
            station_analysis = StationAnalysis(run_id=run_id, station_id=station_id)
            db.add(station_analysis)
            
        # We pick the lot_id from the first component for simplicity if multiple, though usually 1 lot per run
        station_analysis.lot_id = comps[0][3]
        station_analysis.integrity_status = status
        station_analysis.affected_component_count = disturbance_count
        station_analysis.within_station_evidence = {
            "total_components": valid_comps,
            "disturbance_components": disturbance_count,
            "proportion": round(prop, 4) if valid_comps > 0 else 0,
            "reason": "No authoritative station-level aggregation rule exists to convert component counts to a station status."
        }
        station_summaries[station_id] = status
        
    return {
        "processed_stations": processed,
        "unavailable_stations": unavailable,
        "details": station_summaries
    }
