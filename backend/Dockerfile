# ==============================================================================
# Anovis / BurnSight-AI Backend Production Dockerfile
# Optimized for Render Web Service deployment
# ==============================================================================

FROM python:3.11-slim as base

# Prevents Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source and ML models
COPY app /app/app
COPY models /app/models
COPY LOT_00.csv /app/LOT_00.csv

# Expose port (Render automatically routes external traffic to $PORT)
EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start production server using Gunicorn with Uvicorn workers
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w 1 --timeout 120 -b 0.0.0.0:${PORT:-8000} app.main:app"]
