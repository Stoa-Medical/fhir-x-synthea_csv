"""
Payer reverse mapper: FHIR R4 Organization resource to Synthea payers.csv row.
"""

from typing import Any, Dict, List, Optional

from ..common.reverse_transformers import (
    extract_extension_by_url,
)


PAYER_OWNERSHIP_URL = (
    "http://synthea.mitre.org/fhir/StructureDefinition/payer-ownership"
)
PAYER_STATS_URL = (
    "http://synthea.mitre.org/fhir/StructureDefinition/payer-stats"
)


def _safe_get_first(items: Optional[List[Any]]) -> Optional[Any]:
    if items and isinstance(items, list) and len(items) > 0:
        return items[0]
    return None


def _extract_address(org: Dict[str, Any]) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {
        "Address": None,
        "City": None,
        "State_Headquartered": None,
        "Zip": None,
    }
    addresses = org.get("address")
    addr = _safe_get_first(addresses) if isinstance(addresses, list) else None
    if not isinstance(addr, dict):
        return result
    line = addr.get("line")
    result["Address"] = _safe_get_first(line) if isinstance(line, list) else None
    result["City"] = addr.get("city")
    result["State_Headquartered"] = addr.get("state")
    result["Zip"] = addr.get("postalCode")
    return result


def _extract_phone(org: Dict[str, Any]) -> Optional[str]:
    telecom = org.get("telecom")
    if not isinstance(telecom, list):
        return None
    phones: List[str] = []
    for t in telecom:
        if isinstance(t, dict) and t.get("system") == "phone":
            val = t.get("value")
            if val:
                phones.append(str(val))
    return "; ".join(phones) if phones else None


def _extract_ownership(org: Dict[str, Any]) -> Optional[str]:
    exts = org.get("extension")
    ext = extract_extension_by_url(exts, PAYER_OWNERSHIP_URL)
    if ext and isinstance(ext, dict):
        val = ext.get("valueCode")
        return str(val) if val is not None else None
    return None


def _extract_stats(org: Dict[str, Any]) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {
        "Amount_Covered": None,
        "Amount_Uncovered": None,
        "Revenue": None,
        "Covered_Encounters": None,
        "Uncovered_Encounters": None,
        "Covered_Medications": None,
        "Uncovered_Medications": None,
        "Covered_Procedures": None,
        "Uncovered_Procedures": None,
        "Covered_Immunizations": None,
        "Uncovered_Immunizations": None,
        "Unique_Customers": None,
        "QOLS_Avg": None,
        "Member_Months": None,
    }

    exts = org.get("extension")
    stats_ext = extract_extension_by_url(exts, PAYER_STATS_URL)
    if not (stats_ext and isinstance(stats_ext, dict)):
        return result
    sub_exts = stats_ext.get("extension")
    if not isinstance(sub_exts, list):
        return result

    def take(url_key: str) -> Optional[Any]:
        for e in sub_exts:
            if isinstance(e, dict) and e.get("url") == url_key:
                # Prefer decimal if present, else integer
                if "valueDecimal" in e:
                    return e.get("valueDecimal")
                if "valueInteger" in e:
                    return e.get("valueInteger")
        return None

    mapping = {
        "Amount_Covered": "amountCovered",
        "Amount_Uncovered": "amountUncovered",
        "Revenue": "revenue",
        "Covered_Encounters": "coveredEncounters",
        "Uncovered_Encounters": "uncoveredEncounters",
        "Covered_Medications": "coveredMedications",
        "Uncovered_Medications": "uncoveredMedications",
        "Covered_Procedures": "coveredProcedures",
        "Uncovered_Procedures": "uncoveredProcedures",
        "Covered_Immunizations": "coveredImmunizations",
        "Uncovered_Immunizations": "uncoveredImmunizations",
        "Unique_Customers": "uniqueCustomers",
        "QOLS_Avg": "qolsAvg",
        "Member_Months": "memberMonths",
    }

    for csv_key, sub_url in mapping.items():
        val = take(sub_url)
        result[csv_key] = str(val) if val is not None else None

    return result


def filter_none_to_empty(d: Dict[str, Optional[str]]) -> Dict[str, str]:
    return {k: ("" if v is None else str(v)) for k, v in d.items()}


def fhir_organization_to_payer_csv_transform(fhir_org: Dict[str, Any]) -> Dict[str, str]:
    """Transform FHIR Organization into payers.csv row fields."""
    address = _extract_address(fhir_org)
    phone = _extract_phone(fhir_org)
    ownership = _extract_ownership(fhir_org)
    stats = _extract_stats(fhir_org)

    result: Dict[str, Optional[str]] = {
        "Id": fhir_org.get("id"),
        "Name": fhir_org.get("name"),
        "Ownership": ownership,
        "Address": address["Address"],
        "City": address["City"],
        "State_Headquartered": address["State_Headquartered"],
        "Zip": address["Zip"],
        "Phone": phone,
        **stats,
    }
    return filter_none_to_empty(result)


def map_fhir_payer_to_csv(fhir_org: Dict[str, Any]) -> Dict[str, str]:
    """
    Convert FHIR Organization resource to Synthea payers.csv format.

    Args:
        fhir_org: FHIR Organization resource as dictionary

    Returns:
        Synthea CSV payer as dictionary (all string values)
    """
    if not fhir_org or fhir_org.get("resourceType") != "Organization":
        raise ValueError("Input must be a FHIR Organization resource")
    return fhir_organization_to_payer_csv_transform(fhir_org)


