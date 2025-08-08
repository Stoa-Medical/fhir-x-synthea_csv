"""
Supply mapper: Synthea CSV to FHIR R4 SupplyDelivery resource.
"""

from typing import Any, Dict, Optional

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


def _build_item_codeable_concept(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build CodeableConcept for the supplied item (SNOMED CT preferred)."""
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


def _build_supplied_item(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build the suppliedItem element with quantity and itemCodeableConcept."""
    item_concept = _build_item_codeable_concept(src)
    quantity_value = src.get("QUANTITY")

    supplied_item: Dict[str, Any] = {}

    if item_concept:
        supplied_item["itemCodeableConcept"] = item_concept

    if quantity_value is not None and quantity_value != "":
        try:
            supplied_item["quantity"] = {"value": float(str(quantity_value))}
        except (ValueError, TypeError):
            # If quantity is non-numeric, omit it
            pass

    return supplied_item if supplied_item else None


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    """Generate a deterministic ID for the supply delivery."""
    patient = src.get("PATIENT")
    date = src.get("DATE")
    code = src.get("CODE")

    if patient and date and code:
        date_clean = str(date).replace(" ", "").replace(":", "").replace("-", "")
        return f"supply-{patient}-{date_clean}-{code}"
    return None


def _build_encounter_extension(encounter_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Build Resource Encounter extension to associate an encounter."""
    if not encounter_id:
        return None
    return {
        "url": "http://hl7.org/fhir/StructureDefinition/resource-encounter",
        "valueReference": create_reference("Encounter", encounter_id),
    }


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None/empty values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def supply_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea supplies.csv row to FHIR SupplyDelivery resource."""
    encounter_ext = _build_encounter_extension(src.get("ENCOUNTER"))
    extensions = [e for e in [encounter_ext] if e]

    result: Dict[str, Any] = {
        "resourceType": "SupplyDelivery",
        "id": _generate_id(src),
        "status": "completed",
        "patient": create_reference("Patient", src.get("PATIENT")) if src.get("PATIENT") else None,
        "occurrenceDateTime": to_fhir_datetime(src.get("DATE")),
        "suppliedItem": _build_supplied_item(src),
        "extension": extensions if extensions else None,
    }

    return filter_none_values(result)


def map_supply(synthea_supply: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV supplies row to FHIR SupplyDelivery resource.

    Args:
        synthea_supply: Dictionary with Synthea supplies CSV fields

    Returns:
        FHIR SupplyDelivery resource as dictionary
    """
    return supply_transform(synthea_supply)


