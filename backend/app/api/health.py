"""Health and Readiness endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.ml.model_registry import registry
from app.services.model_manager import model_manager
from app.db.session import get_db
from app.config import APP_VERSION

logger = logging.getLogger("sih26170.health")

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Return basic and detailed system health status."""
    models_health = registry.health_report()

    # Determine statuses
    catboost_loaded = registry.is_loaded("component_96h_classifier")
    module_b_loaded = registry.is_loaded("b0_models") or (
        registry.is_loaded("B0_IDDQ") and registry.is_loaded("B0_Leakage") and registry.is_loaded("B0_Delay")
    )
    module_a_loaded = all(
        registry.is_loaded(k) for k in ["isolation_forest", "if_scaler", "pat_reference", "peer_scaler", "peer_knn"]
    )

    db_status = "Disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "Connected"
    except Exception:
        pass

    api_status = "Operational"
    if not catboost_loaded and not module_b_loaded:
        api_status = "Degraded"

    return {
        "status": "ok",
        "service": "Anovis — Burn-In Screening API",
        "version": APP_VERSION,
        "api": api_status,
        "database": db_status,
        "feature_engine": "v1.0",
        "models_ready": model_manager.is_ready(),
        "module_a": "Loaded" if module_a_loaded else "Degraded",
        "module_b": "Loaded" if module_b_loaded else "Unavailable",
        "catboost_96h": "Loaded" if catboost_loaded else "Unavailable",
        "artifacts": models_health,
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe for container orchestrators (Render / Kubernetes).
    Verifies that required ML models and database are functional before receiving traffic.
    """
    is_models_ready = model_manager.is_ready()

    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.warning("Readiness probe DB check failed: %s", e)

    if not is_models_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "reason": "ML models not fully loaded into memory",
                "models_ready": False,
                "database_connected": db_connected,
            }
        )

    return {
        "status": "ready",
        "service": "Anovis — Burn-In Screening API",
        "version": APP_VERSION,
        "models_ready": True,
        "database_connected": db_connected,
    }
