"""
Provider mapper: Synthea providers.csv to FHIR R4 Practitioner and PractitionerRole.
"""

from typing import Any, Dict, Optional, List

from ..common.transformers import (
    create_reference,
)
from ..common.lexicons import (
    gender_lexicon,
)


def _build_name_from_full(name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not name or not isinstance(name, str):
        return None
    parts = [p for p in name.strip().split(" ") if p]
    if not parts:
        return None
    given = parts[0]
    family = parts[-1] if len(parts) > 1 else None
    human_name: Dict[str, Any] = {"use": "official"}
    if given:
        human_name["given"] = [given]
    if family:
        human_name["family"] = family
    return human_name if len(human_name) > 1 else None


def _build_address(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    address: Dict[str, Any] = {}
    if street := src.get("Address"):
        address["line"] = [street]
    if city := src.get("City"):
        address["city"] = city
    if state := src.get("State"):
        address["state"] = state
    if postal := src.get("Zip"):
        address["postalCode"] = postal

    # Geolocation extension if both lat/lon present
    lat = src.get("Lat")
    lon = src.get("Lon")
    if lat not in (None, "") and lon not in (None, ""):
        try:
            lat_f = float(lat)
            lon_f = float(lon)
            address["extension"] = [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {"url": "latitude", "valueDecimal": lat_f},
                        {"url": "longitude", "valueDecimal": lon_f},
                    ],
                }
            ]
        except (TypeError, ValueError):
            # ignore bad coordinates
            pass

    return address if address else None


def _build_role_code(speciality: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    if not speciality:
        return None
    # Represent as CodeableConcept with text; no known coding system provided by CSV
    return [{"text": str(speciality)}]


def _build_stats_extension(encounters: Optional[str], procedures: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    values: List[Dict[str, Any]] = []
    ext_url = "http://example.org/fhir/StructureDefinition/provider-stats"

    def to_int_or_none(v: Optional[str]) -> Optional[int]:
        if v in (None, ""):
            return None
        try:
            return int(float(str(v)))
        except (TypeError, ValueError):
            return None

    enc = to_int_or_none(encounters)
    proc = to_int_or_none(procedures)

    subext = []
    if enc is not None:
        subext.append({"url": "encounters", "valueInteger": enc})
    if proc is not None:
        subext.append({"url": "procedures", "valueInteger": proc})

    if subext:
        values.append({"url": ext_url, "extension": subext})

    return values or None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v not in (None, "", [])}


def _generate_practitioner_role_id(src: Dict[str, Any]) -> Optional[str]:
    pid = src.get("Id")
    org = src.get("Organization")
    if pid and org:
        return f"prr-{pid}-{org}"
    return None


def map_practitioner(synthea_provider: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert providers.csv row to FHIR Practitioner.
    """
    result = {
        "resourceType": "Practitioner",
        "id": synthea_provider.get("Id"),
        "name": [n for n in [_build_name_from_full(synthea_provider.get("Name"))] if n],
        "gender": gender_lexicon.get(synthea_provider.get("Gender")) if synthea_provider.get("Gender") else None,
        "address": [a for a in [_build_address(synthea_provider)] if a],
    }
    return filter_none_values(result)


def map_practitioner_role(synthea_provider: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert providers.csv row to FHIR PractitionerRole.
    """
    result = {
        "resourceType": "PractitionerRole",
        "id": _generate_practitioner_role_id(synthea_provider),
        "practitioner": create_reference("Practitioner", synthea_provider.get("Id")) if synthea_provider.get("Id") else None,
        "organization": create_reference("Organization", synthea_provider.get("Organization")) if synthea_provider.get("Organization") else None,
        "code": _build_role_code(synthea_provider.get("Speciality")),
        "extension": _build_stats_extension(synthea_provider.get("Encounters"), synthea_provider.get("Procedures")),
    }
    return filter_none_values(result)


