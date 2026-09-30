-- =============================================================================
-- ANOVIS / BURNSIGHT-AI: PRODUCTION SUPABASE POSTGRESQL SCHEMA
-- =============================================================================
-- Project: Anovis AI-Driven Semiconductor Burn-In Screening
-- Target Database: Supabase PostgreSQL (Postgres 15+)
-- Description: Core tables, relational constraints, JSON evidence schemas, and indexes.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. LOTS TABLE
CREATE TABLE IF NOT EXISTS lots (
    id SERIAL PRIMARY KEY,
    lot_id VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_lots_lot_id ON lots(lot_id);
CREATE INDEX IF NOT EXISTS idx_lots_created_at ON lots(created_at);

-- 2. COMPONENTS TABLE
CREATE TABLE IF NOT EXISTS components (
    id SERIAL PRIMARY KEY,
    component_id VARCHAR(100) UNIQUE NOT NULL,
    lot_id VARCHAR(100) REFERENCES lots(lot_id) ON DELETE CASCADE,
    device_type VARCHAR(100),
    station_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_components_comp_id ON components(component_id);
CREATE INDEX IF NOT EXISTS idx_components_lot_id ON components(lot_id);
CREATE INDEX IF NOT EXISTS idx_components_station ON components(station_id);
CREATE INDEX IF NOT EXISTS idx_components_created_at ON components(created_at);

-- 3. SCREENING RUNS TABLE
CREATE TABLE IF NOT EXISTS screening_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) UNIQUE NOT NULL,
    lot_id VARCHAR(100) REFERENCES lots(lot_id) ON DELETE SET NULL,
    source_filename VARCHAR(255),
    source_file_hash VARCHAR(100),
    status VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_rows INT,
    valid_rows INT,
    invalid_rows INT,
    component_count INT,
    warning_count INT,
    error_count INT,
    model_version VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_runs_run_id ON screening_runs(run_id);
CREATE INDEX IF NOT EXISTS idx_runs_lot_id ON screening_runs(lot_id);

-- 4. MEASUREMENTS TABLE
CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    component_id VARCHAR(100) NOT NULL REFERENCES components(component_id) ON DELETE CASCADE,
    checkpoint_hour INT NOT NULL CHECK (checkpoint_hour IN (0, 24, 96, 168)),
    timestamp TIMESTAMP WITH TIME ZONE,
    temperature VARCHAR(50),
    voltage VARCHAR(50),
    iddq_ua DOUBLE PRECISION,
    leakage_na DOUBLE PRECISION,
    prop_delay_ns DOUBLE PRECISION,
    source_row_number INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_run_comp_chkpt UNIQUE(run_id, component_id, checkpoint_hour)
);
CREATE INDEX IF NOT EXISTS idx_meas_comp_id ON measurements(component_id);
CREATE INDEX IF NOT EXISTS idx_meas_run_id ON measurements(run_id);
CREATE INDEX IF NOT EXISTS idx_meas_checkpoint ON measurements(checkpoint_hour);

-- 5. SCREENING RESULTS TABLE
CREATE TABLE IF NOT EXISTS screening_results (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    component_id VARCHAR(100) NOT NULL REFERENCES components(component_id) ON DELETE CASCADE,
    decision VARCHAR(50),
    ldi DOUBLE PRECISION,
    a_score DOUBLE PRECISION,
    s_score DOUBLE PRECISION,
    prediction_risk DOUBLE PRECISION,
    uncertainty_risk DOUBLE PRECISION,
    integrity_status VARCHAR(50),
    stage VARCHAR(50),
    evidence JSONB,
    warnings JSONB,
    model_version VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_run_comp_result UNIQUE(run_id, component_id)
);
CREATE INDEX IF NOT EXISTS idx_screen_comp_id ON screening_results(component_id);
CREATE INDEX IF NOT EXISTS idx_screen_decision ON screening_results(decision);
CREATE INDEX IF NOT EXISTS idx_screen_created_at ON screening_results(created_at);

-- 6. ANOMALY EVIDENCE TABLE
CREATE TABLE IF NOT EXISTS anomaly_evidence (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    component_id VARCHAR(100) NOT NULL REFERENCES components(component_id) ON DELETE CASCADE,
    pat_score DOUBLE PRECISION,
    pat_evidence JSONB,
    peer_score DOUBLE PRECISION,
    peer_evidence JSONB,
    temporal_score DOUBLE PRECISION,
    temporal_evidence JSONB,
    isolation_forest_score DOUBLE PRECISION,
    isolation_forest_evidence JSONB,
    a_score DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_anom_evidence_comp ON anomaly_evidence(component_id);

-- 7. ANOMALY ORIGINS TABLE
CREATE TABLE IF NOT EXISTS anomaly_origins (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    component_id VARCHAR(100) REFERENCES components(component_id) ON DELETE CASCADE,
    lot_id VARCHAR(100) REFERENCES lots(lot_id) ON DELETE SET NULL,
    station_id VARCHAR(100),
    device_status VARCHAR(50),
    lot_status VARCHAR(50),
    station_status VARCHAR(50),
    device_score DOUBLE PRECISION,
    lot_score DOUBLE PRECISION,
    station_score DOUBLE PRECISION,
    evidence JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. LOT & STATION ANALYSIS TABLES
CREATE TABLE IF NOT EXISTS lot_analysis (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    lot_id VARCHAR(100) NOT NULL REFERENCES lots(lot_id) ON DELETE CASCADE,
    lot_shift_score DOUBLE PRECISION,
    status VARCHAR(50),
    affected_component_count INT,
    total_component_count INT,
    parameter_evidence JSONB,
    distribution_evidence JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS station_analysis (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    lot_id VARCHAR(100) REFERENCES lots(lot_id) ON DELETE SET NULL,
    station_id VARCHAR(100) NOT NULL,
    station_shift_score DOUBLE PRECISION,
    integrity_status VARCHAR(50),
    within_station_evidence JSONB,
    cross_station_evidence JSONB,
    parameter_evidence JSONB,
    affected_component_count INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. PREDICTIONS (168H) TABLE
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    component_id VARCHAR(100) NOT NULL REFERENCES components(component_id) ON DELETE CASCADE,
    model_name VARCHAR(100),
    model_version VARCHAR(100),
    prediction_stage VARCHAR(50),
    available BOOLEAN,
    status VARCHAR(50),
    predicted_168h JSONB,
    input_checkpoint JSONB,
    evidence JSONB,
    warnings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_predictions_comp_id ON predictions(component_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);

-- 10. RISK FUSION RESULTS TABLE
CREATE TABLE IF NOT EXISTS risk_fusion_results (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    component_id VARCHAR(100) NOT NULL REFERENCES components(component_id) ON DELETE CASCADE,
    a_score DOUBLE PRECISION,
    s_score DOUBLE PRECISION,
    prediction_risk DOUBLE PRECISION,
    uncertainty_risk DOUBLE PRECISION,
    ldi DOUBLE PRECISION,
    fusion_score DOUBLE PRECISION,
    final_decision VARCHAR(50),
    decision_basis JSONB,
    model_version VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_fusion_comp_id ON risk_fusion_results(component_id);

-- 11. EXPLANATIONS (SHAP) TABLE
CREATE TABLE IF NOT EXISTS explanations (
    id SERIAL PRIMARY KEY,
    prediction_id INT REFERENCES predictions(id) ON DELETE SET NULL,
    component_id VARCHAR(100) NOT NULL REFERENCES components(component_id) ON DELETE CASCADE,
    shap_data JSONB,
    top_features JSONB,
    model_version VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_explanations_comp ON explanations(component_id);
CREATE INDEX IF NOT EXISTS idx_explanations_created_at ON explanations(created_at);

-- 12. QA REPORTS (GEMINI + PDF) TABLE
CREATE TABLE IF NOT EXISTS qa_reports (
    id SERIAL PRIMARY KEY,
    component_id VARCHAR(100) NOT NULL REFERENCES components(component_id) ON DELETE CASCADE,
    lot_id VARCHAR(100) REFERENCES lots(lot_id) ON DELETE SET NULL,
    report_data JSONB,
    pdf_path VARCHAR(500),
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_qa_reports_comp ON qa_reports(component_id);
CREATE INDEX IF NOT EXISTS idx_qa_reports_lot ON qa_reports(lot_id);
CREATE INDEX IF NOT EXISTS idx_qa_reports_created_at ON qa_reports(created_at);

-- 13. AUDIT EVENTS TABLE
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES screening_runs(run_id) ON DELETE SET NULL,
    component_id VARCHAR(100) REFERENCES components(component_id) ON DELETE SET NULL,
    event_type VARCHAR(100),
    message TEXT,
    severity VARCHAR(50),
    metadata_ JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
