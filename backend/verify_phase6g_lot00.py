import json
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import ScreeningRun, Component, Measurement, AnomalyEvidence, AnomalyOrigins, Prediction, RiskFusionResult, AuditEvent
from app.services.ingestion_service import process_csv_upload
from app.services.module_a_service import run_module_a_for_run
from app.services.anomaly_analysis_service import run_anomaly_analysis_for_run
from app.services.module_b_service import run_module_b_for_run

# For API test, we simulate API behavior or invoke directly via TestClient
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

engine = create_engine("sqlite:///sih26170_lot00_e2e.db")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)

def get_test_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[app.dependency_overrides.get("get_db", get_test_db)] = get_test_db

from app.ml.model_registry import registry
registry.load_all()

def main():
    db = SessionLocal()
    
    # 1. Ingestion
    print("=== 1. Ingestion ===")
    with open("LOT_00.csv", "rb") as f:
        content = f.read()
    
    res = process_csv_upload(content, "LOT_00.csv", db)
    if "run_id" not in res:
        print("Ingestion failed")
        sys.exit(1)
        
    run_id = res["run_id"]
    print(f"Run ID: {run_id}")
    
    comps = db.query(Component).filter_by(lot_id="LOT_00").count()
    meas = db.query(Measurement).filter_by(run_id=run_id).count()
    print(f"Components: {comps}")
    print(f"Measurements: {meas}")
    
    # 2. Module A
    print("\n=== 2. Module A ===")
    run_module_a_for_run(run_id, db)
    mod_a_count = db.query(AnomalyEvidence).filter_by(run_id=run_id).count()
    print(f"Module A outputs: {mod_a_count}")
    
    # 3. Phase 4
    print("\n=== 3. Phase 4 Anomaly Analysis ===")
    run_anomaly_analysis_for_run(run_id, db)
    phase4_count = db.query(AnomalyOrigins).filter_by(run_id=run_id).count()
    print(f"Phase 4 outputs: {phase4_count}")
    
    # 4. Module B
    print("\n=== 4. Module B ===")
    run_module_b_for_run(run_id, db)
    mod_b_count = db.query(Prediction).filter_by(run_id=run_id).count()
    print(f"Module B predictions: {mod_b_count}")
    
    # 5. Risk Fusion (API execution)
    print("\n=== 5. Risk Fusion API Execution ===")
    from app.db.session import get_db
    def override_get_db_lambda():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db_lambda
    api_response = client.post(f"/screening-runs/{run_id}/risk-fusion")
    if api_response.status_code != 200:
        print(f"API Error: {api_response.text}")
        sys.exit(1)
        
    api_data = api_response.json()
    results_api = api_data["results"]
    
    # 6. DB Verification & Parity
    print("\n=== 6. DB vs API Parity ===")
    rf_db_all = db.query(RiskFusionResult).filter_by(run_id=run_id).all()
    rf_count = len(rf_db_all)
    print(f"RiskFusionResult rows: {rf_count}")
    
    decision_dist = {}
    null_ldi_count = 0
    null_s_score_count = 0
    null_a_score_count = 0
    
    for r_db in rf_db_all:
        r_api = next((x for x in results_api if x["component_id"] == r_db.component_id), None)
        if not r_api:
            print(f"Component {r_db.component_id} missing in API!")
            sys.exit(1)
            
        # Parity Check
        assert r_api["a_score"] == r_db.a_score
        assert r_api["s_score"] == r_db.s_score
        assert r_api["prediction_risk"] == r_db.prediction_risk
        assert r_api["uncertainty_risk"] == r_db.uncertainty_risk
        assert r_api["ldi"] == r_db.ldi
        assert r_api["fusion_score"] == r_db.fusion_score
        assert r_api["final_decision"] == r_db.final_decision
        assert r_api["decision_basis"] == r_db.decision_basis
        assert r_api["model_version"] == r_db.model_version
        
        # Stats
        dec = r_db.final_decision or "UNAVAILABLE"
        decision_dist[dec] = decision_dist.get(dec, 0) + 1
        
        if r_db.ldi is None: null_ldi_count += 1
        if r_db.s_score is None: null_s_score_count += 1
        if r_db.a_score is None: null_a_score_count += 1
        
    print("API and DB match 100%.")
    
    print("\n=== 7. Idempotency ===")
    client.post(f"/screening-runs/{run_id}/risk-fusion")
    rf_count_2 = db.query(RiskFusionResult).filter_by(run_id=run_id).count()
    assert rf_count == rf_count_2
    print("Idempotency verified. No duplicate rows.")
    
    print("\n=== 8. Audit Trail ===")
    audit_count = db.query(AuditEvent).filter_by(run_id=run_id, event_type="RISK_FUSION").count()
    print(f"Risk Fusion Audit events: {audit_count}")
    
    print("\n=== SUMMARY ===")
    print(f"Components: {comps}")
    print(f"Measurements: {meas}")
    print(f"Module A outputs: {mod_a_count}")
    print(f"Phase 4 outputs: {phase4_count}")
    print(f"Module B predictions: {mod_b_count}")
    print(f"RiskFusionResult rows: {rf_count}")
    print(f"LDI unavailable: {null_ldi_count}")
    print(f"S_SCORE unavailable: {null_s_score_count}")
    print(f"A_SCORE unavailable: {null_a_score_count}")
    
    print("\nDECISION DISTRIBUTION:")
    for k, v in decision_dist.items():
        print(f"{k}: {v}")
        
    print("\nSUCCESS!")
    
if __name__ == "__main__":
    main()
