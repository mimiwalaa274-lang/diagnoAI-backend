from __future__ import annotations

from services.ontology_reasoner import STRONG_ONTOLOGY_RATIO
from services.prediction_service import STRONG_CONFIDENCE


def decide_reasoning_mode(ml_result: dict, ontology_result: dict | None, ontology_support: dict) -> tuple[str, list[str]]:
    warnings: list[str] = []
    ml_status = ml_result.get("ml_status")
    ml_confidence = ml_result.get("ml_confidence")
    ml_is_strong = ml_status == "strong" and (ml_confidence is None or ml_confidence >= STRONG_CONFIDENCE)
    ontology_is_available = ontology_support.get("ontology_available", True)
    ontology_is_strong = bool(ontology_result) and ontology_support.get("supported", False)
    best_ratio = (ontology_result or {}).get("matching_ratio", 0.0)

    if ml_status == "skipped_stage2":
        if not ontology_is_available:
            warnings.append("Ontology unavailable; CBC stage 2 was skipped and fallback reasoning is limited.")
        return "ontology_only_fallback", warnings

    if ml_result.get("missing_features_filled"):
        warnings.append("Some missing features were filled with medians or safe defaults.")

    if ml_status == "weak":
        warnings.append("ML confidence is below the strong-confidence threshold.")

    if not ontology_is_available:
        warnings.append("Ontology unavailable; using model output and detected findings only.")

    if not ontology_result:
        warnings.append("No clear ontology disease match found.")
        return "no_clear_match", warnings

    if best_ratio < STRONG_ONTOLOGY_RATIO:
        warnings.append("Ontology support is weak because too few required findings matched.")

    if ml_is_strong and ontology_is_strong:
        return "ml_plus_ontology_agreement", warnings

    if not ml_is_strong and best_ratio >= STRONG_ONTOLOGY_RATIO:
        return "weak_ml_strong_ontology", warnings

    if ml_is_strong and not ontology_support.get("supported", False):
        if ontology_result.get("disease") != ontology_support.get("disease"):
            warnings.append("Conflicting evidence: ontology candidate differs from the ML prediction.")
        if best_ratio > 0:
            return "weak_ontology_support", warnings
        warnings.append("ML and ontology evidence point to different candidates.")
        return "conflicting_evidence", warnings

    return "weak_ontology_support", warnings
