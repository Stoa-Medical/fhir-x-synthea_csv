# Medication (FHIR → medications.csv)

## Primary Source Resource
- MedicationRequest

## Field Mappings
| Source Field | Target Field | Transform | Notes |
|--------------|--------------|-----------|-------|
| MedicationRequest.authoredOn or occurrencePeriod.start | medications.Start | Parse FHIR datetime → Synthea format | Prefer authoredOn |
| MedicationRequest.occurrencePeriod.end | medications.Stop | Parse FHIR datetime | Optional |
| MedicationRequest.subject | medications.Patient | Extract reference id | Patient/{id} |
| MedicationRequest.encounter | medications.Encounter | Extract reference id | Encounter/{id} |
| MedicationRequest.insurance[0] | medications.Payer | Extract reference id | Coverage/{id} or Organization/{id} |
| MedicationRequest.medicationCodeableConcept (RxNorm) | medications.Code | Extract coding by RxNorm system | Fallback to first coding |
| MedicationRequest.medicationCodeableConcept | medications.Description | Display or text fallback | |
| MedicationRequest.dispenseRequest.numberOfRepeatsAllowed | medications.Dispenses | Stringify | |
| MedicationRequest.reasonCode[0] | medications.ReasonCode | SNOMED coding code | Fallback to first coding |
| MedicationRequest.reasonCode[0] | medications.ReasonDescription | SNOMED display or text | |
| ext(baseCost) | medications.Base_Cost | Extract extension valueDecimal | URL: `.../medication-baseCost` |
| ext(payerCoverage) | medications.Payer_Coverage | Extract extension valueDecimal | URL: `.../medication-payerCoverage` |
| ext(totalCost) | medications.TotalCost | Extract extension valueDecimal | URL: `.../medication-totalCost` |

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_synthea_csv.medication.map_fhir_medication_request_to_csv`
- Only `MedicationRequest` is supported for now. `MedicationDispense`/`MedicationAdministration` can be added later.

