"""
Prediction Engine — uses b0_models.pkl for 168h prediction with lazy loading.

B0 models expect 6 features:
  Iddq_uA_0h, Iddq_uA_24h, Leakage_nA_0h, Leakage_nA_24h, PropDelay_ns_0h, PropDelay_ns_24h

Output: predicted 168h for Iddq_uA, Leakage_nA, PropDelay_ns
"""
import logging
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from app.config import MODEL_DIR, MODEL_FILES
from app.ml.model_registry import registry
from app.inference.feature_builder import build_b0_vector

logger = logging.getLogger("sih26170.prediction_engine")

B0_TARGETS = ["Iddq_uA_168h", "Leakage_nA_168h", "PropDelay_ns_168h"]


def predict_168h(measurements: Dict[str, Any], release_after: bool = False) -> Dict[str, Any]:
    """
    Run B0 168h prediction with lazy loading.
    If release_after=True, unloads b0_models from memory after inference to conserve RAM.
    """
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

    try:
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
    finally:
        if release_after:
            registry.unload("b0_models")

    return {
        "available": True,
        "predicted_168h": predictions,
        "model_used": "B0",
        "model_version": "b0-baseline-v1.0",
        "stage": "24h",
        "warnings": warnings,
    }


def get_b_model_availability() -> Dict[str, Any]:
    """Return availability info for all B-model tiers without loading heavy models."""
    b0_file = Path(MODEL_DIR) / MODEL_FILES.get("b0_models", "")
    b0_available = registry.is_loaded("b0_models") or b0_file.exists()
    return {
        "B0": {
            "available": b0_available,
            "stage": "24h",
            "reason": None if b0_available else "Model artifact not available",
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
