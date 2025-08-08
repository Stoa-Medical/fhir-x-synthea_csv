"""
Medication reverse mapper: FHIR R4 MedicationRequest → Synthea medications.csv.
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
    extract_extension_by_url,
)

RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SNOMED_SYSTEM = "http://snomed.info/sct"

EXT_BASE_COST = "http://synthea.org/fhir/StructureDefinition/medication-baseCost"
EXT_PAYER_COVERAGE = "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage"
EXT_TOTAL_COST = "http://synthea.org/fhir/StructureDefinition/medication-totalCost"


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: (v if v is not None else "") for k, v in d.items()}


def _extract_occurrence_start(mr: Dict[str, Any]) -> Optional[str]:
    authored_on = mr.get("authoredOn")
    if authored_on:
        return parse_fhir_datetime(authored_on)
    occ = mr.get("occurrencePeriod")
    if isinstance(occ, dict) and occ.get("start"):
        return parse_fhir_datetime(occ.get("start"))
    return None


def _extract_occurrence_end(mr: Dict[str, Any]) -> Optional[str]:
    occ = mr.get("occurrencePeriod")
    if isinstance(occ, dict) and occ.get("end"):
        return parse_fhir_datetime(occ.get("end"))
    return None


def _extract_med_code_and_text(mr: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    concept = mr.get("medicationCodeableConcept")
    code, text = None, None
    if isinstance(concept, dict):
        coding = extract_coding_by_system(concept, RXNORM_SYSTEM)
        if coding:
            code = coding.get("code")
            text = coding.get("display")
        if not text:
            text = concept.get("text")
        if (not code or not text) and isinstance(concept.get("coding"), list) and concept["coding"]:
            first = concept["coding"][0]
            code = code or first.get("code")
            text = text or first.get("display")
    return code, text


def _extract_reason(mr: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    reasons = mr.get("reasonCode") or []
    if isinstance(reasons, list) and reasons:
        rc = reasons[0]
        if isinstance(rc, dict):
            coding = extract_coding_by_system(rc, SNOMED_SYSTEM) or None
            code = None
            display = None
            if coding:
                code = coding.get("code")
                display = coding.get("display")
            if not display:
                display = rc.get("text")
            if (not code or not display) and isinstance(rc.get("coding"), list) and rc["coding"]:
                first = rc["coding"][0]
                code = code or first.get("code")
                display = display or first.get("display")
            return code, display
    return None, None


def _extract_extension_decimal(mr: Dict[str, Any], url: str) -> Optional[str]:
    ext = extract_extension_by_url(mr.get("extension"), url)
    if isinstance(ext, dict):
        val = ext.get("valueDecimal")
        if val is not None:
            return str(val)
    return None


def fhir_medication_request_to_csv_transform(fhir_mr: Dict[str, Any]) -> Dict[str, Any]:
    start = _extract_occurrence_start(fhir_mr)
    stop = _extract_occurrence_end(fhir_mr)

    patient_id = extract_reference_id(fhir_mr.get("subject"))
    encounter_id = extract_reference_id(fhir_mr.get("encounter"))

    payer_id = None
    insurance = fhir_mr.get("insurance") or []
    if isinstance(insurance, list) and insurance:
        payer_id = extract_reference_id(insurance[0])

    code, description = _extract_med_code_and_text(fhir_mr)

    reason_code, reason_text = _extract_reason(fhir_mr)

    dispenses = None
    disp = fhir_mr.get("dispenseRequest")
    if isinstance(disp, dict):
        repeats = disp.get("numberOfRepeatsAllowed")
        if repeats is not None:
            try:
                dispenses = str(int(repeats))
            except (ValueError, TypeError):
                dispenses = None

    base_cost = _extract_extension_decimal(fhir_mr, EXT_BASE_COST)
    payer_cov = _extract_extension_decimal(fhir_mr, EXT_PAYER_COVERAGE)
    total_cost = _extract_extension_decimal(fhir_mr, EXT_TOTAL_COST)

    result = {
        "START": start,
        "STOP": stop,
        "PATIENT": patient_id,
        "PAYER": payer_id,
        "ENCOUNTER": encounter_id,
        "CODE": code,
        "DESCRIPTION": description,
        "Base_Cost": base_cost,
        "Payer_Coverage": payer_cov,
        "Dispenses": dispenses,
        "TotalCost": total_cost,
        "ReasonCode": reason_code,
        "ReasonDescription": reason_text,
    }

    return filter_none_values(result)


def map_fhir_medication_request_to_csv(fhir_medication_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR MedicationRequest to Synthea medications.csv row.
    """
    if not fhir_medication_request or fhir_medication_request.get("resourceType") != "MedicationRequest":
        raise ValueError("Input must be a FHIR MedicationRequest resource")
    return fhir_medication_request_to_csv_transform(fhir_medication_request)


