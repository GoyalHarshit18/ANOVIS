import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base
from app.db.session import get_db
from app.db.models import Measurement, Component, Lot, ScreeningRun, AnomalyEvidence, ScreeningResult

import os
db_path = os.path.join(os.path.dirname(__file__), "test_phase3.db").replace("\\", "/")



    
def setup_mock_run(db, run_id, lot_id="LOT_A", components=None):
    if not db.query(Lot).filter_by(lot_id=lot_id).first():
        db.add(Lot(lot_id=lot_id))
    
    run = db.query(ScreeningRun).filter_by(run_id=run_id).first()
    if not run:
        run = ScreeningRun(run_id=run_id, lot_id=lot_id, status="READY_FOR_INFERENCE")
        db.add(run)

    for comp_id, checkpoints in components.items():
        if not db.query(Component).filter_by(component_id=comp_id).first():
            db.add(Component(component_id=comp_id, lot_id=lot_id))
            
        for chk, meas in checkpoints.items():
            db.add(Measurement(
                run_id=run_id,
                component_id=comp_id,
                checkpoint_hour=chk,
                iddq_ua=meas.get("iddq_ua"),
                leakage_na=meas.get("leakage_na"),
                prop_delay_ns=meas.get("prop_delay_ns"),
                temperature=meas.get("temperature"),
                voltage=meas.get("voltage")
            ))
            
    db.commit()

def test_single_valid_component(client, db):
    setup_mock_run(db, "RUN_1", components={
        "COMP_1": {
            0: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0, "temperature": "25.0", "voltage": "3.3"},
            24: {"iddq_ua": 1.1, "leakage_na": 11.0, "prop_delay_ns": 5.1, "temperature": "25.0", "voltage": "3.3"}
        }
    })
    
    response = client.post("/screening-runs/RUN_1/module-a")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "MODULE_A_COMPLETED"
    assert data["total_components"] == 1
    assert data["processed_components"] == 1
    
    # Check persistence
    ae = db.query(AnomalyEvidence).filter_by(run_id="RUN_1", component_id="COMP_1").first()
    assert ae is not None
    assert ae.a_score is not None
    assert ae.pat_evidence is not None
    assert ae.peer_evidence is not None
    
    sr = db.query(ScreeningResult).filter_by(run_id="RUN_1", component_id="COMP_1").first()
    assert sr is not None
    assert sr.decision == "AVAILABLE"
    assert sr.evidence.get("prediction_class") is not None

def test_multi_component_lot(client, db):
    setup_mock_run(db, "RUN_2", components={
        "COMP_1": {
            0: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0, "temperature": "25.0", "voltage": "3.3"},
            24: {"iddq_ua": 1.1, "leakage_na": 11.0, "prop_delay_ns": 5.1, "temperature": "25.0", "voltage": "3.3"}
        },
        "COMP_2": {
            0: {"iddq_ua": 2.0, "leakage_na": 20.0, "prop_delay_ns": 6.0, "temperature": "25.0", "voltage": "3.3"},
            24: {"iddq_ua": 2.1, "leakage_na": 21.0, "prop_delay_ns": 6.1, "temperature": "25.0", "voltage": "3.3"}
        }
    })
    
    response = client.post("/screening-runs/RUN_2/module-a")
    assert response.status_code == 200
    data = response.json()
    assert data["total_components"] == 2
    assert data["processed_components"] == 2

def test_missing_24h(client, db):
    setup_mock_run(db, "RUN_3", components={
        "COMP_1": {
            0: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0}
        }
    })
    
    response = client.post("/screening-runs/RUN_3/module-a")
    assert response.status_code == 200
    data = response.json()
    assert data["unavailable_components"] == 1
    assert data["status"] == "MODULE_A_COMPLETED_WITH_WARNINGS"
    
    sr = db.query(ScreeningResult).filter_by(run_id="RUN_3", component_id="COMP_1").first()
    assert sr.decision == "UNAVAILABLE"

def test_missing_0h(client, db):
    setup_mock_run(db, "RUN_4", components={
        "COMP_1": {
            24: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0}
        }
    })
    
    response = client.post("/screening-runs/RUN_4/module-a")
    assert response.status_code == 200
    data = response.json()
    assert data["unavailable_components"] == 1

def test_wrong_run_isolation(client, db):
    setup_mock_run(db, "RUN_A", components={
        "COMP_1": {
            0: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0}
        }
    })
    setup_mock_run(db, "RUN_B", components={
        "COMP_1": {
            24: {"iddq_ua": 1.1, "leakage_na": 11.0, "prop_delay_ns": 5.1}
        }
    })
    
    # Run A has only 0h, Run B has only 24h. They should BOTH be unavailable
    response = client.post("/screening-runs/RUN_A/module-a")
    assert response.json()["unavailable_components"] == 1
    
    response = client.post("/screening-runs/RUN_B/module-a")
    assert response.json()["unavailable_components"] == 1

def test_component_failure_isolation(client, db):
    setup_mock_run(db, "RUN_6", components={
        "COMP_1": {
            0: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0, "temperature": "25.0", "voltage": "3.3"},
            24: {"iddq_ua": 1.1, "leakage_na": 11.0, "prop_delay_ns": 5.1, "temperature": "25.0", "voltage": "3.3"}
        },
        "COMP_2": {
            24: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0, "temperature": "25.0", "voltage": "3.3"} # Missing 0h
        }
    })
    
    response = client.post("/screening-runs/RUN_6/module-a")
    data = response.json()
    assert data["processed_components"] == 1
    assert data["unavailable_components"] == 1

def test_idempotency(client, db):
    setup_mock_run(db, "RUN_7", components={
        "COMP_1": {
            0: {"iddq_ua": 1.0, "leakage_na": 10.0, "prop_delay_ns": 5.0, "temperature": "25.0", "voltage": "3.3"},
            24: {"iddq_ua": 1.1, "leakage_na": 11.0, "prop_delay_ns": 5.1, "temperature": "25.0", "voltage": "3.3"}
        }
    })
    
    client.post("/screening-runs/RUN_7/module-a")
    client.post("/screening-runs/RUN_7/module-a")
    
    # Check no duplicates
    aes = db.query(AnomalyEvidence).filter_by(run_id="RUN_7").all()
    assert len(aes) == 1
    
    srs = db.query(ScreeningResult).filter_by(run_id="RUN_7").all()
    assert len(srs) == 1
