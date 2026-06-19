from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib


PANEL_NAMES = ("CBC", "Diabetes", "Kidney", "Liver", "Thyroid")


@dataclass
class PanelArtifacts:
    panel: str
    root: Path
    model: Any | None = None
    scaler: Any | None = None
    label_encoder: Any | None = None
    feature_columns: list[str] = field(default_factory=list)
    medians: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)


@dataclass
class CBCArtifacts:
    root: Path
    stage1_model: Any | None = None
    stage2_model: Any | None = None
    stage2_label_encoder: Any | None = None
    feature_columns: list[str] = field(default_factory=list)
    medians: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)


class ModelRegistry:
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.cbc: CBCArtifacts | None = None
        self.panels: dict[str, PanelArtifacts] = {}
        self.load_errors: dict[str, str] = {}
        self._discover()

    def _discover(self) -> None:
        self.cbc = self._load_cbc()
        for panel in ("Diabetes", "Kidney", "Liver", "Thyroid"):
            try:
                self.panels[panel.lower()] = self._load_panel(panel)
            except Exception as exc:
                self.load_errors[panel.lower()] = str(exc)

    def _find_panel_root(self, panel: str) -> Path | None:
        target = panel.lower()
        for directory in self.models_dir.rglob("*"):
            if directory.is_dir() and target in directory.name.lower():
                return directory
        return None

    def _load_cbc(self) -> CBCArtifacts | None:
        cbc_files = list(self.models_dir.rglob("cbc_stage1_model.joblib"))
        if not cbc_files:
            self.load_errors["cbc"] = "CBC stage 1 model was not found."
            return None

        root = cbc_files[0].parent
        artifacts = CBCArtifacts(root=root)
        expected = {
            "stage1_model": "cbc_stage1_model.joblib",
            "stage2_model": "cbc_stage2_model.joblib",
            "stage2_label_encoder": "cbc_stage2_label_encoder.joblib",
            "feature_columns": "cbc_feature_columns.joblib",
            "medians": "cbc_feature_medians.joblib",
            "metadata": "cbc_model_metadata.json",
        }
        for key, filename in expected.items():
            path = root / filename
            if not path.exists():
                self.load_errors["cbc"] = f"Missing CBC artifact: {filename}"
                continue
            artifacts.artifact_paths[key] = str(path)
            if path.suffix == ".json":
                setattr(artifacts, key, json.loads(path.read_text(encoding="utf-8")))
            else:
                setattr(artifacts, key, joblib.load(path))

        if not artifacts.feature_columns and artifacts.metadata.get("feature_columns"):
            artifacts.feature_columns = list(artifacts.metadata["feature_columns"])
        return artifacts

    def _load_panel(self, panel: str) -> PanelArtifacts:
        root = self._find_panel_root(panel)
        if root is None:
            raise FileNotFoundError(f"No model folder found for {panel}.")

        artifacts = PanelArtifacts(panel=panel, root=root)
        candidates = list(root.rglob("*.joblib"))
        if not candidates:
            raise FileNotFoundError(f"No joblib artifacts found for {panel}.")

        for path in candidates:
            lower = path.name.lower()
            obj = joblib.load(path)
            artifacts.artifact_paths[path.stem] = str(path)
            if "label" in lower and "encoder" in lower:
                artifacts.label_encoder = obj
            elif "scaler" in lower:
                artifacts.scaler = obj
            elif "feature" in lower and isinstance(obj, (list, tuple)):
                artifacts.feature_columns = [str(item) for item in obj]
            elif "median" in lower and isinstance(obj, dict):
                artifacts.medians = obj
            elif hasattr(obj, "predict"):
                if artifacts.model is None or "best" in lower or "model" in lower:
                    artifacts.model = obj

        for path in root.rglob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            artifacts.metadata.update(data)
            artifacts.artifact_paths[path.stem] = str(path)

        if artifacts.model is None:
            raise FileNotFoundError(f"No predictive model artifact found for {panel}.")

        if not artifacts.feature_columns:
            meta_features = artifacts.metadata.get("features") or artifacts.metadata.get("feature_columns")
            if meta_features:
                artifacts.feature_columns = [str(item) for item in meta_features]
            elif hasattr(artifacts.model, "feature_names_in_"):
                artifacts.feature_columns = [str(item) for item in artifacts.model.feature_names_in_]

        return artifacts

    def get_panel(self, panel: str) -> PanelArtifacts | None:
        return self.panels.get(panel.lower())

    def health(self) -> dict[str, Any]:
        loaded = {"CBC": self.cbc is not None}
        loaded.update({name: key in self.panels for name, key in [(p, p.lower()) for p in PANEL_NAMES if p != "CBC"]})
        return {
            "models_dir": str(self.models_dir),
            "loaded_panels": loaded,
            "errors": self.load_errors,
        }
