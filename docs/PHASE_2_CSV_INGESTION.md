# PHASE 2 — CSV INGESTION

## 1. Upload Endpoint
**Endpoint**: `POST /upload`  
**Purpose**: Strict CSV ingestion and validation for complete lots.

## 2. Request Format
- **Content-Type**: `multipart/form-data`
- **Parameter**: `file` (the CSV file to upload)

## 3. CSV Schema
The uploaded CSV must contain complete lot data.
- **Required Columns**: `component_id`, `lot_id`
- **Measurement Columns**: Measurements follow the format `{parameter}_{checkpoint}h`. Valid parameters include `iddq_ua`, `leakage_na`, and `prop_delay_ns`. Valid checkpoints are `0`, `24`, `96`, `168`. (e.g. `iddq_ua_96h`).
- **Optional Context**: `temperature`, `voltage`, `device_type`, `station_id`.
- **Evaluation Metadata**: `ground_truth` is safely ignored for production inference.
- **Unknown Columns**: Reported as warnings.

## 4. Validation Rules
- **File Level**: Must be non-empty, utf-8 encoded, valid CSV structure.
- **Header Level**: Must include `component_id` and `lot_id`.
- **Row Level**: Component and Lot IDs must not be empty. Measurement values must be parseable finite floats.
- **Component ID**: Must be unique within the upload. Duplicate IDs yield an error.
- **Lot ID**: A single upload must only contain one unique `lot_id`. Multiple lot IDs yield an error.

## 5. Missing-Data Policy
**Missing is absent (`NULL`).** 
Empty or omitted fields in the CSV are skipped. They are **never** imputed as `0`, interpolated from previous/next checkpoints, or filled with medians. If a model strictly requires a missing checkpoint, that model evaluates to `UNAVAILABLE`.

## 6. Checkpoint Mapping
Incoming flattened CSV rows (e.g., `iddq_ua_0h`, `iddq_ua_24h`) are mapped into **independent rows per checkpoint** in the `measurements` table.
- A component missing 96h data will have `Measurement` records for 0h and 24h, but **no** 96h record.

## 7. Run Lifecycle
Upon successful upload:
1. A unique `run_id` is generated.
2. Status is initially set to `INGESTING`.
3. Valid measurements are parsed and persisted.
4. Status is updated to `READY_FOR_INFERENCE`.

## 8. Database Persistence Behavior
- **Run**: Created for every successful upload, holding metadata like `source_filename`, row counts, and timestamps.
- **Lot**: Found by `lot_id` or newly created.
- **Component**: Found by `component_id` (within the `lot_id`) or created. Historical components are preserved.
- **Measurements**: Measurements are bound to `run_id`, `component_id`, and `checkpoint_hour`. Re-uploading a historical component creates new measurement records under the new `run_id` without overwriting historical run data.

## 9. Error Responses
Use appropriate HTTP Status codes:
- **400 Bad Request**: File is empty, not utf-8, missing headers.
- **422 Unprocessable Entity**: Missing required columns, multiple lots in upload, duplicate components, malformed numeric values.
- **500 Internal Server Error**: Fatal ingestion or persistence error.

## 10. Transaction Behavior
Ingestion is strictly transactional. Database operations occur within a single `Session`. If validation or persistence fails at any point, a complete `ROLLBACK` is performed to ensure no partially-ingested lot data remains.

## 11. Example Successful Response
```json
{
  "run_id": "RUN-ABC12345",
  "status": "READY_FOR_INFERENCE",
  "lot_id": "LOT-2026-091",
  "filename": "lot91.csv",
  "total_rows": 173,
  "valid_rows": 173,
  "invalid_rows": 0,
  "component_count": 173,
  "warnings": [],
  "errors": [],
  "checkpoint_summary": {
      "0h": {"available": true, "count": 173},
      "24h": {"available": true, "count": 173},
      "96h": {"available": "partially_available", "count": 172},
      "168h": {"available": false, "count": 0}
  },
  "data_readiness": {
      "b0": "READY",
      "b1": "READY",
      "b2_early": "READY",
      "component_24h": "READY",
      "component_96h": "PARTIAL",
      "b2_96h": "PARTIAL"
  }
}
```

## 12. Example Failed Response
```json
{
  "error": "CSV_VALIDATION_FAILED",
  "message": "Validation errors encountered",
  "details": [
    {"row": 15, "message": "Invalid numeric value 'abc' in column iddq_ua_24h"}
  ]
}
```

## 13. Test Coverage
Comprehensive tests are located at `backend/app/tests/test_csv_upload.py`.
- **TEST 1**: Valid complete lot upload
- **TEST 2**: Missing 96h data handling (verify `NULL` handling)
- **TEST 3**: Missing required column
- **TEST 4**: Multiple lots prevention
- **TEST 5**: Duplicate component prevention
- **TEST 6**: Malformed numeric value rejection
- **TEST 7**: Empty CSV handling
- **TEST 8**: Unknown columns warning
- **TEST 9**: Reupload same component (history preservation)
- **TEST 10**: Transaction rollback verification
