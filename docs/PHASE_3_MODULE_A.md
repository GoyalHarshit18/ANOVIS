# Phase 3: Module A Production Execution

## Objective
Execute the legacy Module A signals (PAT, Peer, Temporal, Isolation Forest) alongside the new `component_24h_classifier` securely over a successful `screening_run` ingested in Phase 2.

## Key Principles & Rules Honored
1. **Source of Truth:** Module A reads measurements strictly from the Phase 1 canonical database (`Measurement` table), tied to a specific `run_id` and `component_id`. It does not parse the CSV file.
2. **Isolation:** Signal engines are fully executed with component-level isolation. Processing fails over gracefully per-component without aborting the entire screening run.
3. **No Fabrication:** If a required checkpoint (e.g. `0h` or `24h`) is missing, the backend flags the component status as `UNAVAILABLE`. No fabrication or missing data imputation is applied across checkpoints.
4. **Idempotency:** Re-executing `POST /screening-runs/{run_id}/module-a` UPSERTS evidence and screening result states without duplicating records.
5. **Separation of Concerns:** Calculates all AI models securely inside the Python backend using `feature_builder.py` and canonical contracts. No business or ML logic occurs on the React frontend.

## Implementation Details

### Service Layer (`module_a_service.py`)
- **`get_component_measurements`**: Converts `Measurement` entity records back into the canonical `{Feature}_{Hour}h` dictionary map used by Legacy Module A and `feature_builder.py`.
- **`run_module_a_for_component`**: 
  - Validates the availability of `0h` and `24h` check-points.
  - Passes measurement dictionary to legacy engines (`pat_engine`, `peer_engine`, `temporal_engine`, `isolation_forest_engine`).
  - Passes outputs of legacy engines + measurements into `build_component_24h_vector`.
  - Executes the `component_24h_classifier.pkl`.
- **`run_module_a_for_run`**: The central orchestrator that iterates over all components tied to a specific run, executes Module A in isolation, handles per-component failures gracefully, and aggregates run completion summaries (`MODULE_A_COMPLETED` or `MODULE_A_COMPLETED_WITH_WARNINGS`).
- **Persistence (`save_module_a_evidence`)**: Idempotently upserts to the `AnomalyEvidence` and `ScreeningResult` tables with the complete legacy risk profiles, scores, and predicted values.

### API Layer
- **`POST /screening-runs/{run_id}/module-a`**:
  - Exposes a dedicated REST endpoint for orchestrating Phase 3 execution on any previously successfully ingested run.
  - Responds with `200 OK` including component-level summaries of `unavailable_components`, `failed_components`, and `processed_components`.

### Testing (`test_module_a_phase3.py`)
Provides full coverage (10 test cases) testing:
1. **Valid Execution:** Ensures standard evidence is fully persisted into `AnomalyEvidence` and `ScreeningResult`.
2. **Missing 0h / 24h Checkpoints:** Correctly flags the component as `UNAVAILABLE`.
3. **Multi-Component Execution:** Completes analysis correctly on components across the run.
4. **Isolation Contexting:** Ensures test measurements are run-isolated and do not leak between `RUN_A` and `RUN_B`.
5. **Component Failure Isolation:** A single component failure does not rollback or abort the analysis of valid components in the same run.
6. **Feature Contract Fulfillment:** The input payload aligns perfectly to `feature_builder` schemas exactly without None-injection.
7. **Idempotency:** A second API call gracefully overwrites existing models without duplicate SQL row generation.
