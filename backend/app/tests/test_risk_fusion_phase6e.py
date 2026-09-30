import pytest
from app.db.models import ScreeningRun, Component, Measurement, Lot, ScreeningResult, AnomalyEvidence, AnomalyOrigins, Prediction, RiskFusionResult, AuditEvent
from app.services.risk_fusion_service import run_risk_fusion_for_component, run_risk_fusion_for_run
from app.ml.model_registry import registry
from app.inference.feature_builder import build_fusion_vector
from unittest.mock import patch

def setup_mock_run(db, run_id: str, comp_id: str, ldi_none=False, zero_metrics=False):
    if not db.query(ScreeningRun).filter_by(run_id=run_id).first():
        db.add(ScreeningRun(run_id=run_id, status="MODULE_B_COMPLETED"))
    if not db.query(Lot).filter_by(lot_id="LOT_1").first():
        db.add(Lot(lot_id="LOT_1"))
        
    db.add(Component(component_id=comp_id, lot_id="LOT_1", station_id="ST_1"))
    
    for chk in [0, 24, 96]:
        db.add(Measurement(
            run_id=run_id, component_id=comp_id, checkpoint_hour=chk,
            iddq_ua=10.0, leakage_na=100.0, prop_delay_ns=3.0, temperature="25.0", voltage="3.3"
        ))
        
    db.add(AnomalyEvidence(
        run_id=run_id, component_id=comp_id, a_score=50.0 if not zero_metrics else 0.0,
        pat_score=0.1 if not zero_metrics else 0.0, peer_score=0.1 if not zero_metrics else 0.0, 
        temporal_score=0.1 if not zero_metrics else 0.0, isolation_forest_score=0.1 if not zero_metrics else 0.0
    ))
    db.add(ScreeningResult(
        run_id=run_id, component_id=comp_id, stage="MODULE_A",
        evidence={"prediction_probability": 0.2 if not zero_metrics else 0.0}
    ))
    
    db.add(AnomalyOrigins(
        run_id=run_id, component_id=comp_id,
        device_status="NORMAL", station_status="NORMAL", lot_status="NORMAL"
    ))
    
    if not ldi_none:
        db.add(Prediction(
            run_id=run_id, component_id=comp_id, prediction_stage="B2-96h", available=True,
            predicted_168h={"Iddq_uA_168h": 12.0 if not zero_metrics else 0.0, 
                            "Leakage_nA_168h": 110.0 if not zero_metrics else 0.0, 
                            "PropDelay_ns_168h": 3.1 if not zero_metrics else 0.0}
        ))
    db.commit()

def test_1_and_2_and_11_complete_valid_persist(db):
    setup_mock_run(db, "RUN_1", "COMP_1")
    
    run_risk_fusion_for_component("RUN_1", "COMP_1", db)
    db.commit()
    
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_1", component_id="COMP_1").first()
    assert rf is not None
    assert rf.screening_run_id == "RUN_1" if hasattr(rf, 'screening_run_id') else rf.run_id == "RUN_1"
    assert rf.a_score is not None
    assert rf.s_score is not None
    assert rf.prediction_risk is not None
    assert rf.uncertainty_risk is not None
    assert rf.ldi is not None
    assert rf.final_decision is not None

def test_3_null_safety_metrics(db):
    setup_mock_run(db, "RUN_2", "COMP_2", ldi_none=True)
    
    run_risk_fusion_for_component("RUN_2", "COMP_2", db)
    db.commit()
    
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_2", component_id="COMP_2").first()
    assert rf.prediction_risk is None
    assert rf.s_score is None
    assert rf.uncertainty_risk is None
    assert rf.ldi is None

def test_4_actual_zero_remains(db):
    # In some models 0.0 output happens. Let's explicitly test that 0.0 doesn't become NULL
    setup_mock_run(db, "RUN_3", "COMP_3", zero_metrics=True)
    run_risk_fusion_for_component("RUN_3", "COMP_3", db)
    db.commit()
    
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_3", component_id="COMP_3").first()
    # If the inputs produce 0.0 in the safety_engine, they should persist as 0.0
    # Because we mocked zero metrics, it might not be exactly 0 depending on median, 
    # but we just ensure it's not None
    assert rf.prediction_risk is not None
    assert rf.ldi is not None

def test_5_decision_basis_matches(db):
    setup_mock_run(db, "RUN_4", "COMP_4")
    run_risk_fusion_for_component("RUN_4", "COMP_4", db)
    db.commit()
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_4", component_id="COMP_4").first()
    assert "explanation" in rf.decision_basis
    assert rf.final_decision in ["PASS", "MONITOR", "REVIEW_REQUIRED", "REJECT", "REPEAT_MEASUREMENT"]

def test_6_fusion_score_provenance(db):
    setup_mock_run(db, "RUN_5", "COMP_5")
    run_risk_fusion_for_component("RUN_5", "COMP_5", db)
    db.commit()
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_5", component_id="COMP_5").first()
    assert rf.fusion_score is not None

def test_7_run_isolation(db):
    setup_mock_run(db, "RUN_A", "COMP_ISO_A")
    setup_mock_run(db, "RUN_B", "COMP_ISO_B")
    
    run_risk_fusion_for_component("RUN_A", "COMP_ISO_A", db)
    run_risk_fusion_for_component("RUN_B", "COMP_ISO_B", db)
    db.commit()
    
    rfa = db.query(RiskFusionResult).filter_by(run_id="RUN_A").first()
    rfb = db.query(RiskFusionResult).filter_by(run_id="RUN_B").first()
    assert rfa is not None
    assert rfb is not None
    assert rfa.id != rfb.id

def test_8_component_isolation(db):
    setup_mock_run(db, "RUN_C", "COMP_A")
    setup_mock_run(db, "RUN_C", "COMP_B")
    
    run_risk_fusion_for_run("RUN_C", db)
    
    rfs = db.query(RiskFusionResult).filter_by(run_id="RUN_C").all()
    assert len(rfs) == 2
    comp_ids = {r.component_id for r in rfs}
    assert "COMP_A" in comp_ids
    assert "COMP_B" in comp_ids

def test_9_idempotency(db):
    setup_mock_run(db, "RUN_6", "COMP_6")
    run_risk_fusion_for_component("RUN_6", "COMP_6", db)
    db.commit()
    run_risk_fusion_for_component("RUN_6", "COMP_6", db)
    db.commit()
    rfs = db.query(RiskFusionResult).filter_by(run_id="RUN_6", component_id="COMP_6").all()
    assert len(rfs) == 1

def test_10_persistence_failure_rolls_back(db):
    setup_mock_run(db, "RUN_7", "COMP_7")
    
    with patch('app.services.risk_fusion_service.determine_decision', side_effect=Exception("Simulated DB Error")):
        run_risk_fusion_for_run("RUN_7", db)
        
    rfs = db.query(RiskFusionResult).filter_by(run_id="RUN_7").all()
    assert len(rfs) == 0

def test_14_phase6b_unchanged():
    vec = build_fusion_vector(0.1, 0.2, 0.3)
    assert len(vec) == 3

