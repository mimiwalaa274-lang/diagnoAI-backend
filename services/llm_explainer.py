from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")


def _get_openrouter_api_key() -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    return api_key or None


def _humanize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("_", " ")


def fallback_explanation(result: dict[str, Any]) -> str:
    ontology = result.get("ontology_explanation") or {}
    prediction = (result.get("predictions") or [{}])[0]

    disease = _humanize(
        ontology.get("disease")
        or prediction.get("disease")
        or "this condition"
    )

    findings = ontology.get("supporting_findings") or result.get("findings") or []
    tests = ontology.get("recommended_tests") or []
    action = ontology.get("recommended_action")

    findings_text = ", ".join(_humanize(item) for item in findings)
    tests_text = ", ".join(_humanize(item) for item in tests)

    explanation = "Your lab results show some values outside the normal range."

    if disease:
        explanation += f" These changes may suggest {disease}."

    if findings_text:
        explanation += f" The main changes found were: {findings_text}."

    if tests_text:
        explanation += (
            f" Your doctor may ask for follow-up tests such as {tests_text} "
            "to confirm the result."
        )

    if action:
        explanation += f" The next recommended step is {_humanize(action).lower()}."

    explanation += (
        " Please review these results with a qualified healthcare professional. "
        "This is not a final diagnosis."
    )

    return explanation


def generate_explanation(result: dict[str, Any]) -> str:
    api_key = _get_openrouter_api_key()

    if not api_key:
        logger.info("OpenRouter API key not found, using fallback explanations")
        return fallback_explanation(result)

    logger.info("OpenRouter API key loaded successfully")

    ontology = result.get("ontology_explanation") or {}
    prediction = (result.get("predictions") or [{}])[0]

    allowed_context = {
        "disease": ontology.get("disease") or prediction.get("disease"),
        "confidence": result.get("final_confidence") or prediction.get("confidence"),
        "findings": ontology.get("supporting_findings") or result.get("findings"),
        "recommended_tests": ontology.get("recommended_tests"),
        "specialist": ontology.get("specialist"),
        "urgency": ontology.get("urgency"),
        "recommended_action": ontology.get("recommended_action"),
    }

    prompt = (
        "Explain this clinical decision support result in very simple patient-friendly language. "
        "Use simple everyday English. "
        "Replace medical terms with simple explanations whenever possible. "
        "For example:- "
        "'High HbA1c' should become 'high long-term blood sugar levels'"
        "- 'Hyperglycemia' should become 'high blood sugar'- "
        "'Low Hemoglobin' should become 'low blood level that may indicate anemia'"
        "Do not use technical laboratory terms without explaining them simply. "
        "Use short and natural sentences. "
        "Make the explanation sound supportive and understandable for non-medical users. "
        "Never give a final diagnosis. "
        "Use phrases like 'may suggest' or 'could indicate'. "
        "Explain recommendations in a practical and human-friendly way. "
        "Do not sound robotic or overly scientific. "
        "Do not invent symptoms, diseases, treatments, or tests. "
        f"Use only this data: {allowed_context}"
    )

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You format safe, simple medical explanations for a "
                            "clinical decision support system. You do not diagnose."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "temperature": 0.2,
                "max_tokens": 180,
            },
            timeout=20,
        )

        response.raise_for_status()
        print("MODEL:", MODEL_NAME)
        print("STATUS: LLM CALL SUCCESS")
        return response.json()["choices"][0]["message"]["content"].strip()

    except Exception as exc:
        logger.warning(
            "OpenRouter explanation failed, using fallback explanation: %s",
            exc,
        )
        return fallback_explanation(result)
