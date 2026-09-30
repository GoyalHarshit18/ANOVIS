# PHASE 0C — MODEL RECOVERY STATUS

**Legacy Module A artifacts were absent from the new trained-model ZIP, but are present in the existing backend/models directory.**

LEGACY MODULE A

PAT artifact:
FOUND (backend/models/pat_reference.pkl)

Peer artifacts:
FOUND (backend/models/peer_knn.pkl, peer_scaler.pkl, etc.)

Temporal artifact:
FOUND (backend/models/temporal_reference.pkl)

Isolation Forest artifacts:
FOUND (backend/models/isolation_forest.pkl, if_scaler.pkl)

------------------------------------------------------------

REGRESSION

B0:
LOADABLE (with NumPy >= 2.0)

B1:
LOADABLE (with NumPy >= 2.0)

B2-Early:
LOADABLE (with NumPy >= 2.0)

B2-96h:
LOADABLE (with NumPy >= 2.0)

------------------------------------------------------------

NEW ANOMALY MODELS

component_24h:
LOADABLE

component_96h:
LOADABLE

latent_specialist:
LOADABLE

------------------------------------------------------------

STATION

station_disturbance_classifier:
LOADABLE

station_raw_features_ablation:
ABLATION_ONLY

------------------------------------------------------------

FUSION

fusion_96h_classifier:
LOADABLE

------------------------------------------------------------

CONFIG

inference_configuration:
LOADABLE
