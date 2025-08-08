"""
Procedure mapper: Synthea CSV to FHIR R4 Procedure resource.
"""

from typing import Any, Dict, Optional, List

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


def _build_code(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build CodeableConcept for the procedure code."""
    code = src.get("CODE")
    description = src.get("DESCRIPTION")
    system = src.get("SYSTEM") or "http://snomed.info/sct"

    if not code and not description:
        return None

    coding = {
        "system": system,
        "code": code,
        "display": description,
    }

    result = {"coding": [coding]}
    if description:
        result["text"] = description
    return result


def _build_reason_code(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Build reasonCode CodeableConcept array if ReasonCode/ReasonDescription present."""
    r_code = src.get("REASONCODE")
    r_desc = src.get("REASONDESCRIPTION")

    if not r_code and not r_desc:
        return None

    cc: Dict[str, Any] = {}
    coding = None
    if r_code or r_desc:
        coding = {
            "system": "http://snomed.info/sct",
            "code": r_code,
            "display": r_desc,
        }
    if coding:
        cc["coding"] = [coding]
    if r_desc:
        cc["text"] = r_desc

    return [cc] if cc else None


def _build_extensions(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Add non-core data such as Base_Cost as an extension."""
    extensions: List[Dict[str, Any]] = []

    base_cost = src.get("BASE_COST") or src.get("Base_Cost")
    if base_cost not in (None, ""):
        try:
            value = float(str(base_cost))
            extensions.append({
                "url": "http://example.org/fhir/StructureDefinition/baseCost",
                "valueMoney": {"value": value, "currency": "USD"},
            })
        except (ValueError, TypeError):
            # If not numeric, omit the extension
            pass

    return extensions or None


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    """Generate a deterministic ID for the procedure."""
    patient = src.get("PATIENT")
    start = src.get("START")
    code = src.get("CODE")
    if patient and start and code:
        start_clean = start.replace(" ", "").replace("-", "").replace(":", "")
        return f"proc-{patient}-{start_clean}-{code}"
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None/empty list/empty string values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def procedure_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea procedures.csv row to FHIR Procedure."""
    start_dt = to_fhir_datetime(src.get("START")) if src.get("START") else None
    stop_dt = to_fhir_datetime(src.get("STOP")) if src.get("STOP") else None

    performed: Dict[str, Any] = {}
    if start_dt and stop_dt:
        performed = {"performedPeriod": {"start": start_dt, "end": stop_dt}}
    elif start_dt:
        performed = {"performedDateTime": start_dt}

    extensions = _build_extensions(src)

    result: Dict[str, Any] = {
        "resourceType": "Procedure",
        "id": _generate_id(src),
        "status": "completed",
        "code": _build_code(src),
        "subject": create_reference("Patient", src.get("PATIENT")) if src.get("PATIENT") else None,
        "encounter": create_reference("Encounter", src.get("ENCOUNTER")) if src.get("ENCOUNTER") else None,
        "reasonCode": _build_reason_code(src),
        "extension": extensions,
        **performed,
    }

    return filter_none_values(result)


def map_procedure(synthea_procedure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV procedure row to FHIR Procedure resource.

    Args:
        synthea_procedure: Dictionary with Synthea procedures.csv fields

    Returns:
        FHIR Procedure resource as dictionary
    """
    return procedure_transform(synthea_procedure)


