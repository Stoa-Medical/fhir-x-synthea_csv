"""
Organization mapper: Synthea CSV (organizations.csv) to FHIR R4 Organization.

Provider organizations (e.g., hospitals) are modeled as FHIR Organization.
Geolocation is represented with the standard Address geolocation extension,
and aggregate simulation metrics are captured via a custom extension.
"""

from typing import Any, Dict, List, Optional
import re


GEOLOCATION_URL = "http://hl7.org/fhir/StructureDefinition/geolocation"
ORG_STATS_URL = (
    "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats"
)


def _build_address(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    address: Dict[str, Any] = {}

    line = src.get("Address")
    city = src.get("City")
    state = src.get("State")
    postal_code = src.get("Zip")
    lat = src.get("Lat")
    lon = src.get("Lon")

    if line:
        address["line"] = [line]
    if city:
        address["city"] = city
    if state:
        address["state"] = state
    if postal_code:
        address["postalCode"] = postal_code

    # Add geolocation extension if both coordinates present
    if lat and lon:
        try:
            address.setdefault("extension", []).append(
                {
                    "url": GEOLOCATION_URL,
                    "extension": [
                        {"url": "latitude", "valueDecimal": float(str(lat))},
                        {"url": "longitude", "valueDecimal": float(str(lon))},
                    ],
                }
            )
        except (ValueError, TypeError):
            # Skip invalid coordinates
            pass

    return address if address else None


def _split_phones(phone_field: Optional[str]) -> List[str]:
    if not phone_field:
        return []
    parts = re.split(r"[;,/|]", str(phone_field))
    return [p.strip() for p in parts if p and p.strip()]


def _build_telecom(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    telecom: List[Dict[str, Any]] = []
    for phone in _split_phones(src.get("Phone")):
        telecom.append({"system": "phone", "value": phone})
    return telecom if telecom else None


def _build_type() -> List[Dict[str, Any]]:
    # Organization type: Healthcare Provider
    return [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "prov",
                    "display": "Healthcare Provider",
                }
            ]
        }
    ]


def _build_extensions(src: Dict[str, Any]) -> List[Dict[str, Any]]:
    extensions: List[Dict[str, Any]] = []

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

    add_decimal("revenue", src.get("Revenue"))
    add_integer("utilization", src.get("Utilization"))

    if sub_exts:
        extensions.append({"url": ORG_STATS_URL, "extension": sub_exts})

    return extensions


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def organization_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea organizations.csv row to FHIR Organization."""
    result: Dict[str, Any] = {
        "resourceType": "Organization",
        "id": src.get("Id"),
        "name": src.get("Name"),
        "type": _build_type(),
        "address": [a for a in [_build_address(src)] if a],
        "telecom": _build_telecom(src),
        "extension": _build_extensions(src),
    }

    if not result.get("address"):
        result.pop("address", None)
    return filter_none_values(result)


def map_organization(synthea_organization: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV organization to FHIR Organization resource.

    Args:
        synthea_organization: Dictionary with Synthea organizations.csv fields

    Returns:
        FHIR Organization resource as dictionary
    """
    return organization_transform(synthea_organization)


