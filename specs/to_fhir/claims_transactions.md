### CSV → FHIR mapping: claims_transactions.csv to Claim and ClaimResponse

This spec defines how a single row in `claims_transactions.csv` maps into elements of FHIR R4 `Claim` and/or `ClaimResponse` resources. The CSV represents transactions at the line-item level. We map line-item attributes to `Claim.item` and financial outcomes to `ClaimResponse.item.adjudication` (and top-level `payment` when applicable).

Assumptions and scope
- One CSV row corresponds to one Claim line item (identified by `Claim ID` + `Charge ID`) and may also carry adjudication/payment info for that line item.
- We do not aggregate multiple CSV rows into a single Claim/ClaimResponse here; instead, each row can produce:
  - a `Claim` skeleton focusing on a single `item` and contextual fields, and
  - a `ClaimResponse` skeleton referencing the `Claim` and the same `item` sequence with adjudication data.
- Codes for transaction `Type` and `Method` are captured in CodeableConcepts using local code systems where HL7 core codes do not provide a precise fit, keeping values in `code` and/or `text` for round-trip fidelity.

Required CSV → FHIR field mapping
- Id → ClaimResponse.id (unique per transaction). Also carried as Claim.item.extension (for traceability across resources).
- Claim ID → Claim.id. Also referenced by ClaimResponse.request = `Claim/{Claim ID}`.
- Charge ID → Claim.item.sequence (integer). Also ClaimResponse.item.itemSequence.
- Patient ID → Claim.patient = `Patient/{Patient ID}` and ClaimResponse.patient.
- Place of Service → Claim.facility = `Organization/{Place of Service}`.
- Procedure Code → Claim.item.productOrService.coding[0].system = `http://snomed.info/sct` (or textual only if unknown), code = value, display = from `Notes`/`Line Note` if present.
- Provider ID → Claim.provider = `Practitioner/{Provider ID}`.

Dates and period
- From Date → Claim.billablePeriod.start (ISO 8601).
- To Date → Claim.billablePeriod.end (ISO 8601).
- Appointment ID (Encounter) → Claim.item.encounter[0] = `Encounter/{Appointment ID}` if present.

Quantities and amounts
- Units → Claim.item.quantity.value.
- Unit Amount → Claim.item.unitPrice.value.
- Amount (for `CHARGE` or `TRANSFERIN`) → Claim.item.net.value.

Diagnosis references
- DiagnosisRef1..4 (integers 1–8) → Claim.item.diagnosisSequence = [list of integers]. These refer to `Claim.diagnosis` entries defined at the claim level. Since this CSV row does not carry the actual diagnosis codes, we only carry the sequences here.

Transaction semantics and adjudication (ClaimResponse)
- Type → ClaimResponse.item.adjudication.category with a local system `http://synthea.tools/CodeSystem/claims-transaction-type` and code in {`CHARGE`, `PAYMENT`, `ADJUSTMENT`, `TRANSFERIN`, `TRANSFEROUT`}.
- Method → ClaimResponse.payment.type as CodeableConcept using local system `http://synthea.tools/CodeSystem/payment-method` and code from CSV; also set ClaimResponse.payment.date from `To Date` if present.
- Payments → If present and Type = `PAYMENT`, map to ClaimResponse.payment.amount.value and also include an adjudication with category code `payment` (local) and amount.
- Adjustments → If present and Type = `ADJUSTMENT`, include adjudication with category code `adjustment` (local) and amount.
- Transfers → If present and Type in {`TRANSFERIN`, `TRANSFEROUT`}, include adjudication with category code `transfer` (local) and amount. Carry `Transfer Out ID` and `Transfer Type` as adjudication.reason.text.
- Outstanding → If present, carry as ClaimResponse.item.note.text (append-only) in the form `Outstanding: <amount>`.

Other CSV fields
- Department ID, Fee Schedule ID → captured as Claim.item.note text if present.
- Notes and/or Line Note → Claim.item.detail.note.text if using details; otherwise include in Claim.note[].text for simplicity. Implementation uses Claim.note[].text.
- Supervising Provider ID → optional Claim.careTeam entry with role.text = `supervising` and provider reference.
- Patient Insurance ID → Claim.insurance[0].coverage = `Coverage/{Patient Insurance ID}` (if present). Also mirrored to ClaimResponse.insurance when needed.
- Transfer Out ID, Transfer Type → as noted above in adjudication.reason.text.

Data typing and formatting
- All dates are emitted as ISO 8601 strings (e.g., `YYYY-MM-DD` or `YYYY-MM-DDThh:mm:ss+00:00`) consistent with the rest of this library.
- Numeric fields (`Units`, `Unit Amount`, `Amount`, `Payments`, `Adjustments`, `Transfers`, `Outstanding`) are mapped to decimal values in FHIR and preserved as strings on CSV round-trip.

Limitations
- This mapping produces self-contained `Claim`/`ClaimResponse` fragments per transaction; assembling a full Claim with multiple items requires upstream grouping by `Claim ID`.
- Standard adjudication categories are not exhaustive for all Synthea transaction types; we therefore use a local code system to preserve semantics without loss.


