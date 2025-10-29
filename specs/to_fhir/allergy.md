# AllergyIntolerance (Synthea allergies.csv → FHIR R4)

## Semantic Context
The AllergyIntolerance resource represents an individual's propensity for adverse reactions to a substance or product. This mapping transforms Synthea `allergies.csv` data into FHIR R4 AllergyIntolerance resources, preserving the clinical semantics of identification, timing, category, type, and recorded reactions.

## Field Mappings
```python
# Synthea CSV allergies → FHIR AllergyIntolerance mapping
# (source_field, target_field, semantic_concept, transform, notes)
allergies_mapping = [
    ("START", "AllergyIntolerance.recordedDate", "Date recorded", "Format as ISO 8601", "Also used for onset if present"),
    ("START", "AllergyIntolerance.onsetDateTime", "Onset of susceptibility", "Format as ISO 8601", "Optional; mirrors recordedDate"),
    ("STOP", "AllergyIntolerance.clinicalStatus", "Clinical status", "Derived", "active if STOP empty; resolved if present"),
    ("STOP", "AllergyIntolerance.lastOccurrence", "Last known reaction occurrence", "Format as ISO 8601", "Optional, when STOP present"),
    ("PATIENT", "AllergyIntolerance.patient", "Patient reference", "Create Reference(\"Patient/{id}\")", "Required subject"),
    ("ENCOUNTER", "AllergyIntolerance.encounter", "Encounter reference", "Create Reference(\"Encounter/{id}\")", "Asserting encounter"),
    ("CODE", "AllergyIntolerance.code.coding[0].code", "Substance/product code", "Direct copy", "SNOMED CT or RxNorm per SYSTEM"),
    ("SYSTEM", "AllergyIntolerance.code.coding[0].system", "Coding system", "Direct copy", "e.g., http://snomed.info/sct or RxNorm URL"),
    ("DESCRIPTION", "AllergyIntolerance.code.coding[0].display", "Code display", "Direct copy", "Human-readable text"),
    ("DESCRIPTION", "AllergyIntolerance.code.text", "Code text", "Direct copy", "Fallback text"),
    ("TYPE", "AllergyIntolerance.type", "Allergy vs intolerance", "Lowercase", "R4: code with values allergy|intolerance"),
    ("CATEGORY", "AllergyIntolerance.category[0]", "Category of substance", "Normalize to FHIR code", "Map drug→medication; medication→medication; food→food; environment→environment; others omitted"),
    ("REACTION1", "AllergyIntolerance.reaction[0].manifestation[0].coding[0].code", "Reaction manifestation code", "Direct copy", "SNOMED CT code"),
    ("DESCRIPTION1", "AllergyIntolerance.reaction[0].description", "Reaction narrative", "Direct copy", "Text description of the event"),
    ("SEVERITY1", "AllergyIntolerance.reaction[0].severity", "Reaction severity", "Lowercase", "mild|moderate|severe"),
    ("REACTION2", "AllergyIntolerance.reaction[1].manifestation[0].coding[0].code", "Reaction manifestation code", "Direct copy", "Optional second reaction"),
    ("DESCRIPTION2", "AllergyIntolerance.reaction[1].description", "Reaction narrative", "Direct copy", "Optional"),
    ("SEVERITY2", "AllergyIntolerance.reaction[1].severity", "Reaction severity", "Lowercase", "Optional"),
    (None, "AllergyIntolerance.verificationStatus", "Verification status", "Set to confirmed", "All Synthea allergies are considered confirmed"),
    (None, "AllergyIntolerance.id", "Resource ID", "Generate from PATIENT+START+CODE", "Stable composite identifier"),
]
```

## Clinical Status Logic
```
if STOP is null or empty:
  clinicalStatus = { coding: [{ system: "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", code: "active", display: "Active" }] }
else:
  clinicalStatus = { coding: [{ system: "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", code: "resolved", display: "Resolved" }] }
```

## Category Normalization
- drug → medication
- medication → medication
- food → food
- environment → environment
- others → omitted

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.allergy.map_allergy`
- Uses common datetime/reference helpers
- Produces R4-compliant `reaction.manifestation` as CodeableConcept (not CodeableReference)
