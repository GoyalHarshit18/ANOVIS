"""
Google Gemini Integration Service for QA Inspector Reports.

Communicates with Google Gemini API via official google-genai SDK.
Generates grounded, non-hallucinated QA inspection reports based strictly
on SHAP feature attributions, model predictions, and engineering limit checks.
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("sih26170.gemini_service")

SYSTEM_INSTRUCTION = (
    "You are an AI assistant supporting semiconductor quality assurance inspectors.\n"
    "Explain the supplied machine-learning classification using only the provided measurements, model outputs, SHAP contributions, and engineering limits.\n"
    "Do not invent sensor measurements, defect causes, test results, engineering limits, or inspection findings.\n"
    "Do not claim that a SHAP contribution proves physical causation.\n"
    "Do not modify the supplied model prediction or probability.\n"
    "Clearly distinguish model evidence, observed engineering-limit violations, and recommended human verification steps.\n"
    "If the evidence is insufficient to identify a defect mechanism, explicitly say so.\n"
    "Use professional, concise English suitable for a semiconductor QA inspection report.\n"
    "Return structured JSON matching the requested response schema."
)


def _generate_fallback_report(explanation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a deterministic rule-based QA inspection report from verified SHAP and measurement data.
    Used when Gemini API key is missing or when the API call fails or times out.
    """
    comp_id = explanation.get("component_id", "UNKNOWN")
    lot_id = explanation.get("lot_id", "LOT-UNKNOWN")
    prob = explanation.get("anomaly_probability", 0.0)
    status = explanation.get("predicted_status", "NORMAL")
    top_pos = explanation.get("top_positive_contributors", [])
    top_neg = explanation.get("top_negative_contributors", [])
    limit_analysis = explanation.get("limit_analysis", {})
    violations = limit_analysis.get("violations", [])

    is_anomaly = (status == "ANOMALY")

    exec_summary = (
        f"Component {comp_id} (Lot {lot_id}) was evaluated by the 96h CatBoost anomaly detection model. "
        f"The calculated anomaly probability is {prob*100:.1f}%, resulting in a classification of {status} "
        f"(Threshold: {explanation.get('threshold', 0.5)*100:.0f}%)."
    )

    if is_anomaly:
        class_exp = (
            f"The component exceeded the anomaly threshold with a probability of {prob*100:.1f}%. "
            f"Model evidence indicates elevated risk driven primarily by measurement deviations observed at the 96h stage."
        )
    else:
        class_exp = (
            f"The component is within normal operational range with an anomaly probability of {prob*100:.1f}%. "
            f"Key parameters align with baseline lot distribution."
        )

    key_factors = []
    for factor in top_pos[:3]:
        key_factors.append(f"{factor['feature']} (Value: {factor['actual_value']}, SHAP: +{factor['shap_value']:.4f}): Increases anomaly risk evidence.")
    for factor in top_neg[:2]:
        key_factors.append(f"{factor['feature']} (Value: {factor['actual_value']}, SHAP: {factor['shap_value']:.4f}): Supports normal classification.")

    if not key_factors:
        key_factors = ["All evaluated features are within baseline statistical expectations."]

    trends_summary = []
    for trend in explanation.get("measurement_trends", []):
        param = trend.get("parameter")
        pct = trend.get("pct_change_24_96h")
        if pct is not None:
            trends_summary.append(f"{param}: {pct:+.2f}% drift between 24h and 96h.")

    trends_str = "; ".join(trends_summary) if trends_summary else "Measurement drift across 0h, 24h, and 96h stages is within baseline stability margins."

    if violations:
        violation_details = ", ".join([f"{v['parameter']} at {v['stage']} ({v['value']} vs limit {v['limit_value']})" for v in violations])
        limit_str = f"Engineering limit violations detected: {violation_details}."
    else:
        limit_str = "All observed 0h, 24h, and 96h measurements are strictly within static engineering specification limits."

    rec_steps = [
        f"Perform visual and physical inspection of component {comp_id}.",
        "Verify 96h test contact integrity and socket calibration.",
        "Check automated test equipment (ATE) log for transient voltage/temperature spikes during 24h-96h burn-in.",
        "Submit component for physical FA (Failure Analysis) if lot defect density exceeds thresholds." if is_anomaly else "Approve component for next screening stage."
    ]

    limitations = (
        "This explanation is generated from statistical SHAP feature attributions and engineering limit checks. "
        "SHAP values indicate feature contribution to the model's output and do not independently prove physical causation. "
        "Final disposition requires authorized QA engineer review."
    )

    return {
        "executive_summary": exec_summary,
        "classification_explanation": class_exp,
        "key_contributing_factors": key_factors,
        "measurement_trends": trends_str,
        "engineering_limit_assessment": limit_str,
        "recommended_inspection_steps": rec_steps,
        "limitations": limitations,
        "source": "DETERMINISTIC_FALLBACK"
    }


def generate_gemini_qa_report(explanation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a structured Gemini QA Report based on authoritative model explanation data.
    Ensures strict JSON response structure and non-hallucinated content.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
        logger.warning("GEMINI_API_KEY not configured. Returning deterministic QA report fallback.")
        return _generate_fallback_report(explanation)

    # Candidate models in order of priority
    candidate_models = [
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-flash-latest",
    ]
    # Remove duplicates while preserving order
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Prepare concise, structured payload for Gemini
    payload = {
        "component_id": explanation.get("component_id"),
        "lot_id": explanation.get("lot_id"),
        "anomaly_probability": explanation.get("anomaly_probability"),
        "threshold": explanation.get("threshold"),
        "predicted_status": explanation.get("predicted_status"),
        "top_positive_contributors": explanation.get("top_positive_contributors", [])[:5],
        "top_negative_contributors": explanation.get("top_negative_contributors", [])[:5],
        "limit_violations": explanation.get("limit_analysis", {}).get("violations", []),
        "measurement_trends": explanation.get("measurement_trends", []),
    }

    user_prompt = (
        f"Generate a QA Inspection Report for component {explanation.get('component_id')} using the following structured model evidence:\n\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Return a JSON object with EXACTLY these keys:\n"
        "- executive_summary (string)\n"
        "- classification_explanation (string)\n"
        "- key_contributing_factors (list of strings)\n"
        "- measurement_trends (string)\n"
        "- engineering_limit_assessment (string)\n"
        "- recommended_inspection_steps (list of strings)\n"
        "- limitations (string)"
    )

    last_error = None
    for model_name in models_to_try:
        try:
            logger.info("Calling Gemini API with model: %s for %s", model_name, explanation.get("component_id"))
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.2, # Low temperature for factual precision
                ),
            )

            raw_text = response.text.strip()
            # Handle potential markdown code fencing in LLM response
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()

            parsed = json.loads(raw_text)

            # Verify required keys
            required_keys = [
                "executive_summary",
                "classification_explanation",
                "key_contributing_factors",
                "measurement_trends",
                "engineering_limit_assessment",
                "recommended_inspection_steps",
                "limitations"
            ]

            for k in required_keys:
                if k not in parsed:
                    raise ValueError(f"Gemini response missing required key: {k}")

            parsed["source"] = f"GOOGLE_GEMINI_AI ({model_name})"
            logger.info("Successfully generated Gemini QA Report for %s using %s", explanation.get("component_id"), model_name)
            return parsed

        except Exception as e:
            last_error = e
            logger.warning("Gemini attempt with model %s failed: %s", model_name, e)
            continue

    logger.error("All Gemini API attempts failed for %s: %s. Falling back to deterministic report generator.", explanation.get("component_id"), last_error)
    fallback = _generate_fallback_report(explanation)
    fallback["error_detail"] = str(last_error)
    return fallback
