# PHASE 0B — MODEL INVENTORY

## 1. Artifact Inventory

| Artifact | Type | Module | Inputs | Outputs | Preprocessing | Checkpoints | Dependencies | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `component_24h_classifier.pkl` | Pipeline (Imputer + ExtraTrees) | Module A (Early) | 24 features (Raw, Delta, PAT/Peer/Temporal/IF risks) | Class (0/1) | SimpleImputer | 0h, 24h | Old Module A artifacts | PRODUCTION_CANDIDATE |
| `component_96h_classifier.pkl` | Pipeline (Imputer + ExtraTrees) | Module A (Late) | 43 features (24h features + 96h + Deltas) | Class (0/1) | SimpleImputer | 0h, 24h, 96h | Old Module A artifacts | PRODUCTION_CANDIDATE |
| `fusion_96h_classifier.pkl` | Pipeline (Scaler + LogReg) | Risk Fusion | 3 features (`Supervised_Score`, `Component_96h_Score`, `Late_Drift_Risk`) | Class (0/1) | StandardScaler | 0h, 24h, 96h | Component & Latent models | PRODUCTION_CANDIDATE |
| `latent_specialist.pkl` | Pipeline (Imputer + ExtraTrees) | Module A (Latent) | 21 features (Raw + 96h + Drift) | Class (0/1) | SimpleImputer | 0h, 24h, 96h | None directly | PRODUCTION_CANDIDATE |
| `station_disturbance_classifier.pkl` | Pipeline / Model | Station | 21 features (Raw + Delta) | Unknown (likely Class) | Unknown | 0h, 24h | None | PRODUCTION_CANDIDATE |
| `station_raw_features_ablation.pkl`| Pipeline / Model | Station | 11 features (Raw only) | Unknown | Unknown | 0h, 24h | None | ABLATION_ONLY |
| `B0_{IDDQ,Leakage,Delay}.pkl` | Numpy-dependent Regressor | Module B | 6 features (0h, 24h Raw) | Continuous (168h) | Self-contained | 0h, 24h | numpy version | PRODUCTION_CANDIDATE |
| `B1_{IDDQ,Leakage,Delay}.pkl` | Numpy-dependent Regressor | Module B | 11 features (Raw + Temp/Supply) | Continuous (168h) | Self-contained | 0h, 24h | numpy version | PRODUCTION_CANDIDATE |
| `B2_Early_{IDDQ,Leakage,Delay}.pkl`| Numpy-dependent Regressor | Module B | 24 features (B1 + Deltas + Risks)| Continuous (168h) | Self-contained | 0h, 24h | Old Module A artifacts | PRODUCTION_CANDIDATE |
| `B2_96h_{IDDQ,Leakage,Delay}.pkl` | Numpy-dependent Regressor | Module B | 42 features (B2_Early + 96h) | Continuous (168h) | Self-contained | 0h, 24h, 96h | Old Module A artifacts | PRODUCTION_CANDIDATE |
| `inference_configuration.pkl` | dict | Config | None | Dict of thresholds, feature lists | N/A | N/A | None | CONFIGURATION |

## 2. Missing Artifacts
The following artifacts are reported missing in the MANIFEST, but their outputs (`PAT_Risk`, `Peer_Risk`, `Temporal_Risk`, `IF_Risk`) are explicitly required as input features by the new models (`component_24h_classifier.pkl`, `component_96h_classifier.pkl`, `B2_Early`, `B2_96h`):
- `pat_reference.pkl` (REQUIRED_BUT_MISSING)
- `peer_knn.pkl` (REQUIRED_BUT_MISSING)
- `peer_scaler.pkl` (REQUIRED_BUT_MISSING)
- `peer_reference_targets.pkl` (REQUIRED_BUT_MISSING)
- `peer_scales.pkl` (REQUIRED_BUT_MISSING)
- `temporal_reference.pkl` (REQUIRED_BUT_MISSING)
- `isolation_forest.pkl` (REQUIRED_BUT_MISSING)
- `if_scaler.pkl` (REQUIRED_BUT_MISSING)
- `inference_config.pkl` (REPLACED by `inference_configuration.pkl`)

## 3. Duplicate Artifacts
The `previous_model_artifacts/final_models/` directory contains copies of B0, B1, and B2 models which are identical in name to the ones in `regression/`. They are classified as DUPLICATE.

## 4. Evaluation Metrics
The `evaluation_metrics` folder contains CSV files summarizing model performance. These are EVALUATION_ONLY and should not be used in inference or as production outputs.
- `regression_results.csv`: MAE/RMSE/R2 for regression.
- `staged_results.csv`: Metrics per stage.
- `comparison_96h.csv`: TPR/FPR comparison.
- `family_gated.csv`: Gated fusion metrics.
- `fusion_results.csv`, `fusion_defect_report.csv`: Risk fusion performance.
- `drift_shift_report.csv`, `future_risk_results.csv`, `late_results.csv`, `latent_specialist_results.csv`, `specialist_fusion_report.csv`: Sub-model benchmarks.
