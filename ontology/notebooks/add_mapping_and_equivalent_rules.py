from pathlib import Path
from owlready2 import *

BASE_DIR = Path(__file__).parent
ONTO_PATH = BASE_DIR / "lab_decision_support_ontology.owl"

onto_path.append(str(BASE_DIR))

# Load external ontologies if they exist in same folder
for file in BASE_DIR.glob("*.owl"):
    if file.name != ONTO_PATH.name:
        try:
            get_ontology(str(file)).load(only_local=True)
            print("Loaded external ontology:", file.name)
        except Exception as e:
            print("Could not load:", file.name, e)

onto = get_ontology(str(ONTO_PATH)).load(only_local=True)
print("Main ontology loaded successfully")


def get_local_class(name):
    cls = onto.search_one(iri="*" + name)
    if cls is None:
        raise ValueError(f"Local class not found: {name}")
    return cls


def find_external_class(label_text):
    label_text = label_text.lower().strip()

    for cls in default_world.classes():
        if cls.namespace.base_iri == onto.base_iri:
            continue

        if label_text == cls.name.lower():
            return cls

        for label in cls.label:
            if label_text == str(label).lower():
                return cls

    return None


def add_subclass_mapping(local_name, external_label):
    local_cls = get_local_class(local_name)
    external_cls = find_external_class(external_label)

    if external_cls is None:
        print(f"External not found: {local_name} -> {external_label}")
        return

    if external_cls not in local_cls.is_a:
        local_cls.is_a.append(external_cls)

    print(f"Mapped: {local_name} SubClassOf {external_cls.name}")


# =========================
# Mapping
# =========================

disease_mappings = {
    "Iron_Deficiency_Anemia": "iron deficiency anemia",
    "Type_2_Diabetes": "type 2 diabetes mellitus",
    "Chronic_Kidney_Disease": "chronic kidney disease",
    "Hypothyroidism": "hypothyroidism",
    "Hyperthyroidism": "hyperthyroidism",
    "Leukemia_Risk": "leukemia",
    "Infection": "infectious disease",
}

finding_mappings = {
    "Low_Hemoglobin": "anemia",
    "High_WBC": "leukocytosis",
    "Thrombocytopenia": "thrombocytopenia",
    "Thrombocytosis": "thrombocytosis",
    "Hyperglycemia": "hyperglycemia",
    "Hyperbilirubinemia": "hyperbilirubinemia",
    "Jaundice_Risk": "jaundice",
}

for local, external in disease_mappings.items():
    add_subclass_mapping(local, external)

for local, external in finding_mappings.items():
    add_subclass_mapping(local, external)


# =========================
# Equivalent rules
# =========================

with onto:
    class diseaseSuggestedByFinding(ObjectProperty):
        domain = [onto.Disease_Candidate]
        range = [onto.Finding]
        inverse_property = onto.findingSuggestsDisease


def add_equivalent_rule(disease_name, finding_names):
    disease_cls = get_local_class(disease_name)

    expression = onto.Disease_Candidate

    for finding_name in finding_names:
        finding_cls = get_local_class(finding_name)
        expression = expression & diseaseSuggestedByFinding.some(finding_cls)

    if expression not in disease_cls.equivalent_to:
        disease_cls.equivalent_to.append(expression)

    print("Equivalent rule added:", disease_name)


rules = {
    "Iron_Deficiency_Anemia": ["Low_Hemoglobin", "Low_MCV", "High_RDW"],
    "Microcytic_Anemia": ["Low_Hemoglobin", "Low_MCV"],
    "Macrocytic_Anemia": ["Low_Hemoglobin", "High_MCV"],
    "Infection": ["High_WBC", "Neutrophilia"],
    "Leukemia_Risk": ["Very_High_WBC", "Abnormal_Platelets", "Severe_Anemia"],
    "Platelet_Disorder": ["Abnormal_Platelets"],

    "Type_2_Diabetes": ["High_HbA1c", "Hyperglycemia"],
    "Prediabetes": ["High_HbA1c", "Insulin_Resistance_Risk"],

    "Chronic_Kidney_Disease": ["Low_eGFR", "High_Creatinine"],
    "Mild_Kidney_Dysfunction": ["High_Creatinine", "Elevated_BUN"],

    "Severe_Liver_Dysfunction": ["Elevated_ALT", "Elevated_AST", "Hyperbilirubinemia"],
    "Mild_Liver_Dysfunction": ["Elevated_ALT", "Elevated_AST"],

    "Hypothyroidism": ["High_TSH", "Low_T4"],
    "Hyperthyroidism": ["Low_TSH", "High_T3_T4"],
}

for disease, findings in rules.items():
    add_equivalent_rule(disease, findings)


onto.save(file=str(ONTO_PATH), format="rdfxml")
print("Done! Saved in the same ontology.")