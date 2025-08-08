### FHIR R4 SupplyDelivery ➜ Synthea supplies.csv

This spec defines how a FHIR R4 `SupplyDelivery` resource maps back to a Synthea `supplies.csv` row.

- **DATE (required, Date)**
  - FHIR: `occurrenceDateTime` (or `occurrencePeriod.start` if present)
  - CSV: `DATE` (YYYY-MM-DD)
  - Transform: parse FHIR dateTime to date-only string.

- **PATIENT (required, UUID)**
  - FHIR: `patient.reference` → `Patient/{id}`
  - CSV: `PATIENT` = extracted `{id}`

- **ENCOUNTER (required, UUID)**
  - FHIR: Extension `http://hl7.org/fhir/StructureDefinition/resource-encounter` with `valueReference` → `Encounter/{id}`
  - CSV: `ENCOUNTER` = extracted `{id}`; empty if extension missing.

- **CODE (required, String; SNOMED-CT)**
  - FHIR: `suppliedItem.itemCodeableConcept.coding` (prefer `system` = `http://snomed.info/sct`; else first coding)
  - CSV: `CODE` = `coding.code`

- **DESCRIPTION (required, String)**
  - FHIR: Prefer `coding.display`; fallback to `itemCodeableConcept.text`
  - CSV: `DESCRIPTION`

- **QUANTITY (required, Numeric)**
  - FHIR: `suppliedItem.quantity.value`
  - CSV: `QUANTITY` = numeric value (stringified)

### Accepted FHIR variants

- If `occurrencePeriod` present, use `.start` for DATE; otherwise `occurrenceDateTime`.
- If no SNOMED coding, use first available coding.
- If no `resource-encounter` extension, output `ENCOUNTER` empty.


