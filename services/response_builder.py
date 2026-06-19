from __future__ import annotations

import os
from typing import Any

from services.llm_explainer import generate_explanation
from services.recommendation_engine import decide_reasoning_mode


DISCLAIMER = "This system is for clinical decision support only and does not provide a final diagnosis."


def _percent(value: float | None) -> float | None:
    """Prediction services keep ML confidence as 0-1 internally; API responses expose percentages."""
    if value is None:
        return None
    return round(float(value) * 100, 2)


def _ontology_confidence(ontology_result: dict[str, Any] | None) -> float | None:
    if not ontology_result:
        return None
    return round(float(ontology_result.get("matching_ratio", 0.0)) * 100, 2)


def _final_confidence(ml_confidence: float | None, ontology_confidence: float | None) -> float | None:
    """Blend ML and ontology confidence while gracefully handling missing sources."""
    if ml_confidence is None and ontology_confidence is None:
        return None
    if ml_confidence is None:
        return ontology_confidence
    if ontology_confidence is None:
        return ml_confidence
    return round((ml_confidence * 0.7) + (ontology_confidence * 0.3), 2)


def build_response(
    panel: str,
    ml_result: dict[str, Any],
    findings: list[str],
    ontology_result: dict[str, Any] | None,
    ontology_support: dict[str, Any],
) -> dict[str, Any]:
    reasoning_mode, warnings = decide_reasoning_mode(ml_result, ontology_result, ontology_support)
    ml_confidence = _percent(ml_result.get("ml_confidence"))
    ontology_confidence = _ontology_confidence(ontology_result)
    final_confidence = _final_confidence(ml_confidence, ontology_confidence)

    if reasoning_mode == "conflicting_evidence":
        warnings.append("Conflicting evidence: ML prediction is not strongly supported by ontology findings.")

    response = {
        "panel": panel,
        "ml_status": ml_result.get("ml_status"),
        "reasoning_mode": reasoning_mode,
        "ml_confidence": ml_confidence,
        "ontology_confidence": ontology_confidence,
        "final_confidence": final_confidence,
        "cbc_stage1": ml_result.get("cbc_stage1"),
        "cbc_stage2": ml_result.get("cbc_stage2"),
        "predictions": ml_result.get("predictions", []),
        "findings": findings,
        "ontology_explanation": ontology_result,
        "warnings": warnings,
        "missing_features_filled": ml_result.get("missing_features_filled", []),
        "disclaimer": DISCLAIMER,
    }
    if os.getenv("DEBUG_REASONING", "").strip().lower() == "true":
        candidates = (ontology_result or {}).get("candidate_scores", [])
        response["debug"] = {
            "ontology_candidates": candidates,
            "weighted_scores": {item["disease"]: item.get("weighted_score") for item in candidates},
            "match_ratios": {item["disease"]: item.get("matching_ratio") for item in candidates},
            "ontology_support_for_ml": ontology_support,
            "raw_ml_probabilities": ml_result.get("raw_ml_probabilities", {}),
        }
    response["llm_explanation"] = generate_explanation(response)
    return response
