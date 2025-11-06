"""
FHIR x Synthea CSV: Mapping library between FHIR R4 and Synthea CSV formats.

This library demonstrates the use of the chidian mapping framework for
bidirectional semantic data transformations in healthcare.
"""

__version__ = "0.1.0"

from . import fhir_mappers, synthea_csv_mappers

__all__ = ["fhir_mappers", "synthea_csv_mappers"]
