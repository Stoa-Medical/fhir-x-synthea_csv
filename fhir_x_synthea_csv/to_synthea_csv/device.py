"""
Device reverse mapper: FHIR R4 Device to Synthea devices.csv.
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
    extract_extension_by_url,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings for CSV output."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def _extract_use_period(device: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    extensions = device.get("extension")
    use_ext = extract_extension_by_url(
        extensions,
        "http://synthea.tools/fhir/StructureDefinition/device-use-period",
    )
    if not use_ext or not isinstance(use_ext, Dict):
        return None, None
    value_period = use_ext.get("valuePeriod")
    if not isinstance(value_period, Dict):
        return None, None
    start = parse_fhir_datetime(value_period.get("start"))
    stop = parse_fhir_datetime(value_period.get("end"))
    return start, stop


def _extract_encounter_id(device: Dict[str, Any]) -> Optional[str]:
    extensions = device.get("extension")
    enc_ext = extract_extension_by_url(
        extensions,
        "http://hl7.org/fhir/StructureDefinition/resource-encounter",
    )
    if not enc_ext or not isinstance(enc_ext, Dict):
        return None
    return extract_reference_id(enc_ext.get("valueReference"))


def fhir_device_to_csv_transform(fhir_device: Dict[str, Any]) -> Dict[str, Any]:
    """Transform FHIR Device to Synthea devices.csv row."""
    # Start/Stop from use-period extension
    start, stop = _extract_use_period(fhir_device)

    # Patient
    patient_ref = fhir_device.get("patient")
    patient_id = extract_reference_id(patient_ref)

    # Encounter via extension
    encounter_id = _extract_encounter_id(fhir_device)

    # Type coding and description
    type_concept = fhir_device.get("type")
    code = None
    description = None
    if isinstance(type_concept, Dict):
        snomed_coding = extract_coding_by_system(type_concept, "http://snomed.info/sct")
        if snomed_coding:
            code = snomed_coding.get("code")
            description = snomed_coding.get("display")
        else:
            coding_list = type_concept.get("coding", [])
            if isinstance(coding_list, list) and coding_list:
                first = coding_list[0]
                if isinstance(first, Dict):
                    code = first.get("code")
                    description = first.get("display") or description
        if not description:
            description = type_concept.get("text")

    # UDI
    udi_list = fhir_device.get("udiCarrier") or []
    udi_value = None
    if isinstance(udi_list, list) and udi_list:
        first_udi = udi_list[0]
        if isinstance(first_udi, Dict):
            udi_value = (
                first_udi.get("deviceIdentifier")
                or first_udi.get("carrierHRF")
                or None
            )

    result = {
        "START": start,
        "STOP": stop,
        "PATIENT": patient_id,
        "ENCOUNTER": encounter_id,
        "CODE": code,
        "DESCRIPTION": description,
        "UDI": udi_value,
    }

    return filter_none_values(result)


def map_fhir_device_to_csv(fhir_device: Dict[str, Any]) -> Dict[str, Any]:
    """Convert FHIR Device to Synthea devices.csv dict."""
    if not fhir_device or fhir_device.get("resourceType") != "Device":
        raise ValueError("Input must be a FHIR Device resource")
    return fhir_device_to_csv_transform(fhir_device)



