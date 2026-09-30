"""Anovis / BurnSight-AI Backend Configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv


# ==============================================================================
# Base directory
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# Load local .env if present
# ==============================================================================

load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)


# ==============================================================================
# Environment mode
# ==============================================================================

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()


# ==============================================================================
# Model directory
# ==============================================================================

model_dir_env = os.getenv("MODEL_DIR", "models")

MODEL_DIR = (
    (BASE_DIR / model_dir_env).resolve()
    if not Path(model_dir_env).is_absolute()
    else Path(model_dir_env)
)


# ==============================================================================
# API settings
# ==============================================================================

API_HOST = os.getenv("API_HOST", "0.0.0.0")

API_PORT = int(
    os.getenv(
        "PORT",
        os.getenv("API_PORT", "8000"),
    )
)


# ==============================================================================
# CORS configuration
# ==============================================================================

raw_cors = os.getenv("CORS_ORIGINS", "")
frontend_url = os.getenv("FRONTEND_URL", "")

cors_list = set()

if frontend_url:
    for url in frontend_url.split(","):
        clean_url = url.strip().rstrip("/")
        if clean_url:
            cors_list.add(clean_url)

if raw_cors:
    for origin in raw_cors.split(","):
        clean_origin = origin.strip().rstrip("/")
        if clean_origin:
            cors_list.add(clean_origin)


# If development or no explicit frontend URL is set,
# allow localhost defaults.
if ENVIRONMENT != "production" or not cors_list:
    cors_list.update(
        [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
        ]
    )

CORS_ORIGINS = list(cors_list)


# ==============================================================================
# Logging
# ==============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ==============================================================================
# Model artifact filenames
# ==============================================================================

MODEL_FILES = {
    "b0_models": "b0_models.pkl",
    "inference_config": "inference_config.pkl",
    "reference_limits": "reference_limits.pkl",
    "pat_reference": "pat_reference.pkl",
    "peer_scaler": "peer_scaler.pkl",
    "peer_knn": "peer_knn.pkl",
    "peer_reference_targets": "peer_reference_targets.pkl",
    "peer_scales": "peer_scales.pkl",
    "isolation_forest": "isolation_forest.pkl",
    "if_scaler": "if_scaler.pkl",
    "temporal_reference": "temporal_reference.pkl",
    "drift_reference": "drift_reference.pkl",
    "future_envelope": "future_envelope.pkl",
    "component_24h_classifier": "component_24h_classifier.pkl",
    "station_disturbance_classifier": "station_disturbance_classifier.pkl",
    "B0_IDDQ": "B0_IDDQ.pkl",
    "B0_Leakage": "B0_Leakage.pkl",
    "B0_Delay": "B0_Delay.pkl",
    "B1_IDDQ": "B1_IDDQ.pkl",
    "B1_Leakage": "B1_Leakage.pkl",
    "B1_Delay": "B1_Delay.pkl",
    "B2_Early_IDDQ": "B2_Early_IDDQ.pkl",
    "B2_Early_Leakage": "B2_Early_Leakage.pkl",
    "B2_Early_Delay": "B2_Early_Delay.pkl",
    "B2_96h_IDDQ": "B2_96h_IDDQ.pkl",
    "B2_96h_Leakage": "B2_96h_Leakage.pkl",
    "B2_96h_Delay": "B2_96h_Delay.pkl",
    "component_96h_classifier": "component_96h_classifier.pkl",
    "latent_specialist": "latent_specialist.pkl",
    "fusion_96h_classifier": "fusion_96h_classifier.pkl",
}


# ==============================================================================
# Batch limits
# ==============================================================================

MAX_BATCH_SIZE = 10000


# ==============================================================================
# Version
# ==============================================================================

APP_VERSION = "1.0.0"


# ==============================================================================
# Database (Supabase PostgreSQL / local PostgreSQL)
# ==============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:password@localhost:5432/sih26170",
)


# ==============================================================================
# Supabase Storage settings
# ==============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")

SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    "",
)

SUPABASE_STORAGE_BUCKET = os.getenv(
    "SUPABASE_STORAGE_BUCKET",
    "qa-reports",
)


# ==============================================================================
# Gemini AI Settings
# ==============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)