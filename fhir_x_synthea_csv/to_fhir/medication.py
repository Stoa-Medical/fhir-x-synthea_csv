"""
Medication mapper: Synthea medications.csv → FHIR R4 MedicationRequest.
"""

from typing import Any, Dict, Optional

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)

RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SNOMED_SYSTEM = "http://snomed.info/sct"

EXT_BASE_COST = "http://synthea.org/fhir/StructureDefinition/medication-baseCost"
EXT_PAYER_COVERAGE = "http://synthea.org/fhir/StructureDefinition/medication-payerCoverage"
EXT_TOTAL_COST = "http://synthea.org/fhir/StructureDefinition/medication-totalCost"


def _to_decimal(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return None


def _build_medication_code(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    code = src.get("Code") or src.get("CODE")
    display = src.get("Description") or src.get("DESCRIPTION")
    if not code:
        return None
    return {
        "coding": [
            {
                "system": RXNORM_SYSTEM,
                "code": code,
                "display": display,
            }
        ],
        "text": display,
    }


def _build_reason_code(src: Dict[str, Any]) -> Optional[list]:
    r_code = src.get("ReasonCode")
    r_desc = src.get("ReasonDescription")
    if not r_code and not r_desc:
        return None
    coding = {
        "system": SNOMED_SYSTEM,
        "code": r_code,
        "display": r_desc,
    }
    coding = {k: v for k, v in coding.items() if v}
    return [{"coding": [coding], "text": r_desc}] if coding else None


def _build_insurance(src: Dict[str, Any]) -> Optional[list]:
    payer_id = src.get("Payer") or src.get("PAYER")
    if not payer_id:
        return None
    return [create_reference("Coverage", payer_id)]


def _build_cost_extensions(src: Dict[str, Any]) -> list:
    exts = []
    base_cost = _to_decimal(src.get("Base_Cost"))
    if base_cost is not None:
        exts.append({"url": EXT_BASE_COST, "valueDecimal": base_cost})
    payer_cov = _to_decimal(src.get("Payer_Coverage"))
    if payer_cov is not None:
        exts.append({"url": EXT_PAYER_COVERAGE, "valueDecimal": payer_cov})
    total_cost = _to_decimal(src.get("TotalCost"))
    if total_cost is not None:
        exts.append({"url": EXT_TOTAL_COST, "valueDecimal": total_cost})
    return exts


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    patient = src.get("Patient") or src.get("PATIENT")
    start = src.get("Start") or src.get("START")
    code = src.get("Code") or src.get("CODE")
    if patient and start and code:
        start_clean = str(start).replace(" ", "").replace(":", "").replace("-", "")
        return f"medreq-{patient}-{start_clean}-{code}"
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def medication_request_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    start = src.get("Start") or src.get("START")
    stop = src.get("Stop") or src.get("STOP")

    patient_id = src.get("Patient") or src.get("PATIENT")
    encounter_id = src.get("Encounter") or src.get("ENCOUNTER")

    status = "completed" if stop else "active"

    repeats_allowed = src.get("Dispenses")
    try:
        repeats_allowed = int(str(repeats_allowed)) if repeats_allowed not in (None, "") else None
    except (ValueError, TypeError):
        repeats_allowed = None

    extensions = _build_cost_extensions(src)

    result: Dict[str, Any] = {
        "resourceType": "MedicationRequest",
        "id": _generate_id(src),
        "status": status,
        "intent": "order",
        "subject": create_reference("Patient", patient_id) if patient_id else None,
        "encounter": create_reference("Encounter", encounter_id) if encounter_id else None,
        "authoredOn": to_fhir_datetime(start),
        "occurrencePeriod": {
            "start": to_fhir_datetime(start),
            "end": to_fhir_datetime(stop) if stop else None,
        },
        "medicationCodeableConcept": _build_medication_code(src),
        "reasonCode": _build_reason_code(src),
        "dispenseRequest": {
            "numberOfRepeatsAllowed": repeats_allowed,
        } if repeats_allowed is not None else None,
        "insurance": _build_insurance(src),
        "extension": extensions if extensions else None,
    }

    if isinstance(result.get("occurrencePeriod"), dict):
        period = {k: v for k, v in result["occurrencePeriod"].items() if v}
        result["occurrencePeriod"] = period or None

    return filter_none_values(result)


def map_medication(synthea_medication: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea medications.csv row to FHIR MedicationRequest.
    """
    return medication_request_transform(synthea_medication)


