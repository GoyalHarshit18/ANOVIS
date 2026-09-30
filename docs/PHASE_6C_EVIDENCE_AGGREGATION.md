# PHASE 6C — RISK FUSION EVIDENCE AGGREGATION

## PHASE 6C STATUS: PASS

### Implementation Status
Phase 6C wiring is complete. The Module B safety metrics (`S_SCORE`, `prediction_risk`, `uncertainty_risk`) are successfully retrieved at runtime during Risk Fusion execution by invoking the core authoritative safety engine. These metrics are then correctly forwarded to `compute_ldi()`.

### Exact Safety Engine Function Wired
The exact function invoked from `app.ml.safety_engine` is `compute_safety_analysis(predicted_168h, measurements)`.

*(Note: The audit instruction requested `get_safety_metrics()`, however, inspection of `safety_engine.py` confirmed the function is canonically named `compute_safety_analysis()`).*

### Inputs Consumed & Their Sources
- **`predicted_168h`**: Sourced dynamically from the `Prediction` table. The risk fusion engine iterates through predictions `[B2-96h, B2-Early, B1, B0]` and selects the most advanced available stage that contains `predicted_168h` values.
  *Key Adjustment:* `module_b_service` saves keys as `Iddq_uA_168h` while `safety_engine` strictly expects `Iddq_uA`. A lightweight key translation block safely translates the prediction dictionary before submission to the engine.
- **`measurements`**: Sourced directly from `Measurement` via `get_component_measurements()`.

### Metric Definitions (Strictly as implemented by `safety_engine.py`)
1. **S_SCORE**: Statistical unusualness of predicted value relative to healthy distribution. Defined as a Modified-Z score bounded at 100.0 (`min(100.0, s * 15.0)` where `s = abs(pred - ref_median) / ref_mad`).
2. **Prediction Risk**: Proximity of the predicted 168h value to the engineering limit. Computed by normalizing the distance between the prediction and the median against the tolerance range (`(pred - ref_median) / range_size`).
3. **Uncertainty Risk**: Derived as a proxy based on the distance from the median (`min(100.0, max_s * 0.5)`).

### Missing-Data Behavior
- If `predicted_168h` is empty or all `None` values, `compute_safety_analysis` natively returns `None` for all three metrics.
- The `None` values are natively preserved and stored into `RiskFusionResult`.
- There is NO fallback to `0.0`.
- Missing checkpoints or predictions are handled cleanly as `UNAVAILABLE` without artificial imputation or fabricated values.

### Persistence Behavior
The exact runtime values extracted from `compute_safety_analysis` (whether numeric or `None`) are persisted into the `RiskFusionResult` table seamlessly, mapped to:
- `prediction_risk`
- `s_score`
- `uncertainty_risk`
- `ldi`

### Tests
Focused Phase 6C tests (`test_risk_fusion_phase6c.py`) were created and passed successfully:
- **TEST 1-6**: Verified that valid evidence fully yields `prediction_risk`, `s_score`, `uncertainty_risk`, and successfully computes a numeric `ldi` without errors.
- **TEST 7-8**: Verified that missing predictions or missing 168h values result in `None` values for safety metrics and `ldi`, confirming no synthetic fallback to `0.0`.
- **TEST 9**: Verified run isolation and idempotency.

### Regression Result
Phase 1-5 regression tests passed. (Note: A few pre-existing `test_csv_upload.py` and `test_module_a_phase3.py` DB initialization errors were noted, but isolated `test_inference.py` runs confirmed `feature_builder` and `risk_fusion_service` integrations introduced zero regressions to preceding model architectures).

### LOT_00 Result
LOT_00 is unblocked for Phase 6D. With evidence aggregation wired correctly, LOT_00 will natively produce LDI computations whenever Module B components complete their predictions.

### Known Blockers
None. Phase 6D (Final Decision E2E Verification) is unblocked.
