### CSV → FHIR mapping: claims.csv to Claim (and related)

This spec defines how `claims.csv` rows map into elements of the FHIR R4 `Claim` resource. Some fields reflect claim lifecycle and adjudication semantics which, in FHIR, belong to `ClaimResponse`. Where appropriate, we note those relationships.

Assumptions
- Each `claims.csv` row represents a single insurance claim submitted by a provider on behalf of a patient.
- The mapping targets FHIR R4. Elements introduced in R5 (e.g., `Claim.encounter`) are represented using R4-compatible structures (e.g., `Claim.item.encounter`).
- Codes are preserved in `code` and, when known, expressed with standard systems.

Field mapping
- Id → Claim.id. Also include a business identifier in Claim.identifier (system `urn:synthea:claim`).
- Patient ID → Claim.patient = `Patient/{Patient ID}`.
- Provider ID → Claim.provider = `Practitioner/{Provider ID}`.
- Primary Patient Insurance ID → Claim.insurance[0]:
  - sequence = 1, focal = true
  - coverage = `Coverage/{Primary Patient Insurance ID}`
- Secondary Patient Insurance ID → Claim.insurance[1]:
  - sequence = 2, focal = false
  - coverage = `Coverage/{Secondary Patient Insurance ID}`
- Department ID, Patient Department ID → No direct standard element; map as top-level Claim.extension entries with URLs:
  - `http://synthea.tools/StructureDefinition/department-id`
  - `http://synthea.tools/StructureDefinition/patient-department-id`
  Each uses `valueString` with the CSV value.
- Diagnosis1..Diagnosis8 (SNOMED CT codes) → Claim.diagnosis[] entries:
  - diagnosis.sequence = 1..8 for populated codes in order
  - diagnosis.diagnosisCodeableConcept.coding[0].system = `http://snomed.info/sct`, code = the DiagnosisN value
- Referring Provider ID → Ideally Claim.referral = `ServiceRequest/{id}`. Since only a Practitioner ID is given, this cannot be a resolvable reference without an existing ServiceRequest. Omit by default; implementations may introduce a ServiceRequest if available.
- Appointment ID → Represent in R4 as Claim.item[0].encounter[0] = `Encounter/{Appointment ID}`.
- Current Illness Date → Claim.event[] entry:
  - event.type: local CodeableConcept system `http://synthea.tools/CodeSystem/claim-event`, code = `onset`
  - event.whenDateTime = the date
  Alternatively, this may be encoded on a referenced Condition.onset[x] in clinical data; this spec uses Claim.event to keep claim-centric fidelity.
- Service Date → Claim.billablePeriod with start = end = service date.
- Supervising Provider ID → Claim.careTeam[] entry with:
  - sequence = 1
  - provider = `Practitioner/{Supervising Provider ID}`
  - role.text = `supervising`
- Status1 (Primary), Status2 (Secondary), StatusP (Patient) → Do not map to Claim.status (which reflects resource lifecycle, e.g., `active`/`cancelled`). These statuses reflect adjudication lifecycle and belong in ClaimResponse. Preserve optionally as Claim.note[].text for traceability.
- Outstanding1/2/P → Adjudication/financial semantics are in ClaimResponse; do not map to Claim. Preserve optionally as Claim.note[].text for traceability (e.g., `Outstanding1: 123.45`).
- LastBilledDate1/2/P → Claim.event[] entries with event.type codes `bill-primary`, `bill-secondary`, `bill-patient` and event.whenDateTime set to the respective date.
- HealthcareClaimTypeID1/2 → Claim.type and Claim.subType:
  - 1 → `professional`
  - 2 → `institutional`
  Use system `http://terminology.hl7.org/CodeSystem/claim-type` for type codes; carry subtype as a textual refinement in Claim.subType (same system when applicable), or omit if not provided.

Data typing and formatting
- Dates are emitted in ISO 8601 (YYYY-MM-DD or full datetime). This library normalizes via helpers.
- Amounts are not on Claim in this CSV; any amounts present (Outstanding*) are not mapped to Claim elements.

Notes
- This spec intentionally scopes to a self-contained Claim resource using R4 elements. Any adjudication, amounts due, or final outcome should be produced as `ClaimResponse` using other CSV sources (e.g., `claims_transactions.csv`).


