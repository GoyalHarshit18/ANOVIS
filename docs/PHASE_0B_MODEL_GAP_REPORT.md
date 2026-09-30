# PHASE 0B — GAP REPORT

## CRITICAL GAPS
- **Missing Legacy Module A Artifacts**: The new package specifies `PAT_Risk`, `Peer_Risk`, `Temporal_Risk`, and `IF_Risk` as mandatory input features for `component_24h_classifier`, `component_96h_classifier`, `B2_Early`, and `B2_96h`. However, the required artifacts (`pat_reference.pkl`, `isolation_forest.pkl`, `peer_scaler.pkl`, etc.) are missing from the ZIP. This breaks the entire inference pipeline, as the new models cannot run without the legacy risk scores.
- **Regression Model Version Mismatch**: Loading the `B0`, `B1`, and `B2` regression models failed with a `ValueError: <class 'numpy.random._pcg64.PCG64'> is not a known BitGenerator module.` This suggests they were trained with an incompatible `numpy`/`scikit-learn` version relative to the current environment and will crash in production.

## HIGH GAPS
- **Measurement Flattening**: Current database schema flattens checkpoints. The new models strictly differentiate between 0h, 24h, and 96h metrics (and calculate deltas between them). The schema must be refactored to support proper timeseries storage to avoid silently merging 0h/24h data.

## MEDIUM GAPS
- **Duplicate Artifacts**: `previous_model_artifacts/final_models/` contains identical models to `regression/`, leading to potential deployment confusion.

## LOW GAPS
- **Ablation Models in Package**: `station_raw_features_ablation.pkl` is an ablation model included in the production package. It must be explicitly excluded from production deployment to avoid accidental use over `station_disturbance_classifier.pkl`.

## FINAL DECISION MATRIX

| ARTIFACT | STATUS | ACTION |
| --- | --- | --- |
| `component_*_classifier.pkl` | REQUIRES_VERIFICATION | Wait for legacy Module A artifacts to be provided. |
| `fusion_96h_classifier.pkl` | READY_FOR_INTEGRATION | - |
| `latent_specialist.pkl` | READY_FOR_INTEGRATION | - |
| `station_disturbance_classifier.pkl`| READY_FOR_INTEGRATION | - |
| `station_raw_features_ablation.pkl` | ABLATION_ONLY | Do not deploy. |
| `B0_*`, `B1_*`, `B2_*` | REQUIRES_VERIFICATION | Resolve numpy version mismatch. |
| Legacy Module A artifacts | REQUIRED_BUT_MISSING | Must recover from previous builds. |
| `inference_configuration.pkl` | READY_FOR_INTEGRATION | Use for thresholds/features. |
| `evaluation_metrics/*.csv` | EVALUATION_ONLY | Ignore for inference. |
| `previous_model_artifacts/*` | DUPLICATE | Delete or ignore. |
