from owlready2 import *
from pathlib import Path

print("Script started...")

BASE_DIR = Path(__file__).parent

ONTO_PATH = BASE_DIR / "medical_lab_ontology.owl"

if not ONTO_PATH.exists():
    raise FileNotFoundError(f"Ontology file not found: {ONTO_PATH}")

onto_path.append(str(BASE_DIR))

onto = get_ontology(str(ONTO_PATH)).load(only_local=True)

print("Ontology loaded successfully")

def find_imported_class(code):

    entity = default_world.search_one(iri=f"*{code}")

    if entity is None:
        print(f"Not found in imports: {code}")

    return entity


def add_parent(child_name, parent_class):
    child = getattr(onto, child_name, None)
    if child:
        if parent_class not in child.is_a:
            child.is_a.append(parent_class)
    else:
        print("Missing class:", child_name)


def add_equivalent_rule(disease_name, findings):
    disease = getattr(onto, disease_name, None)
    if not disease:
        print("Missing disease:", disease_name)
        return

    expr = onto.DiseaseCandidate

    for finding_name in findings:
        finding = getattr(onto, finding_name, None)
        if finding:
            expr = expr & onto.diseaseIndicatedByFinding.some(finding)
        else:
            print("Missing finding:", finding_name)

    disease.equivalent_to.append(expr)


def add_hpo_mapping(finding_name, hpo_code):

    finding = getattr(onto, finding_name, None)
    hpo_class = find_imported_class(hpo_code)

    if finding is None:
        print(f"Missing finding: {finding_name}")
        return

    if hpo_class is None:
        return

    if hpo_class not in finding.is_a:
        finding.is_a.append(hpo_class)

    print(f"Mapped {finding_name} -> {hpo_code}")


def add_doid_mapping(disease_name, doid_code):

    disease = getattr(onto, disease_name, None)
    doid_class = find_imported_class(doid_code)

    if disease is None:
        print(f"Missing disease: {disease_name}")
        return

    if doid_class is None:
        return

    if doid_class not in disease.is_a:
        disease.is_a.append(doid_class)

    print(f"Mapped {disease_name} -> {doid_code}")

with onto:

    # =========================
    # 1) FINDING HIERARCHY
    # =========================

    class CBC_Finding(onto.Finding): pass
    class Liver_Finding(onto.Finding): pass
    class Kidney_Finding(onto.Finding): pass
    class Diabetes_Finding(onto.Finding): pass
    class Thyroid_Finding(onto.Finding): pass
    class Inflammatory_Finding(onto.Finding): pass
    class Iron_Profile_Finding(onto.Finding): pass

    cbc_findings = [
        "Low_Hemoglobin", "High_Hemoglobin",
        "Low_RBC", "High_RBC",
        "Low_WBC", "High_WBC",
        "Low_Platelets", "High_Platelets",
        "Low_MCV", "High_MCV",
        "Low_MCH", "High_MCH",
        "Low_MCHC", "High_MCHC",
        "High_RDW",
        "Low_Neutrophils", "High_Neutrophils",
        "Low_Lymphocytes", "High_Lymphocytes",
        "High_Eosinophils", "High_Monocytes", "High_Basophils"
    ]

    liver_findings = [
        "High_ALT", "High_AST", "High_ALP",
        "High_Bilirubin", "Low_Albumin", "High_GGT"
    ]

    kidney_findings = [
        "High_Creatinine", "High_BUN", "Low_eGFR", "High_Uric_Acid"
    ]

    diabetes_findings = [
        "High_Fasting_Glucose", "High_Random_Glucose",
        "High_HbA1c", "Low_Glucose"
    ]

    thyroid_findings = [
        "High_TSH", "Low_TSH",
        "Low_T4", "High_T4",
        "Low_T3", "High_T3"
    ]

    inflammatory_findings = [
        "High_CRP", "High_ESR", "High_Procalcitonin"
    ]

    iron_findings = [
        "Low_Ferritin", "High_Ferritin",
        "Low_Serum_Iron", "High_TIBC",
        "Low_TIBC", "Low_Transferrin_Saturation"
    ]

    for f in cbc_findings:
        add_parent(f, CBC_Finding)

    for f in liver_findings:
        add_parent(f, Liver_Finding)

    for f in kidney_findings:
        add_parent(f, Kidney_Finding)

    for f in diabetes_findings:
        add_parent(f, Diabetes_Finding)

    for f in thyroid_findings:
        add_parent(f, Thyroid_Finding)

    for f in inflammatory_findings:
        add_parent(f, Inflammatory_Finding)

    for f in iron_findings:
        add_parent(f, Iron_Profile_Finding)

    # =========================
    # 2) DISEASE HIERARCHY
    # =========================

    class Hematologic_Disease_Candidate(onto.DiseaseCandidate): pass
    class Infectious_Disease_Candidate(onto.DiseaseCandidate): pass
    class Liver_Disease_Group_Candidate(onto.DiseaseCandidate): pass
    class Kidney_Disease_Group_Candidate(onto.DiseaseCandidate): pass
    class Endocrine_Disease_Candidate(onto.DiseaseCandidate): pass
    class Inflammatory_Disease_Group_Candidate(onto.DiseaseCandidate): pass

    hematologic_diseases = [
        "Iron_Deficiency_Anemia_Candidate",
        "Thalassemia_Candidate",
        "Vitamin_B12_Deficiency_Anemia_Candidate",
        "Folate_Deficiency_Anemia_Candidate",
        "Leukemia_Risk_Candidate",
        "Thrombocytopenia_Candidate"
    ]

    infectious_diseases = [
        "Infection_Candidate",
        "Bacterial_Infection_Candidate",
        "Viral_Infection_Candidate"
    ]

    liver_diseases = [
        "Liver_Disease_Candidate",
        "Hepatitis_Candidate"
    ]

    kidney_diseases = [
        "Chronic_Kidney_Disease_Candidate"
    ]

    endocrine_diseases = [
        "Diabetes_Mellitus_Candidate",
        "Hypothyroidism_Candidate",
        "Hyperthyroidism_Candidate"
    ]

    inflammatory_diseases = [
        "Inflammatory_Disease_Candidate"
    ]

    for d in hematologic_diseases:
        add_parent(d, Hematologic_Disease_Candidate)

    for d in infectious_diseases:
        add_parent(d, Infectious_Disease_Candidate)

    for d in liver_diseases:
        add_parent(d, Liver_Disease_Group_Candidate)

    for d in kidney_diseases:
        add_parent(d, Kidney_Disease_Group_Candidate)

    for d in endocrine_diseases:
        add_parent(d, Endocrine_Disease_Candidate)

    for d in inflammatory_diseases:
        add_parent(d, Inflammatory_Disease_Group_Candidate)

    # =========================
    # 3) EQUIVALENT TO RULES
    # =========================

    disease_rules = {
        "Iron_Deficiency_Anemia_Candidate": [
            "Low_Hemoglobin", "Low_MCV", "Low_Ferritin",
            "Low_Serum_Iron", "High_TIBC", "Low_Transferrin_Saturation"
        ],

        "Thalassemia_Candidate": [
            "Low_Hemoglobin", "Low_MCV", "High_RBC"
        ],

        "Vitamin_B12_Deficiency_Anemia_Candidate": [
            "Low_Hemoglobin", "High_MCV"
        ],

        "Folate_Deficiency_Anemia_Candidate": [
            "Low_Hemoglobin", "High_MCV"
        ],

        "Leukemia_Risk_Candidate": [
            "High_WBC", "Low_Hemoglobin", "Low_Platelets"
        ],

        "Infection_Candidate": [
            "High_WBC", "High_CRP", "High_ESR"
        ],

        "Bacterial_Infection_Candidate": [
            "High_WBC", "High_Neutrophils", "High_CRP", "High_Procalcitonin"
        ],

        "Viral_Infection_Candidate": [
            "Low_WBC", "High_Lymphocytes"
        ],

        "Thrombocytopenia_Candidate": [
            "Low_Platelets"
        ],

        "Liver_Disease_Candidate": [
            "High_ALT", "High_AST", "High_Bilirubin", "Low_Albumin"
        ],

        "Hepatitis_Candidate": [
            "High_ALT", "High_AST", "High_Bilirubin"
        ],

        "Chronic_Kidney_Disease_Candidate": [
            "High_Creatinine", "High_BUN", "Low_eGFR"
        ],

        "Diabetes_Mellitus_Candidate": [
            "High_Fasting_Glucose", "High_HbA1c"
        ],

        "Hypothyroidism_Candidate": [
            "High_TSH", "Low_T4"
        ],

        "Hyperthyroidism_Candidate": [
            "Low_TSH", "High_T4"
        ],

        "Inflammatory_Disease_Candidate": [
            "High_CRP", "High_ESR"
        ],
    }

    for disease_name, findings in disease_rules.items():
        add_equivalent_rule(disease_name, findings)

    # =========================
    # 4) HPO MAPPING FOR FINDINGS
    # =========================
    # مهم: الـ IDs دي راجعيها من Protégé Search قبل التسليم النهائي

    hpo_mappings = {
        "Low_Hemoglobin": "0001903",      # Anemia
        "Low_Platelets": "0001873",      # Thrombocytopenia
        "High_Platelets": "0001894",     # Thrombocytosis
        "High_WBC": "0001974",           # Leukocytosis
        "Low_WBC": "0001882",            # Leukopenia
        "Low_Neutrophils": "0001875",    # Neutropenia
        "High_Eosinophils": "0001880",   # Eosinophilia
        "High_MCV": "0001972",           # Macrocytosis
        "Low_MCV": "0001935",            # Microcytosis
        "High_CRP": "0011227",           # Elevated CRP
    }

    for finding_name, hp_id in hpo_mappings.items():
        add_hpo_mapping(finding_name, hp_id)

    # =========================
    # 5) DOID MAPPING FOR DISEASES
    # =========================
    # برضه راجعي الـ IDs من DOID داخل Protégé

    doid_mappings = {
        "Diabetes_Mellitus_Candidate": "9351",
        "Chronic_Kidney_Disease_Candidate": "784",
        "Hepatitis_Candidate": "2237",
        "Thalassemia_Candidate": "12369",
    }

    for disease_name, doid_id in doid_mappings.items():
        add_doid_mapping(disease_name, doid_id)


onto.save(file=str(ONTO_PATH), format="rdfxml")

print("Full ontology upgrade completed successfully.")