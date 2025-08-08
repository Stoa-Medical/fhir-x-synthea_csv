"""
Procedure reverse mapper: FHIR R4 Procedure resource to Synthea CSV procedures row.
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
    extract_extension_by_url,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def _extract_performed(fhir_procedure: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """Extract START and STOP from Procedure.performed[x]."""
    start, stop = None, None

    # performedDateTime
    if "performedDateTime" in fhir_procedure:
        start = parse_fhir_datetime(fhir_procedure.get("performedDateTime"))

    # performedPeriod
    elif "performedPeriod" in fhir_procedure and isinstance(fhir_procedure["performedPeriod"], dict):
        pp = fhir_procedure["performedPeriod"]
        start = parse_fhir_datetime(pp.get("start"))
        stop = parse_fhir_datetime(pp.get("end"))

    return start, stop


def _extract_code_system_code_desc(fhir_procedure: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract SYSTEM, CODE, DESCRIPTION from Procedure.code."""
    code_cc = fhir_procedure.get("code")
    system = "http://snomed.info/sct"
    code = None
    desc = None

    if code_cc and isinstance(code_cc, dict):
        # Prefer SNOMED coding
        snomed = extract_coding_by_system(code_cc, "http://snomed.info/sct")
        chosen = snomed
        if not chosen:
            # Fall back to first coding if present
            codings = code_cc.get("coding", [])
            if isinstance(codings, list) and codings:
                chosen = codings[0]

        if chosen:
            system = chosen.get("system", system)
            code = chosen.get("code")
            desc = chosen.get("display")

        # Fallback to text for description
        if not desc:
            desc = code_cc.get("text")

    return system, code, desc


def _extract_reason(fhir_procedure: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """Extract REASONCODE and REASONDESCRIPTION from Procedure.reasonCode."""
    reason_list = fhir_procedure.get("reasonCode")
    if not reason_list or not isinstance(reason_list, list):
        return None, None

    reason = reason_list[0] if reason_list else None
    if not isinstance(reason, dict):
        return None, None

    # Prefer SNOMED in reason
    snomed = extract_coding_by_system(reason, "http://snomed.info/sct")
    chosen = snomed
    if not chosen:
        codings = reason.get("coding", [])
        if isinstance(codings, list) and codings:
            chosen = codings[0]

    r_code = chosen.get("code") if chosen else None
    r_desc = chosen.get("display") if chosen else None

    if not r_desc:
        r_desc = reason.get("text")

    return r_code, r_desc


def _extract_base_cost(fhir_procedure: Dict[str, Any]) -> Optional[str]:
    """Extract BASE_COST from custom extension valueMoney.value."""
    extensions = fhir_procedure.get("extension")
    ext = extract_extension_by_url(extensions, "http://example.org/fhir/StructureDefinition/baseCost")
    if ext and isinstance(ext, dict):
        v = ext.get("valueMoney")
        if isinstance(v, dict):
            value = v.get("value")
            if value is not None:
                # Preserve numeric formatting; convert to string
                return str(int(value)) if isinstance(value, (int, float)) and value == int(value) else str(value)
    return None


def fhir_procedure_to_csv_transform(fhir_procedure: Dict[str, Any]) -> Dict[str, Any]:
    """Transform FHIR Procedure to Synthea procedures.csv dict."""
    start, stop = _extract_performed(fhir_procedure)

    patient_id = extract_reference_id(fhir_procedure.get("subject"))
    encounter_id = extract_reference_id(fhir_procedure.get("encounter"))

    system, code, desc = _extract_code_system_code_desc(fhir_procedure)
    reason_code, reason_desc = _extract_reason(fhir_procedure)
    base_cost = _extract_base_cost(fhir_procedure)

    result = {
        "START": start,
        "STOP": stop,
        "PATIENT": patient_id,
        "ENCOUNTER": encounter_id,
        "SYSTEM": system,
        "CODE": code,
        "DESCRIPTION": desc,
        "BASE_COST": base_cost,
        "REASONCODE": reason_code,
        "REASONDESCRIPTION": reason_desc,
    }
    return filter_none_values(result)


def map_fhir_procedure_to_csv(fhir_procedure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR Procedure resource to Synthea CSV procedures row.

    Args:
        fhir_procedure: FHIR Procedure resource as dictionary

    Returns:
        Synthea CSV procedures row as dictionary
    """
    if not fhir_procedure or fhir_procedure.get("resourceType") != "Procedure":
        raise ValueError("Input must be a FHIR Procedure resource")
    return fhir_procedure_to_csv_transform(fhir_procedure)


