"""Output schemas for the SIH26170 screening API."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EvidenceDetail(BaseModel):
    score: Optional[float] = None
    status: str = "N/A"
    details: Optional[Dict[str, Any]] = None


class TestIntegrityResult(BaseModel):
    quality: str = "NORMAL"
    within_station: str = "NORMAL"
    cross_station: str = "NORMAL"
    glitch: str = "NOT DETECTED"


class BasisInfo(BaseModel):
    mode: str = "Mode A"
    b_model: str = "B0"
    safety_score_calibrated: bool = False


class BModelResult(BaseModel):
    prediction: Optional[float] = None
    stage: str = "24h"
    available: bool = False
    reason: Optional[str] = None


class Predicted168h(BaseModel):
    Iddq_uA: Optional[float] = None
    Leakage_nA: Optional[float] = None
    PropDelay_ns: Optional[float] = None


class EvidenceBreakdown(BaseModel):
    static_result: str = "N/A"
    pat: Optional[EvidenceDetail] = None
    peer_residual: Optional[EvidenceDetail] = None
    early_temporal: Optional[EvidenceDetail] = None
    isolation_forest: Optional[EvidenceDetail] = None


class HistoryPoint(BaseModel):
    stage: str
    value: Optional[float] = None
    parameter: str = "Leakage_nA"


class ShapFeature(BaseModel):
    feature: str
    value: float


class ComponentScreeningResult(BaseModel):
    component_id: str
    lot: str = "LOT-2026-091"
    device_type: str = "XYZ-IC"
    station: str = "ST-01"
    temperature: str = "125°C"
    voltage: str = "3.3V"

    decision: str = "REVIEW_REQUIRED"
    ldi: Optional[float] = None
    a_score: Optional[float] = None
    s_score: Optional[float] = None
    prediction_risk: Optional[float] = None
    uncertainty_risk: Optional[float] = None

    predicted_168h: Optional[Dict[str, Any]] = None
    test_integrity_flag: bool = False

    screening_stage: str = "24h"
    first_detection_stage: str = "N/A"
    latest_evidence_stage: str = "24h"

    basis: Optional[BasisInfo] = None
    evidence: Optional[EvidenceBreakdown] = None
    test_integrity: Optional[TestIntegrityResult] = None

    history: List[HistoryPoint] = []
    b_models: Optional[Dict[str, BModelResult]] = None
    shap: Optional[List[ShapFeature]] = None

    model_version: str = "risk-fusion-v1.0.0"
    warnings: List[str] = []
    explanation: str = ""


class BatchScreeningSummary(BaseModel):
    total: int = 0
    pass_count: int = 0
    monitor: int = 0
    review: int = 0
    reject: int = 0
    repeat_measurement: int = 0
    data_unavailable: int = 0


class BatchScreeningResponse(BaseModel):
    summary: BatchScreeningSummary
    results: List[ComponentScreeningResult]


class PredictionResponse(BaseModel):
    component_id: str
    predicted_168h: Predicted168h
    envelope: Optional[Dict[str, Any]] = None
    model_used: str = "B0"
    model_version: str = "b0-baseline-v1.0"
    stage: str = "24h"
    warnings: List[str] = []
    available: bool = True


class HealthResponse(BaseModel):
    api: str = "operational"
    database: str = "connected"
    feature_engine: str = "v1.0"
    module_a: str = "loaded"
    module_b: str = "loaded"
    risk_fusion: str = "loaded"
    models: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    component_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class UnifiedPredictionResponse(BaseModel):
    component_id: str
    lot_id: str = "LOT-UNKNOWN"
    anomaly_probability_96h: float
    anomaly_status_96h: str
    predicted_iddq_168h: Optional[float] = None
    predicted_leakage_168h: Optional[float] = None
    predicted_delay_168h: Optional[float] = None
    threshold: float = 0.50
    model_version: str = "catboost-96h-v1.0"

