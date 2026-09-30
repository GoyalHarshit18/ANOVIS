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
    db_status = "Disconnected"

    try:
        db.execute(text("SELECT 1"))
        db_status = "Connected"
    except Exception:
        pass

    return {
        "status": "ok",
        "service": "Anovis — Burn-In Screening API",
        "version": APP_VERSION,
        "api": "Operational",
        "database": db_status,
        "feature_engine": "v1.0",
        "models_ready": model_manager.is_ready(),
        "model_loading": "lazy",
        "required_models": {
            "component_96h_classifier": "available_on_demand",
            "b0_models": "available_on_demand",
        },
        "loaded_models": list(registry._models.keys()),
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
