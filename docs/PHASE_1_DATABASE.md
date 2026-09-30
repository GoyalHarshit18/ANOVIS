# PHASE 1 — DATABASE FOUNDATION

## Database Truth Policy
- **Checkpoints**: Measurements are persisted strictly according to their `checkpoint_hour` (0, 24, 96, 168).
- **Missing Data**: Missing data is explicitly saved as `NULL` / absent. There are no silent fallbacks or manual imputations in the analytical pipeline.
- **Independence**: The `measurements` table retains an independent row for every checkpoint observed for a component in a specific run.

## Tables & Architecture

### Core Entities
- `lots`: Identity for a component lot (`lot_id` unique).
- `components`: Identity for a single device (`component_id` unique). Linked to `lots`.
- `screening_runs`: Represents a single screening invocation or CSV ingestion (`run_id` unique). Contains metadata about completion status and parsed rows.

### Measurements (CRITICAL)
- `measurements`: Captures `checkpoint_hour`, `temperature`, `voltage`, `iddq_ua`, `leakage_na`, `prop_delay_ns`.
  - **Constraint**: `CHECK (checkpoint_hour IN (0, 24, 96, 168))`
  - **Unique Index**: `UNIQUE (run_id, component_id, checkpoint_hour)` guarantees one measurement per checkpoint per run for a component.

### Results & Persistence
- `screening_results`: Final aggregated decision.
  - **Unique Index**: `UNIQUE (run_id, component_id)`.
- `anomaly_evidence`: Persists detailed Module A sub-scores (PAT, Peer, Temporal, IF).
- `anomaly_origins`: Represents where the anomaly originated (Device, Lot, Station).
- `lot_analysis`: Captures lot shift scoring and affected counts.
- `station_analysis`: Captures station shift scoring and test integrity details.

### Predictions & Confidence
- `predictions`: Persists exact predictions. Maps `model_name` and `model_version`.
- `prediction_intervals`: Persists upper/lower bounds separately, marked as calibrated or uncalibrated.
- `safety_envelopes`: Persists static or contextual safety boundaries against which parameters are compared.
- `risk_fusion_results`: Final unified LDI and decision logic outputs.

### Auditability
- `model_versions`: Auditable trail mapping `model_name` to exact `artifact_hash`.
- `audit_events`: Stores missing checkpoints, warnings, execution events.

## Null / Missing-Data Policy
No queries or processing functions are permitted to convert `NULL` to `0`, `""`, or generic defaults. If a model requires 24h data and it is absent, the model status evaluates strictly to `UNAVAILABLE`.
