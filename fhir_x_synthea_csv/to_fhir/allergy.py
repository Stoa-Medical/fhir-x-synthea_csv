"""
Allergy mapper: Synthea CSV to FHIR R4 AllergyIntolerance resource.
"""

from typing import Any, Dict, Optional, List

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


def _system_uri_from_label(label: Optional[str]) -> Optional[str]:
    """Map a human-readable system label to its canonical URI."""
    if not label:
        return None
    if label.startswith("http://") or label.startswith("https://"):
        return label
    normalized = label.strip().lower()
    if normalized in {"snomed", "snomed-ct", "snomed ct"}:
        return "http://snomed.info/sct"
    if normalized in {"rxnorm", "rx norm"}:
        return "http://www.nlm.nih.gov/research/umls/rxnorm"
    # Fallback to provided label if unknown
    return label


def _build_clinical_status(src: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine clinical status based on presence of STOP date.
    Active if no STOP date, resolved if STOP date present.
    """
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
    else:
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
    """All Synthea allergies are considered confirmed."""
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                "code": "confirmed",
                "display": "Confirmed",
            }
        ]
    }


def _normalize_type(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.strip().lower()
    if v in {"allergy", "intolerance"}:
        return v
    return None


def _normalize_category(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    v = value.strip().lower()
    mapping = {
        "drug": "medication",
        "medication": "medication",
        "food": "food",
        "environment": "environment",
    }
    mapped = mapping.get(v)
    return [mapped] if mapped else None


def _build_code(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build the CodeableConcept for the allergy code (RxNorm for meds, SNOMED otherwise)."""
    code = src.get("CODE")
    description = src.get("DESCRIPTION")
    system_label = src.get("SYSTEM")

    if not code:
        return None

    system_uri = _system_uri_from_label(system_label) or "http://snomed.info/sct"

    return {
        "coding": [
            {
                "system": system_uri,
                "code": code,
                "display": description,
            }
        ],
        "text": description,
    }


def _build_reaction_entry(code: Optional[str], description: Optional[str], severity: Optional[str]) -> Optional[Dict[str, Any]]:
    if not code and not description and not severity:
        return None

    reaction: Dict[str, Any] = {}

    if code or description:
        reaction["manifestation"] = [
            {
                "coding": ([
                    {
                        "system": "http://snomed.info/sct",
                        "code": code,
                        "display": description,
                    }
                ] if code else []),
                "text": description,
            }
        ]

    if severity:
        sev = severity.strip().lower()
        if sev in {"mild", "moderate", "severe"}:
            reaction["severity"] = sev

    return reaction if reaction else None


def _build_reactions(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    r1 = _build_reaction_entry(src.get("REACTION1"), src.get("DESCRIPTION1"), src.get("SEVERITY1"))
    r2 = _build_reaction_entry(src.get("REACTION2"), src.get("DESCRIPTION2"), src.get("SEVERITY2"))
    reactions = [r for r in [r1, r2] if r]
    return reactions or None


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    """Generate a unique ID for the allergy."""
    patient = src.get("PATIENT")
    start_date = src.get("START")
    code = src.get("CODE")

    if patient and start_date and code:
        date_clean = str(start_date).replace(" ", "").replace(":", "").replace("-", "")
        return f"alg-{patient}-{date_clean}-{code}"

    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None/empty list/empty string values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def allergy_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea allergy to FHIR AllergyIntolerance."""
    result = {
        "resourceType": "AllergyIntolerance",
        "id": _generate_id(src),
        "clinicalStatus": _build_clinical_status(src),
        "verificationStatus": _build_verification_status(),
        "type": _normalize_type(src.get("TYPE")),
        "category": _normalize_category(src.get("CATEGORY")),
        "code": _build_code(src),
        "patient": create_reference("Patient", src.get("PATIENT")) if src.get("PATIENT") else None,
        "encounter": create_reference("Encounter", src.get("ENCOUNTER")) if src.get("ENCOUNTER") else None,
        "onsetDateTime": to_fhir_datetime(src.get("START")),
        "lastOccurrence": to_fhir_datetime(src.get("STOP")) if src.get("STOP") else None,
        "reaction": _build_reactions(src),
    }

    return filter_none_values(result)


def map_allergy(synthea_allergy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV allergy to FHIR AllergyIntolerance resource.

    Args:
        synthea_allergy: Dictionary with Synthea allergy CSV fields

    Returns:
        FHIR AllergyIntolerance resource as dictionary
    """
    return allergy_transform(synthea_allergy)