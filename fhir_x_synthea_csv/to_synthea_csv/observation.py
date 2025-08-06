"""
Observation reverse mapper: FHIR R4 Observation resource to Synthea CSV observation.
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
)
from ..common.reverse_lexicons import (
    extract_observation_category_from_codeable_concept,
    determine_observation_type,
    extract_value_and_unit,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def fhir_observation_to_csv_transform(fhir_observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform FHIR Observation resource to Synthea CSV observation format.
    
    Args:
        fhir_observation: FHIR Observation resource as dict
        
    Returns:
        Synthea CSV observation dict
    """
    # Extract basic fields
    observation_id = fhir_observation.get("id")
    
    # Date/time (use effectiveDateTime, fall back to issued)
    date = parse_fhir_datetime(fhir_observation.get("effectiveDateTime"))
    if not date:
        date = parse_fhir_datetime(fhir_observation.get("issued"))
    
    # Patient and encounter references
    patient_ref = fhir_observation.get("subject")
    patient_id = extract_reference_id(patient_ref)
    
    encounter_ref = fhir_observation.get("encounter")
    encounter_id = extract_reference_id(encounter_ref)
    
    # Extract code and description from LOINC coding
    code_concept = fhir_observation.get("code")
    loinc_code = None
    description = None
    
    if code_concept:
        # Look for LOINC coding
        loinc_coding = extract_coding_by_system(code_concept, "http://loinc.org")
        if loinc_coding:
            loinc_code = loinc_coding.get("code")
            description = loinc_coding.get("display")
        
        # Fall back to text or first coding
        if not description:
            description = code_concept.get("text")
        
        if not loinc_code or not description:
            # Use first coding if LOINC not found
            coding_list = code_concept.get("coding", [])
            if coding_list and len(coding_list) > 0:
                first_coding = coding_list[0]
                if not loinc_code:
                    loinc_code = first_coding.get("code")
                if not description:
                    description = first_coding.get("display")
    
    # Extract category
    categories = fhir_observation.get("category", [])
    category = extract_observation_category_from_codeable_concept(categories)
    
    # Extract value and units
    value, units = extract_value_and_unit(fhir_observation)
    
    # Determine type based on value
    obs_type = determine_observation_type(fhir_observation)
    
    # Build Synthea CSV observation
    result = {
        "DATE": date,
        "PATIENT": patient_id,
        "ENCOUNTER": encounter_id,
        "CATEGORY": category,
        "CODE": loinc_code,
        "DESCRIPTION": description,
        "VALUE": value,
        "UNITS": units,
        "TYPE": obs_type,
    }
    
    return filter_none_values(result)


def map_fhir_observation_to_csv(fhir_observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR Observation resource to Synthea CSV observation format.
    
    Args:
        fhir_observation: FHIR Observation resource as dictionary
        
    Returns:
        Synthea CSV observation as dictionary
    """
    if not fhir_observation or fhir_observation.get("resourceType") != "Observation":
        raise ValueError("Input must be a FHIR Observation resource")
    
    return fhir_observation_to_csv_transform(fhir_observation)