"""
CarePlan mapper: Synthea CSV to FHIR R4 CarePlan resource.
"""

from typing import Any, Dict, Optional

from ..common.transformers import (
    create_reference,
    to_fhir_date,
)


def _get(src: Dict[str, Any], *keys: str) -> Optional[Any]:
    """Get first non-empty value from possible key variants."""
    for key in keys:
        if key in src and src.get(key) not in (None, ""):
            return src.get(key)
    return None


def _build_status(src: Dict[str, Any]) -> str:
    """
    Determine CarePlan.status from presence of STOP date.
    active if no STOP date, completed if STOP present.
    """
    stop_date = _get(src, "STOP", "Stop")
    return "completed" if stop_date else "active"


def _build_category(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build CarePlan.category[0] from SNOMED code and description."""
    code = _get(src, "CODE", "Code")
    display = _get(src, "DESCRIPTION", "Description")
    if not code:
        return None
    return {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": code,
                "display": display,
            }
        ],
        "text": display,
    }


def _build_period(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build CarePlan.period from Start/Stop dates."""
    start = _get(src, "START", "Start")
    stop = _get(src, "STOP", "Stop")
    if not start and not stop:
        return None
    return {
        "start": to_fhir_date(start) if start else None,
        "end": to_fhir_date(stop) if stop else None,
    }


def _build_reason_note(src: Dict[str, Any]) -> Optional[list]:
    """Optionally include reason as a note since R4 lacks top-level reasonCode."""
    reason_code = _get(src, "REASONCODE", "ReasonCode")
    reason_desc = _get(src, "REASONDESCRIPTION", "ReasonDescription")
    if not reason_code and not reason_desc:
        return None
    text_parts = []
    if reason_desc:
        text_parts.append(str(reason_desc))
    if reason_code:
        text_parts.append(f"({reason_code})")
    return [{"text": "Reason: " + " ".join(text_parts)}]


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None/empty list/empty string values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def careplan_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea careplan to FHIR CarePlan."""
    category = _build_category(src)
    period = _build_period(src)
    result: Dict[str, Any] = {
        "resourceType": "CarePlan",
        "id": _get(src, "Id", "ID"),
        "status": _build_status(src),
        "intent": "plan",
        "category": [category] if category else None,
        "title": _get(src, "DESCRIPTION", "Description"),
        "description": _get(src, "DESCRIPTION", "Description"),
        "subject": create_reference("Patient", _get(src, "PATIENT", "Patient")) if _get(src, "PATIENT", "Patient") else None,
        "encounter": create_reference("Encounter", _get(src, "ENCOUNTER", "Encounter")) if _get(src, "ENCOUNTER", "Encounter") else None,
        "period": period,
        "note": _build_reason_note(src),
    }
    return filter_none_values(result)


def map_careplan(synthea_careplan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV careplan to FHIR CarePlan resource.

    Args:
        synthea_careplan: Dictionary with Synthea careplan CSV fields

    Returns:
        FHIR CarePlan resource as dictionary
    """
    return careplan_transform(synthea_careplan)