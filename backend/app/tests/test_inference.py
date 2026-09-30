import pytest
from app.inference.feature_builder import build_b0_vector, build_b2_early_vector, build_component_24h_vector
from app.inference.model_contracts import B0_FEATURES, B2_EARLY_FEATURES, COMPONENT_24H_FEATURES

def test_b0_feature_construction():
    measurements = {
        "Iddq_uA_0h": 1.0, "Iddq_uA_24h": 1.2,
        "Leakage_nA_0h": 10.0, "Leakage_nA_24h": 12.0,
        "PropDelay_ns_0h": 3.0, "PropDelay_ns_24h": 3.1
    }
    vec = build_b0_vector(measurements)
    assert vec is not None
    assert len(vec) == len(B0_FEATURES)
    assert vec == [1.0, 1.2, 10.0, 12.0, 3.0, 3.1]

def test_b0_missing_feature():
    measurements = {
        "Iddq_uA_0h": 1.0, "Iddq_uA_24h": 1.2,
        "Leakage_nA_0h": 10.0, "Leakage_nA_24h": 12.0,
        "PropDelay_ns_0h": 3.0
        # PropDelay_ns_24h missing
    }
    vec = build_b0_vector(measurements)
    import math
    assert vec is not None
    assert math.isnan(vec[5])

def test_component_24h_feature_construction():
    measurements = {
        "Iddq_uA_0h": 1.0, "Iddq_uA_24h": 1.2,
        "Leakage_nA_0h": 10.0, "Leakage_nA_24h": 12.0,
        "PropDelay_ns_0h": 3.0, "PropDelay_ns_24h": 3.1,
        "Temperature_0h": 25.0, "Voltage_0h": 3.3,
        "Temperature_24h": 25.0, "Voltage_24h": 3.3
    }
    risks = {
        "PAT_Risk": 0.5, "Peer_Risk": 0.6,
        "Temporal_Risk": 0.7, "IF_Risk": 0.8
    }
    vec = build_component_24h_vector(measurements, risks)
    assert vec is not None
    assert len(vec) == len(COMPONENT_24H_FEATURES)

def test_component_24h_missing_risk():
    measurements = {
        "Iddq_uA_0h": 1.0, "Iddq_uA_24h": 1.2,
        "Leakage_nA_0h": 10.0, "Leakage_nA_24h": 12.0,
        "PropDelay_ns_0h": 3.0, "PropDelay_ns_24h": 3.1,
        "Temperature_0h": 25.0, "Voltage_0h": 3.3,
        "Temperature_24h": 25.0, "Voltage_24h": 3.3
    }
    risks = {
        "PAT_Risk": 0.5, "Peer_Risk": 0.6,
        "Temporal_Risk": 0.7
        # IF_Risk missing
    }
    vec = build_component_24h_vector(measurements, risks)
    import math
    assert vec is not None
    assert math.isnan(vec[23])
