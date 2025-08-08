### Synthea payer_transitions.csv ➜ FHIR R4 Coverage

Maps a Synthea `payer_transitions.csv` row (insurance coverage changes over time) to a FHIR `Coverage` resource. The payer is represented as `Organization`; the beneficiary is the `Patient`.

## Field Mappings

| Source Field | Target Field | Notes |
|--------------|--------------|-------|
| Patient (UUID, req) | Coverage.beneficiary.reference | `Patient/{uuid}` |
| Member ID (UUID, opt) | Coverage.subscriberId | Alternatively could be an `identifier`, but `subscriberId` suffices |
| Start_Year (YYYY, req) | Coverage.period.start | Rendered as `YYYY-01-01` (inclusive start) |
| End_Year (YYYY, req) | Coverage.period.end | Rendered as `YYYY-12-31` (inclusive end) |
| Payer (UUID, req) | Coverage.payor[0].reference | `Organization/{uuid}` |
| Secondary Payer (UUID, opt) | Coverage.payor[1].reference | Additional payer reference if present |
| Ownership (Guardian|Self|Spouse, opt) | Coverage.relationship | Map to `subscriber-relationship` codes: `Self→self`, `Spouse→spouse`; `Guardian` stored as text if no standard code |
| Owner Name (opt) | Coverage.extension url=`http://synthea.mitre.org/fhir/StructureDefinition/policy-owner-name` valueString | Free-text name of policy owner if not linked to a managed resource |

Additional defaulting:

- Coverage.status: `active` (status is inferred from period; historical coverages may have end dates in the past but we do not set `inactive` here).
- Coverage.id: deterministic composite `cov-{Patient}-{Start_Year}-{Payer}`.

## Semantic Notes

- The payer organization is modeled via `Organization` and referenced in `Coverage.payor`.
- Only year precision is available in the CSV; we materialize start/end as the first and last day of the year respectively to respect inclusive semantics.
- `Coverage.relationship` uses `http://terminology.hl7.org/CodeSystem/subscriber-relationship` where possible. `Guardian` is retained as `text` if no exact standard code applies.
- While this dataset could inform `EnrollmentRequest`/`EnrollmentResponse`, those resources are not emitted here.

## Implementation Notes

- Owner free-text goes into a dedicated extension to avoid manufacturing unmanaged `Patient`/`RelatedPerson` references.
- If `Member ID` needs stronger modeling, a `Coverage.identifier` with a local system can be added in a future iteration.


