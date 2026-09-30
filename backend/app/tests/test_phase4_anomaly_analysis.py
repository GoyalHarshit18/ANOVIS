import pytest
from app.db.models import ScreeningRun, Component, Measurement, Lot, ScreeningResult, AnomalyEvidence, AnomalyOrigins, LotAnalysis, StationAnalysis
from app.ml.model_registry import registry

def setup_mock_run(db, run_id: str, components: dict, lot_id: str = "LOT_1", station_id: str = "STATION_1"):
    if not db.query(ScreeningRun).filter_by(run_id=run_id).first():
        db.add(ScreeningRun(run_id=run_id, status="MODULE_A_COMPLETED"))
    if not db.query(Lot).filter_by(lot_id=lot_id).first():
        db.add(Lot(lot_id=lot_id))
        
    for comp_id, chkpts in components.items():
        db.add(Component(component_id=comp_id, lot_id=lot_id, station_id=station_id))
        
        for chk, meas in chkpts.items():
            db.add(Measurement(
                run_id=run_id,
                component_id=comp_id,
                checkpoint_hour=chk,
                iddq_ua=meas.get("iddq_ua"),
                leakage_na=meas.get("leakage_na"),
                prop_delay_ns=meas.get("prop_delay_ns"),
                temperature=meas.get("temperature", "25.0"),
                voltage=meas.get("voltage", "3.3")
            ))
            
        # Add mock Module A Evidence
        db.add(ScreeningResult(
            run_id=run_id,
            component_id=comp_id,
            decision="ANOMALOUS",
            a_score=0.85,
            evidence={"prediction_class": 1}
        ))
        
        db.add(AnomalyEvidence(
            run_id=run_id,
            component_id=comp_id,
            pat_evidence={"status": "HIGH"},
            peer_evidence={"status": "NORMAL"}
        ))
            
    db.commit()

def test_device_origin(client, db):
    setup_mock_run(db, "RUN_1", components={
        "COMP_1": {
            0: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0},
            24: {"iddq_ua": 1.1, "leakage_na": 11.0, "prop_delay_ns": 5.1}
        }
    })
    
    response = client.post("/screening-runs/RUN_1/anomaly-analysis")
    assert response.status_code == 200
    
    origin = db.query(AnomalyOrigins).filter_by(run_id="RUN_1", component_id="COMP_1").first()
    assert origin is not None
    assert origin.device_status == "ANOMALOUS"
    assert origin.device_score == 0.85
    assert origin.evidence["a_score"] == 0.85
    assert origin.evidence["pat_status"] == "HIGH"
    
def test_lot_shift(client, db):
    # High iddq lot to force shift detection
    setup_mock_run(db, "RUN_2", components={
        "COMP_1": {
            0: {"iddq_ua": 50.0, "leakage_na": 10.0, "prop_delay_ns": 3.3},
            24: {"iddq_ua": 50.0, "leakage_na": 10.0, "prop_delay_ns": 3.3}
        },
        "COMP_2": {
            0: {"iddq_ua": 51.0, "leakage_na": 10.0, "prop_delay_ns": 3.3},
            24: {"iddq_ua": 51.0, "leakage_na": 10.0, "prop_delay_ns": 3.3}
        }
    })
    
    response = client.post("/screening-runs/RUN_2/anomaly-analysis")
    assert response.status_code == 200
    
    lot_analysis = db.query(LotAnalysis).filter_by(run_id="RUN_2", lot_id="LOT_1").first()
    assert lot_analysis.status == "SHIFT_DETECTED"
    assert lot_analysis.affected_component_count == 2
    
def test_healthy_lot(client, db):
    # Healthy Iddq inside reference limits
    setup_mock_run(db, "RUN_3", components={
        "COMP_1": {
            0: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3},
            24: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3}
        }
    })
    
    response = client.post("/screening-runs/RUN_3/anomaly-analysis")
    assert response.status_code == 200
    
    lot_analysis = db.query(LotAnalysis).filter_by(run_id="RUN_3", lot_id="LOT_1").first()
    assert lot_analysis.status == "NORMAL"
    
def test_multiple_stations(client, db):
    setup_mock_run(db, "RUN_4", components={
        "COMP_1": {0: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3}, 24: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3}}
    }, station_id="STATION_A")
    setup_mock_run(db, "RUN_4", components={
        "COMP_2": {0: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3}, 24: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3}}
    }, station_id="STATION_B")
    
    response = client.post("/screening-runs/RUN_4/anomaly-analysis")
    assert response.status_code == 200
    
    stations = db.query(StationAnalysis).filter_by(run_id="RUN_4").all()
    assert len(stations) == 2
    
def test_missing_checkpoint(client, db):
    # Missing 24h
    setup_mock_run(db, "RUN_5", components={
        "COMP_1": {0: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3}}
    })
    
    response = client.post("/screening-runs/RUN_5/anomaly-analysis")
    assert response.status_code == 200
    
    station = db.query(StationAnalysis).filter_by(run_id="RUN_5").first()
    assert station is None or station.integrity_status == "UNAVAILABLE"
    
def test_idempotency(client, db):
    setup_mock_run(db, "RUN_6", components={
        "COMP_1": {0: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3}, 24: {"iddq_ua": 13.0, "leakage_na": 540.0, "prop_delay_ns": 3.3}}
    })
    
    client.post("/screening-runs/RUN_6/anomaly-analysis")
    client.post("/screening-runs/RUN_6/anomaly-analysis")
    
    origins = db.query(AnomalyOrigins).filter_by(run_id="RUN_6").all()
    assert len(origins) == 1
    
    lots = db.query(LotAnalysis).filter_by(run_id="RUN_6").all()
    assert len(lots) == 1
