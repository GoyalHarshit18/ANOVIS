import pytest
import io

from app.db.models import Measurement, Component, Lot, ScreeningRun

def test_valid_complete_lot(client, db):
    csv_data = """component_id,lot_id,iddq_ua_0h,iddq_ua_24h,iddq_ua_96h,iddq_ua_168h
COMP_001,LOT_A,1.0,1.1,1.2,1.3
COMP_002,LOT_A,2.0,2.1,2.2,2.3
"""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY_FOR_INFERENCE"
    assert data["lot_id"] == "LOT_A"
    assert data["component_count"] == 2
    assert data["valid_rows"] == 2
    assert data["invalid_rows"] == 0
    
    # DB Checks
    run = db.query(ScreeningRun).filter_by(run_id=data["run_id"]).first()
    assert run is not None
    
    lot = db.query(Lot).filter_by(lot_id="LOT_A").first()
    assert lot is not None
    
    comps = db.query(Component).all()
    assert len(comps) == 2
    
    meas = db.query(Measurement).all()
    assert len(meas) == 8 # 2 comps * 4 checkpoints

def test_missing_96h(client, db):
    csv_data = """component_id,lot_id,iddq_ua_0h,iddq_ua_24h,iddq_ua_96h,iddq_ua_168h
COMP_001,LOT_A,1.0,1.1,,1.3
"""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["checkpoint_summary"]["96h"]["count"] == 0
    assert data["data_readiness"]["component_96h"] == "UNAVAILABLE"
    meas = db.query(Measurement).filter_by(checkpoint_hour=96).first()
    assert meas is None

def test_missing_required_column(client, db):
    csv_data = """lot_id,iddq_ua_0h
LOT_A,1.0
"""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error"] == "CSV_VALIDATION_FAILED"
    assert "component_id" in data["detail"]["message"]

def test_multiple_lots(client, db):
    csv_data = """component_id,lot_id,iddq_ua_0h
COMP_001,LOT_A,1.0
COMP_002,LOT_B,1.0
"""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "MULTIPLE_LOTS_IN_SINGLE_UPLOAD"

def test_duplicate_component(client, db):
    csv_data = """component_id,lot_id,iddq_ua_0h
COMP_001,LOT_A,1.0
COMP_001,LOT_A,2.0
"""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 422
    data = response.json()["detail"]
    assert data["error"] == "CSV_VALIDATION_FAILED"
    assert "Duplicate components" in data["message"]

def test_malformed_numeric_value(client, db):
    csv_data = """component_id,lot_id,iddq_ua_0h,iddq_ua_24h
COMP_001,LOT_A,1.0,abc
"""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 422
    assert "Validation errors encountered" in response.json()["detail"]["message"]

def test_empty_csv(client, db):
    csv_data = ""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "CSV_VALIDATION_FAILED"

def test_unknown_column(client, db):
    csv_data = """component_id,lot_id,iddq_ua_0h,operator_name
COMP_001,LOT_A,1.0,Alice
"""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    warnings = data["warnings"]
    assert any("operator_name" in str(w.get("unknown_columns", [])) for w in warnings)

def test_reupload_same_component(client, db):
    csv_data1 = """component_id,lot_id,iddq_ua_0h
COMP_001,LOT_A,1.0
"""
    client.post("/upload", files={"file": ("test.csv", io.BytesIO(csv_data1.encode("utf-8")), "text/csv")})
    
    csv_data2 = """component_id,lot_id,iddq_ua_0h,iddq_ua_24h
COMP_001,LOT_A,1.0,2.0
"""
    response = client.post("/upload", files={"file": ("test.csv", io.BytesIO(csv_data2.encode("utf-8")), "text/csv")})
    
    assert response.status_code == 200
    data = response.json()
    runs = db.query(ScreeningRun).all()
    assert len(runs) == 2
    
    meas = db.query(Measurement).filter_by(component_id="COMP_001").all()
    assert len(meas) == 3 # 0h from run1, 0h & 24h from run2

def test_transaction_rollback(client, monkeypatch, db):
    # We'll monkeypatch db.commit to raise an exception
    from sqlalchemy.orm import Session
    original_commit = Session.commit
    
    def fake_commit(self):
        raise Exception("Fake DB Failure")
        
    monkeypatch.setattr(Session, "commit", fake_commit)
    
    csv_data = """component_id,lot_id,iddq_ua_0h
COMP_001,LOT_A,1.0
"""
    files = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/upload", files=files)
    
    assert response.status_code == 500
    assert response.json()["detail"]["error"] == "INGESTION_FAILED"
    
    monkeypatch.undo()
    comps = db.query(Component).all()
    assert len(comps) == 0 # Rolled back!
