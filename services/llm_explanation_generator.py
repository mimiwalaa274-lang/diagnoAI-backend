import os
import requests


# =========================
# 1) OpenRouter Settings
# =========================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_NAME = "mistralai/mistral-7b-instruct"


# =========================
# 2) Prompt Builder
# =========================

def build_medical_prompt(
    disease: str,
    confidence: float,
    findings: list,
    recommended_tests: list,
    specialist: str,
    urgency: str
) -> str:
    findings_text = ", ".join(findings) if findings else "No clear findings available"
    tests_text = ", ".join(recommended_tests) if recommended_tests else "No additional tests available"

    prompt = f"""
You are a medical explanation assistant.

Important rules:
- Do NOT give a final diagnosis.
- Use phrases like "may indicate" or "could suggest".
- Keep the explanation short and simple.
- Base the explanation only on the provided disease, findings, tests, specialist, and urgency.
- Do not invent new symptoms, diseases, or treatments.

Disease candidate:
{disease}

Model confidence:
{confidence}%

Supporting findings:
{findings_text}

Recommended confirmatory tests:
{tests_text}

Suggested specialist:
{specialist}

Urgency level:
{urgency}

Generate a patient-friendly explanation in English.
"""
    return prompt


# =========================
# 3) LLM Explanation Function
# =========================

def generate_llm_explanation(
    disease: str,
    confidence: float,
    findings: list,
    recommended_tests: list,
    specialist: str,
    urgency: str
) -> str:

    if not OPENROUTER_API_KEY:
        return "LLM explanation unavailable: OPENROUTER_API_KEY is not set."

    prompt = build_medical_prompt(
        disease=disease,
        confidence=confidence,
        findings=findings,
        recommended_tests=recommended_tests,
        specialist=specialist,
        urgency=urgency
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You generate safe, short medical explanations for a clinical decision support system."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 180
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.RequestException as e:
        return f"LLM request failed: {e}"

    except KeyError:
        return "LLM response format error."


# =========================
# 4) Test Example
# =========================

if __name__ == "__main__":

    disease = "Iron Deficiency Anemia"
    confidence = 82.5

    findings = [
        "Low Hemoglobin",
        "Low MCV",
        "High RDW"
    ]

    recommended_tests = [
        "Ferritin",
        "Serum Iron",
        "TIBC",
        "Peripheral Smear"
    ]

    specialist = "Hematologist"
    urgency = "Soon"

    explanation = generate_llm_explanation(
        disease=disease,
        confidence=confidence,
        findings=findings,
        recommended_tests=recommended_tests,
        specialist=specialist,
        urgency=urgency
    )

    print(explanation)