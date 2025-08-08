"""
Claims transactions mapper: Synthea CSV to FHIR R4 Claim and ClaimResponse resources.

Each CSV row yields:
- A Claim fragment containing contextual data and a single item (by Charge ID)
- A ClaimResponse fragment containing adjudication/payment for that item

Upstream aggregation is responsible for grouping all rows with the same Claim ID
into a single consolidated Claim/ClaimResponse if desired.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


LOCAL_TXN_TYPE_SYSTEM = "http://synthea.tools/CodeSystem/claims-transaction-type"
LOCAL_PAYMENT_METHOD_SYSTEM = "http://synthea.tools/CodeSystem/payment-method"


def _as_decimal(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return None


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for v in values:
        if v:
            return v
    return None


def _build_claim(src: Dict[str, Any]) -> Dict[str, Any]:
    """Build a FHIR Claim fragment for a single transaction row."""
    claim_id = src.get("Claim ID")
    patient_id = src.get("Patient ID")
    provider_id = src.get("Provider ID")
    facility_id = src.get("Place of Service")
    appointment_id = src.get("Appointment ID")

    # Item basics
    charge_id = src.get("Charge ID")
    try:
        sequence = int(charge_id) if charge_id is not None and str(charge_id).isdigit() else None
    except Exception:
        sequence = None

    product_code = src.get("Procedure Code")
    units = _as_decimal(src.get("Units"))
    unit_amount = _as_decimal(src.get("Unit Amount"))
    net_amount = _as_decimal(src.get("Amount"))

    diagnosis_sequences: List[int] = []
    for k in ["DiagnosisRef1", "DiagnosisRef2", "DiagnosisRef3", "DiagnosisRef4"]:
        v = src.get(k)
        try:
            if v is not None and str(v) != "":
                diagnosis_sequences.append(int(v))
        except Exception:
            continue

    notes_texts: List[str] = []
    for k in ["Notes", "Line Note"]:
        if t := src.get(k):
            notes_texts.append(str(t))

    item: Dict[str, Any] = {
        "sequence": sequence,
        "productOrService": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": product_code,
                    "display": _first_non_empty(src.get("Notes"), src.get("Line Note")),
                }
            ] if product_code else None,
            "text": product_code,
        } if product_code else None,
        "quantity": {"value": units} if units is not None else None,
        "unitPrice": {"value": unit_amount, "currency": "USD"} if unit_amount is not None else None,
        "net": {"value": net_amount, "currency": "USD"} if net_amount is not None else None,
        "diagnosisSequence": diagnosis_sequences or None,
        "encounter": [create_reference("Encounter", appointment_id)] if appointment_id else None,
    }

    # Clean item
    item = {k: v for k, v in item.items() if v is not None}

    claim: Dict[str, Any] = {
        "resourceType": "Claim",
        "id": claim_id,
        "patient": create_reference("Patient", patient_id) if patient_id else None,
        "provider": create_reference("Practitioner", provider_id) if provider_id else None,
        "facility": create_reference("Organization", facility_id) if facility_id else None,
        "billablePeriod": {
            "start": to_fhir_datetime(src.get("From Date")),
            "end": to_fhir_datetime(src.get("To Date")),
        } if (src.get("From Date") or src.get("To Date")) else None,
        "item": [item] if item else None,
        "note": [{"text": t} for t in notes_texts] if notes_texts else None,
        "insurance": [
            {
                "sequence": 1,
                "focal": True,
                "coverage": create_reference("Coverage", src.get("Patient Insurance ID")),
            }
        ] if src.get("Patient Insurance ID") else None,
    }

    # Optional supervising provider
    supervising_id = src.get("Supervising Provider ID")
    if supervising_id:
        claim["careTeam"] = [
            {
                "sequence": 1,
                "provider": create_reference("Practitioner", supervising_id),
                "role": {"text": "supervising"},
            }
        ]

    # Drop None values
    return {k: v for k, v in claim.items() if v is not None}


def _build_claim_response(src: Dict[str, Any]) -> Dict[str, Any]:
    """Build a FHIR ClaimResponse fragment for a single transaction row."""
    txn_id = src.get("Id")
    claim_id = src.get("Claim ID")
    patient_id = src.get("Patient ID")
    charge_id = src.get("Charge ID")
    try:
        item_seq = int(charge_id) if charge_id is not None and str(charge_id).isdigit() else None
    except Exception:
        item_seq = None

    txn_type = src.get("Type")
    method = src.get("Method")
    payments = _as_decimal(src.get("Payments"))
    adjustments = _as_decimal(src.get("Adjustments"))
    transfers = _as_decimal(src.get("Transfers"))
    outstanding = _as_decimal(src.get("Outstanding"))

    adjudications: List[Dict[str, Any]] = []

    def _adj(cat_code: str, amount: Optional[float]) -> Optional[Dict[str, Any]]:
        if amount is None:
            return None
        return {
            "category": {
                "coding": [
                    {"system": LOCAL_TXN_TYPE_SYSTEM, "code": cat_code}
                ]
            },
            "amount": {"value": amount, "currency": "USD"},
        }

    if payments is not None:
        adj = _adj("payment", payments)
        if adj:
            adjudications.append(adj)
    if adjustments is not None:
        adj = _adj("adjustment", adjustments)
        if adj:
            adjudications.append(adj)
    if transfers is not None:
        # encode transfer direction in reason.text (if available)
        reason_text = None
        if src.get("Transfer Out ID") or src.get("Transfer Type"):
            reason_text = f"transfer: out_id={src.get('Transfer Out ID')}, type={src.get('Transfer Type')}"
        adj = _adj("transfer", transfers)
        if adj:
            if reason_text:
                adj["reason"] = {"text": reason_text}
            adjudications.append(adj)

    notes: List[Dict[str, Any]] = []
    if outstanding is not None:
        notes.append({"text": f"Outstanding: {outstanding}"})
    for k in ["Notes", "Line Note"]:
        if t := src.get(k):
            notes.append({"text": str(t)})

    payment: Optional[Dict[str, Any]] = None
    if txn_type == "PAYMENT" and payments is not None:
        payment = {
            "type": {
                "coding": [
                    {"system": LOCAL_PAYMENT_METHOD_SYSTEM, "code": method}
                ] if method else None,
                "text": method if method else None,
            },
            "amount": {"value": payments, "currency": "USD"},
            "date": to_fhir_datetime(src.get("To Date")) or to_fhir_datetime(src.get("From Date")),
        }

    item: Optional[Dict[str, Any]] = None
    if item_seq is not None or adjudications:
        item = {
            "itemSequence": item_seq,
            "adjudication": adjudications or None,
        }
        item = {k: v for k, v in item.items() if v is not None}

    response: Dict[str, Any] = {
        "resourceType": "ClaimResponse",
        "id": txn_id,
        "status": "active",
        "outcome": "complete",
        "patient": create_reference("Patient", patient_id) if patient_id else None,
        "request": create_reference("Claim", claim_id) if claim_id else None,
        "item": [item] if item else None,
        "payment": payment,
        "note": notes or None,
        "insurer": None,
    }

    return {k: v for k, v in response.items() if v is not None}


def map_claims_transaction(row: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Convert a claims_transactions.csv row to a tuple of (Claim, ClaimResponse) fragments.

    Returns Claim and ClaimResponse dictionaries suitable for inclusion in a Bundle
    or for further aggregation.
    """
    return _build_claim(row), _build_claim_response(row)


