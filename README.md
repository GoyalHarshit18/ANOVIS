# ANOVIS / BurnSight-AI
### AI-Driven Anomaly Detection & Predictive Screening in Semiconductor Component Burn-In

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg?logo=vite)](https://vitejs.dev)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)](https://www.docker.com)
[![CatBoost](https://img.shields.io/badge/CatBoost-1.2+-yellow.svg)](https://catboost.ai)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-brightgreen.svg)](https://shap.readthedocs.io)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-3.5_Flash-4285F4.svg?logo=google)](https://deepmind.google/technologies/gemini/)
[![Supabase](https://img.shields.io/badge/Supabase-Postgres_&_Storage-3ECF8E.svg?logo=supabase)](https://supabase.com)

---

## 1. Project Overview

**Anovis (BurnSight-AI)** is an industrial-grade, AI-powered semiconductor quality assurance platform. It detects early-life component failures, predicts 168h end-of-test degradation, provides mathematical SHAP explainability, and automatically generates grounded QA inspection reports via Google Gemini AI.

### Core Modules:
- **Module 1 (Anomaly Detection & Risk Fusion)**: 96h CatBoost supervised anomaly classification combined with PAT, Peer Residuals, Early Temporal drift, and Isolation Forest scores.
- **Module 2 (168h Predictive Analytics)**: B-Series regression models predicting `IDDQ_168h`, `Leakage_168h`, and `Delay_168h` from 0h + 24h burn-in data without data leakage.
- **Module 3 (Explainability & Grounded QA Reports)**: Exact TreeExplainer SHAP attributions, engineering limit checks, and structured Google Gemini QA Inspector Reports with ReportLab printable PDF exports.

---

## 2. Production Deployment Architecture

```
                    +-----------------------------+
                    |            USER             |
                    +-----------------------------+
                                   |
                                   v
                    +-----------------------------+
                    |       VERCEL FRONTEND       |
                    |         React + Vite        |
                    +-----------------------------+
                                   |
                                   | HTTPS REST API
                                   v
                    +-----------------------------+
                    |       RENDER BACKEND        |
                    |      Dockerized FastAPI     |
                    +-----------------------------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
+-----------------+       +-----------------+       +-----------------+
| CatBoost Models |       |      SHAP       |       |  Google Gemini  |
|  (In-Memory)    |       | Explainability  |       |  QA Inspection  |
+-----------------+       +-----------------+       +-----------------+
         |                         |                         |
         +-------------------------+-------------------------+
                                   |
                                   v
                    +-----------------------------+
                    |      SUPABASE PLATFORM      |
                    |   PostgreSQL + File Storage |
                    +-----------------------------+
```

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, Vite, TailwindCSS / Vanilla CSS, Lucide Icons, Recharts | Interactive inspector dashboard, real-time charts |
| **Backend API** | FastAPI, Uvicorn, Gunicorn | High-performance asynchronous REST API |
| **ML Inference** | CatBoost, Scikit-learn, Joblib, NumPy, Pandas | 96h anomaly classification & 168h regression (in-memory) |
| **Explainability** | SHAP (TreeExplainer) | Exact probability attribution & feature contribution |
| **AI Narrative** | Google Gemini API (`google-genai` SDK) | Grounded, non-hallucinated QA inspection reports |
| **Database** | Supabase PostgreSQL | Relational storage for runs, components, results, and audit trails |
| **File Storage** | Supabase Storage | Persistent storage for generated PDF reports |
| **Containerization** | Docker (Python 3.11-slim) | Container image for Render Web Service |

---

## 4. Repository Structure

```
ps170/
│
├── frontend/                     # Vercel React + Vite Frontend
│   ├── src/
│   │   ├── components/           # UI components, layout, header, sidebar
│   │   ├── pages/                # Dashboard, Anomaly, PredictiveAnalysis, Explainability, etc.
│   │   ├── services/
│   │   │   └── apiService.js     # Centralized API client using VITE_API_BASE_URL
│   │   └── data/                 # Sample data & test fallbacks
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   ├── vercel.json               # SPA routing rewrite configuration for Vercel
│   └── .env.example
│
├── backend/                      # Render Dockerized FastAPI Backend
│   ├── app/
│   │   ├── main.py               # FastAPI entry point & lifespan model loading
│   │   ├── config.py             # App configuration, CORS, environment variables
│   │   ├── api/                  # API route definitions (/health, /predict, /explainability, etc.)
│   │   ├── services/
│   │   │   ├── model_manager.py  # In-memory ModelManager singleton
│   │   │   ├── explainability_service.py # SHAP calculation & global rankings
│   │   │   ├── gemini_service.py # Google Gemini QA report generator & fallback
│   │   │   ├── pdf_service.py    # ReportLab printable PDF generator
│   │   │   ├── supabase_storage_service.py # Supabase storage uploader
│   │   │   └── ...
│   │   ├── ml/                   # Model registry, prediction engine, risk fusion
│   │   ├── inference/            # Feature vector builders & contract validators
│   │   ├── db/                   # SQLAlchemy PostgreSQL models & database session
│   │   └── schemas/              # Pydantic input & output validation schemas
│   ├── models/                   # Packaged ML model artifacts (.pkl)
│   ├── Dockerfile                # Production Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt          # Python production dependencies
│   ├── smoke_test.py             # Automated 10-point deployment smoke test
│   └── .env.example
│
├── docs/
│   └── database_schema.sql       # Production Supabase PostgreSQL schema & indexes
│
├── .gitignore
├── .env.example
└── README.md
```

---

## 5. Machine Learning Models & In-Memory Strategy

All ML models run **inside** the FastAPI process. Models are loaded **once** at server startup via FastAPI `lifespan` and held in memory to ensure sub-100ms inference times.

| Model ID | File Name | Size | Target / Function |
|---|---|---|---|
| **Model 1** | `component_96h_classifier.pkl` | ~10.8 MB | 96h CatBoost Supervised Anomaly Classifier |
| **Model 2** | `B0_IDDQ.pkl` | ~137 KB | 168h IDDQ Regressor ($\mu\text{A}$) |
| **Model 3** | `B0_Leakage.pkl` | ~113 KB | 168h Leakage Regressor ($\text{nA}$) |
| **Model 4** | `B0_Delay.pkl` | ~201 KB | 168h Propagation Delay Regressor ($\text{ns}$) |
| **Specialists** | `latent_specialist.pkl`, `station_disturbance_classifier.pkl`, `isolation_forest.pkl`, `fusion_96h_classifier.pkl` | ~12 MB total | Outlier & drift specialist models |

---

## 6. Environment Variables

### Render Backend (`backend/.env` / Render Dashboard):
```env
# Server
PORT=8000
API_HOST=0.0.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO

# CORS (Set to your deployed Vercel domain)
FRONTEND_URL=https://your-frontend-app.vercel.app
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Models
MODEL_DIR=./models

# Supabase PostgreSQL (Connection Pooler URL)
DATABASE_URL=postgresql+psycopg2://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres

# Supabase Storage & Service Key (Backend ONLY - NEVER in frontend)
SUPABASE_URL=https://[ref].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJh...
SUPABASE_STORAGE_BUCKET=qa-reports

# Google Gemini API (Backend ONLY - NEVER in frontend)
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-3.5-flash-lite
```

### Vercel Frontend (`frontend/.env` / Vercel Project Settings):
```env
# Render Backend Base URL (NO trailing slash)
VITE_API_BASE_URL=https://your-backend.onrender.com
```

> [!CAUTION]
> **Security Guardrail**: Never put `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, or `GEMINI_API_KEY` into frontend environment variables (`VITE_*`).

---

## 7. Production API Endpoints

### Health & Readiness Probes
- `GET /health`: Returns basic and detailed health status (`{"status": "ok", "service": "...", "database": "Connected", "models_ready": true}`).
- `GET /health/ready`: Readiness probe for container orchestrators. Returns HTTP 200 when all models are loaded and operational; returns HTTP 503 if models fail to load.

### Core Inference & Explainability
- `POST /api/predict`: Production unified inference endpoint.
  - **Input**: Component measurements (0h, 24h, 96h).
  - **Output**:
    ```json
    {
      "component_id": "CMP-2026-001",
      "lot_id": "LOT-2026-091",
      "anomaly_probability_96h": 0.0412,
      "anomaly_status_96h": "NORMAL",
      "predicted_iddq_168h": 1.45,
      "predicted_leakage_168h": 5.82,
      "predicted_delay_168h": 1.10,
      "threshold": 0.50,
      "model_version": "catboost-96h-v1.0"
    }
    ```
- `POST /api/explainability/component`: Returns exact SHAP attributions, mathematical base value reconstruction, positive/negative risk contributors, and engineering limit assessments.
- `GET /api/explainability/global`: Returns dataset-wide feature importance ranking and mean absolute SHAP attributions.
- `POST /api/reports/qa`: Generates a Google Gemini QA Inspection report strictly grounded in model evidence with fallback protection.
- `GET /api/reports/qa/{component_id}/pdf`: Streams and downloads a printable ReportLab QA report with inspector sign-off section.

### Screening & Batch Ingestion
- `POST /screen`: Single-component full risk-fusion pipeline.
- `POST /upload`: CSV dataset upload and schema validation.
- `POST /screening-runs/{run_id}/module-a`: Executes PAT, Peer, Temporal, and Isolation Forest analysis.
- `POST /screening-runs/{run_id}/anomaly-analysis`: Evaluates Device, Lot, and Station origin status.
- `POST /screening-runs/{run_id}/module-b`: Runs B0, B1, B2 predictive models.
- `POST /screening-runs/{run_id}/risk-fusion`: Computes final LDI, A-Score, S-Score, and disposition decision.

---

## 8. Step-by-Step Deployment Guide

### STEP 1: Supabase Project Setup
1. Create a project at [supabase.com](https://supabase.com).
2. Under **Project Settings > Database**, copy your `Connection string` (URI mode, Transaction / Session pooler).
3. Under **Project Settings > API**, copy the `Project URL` and `service_role key` (secret).
4. Open the **SQL Editor** in Supabase and run [`docs/database_schema.sql`](file:///c:/Users/Harsh/OneDrive/Desktop/ps170/docs/database_schema.sql) to create all tables and indexes.
5. In **Storage**, create a new bucket named `qa-reports` (Public or authenticated read).

### STEP 2: Deploy Backend to Render
1. In [render.com](https://render.com), click **New > Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   - **Name**: `anovis-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `Dockerfile`
   - **Instance Type**: Starter / Standard (1 GB+ RAM recommended for ML models)
4. Under **Environment Variables**, configure:
   - `ENVIRONMENT` = `production`
   - `DATABASE_URL` = (Your Supabase PostgreSQL URI)
   - `SUPABASE_URL` = (Your Supabase Project URL)
   - `SUPABASE_SERVICE_ROLE_KEY` = (Your Supabase Secret Service Role Key)
   - `SUPABASE_STORAGE_BUCKET` = `qa-reports`
   - `GEMINI_API_KEY` = (Your Google Gemini API Key)
   - `GEMINI_MODEL` = `gemini-3.5-flash-lite`
   - `FRONTEND_URL` = `https://your-frontend.vercel.app`
5. Click **Deploy Web Service**.
6. Once deployed, verify:
   - `https://your-backend.onrender.com/health` -> `{"status": "ok"}`
   - `https://your-backend.onrender.com/health/ready` -> `{"status": "ready"}`

### STEP 3: Deploy Frontend to Vercel
1. In [vercel.com](https://vercel.com), click **Add New > Project**.
2. Import your GitHub repository.
3. Configure the project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL` = `https://your-backend.onrender.com`
5. Click **Deploy**.
6. Update the `FRONTEND_URL` in your Render backend settings with your actual Vercel URL (e.g. `https://anovis.vercel.app`).

---

## 9. Local Development & Testing

### Backend Setup:
```bash
# 1. Navigate to backend
cd backend

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure local environment
cp .env.example .env

# 5. Run tests
pytest

# 6. Run automated smoke test
python smoke_test.py

# 7. Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup:
```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Test production build
npm run build

# 4. Start development server
npm run dev
```

---

## 10. Smoke Test Verification

Run the automated smoke test suite to verify the entire end-to-end pipeline:
```bash
cd backend
python smoke_test.py
```
**Expected Output:**
```
======================================================================
[STARTING ANOVIS PRODUCTION DEPLOYMENT SMOKE TEST]
======================================================================
[TEST 1] Checking GET /health ...
  [PASS] /health OK: status=ok, api=Operational, db=Connected
[TEST 2] Checking GET /health/ready ...
  [PASS] /health/ready OK: models_ready=True
[TEST 3] Verifying in-memory ModelManager & Artifacts ...
  [PASS] ModelManager ready: CatBoost 96h Anomaly Classifier v1.0 & B-Series 168h Parameter Regressors v1.0
[TEST 4] Verifying Feature Order & Contract Consistency ...
  [PASS] Feature contracts verified: 96h features = 43, B0 features = 6
[TEST 5] Testing POST /api/predict (96h Anomaly + 168h Regressors) ...
  [PASS] POST /api/predict OK:
    - Component: CMP-SMOKE-2026-001 (Lot: LOT-PROD-TEST)
    - 96h Anomaly Probability: 0.9791 -> Status: ANOMALY
    - Predicted 168h IDDQ: 8.8976 uA
    - Predicted 168h Leakage: 366.7027 nA
    - Predicted 168h Delay: 2.9998 ns
[TEST 6] Testing POST /api/explainability/component ...
  [PASS] SHAP Explainability OK:
    - Base Value: 0.5, Reconstructed: 0.9692
    - Top Risk Contributor: IDDQ_relative_24_96 (SHAP: +0.065951)
[TEST 7] Testing GET /api/explainability/global ...
  [PASS] Global SHAP OK: Top feature = IDDQ_relative_24_96 (9.77%)
[TEST 8] Testing POST /api/reports/qa ...
  [PASS] QA Report OK (Source: GOOGLE_GEMINI_AI (gemini-3.5-flash-lite))
[TEST 9] Testing GET /api/reports/qa/{component_id}/pdf ...
  [PASS] Printable PDF Report generated successfully: 6625 bytes
[TEST 10] Testing non-regression of POST /screen ...
  [PASS] /screen non-regression OK: decision=REJECT, a_score=100.0

======================================================================
SUCCESS: ALL 10 PRODUCTION SMOKE TESTS PASSED WITH ZERO ERRORS!
======================================================================
```

---

## 11. Disclaimer

> **Quality Assurance & Safety Notice**: AI-generated explanations, predictions, and reports support quality inspection and do not independently establish a physical defect cause. Final disposition requires authorized QA review and compliance with applicable semiconductor reliability standards.
