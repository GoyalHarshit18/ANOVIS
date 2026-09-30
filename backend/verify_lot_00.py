import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import ScreeningRun, Component, RiskFusionResult
from app.services.ingestion_service import process_csv_upload
from app.services.module_a_service import run_module_a_for_run
from app.services.anomaly_analysis_service import run_anomaly_analysis_for_run
from app.services.module_b_service import run_module_b_for_run
from app.services.risk_fusion_service import run_risk_fusion_for_run

from app.db.database import Base
engine = create_engine("sqlite:///sih26170_lot00.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

with open("LOT_00.csv", "rb") as f:
    content = f.read()

res = process_csv_upload(content, "LOT_00.csv", db)
run_id = res["run_id"]

print(f"Run ID: {run_id}")

run_module_a_for_run(run_id, db)
run_anomaly_analysis_for_run(run_id, db)
run_module_b_for_run(run_id, db)
run_risk_fusion_for_run(run_id, db)

# Query results
rf = db.query(RiskFusionResult).filter_by(run_id=run_id).first()
if rf:
    print(f"Component: {rf.component_id}")
    print(f"A_Score: {rf.a_score}")
    print(f"S_Score: {rf.s_score}")
    print(f"Prediction_Risk: {rf.prediction_risk}")
    print(f"Uncertainty_Risk: {rf.uncertainty_risk}")
    print(f"LDI: {rf.ldi}")
    print(f"Fusion_Score: {rf.fusion_score}")
    print(f"Final_Decision: {rf.final_decision}")
    print(f"Decision_Basis: {json.dumps(rf.decision_basis, indent=2)}")
else:
    print("No RiskFusionResult found.")
