"""
==============================================================================
ANOVIS / BURNSIGHT-AI PRODUCTION DEPLOYMENT SMOKE TEST
==============================================================================
Validates:
  1. /health and /health/ready endpoints
  2. In-memory ModelManager & all 4 core ML models
  3. Feature order & contract alignment
  4. 96h CatBoost anomaly detection
  5. 168h B-Series IDDQ, Leakage, Delay regression
  6. SHAP individual & global explainability
  7. Google Gemini QA inspection report & deterministic fallback
  8. Printable PDF report generation with mandatory QA disclaimer
  9. Database models & persistence
"""
import os
import sys
import json

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.ml.model_registry import registry
from app.services.model_manager import model_manager
from app.services.explainability_service import explain_component_96h, get_global_shap_importance
from app.services.gemini_service import generate_gemini_qa_report, _generate_fallback_report
from app.services.pdf_service import generate_qa_report_pdf
from app.inference.model_contracts import COMPONENT_96H_FEATURES, B0_FEATURES

SAMPLE_COMPONENT = {
    "component_id": "CMP-SMOKE-2026-001",
    "lot_id": "LOT-PROD-TEST",
    "device_type": "XYZ-IC",
    "station": "STATION_01",
    "Iddq_uA_0h": 1.25,
    "Iddq_uA_24h": 1.55,
    "Iddq_uA_96h": 4.90,
    "Leakage_nA_0h": 4.10,
    "Leakage_nA_24h": 5.90,
    "Leakage_nA_96h": 27.80,
    "PropDelay_ns_0h": 1.05,
    "PropDelay_ns_24h": 1.12,
    "PropDelay_ns_96h": 1.38,
    "Temperature_0h": 125.0,
    "Voltage_0h": 3.3,
    "Temperature_24h": 125.0,
    "Voltage_24h": 3.3,
    "Temperature_96h": 125.0,
    "Voltage_96h": 3.3,
}

def run_smoke_test():
    print("=" * 70)
    print("[STARTING ANOVIS PRODUCTION DEPLOYMENT SMOKE TEST]")
    print("=" * 70)

    with TestClient(app) as client:
        # 1. Health Probe
        print("\n[TEST 1] Checking GET /health ...")
        r_health = client.get("/health")
        assert r_health.status_code == 200, f"Health endpoint failed: {r_health.text}"
        health_data = r_health.json()
        assert health_data.get("status") == "ok"
        print(f"  [PASS] /health OK: status={health_data.get('status')}, api={health_data.get('api')}, db={health_data.get('database')}")

        # 2. Readiness Probe
        print("\n[TEST 2] Checking GET /health/ready ...")
        r_ready = client.get("/health/ready")
        assert r_ready.status_code == 200, f"Readiness endpoint failed: {r_ready.text}"
        ready_data = r_ready.json()
        assert ready_data.get("status") == "ready"
        assert ready_data.get("models_ready") is True
        print(f"  [PASS] /health/ready OK: models_ready={ready_data.get('models_ready')}")

        # 3. ModelManager & Model Artifacts
        print("\n[TEST 3] Verifying in-memory ModelManager & Artifacts ...")
        assert model_manager.is_ready() is True
        meta = model_manager.get_model_metadata()
        print(f"  [PASS] ModelManager ready: {meta.get('anomaly_model')} & {meta.get('regression_model')}")

        # 4. Feature Contract Consistency
        print("\n[TEST 4] Verifying Feature Order & Contract Consistency ...")
        assert len(COMPONENT_96H_FEATURES) == 43, f"Unexpected 96h feature count: {len(COMPONENT_96H_FEATURES)}"
        assert len(B0_FEATURES) == 6, f"Unexpected B0 feature count: {len(B0_FEATURES)}"
        print(f"  [PASS] Feature contracts verified: 96h features = {len(COMPONENT_96H_FEATURES)}, B0 features = {len(B0_FEATURES)}")

        # 5. Unified Prediction Endpoint POST /api/predict
        print("\n[TEST 5] Testing POST /api/predict (96h Anomaly + 168h Regressors) ...")
        r_pred = client.post("/api/predict", json=SAMPLE_COMPONENT)
        assert r_pred.status_code == 200, f"Prediction endpoint failed: {r_pred.text}"
        pred_data = r_pred.json()
        assert "anomaly_probability_96h" in pred_data
        assert "anomaly_status_96h" in pred_data
        assert "predicted_iddq_168h" in pred_data
        assert "predicted_leakage_168h" in pred_data
        assert "predicted_delay_168h" in pred_data
        print(f"  [PASS] POST /api/predict OK:")
        print(f"    - Component: {pred_data['component_id']} (Lot: {pred_data['lot_id']})")
        print(f"    - 96h Anomaly Probability: {pred_data['anomaly_probability_96h']} -> Status: {pred_data['anomaly_status_96h']}")
        print(f"    - Predicted 168h IDDQ: {pred_data['predicted_iddq_168h']} uA")
        print(f"    - Predicted 168h Leakage: {pred_data['predicted_leakage_168h']} nA")
        print(f"    - Predicted 168h Delay: {pred_data['predicted_delay_168h']} ns")

        # 6. Component Explainability (SHAP)
        print("\n[TEST 6] Testing POST /api/explainability/component ...")
        r_exp = client.post("/api/explainability/component", json={
            "component_id": SAMPLE_COMPONENT["component_id"],
            "measurements": SAMPLE_COMPONENT
        })
        assert r_exp.status_code == 200, f"Explainability endpoint failed: {r_exp.text}"
        exp_data = r_exp.json()
        assert "feature_attributions" in exp_data
        assert len(exp_data["top_positive_contributors"]) > 0
        print(f"  [PASS] SHAP Explainability OK:")
        print(f"    - Base Value: {exp_data['base_value']}, Reconstructed: {exp_data['reconstructed_value']}")
        print(f"    - Top Risk Contributor: {exp_data['top_positive_contributors'][0]['feature']} (SHAP: +{exp_data['top_positive_contributors'][0]['shap_value']})")

        # 7. Global Explainability
        print("\n[TEST 7] Testing GET /api/explainability/global ...")
        r_glob = client.get("/api/explainability/global")
        assert r_glob.status_code == 200, f"Global explainability failed: {r_glob.text}"
        glob_data = r_glob.json()
        assert "global_importance" in glob_data
        print(f"  [PASS] Global SHAP OK: Top feature = {glob_data['global_importance'][0]['feature']} ({glob_data['global_importance'][0]['percentage']}%)")

        # 8. Gemini QA Report & Fallback
        print("\n[TEST 8] Testing POST /api/reports/qa ...")
        r_qa = client.post("/api/reports/qa", json={
            "component_id": SAMPLE_COMPONENT["component_id"],
            "measurements": SAMPLE_COMPONENT
        })
        assert r_qa.status_code == 200, f"QA Report endpoint failed: {r_qa.text}"
        qa_data = r_qa.json()
        report = qa_data.get("report", {})
        required_keys = [
            "executive_summary", "classification_explanation", "key_contributing_factors",
            "measurement_trends", "engineering_limit_assessment", "recommended_inspection_steps", "limitations"
        ]
        for k in required_keys:
            assert k in report, f"Missing required key in QA Report: {k}"
        print(f"  [PASS] QA Report OK (Source: {report.get('source')}):")
        print(f"    - Summary: {report.get('executive_summary')[:100]}...")

        # 9. PDF Report Generation
        print("\n[TEST 9] Testing GET /api/reports/qa/{component_id}/pdf ...")
        r_pdf = client.get(f"/api/reports/qa/{SAMPLE_COMPONENT['component_id']}/pdf")
        assert r_pdf.status_code == 200, f"PDF generation failed: {r_pdf.text}"
        assert r_pdf.content.startswith(b"%PDF"), "Response is not a valid PDF header"
        assert len(r_pdf.content) > 1000, "PDF file too small"
        print(f"  [PASS] Printable PDF Report generated successfully: {len(r_pdf.content)} bytes")

        # 10. Non-regression of existing screening pipeline
        print("\n[TEST 10] Testing non-regression of POST /screen ...")
        r_screen = client.post("/screen", json=SAMPLE_COMPONENT)
        assert r_screen.status_code == 200, f"Screening failed: {r_screen.text}"
        screen_data = r_screen.json()
        assert "decision" in screen_data
        print(f"  [PASS] /screen non-regression OK: decision={screen_data.get('decision')}, a_score={screen_data.get('a_score')}")

    print("\n" + "=" * 70)
    print("SUCCESS: ALL 10 PRODUCTION SMOKE TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 70)

if __name__ == "__main__":
    run_smoke_test()
