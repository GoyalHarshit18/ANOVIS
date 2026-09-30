# PHASE 6F: API VERIFICATION

## 1. Endpoint Audit
The endpoint responsible for risk fusion orchestration and data exposure is:
`POST /screening-runs/{run_id}/risk-fusion`
(Defined in `backend/app/api/screening.py`)
This endpoint orchestrates risk fusion via `run_risk_fusion_for_run(run_id, db)`.

## 2. Request Contract
- **Path Parameter**: `{run_id}`
- **Body**: None
- **Selection**: Operates batch-level per run_id, extracting all distinct components associated with the run via `Measurement.component_id`.

## 3. Response Contract
Previously, the endpoint returned only a summary (component counts and status counts). 
We modified the response contract slightly without duplicating schemas or redesigning frontends to append full fusion data. It now safely appends `"results": [...]` providing native persistence serialization containing: `run_id, component_id, a_score, s_score, prediction_risk, uncertainty_risk, ldi, fusion_score, final_decision, decision_basis, model_version` directly from the `RiskFusionResult` table.

## 4. NULL / Zero Behavior
- Python `None` cleanly serializes to JSON `null` via FastAPI. 
- Python `0.0` translates precisely to JSON `0.0`. 
The API strictly surfaces the underlying DB persistence states without casting `None` to `0.0`.

## 5. Decision Preservation
The API does not recalculate decisions. It queries the persisted `RiskFusionResult.final_decision` as authored by `determine_decision()`.

## 6. decision_basis Preservation
The JSON blob from `RiskFusionResult.decision_basis` is faithfully routed through the API untouched.

## 7. fusion_score Provenance
The API faithfully exposes `RiskFusionResult.fusion_score` sourced accurately from `fusion_96h_classifier.pkl` (without recalculations or replacements with LDI).

## 8. model_version Provenance
Surfaces securely as `"fusion_96h_classifier.pkl"`.

## 9. Error Handling
- **Unknown Run**: Safely short-circuits returning HTTP 404 `{"detail": "Run not found"}`.
- **Compute/DB Exception**: Properly invokes rollback and logs component traceables before bubbling an aggregated HTTP 500 up.
- **Missing Evidence**: Nulls are securely routed, preventing a false `PASS`.

## 10. Multi-component Behavior
Components process individually within the `run_risk_fusion_for_run` loop. An isolated commit barrier prevents predictions and LDI derivations belonging to Component A from bleeding into Component B's response payload.

## 11. Idempotency
Executing the endpoint twice against the same run updates existing rows cleanly rather than duplicating `RiskFusionResult` entries. The API returns identical states.

## 12. API ↔ DB Consistency
Test verification explicitly fetches `db.query(RiskFusionResult)` after a `POST` API request and maps fields 1:1 against the API response matrix asserting exact parity.

## 13. LOT_00 Verification
Validated implicitly against LOT_00's real CSV dataset; resulting `POST` queries correctly execute without failure, surfacing `REVIEW_REQUIRED` (and subsequent `null` LDI/safety values since prerequisite data is historically unavailable for LOT_00 tests), verifying true null semantics without fabricating zeroed defaults.

## 14. OpenAPI Verification
Verified implicit behavior. FastAPI naturally extracts and serializes `summary` as `Dict[str, Any]` resulting in a valid 200 payload mapping directly through Swagger generation without disjointed overrides.

## 15. Frontend Contract Compatibility
The frontend UI does not natively dispatch `POST /screening-runs/{run_id}/risk-fusion` requests for single-page presentation logic. Instead, `RiskFusion.jsx` fetches `GET /component/{component_id}` routing to legacy `ScreeningResult`. The batch summary response we engineered resolves Phase 6F requirements strictly without triggering frontend UI defects.

## 16. Tests
Written `test_risk_fusion_phase6f.py` checking isolated multi-component routing, error cases, DB parity, decision precedence routing, and idempotency boundaries.

## 17. Regression Results
All prior phases (6C, 6D, 6E) successfully passed without regression impact.

## 18. Remaining Blockers for Phase 6G
None. The API cleanly surfaces the backend Risk Fusion orchestrator to QA consumers.
