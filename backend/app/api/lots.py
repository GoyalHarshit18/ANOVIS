"""Lot analysis endpoint."""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.ml.model_registry import registry
from app.db.session import get_db
from app.db.models import Lot, Component, ScreeningResult, Measurement, StationAnalysis, AnomalyOrigins

logger = logging.getLogger("sih26170.lot_api")

router = APIRouter(tags=["lots"])

def store_lot_data(lot_id: str, data: dict):
    """Legacy store function - kept for demo seed compat."""
    pass

@router.get("/lots")
async def get_lots(db: Session = Depends(get_db)):
    """Get list of lots."""
    lots = db.query(Lot).order_by(Lot.created_at.desc()).all()
    results = []
    for lot in lots:
        comp = db.query(Component).filter(Component.lot_id == lot.lot_id).first()
        results.append({
            "lot_id": lot.lot_id,
            "device_type": comp.device_type if comp else "Unknown"
        })
    return {"lots": results}

@router.get("/lot/{lot_id}")
async def get_lot(lot_id: str, db: Session = Depends(get_db)):
    """
    Get lot-level analytics.
    Returns lot statistics, distributions, PAT references, and flagged components.
    """
    # Fetch from db
    lot_db = db.query(Lot).filter(Lot.lot_id == lot_id).first()
    
    if not lot_db:
        raise HTTPException(status_code=404, detail="Lot not found")
        
    components = db.query(Component).filter(Component.lot_id == lot_id).all()
        
    flagged = []
    if components:
        comp_ids = [c.component_id for c in components]
        # Get latest screening results for these components
        # A simple approach for this demo:
        results = db.query(ScreeningResult).filter(ScreeningResult.component_id.in_(comp_ids)).all()
        for r in results:
            if r.decision != "PASS":
                flagged.append(r.component_id)
                
    # Return default/reference lot info
    ref_limits = registry.get("reference_limits")
    pat_ref = registry.get("pat_reference")

    device_type = components[0].device_type if components and components[0].device_type else "Unknown"
    # To get temperature, we'd need to query Measurements, defaulting to Unknown for now
    temperature = "Unknown"
    if components:
        meas = db.query(Measurement).filter(Measurement.component_id == components[0].component_id).first()
        if meas and meas.temperature:
            temperature = meas.temperature

    import statistics
    
    current_leakages = []
    current_iddqs = []
    current_propdelays = []
    if components:
        comp_ids = [c.component_id for c in components]
        measurements = db.query(Measurement).filter(
            Measurement.component_id.in_(comp_ids)
        ).all()
        for m in measurements:
            if m.leakage_na is not None:
                current_leakages.append(m.leakage_na)
            if m.iddq_ua is not None:
                current_iddqs.append(m.iddq_ua)
            if m.prop_delay_ns is not None:
                current_propdelays.append(m.prop_delay_ns)
                
    current_lot_medians = {
        "Leakage_nA_0h": round(statistics.median(current_leakages), 2) if current_leakages else None,
        "Iddq_uA_0h": round(statistics.median(current_iddqs), 2) if current_iddqs else None,
        "PropDelay_ns_0h": round(statistics.median(current_propdelays), 2) if current_propdelays else None,
    }
    
    parameter_metrics = {}
    for param in ["Leakage_nA_0h", "Iddq_uA_0h", "PropDelay_ns_0h"]:
        curr_median = current_lot_medians.get(param)
        hist_ref = None
        if ref_limits and param in ref_limits:
            hist_ref = round(ref_limits[param]["median"], 2)
            
        if param == "Leakage_nA_0h" and hist_ref is None:
            hist_ref = 125.0
            
        shift_score = None
        shift_status = "N/A"
        
        if curr_median is not None and hist_ref is not None and hist_ref > 0:
            shift_ratio = curr_median / hist_ref
            shift_score = round(shift_ratio, 2)
            if shift_ratio > 1.5:
                shift_status = "HIGH"
            elif shift_ratio > 1.2:
                shift_status = "ELEVATED"
            else:
                shift_status = "NORMAL"
                
        parameter_metrics[param] = {
            "current_lot_median": curr_median,
            "historical_ref_median": hist_ref,
            "score": shift_score,
            "status": shift_status
        }
    
    # Lot shift status overall defaults to Leakage for top-level display compatibility
    lot_shift_status = parameter_metrics["Leakage_nA_0h"]["status"]
    lot_shift_score = parameter_metrics["Leakage_nA_0h"]["score"]

    from collections import defaultdict
    station_leakages = defaultdict(list)
    if components:
        comp_station_map = {c.component_id: c.station_id for c in components if c.station_id}
        for m in measurements:
            if m.leakage_na is not None and m.component_id in comp_station_map:
                station_leakages[comp_station_map[m.component_id]].append(m.leakage_na)

    station_means = {}
    within_station_variances = []
    for st, vals in station_leakages.items():
        if len(vals) >= 2:
            st_mean = statistics.mean(vals)
            station_means[st] = st_mean
            within_station_variances.append(statistics.variance(vals, xbar=st_mean))
        elif len(vals) == 1:
            station_means[st] = vals[0]

    within_station_residual_val = round(statistics.mean(within_station_variances), 2) if within_station_variances else 0.0
    within_station_status = "HIGH" if within_station_residual_val > 50 else ("ELEVATED" if within_station_residual_val > 20 else "NORMAL")

    cross_station_residual_val = 0.0
    cross_station_status = "NORMAL"
    station_shift_score_val = 1.0

    if len(station_means) >= 2:
        means_list = list(station_means.values())
        cross_station_residual_val = round(statistics.variance(means_list), 2)
        cross_station_status = "HIGH" if cross_station_residual_val > 30 else ("ELEVATED" if cross_station_residual_val > 15 else "NORMAL")
        min_mean = min(means_list)
        max_mean = max(means_list)
        if min_mean > 0:
            station_shift_score_val = round(max_mean / min_mean, 2)

    test_integrity_risk = "NORMAL"
    if "HIGH" in [within_station_status, cross_station_status]:
        test_integrity_risk = "HIGH"
    elif "ELEVATED" in [within_station_status, cross_station_status]:
        test_integrity_risk = "ELEVATED"
        
    distributions = {"Leakage_nA_0h": []}
    if current_leakages:
        import numpy as np
        try:
            counts, bin_edges = np.histogram(current_leakages, bins=min(10, max(1, len(set(current_leakages)))))
            for i in range(len(counts)):
                if counts[i] > 0 or True: # Include empty bins to show distribution curve
                    bin_label = f"{round(bin_edges[i], 1)}-{round(bin_edges[i+1], 1)}"
                    distributions["Leakage_nA_0h"].append({
                        "bin": bin_label,
                        "count": int(counts[i])
                    })
        except Exception:
            pass


    lot_data = {
        "lot_id": lot_id,
        "components": len(components) if components else 0,
        "device_type": device_type,
        "temperature": temperature,
        "screening_mode": "Mode A",
        "median_leakage": None,
        "engineering_limit": None,
        "pat_reference": {},
        "reference_limits": {},
        "flagged_components": list(set(flagged)),
        "lot_shift": {
            "status": lot_shift_status,
            "score": lot_shift_score,
            "current_lot_median": parameter_metrics["Leakage_nA_0h"]["current_lot_median"],
            "historical_ref_median": parameter_metrics["Leakage_nA_0h"]["historical_ref_median"],
        },
        "parameter_metrics": parameter_metrics,
        "current_lot_medians": current_lot_medians,
        "station_analysis": {
            "within_station_residual": {"status": within_station_status, "value": within_station_residual_val},
            "cross_station_residual": {"status": cross_station_status, "value": cross_station_residual_val},
            "station_shift_score": station_shift_score_val,
            "test_integrity_risk": test_integrity_risk,
        },
        "distributions": distributions,
    }

    if ref_limits:
        if "Leakage_nA_0h" in ref_limits:
            lot_data["median_leakage"] = round(ref_limits["Leakage_nA_0h"]["median"], 2)
            lot_data["engineering_limit"] = round(ref_limits["Leakage_nA_0h"]["upper"], 2)
        lot_data["reference_limits"] = {
            k: {kk: round(vv, 4) for kk, vv in v.items()}
            for k, v in ref_limits.items()
        }

    if pat_ref:
        lot_data["pat_reference"] = {
            k: {kk: round(vv, 4) for kk, vv in v.items()}
            for k, v in pat_ref.items()
        }

    station_analyses_db = db.query(StationAnalysis).filter(StationAnalysis.lot_id == lot_id).all()
    stations_data = []
    
    for st in station_analyses_db:
        st_origins = db.query(AnomalyOrigins).filter(
            AnomalyOrigins.station_id == st.station_id, 
            AnomalyOrigins.lot_id == lot_id
        ).all()
        
        affected_comps = []
        for org in st_origins:
            if org.station_status == "DISTURBANCE" or (org.evidence and org.evidence.get("station_disturbance") == 1):
                affected_comps.append({
                    "component_id": org.component_id,
                    "station_status": org.station_status,
                    "evidence": org.evidence,
                    "score": org.station_score
                })
            
        stations_data.append({
            "station_id": st.station_id,
            "integrity_status": st.integrity_status,
            "affected_component_count": st.affected_component_count,
            "within_station_evidence": st.within_station_evidence,
            "cross_station_evidence": st.cross_station_evidence,
            "parameter_evidence": st.parameter_evidence,
            "components": affected_comps
        })

    lot_data["stations"] = stations_data

    return lot_data
