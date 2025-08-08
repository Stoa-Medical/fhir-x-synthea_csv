"""
Encounter mapper: Synthea encounters.csv to FHIR R4 Encounter resource.
"""

from typing import Any, Dict, Optional, List

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)
from ..common.lexicons import encounter_class_lexicon


def _status_from_period(src: Dict[str, Any]) -> str:
    """Infer Encounter.status from Stop date presence."""
    return "finished" if src.get("Stop") else "in-progress"


def _build_class(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build Encounter.class from EncounterClass string via lexicon."""
    enc_class = src.get("EncounterClass")
    if not enc_class:
        return None
    # MappingDict returns dict with system/code/display
    return encounter_class_lexicon.forward_get(enc_class)


def _build_type(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Build Encounter.type (SNOMED CT)."""
    code = src.get("Code") or src.get("CODE")
    text = src.get("Description") or src.get("DESCRIPTION")
    if not code and not text:
        return None
    type_cc: Dict[str, Any] = {
        "coding": []
    }
    if code:
        type_cc["coding"].append({
            "system": "http://snomed.info/sct",
            "code": code,
            "display": text,
        })
    if text:
        type_cc["text"] = text
    return [type_cc]


def _build_reason_code(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    code = src.get("ReasonCode")
    text = src.get("ReasonDescription")
    if not code and not text:
        return None
    cc: Dict[str, Any] = {"coding": []}
    if code:
        cc["coding"].append({
            "system": "http://snomed.info/sct",
            "code": code,
            "display": text,
        })
    if text:
        cc["text"] = text
    return [cc]


def _build_extensions(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    exts: List[Dict[str, Any]] = []

    def add_decimal_ext(url: str, value: Any) -> None:
        try:
            if value is None or value == "":
                return
            exts.append({"url": url, "valueDecimal": float(str(value))})
        except (ValueError, TypeError):
            # Skip invalid numeric values
            pass

    # Cost extensions
    add_decimal_ext("http://example.org/fhir/StructureDefinition/encounter-baseCost", src.get("Base_Encounter_Cost"))
    add_decimal_ext("http://example.org/fhir/StructureDefinition/encounter-totalClaimCost", src.get("Total_Claim_Cost"))
    add_decimal_ext("http://example.org/fhir/StructureDefinition/encounter-payerCoverage", src.get("Payer_Coverage"))

    # Payer reference extension (Organization)
    payer_id = src.get("Payer")
    if payer_id:
        exts.append({
            "url": "http://example.org/fhir/StructureDefinition/encounter-payer",
            "valueReference": create_reference("Organization", payer_id),
        })

    return exts or None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None/empty values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def encounter_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea encounters.csv row to FHIR Encounter resource."""
    result: Dict[str, Any] = {
        "resourceType": "Encounter",
        "id": src.get("Id"),
        "status": _status_from_period(src),
        "class": _build_class(src),
        "type": _build_type(src),
        "subject": create_reference("Patient", src.get("Patient")) if src.get("Patient") else None,
        "serviceProvider": create_reference("Organization", src.get("Organization")) if src.get("Organization") else None,
        "participant": [
            {
                "individual": create_reference("Practitioner", src.get("Provider"))
            }
        ] if src.get("Provider") else None,
        "period": {
            "start": to_fhir_datetime(src.get("Start")),
            "end": to_fhir_datetime(src.get("Stop")) if src.get("Stop") else None,
        },
        "reasonCode": _build_reason_code(src),
        "extension": _build_extensions(src),
    }

    # Clean nested period dict
    if result.get("period") and result["period"].get("end") is None:
        # Keep start, end omitted if None
        result["period"] = {k: v for k, v in result["period"].items() if v is not None}

    return filter_none_values(result)


def map_encounter(synthea_encounter: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV encounter to FHIR Encounter resource.

    Args:
        synthea_encounter: Dictionary with Synthea encounters CSV fields

    Returns:
        FHIR Encounter resource as dictionary
    """
    return encounter_transform(synthea_encounter)
