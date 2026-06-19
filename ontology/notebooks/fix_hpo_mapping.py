from pathlib import Path
from owlready2 import *

# =========================
# Path Setup
# =========================

BASE_DIR = Path(__file__).parent
ONTO_PATH = BASE_DIR / "lab_decision_support_ontology.owl"

onto_path.append(str(BASE_DIR))

# Load external ontologies first
for file in BASE_DIR.glob("*.owl"):
    if file.name != ONTO_PATH.name:
        try:
            get_ontology(str(file)).load(only_local=True)
            print("Loaded external ontology:", file.name)
        except Exception as e:
            print("Could not load:", file.name, e)

onto = get_ontology(str(ONTO_PATH)).load(only_local=True)
print("Main ontology loaded successfully")


# =========================
# Helpers
# =========================

def is_doid_class(cls):
    iri = cls.iri.lower()
    return "doid" in iri


def is_hpo_class(cls):
    iri = cls.iri.lower()
    return "hp_" in iri or "human_phenotype" in iri or "hp.owl" in iri


def get_local_class(name):
    cls = onto.search_one(iri="*" + name)
    if cls is None:
        raise ValueError(f"Local class not found: {name}")
    return cls


def find_hpo_class(label_text):
    label_text = label_text.lower().strip()

    for cls in default_world.classes():
        if cls.namespace.base_iri == onto.base_iri:
            continue

        if not is_hpo_class(cls):
            continue

        if label_text == cls.name.lower():
            return cls

        for label in cls.label:
            if label_text == str(label).lower():
                return cls

    return None


def fix_finding_mapping(local_name, hpo_label):
    local_cls = get_local_class(local_name)

    # Remove wrong DOID parents from this finding
    old_parents = list(local_cls.is_a)

    for parent in old_parents:
        if isinstance(parent, ThingClass) and is_doid_class(parent):
            local_cls.is_a.remove(parent)
            print(f"Removed wrong DOID parent from {local_name}: {parent.name}")

    # Add correct HPO parent
    hpo_cls = find_hpo_class(hpo_label)

    if hpo_cls is None:
        print(f"HPO class not found for {local_name}: {hpo_label}")
        return

    if hpo_cls not in local_cls.is_a:
        local_cls.is_a.append(hpo_cls)
        print(f"Added HPO mapping: {local_name} SubClassOf {hpo_cls.name}")
    else:
        print(f"HPO mapping already exists: {local_name} -> {hpo_cls.name}")


# =========================
# Correct HPO Mappings
# =========================

correct_hpo_mappings = {
    "Low_Hemoglobin": "anemia",
    "High_WBC": "leukocytosis",
    "Thrombocytopenia": "thrombocytopenia",
    "Thrombocytosis": "thrombocytosis",
    "Hyperglycemia": "hyperglycemia",
    "Hyperbilirubinemia": "hyperbilirubinemia",
    "Jaundice_Risk": "jaundice",
}

for local, hpo_label in correct_hpo_mappings.items():
    fix_finding_mapping(local, hpo_label)


# =========================
# Save
# =========================

onto.save(file=str(ONTO_PATH), format="rdfxml")

print("Done! Wrong DOID mappings removed and HPO mappings fixed.")