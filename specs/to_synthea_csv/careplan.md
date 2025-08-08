# CarePlan (FHIR → careplans.csv)

## Primary Source Resource
- CarePlan

## Field Mappings
| Source Field | Target Field | Transform | Notes |
|--------------|--------------|-----------|-------|
| CarePlan.id | careplans.Id | Direct | Logical id |
| CarePlan.period.start | careplans.Start | Parse FHIR datetime → Synthea format | |
| CarePlan.period.end | careplans.Stop | Parse FHIR datetime | Optional |
| CarePlan.subject | careplans.Patient | Extract reference id | Patient/{id} |
| CarePlan.encounter | careplans.Encounter | Extract reference id | Encounter/{id} |
| CarePlan.category[0] (SNOMED) | careplans.Code | Extract coding by SNOMED system | Fallback to first coding |
| CarePlan.description or title | careplans.Description | Prefer description; fallback title | |
| CarePlan.reasonCode[0] (SNOMED) | careplans.ReasonCode | Extract coding code | Fallback to first coding |
| CarePlan.reasonCode[0] (SNOMED) | careplans.ReasonDescription | Extract display or text | |

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_synthea_csv.careplan.map_fhir_careplan_to_csv`
- `CarePlan.addresses` is not mapped unless a concrete `Condition` id is present in source data.
