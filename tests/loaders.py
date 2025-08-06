"""
Data loaders for converting CSV files and FHIR Bundles into chidian Tables.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from chidian import Table
from chidian import get


# Base paths for test data
TEST_DATA_DIR = Path(__file__).parent / "data"
CSV_DATA_DIR = TEST_DATA_DIR / "csv"
FHIR_DATA_DIR = TEST_DATA_DIR / "fhir"


def load_csv_as_table(csv_path: Path, key_field: Optional[str] = None) -> Table:
    """
    Load a CSV file into a chidian Table.
    
    Args:
        csv_path: Path to the CSV file
        key_field: Optional field to use as row keys (otherwise uses $0, $1, ...)
        
    Returns:
        Table containing CSV rows
    """
    rows = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean up empty strings to None for consistency
            cleaned_row = {k: (v if v != '' else None) for k, v in row.items()}
            rows.append(cleaned_row)
    
    if key_field:
        # Create dict with specified field as keys
        keyed_rows = {}
        for row in rows:
            if key_field in row and row[key_field]:
                keyed_rows[row[key_field]] = row
        return Table(keyed_rows)
    else:
        # Return as list (auto-keyed with $0, $1, ...)
        return Table(rows)


def load_patients_csv() -> Table:
    """Load patients.csv with patient IDs as keys."""
    return load_csv_as_table(CSV_DATA_DIR / "patients.csv", key_field="Id")


def load_observations_csv() -> Table:
    """Load observations.csv as a Table."""
    return load_csv_as_table(CSV_DATA_DIR / "observations.csv")


def load_conditions_csv() -> Table:
    """Load conditions.csv as a Table."""
    return load_csv_as_table(CSV_DATA_DIR / "conditions.csv")


def load_encounters_csv() -> Table:
    """Load encounters.csv as a Table."""
    return load_csv_as_table(CSV_DATA_DIR / "encounters.csv", key_field="Id")


def load_medications_csv() -> Table:
    """Load medications.csv as a Table."""
    return load_csv_as_table(CSV_DATA_DIR / "medications.csv")


def load_immunizations_csv() -> Table:
    """Load immunizations.csv as a Table."""
    return load_csv_as_table(CSV_DATA_DIR / "immunizations.csv")


def load_procedures_csv() -> Table:
    """Load procedures.csv as a Table."""
    return load_csv_as_table(CSV_DATA_DIR / "procedures.csv")


def load_fhir_bundle(json_path: Path) -> Dict[str, Any]:
    """
    Load a FHIR Bundle from a JSON file.
    
    Args:
        json_path: Path to the FHIR Bundle JSON file
        
    Returns:
        Bundle as dictionary
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_bundle_resources(bundle: Dict[str, Any]) -> Table:
    """
    Extract all resources from a FHIR Bundle into a Table.
    
    Args:
        bundle: FHIR Bundle dictionary
        
    Returns:
        Table containing all resources from the bundle
    """
    # Extract resources using chidian's get with path notation
    resources = get(bundle, "entry[*].resource", default=[])
    
    # Filter out None values and ensure we have a list
    if not isinstance(resources, list):
        resources = [resources] if resources else []
    
    resources = [r for r in resources if r is not None]
    
    # Create table with resources
    # Use resource ID as key if available
    keyed_resources = {}
    for i, resource in enumerate(resources):
        # Try to use resource ID as key, fallback to index
        resource_id = resource.get("id", f"resource_{i}")
        keyed_resources[resource_id] = resource
    
    return Table(keyed_resources)


def extract_resources_by_type(bundle_table: Table, resource_type: str) -> Table:
    """
    Filter a bundle Table to get only resources of a specific type.
    
    Args:
        bundle_table: Table containing bundle resources
        resource_type: FHIR resource type (e.g., "Patient", "Observation")
        
    Returns:
        Table containing only resources of the specified type
    """
    return bundle_table.filter(f"resourceType = '{resource_type}'")


def get_patient_bundle(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Find and load the FHIR bundle for a specific patient ID.
    
    Args:
        patient_id: The patient ID to search for
        
    Returns:
        Bundle dictionary if found, None otherwise
    """
    # Look for files containing the patient ID
    for json_file in FHIR_DATA_DIR.glob("*.json"):
        if patient_id in json_file.name:
            return load_fhir_bundle(json_file)
    
    return None


def get_patient_bundle_table(patient_id: str) -> Optional[Table]:
    """
    Get a Table of resources from a patient's FHIR bundle.
    
    Args:
        patient_id: The patient ID
        
    Returns:
        Table of resources if bundle found, None otherwise
    """
    bundle = get_patient_bundle(patient_id)
    if bundle:
        return extract_bundle_resources(bundle)
    return None


def get_patient_resources(
    bundle_table: Table, 
    patient_id: str,
    resource_type: Optional[str] = None
) -> Table:
    """
    Filter resources for a specific patient from a bundle Table.
    
    Args:
        bundle_table: Table containing bundle resources
        patient_id: Patient ID to filter for
        resource_type: Optional resource type filter
        
    Returns:
        Table containing filtered resources
    """
    # Build filter expression
    patient_ref = f"Patient/{patient_id}"
    
    if resource_type:
        # Filter by both patient reference and resource type
        # Handle different reference fields (subject, patient, etc.)
        filter_expr = (
            f"(subject.reference = '{patient_ref}' OR "
            f"patient.reference = '{patient_ref}') AND "
            f"resourceType = '{resource_type}'"
        )
    else:
        # Just filter by patient reference
        filter_expr = (
            f"subject.reference = '{patient_ref}' OR "
            f"patient.reference = '{patient_ref}'"
        )
    
    return bundle_table.filter(filter_expr)


def get_csv_patient_data(patients_table: Table, patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single patient's data from the patients Table.
    
    Args:
        patients_table: Table of patient data
        patient_id: Patient ID to retrieve
        
    Returns:
        Patient data dictionary if found, None otherwise
    """
    # Use the $ prefix for keyed access
    key = f"${patient_id}"
    if key in patients_table:
        return patients_table.get(key)
    
    # Fallback: search through all rows
    for row in patients_table:
        if row.get("Id") == patient_id:
            return row
    
    return None


def get_csv_patient_observations(observations_table: Table, patient_id: str) -> Table:
    """
    Get all observations for a specific patient from CSV data.
    
    Args:
        observations_table: Table of observation data
        patient_id: Patient ID to filter for
        
    Returns:
        Table containing patient's observations
    """
    return observations_table.filter(f"PATIENT = '{patient_id}'")


def get_csv_patient_conditions(conditions_table: Table, patient_id: str) -> Table:
    """
    Get all conditions for a specific patient from CSV data.
    
    Args:
        conditions_table: Table of condition data
        patient_id: Patient ID to filter for
        
    Returns:
        Table containing patient's conditions
    """
    return conditions_table.filter(f"PATIENT = '{patient_id}'")


def list_available_patients() -> List[str]:
    """
    List all patient IDs available in the test data.
    
    Returns:
        List of patient IDs
    """
    patients = load_patients_csv()
    return patients.unique("Id")


def list_fhir_bundles() -> List[Path]:
    """
    List all FHIR bundle files available.
    
    Returns:
        List of paths to FHIR bundle JSON files
    """
    return sorted([
        f for f in FHIR_DATA_DIR.glob("*.json")
        if not f.name.startswith(("hospital", "practitioner"))
    ])