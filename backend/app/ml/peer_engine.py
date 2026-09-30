"""
Peer Analysis Engine — uses peer_scaler, peer_knn, peer_reference_targets, peer_scales.

1. Prepare 0h feature vector [Iddq_uA_0h, Leakage_nA_0h, PropDelay_ns_0h]
2. Scale with peer_scaler (StandardScaler)
3. Query peer_knn for k nearest neighbors
4. Retrieve peer reference targets (24h values of neighbors)
5. Calculate residuals: measured_24h - mean(peer_24h)
6. Normalize residuals by peer_scales
"""
import logging
from typing import Any, Dict

import numpy as np

from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.peer_engine")

PEER_INPUT_FEATURES = ["Iddq_uA_0h", "Leakage_nA_0h", "PropDelay_ns_0h"]
PEER_TARGET_PARAMS = ["Iddq_uA_24h", "Leakage_nA_24h", "PropDelay_ns_24h"]


def compute_peer_analysis(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """Compute peer analysis evidence."""
    scaler = registry.get("peer_scaler")
    knn = registry.get("peer_knn")
    ref_targets = registry.get("peer_reference_targets")
    scales = registry.get("peer_scales")

    if any(x is None for x in [scaler, knn, ref_targets, scales]):
        missing = []
        if scaler is None: missing.append("peer_scaler")
        if knn is None: missing.append("peer_knn")
        if ref_targets is None: missing.append("peer_reference_targets")
        if scales is None: missing.append("peer_scales")
        return {
            "score": None,
            "status": "DATA_UNAVAILABLE",
            "details": {"reason": f"Missing: {', '.join(missing)}"},
        }

    # Check required 0h features
    input_values = []
    for feat in PEER_INPUT_FEATURES:
        v = measurements.get(feat)
        if v is None:
            return {
                "score": None,
                "status": "DATA_UNAVAILABLE",
                "details": {"reason": f"Missing 0h measurement: {feat}"},
            }
        input_values.append(v)

    try:
        # Step 1: Scale input
        X = np.array(input_values).reshape(1, -1)
        X_scaled = scaler.transform(X)

        # Step 2: Find nearest neighbors
        distances, indices = knn.kneighbors(X_scaled)

        # Step 3: Get peer reference values
        peer_results = {}
        max_norm_residual = 0.0

        for param in PEER_TARGET_PARAMS:
            measured = measurements.get(param)
            if measured is None:
                peer_results[param] = {
                    "measured": None,
                    "expected": None,
                    "residual": None,
                    "normalized_residual": None,
                    "status": "DATA_UNAVAILABLE",
                }
                continue

            # Mean of neighbor targets
            peer_values = ref_targets.iloc[indices[0]][param].values
            expected = float(np.mean(peer_values))
            residual = float(measured - expected)

            # Normalize by scale
            scale_key = f"PeerResidual_{param}"
            scale_val = scales.get(scale_key, 1.0)
            if scale_val == 0 or scale_val < 1e-15:
                norm_residual = 0.0
            else:
                norm_residual = abs(residual) / float(scale_val)

            max_norm_residual = max(max_norm_residual, norm_residual)

            if norm_residual > 3.0:
                status = "HIGH"
            elif norm_residual > 2.0:
                status = "ELEVATED"
            else:
                status = "NORMAL"

            peer_results[param] = {
                "measured": float(measured),
                "expected": expected,
                "residual": residual,
                "normalized_residual": round(norm_residual, 4),
                "status": status,
            }

        # Aggregate peer score: scale to 0-100
        peer_score = min(100.0, max_norm_residual * 25.0)

        if peer_score > 70:
            overall_status = "HIGH"
        elif peer_score > 40:
            overall_status = "ELEVATED"
        else:
            overall_status = "NORMAL"

        return {
            "score": round(peer_score, 1),
            "status": overall_status,
            "details": peer_results,
            "n_neighbors": int(distances.shape[1]),
            "mean_distance": float(np.mean(distances)),
        }

    except Exception as e:
        logger.error("Peer analysis failed: %s", e)
        return {
            "score": None,
            "status": "ERROR",
            "details": {"reason": str(e)},
        }
