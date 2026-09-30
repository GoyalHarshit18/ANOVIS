import pytest
from app.ml.risk_fusion import determine_decision, compute_a_score, compute_ldi
from app.inference.feature_builder import build_fusion_vector

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models import ScreeningRun, Component, Measurement, Lot, ScreeningResult, AnomalyEvidence, AnomalyOrigins, Prediction, RiskFusionResult
from app.services.risk_fusion_service import run_risk_fusion_for_component
from app.ml.model_registry import registry

def test_1_hard_static_failure(db):
    # Hard static failure -> REJECT wins over everything else.
    res = determine_decision(
        static_result="FAIL",
        a_score=10.0,
        prediction_risk=10.0,
        s_score=10.0,
        uncertainty_risk=10.0,
        test_integrity_flag=False,
        ldi=10.0,
        data_available=True,
        fusion_score=0.1
    )
    assert res["decision"] == "REJECT"
    assert "Hard static failure" in res["explanation"]

def test_2_missing_required_evidence(db):
    # Missing required evidence -> data/model failure path (data_available=False).
    res = determine_decision(
        static_result="PASS",
        a_score=10.0,
        prediction_risk=10.0,
        s_score=10.0,
        uncertainty_risk=10.0,
        test_integrity_flag=False,
        ldi=10.0,
        data_available=False,
        fusion_score=0.1
    )
    assert res["decision"] == "REVIEW_REQUIRED"
    assert "Required data or model artifacts unavailable" in res["explanation"]

def test_3_test_integrity_failure(db):
    # Test integrity failure -> REPEAT_MEASUREMENT.
    res = determine_decision(
        static_result="PASS",
        a_score=10.0,
        prediction_risk=10.0,
        s_score=10.0,
        uncertainty_risk=10.0,
        test_integrity_flag=True,
        ldi=10.0,
        data_available=True,
        fusion_score=0.1
    )
    assert res["decision"] == "REPEAT_MEASUREMENT"
    assert "Test integrity is suspect" in res["explanation"]

def test_4_high_ldi_below_threshold(db):
    # LDI = 69 (below 70 threshold)
    res = determine_decision(
        static_result="PASS",
        a_score=40.0,
        prediction_risk=40.0,
        s_score=40.0,
        uncertainty_risk=40.0,
        test_integrity_flag=False,
        ldi=69.0,
        data_available=True,
        fusion_score=0.1
    )
    assert res["decision"] == "MONITOR"
    
def test_5_ldi_exactly_at_threshold(db):
    # LDI = 70.0 (boundary check, using > 70 in code)
    res = determine_decision(
        static_result="PASS",
        a_score=40.0,
        prediction_risk=40.0,
        s_score=40.0,
        uncertainty_risk=40.0,
        test_integrity_flag=False,
        ldi=70.0,
        data_available=True,
        fusion_score=0.1
    )
    assert res["decision"] == "MONITOR"
    
def test_6_ldi_above_threshold(db):
    # LDI = 71.0 (above 70 threshold)
    res = determine_decision(
        static_result="PASS",
        a_score=40.0,
        prediction_risk=40.0,
        s_score=40.0,
        uncertainty_risk=40.0,
        test_integrity_flag=False,
        ldi=71.0,
        data_available=True,
        fusion_score=0.1
    )
    assert res["decision"] == "REVIEW_REQUIRED"

def test_7_valid_low_risk_complete_evidence(db):
    # Valid low risk
    res = determine_decision(
        static_result="PASS",
        a_score=10.0,
        prediction_risk=10.0,
        s_score=10.0,
        uncertainty_risk=10.0,
        test_integrity_flag=False,
        ldi=10.0,
        data_available=True,
        fusion_score=0.1
    )
    assert res["decision"] == "PASS"

def test_9_fusion_score_does_not_override(db):
    # Fusion score > 0.5 returns REVIEW_REQUIRED, but if static failure is present, REJECT wins.
    res = determine_decision(
        static_result="FAIL",
        a_score=10.0,
        prediction_risk=10.0,
        s_score=10.0,
        uncertainty_risk=10.0,
        test_integrity_flag=False,
        ldi=10.0,
        data_available=True,
        fusion_score=0.9
    )
    assert res["decision"] == "REJECT"

def test_10_missing_values_not_converted_to_0(db):
    # compute_a_score with missing values -> None
    res = compute_a_score(
        pat_result={},
        peer_result={"score": 10.0},
        temporal_result={"score": 10.0},
        if_result={"score": 10.0}
    )
    assert res is None

def test_11_valid_numeric_zero_remains(db):
    # compute_a_score with 0.0 values -> returns float (0.0)
    res = compute_a_score(
        pat_result={"score": 0.0},
        peer_result={"score": 0.0},
        temporal_result={"score": 0.0},
        if_result={"score": 0.0}
    )
    assert res == 0.0

def test_12_phase6b_canonical_vector_unchanged(db):
    vec = build_fusion_vector(0.1, 0.2, 0.3)
    assert len(vec) == 3
    assert vec[0] == 0.1
    assert vec[1] == 0.2
    assert vec[2] == 0.3




def setup_mock_run(db, run_id: str, comp_id: str):
    db.add(ScreeningRun(run_id=run_id, status="MODULE_B_COMPLETED"))
    db.add(Lot(lot_id="LOT_1"))
    db.add(Component(component_id=comp_id, lot_id="LOT_1", station_id="ST_1"))
    
    for chk in [0, 24, 96]:
        db.add(Measurement(
            run_id=run_id, component_id=comp_id, checkpoint_hour=chk,
            iddq_ua=10.0, leakage_na=100.0, prop_delay_ns=3.0, temperature="25.0", voltage="3.3"
        ))
        
    db.add(AnomalyEvidence(
        run_id=run_id, component_id=comp_id, a_score=50.0,
        pat_score=0.1, peer_score=0.1, temporal_score=0.1, isolation_forest_score=0.1
    ))
    db.add(ScreeningResult(
        run_id=run_id, component_id=comp_id, stage="MODULE_A",
        evidence={"prediction_probability": 0.2}
    ))
    
    # Simulate a Hard Failure inside AnomalyOrigins
    db.add(AnomalyOrigins(
        run_id=run_id, component_id=comp_id,
        device_status="FAIL", station_status="NORMAL", lot_status="NORMAL"
    ))
    
    db.add(Prediction(
        run_id=run_id, component_id=comp_id, prediction_stage="B2-96h", available=True,
        predicted_168h={"Iddq_uA_168h": 12.0, "Leakage_nA_168h": 110.0, "PropDelay_ns_168h": 3.1}
    ))
    db.commit()

def test_8_decision_basis_matches_branch(db):
    setup_mock_run(db, "RUN_8", "COMP_8")
    
    run_risk_fusion_for_component("RUN_8", "COMP_8", db)
    db.commit()
    
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_8").first()
    assert rf is not None
    assert rf.final_decision == "REJECT"  # Because we injected FAIL in AnomalyOrigins
    # Decision basis contains current_state, future_state, etc.
    assert "current_state" in rf.decision_basis
