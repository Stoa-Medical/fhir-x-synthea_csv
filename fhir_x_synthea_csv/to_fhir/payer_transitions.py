"""
Payer transitions mapper: Synthea payer_transitions.csv ➜ FHIR R4 Coverage.
"""

from typing import Any, Dict, Optional, List

from ..common.transformers import create_reference


def _compose_period(start_year: Optional[str], end_year: Optional[str]) -> Optional[Dict[str, str]]:
    if not start_year and not end_year:
        return None
    period: Dict[str, str] = {}
    if start_year:
        # Inclusive year start
        period["start"] = f"{str(start_year)}-01-01"
    if end_year:
        # Inclusive year end
        period["end"] = f"{str(end_year)}-12-31"
    return period or None


def _relationship_code(ownership: Optional[str]) -> Optional[Dict[str, Any]]:
    if not ownership:
        return None
    value = str(ownership).strip().lower()
    coding: Optional[Dict[str, Any]] = None
    if value == "self":
        coding = {
            "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
            "code": "self",
            "display": "Self",
        }
    elif value == "spouse":
        coding = {
            "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
            "code": "spouse",
            "display": "Spouse",
        }

    relationship: Dict[str, Any] = {}
    if coding:
        relationship["coding"] = [coding]
        relationship["text"] = ownership
        return relationship

    # Uncoded fallback (e.g., Guardian)
    relationship["text"] = ownership
    return relationship


def _owner_name_extension(owner_name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not owner_name:
        return None
    return {
        "url": "http://synthea.mitre.org/fhir/StructureDefinition/policy-owner-name",
        "valueString": str(owner_name),
    }


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    patient = src.get("Patient") or src.get("PATIENT")
    start_year = src.get("Start_Year") or src.get("START_YEAR")
    payer = src.get("Payer") or src.get("PAYER")
    if patient and start_year and payer:
        return f"cov-{patient}-{start_year}-{payer}"
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def payer_transition_to_coverage(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform payer_transitions row to FHIR Coverage."""
    patient_id = src.get("Patient") or src.get("PATIENT")
    payer_id = src.get("Payer") or src.get("PAYER")
    secondary_payer_id = src.get("Secondary Payer") or src.get("SECONDARY_PAYER") or src.get("Secondary_Payer")

    extensions: List[Dict[str, Any]] = []
    owner_ext = _owner_name_extension(src.get("Owner Name") or src.get("OWNER_NAME"))
    if owner_ext:
        extensions.append(owner_ext)

    result: Dict[str, Any] = {
        "resourceType": "Coverage",
        "id": _generate_id(src),
        "status": "active",
        "beneficiary": create_reference("Patient", patient_id) if patient_id else None,
        "payor": [
            create_reference("Organization", payer_id)
        ] if payer_id else None,
        "period": _compose_period(src.get("Start_Year") or src.get("START_YEAR"), src.get("End_Year") or src.get("END_YEAR")),
        "subscriberId": src.get("Member ID") or src.get("MEMBER_ID"),
        "relationship": _relationship_code(src.get("Ownership") or src.get("OWNERSHIP")),
        "extension": extensions if extensions else None,
    }

    # Append secondary payor if provided
    if secondary_payer_id:
        payors = result.get("payor") or []
        payors.append(create_reference("Organization", secondary_payer_id))
        result["payor"] = payors

    return filter_none_values(result)


def map_payer_transition(row: Dict[str, Any]) -> Dict[str, Any]:
    """Public API: Synthea payer_transitions row ➜ FHIR Coverage."""
    return payer_transition_to_coverage(row)


