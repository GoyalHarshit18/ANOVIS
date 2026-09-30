# SIH26170 — AI-Driven Anomaly Detection in Component Burn-In & Screening
# MASTER PLAN v3 (Final Hardened, Implementation-Ready)

---

# REVISION SUMMARY

### 1. What was wrong
The v1 architecture had seventeen categories of technical/scientific weakness, the most serious being:
- **Signal double-counting**: LDI re-summed peer residual and Early Temporal Anomaly, which were already folded into `A_SCORE`, silently inflating their weight.
- **Module B contract mismatch**: the "strict baseline" quietly included metadata (device type, temperature, voltage) that the SIH problem statement does not specify as inputs.
- **Self-referential statistics**: lot median/MAD were computed *including* the component being scored, biasing PAT against outliers it was supposed to detect.
- **Conflated deployment assumptions**: batch/current-lot screening and cold-start/new-lot screening were treated as one case.
- **Overclaimed independence, physical realism, and probability semantics**: "independent signals," "physically motivated curves," and prediction bounds described as probabilities without calibration.
- **Peer-normalization blind spot**: a miscalibrated test station could raise the whole peer group, hiding the very anomaly the peer engine exists to catch.
- **Predetermined winners**: model and architecture comparisons assumed conclusions ("Gradient Boosting is best," "enhanced beats baseline") before any experiment ran.
- **Unearned metrics**: 100% static recall, fabricated MAE ceilings, and an assumed escape-reduction percentage.

### 2. What was fixed
Each of the 17 mandatory corrections in the governing brief has been applied structurally, not cosmetically — the architecture, data contracts, and evaluation plan were redrawn so that violations are *impossible by construction* (e.g., B0 cannot see 96h/168h data because the feature-availability matrix enforces it at the code-interface level, not just by convention).

### 3. Why the correction matters
This is a **screening system feeding a QA decision** for burn-in/space-grade components. A statistically indefensible score, a leaky feature, or a normalization step that hides a test-station fault does not fail gracefully — it fails silently, exactly where the system is supposed to add value. Judges in a technical SIH round will probe precisely these seams.

### 4. What remains unchanged
- The overall philosophy: **Static → Statistical → Peer → Trajectory → Prediction → Safety Envelope → Fused Risk → Explainable QA Decision.**
- The defect taxonomy (healthy / gradual / accelerating / sudden / latent / sensor-glitch).
- The fail-safe principle: any system failure routes to `REVIEW_REQUIRED` / `DATA_UNAVAILABLE`, never to `PASS`.
- The three-tier research-traceability classification (DIRECT / STAT / ANALOGY / IMPL).
- The overall module names (Module A, Module B, Test-Integrity Layer, Risk Fusion, Explainability).

### 5. New architecture principles
1. **No signal appears twice** in any composite score.
2. **No feature crosses its availability boundary** (24h model never sees 96h/168h data).
3. **No statistic is computed on data that includes the point being judged** (leave-one-out).
4. **No score is called a probability unless it has been calibrated and validated as one.**
5. **No claim of independence, physical realism, or model superiority without empirical evidence.**
6. **Every anomaly source is separated by origin**: device-level, lot-level, station-level.
7. **System failure is always a hard stop, never a silent pass.**

---

# ONE-PAGE MASTER PLAN

```
RAW MEASUREMENT (0h, 24h, ... 168h) + METADATA
        ↓
DATA VALIDATION  (schema, units, range) ── fail → REVIEW_REQUIRED
        ↓
STATIC SCREENING  (datasheet limits)     ── deterministic pass/fail, NOT claimed as 100% recall
        ↓
VERSIONED FEATURE ENGINE  (enforces the Feature-Availability Matrix per inference stage)
        ↓
┌───────────────────────────── MODULE A (current-state anomaly) ─────────────────────────────┐
│  PAT (leave-one-out)   Peer Residual (within & cross-station)   Temporal Anomaly (≤24h feats) │
│                              Isolation Forest (multivariate)                                   │
└───────────────────────────────────────── A_SCORE ──────────────────────────────────────────────┘
        ↓                                                              ↓
   MODULE B (B0/B1/B2 → 168h prediction)                     TEST-INTEGRITY LAYER (rule engine v1)
        ↓                                                              ↓
   Safety Envelope → S_SCORE (score, not probability, unless calibrated)   Measurement-Risk Evidence
        └───────────────────────────────┬───────────────────────────────┘
                                         ↓
                                   RISK FUSION
                     device_risk · future_risk · test_integrity_risk
                                         ↓
                         PASS / MONITOR / REVIEW / REJECT / REPEAT
                                         ↓
                              EXPLAINABILITY (SHAP = correlational, not causal)
                                         ↓
                                     QA REPORT
```

**Headline demo metrics (measured, not assumed):** Escape Reduction %, Early-Detection Lead Time, B0/B1/B2 MAE side-by-side, calibration reliability diagram.

---

# PART I — RESEARCH TRACEABILITY (PRESERVED CLASSIFICATION)

| Technique | Classification | Basis | What it is NOT claimed to be |
|---|---|---|---|
| Static datasheet-limit screening | DIRECT | Standard semiconductor burn-in/QA practice | Not claimed to have 100% recall on latent defects |
| Parametric burn-in trend prediction (0h/24h → later reading) | DIRECT | Established burn-in prediction literature | Not claimed to require metadata — that is B1/B2, not the strict contract |
| IDDQ / parametric peer (neighbor) residual comparison | DIRECT | Peer/neighbor residual methods in IC test literature | Not claimed to be immune to correlated (station-level) shifts |
| GPR-based burn-in degradation modelling | DIRECT | Gaussian-process burn-in modelling literature | Predictive interval, not automatically a "probability of failure" unless calibrated |
| Modified Z-score / MAD-based outlier detection | STAT | Robust statistics | Not claimed to be leakage-safe unless computed leave-one-out |
| Isolation Forest for multivariate anomaly detection | STAT | General anomaly-detection literature (incl. maritime IF+SHAP precedent) | Not claimed to be "proven best" — a candidate among LOF / One-Class SVM / Robust Covariance |
| ShaTS-style grouped/segmented feature attribution | ANALOGY | Time-series SHAP grouping literature | Adapted terminology; not a validated semiconductor-specific method |
| Battery early-life degradation prediction principle | ANALOGY | Battery State-of-Health early-prediction literature | Physics does **not** transfer directly to semiconductors — used only as a structural analogy (early signal → late outcome) |
| Maritime sensor Isolation-Forest + SHAP anomaly pipeline | ANALOGY | Maritime predictive-maintenance literature | Cited for pipeline pattern only, not as evidence of semiconductor reliability |
| Integrated multi-layer screening hierarchy (Static→A→B→Fusion) | IMPL (our contribution) | — | Not an established industry standard |
| Synthetic multi-trajectory benchmark generator | IMPL (our contribution) | — | Not a semiconductor device simulator; not representative of real ISRO hardware |
| LDI / Risk Fusion formulation | IMPL (our contribution) | — | Not an established industry standard; not a probability unless calibrated |
| Test-Integrity separation (device vs. station vs. lot) | IMPL (our contribution) | — | Rule-based v1, not a trained classifier |
| QA evidence-trail / explainability structure | IMPL (our contribution) | — | SHAP attributions are correlational signal importance, not proof of physical root cause |

AEC-Q001 (if referenced anywhere in supporting material) is an **automotive** reliability standard and is explicitly **not** described as an ISRO/space standard — it is used only as an illustrative external-tolerance example where applicable.

---

# PART II — SYSTEM ARCHITECTURE (CORRECTED, NO DUPLICATED SIGNALS)

```
RAW DATA
   ↓
VALIDATION
   ↓
STATIC SCREENING
   ↓
VERSIONED FEATURE ENGINE
   ↓
MODULE A
   ├── PAT (leave-one-out Modified Z)
   ├── Peer Residual (within-station + cross-station)
   ├── Early Temporal Anomaly (0–24h)
   └── Isolation Forest
   ↓
A_SCORE
   │
   ├────────────────────────────┐
   ↓                            ↓
MODULE B                  TEST INTEGRITY LAYER
   ↓                            ↓
168h prediction (B0/B1/B2)   measurement-risk evidence
   ↓
Safety Envelope
   ↓
S_SCORE
   │
   └─────────────┬──────────────┘
                 ↓
            RISK FUSION
                 ↓
   PASS / MONITOR / REVIEW / REJECT / REPEAT
                 ↓
            EXPLAINABILITY
                 ↓
              QA REPORT
```

**Invariant enforced by design:** `A_SCORE` is the *only* place peer residual and Early Temporal Anomaly are summed. Everything downstream (`LDI`, Risk Fusion) consumes `A_SCORE` as a single opaque number, never its sub-components again.

---

# PART III — CORRECTION #1: RISK FUSION AND LDI (NO DOUBLE COUNTING)

### Why v1 was wrong
`A_score = PAT + peer_residual + temporal_anomaly + IF`, then
`LDI = w1·A_score + w2·peer_residual + w3·temporal_anomaly + w4·acceleration + w5·S_score`
re-injects peer residual and Early Temporal Anomaly a second time, silently doubling their effective weight relative to PAT and IF.

### Fix
```
LDI = w1·A_SCORE + w2·S_SCORE + w3·Prediction_Risk + w4·Uncertainty_Risk
```
- `A_SCORE` — current-state abnormality (Module A, already a fused composite).
- `S_SCORE` — statistical unusualness of the predicted drift relative to the healthy drift distribution; it answers "how unusual is this projected drift?"
- `Prediction_Risk` — distance of the predicted 168h value to the engineering/static limit; it answers "how close is the projected value to the allowed engineering boundary?"
- `Uncertainty_Risk` — width of the prediction interval / model confidence; a wide interval increases risk of an unseen violation even if the point prediction looks fine.

Each right-hand term is a **terminal, already-fused score** — none of PAT, peer residual, Early Temporal Anomaly, or Isolation Forest appear individually past `A_SCORE`. Weights `w1..w4` are tuned on a held-out validation split (Phase 9), not hand-picked.

If simpler proves better empirically (e.g., `A_SCORE` and `S_SCORE` alone suffice), the plan explicitly permits dropping `Prediction_Risk`/`Uncertainty_Risk` from the final formula — the four-term form is the ceiling, not a requirement.

---

# PART IV — CORRECTION #2: MODULE B STAGED PREDICTION CONTRACT

| Model | Inputs | Inference stage | Purpose |
|---|---|---|---|
| **B0** | `Value_0h`, `Value_24h` only | 24h | Exact SIH requirement — official strict baseline |
| **B1** | B0 + `Device_Type`, `Temperature`, `Voltage` | 24h | Tests whether contextual metadata helps |
| **B2-Early** | B1 + early trajectory/peer/cross-parameter features available by 24h | 24h | Enhanced early-warning model without waiting for 96h |
| **B2-96h** | B1 + `Value_96h`, 24→96h slope/acceleration/curvature, peer/cross-parameter features available by 96h | 96h | Refined mid-burn-in prediction using additional evidence |

Rules:

- B0's MAE is the number reported against the literal SIH problem statement. It is never blended with B1/B2 results.
- B1, B2-Early, and B2-96h are reported side-by-side, never presented as replacing B0.
- B2-Early may use only features available at or before 24h.
- B2-96h may use only features available at or before 96h.
- Neither model may use `Value_168h` actual, post-failure data, or any future-derived feature at inference.
- B2-Early preserves the project's early-warning claim; B2-96h is a later-stage refinement.
- Model selection remains empirical; no accuracy ordering is assumed.

# PART V — CORRECTION #3: LEAVE-ONE-OUT PAT STATISTICS

### Formula
For component *i* in lot *L*:
```
L_minus_i        = L \ {i}
median_minus_i    = median(L_minus_i)
MAD_minus_i       = median(|x - median_minus_i|) for x in L_minus_i
ModifiedZ_minus_i = 0.6745 * (x_i - median_minus_i) / MAD_minus_i
```

### Pseudocode
```python
def modified_z_loo(values, index):
    others = values[:index] + values[index+1:]
    med = median(others)
    mad = median([abs(v - med) for v in others])
    if mad == 0:
        mad = fallback_mad(others)   # see zero-MAD handling below
    return 0.6745 * (values[index] - med) / mad
```

### Edge cases
- **Small lot (n < 5):** leave-one-out statistics become unstable; fall back to Mode B (historical reference population) rather than in-lot statistics.
- **Zero MAD (all remaining values identical):** substitute a small-sample-safe estimator — either (a) a minimum-MAD floor derived from historical process variance for that parameter/device, or (b) fall back to IQR-based scaling. Never divide by zero.
- **Lot fully homogeneous defect (entire lot shifted together):** leave-one-out cannot detect a lot-wide shift by construction — this is precisely why cross-lot / historical reference comparison (Mode B, Part VII) and station-level checks (Part VIII) exist as complementary layers.

### Validation tests
- Unit test: injecting a synthetic outlier must not shrink its own detected deviation (regression test against the v1 bug).
- Unit test: MAD=0 lots must not raise a divide-by-zero exception and must route to fallback estimator.
- Empirical regression test: controlled synthetic outlier cases must show that LOO removes or materially reduces systematic self-suppression across multiple lot sizes, outlier magnitudes, contamination levels, and zero-MAD cases. This is not a universal mathematical monotonicity claim.

### When LOO is necessary
Whenever the statistic used to judge component *i* is derived from a population that *includes* component *i*, LOO is mandatory — otherwise an outlier pulls its own reference distribution toward itself, understating its own deviation. This applies to lot median/MAD (PAT) and to peer-group means/medians (Peer Residual).


# PART VI — CORRECTION #4: TWO DEPLOYMENT/EVALUATION MODES

### Mode A — Batch-Aware / Current-Lot Screening
The system has a full (or partial) lot available. Lot median/MAD and peer statistics are computed **leave-one-out** from currently available components. Appropriate when the lot has enough components (n ≥ 5, tunable threshold) for stable robust statistics.

### Mode B — Cold-Start / Historical-Reference Screening
Used when the current lot is too small, brand new, or statistics are otherwise unreliable. Falls back to a **hierarchical reference**:
```
device + temperature-bin reference
        ↓ (if insufficient population)
device-only historical reference
        ↓ (if insufficient population)
global healthy reference population
```
Historical references are built only from **training-split, previously-validated-healthy** components — never from the test/validation lots being scored, preventing leakage across evaluation folds.

In real deployment, “historically healthy” requires explicit provenance. A component/lot enters the healthy reference population only after passing the organization’s established qualification/reliability acceptance process and having no known subsequent failure, rework, or invalid-test disposition within the defined observation window. The reference record should retain source lot, device type, test conditions, acceptance basis, observation window, and reference-data version. If validated-healthy history is insufficient, the system falls back hierarchically or routes to `REVIEW_REQUIRED`; it must not silently treat unverified data as healthy.

### Why they must be distinguished
- Mode A statistics are unavailable or unstable for new/small lots — using them anyway silently produces meaningless Modified-Z values.
- Mode B references introduce a different bias source (temporal drift of the "healthy" reference population over time) that must be monitored (MLOps, Part XV) rather than ignored.
- Small-lot handling: lots below the stability threshold are **automatically routed to Mode B**, and the QA report states which mode was used, so a reviewer knows the statistical basis of the score.

Both modes are reported in evaluation (Part XI, Experiment J).

### Whole-Lot Shift Detection — Lot Shift Score

Leave-one-out PAT cannot detect a uniformly shifted lot because every component can remain normal relative to its peers. Add a complementary **Lot Shift Score**:

```text
current_lot_statistic = robust location/scale summary of current lot
historical_reference  = corresponding training-only healthy reference
Lot_Shift_Score       = normalized distance(current_lot_statistic,
                                           historical_reference)
```

- PAT asks: **“Is this component unusual relative to its current lot?”**
- Lot Shift Score asks: **“Is this lot unusual relative to historically healthy lots?”**
- The score is evaluated explicitly on whole-lot-shift scenarios.
- Its historical reference is fitted only from the training split during evaluation.


---

# PART VII — CORRECTION #5: "COMPLEMENTARY," NOT "INDEPENDENT," SIGNALS

v1 claimed "five independent signals." This is corrected everywhere (architecture text, judge answers, demo script) to:

> "Multiple complementary detection signals with partially independent failure modes."

PAT, Peer Residual, Temporal Anomaly, Isolation Forest, and Prediction can be correlated — e.g., a large PAT deviation often co-occurs with a large peer residual. The value of the architecture is **not** statistical independence; it is that **different signals are sensitive to different anomaly patterns** (PAT catches absolute-limit drift, peer residual catches relative/lot-context drift, Early Temporal Anomaly catches trajectory shape, Isolation Forest catches multivariate combinations none of the univariate signals see alone). This distinction is applied consistently in the architecture doc, judge-question answers, and demo narration.

---

# PART VIII — CORRECTION #6: PEER / TEST-STATION LOGIC

### The blind spot
```
Station 3 calibration error → all Station-3 values elevated → Station-3 peer median also
elevated → component appears normal relative to its (also-shifted) peers
```
A peer engine that only ever compares within-station can be fooled exactly when a station fault is present — the fault raises the very baseline used to judge it.

### Fix — compute both
```
within_station_peer_residual   = deviation from peers tested on the SAME station
cross_station_peer_residual    = deviation from peers tested on OTHER stations (same lot/device/time window)
station_shift_score            = |within_station peer median − cross_station peer median|
```
A large `station_shift_score` combined with small `within_station_peer_residual` but large `cross_station_peer_residual` is the signature of a station-level shift, not a device-level defect — this evidence feeds the **Test-Integrity Layer** rather than the device-risk path.

`Test_Station` is **not** forced into every peer definition — it is used specifically to construct the within/cross split and the shift score, not as a blanket grouping key for all statistics.

### Three anomaly origins, kept separate throughout
| Origin | Signature | Routed to |
|---|---|---|
| Device-level anomaly | Elevated vs. both within- and cross-station peers | Device risk |
| Lot-level process shift | Elevated vs. historical reference, but consistent across the lot | Lot-context flag, reviewed separately |
| Station-level measurement shift | Elevated within-station only, normal cross-station | Test-Integrity risk |

---

# PART IX — CORRECTION #7: SAFETY ENVELOPE, SLOPE, AND PROBABILITY LANGUAGE

### Safety evidence is explicitly separated

“Safety Slope” is a family of related engineering signals, not one ambiguous scalar:

1. **Cumulative Safety Drift Envelope** — acceptable cumulative change from baseline over the burn-in horizon.
2. **Interval Safety Slope Envelope** — acceptable rate of change over an interval such as 0→24h or 24→96h.
3. **Acceleration signal** — change in slope between intervals, used to identify increasing degradation rate.

These are distinct evidence types and must not be counted twice. `S_SCORE` remains the terminal statistical-unusualness score for projected drift; `Prediction_Risk` remains distance to the engineering/static limit.

Three explicitly separated cases — never blended:

1. **GPR / probabilistic model** — if a valid predictive distribution exists, it can report `P(Value_168h > Static_Max)` as an actual probability, because the model was built to produce one.
2. **Quantile regression** — produces `P50 / P90 / P95 / P99` (conditional quantiles). A P95 prediction is **not** described as "95% probability of failure" — it is the value below which 95% of the conditional predicted distribution falls, under the model's assumptions.
3. **Point-prediction model** (e.g., gradient boosting regressor) — reports `Predicted_168h`, `distance_to_safety_envelope`, and a `safety_exceedance_score` (a bounded 0–100 score derived from distance, not a probability at all).

All QA-facing report language, the risk-fusion formula, and the API schema are updated so that only case (1), and only after calibration validation (Part XVIII), may use the word "probability."

---

# PART X — CORRECTION #8: TEMPORAL FEATURE AVAILABILITY MATRIX

| Feature | 24h avail. | 96h avail. | 168h avail. | Module A | B0 | B1 | B2 | Training-only | Inference allowed |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `Value_0h` | Y | Y | Y | Y | Y | Y | Y | N | Y |
| `Value_24h` | Y | Y | Y | Y | Y | Y | Y | N | Y |
| `slope_0_24` | Y | Y | Y | Y | N | N | Y | N | Y |
| `relative_drift_0_24` | Y | Y | Y | Y | N | N | Y | N | Y |
| `Device_Type` | Y | Y | Y | context | N | Y | Y | N | Y |
| `Temperature` | Y | Y | Y | context | N | Y | Y | N | Y |
| `Voltage` | Y | Y | Y | context | N | Y | Y | N | Y |
| `Value_96h` | N | Y | Y | at 96h stage only | N | N | B2-96h only | N | Y (≥96h stage) |
| `early_temporal_anomaly_score` | Y | Y | Y | Early Temporal Anomaly | N | N | B2-Early/B2-96h | N | Y |
| `mid_burnin_temporal_anomaly_score` | N | Y | Y | Mid-Burn-In Temporal Anomaly | N | N | B2-96h | N | Y (≥96h stage) |
| `slope_24_96` | N | Y | Y | at 96h stage only | N | N | B2-96h | N | Y (≥96h stage) |
| `acceleration` | N | Y | Y | at 96h stage only | N | N | B2-96h | N | Y (≥96h stage) |
| `trajectory_curvature` | N | Y | Y | at 96h stage only | N | N | B2-96h | N | Y (≥96h stage) |
| `slope_96_168` | N | N | Y | N | N | N | N | Y | N (post-hoc validation only) |
| `Value_168h` (actual) | N | N | Y | N | N | N | N | Y (label) | N |
| `actual_vs_predicted_error` | N | N | Y | N | N | N | N | Y | N |
| `within_station_peer_residual` | Y | Y | Y | Y | N | N | Y | N | Y |
| `cross_station_peer_residual` | Y | Y | Y | Y | N | N | Y | N | Y |
| `station_shift_score` | Y | Y | Y | Test-Integrity | N | N | N | N | Y |

Anything marked `Training-only` (actual 168h value, post-failure data, `actual_vs_predicted_error`) is **structurally excluded** from the online feature pipeline at inference time — the versioned feature engine builds two distinct feature sets (train-time vs. inference-time) from the same schema, and inference-time code has no access to the train-only columns at all (not just "convention," an actual interface boundary).


# PART XI — CORRECTION #9: SYNTHETIC GENERATOR REFRAMED

The defect taxonomy is preserved, with claims narrowed:

> The generator is **not** a semiconductor device simulator. It is a controlled synthetic benchmark for testing whether the screening architecture can detect predefined statistical/Early Temporal Anomaly patterns.

Trajectory families (unchanged taxonomy, reframed description — "physics-inspired candidate trajectory families used for controlled methodology stress testing," not "physically motivated curves"):

```
Healthy            → mild/saturating drift
Gradual defect     → elevated drift
Accelerating defect→ convex nonlinear drift
Sudden degradation → piecewise change
Latent defect      → delayed nonlinear drift
Sensor glitch      → isolated measurement disturbance
```

Temperature effects and cross-parameter coupling are retained as **configurable assumptions/mechanisms**, explicitly labeled as such — not validated semiconductor physics. Every synthetic-data section and the demo script carries this framing so no claim is made that synthetic performance predicts real-hardware performance.

---

# PART XII — CORRECTION #10: TEST-INTEGRITY DETECTION LAYER (RENAMED)

Renamed from "classifier" to **Test-Integrity Detection Layer** (a.k.a. **Measurement-Integrity Rule Engine v1**).

```
Rule Engine v1  (deterministic checks: station_shift_score, repeat-measurement variance,
                 out-of-tolerance environmental readings, known-bad-station flags)
      ↓
repeat measurement / investigate

Future path (not MVP):
Rule Engine v1 → Supervised Test-Integrity Model v2 (trained once labeled
repeat-measurement outcomes exist)
```

Rules vs. ML classification are never conflated in any document section, demo script, or API description — v1 ships as rules only.

---

# PART XIII — CORRECTION #11 & #13: STATIC SCREENING METRICS AND ESCAPE REDUCTION

Static screening's recall/precision against **latent** defects is **measured, not assumed**:
```
Static-only latent-defect recall
Static-only FNR
Static escape count
```
The central experiment across the whole project is **STATIC ONLY vs. STATIC + DYNAMIC**, reported as:
```
Static Escape Count
Dynamic (Hybrid) Escape Count
Escape Reduction % = (Static_Missed − Hybrid_Missed) / Static_Missed × 100
```
This percentage is a demo headline number **only after** it is measured on the synthetic benchmark — it is never pre-written into the plan or slides before the experiment runs.

---

# PART XIV — CORRECTION #12: EARLY DETECTION LEAD TIME

```
Lead_Time = Failure_Time − First_Detection_Time
```
Example: failure event at 168h, first flagged at 24h → lead time = 144h. Computed only for defect instances with a well-defined failure/reference-violation event. Reported as: mean, median, minimum, and distribution by defect class (gradual / accelerating / sudden / latent). This is a headline evaluation metric alongside Escape Reduction %.

---

# PART XV — CORRECTIONS #14–16: NO ASSUMED WINNERS

### Candidate models (shortlist, not exhaustive-for-its-own-sake)
- **Anomaly detection:** Isolation Forest (primary candidate, not "proven best"), Local Outlier Factor, One-Class SVM, Robust Covariance (Elliptic Envelope) — shortlisted for interpretability + tabular fit, not run wastefully beyond this set.
- **Module B regression:** Linear/Ridge, Random Forest, Gradient Boosting, XGBoost/LightGBM/CatBoost (pick one boosting library, not all three, per compute budget), GPR (for the calibrated-uncertainty variant).

### Language corrections applied throughout
- "Gradient Boosting is a strong **candidate baseline** because the problem is low-dimensional tabular prediction; final selection is empirical."
- "Isolation Forest is a **primary candidate**," not "proven best."
- "Evaluate whether each added layer produces measurable benefit on the defect classes it is designed to address" — replaces any "Model G should beat A–F" language.
- No assumption that enhanced > baseline, GPR > GBM, or ML > statistical. If a simpler model wins on the evaluation metrics, the plan explicitly selects the simpler model.

---

# PART XVI — CORRECTION #17: CALIBRATION

Explicit distinction maintained everywhere:
- **Score**: 0–100 relative risk score (A_SCORE, S_SCORE, LDI as currently defined) — a ranking/severity signal, not a probability.
- **Probability**: calibrated probability of defect — only produced where a model is explicitly calibrated (e.g., Platt scaling / isotonic regression on a held-out validation split) and validated as such.

LDI is **never** reported as "87% probability" unless calibration has actually been performed and validated. Required calibration artifacts:
- Calibration curve / reliability diagram (predicted probability bucket vs. observed defect rate)
- Brier score, for any output presented as a probability
- Threshold calibration (operating point selection for PASS/MONITOR/REVIEW/REJECT cutoffs)
- Calibration computed only on validation-split data never used in training


# PART XVII — RESTRUCTURED RISK OUTPUT / API

```json
{
  "device_risk": 82,
  "future_risk": 91,
  "test_integrity_risk": 8,
  "overall_risk_score": 87,
  "decision": "REVIEW",
  "screening_stage": "24h",
  "first_detection_stage": "24h",
  "latest_evidence_stage": "24h",
  "basis": {
    "mode": "Mode A (batch-aware, leave-one-out)",
    "b_model_used": "B2-Early",
    "safety_score_type": "quantile (P95), not a calibrated probability",
    "calibrated_probability_available": false
  }
}
```
*(Illustrative numbers only — never hard-coded in the real system.)*

- **device_risk** — is current behavior abnormal? (derived from `A_SCORE`)
- **future_risk** — is projected behavior concerning? (derived from `S_SCORE` / `Prediction_Risk` / `Uncertainty_Risk`)
- **test_integrity_risk** — could the measurement itself be unreliable? (Test-Integrity Layer)
- **overall_risk_score / decision** — Risk Fusion output (LDI-based) → QA action
- `LDI` is retained **internally** as the fusion computation; the API surfaces its three interpretable components (`device_risk`, `future_risk`, `test_integrity_risk`) plus the fused `overall_risk_score`, so QA never has to reverse-engineer what LDI "means."

---

# PART XVIII — FORMAL FEATURE-LEAKAGE TABLE

See Part X (Temporal Feature Availability Matrix) — it doubles as the leakage table. Explicitly prohibited at inference time, in all stages: `Value_168h` (actual), `slope_96_168`, `actual_vs_predicted_error`, and any post-failure/repair data. These are marked `Training-only` and are structurally excluded from the inference feature-builder's output schema (Part X).

---

# DATASET SPLIT — MANDATORY FIRST EVALUATION STEP

The dataset split occurs **before fitting any reference population, model, safety envelope, calibration artifact, fusion weight, or decision threshold**.

```text
RAW DATA
  ↓
GROUPED TRAIN / VALIDATION / TEST SPLIT
  ↓
FIT TRAIN-ONLY ARTIFACTS
  ├── historical healthy references / PAT fallback references
  ├── peer references
  ├── Lot Shift references
  ├── Isolation Forest / candidate anomaly models
  ├── Module B models
  ├── safety drift/slope envelopes
  ├── probability calibration
  └── LDI / fusion weights and thresholds
  ↓
VALIDATION: model selection + calibration + operating-point tuning
  ↓
FINAL TEST: untouched unbiased evaluation
```

Split by **lot / production-batch group**, never by random measurement rows, so observations from the same lot cannot cross train/validation/test. All validation/test reference statistics must be fitted from training data only.

# PART XIX — VALIDATION SCENARIOS

### Scenario 1 — New component within a known lot
The lot already has ≥ threshold components; Mode A (leave-one-out) statistics apply directly.

### Scenario 2 — New lot
The model has never seen this lot. Hierarchical fallback (Mode B):
```
device + temperature reference → device-only reference → global healthy reference
```
Both scenarios are reported side-by-side in the evaluation results (Experiment J, Part XX), including how many components in the synthetic benchmark fell into each mode and how detection performance differed between them.

---

# PART XX — EXPERIMENT MATRIX

| Exp. | Description | Reports |
|---|---|---|
| A | Static-only baseline | Recall, FNR, Precision, PR-AUC, static escape count |
| B | Static + PAT | Δ vs. A |
| C | Static + PAT + Peer Residual | Δ vs. B |
| D | Static + PAT + Peer + Isolation Forest (= full A_SCORE) | Δ vs. C |
| E | Module B — B0 | MAE (strict SIH contract) |
| F | Module B — B1 | MAE, Δ vs. E |
| G | Module B — B2-Early | MAE, Δ vs. F; 24h early-warning stage |
| G2 | Module B — B2-96h | MAE, Δ vs. B2-Early; 96h refinement stage |
| H | Full integrated system (Module A + B + Fusion) | All metrics below |
| I | Test-integrity stress test (synthetic station miscalibration injected) | Within/cross-station residual behavior, false-normal rate |
| J | Distribution-shift / new-lot test (Scenario 2, Mode B) | Recall/FNR under cold start vs. Scenario 1 |
| K | Missing-data robustness | Fail-safe routing correctness (never silently PASS) |
| L | Sensor-glitch robustness | REPEAT_MEASUREMENT vs. false REJECT rate |

Every experiment reports, where applicable: Recall, FNR, Precision, PR-AUC, false alarms, review burden, static escapes, Escape Reduction %, Lead Time, and MAE (prediction experiments only).

---

# PART XXI — ABLATION STUDY

Remove one component at a time from the full system and measure impact **empirically**, with no assumed direction of effect:
```
Remove PAT
Remove Peer Residual
Remove Temporal Features
Remove Isolation Forest
Remove Cross-Parameter Features
Remove Safety Slope
Remove Prediction (Module B)
Remove Test-Integrity Layer
```
Report class-specific effects (e.g., the hypothesis that removing acceleration mainly hurts `accelerating_drift`/`latent_defect`/`eventual_limit_violation` detection is stated as a hypothesis to test, not an assumed result — verified against the synthetic benchmark's labeled defect classes).


# PART XXII — SIH DEMO SCRIPT

**Centerpiece component walkthrough:**
```
Static value            → PASS
Lot-relative (PAT/Peer) → ABNORMAL
Early trajectory (≤24h) → ABNORMAL
168h prediction (B2)    → CONCERNING
Safety envelope         → EXCEEDED (quantile-based, not labeled "probability")
Final decision          → REVIEW / REJECT, with full evidence trail
```
**Secondary demo — sensor glitch handling:**
```
Sensor glitch signature detected (Test-Integrity Layer)
      ↓
REPEAT_MEASUREMENT   (not a false REJECT)
```
Show the exact evidence trail (which signals fired, within/cross-station residuals, B0/B1/B2-Early/B2-96h predictions, safety-envelope distance) so the decision is auditable end-to-end.

---

# PART XXIII — JUDGE QUESTIONS (UPDATED, CONCISE DEFENSIBLE ANSWERS)

1. **Why isn't static screening enough?** — It catches only fixed-limit violations at one point in time; it cannot see lot-relative deviation, trajectory shape, or projected drift (measured static-only latent-defect recall, Part XIII, quantifies the gap).
2. **Why PAT?** — Detects deviation from what's expected for that parameter/device given lot context, catching subtler shifts than a fixed limit.
3. **Why Modified Z instead of ordinary Z?** — Robust to outliers and non-normal burn-in distributions; median/MAD are less sensitive to the very anomalies being detected.
4. **Why leave-one-out statistics?** — Prevents the component under test from biasing its own reference distribution (Part V).
5. **Why peer residual?** — Adds lot-relative context PAT alone doesn't capture, especially for parameters with natural lot-to-lot variation.
6. **Why can `Test_Station` create a blind spot?** — A station-wide shift raises the peer baseline itself, masking the shift it should reveal (Part VIII) — fixed via within/cross-station split.
7. **Difference between device risk and test-integrity risk?** — Device risk asks "is the component abnormal"; test-integrity risk asks "can we trust the measurement itself."
8. **How does B0 satisfy the SIH requirement?** — B0 uses exactly `Value_0h, Value_24h → Value_168h`, no metadata, matching the literal problem statement (Part IV).
9. **How do you prevent future-data leakage?** — Feature-Availability Matrix (Part X) structurally separates train-only columns from the inference feature-builder's output.
10. **Why use synthetic data?** — No labeled real burn-in failure dataset is available for this SIH scope; synthetic data lets the architecture be stress-tested against known ground truth.
11. **How do you know synthetic defects aren't too easy?** — By reporting per-class recall/FNR and lead time rather than a single aggregate accuracy, and by including subtle classes (latent, accelerating) specifically designed to be hard.
12. **Why not deep learning?** — Tabular, low-dimensional, small-sample-per-lot data; boosting/GPR/Isolation Forest are better-suited and more explainable at this data scale.
13. **Why Isolation Forest?** — Efficient multivariate anomaly detection without needing labeled anomalies; a candidate, evaluated against LOF/One-Class SVM/Robust Covariance.
14. **Why not LOF?** — It's in the candidate shortlist; final choice is decided by the anomaly-detection experiments, not assumed.
15. **Why not One-Class SVM?** — Same — shortlisted, selection is empirical.
16. **Why Gradient Boosting?** — Strong candidate baseline for low-dimensional tabular regression; not assumed to win outright.
17. **Why GPR?** — Offers a genuine calibrated predictive distribution when uncertainty quantification is required, unlike point-prediction models.
18. **What does your prediction interval actually mean?** — Depends on model type (Part IX): a true probability only for a calibrated GPR; a conditional quantile for quantile regression; a distance-to-envelope score for point predictors.
19. **How is the safety envelope calculated?** — Comparing the predicted 168h value (and its interval/quantiles) against the static datasheet limit.
20. **Why 95th/99th percentile?** — A configurable operating-point choice, not claimed universally correct; QA can tune it to their risk tolerance.
21. **What happens with a new lot?** — Mode B hierarchical fallback (device+temp → device → global reference), Part VI/XIX Scenario 2.
22. **What happens with a lot of only 5 components?** — Below the stability threshold routes to Mode B rather than unstable in-lot statistics.
23. **What happens if the whole lot is bad?** — Leave-one-out cannot catch a uniform lot-wide shift by construction; cross-lot historical comparison and station-level checks provide the complementary signal.
24. **What happens if the test station is miscalibrated?** — Within/cross-station residual split and `station_shift_score` flag it as test-integrity risk, not device risk (Part VIII).
25. **How do you distinguish sensor glitch from component degradation?** — Glitch signature is an isolated, non-persistent disturbance inconsistent with trajectory continuity; routed to REPEAT_MEASUREMENT via the Test-Integrity Layer.
26. **What does SHAP actually explain?** — Feature contribution to the model's score — a correlational importance ranking.
27. **Does SHAP prove physical root cause?** — No — explicitly stated throughout the plan.
28. **What does LDI mean?** — An internal fused risk index combining A_SCORE, S_SCORE, Prediction_Risk, and Uncertainty_Risk (Part III); not an industry-standard metric.
29. **Is LDI a probability?** — Only if calibrated and validated as one (Part XVI); otherwise it's a relative risk score.
30. **How do you prevent double-counting?** — Each sub-signal contributes to exactly one composite score before entering LDI (Part III).
31. **False-negative strategy?** — Multiple complementary signals + lead-time metric to catch defects earlier than static alone; measured via escape reduction.
32. **False-positive strategy?** — Calibrated thresholds, review-burden metric tracked explicitly, MONITOR tier to avoid hard REJECT on borderline cases.
33. **What is early detection lead time?** — Part XIV.
34. **How much static escape reduction do you achieve?** — Reported as a measured experimental result (Part XIII), never pre-assumed.
35. **How would this be validated on real space-grade hardware?** — Not claimed as validated for space; would require a real-hardware validation phase with actual failure labels, outside current SIH scope.
36. **Limitations of synthetic data?** — Does not represent real ISRO hardware physics; trajectory families are configurable assumptions, not validated device physics (Part XI).
37. **What happens under distribution shift?** — Monitored via MLOps drift checks (Part XXVI) and evaluated directly in Experiment J.
38. **What happens if the model is unavailable?** — Fail-safe routes to REVIEW_REQUIRED/DATA_UNAVAILABLE, never PASS (Part XXIV).
39. **What happens if the prediction model is wrong?** — Uncertainty_Risk and the safety-envelope distance still feed the fused decision; wrong predictions are caught in aggregate via calibration monitoring, not assumed away.
40. **Why should QA trust the output?** — Because every score is traceable to an evidence trail (Part XXII), no score is mislabeled as something it isn't (Part IX/XVI), and no failure mode silently produces a PASS.

---

# DECISION PRECEDENCE

Risk fusion uses the following action precedence:

```text
HARD STATIC FAILURE
        ↓
     REJECT

DATA / MODEL FAILURE
        ↓
REVIEW_REQUIRED / DATA_UNAVAILABLE

HIGH TEST-INTEGRITY RISK
        ↓
REPEAT_MEASUREMENT / INVESTIGATE

HIGH DEVICE OR FUTURE RISK
        ↓
REVIEW / REJECT according to calibrated operating thresholds

OTHERWISE
        ↓
PASS / MONITOR
```

`REPEAT_MEASUREMENT` is an **action override**, not merely another numerical risk score. A suspected measurement-integrity problem should not directly become a device rejection when the correct action is to obtain a trustworthy measurement.

# PART XXIV — FAIL-SAFE ARCHITECTURE (PRESERVED)

```
missing data / unknown device / model unavailable / distribution shift /
invalid units / insufficient reference population
        ↓
REVIEW_REQUIRED / DATA_UNAVAILABLE
```
Never `error → PASS`. Static engineering failures remain hard failures under all conditions.


# PART XXV — API / DASHBOARD / MLOPS (SUMMARY)

**API** — returns the restructured JSON of Part XVII; always includes `screening_stage`, `first_detection_stage`, `latest_evidence_stage`, and `basis` (mode used, B-model used, whether the safety score is a calibrated probability) so downstream consumers never mis-attribute meaning to a number.

**Dashboard** — per-lot view showing static pass/fail, `A_SCORE` breakdown (without exposing internal duplicate-risk math), B0/B1/B2-Early/B2-96h predictions side-by-side, screening stage timeline, first detection stage, latest evidence stage, safety-envelope distance, test-integrity flags (within vs. cross-station), and the final QA decision with evidence links.

# PART XXVI — MLOPS

- Feature-schema versioning tied 1:1 to the Feature-Availability Matrix (Part X) — a schema change requires an explicit matrix update and re-validation that no train-only column leaked into inference.
- Drift monitoring on: input distributions, `A_SCORE`/`S_SCORE` distributions, and calibration reliability (re-run the reliability diagram periodically against newly-labeled outcomes if/when available).
- Model registry distinguishes B0/B1/B2 and Rule-Engine-v1 vs. future Supervised-Test-Integrity-v2 as separate versioned artifacts.

---

# PART XXVII — CLAIMS THIS PLAN DOES NOT MAKE

- AI does not guarantee detection of all latent defects.
- Synthetic data does not represent real ISRO hardware.
- AEC-Q001, if referenced, is not treated as an ISRO/space standard.
- Battery degradation physics is not claimed to transfer directly to semiconductors.
- Maritime anomaly-detection methods are not claimed to prove semiconductor reliability.
- SHAP is not claimed to identify physical root cause.
- Statistical anomaly is not automatically claimed to mean physical defect.
- LDI is not claimed to be an established industry standard.
- LDI is not claimed to be a probability unless properly calibrated.
- The model is not claimed to be production-qualified for space.
- High synthetic-benchmark accuracy is not claimed to prove industrial reliability.
- No model is called "best" before experiments are run.
- Enhanced models are not assumed to outperform simpler ones.
- 95th/99th percentile is not claimed universally correct — it's a tunable operating point.
- Static screening is not claimed to have 100% recall against latent defects.

---

# PART XXVIII — FINAL CONSISTENCY AUDIT

Checked terms for consistency with the corrected architecture: `LDI`, `A_score`, `peer residual`, `Early Temporal Anomaly`, `Value_0h/24h/96h/168h`, `safety slope`, `95th/99th`, `probability`, `SHAP`, `classifier`, `static recall`, `synthetic`, `leakage`, `independent`, `best model`.

- **Architecture consistency:** no duplicated signals — verified (Part III).
- **Module B consistency:** B0 exactly equals `0h + 24h → 168h` — verified (Part IV).
- **Leakage consistency:** no future information enters inference — verified (Part X/XVIII).
- **PAT consistency:** leave-one-out used throughout — verified (Part V).
- **Validation consistency:** lot grouping correctly handled across Modes A/B — verified (Part VI, Part XIX).
- **Probability consistency:** probability never confused with quantiles/bounds — verified (Part IX, Part XVI).
- **Explainability consistency:** SHAP described as correlational, not causal — verified (Part XXIII Q26–27, Part XXVII).
- **Synthetic-data consistency:** no real-hardware representation claim — verified (Part XI, Part XXVII).
- **Decision consistency:** model failure cannot result in PASS — verified (Part XXIV).
- **Evaluation consistency:** no predetermined winner — verified (Part XV, Part XX, Part XXI).

---

# FINAL CONSISTENCY AUDIT — v3

- **Architecture preserved:** Static → Statistical → Peer → Trajectory → Prediction → Safety → Fusion → Explainability remains unchanged.
- **No double counting:** `A_SCORE` remains the only downstream representation of Module A sub-signals.
- **B0 contract:** exactly `Value_0h + Value_24h → Value_168h`.
- **B2-Early:** only ≤24h information.
- **B2-96h:** only ≤96h information.
- **Prediction_Risk:** distance to engineering/static limit.
- **S_SCORE:** statistical unusualness relative to healthy drift distribution.
- **Safety evidence:** cumulative drift envelope, interval slope envelope, and acceleration are distinct.
- **LOO testing:** universal monotonicity claim removed; empirical regression testing used.
- **Whole-lot protection:** Lot Shift Score added against training-only historical healthy references.
- **Historical healthy provenance:** explicitly defined for real deployment.
- **Decision precedence:** hard static failure > data/model failure > high test-integrity → REPEAT_MEASUREMENT > device/future risk > normal decision.
- **Dataset split:** occurs before fitting PAT references, peer references, Lot Shift references, Isolation Forest, Module B, safety envelopes, calibration, fusion weights, and thresholds.
- **Stage tracking:** `screening_stage`, `first_detection_stage`, `latest_evidence_stage` added to API/dashboard.
- **No unnecessary models added.**
- **No experiment outcome assumed.**
- **No probability claim without calibration.**
- **Fail-safe principle preserved:** system failure never silently produces PASS.

**Final status:** v2 architecture preserved with the requested v3 hardening changes applied; no architectural redesign performed.

# FINAL ARCHITECTURE DECISION

```
STATIC LIMIT
     ↓
STATISTICAL DEVIATION        (PAT, leave-one-out Modified Z)
     ↓
PEER DEVIATION                (within-station + cross-station residuals)
     ↓
TRAJECTORY ABNORMALITY        (Early Temporal Anomaly, ≤24h features, + Isolation Forest → A_SCORE)
     ↓
EARLY FUTURE PREDICTION       (Module B: B0 strict / B1 contextual / B2 enhanced)
     ↓
SAFETY ENVELOPE                (quantile/point/GPR-appropriate exceedance → S_SCORE)
     ↓
DEVICE RISK / FUTURE RISK / TEST-INTEGRITY RISK   (Risk Fusion: A_SCORE, S_SCORE,
                                                     Prediction_Risk, Uncertainty_Risk → LDI)
     ↓
QA DECISION                    (PASS / MONITOR / REVIEW / REJECT / REPEAT)
     ↓
EXPLAINABLE EVIDENCE           (SHAP = correlational importance, full evidence trail)
```
No signal is summed twice. No feature crosses its availability boundary. No statistic includes the point it is judging. No score is called a probability unless calibrated. No independence, physical-realism, or superiority claim is made without evidence. Device-, lot-, and station-level anomaly origins are kept separate end to end. Every failure mode routes to REVIEW/DATA_UNAVAILABLE, never to PASS.

---

# EXACT NEXT 15 IMPLEMENTATION ACTIONS

1. **`schema/data_contract.py`** — Define the raw input schema (component ID, lot ID, station ID, device type, temperature, voltage, `Value_0h/24h/96h/168h`). *Input:* none. *Output:* schema definitions. *Validation:* unit tests on required fields. *Dependency:* none.
2. **`schema/feature_availability_matrix.py`** — Encode Part X's matrix as an enforced interface (train-only vs. inference-allowed columns per stage). *Input:* schema. *Output:* two feature-set builders (train/inference). *Validation:* test that inference builder cannot access train-only columns. *Dependency:* 1.
3. **`validation/validate_input.py`** — Schema/units/range validation with fail → `REVIEW_REQUIRED`. *Input:* raw record. *Output:* validated record or fail-safe flag. *Validation:* malformed-input test suite. *Dependency:* 1.
4. **`screening/static_screen.py`** — Deterministic datasheet-limit check. *Input:* validated record. *Output:* static PASS/FAIL + escape-tracking hook. *Validation:* known-limit test cases. *Dependency:* 3.
5. **`synthetic/generator.py`** — Implement the six trajectory families (Part XI) with configurable, clearly-labeled assumption parameters. *Input:* config (n components, defect-class mix, noise). *Output:* labeled synthetic dataset. *Validation:* per-class distribution sanity checks. *Dependency:* 1.
6. **`eval/dataset_split.py`** — Freeze grouped train/validation/test lots before fitting any reference population, model, safety envelope, calibration, fusion weight, or threshold. *Validation:* assert no lot/production batch crosses splits. *Dependency:* 1.
6. **`features/pat.py`** — Leave-one-out median/MAD/Modified-Z with zero-MAD and small-lot fallback (Part V). *Input:* lot values. *Output:* per-component PAT score. *Validation:* LOO regression test (self-suppression bug check). *Dependency:* 2, 5.
7. **`features/peer_residual.py`**
8. **`features/lot_shift.py`** — Compare current-lot robust statistics against training-only historically healthy references and produce `Lot_Shift_Score`. *Validation:* whole-lot-shift injection test. — Within-station and cross-station residuals + `station_shift_score` (Part VIII). *Input:* lot + station-tagged values. *Output:* three residual/shift scores per component. *Validation:* synthetic station-shift injection test. *Dependency:* 2, 5.
8. **`features/temporal_anomaly.py`** — Early Temporal Anomaly (0–24h) plus optional Mid-Burn-In Temporal Anomaly (24–96h) (slope_0_24, relative_drift_0_24). *Input:* validated record. *Output:* temporal feature vector. *Validation:* availability-boundary test (no 96h/168h leakage). *Dependency:* 2, 5.
9. **`models/isolation_forest.py`** — Multivariate anomaly score over Module A feature set. *Input:* feature vectors. *Output:* IF anomaly score. *Validation:* candidate comparison harness vs. LOF/One-Class SVM/Robust Covariance. *Dependency:* 6, 7, 8.
10. **`fusion/a_score.py`** — Combine PAT, peer residual, Early Temporal Anomaly, IF into a single `A_SCORE`. *Input:* outputs of 6–9. *Output:* `A_SCORE`. *Validation:* confirm no sub-signal reused downstream (Part III invariant test). *Dependency:* 6, 7, 8, 9.
11. **`models/module_b.py`** — Train B0/B1/B2-Early/B2-96h regressors with strict input-set separation. *Input:* feature sets per contract (Part IV). *Output:** predicted `Value_168h` + interval/quantiles per model type. *Validation:* leakage test ensuring B0 never sees B1/B2-only columns. *Dependency:* 2, 5.
12. **`safety/envelope.py`** — Compute `S_SCORE` per model-type-appropriate semantics (probability/quantile/distance, Part IX). *Input:* Module B outputs + static limits. *Output:* `S_SCORE`, `Prediction_Risk`, `Uncertainty_Risk`. *Validation:* semantic-label test (no "probability" label on uncalibrated output). *Dependency:* 11.
13. **`test_integrity/rule_engine.py`** — Rule-based Measurement-Integrity Layer using `station_shift_score` and repeat-measurement checks (Part XII). *Input:* peer-residual + station outputs. *Output:* `test_integrity_risk`, REPEAT_MEASUREMENT flag. *Validation:* sensor-glitch synthetic test (Experiment L). *Dependency:* 7.
14. **`fusion/risk_fusion.py`** — Compute LDI from `A_SCORE`, `S_SCORE`, `Prediction_Risk`, `Uncertainty_Risk`; expose `device_risk/future_risk/test_integrity_risk/overall_risk_score/decision` per the API schema (Part XVII). *Input:* outputs of 10, 12, 13. *Output:* fused decision object. *Validation:* double-counting invariant test + fail-safe routing test (Part XXIV). *Dependency:* 10, 12, 13.
15. **`eval/experiment_runner.py`** — Run Experiments A–L (Part XX) and the ablation study (Part XXI), producing Recall/FNR/Precision/PR-AUC/Escape-Reduction%/Lead-Time/MAE/calibration reports with no predetermined outcome hard-coded. *Input:* synthetic dataset + all trained models. *Output:* experiment result tables/plots. *Validation:* re-run determinism check on fixed random seed. *Dependency:* 4, 9, 10, 11, 12, 13, 14.

