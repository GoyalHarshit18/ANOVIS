/**
 * Centralized Prototype Demo Fallbacks
 * Used ONLY when backend data is genuinely missing/null/undefined/N/A.
 * Real backend data ALWAYS takes precedence.
 * Legitimate zero values (0, 0.0, false) are preserved.
 */

export const DEMO_IDENTIFIERS = {
  lot: "LOT_PRED_TEST_01",
  componentId: "CMP_00173",
  deviceType: "TYPE_B",
  station: "ST_01",
  runId: "RUN-0619AC50",
  filename: "burnin_data_v102.csv",
  timestamp: "27 Sep 2026, 01:03 AM",
};

export const DEMO_STATION = {
  run: "RUN-0619AC50",
  stationId: "ST_01",
  status: "ANOMALOUS",
  reason: "Station-level disturbance detected based on elevated component anomaly concentration and station shift evidence.",
  proportionAnomalous: "27.3%",
  stationShiftScore: "0.82",
  temperatureVariance: "3.8 °C",
  voltageNoise: "18.6 mV",
  setupYield: "72.7%",
  historicalTemperatureVariance: "1.4 °C",
  historicalVoltageNoise: "7.2 mV",
  historicalSetupYield: "94.5%",
  affectedComponents: [
    { id: "CMP_004", score: 0.87, station_status: "FLAGGED", evidence: "Station shift & concentration anomaly" },
    { id: "C01_011", score: 0.81, station_status: "FLAGGED", evidence: "Station shift & concentration anomaly" },
    { id: "C03_019", score: 0.76, station_status: "FLAGGED", evidence: "Station shift & concentration anomaly" },
    { id: "C07_006", score: 0.72, station_status: "FLAGGED", evidence: "Station shift & concentration anomaly" }
  ]
};

export const DEMO_LOT = {
  lot_id: "LOT_PRED_TEST_01",
  run_id: "RUN-0619AC50",
  device_type: "TYPE_B",
  components: 22,
  flagged_components: ["CMP_004", "C01_011", "C03_019", "C07_006", "CMP_00173", "CMP_00088"],
  lot_shift: {
    status: "NORMAL",
    score: 0.18
  },
  station_analysis: {
    test_integrity_risk: 0.12,
    station_shift_score: 0.82
  },
  parameter_metrics: {
    Iddq_uA_0h: { current_lot_median: 13.12, historical_ref_median: 13.05, score: 0.05 },
    Leakage_nA_0h: { current_lot_median: 545.47, historical_ref_median: 538.20, score: 0.13 },
    PropDelay_ns_0h: { current_lot_median: 3.37, historical_ref_median: 3.36, score: 0.03 }
  },
  reference_limits: {
    Iddq_uA_0h: { lower: 10.50, upper: 16.20 },
    Leakage_nA_0h: { lower: 450.00, upper: 650.00 },
    PropDelay_ns_0h: { lower: 3.10, upper: 3.65 }
  },
  distributions: {
    Leakage_nA_0h: [
      { bin: '480-500', count: 1 },
      { bin: '500-520', count: 3 },
      { bin: '520-540', count: 7 },
      { bin: '540-560', count: 6 },
      { bin: '560-580', count: 3 },
      { bin: '580-600', count: 2 }
    ]
  },
  stations: [
    {
      station_id: "ST_01",
      integrity_status: "ANOMALOUS",
      station_shift_score: 0.82,
      within_station_evidence: {
        total_components: 22,
        disturbance_components: 6,
        proportion: 0.273,
        reason: "Station-level disturbance detected based on elevated component anomaly concentration and station shift evidence."
      },
      parameter_evidence: {
        temperature_variance: "3.8 °C",
        voltage_noise: "18.6 mV",
        setup_yield: "72.7%"
      },
      historical_reference: {
        historical_temperature_variance: "1.4 °C",
        historical_voltage_noise: "7.2 mV",
        historical_setup_yield: "94.5%"
      },
      components: [
        { component_id: "CMP_004", score: 0.87, station_status: "FLAGGED", evidence: "Station shift & concentration anomaly" },
        { component_id: "C01_011", score: 0.81, station_status: "FLAGGED", evidence: "Station shift & concentration anomaly" },
        { component_id: "C03_019", score: 0.76, station_status: "FLAGGED", evidence: "Station shift & concentration anomaly" },
        { component_id: "C07_006", score: 0.72, station_status: "FLAGGED", evidence: "Station shift & concentration anomaly" }
      ]
    }
  ]
};

export const DEMO_COMPONENT_RESULTS = [
  { component_id: "CMP_004", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 87.0, ldi: 74.2, stage: "96h", decision: "REJECT", prediction_risk: 0.88 },
  { component_id: "C01_011", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 81.0, ldi: 68.5, stage: "96h", decision: "REJECT", prediction_risk: 0.82 },
  { component_id: "CMP_00173", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 84.2, ldi: 64.4, stage: "96h", decision: "REVIEW_REQUIRED", prediction_risk: 0.78 },
  { component_id: "C03_019", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 76.0, ldi: 58.1, stage: "96h", decision: "REVIEW_REQUIRED", prediction_risk: 0.65 },
  { component_id: "C07_006", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 72.0, ldi: 54.0, stage: "96h", decision: "REVIEW_REQUIRED", prediction_risk: 0.60 },
  { component_id: "CMP_00088", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 68.4, ldi: 49.2, stage: "96h", decision: "REPEAT_MEASUREMENT", prediction_risk: 0.52 },
  { component_id: "CMP_00013", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 18.2, ldi: 12.0, stage: "96h", decision: "PASS", prediction_risk: 0.12 },
  { component_id: "CMP_00021", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 14.5, ldi: 9.8, stage: "96h", decision: "PASS", prediction_risk: 0.08 },
  { component_id: "CMP_00034", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 22.1, ldi: 16.4, stage: "96h", decision: "PASS", prediction_risk: 0.15 },
  { component_id: "CMP_00045", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 19.8, ldi: 14.2, stage: "96h", decision: "PASS", prediction_risk: 0.11 },
  { component_id: "CMP_00052", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 16.3, ldi: 11.5, stage: "96h", decision: "PASS", prediction_risk: 0.09 },
  { component_id: "CMP_00067", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 21.0, ldi: 15.0, stage: "96h", decision: "PASS", prediction_risk: 0.14 },
  { component_id: "CMP_00078", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 17.4, ldi: 12.8, stage: "96h", decision: "PASS", prediction_risk: 0.10 },
  { component_id: "CMP_00091", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 24.5, ldi: 18.2, stage: "96h", decision: "PASS", prediction_risk: 0.16 },
  { component_id: "CMP_00103", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 15.2, ldi: 10.4, stage: "96h", decision: "PASS", prediction_risk: 0.07 },
  { component_id: "CMP_00115", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 18.9, ldi: 13.6, stage: "96h", decision: "PASS", prediction_risk: 0.12 },
  { component_id: "CMP_00128", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 20.3, ldi: 14.8, stage: "96h", decision: "PASS", prediction_risk: 0.13 },
  { component_id: "CMP_00139", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 16.8, ldi: 11.9, stage: "96h", decision: "PASS", prediction_risk: 0.09 },
  { component_id: "CMP_00144", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 23.0, ldi: 17.1, stage: "96h", decision: "PASS", prediction_risk: 0.15 },
  { component_id: "CMP_00156", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 19.4, ldi: 13.9, stage: "96h", decision: "PASS", prediction_risk: 0.11 },
  { component_id: "CMP_00162", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 25.1, ldi: 19.0, stage: "96h", decision: "MONITOR", prediction_risk: 0.22 },
  { component_id: "CMP_00180", lot: "LOT_PRED_TEST_01", device_type: "TYPE_B", station: "ST_01", a_score: 27.8, ldi: 21.4, stage: "96h", decision: "MONITOR", prediction_risk: 0.26 }
];

export const DEMO_DASHBOARD_SUMMARY = {
  pass: 16,
  monitor: 2,
  review: 3,
  reject: 1,
  repeat_measurement: 0,
  data_unavailable: 0
};

export const DEMO_COMPONENT_DETAIL = {
  component_id: "CMP_00173",
  lot: "LOT_PRED_TEST_01",
  device_type: "TYPE_B",
  station: "ST_01",
  decision: "REVIEW_REQUIRED",
  a_score: 84.2,
  ldi: 64.4,
  s_score: 88.5,
  prediction_risk: 78.5,
  uncertainty_risk: 24.0,
  fusion_score: 88.0,
  stage: "96h",
  screening_stage: "FINAL",
  run_id: "RUN-0619AC50",
  explanation: "Static screening passes, but dynamic drift and early temporal deviations warrant QA review.",
  evidence: {
    current_state: {
      a_score: 84.2,
      supervised_score: 0.842
    },
    future_state: {
      prediction_risk: 78.5,
      s_score: 88.5
    },
    fusion_state: {
      component_96h_score: 0.82,
      late_drift_risk: 0.74,
      fusion_score: 0.88,
      fusion_status: "AVAILABLE"
    },
    test_integrity: {
      integrity_flag: false
    },
    explanation: "Static screening passes, but dynamic drift and early temporal deviations warrant QA review.",
    pat: {
      score: 85.2,
      status: "ELEVATED",
      details: {
        Iddq_uA_24h: { measured: 13.02, median: 13.12, mad: 0.83, modified_z: -0.09, abs_modified_z: 0.09, status: "NORMAL" },
        Leakage_nA_24h: { measured: 524.49, median: 545.47, mad: 35.64, modified_z: -0.40, abs_modified_z: 0.40, status: "NORMAL" },
        PropDelay_ns_24h: { measured: 3.37, median: 3.37, mad: 0.05, modified_z: -0.04, abs_modified_z: 0.04, status: "NORMAL" }
      }
    },
    peer_residual: {
      score: 78.4,
      status: "ELEVATED",
      details: {
        Iddq_uA_24h: { measured: 13.02, expected: 13.07, residual: -0.05, normalized_residual: 0.14, status: "NORMAL" },
        Leakage_nA_24h: { measured: 524.49, expected: 525.59, residual: -1.10, normalized_residual: 0.07, status: "NORMAL" },
        PropDelay_ns_24h: { measured: 3.37, expected: 3.36, residual: 0.01, normalized_residual: 0.26, status: "NORMAL" }
      },
      n_neighbors: 10,
      mean_distance: 0.11
    },
    early_temporal: {
      score: 91.0,
      status: "HIGH",
      details: {
        Iddq_uA: { drift_0_24h: -0.33, relative_drift: -0.02, early_slope: -0.01, z_score: 1.11, status: "NORMAL" },
        Leakage_nA: { drift_0_24h: 7.92, relative_drift: 0.02, early_slope: 0.33, z_score: 0.34, status: "NORMAL" },
        PropDelay_ns: { drift_0_24h: 0.03, relative_drift: 0.01, early_slope: 0.001, z_score: 0.99, status: "NORMAL" }
      }
    },
    isolation_forest: {
      score: 88.3,
      status: "HIGH",
      details: {
        raw_score: 0.1107,
        prediction: 1,
        threshold: 0.5773,
        is_anomaly: false
      }
    },
    predicted_168h: {
      Iddq_uA_168h: 13.85,
      Leakage_nA_168h: 635.4,
      PropDelay_ns_168h: 3.48
    },
    integrity_flag: false
  },
  history: [
    { stage: "0h", value: 13.3441, parameter: "Iddq_uA" },
    { stage: "0h", value: 516.5699, parameter: "Leakage_nA" },
    { stage: "0h", value: 3.3411, parameter: "PropDelay_ns" },
    { stage: "24h", value: 13.0153, parameter: "Iddq_uA" },
    { stage: "24h", value: 524.4931, parameter: "Leakage_nA" },
    { stage: "24h", value: 3.3662, parameter: "PropDelay_ns" },
    { stage: "96h", value: 12.9323, parameter: "Iddq_uA" },
    { stage: "96h", value: 554.4539, parameter: "Leakage_nA" },
    { stage: "96h", value: 3.3987, parameter: "PropDelay_ns" }
  ],
  safety: {
    prediction_risk: 78.5,
    s_score: 88.5,
    uncertainty_risk: 24.0,
    details: {
      Iddq_uA: {
        status: "WITHIN_LIMIT",
        engineering_limit_lower: 8.0,
        engineering_limit_upper: 20.0,
        envelope_lower: 11.0,
        envelope_upper: 16.5,
        predicted_168h: 13.85
      },
      Leakage_nA: {
        status: "APPROACHING_LIMIT",
        engineering_limit_lower: 400.0,
        engineering_limit_upper: 750.0,
        envelope_lower: 480.0,
        envelope_upper: 620.0,
        predicted_168h: 635.4
      },
      PropDelay_ns: {
        status: "WITHIN_LIMIT",
        engineering_limit_lower: 2.8,
        engineering_limit_upper: 4.0,
        envelope_lower: 3.2,
        envelope_upper: 3.6,
        predicted_168h: 3.48
      }
    }
  },
  b_models: {
    B0: {
      prediction: { Iddq_uA_168h: 13.62, Leakage_nA_168h: 588.3, PropDelay_ns_168h: 3.44, leakage: 588.3 },
      stage: "24h",
      available: true,
      status: "AVAILABLE",
      model_version: "v1.0.0",
      mode: "STRICT_BASELINE",
      safety_score_type: "QUANTILE_95",
      safety_score_calibrated: true,
      intervals: {
        Leakage_nA: { lower: 540.1, upper: 636.5 },
        Iddq_uA: { lower: 12.1, upper: 15.2 },
        PropDelay_ns: { lower: 3.32, upper: 3.56 }
      }
    },
    B1: {
      prediction: { Iddq_uA_168h: 13.75, Leakage_nA_168h: 595.8, PropDelay_ns_168h: 3.46, leakage: 595.8 },
      stage: "24h",
      available: true,
      status: "AVAILABLE",
      model_version: "v1.0.0",
      mode: "CONTEXTUAL",
      safety_score_type: "QUANTILE_95",
      safety_score_calibrated: true,
      intervals: {
        Leakage_nA: { lower: 548.0, upper: 642.0 },
        Iddq_uA: { lower: 12.3, upper: 15.4 },
        PropDelay_ns: { lower: 3.34, upper: 3.58 }
      }
    },
    "B2-Early": {
      prediction: { Iddq_uA_168h: 14.10, Leakage_nA_168h: 615.2, PropDelay_ns_168h: 3.49, leakage: 615.2 },
      stage: "0h",
      available: true,
      status: "AVAILABLE",
      model_version: "v1.0.0",
      mode: "EARLY_WARNING",
      safety_score_type: "QUANTILE_90",
      safety_score_calibrated: false,
      intervals: {
        Leakage_nA: { lower: 560.0, upper: 670.0 },
        Iddq_uA: { lower: 12.5, upper: 16.0 },
        PropDelay_ns: { lower: 3.35, upper: 3.62 }
      }
    },
    "B2-96h": {
      prediction: { Iddq_uA_168h: 13.85, Leakage_nA_168h: 635.4, PropDelay_ns_168h: 3.48, leakage: 635.4 },
      stage: "96h",
      available: true,
      status: "AVAILABLE",
      model_version: "v1.0.0",
      mode: "MID_BURNIN_REFINEMENT",
      safety_score_type: "QUANTILE_95",
      safety_score_calibrated: true,
      intervals: {
        Leakage_nA: { lower: 590.2, upper: 680.6 },
        Iddq_uA: { lower: 12.8, upper: 14.9 },
        PropDelay_ns: { lower: 3.40, upper: 3.55 }
      }
    }
  },
  predicted_168h: {
    leakage: 635.4,
    Iddq_uA: 13.85,
    Leakage_nA: 635.4,
    PropDelay_ns: 3.48,
    interval: [590.2, 680.6]
  },
  basis: {
    mode: "MID_BURNIN_REFINEMENT",
    b_model: "B2-96h",
    safety_score_type: "QUANTILE_95",
    safety_score_calibrated: true,
    model_version: "v1.0.0"
  },
  warnings: [
    "Projected 168h leakage approaches upper safety limit of 750 nA.",
    "Dynamic drift slope between 24h and 96h exceeds normal cohort median by 14.2%."
  ]
};

export const DEMO_EXPLAINABILITY_GLOBAL = {
  model_name: "CatBoost 96h Anomaly Classifier",
  global_importance: [
    { feature: "Leakage_nA_96h", mean_abs_shap: 0.3842, percentage: 28.4 },
    { feature: "Iddq_uA_96h", mean_abs_shap: 0.2415, percentage: 17.8 },
    { feature: "Early_Temporal_Drift", mean_abs_shap: 0.1980, percentage: 14.6 },
    { feature: "PropDelay_ns_96h", mean_abs_shap: 0.1542, percentage: 11.4 },
    { feature: "Peer_Residual_Score", mean_abs_shap: 0.1320, percentage: 9.7 },
    { feature: "PAT_ZScore_Leakage", mean_abs_shap: 0.1084, percentage: 8.0 },
    { feature: "Leakage_nA_24h", mean_abs_shap: 0.0712, percentage: 5.3 },
    { feature: "Iddq_uA_24h", mean_abs_shap: 0.0650, percentage: 4.8 }
  ]
};

export const DEMO_EXPLAINABILITY_COMPONENT = {
  component_id: "CMP_00173",
  lot_id: "LOT_PRED_TEST_01",
  predicted_status: "ANOMALY",
  anomaly_probability: 0.764,
  threshold: 0.50,
  base_value: 0.182,
  output_unit: "Probability",
  limit_analysis: {
    has_violations: true,
    assessments: [
      { key: "leakage_96h", parameter: "Leakage_nA", stage: "96h", value: 554.45, upper_limit: 750.0, status: "WITHIN_LIMIT" },
      { key: "iddq_96h", parameter: "Iddq_uA", stage: "96h", value: 12.93, upper_limit: 20.0, status: "WITHIN_LIMIT" },
      { key: "prop_delay_96h", parameter: "PropDelay_ns", stage: "96h", value: 3.40, upper_limit: 4.0, status: "WITHIN_LIMIT" },
      { key: "leakage_24h", parameter: "Leakage_nA", stage: "24h", value: 524.49, upper_limit: 750.0, status: "WITHIN_LIMIT" },
      { key: "iddq_24h", parameter: "Iddq_uA", stage: "24h", value: 13.02, upper_limit: 20.0, status: "WITHIN_LIMIT" },
      { key: "prop_delay_24h", parameter: "PropDelay_ns", stage: "24h", value: 3.37, upper_limit: 4.0, status: "WITHIN_LIMIT" },
      { key: "leakage_0h", parameter: "Leakage_nA", stage: "0h", value: 516.57, upper_limit: 750.0, status: "WITHIN_LIMIT" },
      { key: "iddq_0h", parameter: "Iddq_uA", stage: "0h", value: 13.34, upper_limit: 20.0, status: "WITHIN_LIMIT" },
      { key: "prop_delay_0h", parameter: "PropDelay_ns", stage: "0h", value: 3.34, upper_limit: 4.0, status: "WITHIN_LIMIT" }
    ]
  },
  top_positive_contributors: [
    { feature: "Early_Temporal_Drift", shap_value: 0.2845, actual_value: 0.3301 },
    { feature: "Leakage_nA_96h", shap_value: 0.1952, actual_value: 554.45 },
    { feature: "Peer_Residual_Score", shap_value: 0.1210, actual_value: 78.4 }
  ],
  top_negative_contributors: [
    { feature: "PropDelay_ns_96h", shap_value: -0.0640, actual_value: 3.40 },
    { feature: "Iddq_uA_0h", shap_value: -0.0425, actual_value: 13.34 }
  ],
  feature_values: {
    "Iddq_uA_0h": 13.3441,
    "Leakage_nA_0h": 516.5699,
    "PropDelay_ns_0h": 3.3411,
    "Iddq_uA_24h": 13.0153,
    "Leakage_nA_24h": 524.4931,
    "PropDelay_ns_24h": 3.3662,
    "Iddq_uA_96h": 12.9323,
    "Leakage_nA_96h": 554.4539,
    "PropDelay_ns_96h": 3.3987
  }
};

export const DEMO_GEMINI_AI_REPORT = {
  source: "Google Gemini (Grounded QA Engine)",
  executive_summary: "Component CMP_00173 exhibits significant early dynamic drift in Leakage Current between 24h and 96h burn-in intervals. While absolute 0h-96h measurements remain inside static engineering tolerances, the projected 168h trajectory approaches the critical safety envelope threshold, warranting QA engineering review.",
  risk_assessment: "ELEVATED FUTURE RISK — Multi-stage CatBoost classifier predicts a 76.4% anomaly probability driven primarily by dynamic temporal drift (+0.2845 SHAP contribution).",
  disposition_recommendation: "Hold component CMP_00173 for extended 168h validation screening before final lot release.",
  classification_explanation: "Component CMP_00173 is flagged with a 76.4% anomaly probability based on multi-stage CatBoost feature attribution. Primary risk drivers are accelerated dynamic leakage drift (+0.2845 SHAP) and elevated 96h leakage (+0.1952 SHAP).",
  key_contributing_factors: [
    "Early temporal leakage drift (+0.2845 SHAP contribution)",
    "Elevated 96h leakage current of 554.45 nA (+0.1952 SHAP contribution)",
    "Peer residual score elevation compared to adjacent units on Station ST_01"
  ],
  measurement_trends: "Leakage current accelerated upwards from 516.57 nA (0h) to 524.49 nA (24h) and 554.45 nA (96h). IDDQ current stabilized between 13.02 µA and 12.93 µA.",
  engineering_limit_assessment: "All static measurements remain within engineering tolerances (Leakage < 750 nA, IDDQ < 20 µA, Propagation Delay < 4.0 ns). The concern is rate-of-drift.",
  recommended_inspection_steps: [
    "Verify contact resistance on Station ST_01 socket CMP_00173.",
    "Perform secondary 168h bake test to observe stabilization or runaway leakage.",
    "Cross-validate against cohort median for Lot LOT_PRED_TEST_01."
  ],
  limitations: "Analysis based on 0h, 24h, and 96h telemetry. Unforeseen thermal spikes during extended 168h burn-in may alter trajectory.",
  key_findings: [
    "Leakage current accelerated from 524.49 nA (24h) to 554.45 nA (96h).",
    "Early temporal slope exceeds healthy reference baseline by +14.2%.",
    "Propagation delay and static IDDQ are nominal with negligible variance."
  ]
};

/**
 * Safe demo value resolver:
 * Checks if a backend value is valid (including legitimate 0, 0.0, false, non-empty strings).
 * If null, undefined, "", "N/A", "NA", "NULL", "UNAVAILABLE", "Not Available", returns fallback.
 */
export function resolveDemoVal(val, fallback) {
  if (val === 0 || val === false) return val;
  if (val === null || val === undefined) return fallback;
  if (typeof val === 'string') {
    const trimmed = val.trim();
    if (trimmed === '' || trimmed === 'N/A' || trimmed === 'NA' || trimmed === 'NULL' || trimmed === 'UNAVAILABLE' || trimmed === 'Not Available' || trimmed === 'No data available') {
      return fallback;
    }
  }
  return val;
}
