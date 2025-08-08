"""
Allergy mapper: Synthea CSV to FHIR R4 AllergyIntolerance resource.
"""

from typing import Any, Dict, List, Optional

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


def _normalize_category(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = str(value).strip().lower()
    if v in ["drug", "medication"]:
        return "medication"
    if v == "food":
        return "food"
    if v == "environment":
        return "environment"
    return None


def _build_clinical_status(src: Dict[str, Any]) -> Dict[str, Any]:
    stop_date = src.get("STOP")
    if stop_date:
        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                    "code": "resolved",
                    "display": "Resolved",
                }
            ]
        }
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                "code": "active",
                "display": "Active",
            }
        ]
    }


def _build_verification_status() -> Dict[str, Any]:
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                "code": "confirmed",
                "display": "Confirmed",
            }
        ]
    }


def _build_code(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    code = src.get("CODE")
    system = src.get("SYSTEM")
    display = src.get("DESCRIPTION")
    if not code:
        return None
    coding: Dict[str, Any] = {
        "code": code,
    }
    if system:
        coding["system"] = system
    if display:
        coding["display"] = display
    result: Dict[str, Any] = {"coding": [coding]}
    if display:
        result["text"] = display
    return result


def _build_reactions(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    reactions: List[Dict[str, Any]] = []
    for idx in ("1", "2"):
        rx_code = src.get(f"REACTION{idx}")
        rx_desc = src.get(f"DESCRIPTION{idx}")
        rx_sev = src.get(f"SEVERITY{idx}")

        if not (rx_code or rx_desc or rx_sev):
            continue

        reaction: Dict[str, Any] = {}

        # manifestation as CodeableConcept (R4)
        if rx_code:
            reaction["manifestation"] = [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": rx_code,
                        }
                    ]
                }
            ]

        if rx_desc:
            reaction["description"] = rx_desc

        if rx_sev:
            reaction["severity"] = str(rx_sev).strip().lower()

        reactions.append(reaction)

    return reactions or None


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    patient = src.get("PATIENT")
    start_date = src.get("START")
    code = src.get("CODE")
    if patient and start_date and code:
        date_clean = start_date.replace(" ", "").replace(":", "").replace("-", "")
        return f"alg-{patient}-{date_clean}-{code}"
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def allergy_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea allergies.csv row to FHIR AllergyIntolerance."""
    category_value = _normalize_category(src.get("CATEGORY")) if src.get("CATEGORY") else None
    reactions = _build_reactions(src)
    result = {
        "resourceType": "AllergyIntolerance",
        "id": _generate_id(src),
        "clinicalStatus": _build_clinical_status(src),
        "verificationStatus": _build_verification_status(),
        "type": str(src.get("TYPE")).strip().lower() if src.get("TYPE") else None,
        "category": [category_value] if category_value else None,
        "code": _build_code(src),
        "patient": create_reference("Patient", src.get("PATIENT")) if src.get("PATIENT") else None,
        "encounter": create_reference("Encounter", src.get("ENCOUNTER")) if src.get("ENCOUNTER") else None,
        "recordedDate": to_fhir_datetime(src.get("START")),
        "onsetDateTime": to_fhir_datetime(src.get("START")),
        "lastOccurrence": to_fhir_datetime(src.get("STOP")) if src.get("STOP") else None,
        "reaction": reactions,
    }
    return filter_none_values(result)


def map_allergy(synthea_allergy: Dict[str, Any]) -> Dict[str, Any]:
    """Public API: Convert allergies.csv row to FHIR AllergyIntolerance."""
    return allergy_transform(synthea_allergy)


