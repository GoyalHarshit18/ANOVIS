# PHASE 0 — ARCHITECTURE & CONTRACT FREEZE

## 1. Project Objective
Build a robust, end-to-end AI-driven anomaly detection system for semiconductor burn-in and screening (SIH26170). The system evaluates components against absolute thresholds, peer population behavior, and historical drift to detect anomalous devices, evaluate lot/station health, and predict 168h end-of-life characteristics.

## 2. System Architecture
- **Input**: CSV file uploads containing component measurements.
- **Backend**: FastAPI web server handling validation, screening orchestration, risk fusion, and API endpoints.
- **Database**: PostgreSQL storing historical data, measurements, and screening results.
- **ML Layer**: Python-based inference engine (Module A for screening, Module B for predictions, Risk Fusion for decision). ML models are loaded from disk as serialized artifacts (e.g. `.pkl`), not from the database.
- **Frontend**: React SPA utilizing TailwindCSS and Recharts, acting strictly as a presentation layer reading from the FastAPI backend.

## 3. Frontend Responsibilities
- **Data Presentation**: Strictly a presentation layer. It displays values provided by the backend.
- **State Handling**: Must gracefully handle and display loading states, error states, and unavailable states.
- **N/A Handling**: Must display `N/A` for any missing or `null` analytical values (see Null/N/A Contract).
- **Prohibitions**: The frontend MUST NOT perform analytical calculations (PAT, A_SCORE, predictions, etc.) or fabricate mock data.

## 4. Backend Responsibilities
- **Data Validation**: Authoritative validation of input data schemas, bounds, and consistency.
- **Orchestration**: Directing the pipeline (Validation → Module A → Module B → Risk Fusion).
- **Persistence**: Connecting to the PostgreSQL database for CRUD operations.
- **API Contracts**: Serving strictly defined JSON contracts to the frontend.

## 5. Database Responsibilities
- **Storage Strategy**: Relational storage (SQLAlchemy -> PostgreSQL).
- **Core Entities**:
  - `lots`: Lot metadata.
  - `components`: Component identity and lot/station mappings.
  - `measurements`: Raw electrical readings (Iddq, Leakage, PropDelay) indexed by component and checkpoint hour.
  - `screening_results`: Final module scores, evidence JSON, decisions, and warnings.
  - `screening_runs`: Aggregated metadata for batch processing.

## 6. ML Artifact Responsibilities
- **Storage**: Model binaries and scalers (`.pkl` files) remain on the filesystem (`models/` directory) and are loaded into memory via `model_registry.py`.
- **Database Role**: The database only stores model metadata (version, hash) and the results of inferences, never the binaries themselves.

## 7. Input CSV Contract
The primary input is a CSV file containing multiple components from a single lot.
- **Expected Fields**: `component_id`, `lot_id`, `station` (if applicable).
- **Time-Series Features**: `Iddq_uA_0h`, `Iddq_uA_24h`, `Iddq_uA_96h`, `Iddq_uA_168h` (and similar for `Leakage_nA` and `PropDelay_ns`).
- **Ground Truth**: `ground_truth` (used strictly for validation/evaluation, not inference).

## 8. Checkpoint Contract
The timeline is strictly fixed to **0h, 24h, 96h, and 168h**. 
Missing data must remain missing and not be interpolated. 96h must remain 96h.

## 9. Module A Contract
**Current Outputs**:
- **PAT**: Score, modified-z, parameter evidence.
- **Peer Residual**: Expected value, residual, normalized residual, score.
- **Early Temporal**: Drift, slope, temporal evidence, score.
- **Isolation Forest**: Raw anomaly score, prediction, derived score.
- **A_SCORE**: Final aggregated anomaly score.

## 10. Device Anomaly Contract
Defined as an individual component showing abnormal behavior relative to historical/peer populations. Represented by combinations of PAT, Peer, Temporal, and IF scores culminating in the `A_SCORE`. Decisions are dictated exclusively by the backend.

## 11. Lot Anomaly Contract
Compares the current lot population against a historical healthy reference lot.
**Outputs**: Lot shift score, status, affected component counts, parameter distribution evidence.

## 12. Station Anomaly Contract
Evaluates within-station behavior, cross-station variance, and test integrity/calibration drift.
**Outputs**: Station shift score, within/cross-station residuals, test integrity flags.

## 13. Module B Contract
Predicts 168h end-of-life values using 0h and 24h inputs.
**Current State**: B0 models are loaded. B1 and B2 models are currently UNAVAILABLE.

## 14. Future-Risk Contract
Provides safety envelopes and prediction intervals for 168h metrics, boiling down to `prediction_risk`, `uncertainty_risk`, and `s_score`. 

## 15. Risk Fusion Contract
Aggregates `A_SCORE`, `S_SCORE`, `LDI`, and risks to output a final `decision`, `decision_reason`, and `warnings`. Logic is backend-owned.

## 16. Final Decision Contract
Supported values: `PASS`, `MONITOR`, `REVIEW_REQUIRED`, `REJECT`, `REPEAT_MEASUREMENT`, `DATA_UNAVAILABLE`.

## 17. API Inventory
- `GET /health`: Returns system status and loaded models.
- `POST /screen`: Single component screening.
- `POST /predict`: Single component 168h prediction.
- `GET /components`: Retrieves list of screening results.
- `GET /lots`: Retrieves list of lots.
- `GET /lot/{lot_id}`: Retrieves lot analytics.

## 18. Existing Database Inventory
- **lots**: `id`, `lot_id`, timestamps.
- **components**: `id`, `component_id`, `device_type`, `lot_id`, `station_id`.
- **measurements**: `id`, `component_id`, `timestamp`, `hour`, `temperature`, `voltage`, `iddq_ua`, `leakage_na`, `prop_delay_ns`.
- **screening_results**: `id`, `component_id`, scores (`ldi`, `a_score`, `s_score`), `prediction_risk`, `uncertainty_risk`, `predicted_168h`, `decision`, `stage`, `evidence` JSONs.
- **screening_runs**: Aggregates for batch screening operations.

## 19. Existing Model Inventory
- `b0_models`, `inference_config`, `reference_limits`, `pat_reference`, `peer_scaler`, `peer_knn`, `isolation_forest`, `if_scaler`, `temporal_reference`, `drift_reference`, `future_envelope`.

## 20. Mock-Data Audit
- **Backend Test Fixtures**: `app/db/seed.py` produces synthetic data for testing.
- **Frontend Fallbacks**: UI logic exists for `aScoreModified` demonstration (e.g. `data.a_score * 0.4`).
- No hardcoded production analytical mocks exist in the primary API responses, but UI placeholders exist for Lot/Station tabs.

## 21. Missing Functionality
- Full Lot statistical distribution analysis.
- Station anomaly endpoint and logic.
- B1 and B2 prediction models.
- Dedicated `/component/{id}/history` and `/runs` endpoints.

## 22. Known Fallback/Default-Value Issues
- `api/screening.py` flattens measurements into a single row using fallback logic (e.g. `Iddq_uA_24h` or `Iddq_uA_0h`), breaking the 0h/24h/96h checkpoint contract.
- Fallback default values are used in `app/db/models.py` for default stages and temperatures if omitted.

## 23. Phase 1 Requirements
- Rewrite database measurement persistence to explicitly support independent 0h, 24h, 96h, and 168h records.
- Implement proper Lot and Station anomaly analytical endpoints in the backend.
- Refactor API routes to align with the Future Endpoint Structure (`/runs`, `/component/{id}/history`, etc.).
- Establish dynamic parameter fetching without relying on `or` fallback conditionals in the API insertion layer.
