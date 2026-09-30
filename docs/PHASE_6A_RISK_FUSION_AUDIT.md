# PHASE 6A — RISK FUSION ARCHITECTURE & IMPLEMENTATION AUDIT

## PHASE 6A STATUS: PASS

The existing architecture has been inspected. Actual model behavior, DB mappings, and decision logic have been verified. Missing definitions are explicitly identified, and no assumptions were silently made. Implementation can proceed with a concrete plan.

---

### 1. Existing Risk Fusion Implementation
The backend currently contains a partially wired structural foundation for Risk Fusion:
- `backend/app/ml/risk_fusion.py`: Contains authoritative business logic (`compute_a_score`, `compute_ldi`, `determine_decision`). Active, production logic.
- `backend/app/services/risk_fusion_service.py`: Contains the application wrapper (`run_risk_fusion_for_component`). It manually performs inline inference for `Component_96h_Score` and `Late_Drift_Risk` instead of using a canonical feature builder. Active, production logic.
- `backend/app/api/screening.py`: Contains the target API endpoint `POST /screening-runs/{run_id}/risk-fusion`.

### 2. Fusion Model Details
**Artifact**: `fusion_96h_classifier.pkl`
- **Type**: `sklearn.pipeline.Pipeline`
- **Steps**: `StandardScaler()` → `LogisticRegression(class_weight='balanced', max_iter=2000, random_state=42)`
- **Expected Features (3)**: `['Supervised_Score', 'Component_96h_Score', 'Late_Drift_Risk']`
- **Classes**: `[0, 1]` (Binary Classification)
- **Output**: Calibrated probabilities available via `predict_proba()`
- **Metadata**: Verified against `inspection_results.json`.

### 3. Exact Fusion Feature Contract
There is **NO** dedicated canonical feature builder for Risk Fusion in `backend/app/inference/feature_builder.py`. The features are manually constructed inline in `risk_fusion_service.py`:
`X_fusion = np.array([[supervised_score, component_96h_score, late_drift_risk]])`
Phase 6 will need to formalize this into `build_fusion_vector`.

### 4. Module A Evidence Mapping
- **SOURCE**: Module A outputs are properly persisted in the `anomaly_evidence` and `screening_results` tables.
- **PAT_Risk, Peer_Risk, Temporal_Risk, IF_Risk**: Sourced from `anomaly_evidence` columns.
- **A_SCORE**: Sourced from `anomaly_evidence.a_score` or calculated on-the-fly via `compute_a_score`.
- **Supervised_Score**: Sourced from `screening_results.evidence["prediction_class"]` (or `prediction_probability`).

### 5. Module B Evidence Mapping
- **B0 / B1 / B2 Predictions**: Sourced correctly from `predictions` table.
- **prediction_risk, uncertainty_risk, S_SCORE**: **UNAVAILABLE / GAP**. The mathematical definitions exist in `backend/app/ml/safety_engine.py`, but this engine is **never** invoked by Module B (`module_b_service.py`). These values are currently always `None`.

### 6. Device / Lot / Station Evidence Mapping
- **DEVICE**: Sourced from `anomaly_origins.device_status`. A value of `"REJECT"` or `"FAIL"` triggers the static failure precedence.
- **LOT**: Sourced from `lot_analysis` table.
- **STATION**: Sourced from `anomaly_origins.station_status`. A value of `"DISTURBANCE"` correctly raises the `test_integrity_flag`.

### 7. LDI Status
- **Status**: IMPLEMENTED.
- **Formula**: `0.4 * a_score + 0.3 * prediction_risk + 0.2 * s_score + 0.1 * uncertainty_risk`
- **Location**: `backend/app/ml/risk_fusion.py:compute_ldi`
- **Condition**: Currently returns `None` if any input is missing (Phase 6 requirement).

### 8. S_SCORE Status
- **Status**: **NOT_DEFINED** (in runtime). The logic sits unused in `safety_engine.py` (Modified-Z of predicted value against reference) but is not executed or persisted.

### 9. Prediction_Risk Status
- **Status**: **NOT_DEFINED** (in runtime). Exists conceptually in `safety_engine.py` but is not wired up.

### 10. Uncertainty_Risk Status
- **Status**: **NOT_DEFINED** (in runtime). Exists conceptually in `safety_engine.py` but is not wired up.

### 11. Final Decision Logic
**CURRENT AUTHORITATIVE DECISION LOGIC**:
`backend/app/ml/risk_fusion.py` -> `determine_decision()`
This single implementation handles the cascading rule precedence (Hard static failure -> Data/model failure -> Test integrity -> High risk -> PASS/MONITOR).

### 12. Database Readiness
The current DB schema in `models.py` is **fully sufficient** for Phase 6.
- The `RiskFusionResult` table exists and includes columns for `a_score`, `s_score`, `prediction_risk`, `uncertainty_risk`, `ldi`, `fusion_score`, `final_decision`, and `decision_basis`.

### 13. API Readiness
The required API endpoint already exists and is wired to the correct service:
- `POST /screening-runs/{run_id}/risk-fusion`

### 14. Frontend Dependency Audit
The frontend (e.g., `ComponentsList.jsx`, `Anomaly.jsx`, `Dashboard.jsx`, `PredictiveAnalysis.jsx`) expects:
- `a_score`, `ldi`, `decision`, `prediction_risk`, `s_score`, `uncertainty_risk`.
- **Mismatch**: The backend currently cannot supply `ldi`, `prediction_risk`, `s_score`, or `uncertainty_risk` due to the Module B gap.

### 15. Mock / Fallback Audit
- **Production Fallback**: `backend/app/ml/risk_fusion.py` uses `or 0.0` for sub-scores in `compute_a_score` when `anomaly_evidence` inputs are missing.
- **Frontend Mock**: `frontend/src/pages/Anomaly.jsx` manually mocks an A_SCORE reduction using `data.a_score * 0.4` for demo purposes when a user tweaks settings.

### 16. Duplicate Logic Audit
- **PASS**: No duplicate implementations were found for `A_SCORE`, `LDI`, or decision logic.

### 17. LOT_00 Readiness
- **BLOCKED**: While LOT_00 successfully ran through Phase 5, the absence of Module B safety metrics (`S_SCORE`, `prediction_risk`, `uncertainty_risk`) causes the LDI calculation to immediately return `None`, preventing the High Risk rule precedence from functioning properly.

### 18. Missing Pieces / Exact Blockers
1. **Safety Engine Disconnected**: `app/ml/safety_engine.py` must be executed to compute the missing Module B risks (`S_SCORE`, `prediction_risk`, `uncertainty_risk`).
2. **No Canonical Feature Builder**: `risk_fusion_service.py` creates inline numpy arrays for the 3 fusion features instead of using `feature_builder.py`.

---

## 19. REQUIRED PHASE 6B–6H PLAN

### PHASE 6B — Fusion Model Integration
- **Modify**: `backend/app/inference/feature_builder.py`
- **Action**: Create `build_fusion_vector(supervised_score, component_96h_score, late_drift_risk)`.
- **Modify**: `backend/app/services/risk_fusion_service.py` to use the canonical builder instead of inline numpy array construction.

### PHASE 6C — Evidence Aggregation
- **Modify**: `backend/app/services/risk_fusion_service.py` (or `module_b_service.py`).
- **Action**: Wire in `app.ml.safety_engine.get_safety_metrics()` to actually compute and retrieve `S_SCORE`, `prediction_risk`, and `uncertainty_risk`.

### PHASE 6D — Final Decision Engine
- **Action**: Rely entirely on the existing `determine_decision` in `risk_fusion.py`. No new files needed. Verify threshold parsing against `inference_configuration.pkl`.

### PHASE 6E — Persistence + Audit
- **Action**: Ensure `RiskFusionResult` table is fully populated without `None` values (assuming Phase 6C resolves the missing inputs).

### PHASE 6F — API
- **Action**: Validate `POST /screening-runs/{run_id}/risk-fusion` error handling and status updates.

### PHASE 6G — E2E Real LOT_00
- **Action**: Re-run the LOT_00 pipeline through Phase 6 using `run_e2e.py` to ensure all fields are natively populated.

### PHASE 6H — Regression Tests
- **Action**: Add specific unit tests for `compute_ldi` resolving `None` correctly and the canonical fusion feature builder.

---

## PHASE 6B STATUS
- **Status:** PASS
- **Canonical Builder Created:** Implemented `build_fusion_vector` in `feature_builder.py`.
- **Exact Feature Order:** Preserved exact order `['Supervised_Score', 'Component_96h_Score', 'Late_Drift_Risk']`.
- **Validation:** Added strict checks to reject NaNs, non-numeric values, and incorrect feature counts. No fallback-to-zero logic is introduced.
- **Service Updated:** Replaced inline `np.array` construction in `risk_fusion_service.py` with the new canonical builder.
- **Tests Executed:** Added and passed 5 focused tests verifying input handling, validations, None/NaN behavior, and downstream model acceptance. Regression tests across Phase 1-5 continue to pass seamlessly.
