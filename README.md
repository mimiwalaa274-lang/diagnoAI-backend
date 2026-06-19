# Hybrid Medical AI Clinical Decision Support Backend

FastAPI backend for hybrid clinical decision support:

- ML prediction
- abnormal finding detection from `data/normal_ranges.json`
- ontology fallback reasoning from `ontology/lab_decision_support_ontology.owl`
- optional OpenRouter explanation formatting

## Run

```bash
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## Optional LLM Explanation

The backend loads `OPENROUTER_API_KEY` automatically from a `.env` file in the `backend/` folder.

Create the file:

```bash
copy .env.example .env
```

Then edit `backend/.env`:

```text
OPENROUTER_API_KEY=your_api_key_here
```

Start the backend from the `backend/` folder:

```bash
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```

If the key is missing or the request fails, the backend returns a safe template explanation. The LLM only formats the structured result and is instructed not to diagnose or invent findings, tests, treatments, or symptoms.

To verify LLM formatting is active, add your key to `backend/.env`, restart uvicorn, call `POST /predict`, and check that `llm_explanation` is a natural generated explanation. If the key is missing or invalid, the field still returns a safe fallback explanation.

## Endpoints

- `GET /health`
- `GET /panels`
- `POST /predict`

Example:

```json
{
  "panel": "CBC",
  "values": {
    "hemoglobin": 9.5,
    "wbc": 7000,
    "rbc": 4.1,
    "hematocrit": 32,
    "mcv": 70,
    "mch": 24,
    "mchc": 31,
    "lymp_abs": 2.0,
    "neut_abs": 4.5
  }
}
```
