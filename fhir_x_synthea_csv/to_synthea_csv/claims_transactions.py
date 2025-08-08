"""
Reverse mapper: FHIR R4 Claim / ClaimResponse to Synthea claims_transactions.csv rows.

Two helpers are provided:
- map_fhir_claim_to_claims_transactions: one CHARGE row per Claim.item
- map_fhir_claimresponse_to_claims_transaction: a single row for adjudication/payment

Fields not present on the source resource are left as empty strings.
"""

from typing import Any, Dict, List, Optional

from ..common.reverse_transformers import (
    extract_reference_id,
    extract_coding_by_system,
    parse_fhir_datetime,
)


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _first_coding_code(codeable: Optional[Dict[str, Any]]) -> Optional[str]:
    if not codeable or not isinstance(codeable, dict):
        return None
    coding = codeable.get("coding")
    if isinstance(coding, list) and coding:
        first = coding[0]
        if isinstance(first, dict):
            return first.get("code") or codeable.get("text")
    return codeable.get("text")


def _collect_notes(resource: Dict[str, Any]) -> str:
    notes = resource.get("note")
    if not isinstance(notes, list):
        return ""
    texts: List[str] = []
    for n in notes:
        if isinstance(n, dict) and n.get("text"):
            texts.append(str(n.get("text")))
    return "; ".join(texts)


def _get_supervising_provider_id(claim: Dict[str, Any]) -> str:
    care_team = claim.get("careTeam")
    if not isinstance(care_team, list):
        return ""
    for entry in care_team:
        if not isinstance(entry, dict):
            continue
        role = entry.get("role")
        role_text = role.get("text") if isinstance(role, dict) else None
        if (role_text and role_text.lower() == "supervising") or not role_text:
            pid = extract_reference_id(entry.get("provider"))
            if pid:
                return pid
    return ""


def map_fhir_claim_to_claims_transactions(claim: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Produce CHARGE rows for each Claim.item."""
    if not claim or claim.get("resourceType") != "Claim":
        raise ValueError("Input must be a FHIR Claim resource")

    claim_id = claim.get("id")
    patient_id = extract_reference_id(claim.get("patient"))
    provider_id = extract_reference_id(claim.get("provider"))
    facility_id = extract_reference_id(claim.get("facility"))
    billable = claim.get("billablePeriod") or {}
    from_date = parse_fhir_datetime(billable.get("start"))
    to_date = parse_fhir_datetime(billable.get("end"))
    insurance = claim.get("insurance")
    member_id = None
    if isinstance(insurance, list) and insurance:
        member_id = extract_reference_id(insurance[0].get("coverage"))
    supervising_id = _get_supervising_provider_id(claim)
    claim_notes = _collect_notes(claim)

    rows: List[Dict[str, Any]] = []
    items = claim.get("item") or []
    for item in items:
        if not isinstance(item, dict):
            continue
        seq = item.get("sequence")
        proc_code = _first_coding_code(item.get("productOrService"))
        quantity = item.get("quantity") or {}
        units = quantity.get("value")
        unit_price = (item.get("unitPrice") or {}).get("value")
        net_amount = (item.get("net") or {}).get("value")
        enc_list = item.get("encounter") or []
        appt_id = None
        if isinstance(enc_list, list) and enc_list:
            appt_id = extract_reference_id(enc_list[0])
        diag_seq = item.get("diagnosisSequence") or []
        diag_seq = [str(d) for d in diag_seq if d is not None]

        row: Dict[str, Any] = {
            "Id": f"txn-{claim_id}-{seq}" if claim_id and seq is not None else "",
            "Claim ID": _safe_str(claim_id),
            "Charge ID": _safe_str(seq),
            "Patient ID": _safe_str(patient_id),
            "Type": "CHARGE",
            "Amount": _safe_str(net_amount),
            "Method": "",
            "From Date": _safe_str(from_date),
            "To Date": _safe_str(to_date),
            "Place of Service": _safe_str(facility_id),
            "Procedure Code": _safe_str(proc_code),
            "Modifier1": "",
            "Modifier2": "",
            "DiagnosisRef1": diag_seq[0] if len(diag_seq) > 0 else "",
            "DiagnosisRef2": diag_seq[1] if len(diag_seq) > 1 else "",
            "DiagnosisRef3": diag_seq[2] if len(diag_seq) > 2 else "",
            "DiagnosisRef4": diag_seq[3] if len(diag_seq) > 3 else "",
            "Units": _safe_str(units),
            "Department ID": "",
            "Notes": claim_notes,
            "Unit Amount": _safe_str(unit_price),
            "Transfer Out ID": "",
            "Transfer Type": "",
            "Payments": "",
            "Adjustments": "",
            "Transfers": "",
            "Outstanding": "",
            "Appointment ID": _safe_str(appt_id),
            "Line Note": "",
            "Patient Insurance ID": _safe_str(member_id),
            "Fee Schedule ID": "",
            "Provider ID": _safe_str(provider_id),
            "Supervising Provider ID": _safe_str(supervising_id),
        }

        # Ensure empty strings for missing values
        for k, v in list(row.items()):
            if v is None:
                row[k] = ""

        rows.append(row)

    return rows


def map_fhir_claimresponse_to_claims_transaction(claim_response: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a non-CHARGE transaction row from ClaimResponse."""
    if not claim_response or claim_response.get("resourceType") != "ClaimResponse":
        raise ValueError("Input must be a FHIR ClaimResponse resource")

    rid = claim_response.get("id")
    patient_id = extract_reference_id(claim_response.get("patient"))
    request_id = extract_reference_id(claim_response.get("request"))

    item_list = claim_response.get("item") or []
    item_seq = None
    adjudication = []
    if isinstance(item_list, list) and item_list:
        first_item = item_list[0]
        if isinstance(first_item, dict):
            item_seq = first_item.get("itemSequence")
            adjudication = first_item.get("adjudication") or []

    method = None
    payments_val = ""
    adjustments_val = ""
    transfers_val = ""
    txn_type = ""

    payment = claim_response.get("payment") or {}
    if payment.get("amount") and payment["amount"].get("value") is not None:
        txn_type = "PAYMENT"
        payments_val = _safe_str(payment["amount"]["value"])
        # Try to extract method text or code
        ptype = payment.get("type")
        if isinstance(ptype, dict):
            coding = ptype.get("coding")
            if isinstance(coding, list) and coding and isinstance(coding[0], dict):
                method = coding[0].get("code") or ptype.get("text")
            else:
                method = ptype.get("text")

    # If not a payment, inspect adjudications
    if not txn_type and isinstance(adjudication, list):
        for adj in adjudication:
            if not isinstance(adj, dict):
                continue
            category = adj.get("category")
            code = _first_coding_code(category)
            amount = (adj.get("amount") or {}).get("value")
            if code == "adjustment" and amount is not None:
                txn_type = "ADJUSTMENT"
                adjustments_val = _safe_str(amount)
                break
            if code == "transfer" and amount is not None:
                # Direction cannot be derived without context; default to TRANSFERIN
                txn_type = "TRANSFERIN"
                transfers_val = _safe_str(amount)
                break

    # Fallback if any adjudication had amount
    if not txn_type and isinstance(adjudication, list):
        for adj in adjudication:
            amount = (adj.get("amount") or {}).get("value")
            if amount is not None:
                txn_type = "PAYMENT"
                payments_val = _safe_str(amount)
                break

    row: Dict[str, Any] = {
        "Id": _safe_str(rid),
        "Claim ID": _safe_str(request_id),
        "Charge ID": _safe_str(item_seq),
        "Patient ID": _safe_str(patient_id),
        "Type": _safe_str(txn_type),
        "Amount": "",
        "Method": _safe_str(method),
        "From Date": "",
        "To Date": _safe_str(parse_fhir_datetime((payment.get("date") if isinstance(payment, dict) else None))),
        "Place of Service": "",
        "Procedure Code": "",
        "Modifier1": "",
        "Modifier2": "",
        "DiagnosisRef1": "",
        "DiagnosisRef2": "",
        "DiagnosisRef3": "",
        "DiagnosisRef4": "",
        "Units": "",
        "Department ID": "",
        "Notes": _collect_notes(claim_response),
        "Unit Amount": "",
        "Transfer Out ID": "",
        "Transfer Type": "",
        "Payments": _safe_str(payments_val),
        "Adjustments": _safe_str(adjustments_val),
        "Transfers": _safe_str(transfers_val),
        "Outstanding": "",  # could parse from notes if necessary
        "Appointment ID": "",
        "Line Note": "",
        "Patient Insurance ID": "",
        "Fee Schedule ID": "",
        "Provider ID": "",
        "Supervising Provider ID": "",
    }

    # Normalize Nones to empty strings
    for k, v in list(row.items()):
        if v is None:
            row[k] = ""

    return row


