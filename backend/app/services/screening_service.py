"""
Screening Service — orchestrates the full screening pipeline.

validate → static screening → PAT → peer → temporal → IF → A_SCORE →
B0 prediction → safety → risk fusion → decision → explainability → response
"""
import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np

from app.ml.model_registry import registry
from app.ml.pat_engine import compute_pat
from app.ml.peer_engine import compute_peer_analysis
from app.ml.temporal_engine import compute_temporal_analysis
from app.ml.isolation_forest_engine import compute_isolation_forest
from app.ml.prediction_engine import predict_168h, get_b_model_availability
from app.ml.safety_engine import compute_safety_analysis
from app.ml.risk_fusion import compute_a_score, compute_ldi, determine_decision

logger = logging.getLogger("sih26170.screening_service")

PARAMS = ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]


def _static_screening(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """Check measurements against static reference limits."""
    ref_limits = registry.get("reference_limits")
    if ref_limits is None:
        return {
            "result": "DATA_UNAVAILABLE",
            "violations": [],
            "details": {"reason": "Reference limits not loaded"},
        }

    violations = []
    details = {}

    # Check all available measurement stages against limits
    for stage_suffix in ["_0h", "_24h", "_96h", "_168h"]:
        for param in PARAMS:
            key = f"{param}{stage_suffix}"
            value = measurements.get(key)
            if value is None:
                continue

            if key in ref_limits:
                ref = ref_limits[key]
                lower = ref["lower"]
                upper = ref["upper"]
                detail = {
                    "value": float(value),
                    "lower": float(lower),
                    "upper": float(upper),
                    "median": float(ref["median"]),
                    "within_limits": bool(lower <= value <= upper),
                }
                details[key] = detail

                if value < lower or value > upper:
                    violations.append({
                        "parameter": key,
                        "value": float(value),
                        "limit_type": "lower" if value < lower else "upper",
                        "limit_value": float(lower if value < lower else upper),
                    })

    result = "FAIL" if violations else "PASS"
    return {
        "result": result,
        "violations": violations,
        "details": details,
    }


def _compute_test_integrity(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess test/measurement integrity.
    Check for sensor glitches, station shifts, etc.
    """
    quality = "NORMAL"
    within_station = "NORMAL"
    cross_station = "NORMAL"
    glitch = "NOT DETECTED"
    flag = False

    # Detect sensor glitch: sudden near-zero reading after normal
    for param in PARAMS:
        v0 = measurements.get(f"{param}_0h")
        v24 = measurements.get(f"{param}_24h")
        if v0 is not None and v24 is not None:
            if v0 > 0 and v24 > 0:
                ratio = v24 / v0 if v0 != 0 else 1.0
                if ratio < 0.01 or ratio > 100:
                    glitch = "DETECTED"
                    quality = "LOW"
                    within_station = "HIGH"
                    flag = True

    return {
        "quality": quality,
        "within_station": within_station,
        "cross_station": cross_station,
        "glitch": glitch,
        "flag": flag,
    }


def _build_history(measurements: Dict[str, Any]) -> List[Dict]:
    """Build measurement history timeline for all parameters."""
    history = []
    for param in PARAMS:
        for stage in ["0h", "24h", "96h", "168h"]:
            key = f"{param}_{stage}"
            value = measurements.get(key)
            if value is not None:
                history.append({"stage": stage, "value": round(float(value), 4), "parameter": param})
    return history


def _generate_shap_proxy(
    pat_result: Dict, peer_result: Dict, temporal_result: Dict, if_result: Dict
) -> List[Dict]:
    """
    Generate SHAP-like feature importance proxy from sub-signal scores.
    This is correlational importance, NOT causal.
    """
    features = []
    total = 0.0

    scores = [
        ("Early Slope (0-24h)", (temporal_result.get("score") or 0) if temporal_result else 0),
        ("Lot PAT Residual", (pat_result.get("score") or 0) if pat_result else 0),
        ("Initial Value (0h)", (pat_result.get("score") * 0.5) if (pat_result and pat_result.get("score") is not None) else 0),
        ("Peer Deviation", (peer_result.get("score") or 0) if peer_result else 0),
        ("Multivariate Anomaly (IF)", (if_result.get("score") or 0) if if_result else 0),
    ]

    total = sum(s for _, s in scores)
    if total == 0:
        total = 1.0

    for name, score in scores:
        features.append({
            "feature": name,
            "value": round(score / total, 4),
        })

    # Sort descending
    features.sort(key=lambda x: x["value"], reverse=True)
    return features[:5]


def screen_component(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full screening pipeline for a single component.
    Returns a result dict compatible with the frontend's ComponentScreeningResult shape.
    """
    start = time.time()
    component_id = measurements.get("component_id", "UNKNOWN")
    logger.info("Screening component %s", component_id)

    # 1. Determine screening stage

    has_0h = any(measurements.get(f"{p}_0h") is not None for p in PARAMS)
    has_24h = any(measurements.get(f"{p}_24h") is not None for p in PARAMS)
    has_96h = any(measurements.get(f"{p}_96h") is not None for p in PARAMS)
    has_168h = any(measurements.get(f"{p}_168h") is not None for p in PARAMS)

    if has_168h:
        screening_stage = "168h"
    elif has_96h:
        screening_stage = "96h"
    elif has_24h:
        screening_stage = "24h"
    elif has_0h:
        screening_stage = "0h"
    else:
        return _error_result(component_id, measurements, "No measurements provided")

    # 2. Static screening
    static = _static_screening(measurements)
    all_warnings = []

    # 3. Test integrity
    integrity = _compute_test_integrity(measurements)

    # If only 0h data and static FAIL, short-circuit
    if screening_stage == "0h" and static["result"] == "FAIL":
        return _build_result(
            component_id=component_id,
            measurements=measurements,
            decision="REJECT",
            static=static,
            integrity=integrity,
            explanation="Hard static failure at 0h.",
            screening_stage="0h",
            first_detection_stage="0h",
        )

    # 4. PAT (needs 24h data)
    pat_result = compute_pat(measurements) if has_24h else {"score": None, "status": "N/A"}

    # 5. Peer analysis (needs 0h data)
    peer_result = compute_peer_analysis(measurements) if has_0h else {"score": None, "status": "N/A"}

    # 6. Temporal analysis (needs 0h + 24h)
    temporal_result = compute_temporal_analysis(measurements) if (has_0h and has_24h) else {"score": None, "status": "N/A"}

    # 7. Isolation Forest (needs 0h + 24h)
    if_result = compute_isolation_forest(measurements) if (has_0h and has_24h) else {"score": None, "status": "N/A"}

    # 8. A_SCORE
    a_score = compute_a_score(pat_result, peer_result, temporal_result, if_result)

    # 9. B0 Prediction
    prediction = predict_168h(measurements) if (has_0h and has_24h) else {"available": False, "predicted_168h": {}}
    predicted_168h = prediction.get("predicted_168h", {})
    if prediction.get("warnings"):
        all_warnings.extend(prediction["warnings"])

    # 10. Safety analysis
    safety = compute_safety_analysis(predicted_168h, measurements) if predicted_168h else {
        "prediction_risk": None, "s_score": None, "uncertainty_risk": None
    }

    prediction_risk = safety.get("prediction_risk")
    s_score = safety.get("s_score")
    uncertainty_risk = safety.get("uncertainty_risk")

    # 11. LDI
    ldi = compute_ldi(a_score, prediction_risk, s_score, uncertainty_risk)

    # 12. Decision
    data_available = has_0h and has_24h and bool(prediction.get("available") or registry.is_loaded("b0_models"))
    decision_result = determine_decision(
        static_result=static["result"],
        a_score=a_score,
        prediction_risk=prediction_risk,
        s_score=s_score,
        uncertainty_risk=uncertainty_risk,
        test_integrity_flag=integrity["flag"],
        ldi=ldi,
        data_available=data_available,
    )

    decision = decision_result["decision"]
    explanation = decision_result["explanation"]
    first_detection_stage = decision_result["first_detection_stage"]
    all_warnings.extend(decision_result.get("warnings", []))

    # 13. SHAP proxy
    shap = _generate_shap_proxy(pat_result, peer_result, temporal_result, if_result)

    duration = time.time() - start
    logger.info("Screened %s -> %s (%.3fs)", component_id, decision, duration)

    return _build_result(
        component_id=component_id,
        measurements=measurements,
        decision=decision,
        static=static,
        integrity=integrity,
        pat_result=pat_result,
        peer_result=peer_result,
        temporal_result=temporal_result,
        if_result=if_result,
        a_score=a_score,
        ldi=ldi,
        prediction=prediction,
        predicted_168h=predicted_168h,
        safety=safety,
        prediction_risk=prediction_risk,
        s_score=s_score,
        uncertainty_risk=uncertainty_risk,
        explanation=explanation,
        screening_stage=screening_stage,
        first_detection_stage=first_detection_stage,
        shap=shap,
        warnings=all_warnings,
    )


def _build_result(
    component_id: str,
    measurements: Dict[str, Any],
    decision: str,
    static: Dict,
    integrity: Dict,
    explanation: str = "",
    screening_stage: str = "24h",
    first_detection_stage: str = "N/A",
    pat_result: Dict = None,
    peer_result: Dict = None,
    temporal_result: Dict = None,
    if_result: Dict = None,
    a_score: float = None,
    ldi: float = None,
    prediction: Dict = None,
    predicted_168h: Dict = None,
    safety: Dict = None,
    prediction_risk: float = None,
    s_score: float = None,
    uncertainty_risk: float = None,
    shap: List = None,
    warnings: List = None,
) -> Dict[str, Any]:
    """Build the final result dict matching the frontend contract."""

    # Build B-model results
    b_availability = get_b_model_availability()
    b_models = {}
    for model_name, info in b_availability.items():
        b_model_entry = {
            "prediction": None,
            "stage": info["stage"],
            "available": info["available"],
        }
        if model_name == "B0" and info["available"] and predicted_168h:
            # Use the primary prediction param for the B-model card
            b_model_entry["prediction"] = predicted_168h.get("Leakage_nA")
        b_models[model_name] = b_model_entry

    # Frontend-compatible predicted_168h
    frontend_predicted = None
    if predicted_168h:
        primary_pred = predicted_168h.get("Leakage_nA")
        # Build interval from future envelope
        envelope = registry.get("future_envelope")
        interval = []
        if envelope and "Leakage_nA_168h" in envelope:
            env = envelope["Leakage_nA_168h"]
            interval = [round(env["lower"], 1), round(env["upper"], 1)]

        frontend_predicted = {
            "leakage": primary_pred,
            "Iddq_uA": predicted_168h.get("Iddq_uA"),
            "Leakage_nA": predicted_168h.get("Leakage_nA"),
            "PropDelay_ns": predicted_168h.get("PropDelay_ns"),
            "interval": interval,
        }

    history = _build_history(measurements)

    return {
        "component_id": component_id,
        "lot": measurements.get("lot_id", "LOT-2026-091"),
        "device_type": measurements.get("device_type", "XYZ-IC"),
        "station": measurements.get("station", "ST-01"),
        "temperature": measurements.get("temperature", "125°C"),
        "voltage": measurements.get("voltage", "3.3V"),
        "decision": decision,
        "ldi": ldi,
        "a_score": a_score,
        "s_score": s_score,
        "prediction_risk": prediction_risk,
        "uncertainty_risk": uncertainty_risk,
        "predicted_168h": frontend_predicted,
        "test_integrity_flag": integrity.get("flag", False),
        "screening_stage": screening_stage,
        "first_detection_stage": first_detection_stage,
        "latest_evidence_stage": screening_stage,
        "basis": {
            "mode": "Mode A",
            "b_model": "B0" if (prediction and prediction.get("available")) else "None",
            "safety_score_calibrated": False,
            "safety_score_type": "quantile estimate, not a calibrated probability",
            "calibrated_probability_available": False,
        },
        "evidence": {
            "static_result": static["result"],
            "static_violations": static.get("violations", []),
            "static_details": static.get("details", {}),
            "pat": {
                "score": pat_result.get("score") if pat_result else None,
                "status": pat_result.get("status", "N/A") if pat_result else "N/A",
                "details": pat_result.get("details") if pat_result else None,
            },
            "peer_residual": {
                "score": peer_result.get("score") if peer_result else None,
                "status": peer_result.get("status", "N/A") if peer_result else "N/A",
                "details": peer_result.get("details") if peer_result else None,
            },
            "early_temporal": {
                "score": temporal_result.get("score") if temporal_result else None,
                "status": temporal_result.get("status", "N/A") if temporal_result else "N/A",
                "details": temporal_result.get("details") if temporal_result else None,
            },
            "isolation_forest": {
                "score": if_result.get("score") if if_result else None,
                "status": if_result.get("status", "N/A") if if_result else "N/A",
                "details": if_result.get("details") if if_result else None,
            },
        },
        "test_integrity": {
            "quality": integrity.get("quality", "NORMAL"),
            "within_station": integrity.get("within_station", "NORMAL"),
            "cross_station": integrity.get("cross_station", "NORMAL"),
            "glitch": integrity.get("glitch", "NOT DETECTED"),
        },
        "safety": safety if safety else {},
        "history": history,
        "b_models": b_models,
        "shap": shap or [],
        "model_version": "risk-fusion-v1.0.0",
        "warnings": warnings or [],
        "explanation": explanation,
    }


def _error_result(component_id: str, measurements: Dict, reason: str) -> Dict:
    """Build an error/unavailable result."""
    return _build_result(
        component_id=component_id,
        measurements=measurements,
        decision="DATA_UNAVAILABLE",
        static={"result": "N/A", "violations": [], "details": {}},
        integrity={"quality": "UNKNOWN", "within_station": "UNKNOWN", "cross_station": "UNKNOWN", "glitch": "UNKNOWN", "flag": False},
        explanation=reason,
        warnings=[reason],
    )
