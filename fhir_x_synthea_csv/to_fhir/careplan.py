"""
CarePlan mapper: Synthea careplans.csv to FHIR R4 CarePlan resource.
"""

from typing import Any, Dict, Optional

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
    create_identifier,
)

SNOMED_SYSTEM = "http://snomed.info/sct"


def _get(src: Dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        if key in src and src.get(key) not in (None, ""):
            return src.get(key)
    return None


def _derive_status(stop: Optional[str]) -> str:
    return "active" if not stop else "completed"


def _build_period(start: Optional[str], stop: Optional[str]) -> Optional[Dict[str, Any]]:
    start_dt = to_fhir_datetime(start) if start else None
    end_dt = to_fhir_datetime(stop) if stop else None
    if not start_dt and not end_dt:
        return None
    period: Dict[str, Any] = {}
    if start_dt:
        period["start"] = start_dt
    if end_dt:
        period["end"] = end_dt
    return period


def _build_category(code: Optional[str]) -> Optional[list]:
    if not code:
        return None
    return [
        {
            "coding": [
                {
                    "system": SNOMED_SYSTEM,
                    "code": code,
                }
            ]
        }
    ]


def _build_reason_code(code: Optional[str], display: Optional[str]) -> Optional[list]:
    if not code and not display:
        return None
    coding = {"system": SNOMED_SYSTEM}
    if code:
        coding["code"] = code
    if display:
        coding["display"] = display
    return [{"coding": [coding], "text": display}]


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    provided_id = _get(src, "Id", "ID")
    if provided_id:
        return provided_id
    # Fallback generation using patient-start-code
    patient = _get(src, "Patient", "PATIENT")
    start = _get(src, "Start", "START")
    code = _get(src, "Code", "CODE")
    if patient and start:
        start_clean = str(start).replace(" ", "").replace(":", "").replace("-", "")
        code_part = code or "nocode"
        return f"careplan-{patient}-{start_clean}-{code_part}"
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def careplan_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    start = _get(src, "Start", "START")
    stop = _get(src, "Stop", "STOP")
    patient_id = _get(src, "Patient", "PATIENT")
    encounter_id = _get(src, "Encounter", "ENCOUNTER")
    code = _get(src, "Code", "CODE")
    description = _get(src, "Description", "DESCRIPTION")
    reason_code = _get(src, "ReasonCode")
    reason_desc = _get(src, "ReasonDescription")

    result: Dict[str, Any] = {
        "resourceType": "CarePlan",
        "id": _generate_id(src),
        "status": _derive_status(stop),
        "intent": "plan",
        "subject": create_reference("Patient", patient_id) if patient_id else None,
        "encounter": create_reference("Encounter", encounter_id) if encounter_id else None,
        "period": _build_period(start, stop),
        "category": _build_category(code),
        "title": description,
        "description": description,
        "reasonCode": _build_reason_code(reason_code, reason_desc),
    }

    return filter_none_values(result)


def map_careplan(synthea_careplan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea careplans.csv row to FHIR CarePlan resource.
    """
    return careplan_transform(synthea_careplan)
