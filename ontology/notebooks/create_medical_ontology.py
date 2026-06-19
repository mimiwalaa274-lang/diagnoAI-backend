from owlready2 import *

# =========================
# 1) Create Ontology
# =========================

onto = get_ontology("http://example.org/lab_decision_support.owl")

with onto:

    # =========================
    # Main Classes
    # =========================

    class Medical_Entity(Thing):
        pass

    class Lab_Panel(Medical_Entity):
        pass

    class Lab_Test(Medical_Entity):
        pass

    class Patient_Factor(Medical_Entity):
        pass

    class Finding(Medical_Entity):
        pass

    class Disease_Candidate(Medical_Entity):
        pass

    class Recommendation(Medical_Entity):
        pass

    # =========================
    # Recommendation Subclasses
    # =========================

    class Additional_Test(Recommendation):
        pass

    class Specialist(Recommendation):
        pass

    class Urgency_Level(Recommendation):
        pass

    class Recommended_Action(Recommendation):
        pass

    # =========================
    # Object Properties
    # =========================

    class hasLabTest(ObjectProperty):
        domain = [Lab_Panel]
        range = [Lab_Test]

    class hasPatientFactor(ObjectProperty):
        domain = [Lab_Panel]
        range = [Patient_Factor]

    class labTestIndicatesFinding(ObjectProperty):
        domain = [Lab_Test]
        range = [Finding]

    class patientFactorIndicatesFinding(ObjectProperty):
        domain = [Patient_Factor]
        range = [Finding]

    class findingSuggestsDisease(ObjectProperty):
        domain = [Finding]
        range = [Disease_Candidate]

    class diseaseRequiresTest(ObjectProperty):
        domain = [Disease_Candidate]
        range = [Additional_Test]

    class diseaseTreatedBy(ObjectProperty):
        domain = [Disease_Candidate]
        range = [Specialist]

    class diseaseHasUrgency(ObjectProperty):
        domain = [Disease_Candidate]
        range = [Urgency_Level]

    class diseaseHasAction(ObjectProperty):
        domain = [Disease_Candidate]
        range = [Recommended_Action]


# =========================
# Helper Functions
# =========================

def make_classes(parent, names):
    created = {}
    with onto:
        for name in names:
            created[name] = types.new_class(name, (parent,))
    return created


def add_relation(subject, prop, objects):
    if not isinstance(objects, list):
        objects = [objects]
    for obj in objects:
        getattr(subject, prop.name).append(obj)


# =========================
# 2) Create Classes
# =========================

panels = make_classes(onto.Lab_Panel, [
    "CBC_Panel",
    "Diabetes_Panel",
    "Kidney_Function_Panel",
    "Liver_Function_Panel",
    "Thyroid_Function_Panel"
])

lab_tests = make_classes(onto.Lab_Test, [
    # CBC
    "Hemoglobin", "WBC", "RBC", "Platelets", "Hematocrit",
    "MCV", "MCH", "MCHC", "RDW",
    "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils",

    # Diabetes
    "HbA1c", "Blood_Glucose",

    # Kidney
    "Creatinine", "BUN", "eGFR", "Uric_Acid",

    # Liver
    "ALT", "AST", "ALP", "Bilirubin", "Albumin",

    # Thyroid
    "TSH", "T3", "T4"
])

patient_factors = make_classes(onto.Patient_Factor, [
    "Age", "Gender", "BMI", "Hypertension", "Heart_Disease"
])

findings = make_classes(onto.Finding, [
    # CBC
    "Low_Hemoglobin", "Low_RBC", "Low_MCV", "High_MCV", "High_RDW",
    "High_WBC", "Neutrophilia", "Lymphocytosis",
    "Thrombocytopenia", "Thrombocytosis",
    "Very_High_WBC", "Abnormal_Platelets", "Severe_Anemia",

    # Diabetes
    "High_HbA1c", "Hyperglycemia", "Obesity_Finding",
    "Hypertension_Finding", "Insulin_Resistance_Risk",

    # Kidney
    "High_Creatinine", "Elevated_BUN", "Low_eGFR",
    "Hyperuricemia", "Kidney_Function_Impairment",

    # Liver
    "Elevated_ALT", "Elevated_AST", "High_ALP",
    "Hyperbilirubinemia", "Hypoalbuminemia",
    "Hepatic_Cell_Injury", "Liver_Damage",
    "Jaundice_Risk", "Liver_Synthetic_Dysfunction",

    # Thyroid
    "High_TSH", "Low_TSH", "Low_T4", "High_T3_T4"
])

diseases = make_classes(onto.Disease_Candidate, [
    # CBC
    "Healthy",
    "Iron_Deficiency_Anemia",
    "Microcytic_Anemia",
    "Macrocytic_Anemia",
    "Normocytic_Anemia",
    "Infection",
    "Leukemia_Risk",
    "Platelet_Disorder",
    "Anemia_Other",

    # Diabetes
    "Healthy_Diabetes_Status",
    "Prediabetes",
    "Type_2_Diabetes",

    # Kidney
    "Normal_Kidney_Function",
    "Mild_Kidney_Dysfunction",
    "Chronic_Kidney_Disease",

    # Liver
    "Normal_Liver_Function",
    "Mild_Liver_Dysfunction",
    "Severe_Liver_Dysfunction",

    # Thyroid
    "Normal_Thyroid_Function",
    "Hypothyroidism",
    "Hyperthyroidism"
])

additional_tests = make_classes(onto.Additional_Test, [
    "Ferritin", "Serum_Iron", "TIBC", "Peripheral_Smear",
    "Bone_Marrow_Biopsy", "Flow_Cytometry", "CRP",
    "Urine_Albumin", "Urine_Analysis", "Kidney_Ultrasound",
    "Liver_Ultrasound", "Free_T4", "Free_T3",
    "Anti_TPO", "Repeat_Lab_Test"
])

specialists = make_classes(onto.Specialist, [
    "Hematologist",
    "Endocrinologist",
    "Nephrologist",
    "Hepatologist",
    "Internal_Medicine",
    "Emergency_Physician"
])

urgency_levels = make_classes(onto.Urgency_Level, [
    "Routine", "Soon", "Urgent", "Emergency"
])

actions = make_classes(onto.Recommended_Action, [
    "Repeat_Test",
    "Order_Confirmatory_Test",
    "Refer_To_Specialist",
    "Urgent_Medical_Attention",
    "Lifestyle_Modification",
    "Medical_Follow_Up"
])


# =========================
# 3) Panel Relations
# =========================

for test in [
    "Hemoglobin", "WBC", "RBC", "Platelets", "Hematocrit",
    "MCV", "MCH", "MCHC", "RDW",
    "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils"
]:
    add_relation(panels["CBC_Panel"], onto.hasLabTest, lab_tests[test])

for test in ["HbA1c", "Blood_Glucose"]:
    add_relation(panels["Diabetes_Panel"], onto.hasLabTest, lab_tests[test])

for factor in ["BMI", "Age", "Hypertension", "Heart_Disease"]:
    add_relation(panels["Diabetes_Panel"], onto.hasPatientFactor, patient_factors[factor])

for test in ["Creatinine", "BUN", "eGFR", "Uric_Acid"]:
    add_relation(panels["Kidney_Function_Panel"], onto.hasLabTest, lab_tests[test])

for factor in ["Age", "Gender"]:
    add_relation(panels["Kidney_Function_Panel"], onto.hasPatientFactor, patient_factors[factor])

for test in ["ALT", "AST", "ALP", "Bilirubin", "Albumin"]:
    add_relation(panels["Liver_Function_Panel"], onto.hasLabTest, lab_tests[test])

for test in ["TSH", "T3", "T4"]:
    add_relation(panels["Thyroid_Function_Panel"], onto.hasLabTest, lab_tests[test])


# =========================
# 4) Lab Test → Finding Relations
# =========================

test_to_findings = {
    "Hemoglobin": ["Low_Hemoglobin", "Severe_Anemia"],
    "RBC": ["Low_RBC"],
    "MCV": ["Low_MCV", "High_MCV"],
    "RDW": ["High_RDW"],
    "WBC": ["High_WBC", "Very_High_WBC"],
    "Neutrophils": ["Neutrophilia"],
    "Lymphocytes": ["Lymphocytosis"],
    "Platelets": ["Thrombocytopenia", "Thrombocytosis", "Abnormal_Platelets"],

    "HbA1c": ["High_HbA1c"],
    "Blood_Glucose": ["Hyperglycemia"],

    "Creatinine": ["High_Creatinine"],
    "BUN": ["Elevated_BUN", "Kidney_Function_Impairment"],
    "eGFR": ["Low_eGFR"],
    "Uric_Acid": ["Hyperuricemia"],

    "ALT": ["Elevated_ALT", "Hepatic_Cell_Injury"],
    "AST": ["Elevated_AST", "Liver_Damage"],
    "ALP": ["High_ALP"],
    "Bilirubin": ["Hyperbilirubinemia", "Jaundice_Risk"],
    "Albumin": ["Hypoalbuminemia", "Liver_Synthetic_Dysfunction"],

    "TSH": ["High_TSH", "Low_TSH"],
    "T3": ["High_T3_T4"],
    "T4": ["Low_T4", "High_T3_T4"]
}

for test_name, finding_names in test_to_findings.items():
    for finding_name in finding_names:
        add_relation(
            lab_tests[test_name],
            onto.labTestIndicatesFinding,
            findings[finding_name]
        )


# =========================
# 5) Patient Factor → Finding Relations
# =========================

factor_to_findings = {
    "BMI": ["Obesity_Finding", "Insulin_Resistance_Risk"],
    "Hypertension": ["Hypertension_Finding"],
    "Heart_Disease": ["Insulin_Resistance_Risk"]
}

for factor_name, finding_names in factor_to_findings.items():
    for finding_name in finding_names:
        add_relation(
            patient_factors[factor_name],
            onto.patientFactorIndicatesFinding,
            findings[finding_name]
        )


# =========================
# 6) Finding → Disease Relations
# =========================

finding_to_diseases = {
    # CBC
    "Low_Hemoglobin": [
        "Iron_Deficiency_Anemia",
        "Microcytic_Anemia",
        "Macrocytic_Anemia",
        "Normocytic_Anemia",
        "Anemia_Other"
    ],
    "Low_MCV": ["Iron_Deficiency_Anemia", "Microcytic_Anemia"],
    "High_MCV": ["Macrocytic_Anemia"],
    "High_RDW": ["Iron_Deficiency_Anemia", "Anemia_Other"],
    "High_WBC": ["Infection", "Leukemia_Risk"],
    "Neutrophilia": ["Infection"],
    "Lymphocytosis": ["Infection", "Leukemia_Risk"],
    "Thrombocytopenia": ["Platelet_Disorder", "Leukemia_Risk"],
    "Thrombocytosis": ["Platelet_Disorder"],
    "Very_High_WBC": ["Leukemia_Risk"],
    "Abnormal_Platelets": ["Platelet_Disorder", "Leukemia_Risk"],
    "Severe_Anemia": ["Leukemia_Risk", "Anemia_Other"],

    # Diabetes
    "High_HbA1c": ["Type_2_Diabetes", "Prediabetes"],
    "Hyperglycemia": ["Type_2_Diabetes"],
    "Obesity_Finding": ["Type_2_Diabetes", "Prediabetes"],
    "Hypertension_Finding": ["Type_2_Diabetes"],
    "Insulin_Resistance_Risk": ["Prediabetes", "Type_2_Diabetes"],

    # Kidney
    "High_Creatinine": ["Mild_Kidney_Dysfunction", "Chronic_Kidney_Disease"],
    "Elevated_BUN": ["Mild_Kidney_Dysfunction", "Chronic_Kidney_Disease"],
    "Low_eGFR": ["Chronic_Kidney_Disease"],
    "Kidney_Function_Impairment": ["Mild_Kidney_Dysfunction", "Chronic_Kidney_Disease"],

    # Liver
    "Elevated_ALT": ["Mild_Liver_Dysfunction", "Severe_Liver_Dysfunction"],
    "Elevated_AST": ["Mild_Liver_Dysfunction", "Severe_Liver_Dysfunction"],
    "High_ALP": ["Mild_Liver_Dysfunction", "Severe_Liver_Dysfunction"],
    "Hyperbilirubinemia": ["Severe_Liver_Dysfunction"],
    "Hypoalbuminemia": ["Severe_Liver_Dysfunction"],
    "Hepatic_Cell_Injury": ["Mild_Liver_Dysfunction"],
    "Liver_Damage": ["Mild_Liver_Dysfunction", "Severe_Liver_Dysfunction"],
    "Jaundice_Risk": ["Severe_Liver_Dysfunction"],
    "Liver_Synthetic_Dysfunction": ["Severe_Liver_Dysfunction"],

    # Thyroid
    "High_TSH": ["Hypothyroidism"],
    "Low_TSH": ["Hyperthyroidism"],
    "Low_T4": ["Hypothyroidism"],
    "High_T3_T4": ["Hyperthyroidism"]
}

for finding_name, disease_names in finding_to_diseases.items():
    for disease_name in disease_names:
        add_relation(
            findings[finding_name],
            onto.findingSuggestsDisease,
            diseases[disease_name]
        )


# =========================
# 7) Disease → Additional Tests
# =========================

disease_to_tests = {
    "Iron_Deficiency_Anemia": [
        "Ferritin", "Serum_Iron", "TIBC", "Peripheral_Smear"
    ],
    "Microcytic_Anemia": [
        "Ferritin", "Serum_Iron", "TIBC", "Peripheral_Smear"
    ],
    "Macrocytic_Anemia": [
        "Peripheral_Smear", "Repeat_Lab_Test"
    ],
    "Normocytic_Anemia": [
        "Peripheral_Smear", "Repeat_Lab_Test"
    ],
    "Infection": [
        "CRP", "Repeat_Lab_Test"
    ],
    "Leukemia_Risk": [
        "Bone_Marrow_Biopsy", "Flow_Cytometry", "Peripheral_Smear"
    ],
    "Platelet_Disorder": [
        "Peripheral_Smear", "Repeat_Lab_Test"
    ],
    "Anemia_Other": [
        "Peripheral_Smear", "Repeat_Lab_Test"
    ],

    "Type_2_Diabetes": [
        "Repeat_Lab_Test"
    ],
    "Prediabetes": [
        "Repeat_Lab_Test"
    ],

    "Chronic_Kidney_Disease": [
        "Urine_Albumin", "Urine_Analysis", "Kidney_Ultrasound"
    ],
    "Mild_Kidney_Dysfunction": [
        "Urine_Analysis", "Repeat_Lab_Test"
    ],

    "Severe_Liver_Dysfunction": [
        "Liver_Ultrasound", "Repeat_Lab_Test"
    ],
    "Mild_Liver_Dysfunction": [
        "Repeat_Lab_Test"
    ],

    "Hypothyroidism": [
        "Free_T4", "Anti_TPO"
    ],
    "Hyperthyroidism": [
        "Free_T3", "Free_T4"
    ]
}

for disease_name, test_names in disease_to_tests.items():
    for test_name in test_names:
        add_relation(
            diseases[disease_name],
            onto.diseaseRequiresTest,
            additional_tests[test_name]
        )


# =========================
# 8) Disease → Specialist
# =========================

disease_to_specialist = {
    "Iron_Deficiency_Anemia": "Hematologist",
    "Microcytic_Anemia": "Hematologist",
    "Macrocytic_Anemia": "Hematologist",
    "Normocytic_Anemia": "Hematologist",
    "Anemia_Other": "Hematologist",
    "Leukemia_Risk": "Hematologist",
    "Platelet_Disorder": "Hematologist",
    "Infection": "Internal_Medicine",

    "Type_2_Diabetes": "Endocrinologist",
    "Prediabetes": "Endocrinologist",
    "Hypothyroidism": "Endocrinologist",
    "Hyperthyroidism": "Endocrinologist",

    "Chronic_Kidney_Disease": "Nephrologist",
    "Mild_Kidney_Dysfunction": "Nephrologist",

    "Mild_Liver_Dysfunction": "Hepatologist",
    "Severe_Liver_Dysfunction": "Hepatologist"
}

for disease_name, specialist_name in disease_to_specialist.items():
    add_relation(
        diseases[disease_name],
        onto.diseaseTreatedBy,
        specialists[specialist_name]
    )


# =========================
# 9) Disease → Urgency
# =========================

disease_to_urgency = {
    "Healthy": "Routine",
    "Healthy_Diabetes_Status": "Routine",
    "Normal_Kidney_Function": "Routine",
    "Normal_Liver_Function": "Routine",
    "Normal_Thyroid_Function": "Routine",

    "Prediabetes": "Routine",
    "Type_2_Diabetes": "Soon",

    "Iron_Deficiency_Anemia": "Soon",
    "Microcytic_Anemia": "Soon",
    "Macrocytic_Anemia": "Soon",
    "Normocytic_Anemia": "Soon",
    "Anemia_Other": "Soon",
    "Infection": "Soon",

    "Mild_Kidney_Dysfunction": "Soon",
    "Chronic_Kidney_Disease": "Soon",

    "Mild_Liver_Dysfunction": "Soon",
    "Severe_Liver_Dysfunction": "Urgent",

    "Hypothyroidism": "Soon",
    "Hyperthyroidism": "Soon",

    "Leukemia_Risk": "Emergency",
    "Platelet_Disorder": "Urgent"
}

for disease_name, urgency_name in disease_to_urgency.items():
    add_relation(
        diseases[disease_name],
        onto.diseaseHasUrgency,
        urgency_levels[urgency_name]
    )


# =========================
# 10) Disease → Recommended Action
# =========================

disease_to_action = {
    "Healthy": "Medical_Follow_Up",
    "Healthy_Diabetes_Status": "Medical_Follow_Up",
    "Normal_Kidney_Function": "Medical_Follow_Up",
    "Normal_Liver_Function": "Medical_Follow_Up",
    "Normal_Thyroid_Function": "Medical_Follow_Up",

    "Prediabetes": "Lifestyle_Modification",
    "Type_2_Diabetes": "Medical_Follow_Up",

    "Iron_Deficiency_Anemia": "Order_Confirmatory_Test",
    "Microcytic_Anemia": "Order_Confirmatory_Test",
    "Macrocytic_Anemia": "Order_Confirmatory_Test",
    "Normocytic_Anemia": "Order_Confirmatory_Test",
    "Anemia_Other": "Order_Confirmatory_Test",
    "Infection": "Order_Confirmatory_Test",

    "Mild_Kidney_Dysfunction": "Refer_To_Specialist",
    "Chronic_Kidney_Disease": "Refer_To_Specialist",

    "Mild_Liver_Dysfunction": "Medical_Follow_Up",
    "Severe_Liver_Dysfunction": "Refer_To_Specialist",

    "Hypothyroidism": "Order_Confirmatory_Test",
    "Hyperthyroidism": "Order_Confirmatory_Test",

    "Leukemia_Risk": "Urgent_Medical_Attention",
    "Platelet_Disorder": "Refer_To_Specialist"
}

for disease_name, action_name in disease_to_action.items():
    add_relation(
        diseases[disease_name],
        onto.diseaseHasAction,
        actions[action_name]
    )


# =========================
# 11) Save Ontology
# =========================

output_path = "lab_decision_support_ontology.owl"
onto.save(file=output_path, format="rdfxml")

print("Ontology created successfully!")
print(f"Saved as: {output_path}")