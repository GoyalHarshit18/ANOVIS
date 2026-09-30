"""
Prediction Engine — uses b0_models.pkl for 168h prediction.

B0 models expect 6 features:
  Iddq_uA_0h, Iddq_uA_24h, Leakage_nA_0h, Leakage_nA_24h, PropDelay_ns_0h, PropDelay_ns_24h

Output: predicted 168h for Iddq_uA, Leakage_nA, PropDelay_ns
"""
import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.prediction_engine")

from app.inference.feature_builder import build_b0_vector

B0_TARGETS = ["Iddq_uA_168h", "Leakage_nA_168h", "PropDelay_ns_168h"]


def predict_168h(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """Run B0 168h prediction."""
    b0_models = registry.get("b0_models")
    if b0_models is None:
        return {
            "available": False,
            "predicted_168h": {},
            "model_used": "B0",
            "reason": "B0 model artifacts not loaded",
        }

    # Check required features and construct exactly the ordered vector
    vector = build_b0_vector(measurements)
    if vector is None:
        return {
            "available": False,
            "predicted_168h": {},
            "model_used": "B0",
            "reason": "Missing required features or validation failed",
        }

    # B0 models were trained with exactly these features in this order
    X = np.array([vector])

    predictions = {}
    warnings = []

    for target_name in B0_TARGETS:
        pipeline = b0_models.get(target_name)
        if pipeline is None:
            param = target_name.replace("_168h", "")
            predictions[param] = None
            warnings.append(f"No B0 pipeline for {target_name}")
            continue

        try:
            pred = pipeline.predict(X)[0]
            param = target_name.replace("_168h", "")
            predictions[param] = round(float(pred), 4)
        except Exception as e:
            param = target_name.replace("_168h", "")
            predictions[param] = None
            warnings.append(f"B0 prediction error for {target_name}: {e}")
            logger.error("B0 prediction error for %s: %s", target_name, e)

    return {
        "available": True,
        "predicted_168h": predictions,
        "model_used": "B0",
        "model_version": "b0-baseline-v1.0",
        "stage": "24h",
        "warnings": warnings,
    }


def get_b_model_availability() -> Dict[str, Any]:
    """Return availability info for all B-model tiers."""
    b0_loaded = registry.is_loaded("b0_models")
    return {
        "B0": {
            "available": b0_loaded,
            "stage": "24h",
            "reason": None if b0_loaded else "Model artifact not loaded",
        },
        "B1": {
            "available": False,
            "stage": "24h",
            "reason": "Model artifact not provided",
        },
        "B2-Early": {
            "available": False,
            "stage": "24h",
            "reason": "Model artifact not provided",
        },
        "B2-96h": {
            "available": False,
            "stage": "96h",
            "reason": "Model artifact not provided",
        },
    }
