from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent

# Load backend/.env before importing service modules that may read environment variables.
# This makes OPENROUTER_API_KEY available automatically when uvicorn starts.
load_dotenv(BASE_DIR / ".env")

from services.finding_detector import FindingDetector
from services.model_loader import ModelRegistry, PANEL_NAMES
from services.ontology_reasoner import OntologyReasoner
from services.prediction_service import PredictionService, canonical_panel
from services.response_builder import build_response


MODELS_DIR = BASE_DIR / "models"
RANGES_PATH = BASE_DIR / "data" / "normal_ranges.json"
ONTOLOGY_PATH = BASE_DIR / "ontology" / "lab_decision_support_ontology.owl"


class PredictRequest(BaseModel):
    panel: str = Field(..., description="One of: CBC, Diabetes, Kidney, Liver, Thyroid")
    values: dict[str, Any] = Field(default_factory=dict)


app = FastAPI(
    title="Hybrid Medical AI Clinical Decision Support API",
    version="1.0.0",
    description="ML prediction + finding detection + ontology reasoning + optional LLM explanation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


registry = ModelRegistry(MODELS_DIR)
predictor = PredictionService(registry)
finding_detector = FindingDetector(RANGES_PATH)
ontology_reasoner = OntologyReasoner(ONTOLOGY_PATH)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "models": registry.health(),
        "ontology_loaded": ontology_reasoner.available,
        "ontology_error": ontology_reasoner.load_error,
        "normal_ranges_loaded": RANGES_PATH.exists(),
    }


@app.get("/panels")
def panels() -> dict[str, Any]:
    return {
        "supported_panels": list(PANEL_NAMES),
        "normal_ranges": finding_detector.ranges,
        "model_artifacts": registry.health(),
    }


@app.post("/predict")
def predict(request: PredictRequest) -> dict[str, Any]:
    try:
        panel = canonical_panel(request.panel)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        ml_result = predictor.predict(panel, request.values)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    findings = finding_detector.detect(panel, request.values)
    ontology_result = ontology_reasoner.reason(findings, ml_result.get("ml_disease"), panel)
    ontology_support = ontology_reasoner.supports(ml_result.get("ml_disease"), findings, panel)
    return build_response(panel, ml_result, findings, ontology_result, ontology_support)
