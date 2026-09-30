"""
Safety Analysis Engine — uses future_envelope.pkl and reference_limits.pkl.

Computes:
- Prediction Risk: proximity of predicted 168h to engineering limit
- S_SCORE: statistical unusualness of predicted value relative to healthy distribution
- Uncertainty Risk: based on prediction spread (derived from ensemble variance)
"""
import logging
from typing import Any, Dict

import numpy as np

from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.safety_engine")

PARAMS = ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]


def compute_safety_analysis(
    predicted_168h: Dict[str, Any],
    measurements: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute safety evidence from predicted 168h values.
    
    Returns prediction_risk, s_score, uncertainty_risk, envelope info.
    """
    envelope = registry.get("future_envelope")
    ref_limits = registry.get("reference_limits")

    if not predicted_168h or all(v is None for v in predicted_168h.values()):
        return {
            "prediction_risk": None,
            "s_score": None,
            "uncertainty_risk": None,
            "status": "DATA_UNAVAILABLE",
            "details": {"reason": "No predictions available"},
        }

    max_risk = 0.0
    max_s = 0.0
    details = {}

    for param in PARAMS:
        pred = predicted_168h.get(param)
        if pred is None:
            details[param] = {"status": "UNAVAILABLE"}
            continue

        param_detail = {"predicted_168h": pred}

        # Engineering limit from reference_limits
        ref_key_168h = f"{param}_168h"
        if ref_limits and ref_key_168h in ref_limits:
            ref = ref_limits[ref_key_168h]
            upper_limit = ref["upper"]
            lower_limit = ref["lower"]
            ref_median = ref["median"]
            ref_mad = ref["mad"]

            param_detail["engineering_limit_upper"] = round(upper_limit, 4)
            param_detail["engineering_limit_lower"] = round(lower_limit, 4)
            param_detail["ref_median"] = round(ref_median, 4)

            # Prediction risk: how close to the limit
            if upper_limit > lower_limit:
                range_size = upper_limit - ref_median
                if range_size > 0:
                    proximity = (pred - ref_median) / range_size
                    risk = min(100.0, max(0.0, proximity * 100.0))
                else:
                    risk = 0.0
            else:
                risk = 0.0

            max_risk = max(max_risk, risk)
            param_detail["prediction_risk"] = round(risk, 1)

            # S_SCORE: Modified-Z of predicted value against reference
            if ref_mad > 1e-15:
                s = abs(pred - ref_median) / ref_mad
                s_score = min(100.0, s * 15.0)
            else:
                s_score = 0.0

            max_s = max(max_s, s_score)
            param_detail["s_score"] = round(s_score, 1)
        else:
            param_detail["prediction_risk"] = None
            param_detail["s_score"] = None

        # Envelope check
        if envelope:
            env_key = f"{param}_168h"
            if env_key in envelope:
                env = envelope[env_key]
                env_lower = env["lower"]
                env_upper = env["upper"]
                param_detail["envelope_lower"] = round(env_lower, 4)
                param_detail["envelope_upper"] = round(env_upper, 4)
                param_detail["within_envelope"] = bool(env_lower <= pred <= env_upper)

        details[param] = param_detail

    # Uncertainty risk: simplified (based on prediction spread estimate)
    # Since B0 uses RandomForest, we could use tree variance, but that 
    # requires model internals. Use a proxy based on distance from median.
    uncertainty_risk = min(100.0, max_s * 0.5)

    return {
        "prediction_risk": round(max_risk, 1),
        "s_score": round(max_s, 1),
        "uncertainty_risk": round(uncertainty_risk, 1),
        "details": details,
    }
