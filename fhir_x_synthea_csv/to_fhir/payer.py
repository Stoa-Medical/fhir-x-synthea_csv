"""
Payer mapper: Synthea CSV to FHIR R4 Organization resource.

The payer entity is modeled as a FHIR Organization. Aggregate statistics are
represented via a custom extension.
"""

from typing import Any, Dict, List, Optional
import re


PAYER_OWNERSHIP_URL = (
    "http://synthea.mitre.org/fhir/StructureDefinition/payer-ownership"
)
PAYER_STATS_URL = (
    "http://synthea.mitre.org/fhir/StructureDefinition/payer-stats"
)


def _build_address(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    address: Dict[str, Any] = {}

    line = src.get("Address")
    city = src.get("City")
    state = src.get("State_Headquartered")
    postal_code = src.get("Zip")

    if line:
        address["line"] = [line]
    if city:
        address["city"] = city
    if state:
        address["state"] = state
    if postal_code:
        address["postalCode"] = postal_code

    return address if address else None


def _split_phones(phone_field: Optional[str]) -> List[str]:
    if not phone_field:
        return []
    # Split on commas, semicolons, slashes or pipes
    parts = re.split(r"[;,/|]", str(phone_field))
    return [p.strip() for p in parts if p and p.strip()]


def _build_telecom(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    telecom: List[Dict[str, Any]] = []
    for phone in _split_phones(src.get("Phone")):
        telecom.append({"system": "phone", "value": phone})
    return telecom if telecom else None


def _build_type() -> List[Dict[str, Any]]:
    # Organization type: Insurance Company
    return [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "ins",
                    "display": "Insurance Company",
                }
            ]
        }
    ]


def _build_extensions(src: Dict[str, Any]) -> List[Dict[str, Any]]:
    extensions: List[Dict[str, Any]] = []

    # Ownership extension (valueCode)
    ownership = src.get("Ownership")
    if ownership:
        extensions.append({
            "url": PAYER_OWNERSHIP_URL,
            "valueCode": str(ownership).lower(),
        })

    # Stats extension with nested sub-extensions
    sub_exts: List[Dict[str, Any]] = []

    def add_decimal(url_key: str, value: Any) -> None:
        if value is None or value == "":
            return
        try:
            sub_exts.append({"url": url_key, "valueDecimal": float(str(value))})
        except (ValueError, TypeError):
            pass

    def add_integer(url_key: str, value: Any) -> None:
        if value is None or value == "":
            return
        try:
            sub_exts.append({"url": url_key, "valueInteger": int(float(str(value)))})
        except (ValueError, TypeError):
            pass

    add_decimal("amountCovered", src.get("Amount_Covered"))
    add_decimal("amountUncovered", src.get("Amount_Uncovered"))
    add_decimal("revenue", src.get("Revenue"))
    add_integer("coveredEncounters", src.get("Covered_Encounters"))
    add_integer("uncoveredEncounters", src.get("Uncovered_Encounters"))
    add_integer("coveredMedications", src.get("Covered_Medications"))
    add_integer("uncoveredMedications", src.get("Uncovered_Medications"))
    add_integer("coveredProcedures", src.get("Covered_Procedures"))
    add_integer("uncoveredProcedures", src.get("Uncovered_Procedures"))
    add_integer("coveredImmunizations", src.get("Covered_Immunizations"))
    add_integer("uncoveredImmunizations", src.get("Uncovered_Immunizations"))
    add_integer("uniqueCustomers", src.get("Unique_Customers"))
    add_decimal("qolsAvg", src.get("QOLS_Avg"))
    add_integer("memberMonths", src.get("Member_Months"))

    if sub_exts:
        extensions.append({"url": PAYER_STATS_URL, "extension": sub_exts})

    return extensions


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def payer_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea payer row into FHIR Organization resource."""
    result: Dict[str, Any] = {
        "resourceType": "Organization",
        "id": src.get("Id"),
        "name": src.get("Name"),
        "type": _build_type(),
        "address": [a for a in [_build_address(src)] if a],
        "telecom": _build_telecom(src),
        "extension": _build_extensions(src),
    }
    # Remove keys with None/empty values
    if not result.get("address"):
        result.pop("address", None)
    return filter_none_values(result)


def map_payer(synthea_payer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV payer to FHIR Organization resource.

    Args:
        synthea_payer: Dictionary with Synthea payers.csv fields

    Returns:
        FHIR Organization resource as dictionary
    """
    return payer_transform(synthea_payer)


