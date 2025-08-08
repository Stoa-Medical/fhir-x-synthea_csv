"""
Reverse mappings from FHIR R4 resources to Synthea CSV format.

This module provides functions to transform FHIR R4 resources back to 
Synthea CSV format, enabling bidirectional semantic data mapping.
"""

from .patient import map_fhir_patient_to_csv
from .observation import map_fhir_observation_to_csv
from .condition import map_fhir_condition_to_csv
from .supply import map_fhir_supply_to_csv
from .careplan import map_fhir_careplan_to_csv
from .allergy import map_fhir_allergy_to_csv
from .claim import map_fhir_claim_to_claims_row
from .claims_transactions import (
    map_fhir_claim_to_claims_transactions,
    map_fhir_claimresponse_to_claims_transaction,
)
from .encounter import map_fhir_encounter_to_csv
from .device import map_fhir_device_to_csv
from .immunization import map_fhir_immunization_to_csv
from .medication import map_fhir_medication_request_to_csv
from .organization import map_fhir_organization_to_csv
from .payer_transitions import map_fhir_coverage_to_payer_transition
from .payer import map_fhir_payer_to_csv
from .procedure import map_fhir_procedure_to_csv
from .provider import map_fhir_provider_to_csv

__all__ = [
    "map_fhir_patient_to_csv",
    "map_fhir_observation_to_csv", 
    "map_fhir_condition_to_csv",
    "map_fhir_supply_to_csv",
    "map_fhir_careplan_to_csv",
    "map_fhir_allergy_to_csv",
    "map_fhir_claim_to_claims_row",
    "map_fhir_claim_to_claims_transactions",
    "map_fhir_claimresponse_to_claims_transaction",
    "map_fhir_encounter_to_csv",
    "map_fhir_device_to_csv",
    "map_fhir_immunization_to_csv",
    "map_fhir_medication_request_to_csv",
    "map_fhir_organization_to_csv",
    "map_fhir_coverage_to_payer_transition",
    "map_fhir_payer_to_csv",
    "map_fhir_procedure_to_csv",
    "map_fhir_provider_to_csv",
]