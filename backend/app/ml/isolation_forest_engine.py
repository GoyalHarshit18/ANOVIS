"""
Isolation Forest Engine — uses isolation_forest.pkl, if_scaler.pkl, inference_config.pkl.

Feature generation pipeline:
1. 6 raw features: Iddq_uA_0h/24h, Leakage_nA_0h/24h, PropDelay_ns_0h/24h
2. 3 slope features: *_slope_0_24
3. 3 relative drift features: *_relative_drift_0_24
Total: 12 features → if_scaler → isolation_forest → anomaly score
"""
import logging
from typing import Any, Dict

import numpy as np

from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.isolation_forest_engine")

RAW_FEATURES = [
    "Iddq_uA_0h", "Iddq_uA_24h",
    "Leakage_nA_0h", "Leakage_nA_24h",
    "PropDelay_ns_0h", "PropDelay_ns_24h",
]

SLOPE_FEATURES = [
    "Iddq_uA_slope_0_24",
    "Leakage_nA_slope_0_24",
    "PropDelay_ns_slope_0_24",
]

DRIFT_FEATURES = [
    "Iddq_uA_relative_drift_0_24",
    "Leakage_nA_relative_drift_0_24",
    "PropDelay_ns_relative_drift_0_24",
]

ALL_FEATURES = RAW_FEATURES + SLOPE_FEATURES + DRIFT_FEATURES

PARAMS = ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]


def _generate_features(measurements: Dict[str, Any]) -> np.ndarray:
    """Generate the 12-feature vector from raw 0h+24h measurements."""
    features = []

    # Raw features
    for f in RAW_FEATURES:
        v = measurements.get(f)
        if v is None:
            return None
        features.append(float(v))

    # Slope features (value_24h - value_0h) / 24
    for param in PARAMS:
        v0 = measurements.get(f"{param}_0h")
        v24 = measurements.get(f"{param}_24h")
        if v0 is None or v24 is None:
            return None
        slope = (v24 - v0) / 24.0
        features.append(float(slope))

    # Relative drift features
    for param in PARAMS:
        v0 = measurements.get(f"{param}_0h")
        v24 = measurements.get(f"{param}_24h")
        if v0 is None or v24 is None:
            return None
        if abs(v0) < 1e-15:
            rel_drift = 0.0
        else:
            rel_drift = (v24 - v0) / v0
        features.append(float(rel_drift))

    return np.array(features).reshape(1, -1)


def compute_isolation_forest(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """Run Isolation Forest inference."""
    iforest = registry.get("isolation_forest")
    scaler = registry.get("if_scaler")
    config = registry.get("inference_config")

    if iforest is None or scaler is None:
        return {
            "score": None,
            "status": "DATA_UNAVAILABLE",
            "details": {"reason": "Isolation Forest or scaler not loaded"},
        }

    X = _generate_features(measurements)
    if X is None:
        return {
            "score": None,
            "status": "DATA_UNAVAILABLE",
            "details": {"reason": "Missing required 0h/24h measurements"},
        }

    try:
        # Scale
        X_scaled = scaler.transform(X)

        # Anomaly score (negative = anomaly)
        raw_score = iforest.decision_function(X_scaled)[0]
        prediction = iforest.predict(X_scaled)[0]  # 1 = normal, -1 = anomaly

        # Get threshold from config
        if_threshold = config.get("if_threshold", 0.0) if config else 0.0

        # Convert to evidence score (0-100 scale)
        # Lower decision_function → more anomalous
        # Threshold is the boundary; values below are anomalies
        # Map: at threshold → 50, well below threshold → 100, well above → 0
        if abs(if_threshold) < 1e-15:
            normalized = 50.0
        else:
            deviation = (if_threshold - raw_score) / abs(if_threshold)
            normalized = 50.0 + deviation * 50.0

        if_score = max(0.0, min(100.0, normalized))

        if if_score > 70:
            status = "HIGH"
        elif if_score > 40:
            status = "ELEVATED"
        else:
            status = "NORMAL"

        return {
            "score": round(if_score, 1),
            "status": status,
            "details": {
                "raw_score": round(float(raw_score), 6),
                "prediction": int(prediction),
                "threshold": float(if_threshold),
                "is_anomaly": bool(prediction == -1),
            },
        }

    except Exception as e:
        logger.error("Isolation Forest inference failed: %s", e)
        return {
            "score": None,
            "status": "ERROR",
            "details": {"reason": str(e)},
        }
