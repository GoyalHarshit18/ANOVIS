import gc
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

from app.config import MODEL_DIR, MODEL_FILES

logger = logging.getLogger("sih26170.model_registry")


class ModelStatus(str, Enum):
    LOADED = "loaded"
    UNAVAILABLE = "unavailable"
    INCOMPATIBLE = "incompatible"
    ERROR = "error"
    NOT_PROVIDED = "not_provided"


class ModelRegistry:
    """
    Lazy-loading model registry.
    Artifacts are loaded on demand via .get(key) rather than all at startup,
    minimizing memory footprint for low-memory environments.
    """

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._status: Dict[str, ModelStatus] = {}
        self._errors: Dict[str, str] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._models:
            return self._models[key]

        if key not in MODEL_FILES:
            self._status[key] = ModelStatus.UNAVAILABLE
            self._errors[key] = f"Unknown model key: {key}"
            return None

        filepath = Path(MODEL_DIR) / MODEL_FILES[key]

        if not filepath.exists():
            self._status[key] = ModelStatus.NOT_PROVIDED
            self._errors[key] = f"File not found: {filepath}"
            return None

        try:
            logger.info("Loading model: %s", key)

            obj = joblib.load(filepath)

            self._models[key] = obj
            self._status[key] = ModelStatus.LOADED
            self._errors.pop(key, None)

            logger.info(
                "Model loaded: %s (%s)",
                key,
                type(obj).__name__,
            )

            return obj

        except Exception as exc:
            self._status[key] = ModelStatus.ERROR
            self._errors[key] = str(exc)

            logger.exception(
                "Model load failed: %s: %s",
                key,
                exc,
            )

            return None

    def unload(self, key: str) -> None:
        if key in self._models:
            logger.info("Unloading model: %s", key)
            del self._models[key]
            self._status[key] = ModelStatus.UNAVAILABLE
            gc.collect()
            logger.info("Model unloaded: %s", key)

    def unload_all(self) -> None:
        self._models.clear()
        for key in list(self._status.keys()):
            if self._status[key] == ModelStatus.LOADED:
                self._status[key] = ModelStatus.UNAVAILABLE
        gc.collect()

    def load_all(self) -> dict:
        """
        Compatibility method.
        Does NOT load all models at startup. Initializes lazy-loading state.
        """
        logger.info("ML models will be loaded on demand.")
        return self.health_report()

    def status(self, key: str) -> ModelStatus:
        if key in self._models:
            return ModelStatus.LOADED
        if key not in MODEL_FILES:
            return ModelStatus.UNAVAILABLE
        filepath = Path(MODEL_DIR) / MODEL_FILES[key]
        if not filepath.exists():
            return ModelStatus.NOT_PROVIDED
        return self._status.get(key, ModelStatus.UNAVAILABLE)

    def is_loaded(self, key: str) -> bool:
        return key in self._models and self._status.get(key) == ModelStatus.LOADED

    def error(self, key: str) -> Optional[str]:
        return self._errors.get(key)

    def health_report(self) -> dict:
        report = {}
        for key in MODEL_FILES:
            filepath = Path(MODEL_DIR) / MODEL_FILES[key]
            if key in self._models:
                status_val = ModelStatus.LOADED.value
            elif not filepath.exists():
                status_val = ModelStatus.NOT_PROVIDED.value
            else:
                status_val = self._status.get(key, ModelStatus.UNAVAILABLE).value

            report[key] = {
                "status": status_val,
                "error": self._errors.get(key),
            }
        return report

    def model_info(self) -> dict:
        return {
            "module_a_version": "available-on-demand" if (Path(MODEL_DIR) / MODEL_FILES.get("isolation_forest", "")).exists() else "unavailable",
            "b0_version": (
                "b0-baseline-v1.0"
                if self.is_loaded("b0_models")
                else "available-on-demand"
            ),
            "b1_version": "unavailable",
            "b2_early_version": "unavailable",
            "b2_96h_version": "unavailable",
            "risk_fusion_version": "available-on-demand",
            "snapshot_hash": "sih26170-v1",
            "calibration_date": "not provided",
            "stale": False,
            "feature_schema_version": "v1",
            "artifacts": self.health_report(),
        }


registry = ModelRegistry()