"""
SHAP Explainability Service for 96h Semiconductor Anomaly Classification.

Provides individual component SHAP explanations, reconstruction verification,
positive/negative feature contributions, and global feature importance ranking.
"""
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from app.config import MODEL_DIR
from app.ml.model_registry import registry
from app.inference.model_contracts import COMPONENT_96H_FEATURES
from app.inference.feature_builder import build_b2_96h_vector
from app.services.limit_analysis_service import analyze_engineering_limits, analyze_measurement_trends

logger = logging.getLogger("sih26170.explainability_service")

# Global in-memory cache for model, explainer, and global SHAP summary
_EXPLAINER_CACHE: Dict[str, Any] = {}
_GLOBAL_SHAP_CACHE: Optional[Dict[str, Any]] = None


def _get_model_and_explainer() -> Tuple[Any, Any, Any]:
    """
    Retrieves or initializes the 96h anomaly classifier pipeline, imputer, classifier, and SHAP explainer.
    Caches instances to avoid redundant load overhead.
    """
    if "pipeline" in _EXPLAINER_CACHE and "explainer" in _EXPLAINER_CACHE:
        return (
            _EXPLAINER_CACHE["pipeline"],
            _EXPLAINER_CACHE["imputer"],
            _EXPLAINER_CACHE["explainer"],
        )

    import shap
    pipe = registry.get("component_96h_classifier")
    if not pipe:
        filepath = Path(MODEL_DIR) / "component_96h_classifier.pkl"
        if filepath.exists():
            pipe = joblib.load(filepath)
            logger.info("Loaded component_96h_classifier directly from %s", filepath)

    if not pipe:
        raise RuntimeError("component_96h_classifier artifact unavailable")

    imputer = pipe.named_steps["imputer"]
    if not hasattr(imputer, "_fill_dtype"):
        imputer._fill_dtype = getattr(imputer, "_fit_dtype", float)

    clf = pipe.named_steps["classifier"]
    explainer = shap.TreeExplainer(clf)

    _EXPLAINER_CACHE["pipeline"] = pipe
    _EXPLAINER_CACHE["imputer"] = imputer
    _EXPLAINER_CACHE["explainer"] = explainer

    logger.info("Initialized SHAP TreeExplainer for component_96h_classifier")
    return pipe, imputer, explainer


def explain_component_96h(
    measurements: Dict[str, Any],
    legacy_risks: Optional[Dict[str, float]] = None,
    threshold: float = 0.50
) -> Dict[str, Any]:
    """
    Computes individual SHAP explanation for a component based on 96h classifier inputs.
    Returns authoritative model outputs, feature values, SHAP attribution breakdown,
    limit assessments, and trends.
    """
    if legacy_risks is None:
        legacy_risks = {
            "PAT_Risk": 0.0,
            "Peer_Risk": 0.0,
            "Temporal_Risk": 0.0,
            "IF_Risk": 0.0,
        }

    component_id = str(measurements.get("component_id", "UNKNOWN"))
    lot_id = str(measurements.get("lot_id", measurements.get("lot", "LOT-UNKNOWN")))

    # Build feature vector
    raw_vector = build_b2_96h_vector(measurements, legacy_risks)
    if not raw_vector:
        # Fallback vector with NaNs filled
        raw_vector = [np.nan] * len(COMPONENT_96H_FEATURES)

    feature_names = list(COMPONENT_96H_FEATURES)
    df_raw = pd.DataFrame([raw_vector], columns=feature_names)

    pipe, imputer, explainer = _get_model_and_explainer()

    # Impute missing values
    x_imp = imputer.transform(df_raw)

    # Calculate model output probability for Class 1 (Anomaly)
    probabilities = pipe.predict_proba(df_raw)[0]
    anomaly_probability = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])
    is_anomaly = bool(anomaly_probability >= threshold)
    predicted_status = "ANOMALY" if is_anomaly else "NORMAL"

    # Compute SHAP values
    raw_shap = explainer.shap_values(x_imp)
    
    # Handle array output shape from TreeExplainer
    if isinstance(raw_shap, list):
        class1_shap = np.array(raw_shap[1])[0]
    elif isinstance(raw_shap, np.ndarray) and len(raw_shap.shape) == 3:
        class1_shap = raw_shap[0, :, 1]
    else:
        class1_shap = np.array(raw_shap)[0]

    # Base value (expected probability for class 1)
    exp_val = explainer.expected_value
    base_value = float(exp_val[1]) if isinstance(exp_val, (list, np.ndarray)) and len(exp_val) > 1 else float(exp_val)

    # Verification: base_value + sum(class1_shap) ≈ anomaly_probability
    reconstructed_value = float(base_value + np.sum(class1_shap))
    reconstruction_diff = abs(reconstructed_value - anomaly_probability)

    # Pair features with values and SHAP scores
    feature_attributions = []
    feature_val_map = {}

    for name, val, shap_val in zip(feature_names, raw_vector, class1_shap):
        actual_val = None if (val is None or (isinstance(val, float) and np.isnan(val))) else float(val)
        s_val = float(shap_val)
        feature_val_map[name] = actual_val
        
        feature_attributions.append({
            "feature": name,
            "actual_value": actual_val,
            "shap_value": round(s_val, 6),
            "abs_shap_value": round(abs(s_val), 6),
            "effect": "INCREASES_ANOMALY_RISK" if s_val > 0 else ("DECREASES_ANOMALY_RISK" if s_val < 0 else "NEUTRAL")
        })

    # Sort attributions
    top_positive = [f for f in sorted(feature_attributions, key=lambda x: x["shap_value"], reverse=True) if f["shap_value"] > 0][:8]
    top_negative = [f for f in sorted(feature_attributions, key=lambda x: x["shap_value"]) if f["shap_value"] < 0][:8]
    top_overall = sorted(feature_attributions, key=lambda x: x["abs_shap_value"], reverse=True)[:10]

    # Limit and Trend Analysis
    limit_analysis = analyze_engineering_limits(measurements)
    measurement_trends = analyze_measurement_trends(measurements)

    return {
        "component_id": component_id,
        "lot_id": lot_id,
        "anomaly_probability": round(anomaly_probability, 4),
        "threshold": threshold,
        "predicted_status": predicted_status,
        "base_value": round(base_value, 4),
        "reconstructed_value": round(reconstructed_value, 4),
        "reconstruction_diff": round(reconstruction_diff, 8),
        "output_unit": "Probability (0.0 to 1.0)",
        "model_version": "catboost-96h-v1.0",
        "feature_attributions": feature_attributions,
        "top_positive_contributors": top_positive,
        "top_negative_contributors": top_negative,
        "top_overall_contributors": top_overall,
        "feature_values": feature_val_map,
        "limit_analysis": limit_analysis,
        "measurement_trends": measurement_trends,
    }


def get_global_shap_importance(sample_records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Returns global feature importance by computing mean absolute SHAP values across a representative dataset sample.
    Caches the output to prevent recomputation on every dashboard request.
    """
    global _GLOBAL_SHAP_CACHE
    if _GLOBAL_SHAP_CACHE is not None and sample_records is None:
        return _GLOBAL_SHAP_CACHE

    pipe, imputer, explainer = _get_model_and_explainer()
    feature_names = list(COMPONENT_96H_FEATURES)

    # Try loading LOT_00.csv for real empirical global SHAP calculation if no sample passed
    df_data = None
    if sample_records:
        records_vector = []
        for r in sample_records:
            vec = build_b2_96h_vector(r, {"PAT_Risk": 0.0, "Peer_Risk": 0.0, "Temporal_Risk": 0.0, "IF_Risk": 0.0})
            if vec:
                records_vector.append(vec)
        if records_vector:
            df_data = pd.DataFrame(records_vector, columns=feature_names)

    if df_data is None:
        lot00_path = Path(MODEL_DIR).parent / "LOT_00.csv"
        if lot00_path.exists():
            try:
                raw_csv = pd.read_csv(lot00_path)
                records = raw_csv.to_dict(orient="records")
                records_vector = []
                for r in records[:30]: # Sample 30 components for rapid calculation
                    v = build_b2_96h_vector(r, {"PAT_Risk": 0.0, "Peer_Risk": 0.0, "Temporal_Risk": 0.0, "IF_Risk": 0.0})
                    if v:
                        records_vector.append(v)
                if records_vector:
                    df_data = pd.DataFrame(records_vector, columns=feature_names)
            except Exception as e:
                logger.warning("Failed to load LOT_00.csv for global SHAP: %s", e)

    # Fallback mock/synthetic reference array if no dataset file present
    if df_data is None or len(df_data) == 0:
        syn_rows = []
        for _ in range(20):
            syn_rows.append([0.0] * len(feature_names))
        df_data = pd.DataFrame(syn_rows, columns=feature_names)

    x_imp = imputer.transform(df_data)
    raw_shap = explainer.shap_values(x_imp)

    if isinstance(raw_shap, list):
        class1_shap = np.array(raw_shap[1])
    elif isinstance(raw_shap, np.ndarray) and len(raw_shap.shape) == 3:
        class1_shap = raw_shap[:, :, 1]
    else:
        class1_shap = np.array(raw_shap)

    # Mean absolute SHAP per feature across samples
    mean_abs_shap = np.mean(np.abs(class1_shap), axis=0)

    feature_ranking = []
    for name, score in zip(feature_names, mean_abs_shap):
        feature_ranking.append({
            "feature": name,
            "mean_abs_shap": round(float(score), 6),
            "percentage": 0.0
        })

    # Sort descending
    feature_ranking.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
    total_score = sum(f["mean_abs_shap"] for f in feature_ranking) or 1.0

    for f in feature_ranking:
        f["percentage"] = round((f["mean_abs_shap"] / total_score) * 100, 2)

    result = {
        "model_name": "CatBoost 96h Anomaly Classifier",
        "sample_size": len(df_data),
        "total_features": len(feature_names),
        "output_unit": "Probability Attribution (SHAP)",
        "global_importance": feature_ranking[:15], # Top 15 features
        "all_importance": feature_ranking,
    }

    if sample_records is None:
        _GLOBAL_SHAP_CACHE = result

    return result
