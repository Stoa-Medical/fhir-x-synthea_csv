### Synthea supplies.csv ➜ FHIR R4 SupplyDelivery

This spec defines how a single row from Synthea `supplies.csv` maps to a FHIR R4 `SupplyDelivery` resource. The CSV records supplies used (fulfilled), which aligns most closely with `SupplyDelivery`.

- **Date (required, Date)**
  - CSV: `DATE` (YYYY-MM-DD)
  - FHIR: `occurrenceDateTime`
  - Transform: date → FHIR dateTime (ISO 8601). If only a date is present, time defaults to 00:00:00+00:00.

- **Patient (required, UUID)**
  - CSV: `PATIENT`
  - FHIR: `patient` (Reference(Patient))
  - Transform: `Patient/{PATIENT}`

- **Encounter (required, UUID)**
  - CSV: `ENCOUNTER`
  - FHIR: Extension `http://hl7.org/fhir/StructureDefinition/resource-encounter` with `valueReference` = `Encounter/{ENCOUNTER}`
  - Rationale: `SupplyDelivery` in R4 does not have an `encounter` element, so the standard Resource Encounter extension is used.

- **Code (required, String; SNOMED-CT)**
  - CSV: `CODE`
  - FHIR: `suppliedItem.itemCodeableConcept.coding[0]`
  - Transform: `system` = `http://snomed.info/sct`, `code` = CSV `CODE`, `display` = CSV `DESCRIPTION`; also set `suppliedItem.itemCodeableConcept.text` = `DESCRIPTION`.

- **Description (required, String)**
  - CSV: `DESCRIPTION`
  - FHIR: `suppliedItem.itemCodeableConcept.text` and `coding.display`

- **Quantity (required, Numeric)**
  - CSV: `QUANTITY`
  - FHIR: `suppliedItem.quantity.value`
  - Transform: numeric conversion; no unit is assumed.

- **Additional elements**
  - `resourceType` = `SupplyDelivery`
  - `status` = `completed` (since supplies were used/fulfilled)
  - `id` = deterministic string: `supply-{PATIENT}-{DATE}{time?}-{CODE}` (non-normative, for consistency with other mappers)

### Notes on SupplyRequest

While `supplies.csv` best represents fulfillment (`SupplyDelivery`), the following correspondences are common if a request view is desired:

- Date → `SupplyRequest.authoredOn`
- Patient → `SupplyRequest.subject`
- Encounter → same extension `resource-encounter`
- Code/Description → `SupplyRequest.itemCodeableConcept`
- Quantity → `SupplyRequest.quantity`

This library’s forward mapper produces `SupplyDelivery` per above.


