"""
Encounter reverse mapper: FHIR R4 Encounter resource to Synthea encounters.csv.
"""

from typing import Any, Dict, Optional, List

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings."""
    return {k: (v if v is not None else "") for k, v in d.items()}


# Minimal reverse map for Encounter.class.code to Synthea string
_ENCOUNTER_CLASS_CODE_TO_SYNTHEA = {
    "AMB": "ambulatory",
    "EMER": "emergency",
    "IMP": "inpatient",
    "ACUTE": "urgentcare",
}


def _extract_encounter_class(enc_class: Optional[Dict[str, Any]]) -> Optional[str]:
    if not enc_class or not isinstance(enc_class, dict):
        return None
    code = enc_class.get("code")
    if code in _ENCOUNTER_CLASS_CODE_TO_SYNTHEA:
        return _ENCOUNTER_CLASS_CODE_TO_SYNTHEA[code]
    # Fallback: try display lowercased
    display = enc_class.get("display")
    return display.lower() if isinstance(display, str) else None


def _extract_type_and_text(types: Optional[List[Dict[str, Any]]]) -> tuple[Optional[str], Optional[str]]:
    if not types or not isinstance(types, list):
        return None, None
    first = types[0]
    code = None
    text = first.get("text") if isinstance(first, dict) else None
    if isinstance(first, dict):
        snomed = extract_coding_by_system(first, "http://snomed.info/sct")
        if snomed:
            code = snomed.get("code")
            if not text:
                text = snomed.get("display")
        else:
            coding_list = first.get("coding")
            if coding_list and isinstance(coding_list, list) and len(coding_list) > 0:
                c0 = coding_list[0]
                if isinstance(c0, dict):
                    code = c0.get("code")
                    text = text or c0.get("display")
    return code, text


def _extract_reason(types: Optional[List[Dict[str, Any]]]) -> tuple[Optional[str], Optional[str]]:
    if not types or not isinstance(types, list):
        return None, None
    first = types[0]
    code = None
    text = first.get("text") if isinstance(first, dict) else None
    if isinstance(first, dict):
        snomed = extract_coding_by_system(first, "http://snomed.info/sct")
        if snomed:
            code = snomed.get("code")
            if not text:
                text = snomed.get("display")
        else:
            coding_list = first.get("coding")
            if coding_list and isinstance(coding_list, list) and len(coding_list) > 0:
                c0 = coding_list[0]
                if isinstance(c0, dict):
                    code = c0.get("code")
                    text = text or c0.get("display")
    return code, text


def _extract_decimal_ext(extensions: Optional[List[Dict[str, Any]]], url: str) -> Optional[str]:
    if not extensions or not isinstance(extensions, list):
        return None
    for ext in extensions:
        if isinstance(ext, dict) and ext.get("url") == url:
            val = ext.get("valueDecimal")
            return str(val) if val is not None else None
    return None


def _extract_payer(extensions: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not extensions or not isinstance(extensions, list):
        return None
    for ext in extensions:
        if isinstance(ext, dict) and ext.get("url") == "http://example.org/fhir/StructureDefinition/encounter-payer":
            ref = ext.get("valueReference")
            return extract_reference_id(ref)
    return None


def fhir_encounter_to_csv_transform(fhir_encounter: Dict[str, Any]) -> Dict[str, Any]:
    """Transform FHIR Encounter to Synthea encounters.csv row."""
    period = fhir_encounter.get("period", {}) or {}
    start = parse_fhir_datetime(period.get("start"))
    stop = parse_fhir_datetime(period.get("end"))

    patient_id = extract_reference_id(fhir_encounter.get("subject"))
    org_id = extract_reference_id(fhir_encounter.get("serviceProvider"))

    provider_id = None
    participants = fhir_encounter.get("participant")
    if isinstance(participants, list) and participants:
        first = participants[0]
        if isinstance(first, dict):
            provider_id = extract_reference_id(first.get("individual"))

    synthea_class = _extract_encounter_class(fhir_encounter.get("class"))

    code, description = _extract_type_and_text(fhir_encounter.get("type"))

    reason_code, reason_text = _extract_reason(fhir_encounter.get("reasonCode"))

    exts = fhir_encounter.get("extension")
    base_cost = _extract_decimal_ext(exts, "http://example.org/fhir/StructureDefinition/encounter-baseCost")
    total_cost = _extract_decimal_ext(exts, "http://example.org/fhir/StructureDefinition/encounter-totalClaimCost")
    payer_cov = _extract_decimal_ext(exts, "http://example.org/fhir/StructureDefinition/encounter-payerCoverage")
    payer_id = _extract_payer(exts)

    result = {
        "Id": fhir_encounter.get("id"),
        "Start": start,
        "Stop": stop,
        "Patient": patient_id,
        "Organization": org_id,
        "Provider": provider_id,
        "Payer": payer_id,
        "EncounterClass": synthea_class,
        "Code": code,
        "Description": description,
        "Base_Encounter_Cost": base_cost,
        "Total_Claim_Cost": total_cost,
        "Payer_Coverage": payer_cov,
        "ReasonCode": reason_code,
        "ReasonDescription": reason_text,
    }

    return filter_none_values(result)



def map_fhir_encounter_to_csv(fhir_encounter: Dict[str, Any]) -> Dict[str, Any]:
    """Convert FHIR Encounter to Synthea encounters.csv dict."""
    if not fhir_encounter or fhir_encounter.get("resourceType") != "Encounter":
        raise ValueError("Input must be a FHIR Encounter resource")
    return fhir_encounter_to_csv_transform(fhir_encounter)
