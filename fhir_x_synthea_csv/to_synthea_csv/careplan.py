"""
CarePlan reverse mapper: FHIR R4 CarePlan resource to Synthea CSV careplans.csv.
"""

from typing import Any, Dict, Optional, List

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
)

SNOMED_SYSTEM = "http://snomed.info/sct"


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def _first_category(categories: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    if categories and isinstance(categories, list) and len(categories) > 0:
        first = categories[0]
        if isinstance(first, Dict):
            return first
    return None


def fhir_careplan_to_csv_transform(fhir_cp: Dict[str, Any]) -> Dict[str, Any]:
    cp_id = fhir_cp.get("id")

    period = fhir_cp.get("period") or {}
    start = parse_fhir_datetime(period.get("start")) if isinstance(period, dict) else None
    stop = parse_fhir_datetime(period.get("end")) if isinstance(period, dict) else None

    subject_ref = fhir_cp.get("subject")
    patient_id = extract_reference_id(subject_ref)

    encounter_ref = fhir_cp.get("encounter")
    encounter_id = extract_reference_id(encounter_ref)

    category_cc = _first_category(fhir_cp.get("category"))
    code = None
    if category_cc:
        snomed_coding = extract_coding_by_system(category_cc, SNOMED_SYSTEM)
        if snomed_coding:
            code = snomed_coding.get("code")
        else:
            # Fallback to first coding
            coding_list = category_cc.get("coding", [])
            if coding_list and isinstance(coding_list, list) and len(coding_list) > 0:
                code = coding_list[0].get("code")

    description = fhir_cp.get("description") or fhir_cp.get("title")

    reason_code_list = fhir_cp.get("reasonCode") or []
    r_code = None
    r_desc = None
    if reason_code_list and isinstance(reason_code_list, list):
        first_rc = reason_code_list[0]
        if isinstance(first_rc, dict):
            snomed = extract_coding_by_system(first_rc, SNOMED_SYSTEM)
            if snomed:
                r_code = snomed.get("code")
                r_desc = snomed.get("display")
            else:
                coding_list = first_rc.get("coding", [])
                if coding_list and isinstance(coding_list, list) and len(coding_list) > 0:
                    r_code = coding_list[0].get("code")
                    r_desc = coding_list[0].get("display") or first_rc.get("text")
            if not r_desc:
                r_desc = first_rc.get("text")

    result = {
        "Id": cp_id,
        "Start": start,
        "Stop": stop,
        "Patient": patient_id,
        "Encounter": encounter_id,
        "Code": code,
        "Description": description,
        "ReasonCode": r_code,
        "ReasonDescription": r_desc,
    }

    return filter_none_values(result)


def map_fhir_careplan_to_csv(fhir_careplan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR CarePlan resource to Synthea CSV careplans.csv format.
    """
    if not fhir_careplan or fhir_careplan.get("resourceType") != "CarePlan":
        raise ValueError("Input must be a FHIR CarePlan resource")
    return fhir_careplan_to_csv_transform(fhir_careplan)
