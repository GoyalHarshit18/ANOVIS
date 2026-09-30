"""
Comprehensive Unit & Integration Test Suite for Module 3 (Explainability & Gemini QA Reports).
"""
import pytest
import numpy as np
import os
import sys

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ml.model_registry import registry
from app.services.explainability_service import (
    explain_component_96h,
    get_global_shap_importance
)
from app.services.gemini_service import (
    generate_gemini_qa_report,
    _generate_fallback_report
)
from app.services.pdf_service import generate_qa_report_pdf
from app.services.limit_analysis_service import (
    analyze_engineering_limits,
    analyze_measurement_trends
)

# Test Fixture sample measurements
SAMPLE_MEASUREMENTS = {
    "component_id": "TEST-COMP-96H-001",
    "lot_id": "LOT-2026-TEST",
    "device_type": "XYZ-IC",
    "station": "ST-01",
    "Iddq_uA_0h": 1.15,
    "Iddq_uA_24h": 1.45,
    "Iddq_uA_96h": 4.85, # Elevated
    "Leakage_nA_0h": 4.20,
    "Leakage_nA_24h": 5.80,
    "Leakage_nA_96h": 28.50, # Exceeds limit
    "PropDelay_ns_0h": 1.05,
    "PropDelay_ns_24h": 1.10,
    "PropDelay_ns_96h": 1.35,
    "Temperature_C_0h": 125.0,
    "Voltage_0h": 3.3,
    "Temperature_C_24h": 125.0,
    "Voltage_24h": 3.3,
    "Temperature_C_96h": 125.0,
    "Voltage_96h": 3.3,
}


@pytest.fixture(scope="module", autouse=True)
def setup_models():
    """Load model registry once for module test run."""
    registry.load_all()


def test_limit_analysis():
    """Test limit detection and trends calculation."""
    limits = analyze_engineering_limits(SAMPLE_MEASUREMENTS)
    assert "status" in limits
    assert limits["has_violations"] is True
    assert len(limits["violations"]) >= 1

    trends = analyze_measurement_trends(SAMPLE_MEASUREMENTS)
    assert len(trends) == 3
    for t in trends:
        assert "parameter" in t
        assert "delta_24_96h" in t


def test_individual_shap_explanation():
    """Test 96h CatBoost individual SHAP calculation & reconstruction."""
    explanation = explain_component_96h(SAMPLE_MEASUREMENTS)
    
    assert explanation["component_id"] == "TEST-COMP-96H-001"
    assert "anomaly_probability" in explanation
    assert "base_value" in explanation
    assert "reconstructed_value" in explanation
    
    # Mathematical Reconstruction Verification: base + sum(shap) ≈ prob
    diff = explanation["reconstruction_diff"]
    assert diff < 1e-4, f"SHAP reconstruction difference too high: {diff}"

    assert len(explanation["top_positive_contributors"]) > 0
    assert len(explanation["top_negative_contributors"]) >= 0
    assert explanation["output_unit"] == "Probability (0.0 to 1.0)"


def test_global_shap_importance():
    """Test global SHAP feature importance summary."""
    global_shap = get_global_shap_importance([SAMPLE_MEASUREMENTS])
    
    assert "global_importance" in global_shap
    assert len(global_shap["global_importance"]) > 0
    top_feature = global_shap["global_importance"][0]
    assert "feature" in top_feature
    assert "mean_abs_shap" in top_feature


def test_gemini_qa_report_generation():
    """Test Gemini QA report generation and fallback schema validation."""
    explanation = explain_component_96h(SAMPLE_MEASUREMENTS)
    report = generate_gemini_qa_report(explanation)
    
    required_keys = [
        "executive_summary",
        "classification_explanation",
        "key_contributing_factors",
        "measurement_trends",
        "engineering_limit_assessment",
        "recommended_inspection_steps",
        "limitations"
    ]

    for key in required_keys:
        assert key in report, f"Missing key in Gemini QA report: {key}"
        assert report[key] is not None

    assert report["source"].startswith("GOOGLE_GEMINI_AI") or report["source"] == "DETERMINISTIC_FALLBACK"


def test_pdf_generation():
    """Test printable PDF report generation."""
    explanation = explain_component_96h(SAMPLE_MEASUREMENTS)
    gemini_report = generate_gemini_qa_report(explanation)
    
    pdf_bytes = generate_qa_report_pdf(explanation, gemini_report)
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000 # Valid PDF file size
    assert pdf_bytes.startswith(b"%PDF") # Valid PDF signature


def test_non_regression_module1_and_module2():
    """Verify Module 1 and Module 2 predictions are intact."""
    from app.services.screening_service import screen_component
    from app.ml.prediction_engine import predict_168h

    # Module 1 screen
    screen_res = screen_component(SAMPLE_MEASUREMENTS)
    assert "decision" in screen_res
    assert "a_score" in screen_res

    # Module 2 predict 168h
    pred_res = predict_168h(SAMPLE_MEASUREMENTS)
    assert "predicted_168h" in pred_res
    assert pred_res["available"] is True


if __name__ == "__main__":
    pytest.main(["-v", __file__])
