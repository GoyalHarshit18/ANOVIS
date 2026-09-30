# PHASE 0 — GAP REPORT

This document catalogs the current implementation state of the SIH26170 system against the final architecture contracts.

## 1. System Architecture
- **FastAPI / React integration**: IMPLEMENTED
- **PostgreSQL connectivity**: IMPLEMENTED
- **Model artifact loading**: IMPLEMENTED
- **File upload endpoint**: NOT_IMPLEMENTED

## 2. Input Contracts
- **CSV Data Validation**: PARTIALLY_IMPLEMENTED (Exists in `validation_service.py` but is minimal)
- **Time Checkpoints (0h, 24h, 96h, 168h)**: NOT_IMPLEMENTED (Database flattens time-series into single generic measurements)
- **Zero-Mock compliance**: PARTIALLY_IMPLEMENTED (Test fixtures remain in `seed.py`, fallback values used in UI state tests)

## 3. Database Integrity
- **lots table**: IMPLEMENTED
- **components table**: IMPLEMENTED
- **measurements table**: NEEDS_VERIFICATION / RISK (Schema is missing an explicit checkpoint structure; `api/screening.py` uses fallback `or` logic to squash 0h/24h into one record)
- **screening_results table**: IMPLEMENTED
- **screening_runs table**: PARTIALLY_IMPLEMENTED (Schema exists, but upload tracking is incomplete)

## 4. Module A (Screening)
- **PAT**: IMPLEMENTED
- **Peer Residual**: IMPLEMENTED
- **Early Temporal Anomaly**: IMPLEMENTED
- **Isolation Forest**: IMPLEMENTED
- **A_SCORE calculation**: IMPLEMENTED
- **Evidence JSON output**: IMPLEMENTED

## 5. Anomaly Types
- **Device Anomaly**: IMPLEMENTED
- **Lot Anomaly**: PARTIALLY_IMPLEMENTED (Endpoint exists but relies on naive DB loops; true statistical shift not calculated)
- **Station Anomaly**: NOT_IMPLEMENTED (No endpoint, only a UI placeholder)

## 6. Module B (Predictions)
- **B0 Models (0/24h -> 168h)**: IMPLEMENTED
- **B1 Models (0/96h -> 168h)**: NOT_IMPLEMENTED / UNAVAILABLE
- **B2 Models (24/96h -> 168h)**: NOT_IMPLEMENTED / UNAVAILABLE

## 7. Future Risk & Fusion
- **Safety/Future Envelope**: IMPLEMENTED
- **Prediction Risk**: IMPLEMENTED
- **Uncertainty Risk**: IMPLEMENTED
- **S_SCORE calculation**: IMPLEMENTED
- **Risk Fusion Logic (decision tree)**: IMPLEMENTED
- **Decision precedence rules**: IMPLEMENTED

## 8. Frontend Integration
- **Backend-Driven Values**: IMPLEMENTED
- **No client-side ML logic**: IMPLEMENTED
- **Null / N/A handling**: PARTIALLY_IMPLEMENTED
- **Lot / Station dashboards**: NOT_IMPLEMENTED (Placeholders exist but not connected to true backend analysis)

## 9. Major Risks & Technical Debt
- **Measurement Flattening**: `api/screening.py` uses `measurements.get("Iddq_uA_24h") or measurements.get("Iddq_uA_0h")`. This silently discards temporal distinction and violates the Checkpoint Contract.
- **Silent Fallbacks**: Default stage and temperature fallback values exist in the API layer.
- **Legacy Dead Code**: Functions in `components.py` and `lots.py` explicitly retained for "legacy demo seed compat".
