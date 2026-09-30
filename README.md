[ANOVIS Logo](./docs/assets/anovis-logo.svg)

# ANOVIS

**AI-Powered Semiconductor Burn-In Intelligence — Detect Anomalies, Predict 168h Degradation, Explain Every Decision**

SIH / Semiconductor Burn-In Reliability Platform | Team ANOVIS

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB.svg)](https://react.dev/)
[![CatBoost](https://img.shields.io/badge/CatBoost-ML-orange.svg)](https://catboost.ai/)
[![SHAP](https://img.shields.io/badge/SHAP-Explainability-purple.svg)](https://shap.readthedocs.io/)
[![Gemini](https://img.shields.io/badge/Gemini-AI%20Reports-4285F4.svg)](https://ai.google.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend-black.svg)](https://vercel.com/)
[![Render](https://img.shields.io/badge/Render-Backend-46E3B7.svg)](https://render.com/)

---

## Table of Contents

- [The Problem](#the-problem)
- [Our Solution](#our-solution)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Core Modules](#core-modules)
- [Model Performance](#model-performance)
- [Getting Started](#getting-started)
- [Production Deployment](#production-deployment)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Team](#team)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Acknowledgments](#acknowledgments)
- [License](#license)

---

## The Problem

### The Hidden Risk in Semiconductor Burn-In Testing

Semiconductor burn-in testing is designed to expose components that may fail after prolonged operation. However, conventional workflows often depend on threshold-based inspection, manual analysis of measurement trajectories, and delayed failure confirmation.

The challenge is not simply detecting whether a measurement is high or low.

The real challenge is identifying **degradation patterns early enough to support engineering action**, predicting how a component may behave by 168 hours, and explaining why an AI system classified it as anomalous.

### Key Challenges

| **Challenge** | **Current Difficulty** | **Impact** |
| --- | --- | --- |
| **Delayed Failure Detection** | Some failures become visible only after extended burn-in | Late intervention and higher screening cost |
| **Multi-Stage Measurements** | IDDQ, leakage and delay evolve across 0h, 24h, 96h and 168h | Difficult to interpret trajectories manually |
| **Early Degradation** | Small changes can become significant later | Risk of missing weak failure signatures |
| **Manual Inspection** | Engineers must compare multiple measurements and limits | Time-consuming and inconsistent |
| **Black-Box AI** | A prediction alone does not explain the decision | Difficult for QA inspectors to trust |
| **Future-State Uncertainty** | 168h measurements may not yet exist | Decisions must be made from earlier observations |

### Why It Matters

- **Reliability:** Identify components showing suspicious degradation before final burn-in completion.
- **Predictive Maintenance:** Estimate 168h electrical characteristics from earlier observations.
- **Quality Assurance:** Provide evidence behind an anomaly classification.
- **Traceability:** Preserve predictions, explanations and inspection reports.
- **Human-in-the-Loop:** AI supports QA decisions rather than replacing engineering judgment.

> **ANOVIS principle:** Detect early. Predict forward. Explain every decision.

---

## Our Solution

### ANOVIS: The AI Semiconductor Reliability Analyst

ANOVIS is an **end-to-end AI platform for semiconductor burn-in screening** that combines anomaly detection, 168-hour degradation prediction and explainable AI into one workflow.

Instead of producing only a binary anomaly label, ANOVIS provides:

1. **96h anomaly detection**
2. **168h IDDQ prediction**
3. **168h Leakage prediction**
4. **168h Propagation Delay prediction**
5. **SHAP-based model explanation**
6. **Gemini-powered QA inspection narrative**
7. **Downloadable inspection reports**

### Key Differentiators

| **Capability** | **ANOVIS** | **Conventional Workflow** |
| --- | --- | --- |
| 96h anomaly detection | **AI-based** | Manual / threshold inspection |
| 168h prediction | **IDDQ + Leakage + Delay** | Usually requires completed test |
| Explainability | **SHAP feature attribution** | Manual interpretation |
| QA narrative | **Gemini-assisted report** | Manually written |
| Component-level output | **Yes** | Yes |
| Lot-level processing | **Yes** | Depends on workflow |
| Persistent results | **Supabase** | Often file-based |
| Web deployment | **Vercel + Render** | Local / internal systems |
| Human review | **Built into workflow** | Manual |

---

## How It Works

### The 4-Stage Workflow

```text
┌──────────────────┐
│  LOT / COMPONENT │
│      INPUT       │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────┐
│  FEATURE ENGINEERING    │
│  0h + 24h + 96h data    │
└────────┬────────────────┘
         │
         ├─────────────────────────────┐
         │                             │
         ▼                             ▼
┌──────────────────┐          ┌────────────────────┐
│ 96h ANOMALY      │          │ 168h PREDICTION    │
│ CATBOOST         │          │ IDDQ / LEAKAGE /   │
│ CLASSIFIER       │          │ DELAY REGRESSORS   │
└────────┬─────────┘          └─────────┬──────────┘
         │                              │
         ▼                              │
┌──────────────────┐                    │
│ SHAP EXPLANATION │                    │
└────────┬─────────┘                    │
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────┐
│              QA INSPECTION VIEW                 │
│ Classification + Explanation + 168h Prediction  │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
               ┌────────────────┐
               │ GEMINI REPORT  │
               │ + PDF EXPORT   │
               └────────────────┘
```

### Processing Pipeline

```text
INPUT DATA
    │
    ▼
Schema Validation
    │
    ▼
Feature Engineering
    │
    ├───────────────► 96h CatBoost Detector
    │                         │
    │                         ▼
    │                    Anomaly Score
    │                         │
    │                         ▼
    │                       SHAP
    │
    └───────────────► 168h Regression Models
                              │
                              ├──► IDDQ
                              ├──► Leakage
                              └──► Delay
                                      │
                                      ▼
                              Prediction Dashboard
                                      │
                                      ▼
                               Gemini QA Report
                                      │
                                      ▼
                                  PDF Report
```

### Step 1: Input

ANOVIS accepts component or lot-level burn-in measurements.

The deployed test interface supports fields such as:

- Component ID
- Lot ID
- Station ID
- Device Type
- Temperature
- Supply Voltage
- IDDQ at 0h / 24h / 96h
- Leakage at 0h / 24h / 96h
- Propagation Delay at 0h / 24h / 96h

The backend validates the incoming schema before inference.

### Step 2: Feature Engineering

The backend reproduces the feature engineering used during model development.

Examples include:

- Absolute measurement changes
- Relative changes
- 0h → 24h drift
- 24h → 96h drift
- 0h → 96h drift
- Temperature and voltage context

The production feature order is controlled by the model configuration to prevent training/inference mismatch.

### Step 3: 96h Anomaly Detection

At 96 hours, the CatBoost classifier evaluates the component.

Output:

- Anomaly probability
- Classification threshold
- Normal / Anomaly status

**ANOVIS does not use a 24h anomaly detector in the final pipeline.**

The 24h measurements are used as part of the predictive feature pipeline; anomaly detection occurs at 96h.

### Step 4: 168h Prediction

Three independent regression models estimate the expected 168h measurements:

- IDDQ
- Leakage
- Propagation Delay

These predictions provide a forward-looking view before the final burn-in point.

### Step 5: Explainability

For every classification, ANOVIS can generate SHAP-based feature attribution.

The system identifies:

- Features pushing the model toward anomaly
- Features pushing the model toward normal
- Most influential measurements
- Relevant measurement trends

SHAP explains the model's decision; it does not independently prove a physical defect mechanism.

### Step 6: AI-Assisted QA Report

Gemini receives verified model evidence from the backend and converts it into a concise QA-oriented explanation.

Gemini does **not** perform the anomaly classification.

The authoritative outputs remain:

- CatBoost prediction
- Anomaly probability
- Threshold
- SHAP contributions
- Measured values
- Engineering limits

### Step 7: Human Review

The QA inspector receives:

- Classification
- Probability
- Measurement summary
- SHAP explanation
- 168h predictions
- AI-generated narrative
- Recommended verification steps
- Downloadable PDF report

Final engineering disposition remains a human decision.

---

## Architecture

### High-Level System Design

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         ANOVIS PLATFORM                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────┐       HTTPS        ┌───────────────────────────┐ │
│  │    VERCEL     │ ─────────────────► │          RENDER           │ │
│  │               │                    │                           │ │
│  │ React + Vite  │                    │ FastAPI                   │ │
│  │ Dashboard     │                    │                           │ │
│  │ Charts        │                    │ ┌───────────────────────┐ │ │
│  │ QA Reports    │                    │ │ CatBoost Models       │ │ │
│  └───────────────┘                    │ │ • 96h Classifier      │ │ │
│                                       │ │ • 168h IDDQ            │ │ │
│                                       │ │ • 168h Leakage         │ │ │
│                                       │ │ • 168h Delay           │ │ │
│                                       │ └───────────────────────┘ │ │
│                                       │                           │ │
│                                       │ SHAP Explainability       │ │
│                                       │ PDF Report Generation     │ │
│                                       └──────────┬───────┬────────┘ │
│                                                  │       │          │
│                                      ┌───────────┘       └──────┐   │
│                                      ▼                          ▼   │
│                              ┌──────────────┐          ┌──────────┐ │
│                              │   SUPABASE   │          │ GEMINI   │ │
│                              │ PostgreSQL   │          │   API    │ │
│                              │ + Storage    │          │ QA Text  │ │
│                              └──────────────┘          └──────────┘ │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Deployment Data Flow

```text
QA Inspector
     │
     ▼
Vercel React Dashboard
     │
     │ HTTPS
     ▼
Render FastAPI
     │
     ├──────────────► CatBoost 96h Classifier
     │                         │
     │                         ▼
     │                        SHAP
     │
     ├──────────────► 168h IDDQ Regressor
     ├──────────────► 168h Leakage Regressor
     └──────────────► 168h Delay Regressor
                               │
                               ▼
                         Verified Results
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
           Supabase                       Gemini API
        Database/Storage                QA Explanation
                │                             │
                └──────────────┬──────────────┘
                               ▼
                         PDF QA Report
```

### Design Principles

- **Single ML backend:** Models run inside FastAPI rather than as separate services.
- **Secure secrets:** Gemini and Supabase service credentials stay on the backend.
- **Persistent storage:** Supabase stores application data and reports.
- **Stateless API:** Render instances can restart without losing persistent application data.
- **Human-in-the-loop:** AI outputs support QA review rather than replacing it.
- **No future leakage:** Future 168h observations are never used as inputs to the earlier prediction stage.

---

## Tech Stack

### AI / ML Pipeline

| **Technology** | **Purpose** | **Role in ANOVIS** |
| --- | --- | --- |
| **Python** | Core ML language | Model inference and feature engineering |
| **CatBoost** | ML framework | Anomaly classification and regression |
| **SHAP** | Explainable AI | Feature-level model attribution |
| **NumPy** | Numerical computing | Feature calculations |
| **Pandas** | Data processing | Input validation and tabular processing |
| **Scikit-learn** | Evaluation utilities | Metrics and validation |

### Machine Learning Models

| **Model** | **Task** | **Output** |
| --- | --- | --- |
| **CatBoost Classifier** | 96h anomaly detection | Anomaly probability / status |
| **CatBoost Regressor** | 168h IDDQ | Predicted IDDQ |
| **CatBoost Regressor** | 168h Leakage | Predicted Leakage |
| **CatBoost Regressor** | 168h Delay | Predicted Delay |

### Backend Infrastructure

| **Technology** | **Purpose** |
| --- | --- |
| **FastAPI** | REST API and inference service |
| **Uvicorn / Gunicorn** | Production ASGI serving |
| **Pydantic** | Request / response validation |
| **Docker** | Backend packaging |
| **Render** | Backend deployment |
| **Gemini API** | QA explanation generation |

### Frontend & Visualization

| **Technology** | **Purpose** |
| --- | --- |
| **React** | Web application |
| **Vite** | Frontend build tooling |
| **JavaScript / TypeScript** | Frontend logic |
| **Charts** | Prediction and explainability visualization |
| **Vercel** | Frontend deployment |

### Data & Storage

| **Technology** | **Purpose** |
| --- | --- |
| **Supabase PostgreSQL** | Persistent application data |
| **Supabase Storage** | PDF reports and persistent files |
| **CSV** | Lot/component import and export |
| **JSON** | API and model configuration |

---

## Core Modules

### 1. `Anomaly Detection` — 96h CatBoost

**Purpose:** Identify components showing anomalous behavior by the 96h measurement stage.

**Inputs:**

- 0h measurements
- 24h measurements
- 96h measurements
- Engineered drift features
- Operating context

**Outputs:**

- Anomaly probability
- Classification
- Threshold
- QA review status

**Important:**

The final production workflow does not perform anomaly classification at 24h.

---

### 2. `168h Prediction` — Multi-Target Regression

**Purpose:** Predict future 168h electrical behavior from earlier burn-in measurements.

Three separate regressors are used.

```text
0h + 24h Measurements
          │
          ├──────────────► IDDQ Regressor ───────► 168h IDDQ
          │
          ├──────────────► Leakage Regressor ────► 168h Leakage
          │
          └──────────────► Delay Regressor ──────► 168h Delay
```

**Why separate models?**

IDDQ, leakage and delay have different units, distributions and degradation behavior. Independent regressors allow each target to be modeled according to its own response characteristics.

---

### 3. `Explainability` — SHAP

**Purpose:** Explain why the 96h classifier made its decision.

**Outputs:**

- Global feature importance
- Individual component explanation
- Positive anomaly contributors
- Negative contributors
- SHAP contribution values
- Feature values

**Example:**

```text
Component
   │
   ▼
96h CatBoost
   │
   ▼
Anomaly Probability
   │
   ▼
SHAP
   │
   ├── IDDQ drift ─────────► anomaly evidence
   ├── Leakage drift ──────► anomaly evidence
   ├── Delay change ───────► normal/anomaly evidence
   └── Voltage context ────► supporting evidence
```

SHAP values indicate model contribution, not physical causality.

---

### 4. `Gemini QA Assistant`

**Purpose:** Convert verified model evidence into a human-readable QA explanation.

Gemini receives:

- Classification
- Probability
- SHAP contributors
- Relevant measurements
- Engineering limits
- 168h predictions

Gemini generates:

- Executive summary
- Classification explanation
- Key contributing factors
- Measurement trends
- Engineering-limit assessment
- Suggested inspection steps
- Limitations

The Gemini API cannot override the ML model's classification or probability.

---

### 5. `QA Report Generator`

**Purpose:** Generate a professional inspection report.

Reports include:

- Component information
- Lot information
- 96h anomaly result
- Measurement summary
- SHAP chart
- Important contributors
- 168h predictions
- Gemini explanation
- QA recommendations
- Human review section
- Report timestamp

Reports are stored using Supabase Storage.

---

### 6. `Lot Processing`

**Purpose:** Process multiple components from a single lot.

Example workflow:

```text
CSV Upload
    │
    ▼
Schema Validation
    │
    ▼
50 / 100 / N Components
    │
    ├── Component 001 ──► Prediction
    ├── Component 002 ──► Prediction
    ├── Component 003 ──► Prediction
    └── ...
    │
    ▼
Lot-Level Summary
```

The system can display:

- Total components
- Normal components
- Anomalous components
- Anomaly percentage
- Prediction distributions
- Components requiring QA review

---

## Model Performance

### 96h Anomaly Detection

The current development evaluation on the matched synthetic test set produced:

| **Metric** | **24h Detector** | **96h Detector** |
| --- | ---: | ---: |
| Precision | 52.72% | **78.87%** |
| Recall | 48.96% | **95.54%** |
| False Positive Rate | 6.82% | **3.97%** |

**Production model:** 96h detector only.

The 24h detector is not part of the final production workflow.

> These results were obtained on a synthetic matched test set derived from training trajectories with perturbations. They should be treated as development/prototype evaluation rather than an independent real-world benchmark.

### 168h Regression

The system evaluates three separate targets:

| **Target** | **Prediction Stage** | **Evaluation** |
| --- | --- | --- |
| IDDQ | 168h | MAE / R² |
| Leakage | 168h | MAE / R² |
| Propagation Delay | 168h | MAE / R² |

The project generates actual-vs-predicted plots for each target.

Because the current evaluation data is synthetic/matched, regression results should be interpreted as prototype validation rather than evidence of field performance.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Git
- Docker (recommended for backend deployment)
- Supabase project for persistent storage
- Gemini API key for AI-generated QA reports

No GPU is required for the deployed CPU inference architecture if the selected Render instance has sufficient memory for the model artifacts.

### Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd ANOVIS
```

### Backend Setup

```bash
cd backend

python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure:

```env
ENVIRONMENT=development

FRONTEND_URL=http://localhost:5173

SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=your_database_url

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model

MODEL_DIR=./models
```

### Start Backend

Use the actual FastAPI module path configured in the repository.

Typical development command:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

---

## Frontend Setup

```bash
cd frontend
npm install
```

Create:

```text
frontend/.env.local
```

Add:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Start:

```bash
npm run dev
```

Open the URL displayed by Vite, typically:

```text
http://localhost:5173
```

---

## Production Deployment

### Deployment Architecture

```text
Frontend
   │
   ▼
Vercel
React + Vite
   │
   │ HTTPS
   ▼
Render
FastAPI + CatBoost + SHAP
   │
   ├────► Supabase PostgreSQL
   │
   ├────► Supabase Storage
   │
   └────► Gemini API
```

### 1. Supabase

Create a Supabase project.

Configure:

- PostgreSQL database
- Required application tables
- Storage bucket for reports
- Appropriate access policies

Backend-only secret:

```env
SUPABASE_SERVICE_ROLE_KEY=...
```

Never expose this key to the frontend.

### 2. Render

Deploy the `backend/` service as a Dockerized Web Service.

Configure:

```text
Root Directory: backend
```

Use the repository's Dockerfile.

The backend must listen on Render's `$PORT`.

Set environment variables:

```env
DATABASE_URL=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...

GEMINI_API_KEY=...
GEMINI_MODEL=...

FRONTEND_URL=https://your-project.vercel.app

ENVIRONMENT=production
```

Verify:

```text
https://your-backend.onrender.com/health
```

### 3. Vercel

Deploy:

```text
frontend/
```

Use:

```text
Framework: Vite
Build Command: npm run build
Output Directory: dist
```

Set:

```env
VITE_API_BASE_URL=https://your-backend.onrender.com
```

Do NOT add:

```text
GEMINI_API_KEY
SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL
```

to Vercel frontend environment variables.

### 4. Final Production Test

Verify:

- Frontend loads
- Backend health endpoint works
- Lot CSV upload works
- 96h anomaly detection works
- 168h prediction works
- SHAP explanation works
- Gemini explanation works
- PDF report works
- Supabase persistence works
- CORS works
- No secrets are exposed

---

## API Reference

### REST API

| **Method** | **Endpoint** | **Description** |
| --- | --- | --- |
| `GET` | `/health` | Backend health |
| `GET` | `/health/ready` | Model/service readiness |
| `POST` | `/api/predict` | Run anomaly + 168h predictions |
| `POST` | `/api/explainability/component` | Explain a component |
| `GET` | `/api/explainability/global` | Global SHAP importance |
| `POST` | `/api/reports/qa` | Generate QA report |
| `GET` | `/api/reports/qa/{report_id}/pdf` | Download PDF |

Actual endpoint names should follow the implementation in the deployed backend.

### Example Prediction Request

```json
{
  "component_id": "TEST-COMP-001",
  "lot_id": "TEST-LOT-001",
  "station_id": "STATION-01",
  "device_type": "TYPE-A",
  "temperature": 25.1,
  "voltage": 1.2,
  "iddq_ua_0h": 42.1,
  "iddq_ua_24h": 44.3,
  "iddq_ua_96h": 48.7,
  "leakage_na_0h": 8.1,
  "leakage_na_24h": 8.6,
  "leakage_na_96h": 9.4,
  "prop_delay_ns_0h": 2.01,
  "prop_delay_ns_24h": 2.03,
  "prop_delay_ns_96h": 2.07
}
```

### Example Response

```json
{
  "component_id": "TEST-COMP-001",
  "lot_id": "TEST-LOT-001",
  "anomaly_probability_96h": 0.08,
  "anomaly_status_96h": "NORMAL",
  "predicted_iddq_168h": 52.1,
  "predicted_leakage_168h": 10.2,
  "predicted_delay_168h": 2.11
}
```

Example values above are illustrative.

---

## Project Structure

```text
ANOVIS/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── services/
│   │   │   ├── inference.py
│   │   │   ├── shap_explainer.py
│   │   │   ├── gemini_service.py
│   │   │   └── report_service.py
│   │   ├── models/
│   │   ├── schemas/
│   │   └── db/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.*
│
├── models_extracted/
├── models_extracted_py/
│
├── docs/
│   ├── architecture/
│   ├── reports/
│   └── assets/
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Team

### Team ANOVIS

| **Member** | **Role** | **Responsibilities** |
| --- | --- | --- |
| **Team Leader** | System Architecture | Overall coordination and integration |
| **ML Engineer** | Machine Learning | Anomaly detection and 168h prediction |
| **GenAI Engineer** | Explainability | SHAP + Gemini QA reporting |
| **Frontend / Backend Engineer** | Full Stack | Dashboard, APIs and deployment |

> Update the member names and exact responsibilities here according to the final team composition before publishing the repository.

### Team Philosophy

We believe in:

- **Explainable AI:** Every important AI decision should have understandable evidence.
- **Predictive Reliability:** Detect risk before final failure confirmation where the available data supports it.
- **Human-in-the-Loop QA:** AI assists engineers; it does not replace authorized engineering decisions.
- **Reproducible ML:** Training and production inference must use consistent feature definitions.
- **Deployment First:** Models should work as part of a complete usable system, not only inside notebooks.

---

## Roadmap

### Phase 1: Hackathon MVP — Current

- 96h anomaly detection
- 168h IDDQ prediction
- 168h Leakage prediction
- 168h Delay prediction
- SHAP explainability
- Gemini-assisted QA reports
- Lot-level processing
- Web dashboard
- PDF report generation

### Phase 2: Production Hardening

- Authentication
- Role-based QA access
- Improved batch processing
- Background jobs
- Audit logging
- Model version management
- Automated CI/CD
- Expanded automated tests

### Phase 3: Industrial Integration

- MES integration
- LIMS integration
- Automated tester-data ingestion
- Historical lot analytics
- QA workflow integration
- Equipment and station monitoring

### Phase 4: Advanced Reliability Intelligence

- Online drift monitoring
- Model monitoring
- Champion/challenger models
- Uncertainty estimation
- Failure-mode analytics
- Cross-lot pattern discovery
- Digital reliability knowledge base

### Long-Term Vision

Build an explainable semiconductor reliability intelligence platform that helps engineering teams move from **reactive screening to predictive, evidence-based quality decisions**.

---

## FAQ

### General

**Q: What does ANOVIS detect?**

A: ANOVIS uses a CatBoost classifier to detect anomalous semiconductor behavior at the 96-hour stage using the available burn-in measurements and engineered features.

**Q: Does ANOVIS detect anomalies at 24 hours?**

A: No. The final production workflow uses 24-hour measurements as predictive context but performs anomaly classification at 96 hours.

**Q: What does ANOVIS predict at 168 hours?**

A: Three regression models predict IDDQ, Leakage and Propagation Delay at 168 hours.

**Q: Does the system replace QA engineers?**

A: No. The system provides model evidence, explanations and recommendations to support human QA inspection.

### Explainability

**Q: Why use SHAP?**

A: SHAP provides feature-level attribution showing which inputs contributed to the model's prediction and in which direction.

**Q: Does SHAP identify the physical root cause?**

A: No. SHAP explains the behavior of the predictive model. It should not be interpreted as proof of a physical defect mechanism.

**Q: Why use Gemini?**

A: Gemini converts verified model evidence into a concise, human-readable QA explanation. Gemini does not determine the anomaly classification.

### Deployment

**Q: Where are the ML models deployed?**

A: The CatBoost models run inside the FastAPI backend deployed on Render. A separate ML-serving deployment is not required for the current architecture.

**Q: Where is the frontend deployed?**

A: The React/Vite frontend is deployed on Vercel.

**Q: Where is data stored?**

A: Supabase PostgreSQL stores persistent application data, while Supabase Storage is used for persistent files such as generated reports.

**Q: Is the Gemini API key exposed to the browser?**

A: No. Gemini is called only from the backend. The API key is stored as a backend environment variable.

### Data & Evaluation

**Q: Are the current model metrics production guarantees?**

A: No. Current development metrics include evaluation on a synthetic matched test set derived from training trajectories. Independent real-world validation is required before production claims.

**Q: Can the system process a complete lot?**

A: Yes. The application supports lot/component-level processing and can return component-level predictions and lot-level summaries.

---

## Acknowledgments

### Open Source Libraries

- [CatBoost](https://catboost.ai/) — Gradient boosting and model inference
- [SHAP](https://shap.readthedocs.io/) — Model explainability
- [FastAPI](https://fastapi.tiangolo.com/) — Backend API framework
- [React](https://react.dev/) — Frontend framework
- [Vite](https://vite.dev/) — Frontend tooling
- [Pandas](https://pandas.pydata.org/) — Data processing
- [NumPy](https://numpy.org/) — Numerical computing
- [Scikit-learn](https://scikit-learn.org/) — ML utilities

### Platform Services

- [Supabase](https://supabase.com/) — PostgreSQL and object storage
- [Vercel](https://vercel.com/) — Frontend deployment
- [Render](https://render.com/) — Backend deployment
- [Google Gemini](https://ai.google.dev/) — AI-assisted QA report generation

---

## License

MIT License

```text
Copyright (c) 2026 Team ANOVIS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, subject to the conditions of the MIT License.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
```

---

**ANOVIS** — *Detect degradation. Predict reliability. Explain every decision.*

*Built for intelligent semiconductor quality assurance.*
