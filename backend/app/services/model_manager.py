"""
Unified ModelManager Service for Anovis Backend.

Loads ML artifacts once at startup into memory, provides high-level methods
for 96h anomaly classification, 168h parameter regression, and metadata inspection.
"""
import logging
from typing import Any, Dict, List, Optional

from app.ml.model_registry import registry, ModelStatus
from app.services.explainability_service import explain_component_96h, get_global_shap_importance
from app.ml.prediction_engine import predict_168h

logger = logging.getLogger("sih26170.model_manager")


class ModelManager:
    """Production Model Manager singleton for in-memory ML inference."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    def load_models(self) -> Dict[str, Any]:
        """Loads all model artifacts once and warms up initial explainers."""
        logger.info("Initializing ModelManager: loading artifacts into memory...")
        registry.load_all()
        report = registry.health_report()
        loaded = sum(1 for v in report.values() if v["status"] == "loaded")
        logger.info("ModelManager loaded %d / %d model artifacts.", loaded, len(report))
        return report

    def is_ready(self) -> bool:
        """Verifies if core production models are loaded and ready."""
        # Core models: 96h anomaly classifier and regression models (b0_models or B0_IDDQ)
        catboost_ready = registry.is_loaded("component_96h_classifier")
        regression_ready = registry.is_loaded("b0_models") or (
            registry.is_loaded("B0_IDDQ") and registry.is_loaded("B0_Leakage") and registry.is_loaded("B0_Delay")
        )
        return bool(catboost_ready and regression_ready)

    def predict_anomaly(
        self,
        measurements: Dict[str, Any],
        legacy_risks: Optional[Dict[str, float]] = None,
        threshold: float = 0.50
    ) -> Dict[str, Any]:
        """
        Runs 96h CatBoost anomaly detection.
        Returns probability, status, and SHAP attribution.
        """
        return explain_component_96h(measurements, legacy_risks=legacy_risks, threshold=threshold)

    def predict_168h(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs 168h regression predictions for IDDQ, Leakage, and Delay.
        Uses 0h and 24h burn-in measurements.
        """
        return predict_168h(measurements)

    def get_model_metadata(self) -> Dict[str, Any]:
        """Returns metadata about loaded models, versions, and feature expectations."""
        info = registry.model_info()
        info["ready"] = self.is_ready()
        info["anomaly_model"] = "CatBoost 96h Anomaly Classifier v1.0"
        info["regression_model"] = "B-Series 168h Parameter Regressors v1.0"
        info["anomaly_threshold"] = 0.50
        return info


model_manager = ModelManager()
