import logging
from typing import Dict, Any, List, Optional
from app.inference.validators import validate_feature_vector
from app.inference.model_contracts import (
    COMPONENT_24H_FEATURES, COMPONENT_96H_FEATURES,
    LATENT_SPECIALIST_FEATURES, STATION_DISTURBANCE_FEATURES, FUSION_96H_FEATURES,
    B0_FEATURES, B1_FEATURES, B2_EARLY_FEATURES, B2_96H_FEATURES
)

logger = logging.getLogger("sih26170.inference.feature_builder")

def safe_float(val: Any) -> float:
    import math
    if val is None:
        return float('nan')
    try:
        f = float(val)
        return f
    except (ValueError, TypeError):
        return float('nan')

def compute_delta(v1: float, v2: float) -> float:
    import math
    if v1 is None or v2 is None or math.isnan(v1) or math.isnan(v2):
        return float('nan')
    return v2 - v1

def compute_slope(v1: float, v2: float, hours: float) -> float:
    if v1 is None or v2 is None or hours is None:
        return float('nan')
    delta = compute_delta(v1, v2)
    import math
    if math.isnan(delta) or hours == 0:
        return float('nan')
    return delta / hours

def compute_relative(v1: float, v2: float) -> float:
    if v1 is None or v2 is None:
        return float('nan')
    delta = compute_delta(v1, v2)
    import math
    if math.isnan(delta) or v1 == 0 or math.isnan(v1):
        return float('nan')
    return delta / v1

def build_component_24h_vector(measurements: Dict[str, Any], legacy_risks: Dict[str, float]) -> Optional[List[float]]:
    """Builds exactly the 24-feature vector for component_24h_classifier.pkl."""
    vector = []
    
    # 0h and 24h raw
    v0_i = safe_float(measurements.get("Iddq_uA_0h"))
    v0_l = safe_float(measurements.get("Leakage_nA_0h"))
    v0_d = safe_float(measurements.get("PropDelay_ns_0h"))
    v24_i = safe_float(measurements.get("Iddq_uA_24h"))
    v24_l = safe_float(measurements.get("Leakage_nA_24h"))
    v24_d = safe_float(measurements.get("PropDelay_ns_24h"))

    vector.extend([v0_i, v0_l, v0_d, v24_i, v24_l, v24_d])

    # Deltas, slopes, relatives
    vector.extend([
        compute_delta(v0_i, v24_i), compute_slope(v0_i, v24_i, 24), compute_relative(v0_i, v24_i),
        compute_delta(v0_l, v24_l), compute_slope(v0_l, v24_l, 24), compute_relative(v0_l, v24_l),
        compute_delta(v0_d, v24_d), compute_slope(v0_d, v24_d, 24), compute_relative(v0_d, v24_d)
    ])

    # Environment
    temp_0 = safe_float(measurements.get("Temperature_0h"))
    if temp_0 is None: temp_0 = safe_float(measurements.get("Temperature_C_0h"))
    sup_0 = safe_float(measurements.get("Voltage_0h"))
    nom_v = 3.3
    temp_24 = safe_float(measurements.get("Temperature_24h"))
    if temp_24 is None: temp_24 = safe_float(measurements.get("Temperature_C_24h"))
    sup_24 = safe_float(measurements.get("Voltage_24h"))

    vector.extend([temp_0, sup_0, nom_v, temp_24, sup_24])

    # Risks
    vector.extend([
        safe_float(legacy_risks.get("PAT_Risk")),
        safe_float(legacy_risks.get("Peer_Risk")),
        safe_float(legacy_risks.get("Temporal_Risk")),
        safe_float(legacy_risks.get("IF_Risk"))
    ])

    if not validate_feature_vector(vector, len(COMPONENT_24H_FEATURES), "component_24h_classifier"):
        return None
    return vector

def build_station_vector(measurements: Dict[str, Any]) -> Optional[List[float]]:
    """Builds the 20-feature vector for station_disturbance_classifier."""
    vector = []
    
    # 0h and 24h raw
    v0_i = safe_float(measurements.get("Iddq_uA_0h"))
    v0_l = safe_float(measurements.get("Leakage_nA_0h"))
    v0_d = safe_float(measurements.get("PropDelay_ns_0h"))
    v24_i = safe_float(measurements.get("Iddq_uA_24h"))
    v24_l = safe_float(measurements.get("Leakage_nA_24h"))
    v24_d = safe_float(measurements.get("PropDelay_ns_24h"))

    vector.extend([v0_i, v0_l, v0_d, v24_i, v24_l, v24_d])

    # Deltas, slopes, relatives
    vector.extend([
        compute_delta(v0_i, v24_i), compute_slope(v0_i, v24_i, 24), compute_relative(v0_i, v24_i),
        compute_delta(v0_l, v24_l), compute_slope(v0_l, v24_l, 24), compute_relative(v0_l, v24_l),
        compute_delta(v0_d, v24_d), compute_slope(v0_d, v24_d, 24), compute_relative(v0_d, v24_d)
    ])

    # Environment
    temp_0 = safe_float(measurements.get("Temperature_0h"))
    if temp_0 is None: temp_0 = safe_float(measurements.get("Temperature_C_0h"))
    sup_0 = safe_float(measurements.get("Voltage_0h"))
    nom_v = 3.3
    temp_24 = safe_float(measurements.get("Temperature_24h"))
    if temp_24 is None: temp_24 = safe_float(measurements.get("Temperature_C_24h"))
    sup_24 = safe_float(measurements.get("Voltage_24h"))

    vector.extend([temp_0, sup_0, nom_v, temp_24, sup_24])

    if not validate_feature_vector(vector, len(STATION_DISTURBANCE_FEATURES), "station_disturbance_classifier"):
        return None
    return vector

def build_b0_vector(measurements: Dict[str, Any]) -> Optional[List[float]]:
    """Builds exactly the 6-feature vector for B0 regression."""
    vector = [
        safe_float(measurements.get("Iddq_uA_0h")),
        safe_float(measurements.get("Iddq_uA_24h")),
        safe_float(measurements.get("Leakage_nA_0h")),
        safe_float(measurements.get("Leakage_nA_24h")),
        safe_float(measurements.get("PropDelay_ns_0h")),
        safe_float(measurements.get("PropDelay_ns_24h")),
    ]
    if not validate_feature_vector(vector, len(B0_FEATURES), "B0"):
        return None
    return vector

def build_b2_early_vector(measurements: Dict[str, Any], legacy_risks: Dict[str, float]) -> Optional[List[float]]:
    """Builds the 24-feature vector for B2-Early."""
    vector = build_component_24h_vector(measurements, legacy_risks)
    if vector and validate_feature_vector(vector, len(B2_EARLY_FEATURES), "B2-Early"):
        return vector
    return None

def build_b1_vector(measurements: Dict[str, Any]) -> Optional[List[float]]:
    """Builds the 11-feature vector for B1."""
    temp_0 = safe_float(measurements.get("Temperature_0h"))
    if temp_0 is None: temp_0 = safe_float(measurements.get("Temperature_C_0h"))
    sup_0 = safe_float(measurements.get("Voltage_0h"))
    nom_v = 3.3
    temp_24 = safe_float(measurements.get("Temperature_24h"))
    if temp_24 is None: temp_24 = safe_float(measurements.get("Temperature_C_24h"))
    sup_24 = safe_float(measurements.get("Voltage_24h"))

    vector = [
        safe_float(measurements.get("Iddq_uA_0h")),
        safe_float(measurements.get("Leakage_nA_0h")),
        safe_float(measurements.get("PropDelay_ns_0h")),
        safe_float(measurements.get("Iddq_uA_24h")),
        safe_float(measurements.get("Leakage_nA_24h")),
        safe_float(measurements.get("PropDelay_ns_24h")),
        temp_0,
        sup_0,
        nom_v,
        temp_24,
        sup_24
    ]
    if not validate_feature_vector(vector, len(B1_FEATURES), "B1"):
        return None
    return vector

def build_b2_96h_vector(measurements: Dict[str, Any], legacy_risks: Dict[str, float]) -> Optional[List[float]]:
    """Builds the 43-feature vector for B2-96h (same as fusion 96h/component 96h)."""
    # Uses COMPONENT_96H_FEATURES
    from app.inference.feature_builder import build_component_24h_vector
    base_24h = build_component_24h_vector(measurements, legacy_risks)
    if not base_24h:
        return None
        
    vector = []
    
    # Raw 0h, 24h, 96h
    v0_i = safe_float(measurements.get("Iddq_uA_0h"))
    v0_l = safe_float(measurements.get("Leakage_nA_0h"))
    v0_d = safe_float(measurements.get("PropDelay_ns_0h"))
    v24_i = safe_float(measurements.get("Iddq_uA_24h"))
    v24_l = safe_float(measurements.get("Leakage_nA_24h"))
    v24_d = safe_float(measurements.get("PropDelay_ns_24h"))
    v96_i = safe_float(measurements.get("Iddq_uA_96h"))
    v96_l = safe_float(measurements.get("Leakage_nA_96h"))
    v96_d = safe_float(measurements.get("PropDelay_ns_96h"))

    vector.extend([v0_i, v0_l, v0_d, v24_i, v24_l, v24_d, v96_i, v96_l, v96_d])

    # Env
    temp_0 = safe_float(measurements.get("Temperature_0h")) or safe_float(measurements.get("Temperature_C_0h"))
    sup_0 = safe_float(measurements.get("Voltage_0h"))
    nom_v = 3.3
    temp_24 = safe_float(measurements.get("Temperature_24h")) or safe_float(measurements.get("Temperature_C_24h"))
    sup_24 = safe_float(measurements.get("Voltage_24h"))
    temp_96 = safe_float(measurements.get("Temperature_96h")) or safe_float(measurements.get("Temperature_C_96h"))
    sup_96 = safe_float(measurements.get("Voltage_96h"))

    vector.extend([temp_0, sup_0, nom_v, temp_24, sup_24, temp_96, sup_96])

    # Env deltas
    vector.extend([
        compute_delta(temp_24, temp_96),
        compute_delta(sup_24, sup_96)
    ])

    # 0-24 deltas
    vector.extend([
        compute_delta(v0_i, v24_i), compute_slope(v0_i, v24_i, 24), compute_relative(v0_i, v24_i),
        compute_delta(v0_l, v24_l), compute_slope(v0_l, v24_l, 24), compute_relative(v0_l, v24_l),
        compute_delta(v0_d, v24_d), compute_slope(v0_d, v24_d, 24), compute_relative(v0_d, v24_d)
    ])

    # 24-96 deltas
    vector.extend([
        compute_delta(v24_i, v96_i), compute_slope(v24_i, v96_i, 72), compute_relative(v24_i, v96_i),
        compute_delta(v0_i, v96_i),
        compute_delta(v24_l, v96_l), compute_slope(v24_l, v96_l, 72), compute_relative(v24_l, v96_l),
        compute_delta(v0_l, v96_l),
        compute_delta(v24_d, v96_d), compute_slope(v24_d, v96_d, 72), compute_relative(v24_d, v96_d),
        compute_delta(v0_d, v96_d)
    ])

    # Risks
    vector.extend([
        safe_float(legacy_risks.get("PAT_Risk")),
        safe_float(legacy_risks.get("Peer_Risk")),
        safe_float(legacy_risks.get("Temporal_Risk")),
        safe_float(legacy_risks.get("IF_Risk"))
    ])

    if not validate_feature_vector(vector, len(B2_96H_FEATURES), "B2-96h"):
        return None
    return vector


def build_latent_specialist_vector(measurements: Dict[str, Any]) -> Optional[List[float]]:
    """Builds the 21-feature vector for latent_specialist."""
    # Raw 0h, 24h, 96h
    v0_i = safe_float(measurements.get("Iddq_uA_0h"))
    v0_l = safe_float(measurements.get("Leakage_nA_0h"))
    v0_d = safe_float(measurements.get("PropDelay_ns_0h"))
    v24_i = safe_float(measurements.get("Iddq_uA_24h"))
    v24_l = safe_float(measurements.get("Leakage_nA_24h"))
    v24_d = safe_float(measurements.get("PropDelay_ns_24h"))
    v96_i = safe_float(measurements.get("Iddq_uA_96h"))
    v96_l = safe_float(measurements.get("Leakage_nA_96h"))
    v96_d = safe_float(measurements.get("PropDelay_ns_96h"))

    temp_0 = safe_float(measurements.get("Temperature_0h")) or safe_float(measurements.get("Temperature_C_0h"))
    sup_0 = safe_float(measurements.get("Voltage_0h"))
    nom_v = 3.3
    temp_24 = safe_float(measurements.get("Temperature_24h")) or safe_float(measurements.get("Temperature_C_24h"))
    sup_24 = safe_float(measurements.get("Voltage_24h"))
    temp_96 = safe_float(measurements.get("Temperature_96h")) or safe_float(measurements.get("Temperature_C_96h"))
    sup_96 = safe_float(measurements.get("Voltage_96h"))

    vector = [
        v0_i, v0_l, v0_d,
        v24_i, v24_l, v24_d,
        v96_i, v96_l, v96_d,
        temp_0, sup_0, nom_v,
        temp_24, sup_24,
        temp_96, sup_96,
        compute_delta(temp_24, temp_96),
        compute_delta(sup_24, sup_96),
        compute_relative(v24_i, v96_i),
        compute_relative(v24_l, v96_l),
        compute_relative(v24_d, v96_d)
    ]
    
    if not validate_feature_vector(vector, len(LATENT_SPECIALIST_FEATURES), "latent_specialist"):
        return None
    return vector

def build_fusion_vector(supervised_score: Any, component_96h_score: Any, late_drift_risk: Any) -> Optional[List[float]]:
    """Builds exactly the 3-feature vector for fusion_96h_classifier."""
    import math
    
    vector = [
        safe_float(supervised_score),
        safe_float(component_96h_score),
        safe_float(late_drift_risk)
    ]
    
    if not validate_feature_vector(vector, 3, "fusion_96h_classifier"):
        return None
        
    # The fusion model (LogisticRegression + StandardScaler) does not support NaN
    if any(math.isnan(v) for v in vector):
        logger.error("Validation failed for fusion_96h_classifier: Vector contains NaN values")
        return None
        
    return vector
