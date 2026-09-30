import json
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db
from app.db.models import ScreeningRun, Component, Measurement, AnomalyEvidence, ScreeningResult, AnomalyOrigins, LotAnalysis, StationAnalysis

def run_e2e():
    print("--- STARTING LOT_00 E2E ---")
    
    with TestClient(app) as client:
        # 1. Upload CSV
        print("1. Uploading CSV...")
        with open("LOT_00.csv", "rb") as f:
            response = client.post("/upload", files={"file": ("LOT_00.csv", f, "text/csv")})
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        run_id = data["run_id"]
        print(f"   Success! run_id: {run_id}")
        
        # 2. Module A
        print("2. Running Module A...")
        response = client.post(f"/screening-runs/{run_id}/module-a")
        assert response.status_code == 200, f"Module A failed: {response.text}"
        print(f"   Success! Module A returned: {response.json()}")
        
        # 3. Phase 4 Anomaly Analysis
        print("3. Running Phase 4 Anomaly Analysis...")
        response = client.post(f"/screening-runs/{run_id}/anomaly-analysis")
        assert response.status_code == 200, f"Phase 4 failed: {response.text}"
        phase4_result = response.json()
        print(f"   Success! Phase 4 returned:\n{json.dumps(phase4_result, indent=2)}")
        
        # 4. Phase 5 Module B
        print("4. Running Phase 5 Module B...")
        response = client.post(f"/screening-runs/{run_id}/module-b")
        assert response.status_code == 200, f"Module B failed: {response.text}"
        mod_b = response.json()
        print(f"   Success! Phase 5 returned:\n{json.dumps(mod_b, indent=2)}")
        
        # 5. Phase 6 Risk Fusion
        print("5. Running Phase 6 Risk Fusion...")
        response = client.post(f"/screening-runs/{run_id}/risk-fusion")
        assert response.status_code == 200, f"Phase 6 failed: {response.text}"
        mod_c = response.json()
        print(f"   Success! Phase 6 returned:\n{json.dumps(mod_c, indent=2)}")
    
    # 6. DB checks
    print("6. Checking Database Row Counts...")
    db = next(get_db())
    from app.db.models import Prediction, RiskFusionResult
    
    comp_count = db.query(Component).filter(Component.measurements.any(Measurement.run_id == run_id)).count()
    origins_count = db.query(AnomalyOrigins).filter_by(run_id=run_id).count()
    lot_count = db.query(LotAnalysis).filter_by(run_id=run_id).count()
    station_count = db.query(StationAnalysis).filter_by(run_id=run_id).count()
    preds_count = db.query(Prediction).filter_by(run_id=run_id).count()
    rf_count = db.query(RiskFusionResult).filter_by(run_id=run_id).count()
    
    print(f"   Components for run: {comp_count}")
    print(f"   AnomalyOrigins saved: {origins_count}")
    print(f"   LotAnalysis saved: {lot_count}")
    print(f"   StationAnalysis saved: {station_count}")
    print(f"   Predictions saved: {preds_count}")
    print(f"   RiskFusionResults saved: {rf_count}")
    
    print("--- LOT_00 E2E COMPLETED SUCCESSFULLY ---")

if __name__ == "__main__":
    run_e2e()
