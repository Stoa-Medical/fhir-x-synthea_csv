### FHIR R4 Coverage ➜ Synthea payer_transitions.csv

Maps a FHIR `Coverage` resource back to a `payer_transitions.csv` row.

## Field Mappings

| Target Field | Source | Notes |
|--------------|--------|-------|
| Patient | Coverage.beneficiary.reference | Extract `Patient/{id}` → `id` |
| Member ID | Coverage.subscriberId or Coverage.identifier | Prefer `subscriberId`; else first identifier.value |
| Start_Year | Coverage.period.start | Year component of date (YYYY) |
| End_Year | Coverage.period.end | Year component of date (YYYY) |
| Payer | Coverage.payor[0].reference | Extract `Organization/{id}` → `id` |
| Secondary Payer | Coverage.payor[1].reference | Optional second payer id if present |
| Ownership | Coverage.relationship | Map codes from `subscriber-relationship` to `Self`/`Spouse`; if unknown but text present and equals `Guardian`, emit `Guardian`; otherwise empty |
| Owner Name | Coverage.extension url=`http://synthea.mitre.org/fhir/StructureDefinition/policy-owner-name` valueString | Optional |

## Notes

- If dates are missing, emit empty strings; CSV schema allows blanks.
- Year extraction should be robust to full datetime strings.
- Unknown relationship codes map to empty string to avoid incorrect semantics.


