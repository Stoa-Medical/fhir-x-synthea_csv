"""
Allergy reverse mapper: FHIR R4 AllergyIntolerance → Synthea allergies.csv row.
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def _extract_start(fhir_allergy: Dict[str, Any]) -> Optional[str]:
    # Prefer recordedDate, fallback onsetDateTime
    start = parse_fhir_datetime(fhir_allergy.get("recordedDate"))
    if not start:
        start = parse_fhir_datetime(fhir_allergy.get("onsetDateTime"))
    return start


def _extract_stop(fhir_allergy: Dict[str, Any]) -> Optional[str]:
    # Use lastOccurrence if present
    stop = parse_fhir_datetime(fhir_allergy.get("lastOccurrence"))
    return stop


def _extract_code_system_display(code_concept: Optional[Dict[str, Any]]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    code = None
    system = None
    display = None
    if not code_concept or not isinstance(code_concept, dict):
        return code, system, display

    # Prefer SNOMED then RxNorm, else first coding
    snomed = extract_coding_by_system(code_concept, "http://snomed.info/sct")
    rxnorm = extract_coding_by_system(code_concept, "http://www.nlm.nih.gov/research/umls/rxnorm")
    chosen = snomed or rxnorm
    if not chosen:
        coding_list = code_concept.get("coding", [])
        if coding_list and isinstance(coding_list, list):
            chosen = coding_list[0]

    if isinstance(chosen, dict):
        code = chosen.get("code")
        system = chosen.get("system")
        display = chosen.get("display")
    if not display:
        display = code_concept.get("text")
    return code, system, display


def _normalize_category_for_csv(categories: Optional[list]) -> Optional[str]:
    if not categories or not isinstance(categories, list) or len(categories) == 0:
        return None
    cat = categories[0]
    if not isinstance(cat, Dict):
        return None
    # Category in FHIR R4 is array of codes: medication|food|environment|biologic
    # We'll pass through common values; Synthea examples include drug/medication/food/environment
    val = None
    if isinstance(cat, str):
        val = cat
    elif isinstance(cat, dict):
        # Some systems represent as {coding: ...}, but spec is code array; handle both
        val = cat.get("text") or cat.get("code")
    if not val:
        return None
    v = str(val).strip().lower()
    if v in ["medication", "drug"]:
        return "medication"
    if v in ["food"]:
        return "food"
    if v in ["environment"]:
        return "environment"
    return v


def _extract_reaction_fields(fhir_allergy: Dict[str, Any], index: int) -> tuple[Optional[str], Optional[str], Optional[str]]:
    reactions = fhir_allergy.get("reaction", [])
    if not isinstance(reactions, list) or index >= len(reactions):
        return None, None, None
    rx = reactions[index]
    code = None
    desc = None
    sev = None
    if isinstance(rx, dict):
        # manifestation is a list of CodeableConcepts
        man_list = rx.get("manifestation", [])
        if isinstance(man_list, list) and len(man_list) > 0:
            man = man_list[0]
            if isinstance(man, dict):
                snomed = extract_coding_by_system(man, "http://snomed.info/sct")
                if snomed:
                    code = snomed.get("code")
                else:
                    coding_list = man.get("coding", [])
                    if coding_list and isinstance(coding_list, list) and len(coding_list) > 0:
                        code = coding_list[0].get("code")
        desc = rx.get("description")
        sev_val = rx.get("severity")
        if sev_val:
            sev = str(sev_val).upper()
    return code, desc, sev


def fhir_allergy_to_csv_transform(fhir_allergy: Dict[str, Any]) -> Dict[str, Any]:
    # Dates
    start = _extract_start(fhir_allergy)
    stop = _extract_stop(fhir_allergy)

    # References
    patient_id = extract_reference_id(fhir_allergy.get("patient"))
    encounter_id = extract_reference_id(fhir_allergy.get("encounter"))

    # Code
    code, system, display = _extract_code_system_display(fhir_allergy.get("code"))

    # Category and type
    category = _normalize_category_for_csv(fhir_allergy.get("category"))
    typ = fhir_allergy.get("type")
    typ = str(typ).lower() if typ else None

    # Reactions
    rx1_code, rx1_desc, rx1_sev = _extract_reaction_fields(fhir_allergy, 0)
    rx2_code, rx2_desc, rx2_sev = _extract_reaction_fields(fhir_allergy, 1)

    result = {
        "START": start,
        "STOP": stop if stop is not None else "",
        "PATIENT": patient_id,
        "ENCOUNTER": encounter_id,
        "SYSTEM": system,
        "CODE": code,
        "DESCRIPTION": display,
        "TYPE": typ,
        "CATEGORY": category,
        "REACTION1": rx1_code,
        "DESCRIPTION1": rx1_desc,
        "SEVERITY1": rx1_sev,
        "REACTION2": rx2_code,
        "DESCRIPTION2": rx2_desc,
        "SEVERITY2": rx2_sev,
    }
    return filter_none_values(result)


def map_fhir_allergy_to_csv(fhir_allergy: Dict[str, Any]) -> Dict[str, Any]:
    if not fhir_allergy or fhir_allergy.get("resourceType") != "AllergyIntolerance":
        raise ValueError("Input must be a FHIR AllergyIntolerance resource")
    return fhir_allergy_to_csv_transform(fhir_allergy)


