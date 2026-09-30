"""Database Integration Tests"""
import pytest
from app.db.models import Base, Lot, Component, Measurement, ScreeningResult


def test_health_endpoint(client, db):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    # SQLite memory engine should always be connected
    assert data["database"] == "Connected"

def test_db_insert_and_retrieve(client, db):
    # Create lot
    lot = Lot(lot_id="LOT-TEST")
    db.add(lot)
    db.commit()

    # Create component
    comp = Component(component_id="COMP-001", lot_id="LOT-TEST", device_type="XYZ")
    db.add(comp)
    db.commit()

    # Retrieve
    retrieved = db.query(Component).filter(Component.component_id == "COMP-001").first()
    assert retrieved is not None
    assert retrieved.device_type == "XYZ"
    assert retrieved.lot_id == "LOT-TEST"

def test_get_missing_component(client):
    response = client.get("/component/COMP-MISSING")
    assert response.status_code == 404
