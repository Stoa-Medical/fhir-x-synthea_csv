"""
Immunization reverse mapper: FHIR R4 Immunization to Synthea CSV immunizations row.
"""

from typing import Any, Dict

from ..common.reverse_transformers import (
    parse_fhir_datetime,
    extract_reference_id,
    extract_coding_by_system,
    extract_extension_by_url,
)


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dict but keep empty strings."""
    return {k: (v if v is not None else "") for k, v in d.items()}


def fhir_immunization_to_csv_transform(fhir_immunization: Dict[str, Any]) -> Dict[str, Any]:
    """Transform FHIR Immunization to Synthea immunizations CSV row."""
    # Date
    date = parse_fhir_datetime(fhir_immunization.get("occurrenceDateTime"))

    # References
    patient_id = extract_reference_id(fhir_immunization.get("patient"))
    encounter_id = extract_reference_id(fhir_immunization.get("encounter"))

    # Coding (prefer CVX)
    vaccine_code = fhir_immunization.get("vaccineCode") or {}
    cvx_coding = extract_coding_by_system(vaccine_code, "http://hl7.org/fhir/sid/cvx")
    code = None
    description = None
    if cvx_coding:
        code = cvx_coding.get("code")
        description = cvx_coding.get("display")
    if not code or not description:
        coding_list = vaccine_code.get("coding", [])
        if coding_list:
            first = coding_list[0]
            code = code or first.get("code")
            description = description or first.get("display")
    if not description:
        description = vaccine_code.get("text")

    # Cost extension
    cost_ext = extract_extension_by_url(
        fhir_immunization.get("extension"),
        "http://synthea.mitre.org/fhir/StructureDefinition/immunization-cost",
    )
    cost = None
    if cost_ext is not None:
        # Expect valueDecimal
        value = cost_ext.get("valueDecimal")
        cost = str(value) if value is not None else None

    result = {
        "DATE": date,
        "PATIENT": patient_id,
        "ENCOUNTER": encounter_id,
        "CODE": code,
        "DESCRIPTION": description,
        "COST": cost,
    }
    return filter_none_values(result)


def map_fhir_immunization_to_csv(fhir_immunization: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert FHIR Immunization to Synthea `immunizations.csv` row representation.
    """
    if not fhir_immunization or fhir_immunization.get("resourceType") != "Immunization":
        raise ValueError("Input must be a FHIR Immunization resource")
    return fhir_immunization_to_csv_transform(fhir_immunization)


