import pytest
import math
import numpy as np
from app.inference.validators import validate_feature_vector
from app.inference.feature_builder import safe_float, compute_delta, compute_slope, compute_relative

def test_validate_feature_vector_invalid():
    # 1. Wrong feature count
    assert not validate_feature_vector([1.0, 2.0], 3, "Test")
    
    # 2. None values
    assert not validate_feature_vector([1.0, None, 3.0], 3, "Test")
    
    # 3. Non-numeric
    assert not validate_feature_vector([1.0, "str", 3.0], 3, "Test")
    
    # 4. Infinite
    assert not validate_feature_vector([1.0, float('inf'), 3.0], 3, "Test")
    assert not validate_feature_vector([1.0, float('-inf'), 3.0], 3, "Test")

def test_validate_feature_vector_valid_nan():
    # NaN is allowed and should be passed to the model
    assert validate_feature_vector([1.0, float('nan'), 3.0], 3, "Test")

def test_safe_float_returns_nan():
    assert math.isnan(safe_float(None))
    assert math.isnan(safe_float(""))
    assert safe_float(5.5) == 5.5

def test_helpers_handle_nan():
    assert math.isnan(compute_delta(10, None))
    assert math.isnan(compute_slope(10, None, 24))
    assert math.isnan(compute_relative(10, None))
    
    assert compute_delta(10, 5) == -5
    assert compute_slope(10, 5, 24) == -5 / 24
    assert compute_relative(10, 5) == -5 / 10
