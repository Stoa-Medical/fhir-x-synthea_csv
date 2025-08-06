"""
Validation helpers for comparing our mapped FHIR resources with Synthea's FHIR output.
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import re


def normalize_datetime(dt_str: Optional[str]) -> Optional[str]:
    """
    Normalize datetime strings for comparison.
    Handles various formats and extracts just the date/datetime portion.
    """
    if not dt_str:
        return None
    
    # Remove timezone info for comparison
    dt_str = re.sub(r'[+-]\d{2}:\d{2}$', '', dt_str)
    dt_str = re.sub(r'Z$', '', dt_str)
    
    # Normalize to consistent format
    try:
        # Try parsing as datetime
        if 'T' in dt_str:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            # Just a date
            dt = datetime.strptime(dt_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
    except:
        return dt_str


def find_extension(extensions: List[Dict], url: str) -> Optional[Dict]:
    """
    Find an extension in a list by URL.
    
    Args:
        extensions: List of FHIR extensions
        url: Extension URL to search for
        
    Returns:
        Extension dict if found, None otherwise
    """
    if not extensions:
        return None
    
    for ext in extensions:
        if ext.get("url") == url:
            return ext
    
    return None


def compare_extensions(
    our_extensions: List[Dict],
    synthea_extensions: List[Dict],
    required_urls: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Compare extension arrays between our output and Synthea's.
    
    Args:
        our_extensions: Our mapped extensions
        synthea_extensions: Synthea's FHIR extensions
        required_urls: Set of extension URLs that must match
        
    Returns:
        Comparison result with matches and mismatches
    """
    result = {
        "match": True,
        "matches": [],
        "mismatches": [],
        "missing_in_ours": [],
        "extra_in_ours": []
    }
    
    our_extensions = our_extensions or []
    synthea_extensions = synthea_extensions or []
    
    # URLs to check
    if required_urls:
        urls_to_check = required_urls
    else:
        # Check all URLs from both sides
        our_urls = {ext.get("url") for ext in our_extensions}
        synthea_urls = {ext.get("url") for ext in synthea_extensions}
        urls_to_check = our_urls | synthea_urls
    
    for url in urls_to_check:
        our_ext = find_extension(our_extensions, url)
        synthea_ext = find_extension(synthea_extensions, url)
        
        if our_ext and synthea_ext:
            # Compare the extensions
            if compare_extension_values(our_ext, synthea_ext):
                result["matches"].append(url)
            else:
                result["mismatches"].append({
                    "url": url,
                    "ours": our_ext,
                    "synthea": synthea_ext
                })
                result["match"] = False
        elif synthea_ext and not our_ext:
            result["missing_in_ours"].append(url)
            # Only fail if this was a required URL
            if required_urls and url in required_urls:
                result["match"] = False
        elif our_ext and not synthea_ext:
            result["extra_in_ours"].append(url)
            # Extra extensions are generally OK
    
    return result


def compare_extension_values(ext1: Dict, ext2: Dict) -> bool:
    """
    Compare the values of two extensions.
    
    Args:
        ext1: First extension
        ext2: Second extension
        
    Returns:
        True if extensions match semantically
    """
    # Check URL matches
    if ext1.get("url") != ext2.get("url"):
        return False
    
    # For nested extensions (like US Core race/ethnicity)
    if "extension" in ext1 and "extension" in ext2:
        return compare_nested_extensions(ext1["extension"], ext2["extension"])
    
    # For simple value extensions
    for key in ext1.keys():
        if key.startswith("value"):
            if key not in ext2:
                return False
            
            # Special handling for different value types
            if key == "valueAddress":
                return compare_addresses(ext1[key], ext2[key])
            elif key == "valueCoding":
                return compare_codings(ext1[key], ext2[key])
            else:
                return ext1[key] == ext2[key]
    
    return True


def compare_nested_extensions(exts1: List[Dict], exts2: List[Dict]) -> bool:
    """Compare nested extension arrays."""
    if len(exts1) != len(exts2):
        return False
    
    # Match extensions by URL
    for ext1 in exts1:
        url = ext1.get("url")
        ext2 = find_extension(exts2, url)
        if not ext2:
            return False
        if not compare_extension_values(ext1, ext2):
            return False
    
    return True


def compare_identifiers(
    our_identifiers: List[Dict],
    synthea_identifiers: List[Dict]
) -> Dict[str, Any]:
    """
    Compare identifier arrays.
    
    Args:
        our_identifiers: Our mapped identifiers
        synthea_identifiers: Synthea's identifiers
        
    Returns:
        Comparison result
    """
    result = {
        "match": True,
        "matches": [],
        "mismatches": []
    }
    
    our_identifiers = our_identifiers or []
    synthea_identifiers = synthea_identifiers or []
    
    # Match identifiers by system
    for our_id in our_identifiers:
        system = our_id.get("system")
        synthea_id = None
        
        for s_id in synthea_identifiers:
            if s_id.get("system") == system:
                synthea_id = s_id
                break
        
        if synthea_id:
            if our_id.get("value") == synthea_id.get("value"):
                result["matches"].append(system)
            else:
                result["mismatches"].append({
                    "system": system,
                    "our_value": our_id.get("value"),
                    "synthea_value": synthea_id.get("value")
                })
                result["match"] = False
    
    return result


def compare_codings(coding1: Dict, coding2: Dict) -> bool:
    """Compare two coding objects."""
    return (
        coding1.get("system") == coding2.get("system") and
        coding1.get("code") == coding2.get("code")
    )


def compare_codeableconcepts(cc1: Dict, cc2: Dict) -> bool:
    """Compare two CodeableConcept objects."""
    # Compare primary coding
    if "coding" in cc1 and "coding" in cc2:
        codings1 = cc1["coding"]
        codings2 = cc2["coding"]
        
        if len(codings1) > 0 and len(codings2) > 0:
            # Compare first/primary coding
            return compare_codings(codings1[0], codings2[0])
    
    return False


def compare_addresses(addr1: Dict, addr2: Dict) -> bool:
    """Compare two address objects."""
    # Compare key fields
    fields = ["city", "state", "postalCode", "country"]
    for field in fields:
        if addr1.get(field) != addr2.get(field):
            return False
    
    # Compare line arrays if present
    if "line" in addr1 and "line" in addr2:
        return addr1["line"] == addr2["line"]
    
    # Compare text representation if present
    if "text" in addr1 and "text" in addr2:
        return addr1["text"] == addr2["text"]
    
    return True


def compare_human_names(name1: Dict, name2: Dict) -> bool:
    """Compare two HumanName objects."""
    # Compare use
    if name1.get("use") != name2.get("use"):
        return False
    
    # Compare family name
    if name1.get("family") != name2.get("family"):
        return False
    
    # Compare given names
    given1 = name1.get("given", [])
    given2 = name2.get("given", [])
    if given1 != given2:
        return False
    
    # Compare prefix/suffix if present
    if name1.get("prefix") != name2.get("prefix"):
        return False
    if name1.get("suffix") != name2.get("suffix"):
        return False
    
    return True


def assert_patient_equivalence(
    our_patient: Dict[str, Any],
    synthea_patient: Dict[str, Any],
    strict: bool = False
) -> Dict[str, Any]:
    """
    Compare our mapped Patient resource with Synthea's.
    
    Args:
        our_patient: Our mapped Patient resource
        synthea_patient: Synthea's Patient resource
        strict: If True, require exact matches; if False, allow semantic equivalence
        
    Returns:
        Validation result dictionary
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "matches": []
    }
    
    # Check resource type
    if our_patient.get("resourceType") != "Patient":
        result["errors"].append("Our resource is not a Patient")
        result["valid"] = False
    
    if synthea_patient.get("resourceType") != "Patient":
        result["errors"].append("Synthea resource is not a Patient")
        result["valid"] = False
    
    # Compare core demographics
    fields_to_compare = [
        ("id", "Patient ID"),
        ("gender", "Gender"),
        ("birthDate", "Birth Date")
    ]
    
    for field, description in fields_to_compare:
        our_value = our_patient.get(field)
        synthea_value = synthea_patient.get(field)
        
        if field == "birthDate":
            # Normalize date format
            our_value = normalize_datetime(our_value)
            synthea_value = normalize_datetime(synthea_value)
        
        if our_value == synthea_value:
            result["matches"].append(f"{description}: {our_value}")
        else:
            result["errors"].append(
                f"{description} mismatch: ours={our_value}, synthea={synthea_value}"
            )
            result["valid"] = False
    
    # Compare names
    our_names = our_patient.get("name", [])
    synthea_names = synthea_patient.get("name", [])
    
    if our_names and synthea_names:
        # Compare primary/first name
        if not compare_human_names(our_names[0], synthea_names[0]):
            result["warnings"].append("Name structure differs")
    
    # Compare marital status
    our_marital = our_patient.get("maritalStatus")
    synthea_marital = synthea_patient.get("maritalStatus")
    
    if our_marital and synthea_marital:
        if not compare_codeableconcepts(our_marital, synthea_marital):
            result["warnings"].append("Marital status coding differs")
    
    # Compare extensions (race, ethnicity)
    ext_comparison = compare_extensions(
        our_patient.get("extension", []),
        synthea_patient.get("extension", []),
        required_urls={
            "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
            "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
        }
    )
    
    if not ext_comparison["match"]:
        result["warnings"].append(f"Extension differences: {ext_comparison}")
    
    # Compare identifiers
    id_comparison = compare_identifiers(
        our_patient.get("identifier", []),
        synthea_patient.get("identifier", [])
    )
    
    if not id_comparison["match"]:
        result["warnings"].append(f"Identifier differences: {id_comparison}")
    
    return result


def assert_observation_equivalence(
    our_observation: Dict[str, Any],
    synthea_observation: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare our mapped Observation resource with Synthea's.
    
    Args:
        our_observation: Our mapped Observation resource
        synthea_observation: Synthea's Observation resource
        
    Returns:
        Validation result dictionary
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "matches": []
    }
    
    # Check resource type
    if our_observation.get("resourceType") != "Observation":
        result["errors"].append("Our resource is not an Observation")
        result["valid"] = False
        return result
    
    # Compare status
    if our_observation.get("status") != synthea_observation.get("status"):
        result["errors"].append(
            f"Status mismatch: {our_observation.get('status')} vs "
            f"{synthea_observation.get('status')}"
        )
        result["valid"] = False
    
    # Compare code (LOINC)
    our_code = our_observation.get("code", {})
    synthea_code = synthea_observation.get("code", {})
    
    if not compare_codeableconcepts(our_code, synthea_code):
        result["errors"].append("Observation code mismatch")
        result["valid"] = False
    else:
        result["matches"].append(f"Code: {our_code.get('coding', [{}])[0].get('code')}")
    
    # Compare value
    our_value = extract_observation_value(our_observation)
    synthea_value = extract_observation_value(synthea_observation)
    
    if our_value != synthea_value:
        # Allow small floating point differences
        if isinstance(our_value, (int, float)) and isinstance(synthea_value, (int, float)):
            if abs(our_value - synthea_value) > 0.01:
                result["errors"].append(
                    f"Value mismatch: {our_value} vs {synthea_value}"
                )
                result["valid"] = False
            else:
                result["matches"].append(f"Value: {our_value} (approx)")
        else:
            result["errors"].append(
                f"Value mismatch: {our_value} vs {synthea_value}"
            )
            result["valid"] = False
    else:
        result["matches"].append(f"Value: {our_value}")
    
    # Compare effectiveDateTime
    our_dt = normalize_datetime(our_observation.get("effectiveDateTime"))
    synthea_dt = normalize_datetime(synthea_observation.get("effectiveDateTime"))
    
    if our_dt != synthea_dt:
        result["warnings"].append(
            f"DateTime mismatch: {our_dt} vs {synthea_dt}"
        )
    
    return result


def extract_observation_value(observation: Dict) -> Any:
    """Extract the value from an Observation resource."""
    # Check for different value types
    if "valueQuantity" in observation:
        return observation["valueQuantity"].get("value")
    elif "valueString" in observation:
        return observation["valueString"]
    elif "valueBoolean" in observation:
        return observation["valueBoolean"]
    elif "valueCodeableConcept" in observation:
        codings = observation["valueCodeableConcept"].get("coding", [])
        if codings:
            return codings[0].get("code")
    
    return None


def assert_condition_equivalence(
    our_condition: Dict[str, Any],
    synthea_condition: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare our mapped Condition resource with Synthea's.
    
    Args:
        our_condition: Our mapped Condition resource
        synthea_condition: Synthea's Condition resource
        
    Returns:
        Validation result dictionary
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "matches": []
    }
    
    # Check resource type
    if our_condition.get("resourceType") != "Condition":
        result["errors"].append("Our resource is not a Condition")
        result["valid"] = False
        return result
    
    # Compare clinical status
    our_clinical = our_condition.get("clinicalStatus", {})
    synthea_clinical = synthea_condition.get("clinicalStatus", {})
    
    if not compare_codeableconcepts(our_clinical, synthea_clinical):
        result["errors"].append("Clinical status mismatch")
        result["valid"] = False
    else:
        result["matches"].append(
            f"Clinical status: {our_clinical.get('coding', [{}])[0].get('code')}"
        )
    
    # Compare code (SNOMED)
    our_code = our_condition.get("code", {})
    synthea_code = synthea_condition.get("code", {})
    
    if not compare_codeableconcepts(our_code, synthea_code):
        result["errors"].append("Condition code mismatch")
        result["valid"] = False
    else:
        result["matches"].append(
            f"SNOMED: {our_code.get('coding', [{}])[0].get('code')}"
        )
    
    # Compare onset
    our_onset = normalize_datetime(our_condition.get("onsetDateTime"))
    synthea_onset = normalize_datetime(synthea_condition.get("onsetDateTime"))
    
    if our_onset != synthea_onset:
        result["errors"].append(
            f"Onset mismatch: {our_onset} vs {synthea_onset}"
        )
        result["valid"] = False
    else:
        result["matches"].append(f"Onset: {our_onset}")
    
    # Compare abatement if present
    if "abatementDateTime" in our_condition or "abatementDateTime" in synthea_condition:
        our_abate = normalize_datetime(our_condition.get("abatementDateTime"))
        synthea_abate = normalize_datetime(synthea_condition.get("abatementDateTime"))
        
        if our_abate != synthea_abate:
            result["warnings"].append(
                f"Abatement mismatch: {our_abate} vs {synthea_abate}"
            )
    
    return result