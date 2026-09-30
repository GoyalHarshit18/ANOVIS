"""Model info endpoint."""
from fastapi import APIRouter
from app.ml.model_registry import registry
from app.ml.prediction_engine import get_b_model_availability

router = APIRouter(tags=["models"])


@router.get("/model-info")
async def get_model_info():
    """Return model registry info, versions, and availability."""
    info = registry.model_info()
    info["b_models"] = get_b_model_availability()
    return info
