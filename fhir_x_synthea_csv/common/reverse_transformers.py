"""
Common transformation functions for FHIR to Synthea CSV reverse mappings.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import re


def parse_fhir_datetime(fhir_dt: Optional[str]) -> Optional[str]:
    """
    Parse FHIR ISO 8601 datetime to Synthea format.
    
    Args:
        fhir_dt: FHIR datetime string (ISO 8601 format)
        
    Returns:
        Synthea datetime string (YYYY-MM-DD HH:MM:SS) or None
    """
    if not fhir_dt:
        return None
    
    try:
        # Parse various FHIR datetime formats
        # Full: 2024-01-15T10:30:00+00:00
        # Date only: 2024-01-15
        # With timezone: 2024-01-15T10:30:00Z
        
        # Remove timezone info for parsing
        dt_clean = re.sub(r'[+-]\d{2}:\d{2}$|Z$', '', fhir_dt)
        
        if 'T' in dt_clean:
            # Has time component
            dt = datetime.fromisoformat(dt_clean)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Date only
            dt = datetime.fromisoformat(dt_clean)
            return dt.strftime("%Y-%m-%d")
            
    except (ValueError, TypeError):
        return None


def parse_fhir_date(fhir_date: Optional[str]) -> Optional[str]:
    """
    Parse FHIR date to Synthea date format.
    
    Args:
        fhir_date: FHIR date string (YYYY-MM-DD)
        
    Returns:
        Synthea date string (YYYY-MM-DD) or None
    """
    if not fhir_date:
        return None
    
    try:
        # FHIR dates are already in YYYY-MM-DD format
        dt = datetime.fromisoformat(fhir_date)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def extract_reference_id(reference: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Extract resource ID from FHIR reference.
    
    Args:
        reference: FHIR reference object {"reference": "ResourceType/id"}
        
    Returns:
        The resource ID or None
    """
    if not reference or not isinstance(reference, dict):
        return None
    
    ref_str = reference.get("reference")
    if not ref_str:
        return None
    
    # Extract ID from "ResourceType/id" format
    if "/" in ref_str:
        return ref_str.split("/")[-1]
    
    return ref_str


def extract_identifier_by_type(
    identifiers: List[Dict[str, Any]], 
    type_code: str
) -> Optional[str]:
    """
    Extract identifier value by type code.
    
    Args:
        identifiers: List of FHIR identifier objects
        type_code: Type code to search for (e.g., "SS", "DL", "PPN")
        
    Returns:
        Identifier value or None
    """
    if not identifiers:
        return None
    
    for identifier in identifiers:
        if not isinstance(identifier, dict):
            continue
            
        id_type = identifier.get("type")
        if not id_type or not isinstance(id_type, dict):
            continue
            
        coding = id_type.get("coding")
        if not coding or not isinstance(coding, list):
            continue
            
        for code in coding:
            if isinstance(code, dict) and code.get("code") == type_code:
                return identifier.get("value")
    
    return None


def extract_coding_by_system(
    codeable_concept: Optional[Dict[str, Any]], 
    system: str
) -> Optional[Dict[str, Any]]:
    """
    Extract coding from CodeableConcept by system.
    
    Args:
        codeable_concept: FHIR CodeableConcept
        system: System URL to search for
        
    Returns:
        Coding object or None
    """
    if not codeable_concept or not isinstance(codeable_concept, dict):
        return None
    
    coding_list = codeable_concept.get("coding")
    if not coding_list or not isinstance(coding_list, list):
        return None
    
    for coding in coding_list:
        if isinstance(coding, dict) and coding.get("system") == system:
            return coding
    
    return None


def extract_extension_by_url(
    extensions: Optional[List[Dict[str, Any]]], 
    url: str
) -> Optional[Dict[str, Any]]:
    """
    Extract extension by URL.
    
    Args:
        extensions: List of FHIR extension objects
        url: Extension URL to search for
        
    Returns:
        Extension object or None
    """
    if not extensions or not isinstance(extensions, list):
        return None
    
    for ext in extensions:
        if isinstance(ext, dict) and ext.get("url") == url:
            return ext
    
    return None


def extract_us_core_race(extensions: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """
    Extract race from US Core race extension.
    
    Args:
        extensions: List of FHIR extensions
        
    Returns:
        Race string (lowercase) or None
    """
    race_ext = extract_extension_by_url(
        extensions, 
        "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
    )
    
    if not race_ext:
        return None
    
    # Look for ombCategory extension within race extension
    race_extensions = race_ext.get("extension", [])
    for ext in race_extensions:
        if isinstance(ext, dict) and ext.get("url") == "ombCategory":
            coding = ext.get("valueCoding")
            if isinstance(coding, dict):
                code = coding.get("code")
                # Map OMB codes back to Synthea values
                race_code_map = {
                    "2106-3": "white",
                    "2054-5": "black", 
                    "2028-9": "asian",
                    "1002-5": "native",
                    "2076-8": "hawaiian",
                    "2131-1": "other",
                }
                return race_code_map.get(code)
    
    return None


def extract_us_core_ethnicity(extensions: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """
    Extract ethnicity from US Core ethnicity extension.
    
    Args:
        extensions: List of FHIR extensions
        
    Returns:
        Ethnicity string (lowercase) or None
    """
    ethnicity_ext = extract_extension_by_url(
        extensions,
        "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
    )
    
    if not ethnicity_ext:
        return None
    
    # Look for ombCategory extension within ethnicity extension
    ethnicity_extensions = ethnicity_ext.get("extension", [])
    for ext in ethnicity_extensions:
        if isinstance(ext, dict) and ext.get("url") == "ombCategory":
            coding = ext.get("valueCoding")
            if isinstance(coding, dict):
                code = coding.get("code")
                # Map OMB codes back to Synthea values
                ethnicity_code_map = {
                    "2135-2": "hispanic",
                    "2186-5": "nonhispanic",
                }
                return ethnicity_code_map.get(code)
    
    return None


def extract_birthplace(extensions: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """
    Extract birthplace from patient-birthPlace extension.
    
    Args:
        extensions: List of FHIR extensions
        
    Returns:
        Birthplace string or None
    """
    birthplace_ext = extract_extension_by_url(
        extensions,
        "http://hl7.org/fhir/StructureDefinition/patient-birthPlace"
    )
    
    if not birthplace_ext:
        return None
    
    value_address = birthplace_ext.get("valueAddress")
    if isinstance(value_address, dict):
        return value_address.get("text")
    
    return None


def extract_geolocation(address: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """
    Extract latitude and longitude from address geolocation extension.
    
    Args:
        address: FHIR Address object
        
    Returns:
        Tuple of (latitude, longitude) strings or (None, None)
    """
    if not isinstance(address, dict):
        return None, None
    
    extensions = address.get("extension")
    geo_ext = extract_extension_by_url(
        extensions,
        "http://hl7.org/fhir/StructureDefinition/geolocation"
    )
    
    if not geo_ext:
        return None, None
    
    geo_extensions = geo_ext.get("extension", [])
    lat, lon = None, None
    
    for ext in geo_extensions:
        if isinstance(ext, dict):
            if ext.get("url") == "latitude":
                lat = str(ext.get("valueDecimal"))
            elif ext.get("url") == "longitude":
                lon = str(ext.get("valueDecimal"))
    
    return lat, lon


def safe_get_first(items: Optional[List[Any]]) -> Optional[Any]:
    """
    Safely get the first item from a list.
    
    Args:
        items: List or None
        
    Returns:
        First item or None
    """
    if items and isinstance(items, list) and len(items) > 0:
        return items[0]
    return None


def join_list_items(items: Optional[List[str]], separator: str = " ") -> Optional[str]:
    """
    Join list items into a single string.
    
    Args:
        items: List of strings
        separator: Separator character
        
    Returns:
        Joined string or None
    """
    if not items or not isinstance(items, list):
        return None
    
    valid_items = [str(item) for item in items if item is not None]
    return separator.join(valid_items) if valid_items else None