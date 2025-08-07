"""
CarePlan reverse mapper: FHIR R4 CarePlan resource to Synthea CSV careplans.
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    parse_fhir_date,
    extract_reference_id,
    extract_coding_by_system,
    safe_get_first,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values but keep empty strings for CSV stability."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def _extract_category_code_and_display(fhir_careplan: Dict[str, Any]) -> tuple[Optional[str], Optional[str], str]:
    """Extract SNOMED code and display from CarePlan.category."""
    system_default = "http://snomed.info/sct"
    category_list = fhir_careplan.get("category") or []
    category = safe_get_first(category_list)
    if isinstance(category, dict):
        snomed = extract_coding_by_system(category, system_default)
        if snomed:
            return snomed.get("code"), snomed.get("display"), system_default
        coding_list = category.get("coding", [])
        if coding_list:
            first = safe_get_first(coding_list)
            if isinstance(first, dict):
                return first.get("code"), first.get("display"), first.get("system", system_default)
        # Fallback to text
        if category.get("text"):
            return None, category.get("text"), system_default
    return None, None, system_default


def _extract_reason_from_notes(fhir_careplan: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """Attempt to parse reasonCode/Description from CarePlan.note text (if previously encoded)."""
    notes = fhir_careplan.get("note") or []
    if not isinstance(notes, list):
        return None, None
    for note in notes:
        if isinstance(note, dict) and note.get("text"):
            text = str(note.get("text"))
            # Expected pattern: "Reason: <desc> (<code>)" but be tolerant
            if text.lower().startswith("reason:"):
                body = text.split(":", 1)[1].strip()
                # Try to split code in parentheses
                if body.endswith(")") and "(" in body:
                    desc, code_part = body.rsplit("(", 1)
                    return code_part[:-1].strip() or None, desc.strip() or None
                return None, body or None
    return None, None


def fhir_careplan_to_csv_transform(fhir_careplan: Dict[str, Any]) -> Dict[str, Any]:
    """Transform FHIR CarePlan to Synthea CSV careplan format."""
    if not fhir_careplan or fhir_careplan.get("resourceType") != "CarePlan":
        raise ValueError("Input must be a FHIR CarePlan resource")

    careplan_id = fhir_careplan.get("id")

    period = fhir_careplan.get("period", {}) if isinstance(fhir_careplan.get("period"), dict) else {}
    start_date = parse_fhir_date(period.get("start"))
    stop_date = parse_fhir_date(period.get("end"))

    subject_id = extract_reference_id(fhir_careplan.get("subject"))
    encounter_id = extract_reference_id(fhir_careplan.get("encounter"))

    code, display, system = _extract_category_code_and_display(fhir_careplan)

    # Try to pull reason out of R5-style fields if present, else from notes
    reason_code, reason_desc = _extract_reason_from_notes(fhir_careplan)

    result = {
        "Id": careplan_id,
        "START": start_date,
        "STOP": stop_date,
        "PATIENT": subject_id,
        "ENCOUNTER": encounter_id,
        "SYSTEM": system,
        "CODE": code,
        "DESCRIPTION": display or fhir_careplan.get("title") or fhir_careplan.get("description"),
        "REASONCODE": reason_code,
        "REASONDESCRIPTION": reason_desc,
    }

    return filter_none_values(result)


def map_fhir_careplan_to_csv(fhir_careplan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR CarePlan resource to Synthea CSV careplan format.

    Args:
        fhir_careplan: FHIR CarePlan resource as dictionary

    Returns:
        Synthea CSV careplan as dictionary
    """
    return fhir_careplan_to_csv_transform(fhir_careplan)