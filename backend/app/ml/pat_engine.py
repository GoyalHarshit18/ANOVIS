"""
PAT Engine — Parameter Analysis Testing using supplied pat_reference.pkl.

Uses Modified-Z score: M_i = 0.6745 * (x_i - median) / MAD
"""
import logging
from typing import Any, Dict, Optional

import numpy as np

from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.pat_engine")

# PAT parameters map to 24h measurements
PAT_PARAMS = ["Iddq_uA_24h", "Leakage_nA_24h", "PropDelay_ns_24h"]


def compute_pat(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute PAT (Parameter Analysis Testing) evidence for a component.

    Returns dict with per-parameter PAT results and aggregate score/status.
    """
    pat_ref = registry.get("pat_reference")
    if pat_ref is None:
        return {
            "score": None,
            "status": "DATA_UNAVAILABLE",
            "details": {"reason": "PAT reference not loaded"},
        }

    results = {}
    max_modified_z = 0.0

    for param in PAT_PARAMS:
        value = measurements.get(param)
        if value is None:
            results[param] = {
                "measured": None,
                "median": pat_ref[param]["median"],
                "mad": pat_ref[param]["mad"],
                "modified_z": None,
                "status": "DATA_UNAVAILABLE",
            }
            continue

        ref = pat_ref[param]
        median = ref["median"]
        mad = ref["mad"]

        if mad == 0 or mad < 1e-15:
            modified_z = 0.0
        else:
            modified_z = 0.6745 * (value - median) / mad

        abs_z = abs(modified_z)
        max_modified_z = max(max_modified_z, abs_z)

        # Status thresholds based on Modified-Z
        if abs_z > 3.5:
            status = "HIGH"
        elif abs_z > 2.5:
            status = "ELEVATED"
        else:
            status = "NORMAL"

        results[param] = {
            "measured": float(value),
            "median": float(median),
            "mad": float(mad),
            "modified_z": float(modified_z),
            "abs_modified_z": float(abs_z),
            "status": status,
        }

    # Aggregate PAT score: scale modified-Z to 0-100
    pat_score = min(100.0, max_modified_z * 20.0)  # 5.0 -> 100

    if pat_score > 70:
        overall_status = "HIGH"
    elif pat_score > 40:
        overall_status = "ELEVATED"
    else:
        overall_status = "NORMAL"

    return {
        "score": round(pat_score, 1),
        "status": overall_status,
        "details": results,
    }
