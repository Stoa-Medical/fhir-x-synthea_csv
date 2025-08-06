"""
Patient mapper: Synthea CSV to FHIR R4 Patient resource.
"""

from typing import Any, Dict, Optional

from ..common.transformers import (
    create_identifier,
    create_reference,
    to_fhir_date,
    to_fhir_datetime,
)
from ..common.lexicons import (
    gender_lexicon,
    marital_status_lexicon,
    race_lexicon,
    ethnicity_lexicon,
)


def _build_name(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build FHIR HumanName from Synthea patient data."""
    name = {"use": "official"}
    
    # Add name components if present
    if prefix := src.get("PREFIX"):
        name["prefix"] = [prefix]
    
    if first := src.get("FIRST"):
        name["given"] = [first]
    
    if last := src.get("LAST"):
        name["family"] = last
    
    if suffix := src.get("SUFFIX"):
        name["suffix"] = [suffix]
    
    # Only return name if it has content
    return name if len(name) > 1 else None


def _build_maiden_name(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build maiden name entry if present."""
    if maiden := src.get("MAIDEN"):
        return {
            "use": "maiden",
            "family": maiden,
        }
    return None


def _build_address(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build FHIR Address from Synthea patient data."""
    address = {"use": "home"}
    
    if street := src.get("ADDRESS"):
        address["line"] = [street]
    
    if city := src.get("CITY"):
        address["city"] = city
    
    if state := src.get("STATE"):
        address["state"] = state
    
    if county := src.get("COUNTY"):
        address["district"] = county
    
    if zip_code := src.get("ZIP"):
        address["postalCode"] = zip_code
    
    # Add geolocation extension if coordinates present
    extensions = []
    if lat := src.get("LAT"):
        if lon := src.get("LON"):
            extensions.append({
                "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                "extension": [
                    {"url": "latitude", "valueDecimal": float(lat)},
                    {"url": "longitude", "valueDecimal": float(lon)},
                ],
            })
    
    if extensions:
        address["extension"] = extensions
    
    return address if len(address) > 1 else None


def _build_identifiers(src: Dict[str, Any]) -> list:
    """Build list of patient identifiers."""
    identifiers = []
    
    # Medical Record Number (using patient ID)
    if patient_id := src.get("Id"):
        identifiers.append(
            create_identifier(
                system="urn:oid:2.16.840.1.113883.19.5",
                value=patient_id,
                use="official",
                type_code="MR",
            )
        )
    
    # Social Security Number
    if ssn := src.get("SSN"):
        identifiers.append(
            create_identifier(
                system="http://hl7.org/fhir/sid/us-ssn",
                value=ssn,
                type_code="SS",
            )
        )
    
    # Driver's License
    if drivers := src.get("DRIVERS"):
        identifiers.append(
            create_identifier(
                system="urn:oid:2.16.840.1.113883.4.3.25",  # Example OID for state DL
                value=drivers,
                type_code="DL",
            )
        )
    
    # Passport
    if passport := src.get("PASSPORT"):
        identifiers.append(
            create_identifier(
                system="http://hl7.org/fhir/sid/passport-USA",
                value=passport,
                type_code="PPN",
            )
        )
    
    return identifiers


def _build_extensions(src: Dict[str, Any]) -> list:
    """Build patient extensions (race, ethnicity, birthplace)."""
    extensions = []
    
    # US Core Race
    if race := src.get("RACE"):
        race_ext = race_lexicon.forward_get(race.lower())
        if race_ext:
            extensions.append(race_ext)
    
    # US Core Ethnicity
    if ethnicity := src.get("ETHNICITY"):
        ethnicity_ext = ethnicity_lexicon.forward_get(ethnicity.lower())
        if ethnicity_ext:
            extensions.append(ethnicity_ext)
    
    # Birth Place
    if birthplace := src.get("BIRTHPLACE"):
        extensions.append({
            "url": "http://hl7.org/fhir/StructureDefinition/patient-birthPlace",
            "valueAddress": {"text": birthplace},
        })
    
    return extensions


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict."""
    return {k: v for k, v in d.items() if v is not None and v != [] and v != ""}


def patient_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Synthea patient to FHIR Patient."""
    result = {
        "resourceType": "Patient",
        "id": src.get("Id"),
        "identifier": _build_identifiers(src),
        "name": [n for n in [_build_name(src), _build_maiden_name(src)] if n],
        "gender": gender_lexicon.get(src.get("GENDER")) if src.get("GENDER") else None,
        "birthDate": to_fhir_date(src.get("BIRTHDATE")),
        "deceasedDateTime": to_fhir_datetime(src.get("DEATHDATE")) if src.get("DEATHDATE") else None,
        "address": [a for a in [_build_address(src)] if a],
        "maritalStatus": marital_status_lexicon.forward_get(src.get("MARITAL")) if src.get("MARITAL") else None,
        "extension": _build_extensions(src),
    }
    
    return filter_none_values(result)


# Since chidian API is different than expected, let's just use the function directly
# The chidian framework expects field-level transformations, not full object transforms

# For now, we'll use our simple transform function
# In a future version, we could refactor to use chidian's field-mapping approach


def map_patient(synthea_patient: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea CSV patient to FHIR Patient resource.
    
    Args:
        synthea_patient: Dictionary with Synthea patient CSV fields
        
    Returns:
        FHIR Patient resource as dictionary
    """
    return patient_transform(synthea_patient)