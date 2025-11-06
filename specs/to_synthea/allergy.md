# AllergyIntolerance (FHIR R4 → Synthea allergies.csv)

## Primary Source Resource
- AllergyIntolerance

## Field Mappings
```python
# FHIR AllergyIntolerance → Synthea CSV allergies mapping
# (source_field, target_field, semantic_concept, transform, notes)
allergies_reverse_mapping = [
    ("AllergyIntolerance.recordedDate or onsetDateTime", "allergies.START", "Date recorded", "Parse FHIR datetime → Synthea format", "Prefer recordedDate; fallback to onsetDateTime"),
    ("AllergyIntolerance.lastOccurrence", "allergies.STOP", "Last occurrence", "Parse FHIR datetime → Synthea format", "If absent but clinicalStatus is resolved/inactive, leave empty string"),
    ("AllergyIntolerance.patient.reference", "allergies.PATIENT", "Patient reference", "Extract reference id", "Patient/{id}"),
    ("AllergyIntolerance.encounter.reference", "allergies.ENCOUNTER", "Encounter reference", "Extract reference id", "Encounter/{id}"),
    ("AllergyIntolerance.code.coding (SNOMED/RxNorm)", "allergies.CODE", "Allergy code", "Extract coding.code", "Prefer SNOMED or RxNorm; fallback first coding"),
    ("AllergyIntolerance.code.coding", "allergies.SYSTEM", "Code system", "Extract coding.system", "Preserved system URL"),
    ("AllergyIntolerance.code", "allergies.DESCRIPTION", "Description", "Display or text fallback", "Human-readable description"),
    ("AllergyIntolerance.type", "allergies.TYPE", "Type", "Lowercase", "allergy|intolerance"),
    ("AllergyIntolerance.category[0]", "allergies.CATEGORY", "Category", "Normalize", "medication/food/environment"),
    ("AllergyIntolerance.reaction[0].manifestation[0]", "allergies.REACTION1", "Reaction 1", "Extract coding.code (SNOMED)", "Optional"),
    ("AllergyIntolerance.reaction[0].description", "allergies.DESCRIPTION1", "Reaction 1 description", "Direct copy", "Optional"),
    ("AllergyIntolerance.reaction[0].severity", "allergies.SEVERITY1", "Severity 1", "Uppercase", "MILD|MODERATE|SEVERE"),
    ("AllergyIntolerance.reaction[1].manifestation[0]", "allergies.REACTION2", "Reaction 2", "Extract coding.code (SNOMED)", "Optional"),
    ("AllergyIntolerance.reaction[1].description", "allergies.DESCRIPTION2", "Reaction 2 description", "Direct copy", "Optional"),
    ("AllergyIntolerance.reaction[1].severity", "allergies.SEVERITY2", "Severity 2", "Uppercase", "Optional"),
]
```

## Clinical Status Handling
- If clinicalStatus indicates resolved/inactive but no `lastOccurrence`, output empty `STOP`.
- Otherwise, omit `STOP` if unknown.

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_synthea_csv.allergy.map_fhir_allergy_to_csv`
- Use existing reverse helpers to parse datetimes and extract codings/references.
