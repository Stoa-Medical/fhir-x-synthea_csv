# CarePlan

## Semantic Context
The CarePlan resource represents a healthcare plan for a patient over a period of time. This mapping transforms Synthea CSV careplan data into FHIR R4 CarePlan resources.

## Field Mappings
| Source Field | Target Field | Semantic Concept | Transform | Notes |
|--------------|--------------|------------------|-----------|-------|
| careplans.Id | CarePlan.id | Resource Identifier | Direct copy | Primary key from CSV |
| careplans.Start | CarePlan.period.start | Plan start date | Format as YYYY-MM-DD | When plan was initiated |
| careplans.Stop | CarePlan.period.end | Plan end date | Format as YYYY-MM-DD | When plan ended (if applicable) |
| careplans.Patient | CarePlan.subject | Patient Reference | Create Reference("Patient/{id}") | Patient the plan is for |
| careplans.Encounter | CarePlan.encounter | Encounter Reference | Create Reference("Encounter/{id}") | Encounter where plan initiated |
| careplans.Code | CarePlan.category[0].coding[0].code | SNOMED Code | Direct copy | SNOMED CT care plan concept |
| careplans.Description | CarePlan.category[0].coding[0].display | Code Display | Direct copy | Human-readable display |
| careplans.Code | CarePlan.category[0].coding[0].system | Code System | Set to "http://snomed.info/sct" | SNOMED CT system |
| careplans.Description | CarePlan.title | Plan title | Direct copy | Fallback title |
| careplans.Description | CarePlan.description | Plan description | Direct copy | Narrative description |
| - | CarePlan.status | Plan status | Derive from Stop | "completed" if Stop present, else "active" |
| - | CarePlan.intent | Plan intent | Set to "plan" | Default intent for CSV-based plan |
| careplans.ReasonCode, careplans.ReasonDescription | CarePlan.note[0].text | Reason for plan | Concatenate ("Reason: {desc} ({code})") | R4 has no top-level reasonCode; encoded in note |

## R5 Note
In FHIR R5, `CarePlan.reason`/`reasonCode` is available. This mapping targets R4; reason is preserved in `CarePlan.note.text` for round-trip fidelity.