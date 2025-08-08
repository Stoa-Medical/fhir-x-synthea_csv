"""
Supply reverse mapper: FHIR R4 SupplyDelivery resource to Synthea supplies.csv.
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def _extract_encounter_id_from_extensions(extensions: Optional[list]) -> Optional[str]:
    if not extensions or not isinstance(extensions, list):
        return None
    for ext in extensions:
        if not isinstance(ext, Dict):
            continue
        if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/resource-encounter":
            return extract_reference_id(ext.get("valueReference"))
    return None


def fhir_supply_to_csv_transform(fhir_supply: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform FHIR SupplyDelivery to Synthea supplies.csv row.
    """
    # Date
    occurrence = fhir_supply.get("occurrenceDateTime")
    if not occurrence:
        # Optional: handle occurrencePeriod.start
        occurrence_period = fhir_supply.get("occurrencePeriod")
        if isinstance(occurrence_period, dict):
            occurrence = occurrence_period.get("start")

    date = parse_fhir_datetime(occurrence)
    if date and len(date) > 10:
        date = date[:10]

    # Patient
    patient_ref = fhir_supply.get("patient")
    patient_id = extract_reference_id(patient_ref)

    # Encounter via extension
    encounter_id = _extract_encounter_id_from_extensions(fhir_supply.get("extension"))

    # Coding and description
    item = fhir_supply.get("suppliedItem", {}) or {}
    codeable = item.get("itemCodeableConcept") if isinstance(item, dict) else None

    snomed_coding = extract_coding_by_system(codeable, "http://snomed.info/sct")
    code = None
    description = None

    if snomed_coding:
        code = snomed_coding.get("code")
        description = snomed_coding.get("display")
    elif isinstance(codeable, dict):
        coding_list = codeable.get("coding", [])
        if coding_list and isinstance(coding_list, list):
            first_coding = coding_list[0]
            if isinstance(first_coding, dict):
                code = first_coding.get("code")
                description = description or first_coding.get("display")
        if not description:
            description = codeable.get("text")

    # Quantity
    quantity_value = None
    if isinstance(item, dict):
        quantity = item.get("quantity")
        if isinstance(quantity, dict):
            qv = quantity.get("value")
            if qv is not None:
                quantity_value = str(qv)

    result = {
        "DATE": date,
        "PATIENT": patient_id,
        "ENCOUNTER": encounter_id,
        "CODE": code,
        "DESCRIPTION": description,
        "QUANTITY": quantity_value,
    }

    return filter_none_values(result)


def map_fhir_supply_to_csv(fhir_supply: Dict[str, Any]) -> Dict[str, Any]:
    """Convert FHIR SupplyDelivery to Synthea supplies.csv dict."""
    if not fhir_supply or fhir_supply.get("resourceType") != "SupplyDelivery":
        raise ValueError("Input must be a FHIR SupplyDelivery resource")
    return fhir_supply_to_csv_transform(fhir_supply)


