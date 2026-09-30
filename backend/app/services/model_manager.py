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
        """
        Models are loaded lazily on first inference request.
        No heavy model is loaded during application startup.
        """
        logger.info(
            "ModelManager initialized — models will be loaded on demand."
        )

        return registry.health_report()

    def is_ready(self) -> bool:
        """
        The application is ready when the required production
        model artifacts exist. Models themselves are loaded lazily
        on the first inference request.
        """
        from pathlib import Path
        from app.config import MODEL_DIR, MODEL_FILES

        required_models = [
            "component_96h_classifier",
            "b0_models",
        ]

        for key in required_models:
            filename = MODEL_FILES.get(key)

            if not filename:
                return False

            if not (Path(MODEL_DIR) / filename).exists():
                return False

        return True

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
