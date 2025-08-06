"""
Reverse lexicons for FHIR to Synthea CSV mappings.
These provide bidirectional lookup capabilities from the existing lexicons.
"""

from chidian.lexicon import Lexicon
from typing import Any, Dict, Optional

from .lexicons import MappingDict


# Reverse gender mapping (FHIR → Synthea)
gender_reverse_lexicon = Lexicon(
    mappings={
        "male": "M",
        "female": "F", 
        "other": "O",
        "unknown": "U",
    },
    default="U",
)


# Reverse marital status mapping (FHIR CodeableConcept code → Synthea)
marital_status_reverse_mapping = {
    "S": "S",  # Single/Never Married
    "M": "M",  # Married
    "D": "D",  # Divorced
    "W": "W",  # Widowed
}

marital_status_reverse_lexicon = MappingDict(marital_status_reverse_mapping)


# Observation category reverse mapping (FHIR category code → Synthea type)
observation_category_reverse_mapping = {
    "vital-signs": "vital-signs",
    "laboratory": "laboratory", 
    "survey": "survey",
    "social-history": "social-history",
    "imaging": "imaging",
    "procedure": "procedure",
    "exam": "exam",
}

observation_category_reverse_lexicon = MappingDict(
    observation_category_reverse_mapping,
    default="exam"
)


# Clinical status reverse mapping (FHIR → presence of STOP date)
clinical_status_reverse_mapping = {
    "active": None,      # No STOP date
    "resolved": "resolved",  # Has STOP date (actual date extracted elsewhere)
    "inactive": "resolved",
    "remission": None,
    "resolved": "resolved",
}

clinical_status_reverse_lexicon = MappingDict(clinical_status_reverse_mapping)


class ReverseLexiconHelper:
    """
    Helper class for complex reverse mappings that require more logic.
    """
    
    @staticmethod
    def extract_marital_status_from_codeable_concept(
        marital_status: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Extract Synthea marital status code from FHIR CodeableConcept.
        
        Args:
            marital_status: FHIR maritalStatus CodeableConcept
            
        Returns:
            Synthea marital status code (S/M/D/W) or None
        """
        if not marital_status or not isinstance(marital_status, dict):
            return None
        
        coding = marital_status.get("coding")
        if not coding or not isinstance(coding, list):
            return None
        
        # Look for v3-MaritalStatus system codes
        for code_obj in coding:
            if isinstance(code_obj, dict):
                system = code_obj.get("system")
                code = code_obj.get("code")
                
                if (system == "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus" and 
                    code in marital_status_reverse_mapping):
                    return marital_status_reverse_mapping[code]
        
        return None
    
    @staticmethod
    def extract_observation_category_from_codeable_concept(
        categories: Optional[list]
    ) -> Optional[str]:
        """
        Extract Synthea observation category from FHIR category array.
        
        Args:
            categories: List of FHIR category CodeableConcepts
            
        Returns:
            Synthea category string or None
        """
        if not categories or not isinstance(categories, list):
            return None
        
        # Take the first category
        category = categories[0] if categories else None
        if not isinstance(category, dict):
            return None
        
        coding = category.get("coding")
        if not coding or not isinstance(coding, list):
            return None
        
        # Look for observation-category system codes
        for code_obj in coding:
            if isinstance(code_obj, dict):
                system = code_obj.get("system")
                code = code_obj.get("code")
                
                if (system == "http://terminology.hl7.org/CodeSystem/observation-category" and
                    code in observation_category_reverse_mapping):
                    return observation_category_reverse_mapping[code]
        
        return "exam"  # Default fallback
    
    @staticmethod
    def determine_observation_type(fhir_observation: Dict[str, Any]) -> str:
        """
        Determine Synthea observation TYPE from FHIR value[x] element.
        
        Args:
            fhir_observation: FHIR Observation resource
            
        Returns:
            "numeric" or "text"
        """
        # Check for numeric values
        if "valueQuantity" in fhir_observation:
            return "numeric"
        elif "valueInteger" in fhir_observation:
            return "numeric"
        elif "valueDecimal" in fhir_observation:
            return "numeric"
        # Text/string values
        elif "valueString" in fhir_observation:
            return "text"
        elif "valueBoolean" in fhir_observation:
            return "text"  # Synthea treats booleans as text
        elif "valueCodeableConcept" in fhir_observation:
            return "text"
        else:
            return "text"  # Default fallback
    
    @staticmethod
    def extract_value_and_unit(fhir_observation: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """
        Extract VALUE and UNITS from FHIR Observation value[x] element.
        
        Args:
            fhir_observation: FHIR Observation resource
            
        Returns:
            Tuple of (value, units) strings
        """
        # Quantity values
        if "valueQuantity" in fhir_observation:
            quantity = fhir_observation["valueQuantity"]
            if isinstance(quantity, dict):
                value = quantity.get("value")
                unit = quantity.get("unit") or quantity.get("code")
                # Format as integer if it's a whole number, otherwise preserve decimals
                if value is not None:
                    if value == int(value):
                        formatted_value = str(int(value))
                    else:
                        formatted_value = str(value)
                    return formatted_value, unit
                return None, unit
        
        # Integer values
        elif "valueInteger" in fhir_observation:
            value = fhir_observation["valueInteger"]
            return str(int(value)) if value is not None else None, None
        
        # Decimal values  
        elif "valueDecimal" in fhir_observation:
            value = fhir_observation["valueDecimal"]
            # Format as integer if it's a whole number, otherwise as decimal
            if value is not None:
                if value == int(value):
                    return str(int(value)), None
                else:
                    return str(value), None
            return None, None
        
        # String values
        elif "valueString" in fhir_observation:
            return fhir_observation["valueString"], None
        
        # Boolean values
        elif "valueBoolean" in fhir_observation:
            value = fhir_observation["valueBoolean"]
            return "true" if value else "false", None
        
        # CodeableConcept values
        elif "valueCodeableConcept" in fhir_observation:
            concept = fhir_observation["valueCodeableConcept"]
            if isinstance(concept, dict):
                # Try to get display text or code
                text = concept.get("text")
                if text:
                    return text, None
                    
                coding = concept.get("coding")
                if coding and isinstance(coding, list) and len(coding) > 0:
                    display = coding[0].get("display") or coding[0].get("code")
                    return display, None
        
        return None, None


# Export the helper class methods as module-level functions for convenience
extract_marital_status_from_codeable_concept = ReverseLexiconHelper.extract_marital_status_from_codeable_concept
extract_observation_category_from_codeable_concept = ReverseLexiconHelper.extract_observation_category_from_codeable_concept
determine_observation_type = ReverseLexiconHelper.determine_observation_type
extract_value_and_unit = ReverseLexiconHelper.extract_value_and_unit