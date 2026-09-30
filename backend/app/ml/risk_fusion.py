"""
Risk Fusion — combines Module A (A_SCORE) and Module B (safety) into final decision.

Uses inference_config.pkl for:
- ldi_weights: [0.35, 0.25, 0.25, 0.15] → [PAT, Peer, Temporal, IF]
- a_score_threshold
- if_threshold

Decision precedence:
1. HARD STATIC FAILURE → REJECT
2. DATA/MODEL FAILURE → REVIEW_REQUIRED / DATA_UNAVAILABLE
3. HIGH TEST-INTEGRITY RISK → REPEAT_MEASUREMENT
4. HIGH DEVICE OR FUTURE RISK → REVIEW / REJECT
5. OTHERWISE → PASS / MONITOR
"""
import logging
from typing import Any, Dict, List, Optional

from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.risk_fusion")


def compute_a_score(
    pat_result: Dict[str, Any],
    peer_result: Dict[str, Any],
    temporal_result: Dict[str, Any],
    if_result: Dict[str, Any],
) -> float:
    """
    Compute A_SCORE as weighted combination of sub-signal scores.
    Uses ldi_weights from inference_config: [PAT, Peer, Temporal, IF]
    """
    config = registry.get("inference_config")
    if config:
        weights = config.get("ldi_weights", [0.35, 0.25, 0.25, 0.15])
    else:
        weights = [0.35, 0.25, 0.25, 0.15]

    scores = []
    for res in [pat_result, peer_result, temporal_result, if_result]:
        if not res or "score" not in res or res["score"] is None:
            return None
        scores.append(res["score"])

    a_score = sum(w * s for w, s in zip(weights, scores))
    return round(min(100.0, max(0.0, a_score)), 1)


def compute_ldi(
    a_score: Optional[float],
    prediction_risk: Optional[float],
    s_score: Optional[float],
    uncertainty_risk: Optional[float],
) -> Optional[float]:
    """
    Compute LDI (Latent Defect Index) — fused risk score.
    Weighted combination of module A and module B evidence.
    Returns None if any required component is missing (Phase 6 requirement).
    """
    if a_score is None or prediction_risk is None or s_score is None or uncertainty_risk is None:
        return None

    ldi = 0.4 * a_score + 0.3 * prediction_risk + 0.2 * s_score + 0.1 * uncertainty_risk
    return round(min(100.0, max(0.0, ldi)), 1)


def determine_decision(
    static_result: str,
    a_score: Optional[float],
    prediction_risk: Optional[float],
    s_score: Optional[float],
    uncertainty_risk: Optional[float],
    test_integrity_flag: bool,
    ldi: Optional[float],
    data_available: bool = True,
    fusion_score: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Apply decision precedence logic.
    Returns decision string, explanation, and evidence flags.
    """
    config = registry.get("inference_config")
    a_threshold = config.get("a_score_threshold", 50.0) if config else 50.0

    warnings: List[str] = []
    first_detection_stage = "N/A"

    # Precedence 1: Hard static failure
    if static_result == "FAIL":
        return {
            "decision": "REJECT",
            "explanation": "Hard static failure. Measurement exceeds engineering limits.",
            "first_detection_stage": "0h",
            "warnings": warnings,
        }

    # Precedence 2: Data/model failure
    if not data_available:
        return {
            "decision": "REVIEW_REQUIRED",
            "explanation": "Required data or model artifacts unavailable for trustworthy screening.",
            "first_detection_stage": "N/A",
            "warnings": ["Insufficient data for complete screening"],
        }

    # Precedence 3: Test integrity
    if test_integrity_flag:
        return {
            "decision": "REPEAT_MEASUREMENT",
            "explanation": "Test integrity is suspect. Repeat measurement recommended.",
            "first_detection_stage": "24h",
            "warnings": ["Test integrity flag raised"],
        }

    # Precedence 4: High device or future risk
    # Only evaluate if we have the necessary data
    if a_score is not None and prediction_risk is not None and ldi is not None:
        if ldi > 90 or (a_score > 90 and prediction_risk > 90):
            return {
                "decision": "REJECT",
                "explanation": "Extremely high device and future risk evidence warrants rejection.",
                "first_detection_stage": "24h",
                "warnings": warnings,
            }

        # REVIEW threshold
        if a_score > a_threshold or prediction_risk > 70 or ldi > 70:
            return {
                "decision": "REVIEW_REQUIRED",
                "explanation": "Static screening passes, but dynamic and future-risk evidence warrants QA review.",
                "first_detection_stage": "24h",
                "warnings": warnings,
            }

        # MONITOR threshold
        if a_score > a_threshold * 0.6 or prediction_risk > 40 or ldi > 40:
            return {
                "decision": "MONITOR",
                "explanation": "Elevated evidence that does not meet stronger action threshold.",
                "first_detection_stage": "24h",
                "warnings": warnings,
            }
            
    if fusion_score is not None and fusion_score > 0.5:
        return {
            "decision": "REVIEW_REQUIRED",
            "explanation": "Fusion classifier flagged risk.",
            "first_detection_stage": "96h",
            "warnings": warnings,
        }

    # PASS
    return {
        "decision": "PASS",
        "explanation": "No current evidence requiring intervention under configured decision rules.",
        "first_detection_stage": "N/A",
        "warnings": warnings,
    }
