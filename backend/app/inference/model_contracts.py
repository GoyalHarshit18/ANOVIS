"""
Authoritative Model Feature Contracts
Derived from actual scikit-learn artifact inspection (feature_names_in_) and configuration.
"""

# ---------------------------------------------------------
# NEW ANOMALY CLASSIFIERS
# ---------------------------------------------------------

COMPONENT_24H_FEATURES = [
    "IDDQ_0h_uA",
    "Leakage_0h_nA",
    "Delay_0h_ns",
    "IDDQ_24h_uA",
    "Leakage_24h_nA",
    "Delay_24h_ns",
    "IDDQ_delta_0_24",
    "IDDQ_slope_0_24",
    "IDDQ_relative_0_24",
    "Leakage_delta_0_24",
    "Leakage_slope_0_24",
    "Leakage_relative_0_24",
    "Delay_delta_0_24",
    "Delay_slope_0_24",
    "Delay_relative_0_24",
    "Temperature_C",
    "Supply_V",
    "Nominal_V",
    "Temperature_24h_C",
    "Supply_24h_V",
    "PAT_Risk",
    "Peer_Risk",
    "Temporal_Risk",
    "IF_Risk"
]

COMPONENT_96H_FEATURES = [
    "IDDQ_0h_uA",
    "Leakage_0h_nA",
    "Delay_0h_ns",
    "IDDQ_24h_uA",
    "Leakage_24h_nA",
    "Delay_24h_ns",
    "IDDQ_delta_0_24",
    "IDDQ_slope_0_24",
    "IDDQ_relative_0_24",
    "Leakage_delta_0_24",
    "Leakage_slope_0_24",
    "Leakage_relative_0_24",
    "Delay_delta_0_24",
    "Delay_slope_0_24",
    "Delay_relative_0_24",
    "Temperature_C",
    "Supply_V",
    "Nominal_V",
    "Temperature_24h_C",
    "Supply_24h_V",
    "PAT_Risk",
    "Peer_Risk",
    "Temporal_Risk",
    "IF_Risk",
    "IDDQ_96h_uA",
    "Leakage_96h_nA",
    "Delay_96h_ns",
    "IDDQ_delta_24_96",
    "IDDQ_slope_24_96",
    "IDDQ_relative_24_96",
    "IDDQ_delta_0_96",
    "Leakage_delta_24_96",
    "Leakage_slope_24_96",
    "Leakage_relative_24_96",
    "Leakage_delta_0_96",
    "Delay_delta_24_96",
    "Delay_slope_24_96",
    "Delay_relative_24_96",
    "Delay_delta_0_96",
    "Temperature_96h_C",
    "Supply_96h_V",
    "Temperature_delta_24_96",
    "Voltage_delta_24_96"
]

LATENT_SPECIALIST_FEATURES = [
    "IDDQ_0h_uA",
    "Leakage_0h_nA",
    "Delay_0h_ns",
    "IDDQ_24h_uA",
    "Leakage_24h_nA",
    "Delay_24h_ns",
    "IDDQ_96h_uA",
    "Leakage_96h_nA",
    "Delay_96h_ns",
    "Temperature_C",
    "Supply_V",
    "Nominal_V",
    "Temperature_24h_C",
    "Supply_24h_V",
    "Temperature_96h_C",
    "Supply_96h_V",
    "Temperature_delta_24_96",
    "Voltage_delta_24_96",
    "IDDQ_Relative_Drift_24_96",
    "Leakage_Relative_Drift_24_96",
    "Delay_Relative_Drift_24_96"
]

STATION_DISTURBANCE_FEATURES = [
    "IDDQ_0h_uA",
    "Leakage_0h_nA",
    "Delay_0h_ns",
    "IDDQ_24h_uA",
    "Leakage_24h_nA",
    "Delay_24h_ns",
    "IDDQ_delta_0_24",
    "IDDQ_slope_0_24",
    "IDDQ_relative_0_24",
    "Leakage_delta_0_24",
    "Leakage_slope_0_24",
    "Leakage_relative_0_24",
    "Delay_delta_0_24",
    "Delay_slope_0_24",
    "Delay_relative_0_24",
    "Temperature_C",
    "Supply_V",
    "Nominal_V",
    "Temperature_24h_C",
    "Supply_24h_V"
]

FUSION_96H_FEATURES = [
    "Supervised_Score",
    "Component_96h_Score",
    "Late_Drift_Risk"
]

# ---------------------------------------------------------
# REGRESSION MODELS (B-SERIES)
# ---------------------------------------------------------
# Derived from Phase 0B configuration metadata, as artifacts lacked explicit feature_names_in_

B0_FEATURES = [
    "Iddq_uA_0h", "Iddq_uA_24h",
    "Leakage_nA_0h", "Leakage_nA_24h",
    "PropDelay_ns_0h", "PropDelay_ns_24h"
]

B1_FEATURES = [
    "IDDQ_0h_uA", "Leakage_0h_nA", "Delay_0h_ns", 
    "IDDQ_24h_uA", "Leakage_24h_nA", "Delay_24h_ns", 
    "Temperature_C", "Supply_V", "Nominal_V", 
    "Temperature_24h_C", "Supply_24h_V"
]

B2_EARLY_FEATURES = COMPONENT_24H_FEATURES

B2_96H_FEATURES = COMPONENT_96H_FEATURES
