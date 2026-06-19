from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from services.finding_detector import normalize_key
from services.model_loader import ModelRegistry, PanelArtifacts


STRONG_CONFIDENCE = 0.60


def normalize_model_label(label: Any) -> str:
    """Normalize model labels so equivalent outputs like 'CBC Related' and 'cbc_related' compare safely."""
    text = str(label).strip().lower().replace(" ", "_")
    truthy_labels = {"1", "true", "yes"}
    return "cbc_related" if text in truthy_labels else text


def canonical_panel(panel: str) -> str:
    lookup = {
        "cbc": "CBC",
        "diabetes": "Diabetes",
        "kidney": "Kidney",
        "liver": "Liver",
        "thyroid": "Thyroid",
    }
    key = normalize_key(panel)
    if key not in lookup:
        raise ValueError(f"Unsupported panel: {panel}")
    return lookup[key]


def _input_lookup(values: dict[str, Any]) -> dict[str, Any]:
    lookup = {}
    aliases = {
        "blood_glucose": "fasting_glucose",
        "glucose": "fasting_glucose",
        "hba1c": "hba1c",
        "t3": "t3_ng_dl",
        "t4": "t4_ug_dl",
    }
    for key, value in values.items():
        normalized = normalize_key(key)
        lookup[normalized] = value
        if normalized in aliases:
            lookup[aliases[normalized]] = value
    return lookup


def _feature_frame(features: list[str], values: dict[str, Any], medians: dict[str, Any] | None = None) -> tuple[pd.DataFrame, list[str]]:
    lookup = _input_lookup(values)
    medians = medians or {}
    row: dict[str, float] = {}
    missing: list[str] = []
    for feature in features:
        key = normalize_key(feature)
        if key in lookup:
            row[feature] = float(lookup[key])
        elif feature in medians:
            row[feature] = float(medians[feature])
            missing.append(feature)
        elif key in medians:
            row[feature] = float(medians[key])
            missing.append(feature)
        else:
            row[feature] = 0.0
            missing.append(feature)
    return pd.DataFrame([row], columns=features), missing


def _decode_prediction(raw: Any, label_encoder: Any | None) -> str:
    value = raw.item() if hasattr(raw, "item") else raw
    if label_encoder is not None:
        try:
            return str(label_encoder.inverse_transform([int(value)])[0])
        except Exception:
            pass
    return str(value)


def _probabilities(model: Any, frame: pd.DataFrame, label_encoder: Any | None = None) -> tuple[float | None, list[dict[str, float]]]:
    if not hasattr(model, "predict_proba"):
        return None, []
    probs = np.asarray(model.predict_proba(frame))[0]
    classes = getattr(model, "classes_", range(len(probs)))
    items = []
    for cls, prob in zip(classes, probs):
        label = _decode_prediction(cls, label_encoder)
        items.append({"disease": label, "confidence": round(float(prob) * 100, 2)})
    return float(np.max(probs)), sorted(items, key=lambda item: item["confidence"], reverse=True)


def _raw_probability_map(predictions: list[dict[str, float]]) -> dict[str, float]:
    """Expose probabilities in debug mode without forcing clients to parse the ranked prediction list."""
    return {item["disease"]: item["confidence"] for item in predictions}


class PredictionService:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def predict(self, panel: str, values: dict[str, Any]) -> dict[str, Any]:
        panel = canonical_panel(panel)
        if panel == "CBC":
            return self._predict_cbc(values)
        artifacts = self.registry.get_panel(panel)
        if artifacts is None:
            error = self.registry.load_errors.get(panel.lower(), f"{panel} model is not loaded.")
            raise RuntimeError(error)
        return self._predict_standard(artifacts, values)

    def _predict_cbc(self, values: dict[str, Any]) -> dict[str, Any]:
        cbc = self.registry.cbc
        if cbc is None or cbc.stage1_model is None:
            raise RuntimeError(self.registry.load_errors.get("cbc", "CBC model is not loaded."))

        features = cbc.feature_columns or list(getattr(cbc.stage1_model, "feature_names_in_", []))
        frame, missing = _feature_frame(features, values, cbc.medians)
        stage1_raw_label = cbc.stage1_model.predict(frame)[0]
        stage1_label = normalize_model_label(stage1_raw_label)
        stage1_confidence, stage1_probs = _probabilities(cbc.stage1_model, frame)
        if stage1_confidence is None:
            stage1_confidence = 1.0

        result = {
            "panel": "CBC",
            "ml_status": "weak",
            "ml_disease": None,
            "ml_confidence": None,
            "predictions": [],
            "cbc_stage1": {"label": stage1_label, "confidence": round(stage1_confidence, 4), "probabilities": stage1_probs},
            "cbc_stage2": None,
            "missing_features_filled": missing,
            "raw_ml_probabilities": _raw_probability_map(stage1_probs),
        }

        if stage1_label != "cbc_related" or stage1_confidence < STRONG_CONFIDENCE:
            result["ml_status"] = "skipped_stage2"
            return result

        if cbc.stage2_model is None:
            raise RuntimeError("CBC stage 2 model is not loaded.")

        raw_prediction = cbc.stage2_model.predict(frame)[0]
        disease = _decode_prediction(raw_prediction, cbc.stage2_label_encoder)
        confidence, predictions = _probabilities(cbc.stage2_model, frame, cbc.stage2_label_encoder)
        result["ml_disease"] = disease
        result["ml_confidence"] = confidence
        result["ml_status"] = "strong" if confidence is None or confidence >= STRONG_CONFIDENCE else "weak"
        result["predictions"] = predictions or [{"disease": disease, "confidence": None}]
        result["raw_ml_probabilities"] = _raw_probability_map(predictions)
        result["cbc_stage2"] = {"disease": disease, "confidence": None if confidence is None else round(confidence, 4)}
        return result

    def _predict_standard(self, artifacts: PanelArtifacts, values: dict[str, Any]) -> dict[str, Any]:
        features = artifacts.feature_columns or list(getattr(artifacts.model, "feature_names_in_", []))
        frame, missing = _feature_frame(features, values, artifacts.medians)
        if artifacts.scaler is not None:
            # Scalers are trained with a fixed feature order, so enforce that order before transform.
            frame = frame[features]
            frame = pd.DataFrame(artifacts.scaler.transform(frame), columns=features)
        raw_prediction = artifacts.model.predict(frame)[0]
        disease = _decode_prediction(raw_prediction, artifacts.label_encoder)
        confidence, predictions = _probabilities(artifacts.model, frame, artifacts.label_encoder)
        return {
            "panel": artifacts.panel,
            "ml_status": "strong" if confidence is None or confidence >= STRONG_CONFIDENCE else "weak",
            "ml_disease": disease,
            "ml_confidence": confidence,
            "predictions": predictions or [{"disease": disease, "confidence": None}],
            "missing_features_filled": missing,
            "raw_ml_probabilities": _raw_probability_map(predictions),
        }
