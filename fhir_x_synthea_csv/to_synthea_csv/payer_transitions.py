"""
Reverse mapper: FHIR R4 Coverage ➜ Synthea payer_transitions.csv
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    extract_reference_id,
)


def _year_from_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    s = str(date_str)
    # Expect formats like YYYY-MM-DD or YYYY
    if len(s) >= 4 and s[0:4].isdigit():
        return s[0:4]
    return None


def _ownership_from_relationship(relationship: Optional[Dict[str, Any]]) -> Optional[str]:
    if not relationship or not isinstance(relationship, dict):
        return None
    # Prefer coded mapping
    coding_list = relationship.get("coding")
    if isinstance(coding_list, list) and len(coding_list) > 0:
        coding = coding_list[0]
        if isinstance(coding, dict):
            code = (coding.get("code") or "").lower()
            if code == "self":
                return "Self"
            if code == "spouse":
                return "Spouse"
    # Fallback to text
    text = relationship.get("text")
    if isinstance(text, str) and text.strip().lower() == "guardian":
        return "Guardian"
    return None


def _extract_owner_name_extension(extensions: Optional[list]) -> Optional[str]:
    if not extensions or not isinstance(extensions, list):
        return None
    for ext in extensions:
        if isinstance(ext, dict) and ext.get("url") == "http://synthea.mitre.org/fhir/StructureDefinition/policy-owner-name":
            val = ext.get("valueString")
            return str(val) if val is not None else None
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: (v if v is not None else "") for k, v in d.items()}


def coverage_to_payer_transition(fhir_coverage: Dict[str, Any]) -> Dict[str, Any]:
    """Transform FHIR Coverage to payer_transitions.csv row."""
    # Patient
    beneficiary_ref = fhir_coverage.get("beneficiary")
    patient_id = extract_reference_id(beneficiary_ref)

    # Payers
    payors = fhir_coverage.get("payor") or []
    payer_id = extract_reference_id(payors[0]) if len(payors) >= 1 else None
    secondary_payer_id = extract_reference_id(payors[1]) if len(payors) >= 2 else None

    # Period years
    period = fhir_coverage.get("period") or {}
    start_year = _year_from_date(period.get("start"))
    end_year = _year_from_date(period.get("end"))

    # Member ID
    member_id = fhir_coverage.get("subscriberId")
    if not member_id:
        identifiers = fhir_coverage.get("identifier")
        if isinstance(identifiers, list) and len(identifiers) > 0:
            first_identifier = identifiers[0]
            if isinstance(first_identifier, dict):
                member_id = first_identifier.get("value")

    # Ownership
    ownership = _ownership_from_relationship(fhir_coverage.get("relationship"))

    # Owner name extension
    owner_name = _extract_owner_name_extension(fhir_coverage.get("extension"))

    result = {
        "Patient": patient_id,
        "Member ID": member_id,
        "Start_Year": start_year,
        "End_Year": end_year,
        "Payer": payer_id,
        "Secondary Payer": secondary_payer_id,
        "Ownership": ownership,
        "Owner Name": owner_name,
    }

    return filter_none_values(result)


def map_fhir_coverage_to_payer_transition(fhir_coverage: Dict[str, Any]) -> Dict[str, Any]:
    if not fhir_coverage or fhir_coverage.get("resourceType") != "Coverage":
        raise ValueError("Input must be a FHIR Coverage resource")
    return coverage_to_payer_transition(fhir_coverage)


