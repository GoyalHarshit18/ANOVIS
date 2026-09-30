import math
import numpy as np
import pytest
import os
import joblib
from app.inference.feature_builder import build_fusion_vector

def test_build_fusion_vector_correct_inputs():
    # 1. correct 3-feature vector
    # 2. exact feature order
    # 3. correct feature count
    # 4. valid numeric inputs
    vec = build_fusion_vector(0.9, 0.8, 0.7)
    assert vec is not None
    assert len(vec) == 3
    assert vec == [0.9, 0.8, 0.7]

def test_build_fusion_vector_malformed_inputs():
    # 5. malformed input rejection
    vec = build_fusion_vector("not_a_number", 0.5, 0.8)
    assert vec is None

def test_build_fusion_vector_none_handling():
    # 6. None handling
    # 7. no fallback-to-zero behavior
    vec = build_fusion_vector(None, 0.5, 0.8)
    assert vec is None
    
    vec2 = build_fusion_vector(0.5, None, 0.8)
    assert vec2 is None

def test_build_fusion_vector_nan_handling():
    vec = build_fusion_vector(math.nan, 0.5, 0.8)
    assert vec is None

def test_fusion_model_accepts_vector():
    # 8. existing fusion model accepts the generated vector
    model_path = os.path.join(os.path.dirname(__file__), '../../models/fusion_96h_classifier.pkl')
    if not os.path.exists(model_path):
        pytest.skip(f"Model not found at {model_path}")
        
    model = joblib.load(model_path)
    
    vec = build_fusion_vector(0.9, 0.8, 0.7)
    assert vec is not None
    
    X = np.array([vec])
    
    try:
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            assert probs is not None
        pred = model.predict(X)
        assert pred is not None
    except Exception as e:
        pytest.fail(f"Model rejected the vector: {e}")
