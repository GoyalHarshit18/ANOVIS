"""
Anovis — AI-Driven Anomaly Detection in Component Burn-In & Screening
FastAPI Backend Application
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, LOG_LEVEL, APP_VERSION
from app.ml.model_registry import registry
from app.api.health import router as health_router
from app.api.screening import router as screening_router
from app.api.components import router as component_router
from app.api.lots import router as lot_router
from app.api.models import router as model_router
from app.api.export import router as export_router
from app.api.explainability import router as explainability_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("sih26170")


# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models at startup."""
    logger.info("=" * 60)
    logger.info("Anovis Backend starting — v%s", APP_VERSION)
    logger.info("=" * 60)

    # Load all model artifacts ONCE
    logger.info("ML models will be loaded on demand.")

    # Log model status summary
    report = registry.health_report()
    loaded = sum(1 for v in report.values() if v["status"] == "loaded")
    total = len(report)
    logger.info("Models loaded: %d / %d", loaded, total)
    for key, info in report.items():
        status = info["status"]
        err = info.get("error", "")
        if status != "loaded":
            logger.warning("  %s: %s — %s", key, status, err)
        else:
            logger.info("  %s: %s", key, status)

    logger.info("Backend ready.")
    yield
    logger.info("Anovis Backend shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Anovis — Burn-In Screening API",
    description="AI-Driven Anomaly Detection in Component Burn-In & Screening",
    version=APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router)
app.include_router(screening_router)
app.include_router(component_router)
app.include_router(lot_router)
app.include_router(model_router)
app.include_router(export_router)
app.include_router(explainability_router)



@app.get("/")
async def root():
    return {
        "service": "Anovis — Burn-In Screening API",
        "version": APP_VERSION,
        "docs": "/docs",
    }
