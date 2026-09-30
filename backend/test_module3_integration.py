from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_integration():
    print("==================================================")
    print("MODULE 3 END-TO-END INTEGRATION TEST")
    print("==================================================")
    
    # 1. Health
    print("\n[1] Checking Health...")
    r = client.get("/health")
    assert r.status_code == 200, f"Health failed: {r.text}"
    print("Health check OK:", r.json().get("api"))

    # 2. Global Explainability
    print("\n[2] Testing /api/explainability/global...")
    r = client.get("/api/explainability/global")
    assert r.status_code == 200, f"Global explainability failed: {r.text}"
    global_exp = r.json()
    print("Model:", global_exp.get("model_name"))
    print("Top feature ranking count:", len(global_exp.get("global_importance", [])))
    print("Top 3 features:")
    for f in global_exp.get("global_importance", [])[:3]:
        print(f"  - {f['feature']}: |SHAP| = {f['mean_abs_shap']} ({f['percentage']}%)")

    # 3. Component Explainability
    print("\n[3] Testing /api/explainability/component...")
    sample_measurements = {
        "component_id": "CMP_00173",
        "lot_id": "LOT_101",
        "Iddq_uA_0h": 1.25, "Iddq_uA_24h": 1.55, "Iddq_uA_96h": 4.85,
        "Leakage_nA_0h": 4.10, "Leakage_nA_24h": 5.90, "Leakage_nA_96h": 27.40,
        "PropDelay_ns_0h": 1.05, "PropDelay_ns_24h": 1.12, "PropDelay_ns_96h": 1.38,
        "Temperature_0h": 125, "Voltage_0h": 3.3,
        "Temperature_24h": 125, "Voltage_24h": 3.3,
        "Temperature_96h": 125, "Voltage_96h": 3.3
    }
    r = client.post("/api/explainability/component", json={
        "component_id": "CMP_00173",
        "measurements": sample_measurements
    })
    assert r.status_code == 200, f"Component explainability failed: {r.text}"
    comp_exp = r.json()
    print(f"Component: {comp_exp.get('component_id')}")
    print(f"Predicted Status: {comp_exp.get('predicted_status')} (Prob: {comp_exp.get('anomaly_probability'):.4f})")
    print(f"Top Positive Features: {len(comp_exp.get('top_positive_contributors', []))}")
    for item in comp_exp.get("top_positive_contributors", [])[:3]:
        print(f"  + {item['feature']}: +{item['shap_value']:.4f} (Actual: {item['actual_value']})")
    print(f"Top Negative Features: {len(comp_exp.get('top_negative_contributors', []))}")
    for item in comp_exp.get("top_negative_contributors", [])[:3]:
        print(f"  - {item['feature']}: {item['shap_value']:.4f} (Actual: {item['actual_value']})")
    
    # 4. QA Report via Gemini
    print("\n[4] Testing /api/reports/qa with Google Gemini API...")
    r = client.post("/api/reports/qa", json={
        "component_id": "CMP_00173",
        "measurements": sample_measurements
    })
    assert r.status_code == 200, f"QA Report failed: {r.text}"
    qa_res = r.json()
    report = qa_res.get("report", {})
    print("Report Source:", report.get("source"))
    print("Executive Summary:\n", report.get("executive_summary"))
    print("Classification Explanation:\n", report.get("classification_explanation"))
    print("Key Contributing Factors:\n", report.get("key_contributing_factors"))
    print("Recommended Steps:\n", report.get("recommended_inspection_steps"))
    
    # 5. PDF generation
    print("\n[5] Testing PDF Report Generation...")
    from app.services.pdf_service import generate_qa_report_pdf
    pdf_bytes = generate_qa_report_pdf(comp_exp, report, None)
    assert pdf_bytes.startswith(b"%PDF"), "Generated file is not a valid PDF header"
    print(f"PDF successfully generated: {len(pdf_bytes)} bytes")
    
    print("\n==================================================")
    print("ALL MODULE 3 TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    test_integration()
