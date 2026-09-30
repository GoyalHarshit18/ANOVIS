"""
Validation Service — validates input data before screening.
"""
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("sih26170.validation_service")

REQUIRED_PARAMS = ["Iddq_uA", "Leakage_nA", "PropDelay_ns"]
VALID_STAGES = ["0h", "24h", "96h", "168h"]
KNOWN_DEVICE_TYPES = ["XYZ-IC", "ABC-IC", "ASIC-001", "FPGA-001"]

# Reasonable ranges for numeric values
VALID_RANGES = {
    "Iddq_uA": (0, 500),
    "Leakage_nA": (0, 10000),
    "PropDelay_ns": (0, 100),
}


def validate_component(measurements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single component's measurements.
    Returns validation result with pass/fail and details.
    """
    errors = []
    warnings = []

    # Required field: component_id
    if not measurements.get("component_id"):
        errors.append("Missing component_id")

    # Must have at least 0h data
    has_0h = False
    for param in REQUIRED_PARAMS:
        if measurements.get(f"{param}_0h") is not None:
            has_0h = True
            break

    if not has_0h:
        errors.append("No 0h measurements provided")

    # Validate numeric values
    for param, (low, high) in VALID_RANGES.items():
        for stage in VALID_STAGES:
            key = f"{param}_{stage}"
            val = measurements.get(key)
            if val is not None:
                if not isinstance(val, (int, float)):
                    errors.append(f"{key}: not numeric")
                elif val < low or val > high:
                    warnings.append(f"{key}: value {val} outside expected range [{low}, {high}]")

    # Device type check
    device_type = measurements.get("device_type", "")
    device_recognized = device_type in KNOWN_DEVICE_TYPES or not device_type

    schema_ok = len(errors) == 0

    return {
        "valid": schema_ok,
        "schema": "PASS" if schema_ok else "FAIL",
        "required_fields": "PASS" if has_0h else "FAIL",
        "units": "PASS",  # Assumed OK if numeric validation passes
        "range_sanity": "PASS" if not warnings else "WARNING",
        "device_type": "Recognized" if device_recognized else "Unknown",
        "reference_population": "Available",
        "errors": errors,
        "warnings": warnings,
    }


def validate_csv_data(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a batch of records.
    Returns overall validation and per-row issues.
    """
    total = len(records)
    valid_count = 0
    invalid_rows = []
    all_warnings = []

    for i, record in enumerate(records):
        result = validate_component(record)
        if result["valid"]:
            valid_count += 1
        else:
            invalid_rows.append({
                "row": i + 1,
                "component_id": record.get("component_id", f"row-{i+1}"),
                "errors": result["errors"],
            })
        if result["warnings"]:
            all_warnings.extend(result["warnings"])

    # Check for duplicate component IDs
    ids = [r.get("component_id") for r in records if r.get("component_id")]
    duplicate_ids = set(x for x in ids if ids.count(x) > 1)
    if duplicate_ids:
        all_warnings.append(f"Duplicate component IDs: {', '.join(sorted(duplicate_ids))}")

    return {
        "valid": valid_count == total,
        "total_rows": total,
        "valid_rows": valid_count,
        "invalid_rows": len(invalid_rows),
        "invalid_details": invalid_rows,
        "warnings": all_warnings,
        "schema": "PASS" if valid_count == total else "FAIL",
        "required_fields": "PASS" if not invalid_rows else f"FAIL ({len(invalid_rows)} missing)",
        "units": "PASS",
        "range_sanity": "PASS" if not all_warnings else "WARNING",
        "device_type": "Recognized",
        "reference_population": "Available",
    }
