# AllergyIntolerance (FHIR R4 → Synthea allergies.csv)

## Primary Source Resource
- AllergyIntolerance

## Field Mappings
| Source Field | Target Field | Transform | Notes |
|--------------|--------------|-----------|-------|
| AllergyIntolerance.recordedDate or onsetDateTime | allergies.START | Parse FHIR datetime → Synthea format | Prefer recordedDate; fallback to onsetDateTime |
| AllergyIntolerance.lastOccurrence | allergies.STOP | Parse FHIR datetime → Synthea format | If absent but clinicalStatus is resolved/inactive, leave empty string |
| AllergyIntolerance.patient.reference | allergies.PATIENT | Extract reference id | Patient/{id} |
| AllergyIntolerance.encounter.reference | allergies.ENCOUNTER | Extract reference id | Encounter/{id} |
| AllergyIntolerance.code.coding (SNOMED/RxNorm) | allergies.CODE | Extract coding.code | Prefer SNOMED or RxNorm; fallback first coding |
| AllergyIntolerance.code.coding | allergies.SYSTEM | Extract coding.system | Preserved system URL |
| AllergyIntolerance.code | allergies.DESCRIPTION | Display or text fallback | Human-readable description |
| AllergyIntolerance.type | allergies.TYPE | Lowercase | allergy|intolerance |
| AllergyIntolerance.category[0] | allergies.CATEGORY | Normalize | medication/food/environment |
| AllergyIntolerance.reaction[0].manifestation[0] | allergies.REACTION1 | Extract coding.code (SNOMED) | Optional |
| AllergyIntolerance.reaction[0].description | allergies.DESCRIPTION1 | Direct copy | Optional |
| AllergyIntolerance.reaction[0].severity | allergies.SEVERITY1 | Uppercase | MILD|MODERATE|SEVERE |
| AllergyIntolerance.reaction[1].manifestation[0] | allergies.REACTION2 | Extract coding.code (SNOMED) | Optional |
| AllergyIntolerance.reaction[1].description | allergies.DESCRIPTION2 | Direct copy | Optional |
| AllergyIntolerance.reaction[1].severity | allergies.SEVERITY2 | Uppercase | Optional |

## Clinical Status Handling
- If clinicalStatus indicates resolved/inactive but no `lastOccurrence`, output empty `STOP`.
- Otherwise, omit `STOP` if unknown.

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_synthea_csv.allergy.map_fhir_allergy_to_csv`
- Use existing reverse helpers to parse datetimes and extract codings/references.
