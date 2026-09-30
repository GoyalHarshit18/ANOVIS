import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from .database import Base

class Lot(Base):
    __tablename__ = "lots"
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    components = relationship("Component", back_populates="lot")

class Component(Base):
    __tablename__ = "components"
    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(String, unique=True, index=True, nullable=False)
    lot_id = Column(String, ForeignKey("lots.lot_id"), index=True, nullable=False)
    device_type = Column(String, nullable=True)
    station_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    lot = relationship("Lot", back_populates="components")
    measurements = relationship("Measurement", back_populates="component")
    screening_results = relationship("ScreeningResult", back_populates="component")

class ScreeningRun(Base):
    __tablename__ = "screening_runs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True, nullable=False)
    lot_id = Column(String, ForeignKey("lots.lot_id"), index=True, nullable=True)
    source_filename = Column(String, nullable=True)
    source_file_hash = Column(String, nullable=True)
    status = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_rows = Column(Integer, nullable=True)
    valid_rows = Column(Integer, nullable=True)
    invalid_rows = Column(Integer, nullable=True)
    component_count = Column(Integer, nullable=True)
    warning_count = Column(Integer, nullable=True)
    error_count = Column(Integer, nullable=True)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=False)
    checkpoint_hour = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    temperature = Column(String, nullable=True)
    voltage = Column(String, nullable=True)
    iddq_ua = Column(Float, nullable=True)
    leakage_na = Column(Float, nullable=True)
    prop_delay_ns = Column(Float, nullable=True)
    source_row_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    component = relationship("Component", back_populates="measurements")
    __table_args__ = (
        UniqueConstraint('run_id', 'component_id', 'checkpoint_hour', name='uq_run_comp_chkpt'),
        CheckConstraint('checkpoint_hour IN (0, 24, 96, 168)', name='chk_valid_checkpoints'),
    )

class ScreeningResult(Base):
    __tablename__ = "screening_results"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=False)
    decision = Column(String, index=True, nullable=True)
    ldi = Column(Float, nullable=True)
    a_score = Column(Float, nullable=True)
    s_score = Column(Float, nullable=True)
    prediction_risk = Column(Float, nullable=True)
    uncertainty_risk = Column(Float, nullable=True)
    integrity_status = Column(String, nullable=True)
    stage = Column(String, nullable=True)
    evidence = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    component = relationship("Component", back_populates="screening_results")
    __table_args__ = (
        UniqueConstraint('run_id', 'component_id', name='uq_run_comp_result'),
    )

class AnomalyEvidence(Base):
    __tablename__ = "anomaly_evidence"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=False)
    pat_score = Column(Float, nullable=True)
    pat_evidence = Column(JSON, nullable=True)
    peer_score = Column(Float, nullable=True)
    peer_evidence = Column(JSON, nullable=True)
    temporal_score = Column(Float, nullable=True)
    temporal_evidence = Column(JSON, nullable=True)
    isolation_forest_score = Column(Float, nullable=True)
    isolation_forest_evidence = Column(JSON, nullable=True)
    a_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AnomalyOrigins(Base):
    __tablename__ = "anomaly_origins"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=True)
    lot_id = Column(String, ForeignKey("lots.lot_id"), index=True, nullable=True)
    station_id = Column(String, index=True, nullable=True)
    device_status = Column(String, nullable=True)
    lot_status = Column(String, nullable=True)
    station_status = Column(String, nullable=True)
    device_score = Column(Float, nullable=True)
    lot_score = Column(Float, nullable=True)
    station_score = Column(Float, nullable=True)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LotAnalysis(Base):
    __tablename__ = "lot_analysis"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    lot_id = Column(String, ForeignKey("lots.lot_id"), index=True, nullable=False)
    lot_shift_score = Column(Float, nullable=True)
    status = Column(String, nullable=True)
    affected_component_count = Column(Integer, nullable=True)
    total_component_count = Column(Integer, nullable=True)
    parameter_evidence = Column(JSON, nullable=True)
    distribution_evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class StationAnalysis(Base):
    __tablename__ = "station_analysis"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    lot_id = Column(String, ForeignKey("lots.lot_id"), index=True, nullable=True)
    station_id = Column(String, index=True, nullable=False)
    station_shift_score = Column(Float, nullable=True)
    integrity_status = Column(String, nullable=True)
    within_station_evidence = Column(JSON, nullable=True)
    cross_station_evidence = Column(JSON, nullable=True)
    parameter_evidence = Column(JSON, nullable=True)
    affected_component_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=False)
    model_name = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    prediction_stage = Column(String, nullable=True)
    available = Column(Boolean, nullable=True)
    status = Column(String, nullable=True)
    predicted_168h = Column(JSON, nullable=True)
    input_checkpoint = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PredictionInterval(Base):
    __tablename__ = "prediction_intervals"
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), index=True, nullable=False)
    parameter = Column(String, nullable=True)
    lower = Column(Float, nullable=True)
    upper = Column(Float, nullable=True)
    method = Column(String, nullable=True)
    calibrated = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SafetyEnvelope(Base):
    __tablename__ = "safety_envelopes"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=False)
    parameter = Column(String, nullable=True)
    lower = Column(Float, nullable=True)
    upper = Column(Float, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RiskFusionResult(Base):
    __tablename__ = "risk_fusion_results"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=False)
    a_score = Column(Float, nullable=True)
    s_score = Column(Float, nullable=True)
    prediction_risk = Column(Float, nullable=True)
    uncertainty_risk = Column(Float, nullable=True)
    ldi = Column(Float, nullable=True)
    fusion_score = Column(Float, nullable=True)
    final_decision = Column(String, nullable=True)
    decision_basis = Column(JSON, nullable=True)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    artifact_name = Column(String, nullable=True)
    artifact_path = Column(String, nullable=True)
    checksum = Column(String, nullable=True)
    sklearn_version = Column(String, nullable=True)
    numpy_version = Column(String, nullable=True)
    loaded_status = Column(String, nullable=True)
    metadata_ = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("screening_runs.run_id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=True)
    event_type = Column(String, nullable=True)
    message = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    metadata_ = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Explanation(Base):
    __tablename__ = "explanations"
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), index=True, nullable=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=False)
    shap_data = Column(JSON, nullable=True)
    top_features = Column(JSON, nullable=True)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class QAReport(Base):
    __tablename__ = "qa_reports"
    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(String, ForeignKey("components.component_id"), index=True, nullable=False)
    lot_id = Column(String, ForeignKey("lots.lot_id"), index=True, nullable=True)
    report_data = Column(JSON, nullable=True)
    pdf_path = Column(String, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

