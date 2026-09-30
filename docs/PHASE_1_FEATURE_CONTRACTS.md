# PHASE 1 — FEATURE CONTRACTS

## Authoritative Order Principle
Features are no longer passed as generic kwargs or implicitly flattened structs. Before any model is called, `app/inference/feature_builder.py` constructs a strict, ordered list of floats corresponding exactly to the artifact's `feature_names_in_` property (or configuration metadata if the pipeline does not export it).

## Verification Strategy
We used a Python script loading each `joblib` artifact and extracting `feature_names_in_` either directly from the `IsolationForest`/`Classifier` instance or its first pipeline step (e.g. `StandardScaler`).

### B0, B1, B2-Early, B2-96h
- **Artifact**: `B0_IDDQ.pkl`, etc.
- **Verification**: Missing `feature_names_in_` explicitly inside the `.pkl` artifact. Sourced from the Phase 0B known configuration.
- **Required Checkpoints**: 0h, 24h (and 96h for B2-96h).
- **Fallback**: NONE. Missing data produces `UNAVAILABLE`.
- **Order (B0/B1)**: Iddq_0h, Iddq_24h, Leakage_0h, Leakage_24h, PropDelay_0h, PropDelay_24h.
- **Order (B2-Early)**: Above + PAT_Risk, Peer_Risk, Temporal_Risk, IF_Risk.

### Component Early (24h) Classifier
- **Artifact**: `anomaly_detection/component_24h_classifier.pkl`
- **Verification**: Directly extracted `feature_names_in_` from the artifact.
- **Required Checkpoints**: 0h, 24h.
- **Feature Count**: 24.
- **Output**: `predict_proba()` used if probabilistic. 

### Component Late (96h) Classifier
- **Artifact**: `anomaly_detection/component_96h_classifier.pkl`
- **Verification**: Directly extracted.
- **Required Checkpoints**: 0h, 24h, 96h.
- **Feature Count**: 43.

### Latent Specialist
- **Artifact**: `anomaly_detection/latent_specialist.pkl`
- **Verification**: Directly extracted.
- **Required Checkpoints**: 0h, 24h, 96h.
- **Feature Count**: 21.

### Station Disturbance Classifier
- **Artifact**: `station_detection/station_disturbance_classifier.pkl`
- **Verification**: Directly extracted.
- **Required Checkpoints**: 0h, 24h.
- **Feature Count**: 20.

### Risk Fusion Classifier
- **Artifact**: `anomaly_detection/fusion_96h_classifier.pkl`
- **Verification**: Directly extracted.
- **Features**: `Supervised_Score`, `Component_96h_Score`, `Late_Drift_Risk`.
