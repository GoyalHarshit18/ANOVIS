import csv
import io
import datetime
import uuid
import math
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import hashlib
import logging

from app.db.models import Lot, Component, Measurement, ScreeningRun

logger = logging.getLogger("sih26170.ingestion")

REQUIRED_HEADERS = {"component_id", "lot_id"}
CHECKPOINTS = [0, 24, 96, 168]

def normalize_header(header: str) -> str:
    h = header.strip().lower()
    if h.startswith("propdelay_ns_") or h.startswith("prop_delay_ns_") or h.startswith("propdelay_"):
        suffix = h.split("_")[-1]
        return f"prop_delay_ns_{suffix}"
    return h

def is_valid_float(value: str) -> bool:
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return False
        return True
    except ValueError:
        return False

def parse_float(value: str) -> float:
    return float(value)

def process_csv_upload(file_content: bytes, filename: str, db: Session) -> Dict[str, Any]:
    logger.info(f"Upload received: {filename}")
    if not file_content:
        return {"error": "CSV_VALIDATION_FAILED", "message": "File is empty", "status_code": 400}
    
    try:
        text = file_content.decode("utf-8")
    except UnicodeDecodeError:
        return {"error": "CSV_VALIDATION_FAILED", "message": "File is not utf-8 encoded", "status_code": 400}

    logger.info("Validation started")
    reader = csv.reader(io.StringIO(text))
    try:
        headers_raw = next(reader)
    except StopIteration:
        return {"error": "CSV_VALIDATION_FAILED", "message": "CSV has no headers", "status_code": 400}

    headers = [normalize_header(h) for h in headers_raw]
    
    missing_required = REQUIRED_HEADERS - set(headers)
    if missing_required:
        return {
            "error": "CSV_VALIDATION_FAILED", 
            "message": f"Missing required columns: {', '.join(missing_required)}", 
            "status_code": 422
        }

    measurement_cols = []
    for h in headers:
        for chk in CHECKPOINTS:
            if h.endswith(f"_{chk}h"):
                measurement_cols.append(h)
                break
    
    unknown_cols = set(headers) - REQUIRED_HEADERS - set(measurement_cols) - {"ground_truth", "device_type", "station_id", "temperature", "voltage"}
    warnings = []
    if unknown_cols:
        warnings.append({"unknown_columns": list(unknown_cols)})
        logger.info(f"Validation warnings: unknown columns {list(unknown_cols)}")

    valid_rows = 0
    invalid_rows = 0
    errors = []
    rows_data = []
    
    lot_ids = set()
    component_ids = set()
    duplicate_components = []

    for idx, row in enumerate(reader, start=2):
        if not row or not any(row):
            continue
            
        if len(row) != len(headers):
            errors.append({"row": idx, "message": "Row length does not match header length"})
            invalid_rows += 1
            continue

        row_dict = {h: v.strip() for h, v in zip(headers, row)}
        
        comp_id = row_dict.get("component_id")
        lot_id = row_dict.get("lot_id")
        
        if not comp_id:
            errors.append({"row": idx, "message": "component_id is empty"})
            invalid_rows += 1
            continue
        if not lot_id:
            errors.append({"row": idx, "message": "lot_id is empty"})
            invalid_rows += 1
            continue

        if comp_id in component_ids:
            duplicate_components.append({"component_id": comp_id, "row": idx})
        component_ids.add(comp_id)
        lot_ids.add(lot_id)

        row_invalid = False
        for m_col in measurement_cols:
            val = row_dict.get(m_col)
            if val:
                if not is_valid_float(val):
                    errors.append({"row": idx, "message": f"Invalid numeric value '{val}' in column {m_col}"})
                    row_invalid = True
        
        if row_invalid:
            invalid_rows += 1
            continue
            
        valid_rows += 1
        rows_data.append(row_dict)

    logger.info("Validation completed")

    if duplicate_components:
        return {
            "error": "CSV_VALIDATION_FAILED", 
            "message": "Duplicate components found in upload",
            "details": duplicate_components,
            "status_code": 422
        }
        
    if len(lot_ids) > 1:
        return {
            "error": "MULTIPLE_LOTS_IN_SINGLE_UPLOAD", 
            "message": "A single uploaded CSV must represent one lot.",
            "details": {"lot_ids": list(lot_ids)},
            "status_code": 422
        }

    if errors:
        return {
            "error": "CSV_VALIDATION_FAILED",
            "message": "Validation errors encountered",
            "details": errors,
            "status_code": 422
        }

    if not rows_data:
        return {
            "error": "CSV_VALIDATION_FAILED", 
            "message": "No valid data rows found", 
            "status_code": 400
        }

    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    lot_id_str = list(lot_ids)[0]
    
    file_hash = hashlib.sha256(file_content).hexdigest()

    try:
        logger.info(f"Run created: {run_id}")
        run = ScreeningRun(
            run_id=run_id,
            lot_id=lot_id_str,
            source_filename=filename,
            source_file_hash=file_hash,
            status="INGESTING",
            started_at=datetime.datetime.utcnow(),
            total_rows=valid_rows + invalid_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            component_count=len(component_ids),
            warning_count=len(warnings),
            error_count=len(errors)
        )
        db.add(run)
        
        lot = db.query(Lot).filter(Lot.lot_id == lot_id_str).first()
        if not lot:
            lot = Lot(lot_id=lot_id_str)
            db.add(lot)
            logger.info(f"Lot identified/created: {lot_id_str}")
        else:
            logger.info(f"Lot identified/found: {lot_id_str}")
            
        db.flush()
            
        existing_comps = db.query(Component).filter(Component.lot_id == lot_id_str).all()
        existing_comp_map = {c.component_id: c for c in existing_comps}
        
        checkpoint_summary = {
            "0h": {"available": False, "count": 0},
            "24h": {"available": False, "count": 0},
            "96h": {"available": False, "count": 0},
            "168h": {"available": False, "count": 0},
        }

        measurements_count = 0
        for row_dict in rows_data:
            comp_id = row_dict["component_id"]
            if comp_id not in existing_comp_map:
                comp = Component(
                    component_id=comp_id,
                    lot_id=lot_id_str,
                    device_type=row_dict.get("device_type"),
                    station_id=row_dict.get("station_id")
                )
                db.add(comp)
                existing_comp_map[comp_id] = comp
            else:
                comp = existing_comp_map[comp_id]
                if row_dict.get("device_type"):
                    comp.device_type = row_dict.get("device_type")
                if row_dict.get("station_id"):
                    comp.station_id = row_dict.get("station_id")

            for chk in CHECKPOINTS:
                chk_str = f"{chk}h"
                
                iddq_key = f"iddq_ua_{chk_str}"
                leak_key = f"leakage_na_{chk_str}"
                prop_key = f"prop_delay_ns_{chk_str}"
                
                v_iddq = row_dict.get(iddq_key)
                v_leak = row_dict.get(leak_key)
                v_prop = row_dict.get(prop_key)
                
                if v_iddq or v_leak or v_prop:
                    meas = Measurement(
                        run_id=run_id,
                        component_id=comp_id,
                        checkpoint_hour=chk,
                        temperature=row_dict.get("temperature"),
                        voltage=row_dict.get("voltage"),
                        iddq_ua=parse_float(v_iddq) if v_iddq else None,
                        leakage_na=parse_float(v_leak) if v_leak else None,
                        prop_delay_ns=parse_float(v_prop) if v_prop else None,
                    )
                    db.add(meas)
                    checkpoint_summary[chk_str]["count"] += 1
                    measurements_count += 1

        db.commit()
        
        run.status = "READY_FOR_INFERENCE"
        run.completed_at = datetime.datetime.utcnow()
        db.commit()
        
        logger.info(f"Component count: {len(component_ids)}")
        logger.info(f"Measurement count: {measurements_count}")
        logger.info("Ingestion completed")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ingestion failed: {str(e)}")
        logger.info("Rollback performed")
        return {
            "error": "INGESTION_FAILED",
            "message": str(e),
            "status_code": 500
        }

    for chk in ["0h", "24h", "96h", "168h"]:
        if checkpoint_summary[chk]["count"] > 0:
            if checkpoint_summary[chk]["count"] == valid_rows:
                checkpoint_summary[chk]["available"] = True
            else:
                checkpoint_summary[chk]["available"] = "partially_available"
                
    data_readiness = {}
    if checkpoint_summary["0h"]["available"] is True and checkpoint_summary["24h"]["available"] is True:
        data_readiness["b0"] = "READY"
        data_readiness["b1"] = "READY"
        data_readiness["b2_early"] = "READY"
        data_readiness["component_24h"] = "READY"
        
        if checkpoint_summary["96h"]["available"] is True:
            data_readiness["component_96h"] = "READY"
            data_readiness["b2_96h"] = "READY"
        elif checkpoint_summary["96h"]["available"] == "partially_available":
            data_readiness["component_96h"] = "PARTIAL"
            data_readiness["b2_96h"] = "PARTIAL"
        else:
            data_readiness["component_96h"] = "UNAVAILABLE"
            data_readiness["b2_96h"] = "UNAVAILABLE"
    else:
        data_readiness["b0"] = "UNAVAILABLE"
        data_readiness["b1"] = "UNAVAILABLE"
        data_readiness["b2_early"] = "UNAVAILABLE"
        data_readiness["component_24h"] = "UNAVAILABLE"
        data_readiness["component_96h"] = "UNAVAILABLE"
        data_readiness["b2_96h"] = "UNAVAILABLE"

    return {
        "run_id": run_id,
        "status": "READY_FOR_INFERENCE",
        "lot_id": lot_id_str,
        "filename": filename,
        "total_rows": valid_rows + invalid_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "component_count": len(component_ids),
        "warnings": warnings,
        "errors": errors,
        "checkpoint_summary": checkpoint_summary,
        "data_readiness": data_readiness
    }
