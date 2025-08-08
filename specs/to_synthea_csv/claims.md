### FHIR → CSV mapping: Claim to claims.csv

This spec defines how a FHIR R4 `Claim` resource is flattened into a `claims.csv` row. Fields related to adjudication or balances are not available on Claim and remain blank unless implementers derive them from `ClaimResponse`.

Field mapping
- Id ← Claim.id (business identifier may be ignored if present).
- Patient ID ← Claim.patient.reference id.
- Provider ID ← Claim.provider.reference id.
- Primary Patient Insurance ID ← the first Claim.insurance entry (sequence 1 or focal=true) coverage reference id.
- Secondary Patient Insurance ID ← the second Claim.insurance entry (sequence 2 or focal=false) coverage reference id.
- Department ID, Patient Department ID ← from Claim.extension with URLs:
  - `http://synthea.tools/StructureDefinition/department-id`
  - `http://synthea.tools/StructureDefinition/patient-department-id`
- Diagnosis1..Diagnosis8 ← Claim.diagnosis[].diagnosisCodeableConcept: take up to 8 SNOMED CT codes in sequence order (fallback to text if no coding).
- Referring Provider ID ← not available from Claim alone; leave blank unless a resolvable Claim.referral to ServiceRequest exists and can be dereferenced; then emit the requester Practitioner id.
- Appointment ID ← from the first Claim.item.encounter reference id if present; otherwise blank.
- Current Illness Date ← from Claim.event where event.type code = `onset` (system `http://synthea.tools/CodeSystem/claim-event`).
- Service Date ← from Claim.billablePeriod.start (prefer start); if only end is present, use end.
- Supervising Provider ID ← from Claim.careTeam where role.text = `supervising`, provider reference id.
- Status1, Status2, StatusP ← not on Claim; leave blank. (May be populated by `ClaimResponse` processing.)
- Outstanding1, Outstanding2, OutstandingP ← not on Claim; leave blank.
- LastBilledDate1/2/P ← from Claim.event where type codes are `bill-primary`, `bill-secondary`, `bill-patient` respectively.
- HealthcareClaimTypeID1/2 ← derived from Claim.type/subType:
  - professional → 1
  - institutional → 2
  Unknown/other → leave blank.

Formatting
- Dates are rendered as `YYYY-MM-DD` (or `YYYY-MM-DD HH:MM:SS` if time is present); helper functions normalize values.

Limitations
- Values that originate from adjudication/payment (statuses, outstanding) require `ClaimResponse` and are not populated here.


