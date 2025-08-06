"""
Observation mapper: Synthea CSV to FHIR R4 Observation resource.
"""

from typing import Any, Dict, Optional, Union

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


# Import the MappingDict class
from ..common.lexicons import MappingDict

# Category mapping
observation_category_mapping = {
    "vital-signs": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs",
            }
        ]
    },
    "laboratory": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
                "display": "Laboratory",
            }
        ]
    },
    "survey": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "survey",
                "display": "Survey",
            }
        ]
    },
    "social-history": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "social-history",
                "display": "Social History",
            }
        ]
    },
    "imaging": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "imaging",
                "display": "Imaging",
            }
        ]
    },
    "procedure": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "procedure",
                "display": "Procedure",
            }
        ]
    },
}

observation_category_lexicon = MappingDict(
    observation_category_mapping,
    default={
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "exam",
                "display": "Exam",
            }
        ]
    },
)


def _is_numeric(value: Any) -> bool:
    """Check if a value can be converted to a number."""
    if value is None or value == "":
        return False
    try:
        float(str(value))
        return True
    except (ValueError, TypeError):
        return False


def _is_boolean(value: Any) -> bool:
    """Check if a value is a boolean."""
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return value.lower() in ["true", "false"]
    return False


def _convert_boolean(value: Any) -> bool:
    """Convert value to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def _build_value_element(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Build the appropriate value[x] element based on the value type.
    Returns a dict with the appropriate key (e.g., {"valueQuantity": {...}})
    """
    value = src.get("VALUE")
    units = src.get("UNITS")
    
    if value is None or value == "":
        return None
    
    # Check for boolean
    if _is_boolean(value):
        return {"valueBoolean": _convert_boolean(value)}
    
    # Check for numeric
    if _is_numeric(value):
        quantity = {"value": float(str(value))}
        
        if units:
            quantity["unit"] = units
            quantity["code"] = units
            quantity["system"] = "http://unitsofmeasure.org"
        else:
            # Default unit for dimensionless quantities
            quantity["unit"] = "1"
            quantity["code"] = "1"
            quantity["system"] = "http://unitsofmeasure.org"
        
        return {"valueQuantity": quantity}
    
    # Default to string
    return {"valueString": str(value)}


def _build_code(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build the CodeableConcept for the observation code."""
    code = src.get("CODE")
    description = src.get("DESCRIPTION")
    
    if not code:
        return None
    
    return {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": code,
                "display": description,
            }
        ],
        "text": description,
    }


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    """Generate a unique ID for the observation."""
    # Use combination of patient, date, and code for uniqueness
    patient = src.get("PATIENT")
    date = src.get("DATE")
    code = src.get("CODE")
    
    if patient and date and code:
        # Simple hash or concatenation
        # In production, might use a proper UUID or hash
        date_clean = date.replace(" ", "").replace(":", "").replace("-", "")
        return f"obs-{patient}-{date_clean}-{code}"
    
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def observation_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea observation to FHIR Observation."""
    result = {
        "resourceType": "Observation",
        "id": _generate_id(src),
        "status": "final",  # All CSV observations are final
        "code": _build_code(src),
        "subject": create_reference("Patient", src.get("PATIENT")) if src.get("PATIENT") else None,
        "encounter": create_reference("Encounter", src.get("ENCOUNTER")) if src.get("ENCOUNTER") else None,
        "effectiveDateTime": to_fhir_datetime(src.get("DATE")),
        "issued": to_fhir_datetime(src.get("DATE")),
        "category": [observation_category_lexicon.forward_get(src.get("TYPE"))] if src.get("TYPE") else None,
    }
    
    # Add value element if present
    value_element = _build_value_element(src)
    if value_element:
        result.update(value_element)
    
    return filter_none_values(result)


# Using direct function approach for now


def map_observation(synthea_observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV observation to FHIR Observation resource.
    
    Args:
        synthea_observation: Dictionary with Synthea observation CSV fields
        
    Returns:
        FHIR Observation resource as dictionary
    """
    return observation_transform(synthea_observation)