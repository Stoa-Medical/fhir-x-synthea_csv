"""
Organization reverse mapper: FHIR R4 Organization → Synthea organizations.csv.
"""

from typing import Any, Dict, Optional, List

from ..common.reverse_transformers import (
    extract_extension_by_url,
    extract_geolocation,
    join_list_items,
    safe_get_first,
)


GEOLOCATION_URL = "http://hl7.org/fhir/StructureDefinition/geolocation"
ORG_STATS_URL = (
    "http://synthea.mitre.org/fhir/StructureDefinition/organization-stats"
)


def _extract_address_components(addresses: Optional[List[Dict[str, Any]]]) -> Dict[str, Optional[str]]:
    result = {
        "Address": None,
        "City": None,
        "State": None,
        "Zip": None,
        "Lat": None,
        "Lon": None,
    }

    if not addresses or not isinstance(addresses, list):
        return result

    # Prefer first address
    addr = None
    for a in addresses:
        if isinstance(a, dict):
            addr = a
            break
    if not addr:
        return result

    line_list = addr.get("line")
    result["Address"] = safe_get_first(line_list)
    result["City"] = addr.get("city")
    result["State"] = addr.get("state")
    result["Zip"] = addr.get("postalCode")

    lat, lon = extract_geolocation(addr)
    result["Lat"], result["Lon"] = lat, lon
    return result


def _extract_phone(telecom: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not telecom or not isinstance(telecom, list):
        return None
    phones = [t.get("value") for t in telecom if isinstance(t, dict) and t.get("system") == "phone" and t.get("value")]
    return join_list_items(phones, "; ")


def _extract_org_stats(extensions: Optional[List[Dict[str, Any]]]) -> Dict[str, Optional[str]]:
    result = {
        "Revenue": None,
        "Utilization": None,
    }

    if not extensions or not isinstance(extensions, list):
        return result

    ext = extract_extension_by_url(extensions, ORG_STATS_URL)
    if not ext:
        return result

    subexts = ext.get("extension", [])
    if not isinstance(subexts, list):
        return result

    def get_subext_value(url_key: str, value_key: str) -> Optional[str]:
        for se in subexts:
            if isinstance(se, dict) and se.get("url") == url_key and value_key in se:
                return str(se.get(value_key))
        return None

    result["Revenue"] = get_subext_value("revenue", "valueDecimal")
    result["Utilization"] = get_subext_value("utilization", "valueInteger")
    return result


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: (v if v is not None else "") for k, v in d.items()}


def fhir_organization_to_csv_transform(fhir_org: Dict[str, Any]) -> Dict[str, Any]:
    org_id = fhir_org.get("id")
    name = fhir_org.get("name")

    address_components = _extract_address_components(fhir_org.get("address", []))
    phone = _extract_phone(fhir_org.get("telecom", []))
    stats = _extract_org_stats(fhir_org.get("extension", []))

    result = {
        "Id": org_id,
        "Name": name,
        "Address": address_components["Address"],
        "City": address_components["City"],
        "State": address_components["State"],
        "Zip": address_components["Zip"],
        "Lat": address_components["Lat"],
        "Lon": address_components["Lon"],
        "Phone": phone,
        "Revenue": stats["Revenue"],
        "Utilization": stats["Utilization"],
    }

    return filter_none_values(result)


def map_fhir_organization_to_csv(fhir_org: Dict[str, Any]) -> Dict[str, Any]:
    if not fhir_org or fhir_org.get("resourceType") != "Organization":
        raise ValueError("Input must be a FHIR Organization resource")
    return fhir_organization_to_csv_transform(fhir_org)


