"""
Reverse mappings from FHIR R4 resources to Synthea CSV format.

This module provides functions to transform FHIR R4 resources back to 
Synthea CSV format, enabling bidirectional semantic data mapping.
"""

from .patient import map_fhir_patient_to_csv
from .observation import map_fhir_observation_to_csv
from .condition import map_fhir_condition_to_csv

__all__ = [
    "map_fhir_patient_to_csv",
    "map_fhir_observation_to_csv", 
    "map_fhir_condition_to_csv",
]