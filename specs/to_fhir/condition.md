# Condition

## Semantic Context
The Condition resource represents a clinical condition, problem, or diagnosis. This mapping transforms Synthea CSV condition data into FHIR R4 Condition resources, preserving the clinical semantics of diagnoses and their temporal relationships.

## Field Mappings
```python
# Synthea CSV conditions → FHIR Condition mapping
# (source_field, target_field, semantic_concept, transform, notes)
conditions_mapping = [
    ("conditions.START", "Condition.onsetDateTime", "Onset Date/Time", "Format as ISO 8601", "When condition started"),
    ("conditions.STOP", "Condition.abatementDateTime", "Abatement Date/Time", "Format as ISO 8601", "When condition resolved (if applicable)"),
    ("conditions.PATIENT", "Condition.subject", "Patient Reference", "Create Reference(\"Patient/{id}\")", "Patient with condition"),
    ("conditions.ENCOUNTER", "Condition.encounter", "Encounter Reference", "Create Reference(\"Encounter/{id}\")", "Encounter where diagnosed"),
    ("conditions.CODE", "Condition.code.coding[0].code", "SNOMED Code", "Direct copy", "SNOMED CT code"),
    ("conditions.DESCRIPTION", "Condition.code.coding[0].display", "Code Display", "Direct copy", "Human-readable description"),
    ("conditions.CODE", "Condition.code.coding[0].system", "Code System", "Set to \"http://snomed.info/sct\"", "SNOMED CT system"),
    ("conditions.DESCRIPTION", "Condition.code.text", "Code Text", "Direct copy", "Fallback text description"),
    (None, "Condition.clinicalStatus", "Clinical Status", "Determine from STOP field", "active or resolved"),
    (None, "Condition.verificationStatus", "Verification Status", "Set to \"confirmed\"", "All CSV conditions are confirmed"),
    (None, "Condition.category", "Condition Category", "Set to \"encounter-diagnosis\"", "Default category"),
    (None, "Condition.id", "Resource ID", "Generate from PATIENT+START+CODE", "Composite key"),
]
```

## Clinical Status Logic
```
if STOP is null or empty:
    clinicalStatus = {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "active",
            "display": "Active"
        }]
    }
else:
    clinicalStatus = {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "resolved",
            "display": "Resolved"
        }]
    }
```

## Verification Status
All conditions from Synthea CSV are considered confirmed:
```json
{
    "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "confirmed",
        "display": "Confirmed"
    }]
}
```

## Category Mapping
Default to encounter-diagnosis for all conditions:
```json
[{
    "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
        "code": "encounter-diagnosis",
        "display": "Encounter Diagnosis"
    }]
}]
```

## Semantic Rules and Constraints
- SNOMED CT codes are preserved from Synthea (primary terminology for conditions)
- Clinical status is derived from presence/absence of STOP date
- All conditions are marked as confirmed (Synthea doesn't generate unconfirmed diagnoses)
- Onset is always present (START field required)
- Abatement only present if condition has resolved (STOP field present)
- Subject (patient) reference is required
- Encounter reference links to the diagnostic encounter

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.condition.condition_mapper`
- Preserves SNOMED CT coding from Synthea
- Automatic clinical status determination
- Handles both active and resolved conditions
- Uses common transformers for datetime formatting
- Generates stable IDs for resource references
