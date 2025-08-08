"""
Provider reverse mapper: FHIR Practitioner (+ PractitionerRole) to Synthea providers.csv row.
"""

from typing import Any, Dict, Optional, Tuple

from ..common.reverse_transformers import (
    extract_geolocation,
    safe_get_first,
    extract_reference_id,
)
from ..common.reverse_lexicons import (
    gender_reverse_lexicon,
)


PROVIDER_STATS_URL = "http://example.org/fhir/StructureDefinition/provider-stats"


def _compose_name(prac: Dict[str, Any]) -> Optional[str]:
    names = prac.get("name", [])
    if not names or not isinstance(names, list):
        return None
    name = names[0] if names else None
    if not isinstance(name, dict):
        return None
    given = name.get("given") or []
    first = safe_get_first(given)
    family = name.get("family")
    if first and family:
        return f"{first} {family}"
    return first or family


def _extract_address_components(prac: Dict[str, Any]) -> Dict[str, Optional[str]]:
    result = {
        "Address": None,
        "City": None,
        "State": None,
        "Zip": None,
        "Lat": None,
        "Lon": None,
    }
    addresses = prac.get("address", [])
    if not addresses or not isinstance(addresses, list):
        return result
    addr = addresses[0]
    if not isinstance(addr, dict):
        return result
    line = addr.get("line") or []
    result["Address"] = safe_get_first(line)
    result["City"] = addr.get("city")
    result["State"] = addr.get("state")
    result["Zip"] = addr.get("postalCode")
    lat, lon = extract_geolocation(addr)
    result["Lat"] = lat
    result["Lon"] = lon
    return result


def _extract_speciality(role: Optional[Dict[str, Any]]) -> Optional[str]:
    if not role or not isinstance(role, dict):
        return None
    codes = role.get("code") or []
    if not codes:
        return None
    cc = codes[0]
    if not isinstance(cc, dict):
        return None
    # Prefer text, fall back to first coding display/code
    if txt := cc.get("text"):
        return txt
    coding = cc.get("coding") or []
    if coding:
        first = coding[0]
        if isinstance(first, dict):
            return first.get("display") or first.get("code")
    return None


def _extract_stats(role: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    if not role or not isinstance(role, dict):
        return None, None
    exts = role.get("extension") or []
    for ext in exts:
        if isinstance(ext, dict) and ext.get("url") == PROVIDER_STATS_URL:
            subs = ext.get("extension") or []
            enc = None
            proc = None
            for sub in subs:
                if not isinstance(sub, dict):
                    continue
                if sub.get("url") == "encounters":
                    val = sub.get("valueInteger")
                    enc = str(val) if val is not None else None
                elif sub.get("url") == "procedures":
                    val = sub.get("valueInteger")
                    proc = str(val) if val is not None else None
            return enc, proc
    return None, None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: (v if v is not None else "") for k, v in d.items()}


def fhir_provider_to_csv_transform(
    practitioner: Dict[str, Any],
    practitioner_role: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Transform FHIR Practitioner (+ optional PractitionerRole) to providers.csv row.
    """
    provider_id = practitioner.get("id")
    name = _compose_name(practitioner)
    gender = gender_reverse_lexicon.get(practitioner.get("gender"))
    addr = _extract_address_components(practitioner)

    org = None
    speciality = None
    encounters = None
    procedures = None

    if practitioner_role:
        org = extract_reference_id(practitioner_role.get("organization"))
        speciality = _extract_speciality(practitioner_role)
        encounters, procedures = _extract_stats(practitioner_role)

    result = {
        "Id": provider_id,
        "Organization": org,
        "Name": name,
        "Gender": gender,
        "Speciality": speciality,
        "Address": addr["Address"],
        "City": addr["City"],
        "State": addr["State"],
        "Zip": addr["Zip"],
        "Lat": addr["Lat"],
        "Lon": addr["Lon"],
        "Encounters": encounters,
        "Procedures": procedures,
    }
    return filter_none_values(result)


def map_fhir_provider_to_csv(
    practitioner: Dict[str, Any],
    practitioner_role: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convert FHIR Practitioner (+ optional PractitionerRole) to Synthea providers.csv format.
    """
    if not practitioner or practitioner.get("resourceType") != "Practitioner":
        raise ValueError("First argument must be a FHIR Practitioner resource")
    if practitioner_role and practitioner_role.get("resourceType") != "PractitionerRole":
        raise ValueError("Second argument, if provided, must be a FHIR PractitionerRole resource")
    return fhir_provider_to_csv_transform(practitioner, practitioner_role)


