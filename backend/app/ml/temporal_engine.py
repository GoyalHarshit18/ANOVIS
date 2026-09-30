"""
Temporal Analysis Engine — uses temporal_reference.pkl and drift_reference.pkl.

Computes:
- Absolute drift (0→24h)
- Relative drift (0→24h) 
- Temporal anomaly evidence using reference median/scale
"""
import logging
from typing import Any, Dict

import numpy as np

from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.temporal_engine")

PARAMS = ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]


def compute_temporal_analysis(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """Compute temporal drift evidence for 0→24h."""
    temp_ref = registry.get("temporal_reference")
    drift_ref = registry.get("drift_reference")

    if temp_ref is None or drift_ref is None:
        return {
            "score": None,
            "status": "DATA_UNAVAILABLE",
            "details": {"reason": "Temporal/drift reference not loaded"},
        }

    results = {}
    max_z = 0.0

    for param in PARAMS:
        val_0h = measurements.get(f"{param}_0h")
        val_24h = measurements.get(f"{param}_24h")

        if val_0h is None or val_24h is None:
            results[param] = {
                "drift_0_24h": None,
                "relative_drift": None,
                "early_slope": None,
                "status": "DATA_UNAVAILABLE",
            }
            continue

        # Absolute drift
        drift = val_24h - val_0h

        # Relative drift
        if abs(val_0h) < 1e-15:
            relative_drift = 0.0
        else:
            relative_drift = drift / val_0h

        # Early slope (per hour)
        early_slope = drift / 24.0

        # Temporal anomaly: compare relative drift to reference
        ref_key = f"{param}_relative_drift_0_24"
        if ref_key in temp_ref:
            ref = temp_ref[ref_key]
            ref_median = ref["median"]
            ref_scale = ref["scale"]
            if ref_scale > 1e-15:
                z_score = abs(relative_drift - ref_median) / ref_scale
            else:
                z_score = 0.0
        else:
            z_score = 0.0

        # Also check absolute drift against drift_reference
        if param in drift_ref:
            d_ref = drift_ref[param]
            d_median = d_ref["median"]
            d_scale = d_ref["scale"]
            if d_scale > 1e-15:
                drift_z = abs(drift - d_median) / d_scale
            else:
                drift_z = 0.0
        else:
            drift_z = 0.0

        combined_z = max(z_score, drift_z)
        max_z = max(max_z, combined_z)

        if combined_z > 3.5:
            status = "HIGH"
        elif combined_z > 2.5:
            status = "ELEVATED"
        else:
            status = "NORMAL"

        results[param] = {
            "drift_0_24h": round(float(drift), 6),
            "relative_drift": round(float(relative_drift), 6),
            "early_slope": round(float(early_slope), 6),
            "z_score": round(float(combined_z), 4),
            "status": status,
        }

    # Aggregate temporal score
    temporal_score = min(100.0, max_z * 20.0)

    if temporal_score > 70:
        overall_status = "HIGH"
    elif temporal_score > 40:
        overall_status = "ELEVATED"
    else:
        overall_status = "NORMAL"

    return {
        "score": round(temporal_score, 1),
        "status": overall_status,
        "details": results,
    }
