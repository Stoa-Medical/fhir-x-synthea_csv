"""
Condition reverse mapper: FHIR R4 Condition resource to Synthea CSV condition.
"""

from typing import Any, Dict, Optional

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict, but keep empty strings.""" 
    return {k: (v if v is not None else "") for k, v in d.items()}


def _is_condition_resolved(fhir_condition: Dict[str, Any]) -> bool:
    """
    Check if condition is resolved based on clinical status.
    
    Args:
        fhir_condition: FHIR Condition resource
        
    Returns:
        True if condition is resolved, False otherwise
    """
    clinical_status = fhir_condition.get("clinicalStatus")
    if not clinical_status or not isinstance(clinical_status, dict):
        return False
    
    coding_list = clinical_status.get("coding", [])
    for coding in coding_list:
        if isinstance(coding, dict):
            code = coding.get("code")
            system = coding.get("system")
            
            # Check for resolved/inactive status
            if (system == "http://terminology.hl7.org/CodeSystem/condition-clinical" and
                code in ["resolved", "inactive", "remission"]):
                return True
    
    return False


def fhir_condition_to_csv_transform(fhir_condition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform FHIR Condition resource to Synthea CSV condition format.
    
    Args:
        fhir_condition: FHIR Condition resource as dict
        
    Returns:
        Synthea CSV condition dict
    """
    # Extract basic fields
    condition_id = fhir_condition.get("id")
    
    # Start date from onsetDateTime
    start_date = parse_fhir_datetime(fhir_condition.get("onsetDateTime"))
    
    # Stop date - check both abatementDateTime and clinical status
    stop_date = None
    explicit_stop = parse_fhir_datetime(fhir_condition.get("abatementDateTime"))
    
    if explicit_stop:
        stop_date = explicit_stop
    elif _is_condition_resolved(fhir_condition):
        # If resolved but no explicit date, we could set a placeholder
        # For now, leave empty as Synthea CSV allows empty STOP dates
        stop_date = ""
    
    # Patient and encounter references
    patient_ref = fhir_condition.get("subject")
    patient_id = extract_reference_id(patient_ref)
    
    encounter_ref = fhir_condition.get("encounter")
    encounter_id = extract_reference_id(encounter_ref)
    
    # Extract SNOMED code and description
    code_concept = fhir_condition.get("code")
    snomed_code = None
    description = None
    system = "http://snomed.info/sct"  # Default for conditions
    
    if code_concept:
        # Look for SNOMED CT coding
        snomed_coding = extract_coding_by_system(code_concept, "http://snomed.info/sct")
        if snomed_coding:
            snomed_code = snomed_coding.get("code")
            description = snomed_coding.get("display")
            system = "http://snomed.info/sct"
        else:
            # Fall back to first coding system and code
            coding_list = code_concept.get("coding", [])
            if coding_list and len(coding_list) > 0:
                first_coding = coding_list[0]
                snomed_code = first_coding.get("code")
                description = first_coding.get("display")
                system = first_coding.get("system", "http://snomed.info/sct")
        
        # Fall back to text if no description
        if not description:
            description = code_concept.get("text")
    
    # Build Synthea CSV condition
    result = {
        "START": start_date,
        "STOP": stop_date, 
        "PATIENT": patient_id,
        "ENCOUNTER": encounter_id,
        "SYSTEM": system,
        "CODE": snomed_code,
        "DESCRIPTION": description,
    }
    
    return filter_none_values(result)


def map_fhir_condition_to_csv(fhir_condition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR Condition resource to Synthea CSV condition format.
    
    Args:
        fhir_condition: FHIR Condition resource as dictionary
        
    Returns:
        Synthea CSV condition as dictionary
    """
    if not fhir_condition or fhir_condition.get("resourceType") != "Condition":
        raise ValueError("Input must be a FHIR Condition resource")
    
    return fhir_condition_to_csv_transform(fhir_condition)