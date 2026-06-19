from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from owlready2 import ThingClass, get_ontology


SUPPORT_PROPERTIES = {
    "findingSuggestsDisease",
    "diseaseSuggestedByFinding",
}
RECOMMENDATION_PROPERTIES = {
    "diseaseRequiresTest": "recommended_tests",
    "diseaseTreatedBy": "specialist",
    "diseaseHasUrgency": "urgency",
    "diseaseHasAction": "recommended_action",
}

# Critical findings add more evidence than generic abnormalities. Findings not listed here use 1.0.
CRITICAL_FINDING_WEIGHTS = {
    "Low_Hemoglobin": 3.0,
    "High_WBC": 2.5,
    "Low_eGFR": 3.0,
    "High_HbA1c": 3.0,
    "Hyperglycemia": 2.5,
    "Thrombocytopenia": 2.0,
}
STRONG_ONTOLOGY_RATIO = 0.60


def norm_name(value: str | None) -> str:
    return (value or "").strip().lower().replace(" ", "_")


def _entity_name(entity: Any) -> str | None:
    return getattr(entity, "name", None)


class OntologyReasoner:
    def __init__(self, ontology_path: Path):
        self.ontology_path = ontology_path
        self.ontology: Any | None = None
        self.available = False
        self.load_error: str | None = None
        self.finding_to_diseases: dict[str, set[str]] = defaultdict(set)
        self.disease_findings: dict[str, set[str]] = defaultdict(set)
        self.recommendations: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "recommended_tests": [],
                "specialist": None,
                "urgency": None,
                "recommended_action": None,
            }
        )
        self.disease_index: dict[str, str] = {}
        self.finding_names: set[str] = set()
        self.disease_names: set[str] = set()

        try:
            # Safer loading keeps FastAPI alive even when the OWL file is missing or malformed.
            self.ontology = get_ontology(str(ontology_path)).load()
            self.available = True
            self._build_indexes()
        except Exception as exc:
            self.load_error = str(exc)

    def _is_subclass_named(self, cls: Any, parent_name: str) -> bool:
        try:
            return any(getattr(parent, "name", None) == parent_name for parent in cls.ancestors())
        except Exception:
            return False

    def _walk_expressions(self, expressions: list[Any]) -> list[Any]:
        """Flatten equivalent-class intersections/unions so nested restrictions are not missed."""
        output: list[Any] = []
        for expr in expressions:
            output.append(expr)
            nested = getattr(expr, "Classes", None)
            if nested:
                output.extend(self._walk_expressions(list(nested)))
        return output

    def _restriction_parts(self, expr: Any) -> tuple[str | None, str | None]:
        prop_name = _entity_name(getattr(expr, "property", None))
        value = getattr(expr, "value", None)
        value_name = _entity_name(value)
        return prop_name, value_name

    def _add_recommendation(self, disease: str, prop_name: str, value_name: str) -> None:
        field = RECOMMENDATION_PROPERTIES[prop_name]
        if field == "recommended_tests":
            if value_name not in self.recommendations[disease][field]:
                self.recommendations[disease][field].append(value_name)
        else:
            self.recommendations[disease][field] = value_name

    def _add_support(self, finding: str, disease: str) -> None:
        self.finding_to_diseases[finding].add(disease)
        self.disease_findings[disease].add(finding)

    def _build_indexes(self) -> None:
        if self.ontology is None:
            return

        classes = list(self.ontology.classes())
        for cls in classes:
            if not isinstance(cls, ThingClass):
                continue
            if self._is_subclass_named(cls, "Finding"):
                self.finding_names.add(cls.name)
            if self._is_subclass_named(cls, "Disease_Candidate"):
                self.disease_names.add(cls.name)
                self.disease_index[norm_name(cls.name)] = cls.name

        for cls in classes:
            name = cls.name
            self.disease_index.setdefault(norm_name(name), name)
            expressions = self._walk_expressions(list(cls.is_a) + list(cls.equivalent_to))

            for expr in expressions:
                prop_name, value_name = self._restriction_parts(expr)
                if not prop_name or not value_name:
                    continue

                # Read both directions of explicit finding-to-disease ontology restrictions.
                if prop_name in SUPPORT_PROPERTIES:
                    if prop_name == "findingSuggestsDisease":
                        self._add_support(name, value_name)
                    else:
                        self._add_support(value_name, name)

                # Read recommendation restrictions from disease classes.
                if prop_name in RECOMMENDATION_PROPERTIES and name in self.disease_names:
                    self._add_recommendation(name, prop_name, value_name)

                # Equivalent disease rules often appear as restrictions whose values are findings.
                if name in self.disease_names and value_name in self.finding_names:
                    self._add_support(value_name, name)

    def canonical_disease(self, disease: str | None, panel: str | None = None) -> str | None:
        if not disease:
            return None
        key = norm_name(disease)
        if key in self.disease_index:
            return self.disease_index[key]
        panel_key = norm_name(panel)
        panel_aliases = {
            ("kidney", "normal"): "Normal_Kidney_Function",
            ("liver", "normal"): "Normal_Liver_Function",
            ("thyroid", "normal"): "Normal_Thyroid_Function",
            ("cbc", "healthy"): "Healthy",
        }
        if (panel_key, key) in panel_aliases:
            return panel_aliases[(panel_key, key)]

        aliases = {
            "diabetes": "Type_2_Diabetes",
            "healthy": "Healthy_Diabetes_Status",
            "normal_liver_profile": "Normal_Liver_Function",
            "possible_mild_liver_dysfunction": "Mild_Liver_Dysfunction",
            "possible_severe_liver_dysfunction": "Severe_Liver_Dysfunction",
            "kidney_damage_risk": "Chronic_Kidney_Disease",
            "reduced_kidney_function": "Mild_Kidney_Dysfunction",
            "normal_kidney_function": "Normal_Kidney_Function",
            "infection": "Infection",
            "leukemia_risk": "Leukemia_Risk",
            "thrombocytopenia": "Platelet_Disorder",
            "anemia": "Anemia_Other",
        }
        return aliases.get(key) or self.disease_index.get(key.title().replace(" ", "_").lower())

    def _candidate_detail(self, disease: str, matched: set[str]) -> dict[str, Any]:
        required = self.disease_findings.get(disease, set())
        total_required = len(required) or len(matched)
        matching_ratio = (len(matched) / total_required) if total_required else 0.0
        weighted_score = sum(CRITICAL_FINDING_WEIGHTS.get(finding, 1.0) for finding in matched)
        return {
            "disease": disease,
            "supporting_findings": sorted(matched),
            "matched_findings_count": len(matched),
            "total_required_findings": total_required,
            "matching_ratio": round(matching_ratio, 4),
            "weighted_score": round(weighted_score, 4),
            "strong_support": matching_ratio >= STRONG_ONTOLOGY_RATIO,
        }

    def reason(self, findings: list[str], ml_disease: str | None = None, panel: str | None = None) -> dict[str, Any] | None:
        if not self.available:
            return None

        matched_by_disease: dict[str, set[str]] = defaultdict(set)
        for finding in findings:
            for disease in self.finding_to_diseases.get(finding, set()):
                matched_by_disease[disease].add(finding)

        ml_canonical = self.canonical_disease(ml_disease, panel)
        if ml_canonical and ml_canonical in self.disease_names:
            matched_by_disease.setdefault(ml_canonical, set()).update(
                set(findings).intersection(self.disease_findings.get(ml_canonical, set()))
            )

        if not matched_by_disease:
            return None

        candidates = [self._candidate_detail(disease, matched) for disease, matched in matched_by_disease.items()]
        candidates.sort(
            key=lambda item: (
                item["strong_support"],
                item["weighted_score"],
                item["matching_ratio"],
                item["disease"] == ml_canonical,
            ),
            reverse=True,
        )

        # Prefer the ML disease only when ontology evidence is strong enough; otherwise keep the strongest ontology candidate.
        selected = candidates[0]
        if ml_canonical:
            ml_candidate = next((item for item in candidates if item["disease"] == ml_canonical), None)
            if ml_candidate and ml_candidate["strong_support"]:
                selected = ml_candidate

        rec = self.recommendations.get(selected["disease"], {})
        return {
            "disease": selected["disease"],
            "supporting_findings": selected["supporting_findings"],
            "matched_findings_count": selected["matched_findings_count"],
            "total_required_findings": selected["total_required_findings"],
            "matching_ratio": selected["matching_ratio"],
            "weighted_score": selected["weighted_score"],
            "recommended_tests": rec.get("recommended_tests", []),
            "specialist": rec.get("specialist"),
            "urgency": rec.get("urgency"),
            "recommended_action": rec.get("recommended_action"),
            "candidate_scores": candidates,
        }

    def supports(self, ml_disease: str | None, findings: list[str], panel: str | None = None) -> dict[str, Any]:
        """Return detailed ontology validation for the ML disease instead of a lossy boolean."""
        if not self.available:
            return {
                "supported": False,
                "matching_ratio": 0.0,
                "matched_findings": 0,
                "required_findings": 0,
                "ontology_available": False,
                "error": self.load_error,
            }

        canonical = self.canonical_disease(ml_disease, panel)
        if not canonical:
            return {
                "supported": False,
                "matching_ratio": 0.0,
                "matched_findings": 0,
                "required_findings": 0,
                "ontology_available": True,
            }

        required = self.disease_findings.get(canonical, set())
        matched = set(findings).intersection(required)
        total_required = len(required)
        ratio = (len(matched) / total_required) if total_required else 0.0
        return {
            "supported": ratio >= STRONG_ONTOLOGY_RATIO,
            "matching_ratio": round(ratio, 4),
            "matched_findings": len(matched),
            "required_findings": total_required,
            "matched_finding_names": sorted(matched),
            "ontology_available": True,
            "disease": canonical,
        }
