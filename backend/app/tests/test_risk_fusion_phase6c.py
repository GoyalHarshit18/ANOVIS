import pytest
from app.db.models import ScreeningRun, Component, Measurement, Lot, ScreeningResult, AnomalyEvidence, AnomalyOrigins, Prediction, RiskFusionResult
from app.services.risk_fusion_service import run_risk_fusion_for_component
from app.ml.model_registry import registry

def setup_mock_run(db, run_id: str, comp_id: str, with_predictions=True, with_ae=True):
    db.add(ScreeningRun(run_id=run_id, status="MODULE_B_COMPLETED"))
    db.add(Lot(lot_id="LOT_1"))
    db.add(Component(component_id=comp_id, lot_id="LOT_1", station_id="ST_1"))
    
    # Add measurements
    for chk in [0, 24, 96]:
        db.add(Measurement(
            run_id=run_id, component_id=comp_id, checkpoint_hour=chk,
            iddq_ua=10.0, leakage_na=100.0, prop_delay_ns=3.0, temperature="25.0", voltage="3.3"
        ))
        
    if with_ae:
        db.add(AnomalyEvidence(
            run_id=run_id, component_id=comp_id, a_score=50.0,
            pat_score=0.1, peer_score=0.1, temporal_score=0.1, isolation_forest_score=0.1
        ))
        db.add(ScreeningResult(
            run_id=run_id, component_id=comp_id, stage="MODULE_A",
            evidence={"prediction_probability": 0.2}
        ))
        
    db.add(AnomalyOrigins(
        run_id=run_id, component_id=comp_id,
        device_status="NORMAL", station_status="NORMAL", lot_status="NORMAL"
    ))
    
    if with_predictions:
        db.add(Prediction(
            run_id=run_id, component_id=comp_id, prediction_stage="B2-96h", available=True,
            predicted_168h={"Iddq_uA_168h": 12.0, "Leakage_nA_168h": 110.0, "PropDelay_ns_168h": 3.1}
        ))
        
    db.commit()

def test_complete_evidence(db):
    setup_mock_run(db, "RUN_1", "COMP_1")
    
    res = run_risk_fusion_for_component("RUN_1", "COMP_1", db)
    db.commit()
    
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_1").first()
    assert rf is not None
    assert rf.prediction_risk is not None
    assert rf.s_score is not None
    assert rf.uncertainty_risk is not None
    assert rf.ldi is not None
    assert res["decision"] is not None

def test_missing_evidence(db):
    setup_mock_run(db, "RUN_2", "COMP_2", with_predictions=False)
    
    res = run_risk_fusion_for_component("RUN_2", "COMP_2", db)
    db.commit()
    
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_2").first()
    assert rf is not None
    assert rf.prediction_risk is None
    assert rf.s_score is None
    assert rf.uncertainty_risk is None
    assert rf.ldi is None
    
def test_missing_fallback(db):
    # If None, should not fallback to 0.0
    setup_mock_run(db, "RUN_3", "COMP_3", with_predictions=False)
    
    res = run_risk_fusion_for_component("RUN_3", "COMP_3", db)
    db.commit()
    rf = db.query(RiskFusionResult).filter_by(run_id="RUN_3").first()
    assert rf.prediction_risk is not 0.0
    assert rf.s_score is not 0.0
    
def test_idempotency(db):
    setup_mock_run(db, "RUN_4", "COMP_4")
    run_risk_fusion_for_component("RUN_4", "COMP_4", db)
    db.flush()
    run_risk_fusion_for_component("RUN_4", "COMP_4", db)
    db.commit()
    rfs = db.query(RiskFusionResult).filter_by(run_id="RUN_4").all()
    assert len(rfs) == 1
