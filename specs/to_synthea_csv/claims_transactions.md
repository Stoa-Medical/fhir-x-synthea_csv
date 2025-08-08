### FHIR → CSV mapping: Claim / ClaimResponse to claims_transactions.csv

This spec defines how to produce `claims_transactions.csv` rows from FHIR R4 `Claim` and `ClaimResponse` resources.

Scope and approach
- From a `Claim`, we produce one `CHARGE` row per `Claim.item` (sequence is used as `Charge ID`).
- From a `ClaimResponse`, we produce a transaction row aligned to its first `item` (by `itemSequence`) with the appropriate `Type` and monetary fields (`Payments`, `Adjustments`, `Transfers`).
- When a single resource lacks fields required by CSV (e.g., `Procedure Code` inside `ClaimResponse`), fields are left blank. Upstream callers can merge data from `Claim` and `ClaimResponse` sharing the same `Claim ID` and `Charge ID` if complete rows are needed.

Claim → CSV (Type = CHARGE)
- Id: `txn-<Claim.id>-<item.sequence>` (deterministic synthetic id for the row)
- Claim ID: `Claim.id`
- Charge ID: `Claim.item.sequence`
- Patient ID: reference id from `Claim.patient`
- Type: `CHARGE`
- Amount: `Claim.item.net.value`
- From Date: `Claim.billablePeriod.start`
- To Date: `Claim.billablePeriod.end`
- Place of Service: reference id from `Claim.facility`
- Procedure Code: first coding code from `Claim.item.productOrService`
- Modifier1/Modifier2: first two modifiers from `Claim.item.modifier` codes if present
- DiagnosisRef1..4: first 4 integers from `Claim.item.diagnosisSequence`
- Units: `Claim.item.quantity.value`
- Notes/Line Note: from `Claim.note[].text`
- Unit Amount: `Claim.item.unitPrice.value`
- Appointment ID: reference id from first `Claim.item.encounter`
- Patient Insurance ID: reference id from `Claim.insurance[0].coverage`
- Provider ID: reference id from `Claim.provider`
- Supervising Provider ID: from `Claim.careTeam` entry where role.text == `supervising` (if any)
- All other CSV fields: left blank.

ClaimResponse → CSV (Type in {PAYMENT, ADJUSTMENT, TRANSFERIN, TRANSFEROUT})
- Id: `ClaimResponse.id`
- Claim ID: reference id from `ClaimResponse.request`
- Charge ID: first `item.itemSequence` (if present)
- Patient ID: reference id from `ClaimResponse.patient`
- Type: derived from adjudication/payment as follows:
  - If `ClaimResponse.payment.amount` present → `PAYMENT`
  - Else if an adjudication with category code `adjustment` (local) → `ADJUSTMENT`
  - Else if adjudication with category code `transfer` (local) → `TRANSFERIN` (positive amount) or `TRANSFEROUT` (negative amount)
  - Else default to `PAYMENT` if any adjudication has amount.
- Method: from `ClaimResponse.payment.type` (coding.code or text)
- Payments/Adjustments/Transfers: set from corresponding amounts; precedence as above
- Outstanding: if a note contains `Outstanding: <amount>`, extract amount
- From/To Date: leave blank unless present in `ClaimResponse.payment.date`
- Place of Service, Procedure Code, Provider ID, etc.: left blank if not present in ClaimResponse

Formatting rules
- Dates are converted to Synthea CSV style (ISO 8601 string accepted by this project).
- Unknown values are empty strings. Numeric values are stringified without altering the numeric value.

Limitations
- `ClaimResponse` does not carry certain line-level attributes required by CSV; complete enrichment requires joining with the corresponding `Claim` by `Claim ID` and `Charge ID`.


