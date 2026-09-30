"""
Engineering Limit & Measurement Trend Analysis Service.
Compares component measurements against configured engineering limits and computes stage-over-stage trends.
"""
import logging
from typing import Any, Dict, List, Optional
from app.ml.model_registry import registry

logger = logging.getLogger("sih26170.limit_analysis")

PARAMS = ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]
STAGES = ["0h", "24h", "96h"]


def analyze_engineering_limits(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates observed sensor measurements against static/reference engineering limits.
    Returns structured limit comparisons, violations, and percentage of limit used.
    """
    ref_limits = registry.get("reference_limits") or {}
    
    # Fallback standard limits if reference_limits dict is missing specific keys
    default_limits = {
        "Iddq_uA": {"lower": 0.0, "upper": 12.0, "unit": "µA"},
        "Leakage_nA": {"lower": 0.0, "upper": 25.0, "unit": "nA"},
        "PropDelay_ns": {"lower": 0.5, "upper": 3.0, "unit": "ns"},
    }

    assessments = []
    violations = []
    
    for stage in STAGES:
        for param in PARAMS:
            key = f"{param}_{stage}"
            value = measurements.get(key)
            if value is None:
                continue
                
            try:
                val_float = float(value)
            except (ValueError, TypeError):
                continue

            ref = ref_limits.get(key)
            if ref and "lower" in ref and "upper" in ref:
                lower = float(ref["lower"])
                upper = float(ref["upper"])
                median = float(ref.get("median", (lower + upper) / 2))
            else:
                fallback = default_limits.get(param, {"lower": 0.0, "upper": 100.0})
                lower = fallback["lower"]
                upper = fallback["upper"]
                median = (lower + upper) / 2.0

            is_violation = (val_float < lower) or (val_float > upper)
            
            # Headroom / percentage of limit
            headroom_pct = round(((val_float - lower) / (upper - lower)) * 100, 1) if (upper > lower) else 0.0
            
            status = "EXCEEDED" if is_violation else "WITHIN_LIMIT"
            
            item = {
                "parameter": param,
                "stage": stage,
                "key": key,
                "value": round(val_float, 4),
                "lower_limit": lower,
                "upper_limit": upper,
                "median": median,
                "headroom_pct": headroom_pct,
                "status": status
            }
            assessments.append(item)
            
            if is_violation:
                violations.append({
                    "key": key,
                    "parameter": param,
                    "stage": stage,
                    "value": round(val_float, 4),
                    "limit_type": "HIGH" if val_float > upper else "LOW",
                    "limit_value": upper if val_float > upper else lower,
                })

    has_violations = len(violations) > 0
    return {
        "status": "VIOLATIONS_DETECTED" if has_violations else "ALL_WITHIN_LIMITS",
        "has_violations": has_violations,
        "violations": violations,
        "assessments": assessments
    }


def analyze_measurement_trends(measurements: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Computes measurement deltas and percentage changes between 0h->24h and 24h->96h.
    """
    trends = []
    
    for param in PARAMS:
        v0 = measurements.get(f"{param}_0h")
        v24 = measurements.get(f"{param}_24h")
        v96 = measurements.get(f"{param}_96h")
        
        def to_f(v):
            if v is None: return None
            try: return float(v)
            except: return None
            
        f0, f24, f96 = to_f(v0), to_f(v24), to_f(v96)
        
        delta_0_24 = round(f24 - f0, 4) if (f0 is not None and f24 is not None) else None
        pct_0_24 = round(((f24 - f0) / abs(f0)) * 100, 2) if (f0 is not None and f24 is not None and f0 != 0) else None
        
        delta_24_96 = round(f96 - f24, 4) if (f24 is not None and f96 is not None) else None
        pct_24_96 = round(((f96 - f24) / abs(f24)) * 100, 2) if (f24 is not None and f96 is not None and f24 != 0) else None
        
        delta_0_96 = round(f96 - f0, 4) if (f0 is not None and f96 is not None) else None
        pct_0_96 = round(((f96 - f0) / abs(f0)) * 100, 2) if (f0 is not None and f96 is not None and f0 != 0) else None

        trends.append({
            "parameter": param,
            "val_0h": f0,
            "val_24h": f24,
            "val_96h": f96,
            "delta_0_24h": delta_0_24,
            "pct_change_0_24h": pct_0_24,
            "delta_24_96h": delta_24_96,
            "pct_change_24_96h": pct_24_96,
            "delta_0_96h": delta_0_96,
            "pct_change_0_96h": pct_0_96,
        })
        
    return trends
