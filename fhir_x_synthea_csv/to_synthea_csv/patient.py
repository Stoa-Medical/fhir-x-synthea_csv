"""
Patient reverse mapper: FHIR R4 Patient resource to Synthea CSV patient.
"""

from typing import Any, Dict, Optional
from datetime import datetime

from ..common.reverse_transformers import (
    parse_fhir_date,
    parse_fhir_datetime,
    extract_reference_id,
    extract_identifier_by_type,
    extract_us_core_race,
    extract_us_core_ethnicity,
    extract_birthplace,
    extract_geolocation,
    safe_get_first,
    join_list_items,
)
from ..common.reverse_lexicons import (
    gender_reverse_lexicon,
    extract_marital_status_from_codeable_concept,
)


def _extract_name_components(names: Optional[list]) -> Dict[str, Optional[str]]:
    """
    Extract name components from FHIR HumanName array.
    
    Args:
        names: List of FHIR HumanName objects
        
    Returns:
        Dict with PREFIX, FIRST, MIDDLE, LAST, SUFFIX, MAIDEN keys
    """
    result = {
        "PREFIX": None,
        "FIRST": None,
        "MIDDLE": None,  
        "LAST": None,
        "SUFFIX": None,
        "MAIDEN": None,
    }
    
    if not names or not isinstance(names, list):
        return result
    
    # Find official name first, fall back to first name
    official_name = None
    maiden_name = None
    
    for name in names:
        if not isinstance(name, dict):
            continue
            
        use = name.get("use")
        if use == "official" and not official_name:
            official_name = name
        elif use == "maiden":
            maiden_name = name
    
    # Use first name if no official name found
    if not official_name and names:
        official_name = names[0]
    
    # Extract from official name
    if official_name:
        # Prefix (Mr., Mrs., Dr., etc.)
        prefix_list = official_name.get("prefix")
        if prefix_list:
            result["PREFIX"] = safe_get_first(prefix_list)
        
        # Given names (first, middle)
        given_list = official_name.get("given")
        if given_list and isinstance(given_list, list):
            if len(given_list) >= 1:
                result["FIRST"] = given_list[0]
            if len(given_list) >= 2:
                result["MIDDLE"] = given_list[1]
        
        # Family name
        result["LAST"] = official_name.get("family")
        
        # Suffix (Jr., Sr., PhD, etc.)
        suffix_list = official_name.get("suffix")
        if suffix_list:
            result["SUFFIX"] = safe_get_first(suffix_list)
    
    # Extract maiden name
    if maiden_name:
        result["MAIDEN"] = maiden_name.get("family")
    
    return result


def _extract_address_components(addresses: Optional[list]) -> Dict[str, Optional[str]]:
    """
    Extract address components from FHIR Address array.
    
    Args:
        addresses: List of FHIR Address objects
        
    Returns:
        Dict with ADDRESS, CITY, STATE, COUNTY, ZIP, LAT, LON keys
    """
    result = {
        "ADDRESS": None,
        "CITY": None,
        "STATE": None,
        "COUNTY": None,
        "ZIP": None,
        "LAT": None,
        "LON": None,
    }
    
    if not addresses or not isinstance(addresses, list):
        return result
    
    # Find home address first, fall back to first address
    home_address = None
    for addr in addresses:
        if isinstance(addr, dict):
            if addr.get("use") == "home":
                home_address = addr
                break
    
    if not home_address and addresses:
        home_address = addresses[0]
    
    if not home_address:
        return result
    
    # Extract address components
    line_list = home_address.get("line")
    if line_list:
        result["ADDRESS"] = safe_get_first(line_list)
    
    result["CITY"] = home_address.get("city")
    result["STATE"] = home_address.get("state") 
    result["COUNTY"] = home_address.get("district")  # FHIR uses district for county
    result["ZIP"] = home_address.get("postalCode")
    
    # Extract geolocation from extension
    lat, lon = extract_geolocation(home_address)
    result["LAT"] = lat
    result["LON"] = lon
    
    return result


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def fhir_patient_to_csv_transform(fhir_patient: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform FHIR Patient resource to Synthea CSV patient format.
    
    Args:
        fhir_patient: FHIR Patient resource as dict
        
    Returns:
        Synthea CSV patient dict
    """
    # Basic patient ID
    patient_id = fhir_patient.get("id")
    
    # Extract name components
    names = fhir_patient.get("name", [])
    name_components = _extract_name_components(names)
    
    # Extract identifiers
    identifiers = fhir_patient.get("identifier", [])
    ssn = extract_identifier_by_type(identifiers, "SS")
    drivers = extract_identifier_by_type(identifiers, "DL") 
    passport = extract_identifier_by_type(identifiers, "PPN")
    
    # Demographics
    gender = gender_reverse_lexicon.get(fhir_patient.get("gender"))
    birth_date = parse_fhir_date(fhir_patient.get("birthDate"))
    death_date = parse_fhir_datetime(fhir_patient.get("deceasedDateTime"))
    
    # Marital status
    marital_status = extract_marital_status_from_codeable_concept(
        fhir_patient.get("maritalStatus")
    )
    
    # Extensions (race, ethnicity, birthplace)
    extensions = fhir_patient.get("extension", [])
    race = extract_us_core_race(extensions)
    ethnicity = extract_us_core_ethnicity(extensions)
    birthplace = extract_birthplace(extensions)
    
    # Address components
    addresses = fhir_patient.get("address", [])
    address_components = _extract_address_components(addresses)
    
    # Build Synthea CSV patient
    result = {
        "Id": patient_id,
        "BIRTHDATE": birth_date,
        "DEATHDATE": death_date,
        "SSN": ssn,
        "DRIVERS": drivers,
        "PASSPORT": passport,
        "PREFIX": name_components["PREFIX"],
        "FIRST": name_components["FIRST"],
        "MIDDLE": name_components["MIDDLE"],
        "LAST": name_components["LAST"],
        "SUFFIX": name_components["SUFFIX"],
        "MAIDEN": name_components["MAIDEN"],
        "MARITAL": marital_status,
        "RACE": race,
        "ETHNICITY": ethnicity,
        "GENDER": gender,
        "BIRTHPLACE": birthplace,
        "ADDRESS": address_components["ADDRESS"],
        "CITY": address_components["CITY"],
        "STATE": address_components["STATE"],
        "COUNTY": address_components["COUNTY"],
        "ZIP": address_components["ZIP"],
        "LAT": address_components["LAT"],
        "LON": address_components["LON"],
    }
    
    return filter_none_values(result)


def map_fhir_patient_to_csv(fhir_patient: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR Patient resource to Synthea CSV patient format.
    
    Args:
        fhir_patient: FHIR Patient resource as dictionary
        
    Returns:
        Synthea CSV patient as dictionary
    """
    if not fhir_patient or fhir_patient.get("resourceType") != "Patient":
        raise ValueError("Input must be a FHIR Patient resource")
    
    return fhir_patient_to_csv_transform(fhir_patient)