from pathlib import Path
from owlready2 import *

# =========================
# 1) Path Setup
# =========================

BASE_DIR = Path(__file__).parent

ONTO_PATH = BASE_DIR / "lab_decision_support_ontology.owl"

onto_path.append(str(BASE_DIR))

onto = get_ontology(str(ONTO_PATH)).load(only_local=True)

print("Ontology loaded successfully")


# =========================
# 2) Helper Functions
# =========================

def get_local_class(name):
    cls = onto.search_one(iri="*" + name)
    if cls is None:
        raise ValueError(f"Local class not found: {name}")
    return cls


def find_external_class_by_label_or_id(search_text):
    """
    Search in imported ontologies like HPO / DOID
    by label, id, or class name.
    """
    search_text = search_text.lower().strip()

    for cls in default_world.classes():

        # avoid returning local classes from our ontology
        if cls.namespace.base_iri == onto.base_iri:
            continue

        # search by class name
        if search_text == cls.name.lower():
            return cls

        # search by label
        for label in cls.label:
            if search_text == str(label).lower():
                return cls

        # search by obo id annotation
        if hasattr(cls, "id"):
            for cid in cls.id:
                if search_text == str(cid).lower():
                    return cls

    return None


def add_subclass_mapping(local_name, external_search_text):
    """
    Adds:
    Local_Class SubClassOf External_Standard_Class
    """
    local_cls = get_local_class(local_name)
    external_cls = find_external_class_by_label_or_id(external_search_text)

    if external_cls is None:
        print(f"External class not found for: {local_name} -> {external_search_text}")
        return

    if external_cls not in local_cls.is_a:
        local_cls.is_a.append(external_cls)

    print(f"Mapped SubClassOf: {local_name} -> {external_cls.name}")


# =========================
# 3) Mapping to DOID / HPO
# =========================

# Diseases -> DOID
disease_doid_mappings = {
    "Iron_Deficiency_Anemia": "iron deficiency anemia",
    "Type_2_Diabetes": "type 2 diabetes mellitus",
    "Chronic_Kidney_Disease": "chronic kidney disease",
    "Hypothyroidism": "hypothyroidism",
    "Hyperthyroidism": "hyperthyroidism",
    "Leukemia_Risk": "leukemia",
    "Infection": "infectious disease",
}

# Findings -> HPO
finding_hpo_mappings = {
    "Low_Hemoglobin": "anemia",
    "High_WBC": "leukocytosis",
    "Thrombocytopenia": "thrombocytopenia",
    "Thrombocytosis": "thrombocytosis",
    "Hyperglycemia": "hyperglycemia",
    "Hyperbilirubinemia": "hyperbilirubinemia",
    "Jaundice_Risk": "jaundice",
}

for local_name, external_name in disease_doid_mappings.items():
    add_subclass_mapping(local_name, external_name)

for local_name, external_name in finding_hpo_mappings.items():
    add_subclass_mapping(local_name, external_name)


# =========================
# 4) Create inverse property for disease definitions
# =========================

with onto:
    if not hasattr(onto, "diseaseSuggestedByFinding"):
        class diseaseSuggestedByFinding(ObjectProperty):
            domain = [onto.Disease_Candidate]
            range = [onto.Finding]
            inverse_property = onto.findingSuggestsDisease


# =========================
# 5) Add Equivalent To Rules
# =========================

def add_equivalent_rule(disease_name, required_findings):
    disease_cls = get_local_class(disease_name)

    expression = get_local_class("Disease_Candidate")

    for finding_name in required_findings:
        finding_cls = get_local_class(finding_name)
        expression = expression & onto.diseaseSuggestedByFinding.some(finding_cls)

    # avoid duplicate equivalent rules
    if expression not in disease_cls.equivalent_to:
        disease_cls.equivalent_to.append(expression)

    print(f"Equivalent To rule added for: {disease_name}")


equivalent_rules = {
    "Iron_Deficiency_Anemia": [
        "Low_Hemoglobin",
        "Low_MCV",
        "High_RDW"
    ],

    "Microcytic_Anemia": [
        "Low_Hemoglobin",
        "Low_MCV"
    ],

    "Macrocytic_Anemia": [
        "Low_Hemoglobin",
        "High_MCV"
    ],

    "Infection": [
        "High_WBC",
        "Neutrophilia"
    ],

    "Leukemia_Risk": [
        "Very_High_WBC",
        "Abnormal_Platelets",
        "Severe_Anemia"
    ],

    "Platelet_Disorder": [
        "Abnormal_Platelets"
    ],

    "Type_2_Diabetes": [
        "High_HbA1c",
        "Hyperglycemia"
    ],

    "Prediabetes": [
        "High_HbA1c",
        "Insulin_Resistance_Risk"
    ],

    "Chronic_Kidney_Disease": [
        "Low_eGFR",
        "High_Creatinine"
    ],

    "Mild_Kidney_Dysfunction": [
        "High_Creatinine",
        "Elevated_BUN"
    ],

    "Severe_Liver_Dysfunction": [
        "Elevated_ALT",
        "Elevated_AST",
        "Hyperbilirubinemia"
    ],

    "Mild_Liver_Dysfunction": [
        "Elevated_ALT",
        "Elevated_AST"
    ],

    "Hypothyroidism": [
        "High_TSH",
        "Low_T4"
    ],

    "Hyperthyroidism": [
        "Low_TSH",
        "High_T3_T4"
    ]
}

for disease_name, findings in equivalent_rules.items():
    add_equivalent_rule(disease_name, findings)


# =========================
# 6) Save in the same ontology
# =========================

onto.save(file=str(ONTO_PATH), format="rdfxml")

print("Done! Mapping + Equivalent rules saved in the same ontology.")