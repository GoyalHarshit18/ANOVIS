# PHASE 6: RISK FUSION ENGINE

## Overview
Phase 6 implements the production Risk Fusion Engine (`module_c` equivalent), replacing legacy/mock risk fusion logic with the canonical `fusion_96h_classifier.pkl` and `latent_specialist.pkl` models. This engine combines existing static engineering evidence from Module A with predictive capabilities from Module B and specialized classifiers.

## Objectives Met
1. **Model Integration**: Located and loaded `fusion_96h_classifier.pkl`, `component_96h_classifier.pkl`, and `latent_specialist.pkl`.
2. **Feature Contracts Maintained**:
   - `component_96h_classifier.pkl` correctly receives the `COMPONENT_96H_FEATURES` array (43 features) identical to `B2-96h`.
   - `latent_specialist.pkl` receives the exactly formulated `LATENT_SPECIALIST_FEATURES` array (21 features).
   - `fusion_96h_classifier.pkl` correctly receives `Supervised_Score`, `Component_96h_Score`, and `Late_Drift_Risk`.
3. **No Fallback / Hardcode**: Missing inputs cause `fusion_status = UNAVAILABLE`. LDI uses `None` instead of mocking values with `0.0`.
4. **Precedence Maintained**:
   - Static Failure -> REJECT/FAIL.
   - Test Integrity -> DISTURBANCE -> REPEAT_MEASUREMENT.
   - Elevated Risk -> REVIEW_REQUIRED / MONITOR.
5. **Persistence**: Fusion artifacts and decision are persisted to `RiskFusionResult` table, and the final decision propagates to `ScreeningResult(stage="FINAL")`. An `AuditEvent` is generated.
6. **E2E Validation**: The real `LOT_00` dataset ran correctly across all phases including Risk Fusion.

## Database Additions
- `RiskFusionResult`: Persists LDI, predictions, fusion score, decisions, and exact decision basis JSON.
- `AuditEvent`: Saves event tracking with warnings and final fusion status.

## Verification
- E2E dataset `data_set_2_LOT_00_lowercase.csv` executed successfully via `run_e2e.py` all the way through Module A -> Phase 4 -> Module B -> Phase 6.

Status: **PASS**
