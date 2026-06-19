from owlready2 import *
from pathlib import Path

print("Fixing Medical Entity hierarchy...")

BASE_DIR = Path(__file__).parent

ONTO_PATH = BASE_DIR / "medical_lab_ontology.owl"

onto_path.append(str(BASE_DIR))

onto = get_ontology(str(ONTO_PATH)).load(only_local=True)

medical_entity = onto.Medical_Entity

classes_to_move = [
    "Body_System",
    "Recommended_Action",
    "Severity_Level",
    "Urgency_Level"
]

for cls_name in classes_to_move:

    cls = getattr(onto, cls_name, None)

    if cls is None:
        print(f"Missing class: {cls_name}")
        continue

    # remove owl:Thing direct inheritance
    if Thing in cls.is_a:
        cls.is_a.remove(Thing)

    # add Medical_Entity
    if medical_entity not in cls.is_a:
        cls.is_a.append(medical_entity)

    print(f"Moved {cls_name} under Medical_Entity")

onto.save(file=str(ONTO_PATH), format="rdfxml")

print("Hierarchy fixed successfully.")