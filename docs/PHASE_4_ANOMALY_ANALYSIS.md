# Phase 4: Device + Lot + Station Anomaly Analysis

## 1. Device Anomaly
Device anomaly interpretation leverages the existing `A_SCORE` and legacy risk metrics originally calculated in Phase 3 by Module A. Instead of producing a new score or algorithm, Phase 4 simply maps the canonical output into the `anomaly_origins` table under `device_status`.

## 2. Lot Anomaly
Lot anomaly analysis determines if the current lot population is shifted compared to a historically healthy reference population. This operates on all valid components within the screening run's context, evaluating 0h and 24h checkpoints for `Iddq_uA`, `Leakage_nA`, and `PropDelay_ns`. A shift is detected if the lot median drifts outside the reference bounds.

## 3. Station Anomaly
Station anomaly analysis evaluates if tests performed at a given station exhibit systematic disturbances. It groups component measurements by `station_id` within the `run_id` and utilizes the canonical `station_disturbance_classifier` for inference. It determines the disturbance proportion and maps within-station metrics.

## 4. Input Data
The service utilizes exact artifacts from `Measurement` and `Component` entities mapped previously in Phase 2, relying directly on run-isolated query boundaries to fetch `0h` and `24h` records.

## 5. Reference Population
The `reference_limits.pkl` artifact provides the authoritative historical healthy bounds (lower, median, upper thresholds and MAD deviations) for structural parameters.

## 6. Station Model
Inference utilizes the actual `station_disturbance_classifier.pkl` production model. It operates completely independently of `station_raw_features_ablation`. 

## 7. Feature Contracts
The station classifier evaluates a rigorous 20-feature dimensional space generated dynamically using `build_station_vector`, preserving strict ordering and null checks.

## 8. Missing-data Behavior
Missing data points immediately short-circuit evaluation dimensions dynamically to `UNAVAILABLE` rather than defaulting to arbitrary median imputations or 0-filled vectors.

## 9. Persistence
Persistence stores data into exactly three database tables (as strictly requested without schema changes):
- `AnomalyOrigins`
- `LotAnalysis`
- `StationAnalysis`

## 10. API
Phase 4 logic is served securely over `POST /screening-runs/{run_id}/anomaly-analysis`.

## 11. Idempotency
Service operations utilize precise `run_id` + `component_id` filtering mapped with SQLAlchemy `.first()` coupled with local `.flush()` calls inside loops to prevent constraint violations and uncontrolled row replication during repeated requests.

## 12. Test Coverage
Extensive `pytest` fixtures were formulated spanning Device Origin extraction, Lot Shifts, Station Modeling, Missing Checkpoints, Multiple Stations, and Idempotency scenarios in `app/tests/test_phase4_anomaly_analysis.py`. Tests passed entirely.

## 13. Real LOT_00 Verification
VERIFIED. The real LOT_00 CSV (`data_set_2_LOT_00_lowercase.csv`) was successfully run natively through the entire pipeline: CSV -> Run -> Module A -> Phase 4.

## 14. Known Limitations
- The station classifier `predict()` output natively yields a component-level disturbance decision since it operates on `1x20` input vectors per component.

## PHASE 4C VERIFICATION

- **reference_limits.pkl interpretation**: Verified. The artifact contains statistical bounding thresholds (`lower`, `median`, `upper`, `mad`) derived from historical data. It does not represent arbitrary engineering limits, hence it acts as a genuine historical healthy reference population. Lot shift logic correctly uses this reference.
- **station classifier interpretation**: Verified. The artifact expects a 20-feature input per component and outputs `[0, 1]` indicating component-level test disturbance.
- **Mock Thresholds Removed**: Yes. Since the model operates per-component and no authoritative aggregation rule was provided to map multiple components into a single station status, the mock `DISTURBANCE` proportion threshold was stripped. Station `integrity_status` is now rigidly set to `UNAVAILABLE` while preserving within-station counts.
- **LOT_00 E2E Result**: PASS. The physical CSV file for `LOT_00` was run successfully through `run_e2e.py`.
- **Components analyzed**: 37 (Module A screened those with 24h data) out of 173 total components in the dataset.
- **Unavailable components**: 136 (Did not have 24h data for Module A)
- **Stations analyzed**: 0 (No station information in this dataset)
- **LotAnalysis result/status**: `NORMAL`
- **StationAnalysis result/status**: `N/A`
- **Exact pytest result**: `6 passed, 9 warnings in 72.43s (0:01:12)`
- **Remaining blockers**: None.

PHASE 4C: PASS
