"""
Model Registry -- loads all ML artifacts once at startup.

Tracks load status per artifact. Exposes health/readiness.
"""

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
    """Singleton-style registry; call .load_all() at startup."""

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._status: Dict[str, ModelStatus] = {}
        self._errors: Dict[str, str] = {}

    # -----------------------------------------------------------------
    def load_all(self) -> None:
        """Load every configured model artifact from MODEL_DIR."""

        model_dir = Path(MODEL_DIR)

        logger.info("=" * 60)
        logger.info("Loading model artifacts from %s", model_dir)
        logger.info("Configured artifacts: %d", len(MODEL_FILES))
        logger.info("=" * 60)

        for index, (key, filename) in enumerate(
            MODEL_FILES.items(),
            start=1,
        ):
            filepath = model_dir / filename

            logger.info(
                "[%d/%d] START loading: %s -> %s",
                index,
                len(MODEL_FILES),
                key,
                filepath,
            )

            if not filepath.exists():
                self._status[key] = ModelStatus.NOT_PROVIDED
                self._errors[key] = f"File not found: {filepath}"

                logger.warning(
                    "[%d/%d] MISSING: %s",
                    index,
                    len(MODEL_FILES),
                    filepath,
                )
                continue

            try:
                obj = joblib.load(filepath)

                self._models[key] = obj
                self._status[key] = ModelStatus.LOADED

                logger.info(
                    "[%d/%d] DONE loading: %s (%s)",
                    index,
                    len(MODEL_FILES),
                    key,
                    type(obj).__name__,
                )

            except Exception as exc:
                self._status[key] = ModelStatus.ERROR
                self._errors[key] = str(exc)

                logger.exception(
                    "[%d/%d] FAILED loading: %s",
                    index,
                    len(MODEL_FILES),
                    key,
                )

        loaded = sum(
            1
            for status in self._status.values()
            if status == ModelStatus.LOADED
        )

        logger.info("=" * 60)
        logger.info(
            "MODEL LOADING COMPLETE: %d/%d loaded",
            loaded,
            len(MODEL_FILES),
        )
        logger.info("=" * 60)

    # -----------------------------------------------------------------
    def get(self, key: str) -> Optional[Any]:
        return self._models.get(key)

    # -----------------------------------------------------------------
    def status(self, key: str) -> ModelStatus:
        return self._status.get(key, ModelStatus.UNAVAILABLE)

    # -----------------------------------------------------------------
    def is_loaded(self, key: str) -> bool:
        return self._status.get(key) == ModelStatus.LOADED

    # -----------------------------------------------------------------
    def error(self, key: str) -> Optional[str]:
        return self._errors.get(key)

    # -----------------------------------------------------------------
    def health_report(self) -> dict:
        """Return a dict suitable for /health and /model-info."""

        report = {}

        for key in MODEL_FILES:
            st = self._status.get(
                key,
                ModelStatus.UNAVAILABLE,
            )

            report[key] = {
                "status": st.value,
                "error": self._errors.get(key),
            }

        return report

    # -----------------------------------------------------------------
    def model_info(self) -> dict:
        """Detailed model-info for /model-info endpoint."""

        info: dict = {
            "module_a_version": (
                "a-model-v1.0"
                if self.is_loaded("isolation_forest")
                else "unavailable"
            ),
            "b0_version": (
                "b0-baseline-v1.0"
                if self.is_loaded("b0_models")
                else "unavailable"
            ),
            "b1_version": (
                "unavailable — model artifact not provided"
            ),
            "b2_early_version": (
                "unavailable — model artifact not provided"
            ),
            "b2_96h_version": (
                "unavailable — model artifact not provided"
            ),
            "risk_fusion_version": (
                "risk-fusion-v1.0.0"
                if self.is_loaded("inference_config")
                else "unavailable"
            ),
            "snapshot_hash": "sih26170-v1",
            "calibration_date": "not provided",
            "stale": False,
            "feature_schema_version": "v1",
            "artifacts": self.health_report(),
        }

        return info


# -----------------------------------------------------------------
# Global singleton
# -----------------------------------------------------------------

registry = ModelRegistry()