# Encounter (FHIR → Synthea encounters.csv)

## Primary Source Resource
- Encounter

## Field Mappings
| Source Field | Target Field | Transform | Notes |
|--------------|--------------|-----------|-------|
| Encounter.period.start | encounters.Start | Parse FHIR datetime → Synthea format | Required |
| Encounter.period.end | encounters.Stop | Parse FHIR datetime → Synthea format | Optional |
| Encounter.subject | encounters.Patient | Extract reference id | Patient/{id} |
| Encounter.serviceProvider | encounters.Organization | Extract reference id | Organization/{id} |
| Encounter.participant[0].individual | encounters.Provider | Extract reference id | Practitioner/{id} |
| Encounter.class | encounters.EncounterClass | Map ActCode → Synthea string | ambulatory/emergency/inpatient/wellness/urgentcare |
| Encounter.type[0] (SNOMED) | encounters.Code | Extract coding by SNOMED system | Fallback to first coding |
| Encounter.type[0] | encounters.Description | Display or text fallback | |
| Encounter.reasonCode[0] (SNOMED) | encounters.ReasonCode | Extract coding by SNOMED system | Optional |
| Encounter.reasonCode[0] | encounters.ReasonDescription | Display or text fallback | Optional |
| ext(encounter-baseCost) | encounters.Base_Encounter_Cost | Extract extension valueDecimal | URL: `.../encounter-baseCost` |
| ext(encounter-totalClaimCost) | encounters.Total_Claim_Cost | Extract extension valueDecimal | URL: `.../encounter-totalClaimCost` |
| ext(encounter-payerCoverage) | encounters.Payer_Coverage | Extract extension valueDecimal | URL: `.../encounter-payerCoverage` |
| ext(encounter-payer) | encounters.Payer | Extract valueReference id | Organization/{id} |

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_synthea_csv.encounter.map_fhir_encounter_to_csv`
- Status is not represented in encounters.csv; we infer Stop presence only for status when converting the other direction.
