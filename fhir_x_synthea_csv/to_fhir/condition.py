"""
Condition mapper: Synthea CSV to FHIR R4 Condition resource.
"""

from typing import Any, Dict, Optional

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


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
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "resolved",
                    "display": "Resolved",
                }
            ]
        }
    else:
        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active",
                }
            ]
        }


def _build_verification_status() -> Dict[str, Any]:
    """
    Return verification status. All Synthea conditions are confirmed.
    """
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "confirmed",
                "display": "Confirmed",
            }
        ]
    }


def _build_category() -> list:
    """
    Return default category for conditions.
    """
    return [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "encounter-diagnosis",
                    "display": "Encounter Diagnosis",
                }
            ]
        }
    ]


def _build_code(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build the CodeableConcept for the condition code (SNOMED CT)."""
    code = src.get("CODE")
    description = src.get("DESCRIPTION")
    
    if not code:
        return None
    
    return {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": code,
                "display": description,
            }
        ],
        "text": description,
    }


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    """Generate a unique ID for the condition."""
    patient = src.get("PATIENT")
    start_date = src.get("START")
    code = src.get("CODE")
    
    if patient and start_date and code:
        # Clean date for ID generation
        date_clean = start_date.replace(" ", "").replace(":", "").replace("-", "")
        return f"cond-{patient}-{date_clean}-{code}"
    
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def condition_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea condition to FHIR Condition."""
    result = {
        "resourceType": "Condition",
        "id": _generate_id(src),
        "clinicalStatus": _build_clinical_status(src),
        "verificationStatus": _build_verification_status(),
        "category": _build_category(),
        "code": _build_code(src),
        "subject": create_reference("Patient", src.get("PATIENT")) if src.get("PATIENT") else None,
        "encounter": create_reference("Encounter", src.get("ENCOUNTER")) if src.get("ENCOUNTER") else None,
        "onsetDateTime": to_fhir_datetime(src.get("START")),
        "abatementDateTime": to_fhir_datetime(src.get("STOP")) if src.get("STOP") else None,
    }
    
    return filter_none_values(result)


# Using direct function approach for now


def map_condition(synthea_condition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV condition to FHIR Condition resource.
    
    Args:
        synthea_condition: Dictionary with Synthea condition CSV fields
        
    Returns:
        FHIR Condition resource as dictionary
    """
    return condition_transform(synthea_condition)