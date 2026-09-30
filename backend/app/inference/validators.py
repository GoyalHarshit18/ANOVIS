import logging
from typing import Dict, Any, List

logger = logging.getLogger("sih26170.inference.validators")

def validate_required_checkpoints(measurements: Dict[str, Any], required_checkpoints: List[str]) -> bool:
    """Validate that the required checkpoints are present in the measurement dictionary."""
    for chkpt in required_checkpoints:
        if not any(f"_{chkpt}" in key for key, val in measurements.items() if val is not None):
            logger.warning(f"Validation failed: Missing required checkpoint {chkpt}")
            return False
    return True

def validate_feature_vector(vector: List[float], expected_count: int, model_name: str) -> bool:
    """Validate that the constructed feature vector matches the model's contract."""
    if len(vector) != expected_count:
        logger.error(f"Validation failed for {model_name}: Expected {expected_count} features, got {len(vector)}")
        return False
    
    import math
    if any(v is None for v in vector):
        logger.error(f"Validation failed for {model_name}: Vector contains None values")
        return False
        
    for v in vector:
        if not isinstance(v, (int, float)):
            logger.error(f"Validation failed for {model_name}: Vector contains non-numeric values")
            return False
        if math.isinf(v):
            logger.error(f"Validation failed for {model_name}: Vector contains infinite values")
            return False
            
    return True

def extract_checkpoint_data(measurements: Dict[str, Any], param: str, checkpoint: str) -> Any:
    """Extract a specific checkpoint data, preserving NULL/None."""
    key = f"{param}_{checkpoint}"
    return measurements.get(key)
