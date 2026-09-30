import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.models import Prediction, ScreeningResult, Component, Lot, Measurement, ScreeningRun, SafetyEnvelope, PredictionInterval

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    yield db
    db.close()

def setup_test_data(db):
    # clear old test data
    db.query(PredictionInterval).delete()
    db.query(Prediction).filter(Prediction.run_id == "TEST_RUN_C").delete()
    db.query(SafetyEnvelope).filter(SafetyEnvelope.run_id == "TEST_RUN_C").delete()
    db.query(ScreeningResult).filter(ScreeningResult.run_id == "TEST_RUN_C").delete()
    db.query(Component).filter(Component.lot_id == "TEST_LOT_C").delete()
    db.query(Lot).filter(Lot.lot_id == "TEST_LOT_C").delete()
    db.query(ScreeningRun).filter(ScreeningRun.run_id == "TEST_RUN_C").delete()
    db.commit()

    run = ScreeningRun(run_id="TEST_RUN_C")
    db.add(run)
    db.commit()

    lot = Lot(lot_id="TEST_LOT_C")
    db.add(lot)
    db.commit()

    # Comp 1: Has Envelope and Interval and all predictions
    comp1 = Component(component_id="CMP_TEST_C1", lot_id="TEST_LOT_C")
    # Comp 2: No Envelope, no interval
    comp2 = Component(component_id="CMP_TEST_C2", lot_id="TEST_LOT_C")
    db.add_all([comp1, comp2])
    db.commit()

    res1 = ScreeningResult(
        run_id="TEST_RUN_C", component_id="CMP_TEST_C1", decision="PASS",
        s_score=100.0, prediction_risk=50.0, uncertainty_risk=20.0,
        evidence={"predicted_168h": {"Leakage_nA_168h": 10}, "basis": {"mode": "demo"}}
    )
    res2 = ScreeningResult(
        run_id="TEST_RUN_C", component_id="CMP_TEST_C2", decision="PASS",
        s_score=99.0, prediction_risk=99.0, uncertainty_risk=99.0,
        evidence={"predicted_168h": {"Leakage_nA_168h": 20}}
    )
    db.add_all([res1, res2])
    db.commit()

    # Add predictions
    p1 = Prediction(
        run_id="TEST_RUN_C", component_id="CMP_TEST_C1", model_name="B0", model_version="vB0",
        prediction_stage="0h", available=True, status="OK"
    )
    p2 = Prediction(
        run_id="TEST_RUN_C", component_id="CMP_TEST_C1", model_name="B2-96h", model_version="vB2_96h",
        prediction_stage="96h", available=True, status="OK"
    )
    
    p3 = Prediction(
        run_id="TEST_RUN_C", component_id="CMP_TEST_C2", model_name="B1", model_version="vB1_C2",
        prediction_stage="24h", available=True, status="OK"
    )
    db.add_all([p1, p2, p3])
    db.commit()
    
    # Add interval to p2
    inv = PredictionInterval(
        prediction_id=p2.id, parameter="Leakage_nA", lower=5.0, upper=15.0, calibrated=True
    )
    db.add(inv)
    db.commit()
    
    # Add envelope to comp1
    env = SafetyEnvelope(
        run_id="TEST_RUN_C", component_id="CMP_TEST_C1", parameter="Leakage_nA", lower=0.0, upper=100.0
    )
    db.add(env)
    db.commit()

@pytest.fixture(scope="module", autouse=True)
def setup(db):
    setup_test_data(db)

def test_basis_model_and_version():
    res = client.get("/component/CMP_TEST_C1")
    data = res.json()
    assert data["basis"]["b_model"] == "B2-96h"
    assert data["model_version"] == "vB2_96h"
    assert data["model_version"] != "component_24h_classifier.pkl"
    assert data["basis"]["safety_score_calibrated"] is True

def test_basis_fallback():
    res = client.get("/component/CMP_TEST_C2")
    data = res.json()
    assert data["basis"]["b_model"] == "B1"
    assert data["model_version"] == "vB1_C2"

def test_interval_exists():
    res = client.get("/component/CMP_TEST_C1")
    data = res.json()
    assert data["intervals"]["Leakage_nA"]["lower"] == 5.0
    assert data["intervals"]["Leakage_nA"]["upper"] == 15.0

def test_interval_not_exists():
    res = client.get("/component/CMP_TEST_C2")
    data = res.json()
    assert "Leakage_nA" not in data["intervals"] or data["intervals"]["Leakage_nA"] is None

def test_safety_envelope_exists():
    res = client.get("/component/CMP_TEST_C1")
    data = res.json()
    assert data["safety"]["details"]["Leakage_nA"]["engineering_limit_upper"] == 100.0
    assert data["safety"]["details"]["Leakage_nA"]["status"] == "WITHIN_LIMIT"
    # Consistency
    assert data["safety"]["s_score"] == 100.0
    assert data["safety"]["prediction_risk"] == 50.0
    
def test_safety_envelope_not_exists():
    res = client.get("/component/CMP_TEST_C2")
    data = res.json()
    # No limit
    assert "engineering_limit_upper" not in data["safety"]["details"]["Leakage_nA"] or data["safety"]["details"]["Leakage_nA"]["engineering_limit_upper"] is None
    # Top level nullified
    assert data["safety"]["s_score"] is None
    assert data["safety"]["prediction_risk"] is None
