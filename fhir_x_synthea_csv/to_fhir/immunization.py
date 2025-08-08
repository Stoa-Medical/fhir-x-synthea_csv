"""
Immunization mapper: Synthea CSV to FHIR R4 Immunization resource.
"""

from typing import Any, Dict, Optional

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


def _build_vaccine_code(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build CodeableConcept for vaccineCode using CVX."""
    code = src.get("CODE")
    description = src.get("DESCRIPTION")
    if not code:
        return None
    return {
        "coding": [
            {
                "system": "http://hl7.org/fhir/sid/cvx",
                "code": code,
                "display": description,
            }
        ],
        "text": description,
    }


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    """Generate a unique ID for the immunization from patient+date+code."""
    patient = src.get("PATIENT")
    date = src.get("DATE")
    code = src.get("CODE")
    if patient and date and code:
        date_clean = str(date).replace(" ", "").replace(":", "").replace("-", "").replace("T", "")
        return f"immun-{patient}-{date_clean}-{code}"
    return None


def _build_cost_extension(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create extension for COST if present."""
    cost = src.get("COST")
    if cost is None or cost == "":
        return None
    try:
        value = float(str(cost))
    except (ValueError, TypeError):
        return None
    return {
        "url": "http://synthea.mitre.org/fhir/StructureDefinition/immunization-cost",
        "valueDecimal": value,
    }


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None/empty values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def immunization_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea immunization row to FHIR Immunization resource."""
    extensions = []
    cost_ext = _build_cost_extension(src)
    if cost_ext:
        extensions.append(cost_ext)

    result = {
        "resourceType": "Immunization",
        "id": _generate_id(src),
        "status": "completed",
        "vaccineCode": _build_vaccine_code(src),
        "patient": create_reference("Patient", src.get("PATIENT")) if src.get("PATIENT") else None,
        "encounter": create_reference("Encounter", src.get("ENCOUNTER")) if src.get("ENCOUNTER") else None,
        "occurrenceDateTime": to_fhir_datetime(src.get("DATE")),
        "extension": extensions or None,
    }

    return filter_none_values(result)


def map_immunization(synthea_immunization: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV immunization to FHIR Immunization resource.

    Args:
        synthea_immunization: Dictionary with Synthea immunization CSV fields

    Returns:
        FHIR Immunization resource as dictionary
    """
    return immunization_transform(synthea_immunization)


