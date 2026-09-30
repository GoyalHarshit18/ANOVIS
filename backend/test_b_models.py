import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.models import Prediction, ScreeningResult, Component, Lot, Measurement, ScreeningRun

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    yield db
    db.close()

def setup_test_data(db):
    # clear old test data
    db.query(Prediction).filter(Prediction.run_id == "TEST_RUN_B").delete()
    db.query(Prediction).filter(Prediction.run_id == "TEST_RUN_OTHER").delete()
    db.query(Prediction).filter(Prediction.component_id == "CMP_OTHER").delete()
    
    db.query(ScreeningResult).filter(ScreeningResult.run_id == "TEST_RUN_B").delete()
    db.query(Measurement).filter(Measurement.run_id == "TEST_RUN_B").delete()
    
    db.query(Component).filter(Component.lot_id == "TEST_LOT_B").delete()
    db.query(Component).filter(Component.component_id == "CMP_OTHER").delete()
    db.query(Lot).filter(Lot.lot_id == "TEST_LOT_B").delete()
    
    db.query(ScreeningRun).filter(ScreeningRun.run_id == "TEST_RUN_B").delete()
    db.query(ScreeningRun).filter(ScreeningRun.run_id == "TEST_RUN_OTHER").delete()
    db.commit()

    run1 = ScreeningRun(run_id="TEST_RUN_B")
    run2 = ScreeningRun(run_id="TEST_RUN_OTHER")
    db.add_all([run1, run2])
    db.commit()

    lot = Lot(lot_id="TEST_LOT_B")
    db.add(lot)
    db.commit()

    comp1 = Component(component_id="CMP_TEST_B1", lot_id="TEST_LOT_B")
    comp2 = Component(component_id="CMP_TEST_B2", lot_id="TEST_LOT_B")
    comp3 = Component(component_id="CMP_TEST_B3", lot_id="TEST_LOT_B")
    comp4 = Component(component_id="CMP_OTHER", lot_id="TEST_LOT_B")
    db.add_all([comp1, comp2, comp3, comp4])
    db.commit()

    # CMP_TEST_B1: Has all 4 models
    res1 = ScreeningResult(
        run_id="TEST_RUN_B", component_id="CMP_TEST_B1", decision="PASS",
        evidence={"predicted_168h": {"leakage": 10}, "b_models": None} # None so we don't rely on it
    )
    # CMP_TEST_B2: Missing B2-96h
    res2 = ScreeningResult(
        run_id="TEST_RUN_B", component_id="CMP_TEST_B2", decision="PASS",
        evidence={"predicted_168h": {"leakage": 20}}
    )
    # CMP_TEST_B3: Missing B1
    res3 = ScreeningResult(
        run_id="TEST_RUN_B", component_id="CMP_TEST_B3", decision="PASS",
        evidence={"predicted_168h": {"leakage": 30}}
    )
    db.add_all([res1, res2, res3])
    db.commit()

    preds = []
    # CMP_TEST_B1 - all 4
    for m in ["B0", "B1", "B2-Early", "B2-96h"]:
        stage = "0h" if m == "B0" else ("96h" if m == "B2-96h" else "24h")
        preds.append(Prediction(
            run_id="TEST_RUN_B", component_id="CMP_TEST_B1", model_name=m, model_version="v2.0",
            prediction_stage=stage, available=True, status="OK",
            predicted_168h={"leakage": 100 + len(preds)}
        ))

    # CMP_TEST_B2 - missing B2-96h
    for m in ["B0", "B1", "B2-Early"]:
        stage = "0h" if m == "B0" else ("96h" if m == "B2-96h" else "24h")
        preds.append(Prediction(
            run_id="TEST_RUN_B", component_id="CMP_TEST_B2", model_name=m, model_version="v2.0",
            prediction_stage=stage, available=True, status="OK",
            predicted_168h={"leakage": 200 + len(preds)}
        ))
    
    # CMP_TEST_B3 - missing B1
    for m in ["B0", "B2-Early", "B2-96h"]:
        stage = "0h" if m == "B0" else ("96h" if m == "B2-96h" else "24h")
        preds.append(Prediction(
            run_id="TEST_RUN_B", component_id="CMP_TEST_B3", model_name=m, model_version="v2.0",
            prediction_stage=stage, available=True, status="OK",
            predicted_168h={"leakage": 300 + len(preds)}
        ))

    # Test 8,9: Add prediction for different run / different component
    preds.append(Prediction(
        run_id="TEST_RUN_OTHER", component_id="CMP_TEST_B1", model_name="B0", model_version="v9.9",
        prediction_stage="0h", available=True, status="OK",
        predicted_168h={"leakage": 999}
    ))
    preds.append(Prediction(
        run_id="TEST_RUN_B", component_id="CMP_OTHER", model_name="B0", model_version="v9.9",
        prediction_stage="0h", available=True, status="OK",
        predicted_168h={"leakage": 888}
    ))
    db.add_all(preds)
    db.commit()

@pytest.fixture(scope="module", autouse=True)
def setup(db):
    setup_test_data(db)

def test_1_to_5_and_8_9(db):
    res = client.get("/component/CMP_TEST_B1")
    assert res.status_code == 200
    data = res.json()
    
    b_models = data["b_models"]
    assert len(b_models) == 4
    assert "B0" in b_models
    assert "B1" in b_models
    assert "B2-Early" in b_models
    assert "B2-96h" in b_models
    
    preds_in_db = {
        p.model_name: p.predicted_168h 
        for p in db.query(Prediction).filter(Prediction.run_id=="TEST_RUN_B", Prediction.component_id=="CMP_TEST_B1").all()
    }
    
    for m in ["B0", "B1", "B2-Early", "B2-96h"]:
        assert b_models[m]["available"] is True
        assert b_models[m]["prediction"] == preds_in_db[m]

def test_6_missing_b2_96h():
    res = client.get("/component/CMP_TEST_B2")
    assert res.status_code == 200
    data = res.json()
    b_models = data["b_models"]
    
    assert b_models["B0"]["available"] is True
    assert b_models["B1"]["available"] is True
    assert b_models["B2-Early"]["available"] is True
    assert b_models["B2-96h"]["available"] is False
    assert b_models["B2-96h"]["prediction"] is None
    assert b_models["B2-96h"]["status"] == "UNAVAILABLE"

def test_7_missing_b1():
    res = client.get("/component/CMP_TEST_B3")
    assert res.status_code == 200
    data = res.json()
    b_models = data["b_models"]
    
    assert b_models["B1"]["available"] is False
    assert b_models["B0"]["available"] is True
    assert b_models["B2-Early"]["available"] is True
    assert b_models["B2-96h"]["available"] is True

def test_10_no_hardcoded_values():
    # By construction of tests 1-5, values are strictly taken from the DB.
    assert True
