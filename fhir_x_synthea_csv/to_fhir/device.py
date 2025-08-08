"""
Device mapper: Synthea CSV devices.csv to FHIR R4 Device resource.
"""

from typing import Any, Dict, Optional, List

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


def _build_type(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build Device.type CodeableConcept using SNOMED CT code and description."""
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


def _build_udi(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Build udiCarrier array from UDI string."""
    udi = src.get("UDI")
    if not udi:
        return None
    return [
        {
            # deviceIdentifier holds the DI portion in many implementations;
            # carrierHRF for a human-readable representation
            "deviceIdentifier": str(udi),
            "carrierHRF": str(udi),
        }
    ]


def _build_use_period_extension(start: Optional[str], stop: Optional[str]) -> Optional[Dict[str, Any]]:
    if not start and not stop:
        return None
    period: Dict[str, Any] = {}
    start_dt = to_fhir_datetime(start) if start else None
    end_dt = to_fhir_datetime(stop) if stop else None
    if start_dt:
        period["start"] = start_dt
    if end_dt:
        period["end"] = end_dt
    if not period:
        return None
    return {
        "url": "http://synthea.tools/fhir/StructureDefinition/device-use-period",
        "valuePeriod": period,
    }


def _build_encounter_extension(encounter_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not encounter_id:
        return None
    return {
        "url": "http://hl7.org/fhir/StructureDefinition/resource-encounter",
        "valueReference": create_reference("Encounter", encounter_id),
    }


def _derive_status(stop: Optional[str]) -> Optional[str]:
    # Active if no STOP provided, inactive otherwise
    return "active" if not stop else "inactive"


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    patient = src.get("PATIENT")
    start = src.get("START")
    code = src.get("CODE")
    if patient and start and code:
        start_clean = str(start).replace(" ", "").replace(":", "").replace("-", "")
        return f"device-{patient}-{start_clean}-{code}"
    return None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def device_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea devices.csv row to FHIR Device resource."""
    use_period_ext = _build_use_period_extension(src.get("START"), src.get("STOP"))
    encounter_ext = _build_encounter_extension(src.get("ENCOUNTER"))
    extensions = [e for e in [use_period_ext, encounter_ext] if e]

    result: Dict[str, Any] = {
        "resourceType": "Device",
        "id": _generate_id(src),
        "status": _derive_status(src.get("STOP")),
        "patient": create_reference("Patient", src.get("PATIENT")) if src.get("PATIENT") else None,
        "type": _build_type(src),
        "udiCarrier": _build_udi(src),
        "extension": extensions if extensions else None,
    }

    return filter_none_values(result)


def map_device(synthea_device: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV device row to FHIR Device resource.

    Args:
        synthea_device: Dictionary with Synthea devices CSV fields

    Returns:
        FHIR Device resource as dictionary
    """
    return device_transform(synthea_device)



