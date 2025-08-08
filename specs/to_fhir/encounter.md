# Encounter (Synthea encounters.csv → FHIR Encounter)

## Semantic Context
Encounters represent interactions between a patient and healthcare providers for the purpose of providing healthcare services or assessing the health status of a patient. This mapping transforms Synthea `encounters.csv` rows into FHIR R4 `Encounter` resources.

## Field Mappings
| Source Field | Target Field | Semantic Concept | Transform | Semantic Notes |
|--------------|--------------|------------------|-----------|----------------|
| encounters.Id | Encounter.id | Encounter Identity | Direct copy | Primary identifier |
| encounters.Start | Encounter.period.start | Start Date/Time | Format to FHIR datetime | ISO 8601 |
| encounters.Stop | Encounter.period.end | End Date/Time | Format to FHIR datetime | Optional |
| encounters.Patient | Encounter.subject | Patient Subject | Create reference `Patient/{id}` | Required |
| encounters.Organization | Encounter.serviceProvider | Managing Organization | Create reference `Organization/{id}` | Required |
| encounters.Provider | Encounter.participant[0].individual | Attending Practitioner | Create reference `Practitioner/{id}` | Required |
| encounters.EncounterClass | Encounter.class | Encounter Class | Map via ActCode lexicon | ambulatory/emergency/inpatient/wellness/urgentcare |
| encounters.Code | Encounter.type[0] | Encounter Type (SNOMED CT) | Create CodeableConcept (SNOMED) | Required |
| encounters.Description | Encounter.type[0].text | Encounter Type Text | Direct copy | Description of encounter |
| encounters.ReasonCode | Encounter.reasonCode[0] | Reason (SNOMED CT) | Create CodeableConcept (SNOMED) | Optional |
| encounters.ReasonDescription | Encounter.reasonCode[0].text | Reason Text | Direct copy | Optional |
| encounters.Payer | Encounter.extension(encounter-payer) | Payer Reference | Extension with valueReference `Organization/{id}` | Custom extension |
| encounters.Base_Encounter_Cost | Encounter.extension(baseCost) | Base Encounter Cost | Extension valueDecimal | Excludes line items |
| encounters.Total_Claim_Cost | Encounter.extension(totalClaimCost) | Total Claim Cost | Extension valueDecimal | Includes line items |
| encounters.Payer_Coverage | Encounter.extension(payerCoverage) | Payer Coverage | Extension valueDecimal | Amount covered by payer |

## Semantic Rules and Constraints
- Encounter.status is set to "finished" if Stop is present, otherwise "in-progress".
- Encounter.class uses HL7 v3 ActCode codings (e.g., AMB, EMER, IMP, ACUTE) via lexicon mapping.
- Encounter.type uses SNOMED CT coding system `http://snomed.info/sct`.
- Custom extension URLs used:
  - `http://example.org/fhir/StructureDefinition/encounter-baseCost`
  - `http://example.org/fhir/StructureDefinition/encounter-totalClaimCost`
  - `http://example.org/fhir/StructureDefinition/encounter-payerCoverage`
  - `http://example.org/fhir/StructureDefinition/encounter-payer` (valueReference)

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.encounter.map_encounter`
- Uses `encounter_class_lexicon` for class mapping.
- Leverages common transformers for date formatting and reference creation.
- Numeric costs are parsed as floats; invalid values are omitted.
