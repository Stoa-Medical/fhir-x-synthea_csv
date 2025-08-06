"""
Test cases for Patient resource mapping using chidian Tables.
"""

import pytest
from chidian import Table

from fhir_x_synthea_csv.to_fhir import map_patient
from .loaders import (
    extract_resources_by_type,
    get_csv_patient_data,
)
from .validators import assert_patient_equivalence


# Test Constants
TEST_PATIENT_ID = "8c8e1c9a-b310-43c6-33a7-ad11bad21c40"


@pytest.mark.unit
def test_patient_mapping_basic(sample_csv_patient):
    """Test basic patient mapping functionality."""
    fhir_patient = map_patient(sample_csv_patient)
    
    assert fhir_patient["resourceType"] == "Patient"
    assert fhir_patient["id"] == sample_csv_patient["Id"]
    assert fhir_patient["gender"] == "male"  # M -> male
    assert fhir_patient["birthDate"] == "1985-03-15"


@pytest.mark.unit
def test_patient_core_fields(sample_csv_patient):
    """Test that core patient fields are mapped correctly."""
    fhir_patient = map_patient(sample_csv_patient)
    
    # Check required fields
    assert fhir_patient["id"] == "test-patient-123"
    assert fhir_patient["gender"] == "male"  # M -> male
    assert fhir_patient["birthDate"] == "1985-03-15"
    
    # Check name structure
    assert "name" in fhir_patient
    assert isinstance(fhir_patient["name"], list)
    assert len(fhir_patient["name"]) > 0
    
    primary_name = fhir_patient["name"][0]
    assert primary_name["use"] == "official"
    assert primary_name["given"] == ["John"]
    assert primary_name["family"] == "Smith"
    assert primary_name["prefix"] == ["Mr."]


@pytest.mark.unit
def test_patient_identifiers(sample_csv_patient):
    """Test that patient identifiers are mapped correctly."""
    fhir_patient = map_patient(sample_csv_patient)
    
    assert "identifier" in fhir_patient
    identifiers = fhir_patient["identifier"]
    assert isinstance(identifiers, list)
    
    # Check for expected identifier types
    identifier_types = {
        id_obj["type"]["coding"][0]["code"]
        for id_obj in identifiers
        if "type" in id_obj
    }
    
    # Should have MR (medical record), SS (SSN), DL (driver's license), PPN (passport)
    expected_types = {"MR", "SS", "DL", "PPN"}
    assert identifier_types == expected_types
    
    # Check SSN value
    ssn_identifier = next(
        (id_obj for id_obj in identifiers 
         if id_obj.get("type", {}).get("coding", [{}])[0].get("code") == "SS"),
        None
    )
    assert ssn_identifier is not None
    assert ssn_identifier["value"] == "999-12-3456"


@pytest.mark.unit
def test_patient_address(sample_csv_patient):
    """Test that patient address is mapped correctly."""
    fhir_patient = map_patient(sample_csv_patient)
    
    assert "address" in fhir_patient
    addresses = fhir_patient["address"]
    assert isinstance(addresses, list)
    assert len(addresses) == 1
    
    address = addresses[0]
    assert address["use"] == "home"
    assert address["line"] == ["123 Main Street"]
    assert address["city"] == "Boston"
    assert address["state"] == "Massachusetts"
    assert address["postalCode"] == "02101"
    
    # Check geolocation extension
    assert "extension" in address
    geo_ext = next(
        (ext for ext in address["extension"] 
         if ext["url"] == "http://hl7.org/fhir/StructureDefinition/geolocation"),
        None
    )
    assert geo_ext is not None


@pytest.mark.unit
def test_patient_extensions(sample_csv_patient):
    """Test that US Core extensions are mapped correctly."""
    fhir_patient = map_patient(sample_csv_patient)
    
    assert "extension" in fhir_patient
    extensions = fhir_patient["extension"]
    
    # Check for race extension
    race_ext = next(
        (ext for ext in extensions 
         if ext["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"),
        None
    )
    assert race_ext is not None, "Race extension not found"
    
    # Check race coding
    race_coding = None
    for nested_ext in race_ext.get("extension", []):
        if nested_ext["url"] == "ombCategory":
            race_coding = nested_ext.get("valueCoding")
            break
    
    assert race_coding is not None
    assert race_coding["code"] == "2106-3"  # White
    
    # Check for ethnicity extension
    ethnicity_ext = next(
        (ext for ext in extensions 
         if ext["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"),
        None
    )
    assert ethnicity_ext is not None, "Ethnicity extension not found"


@pytest.mark.unit
def test_patient_with_death_date(sample_csv_patient):
    """Test mapping for a patient with a death date."""
    # Modify sample to have death date
    sample_csv_patient["DEATHDATE"] = "2023-12-01"
    
    fhir_patient = map_patient(sample_csv_patient)
    assert "deceasedDateTime" in fhir_patient
    assert fhir_patient["deceasedDateTime"] is not None


@pytest.mark.requires_csv
def test_patient_mapping_with_real_data(test_patient_data):
    """Test mapping with real CSV data."""
    fhir_patient = map_patient(test_patient_data)
    
    assert fhir_patient["resourceType"] == "Patient"
    assert fhir_patient["id"] == TEST_PATIENT_ID
    assert "gender" in fhir_patient
    assert "birthDate" in fhir_patient
    assert "name" in fhir_patient


@pytest.mark.requires_both
def test_patient_comparison_with_synthea(test_patient_data, test_patient_bundle):
    """Test comparing our mapped patient with Synthea's FHIR output."""
    # Transform using our mapper
    our_fhir_patient = map_patient(test_patient_data)
    
    # Get Synthea's patient
    synthea_patients = extract_resources_by_type(test_patient_bundle, "Patient")
    assert len(synthea_patients) == 1, "Expected exactly one Patient resource"
    
    # Get the first (and only) patient from the table
    synthea_patient = None
    for patient in synthea_patients:
        synthea_patient = patient
        break
    
    assert synthea_patient is not None
    
    # Compare the resources
    result = assert_patient_equivalence(our_fhir_patient, synthea_patient)
    
    # Print detailed comparison for debugging if needed
    if not result["valid"] or result["warnings"]:
        print(f"\nPatient {TEST_PATIENT_ID} comparison:")
        print(f"  Matches: {result['matches']}")
        if result["errors"]:
            print(f"  Errors: {result['errors']}")
        if result["warnings"]:
            print(f"  Warnings: {result['warnings']}")
    
    # Assert the mapping is valid (allow warnings but not errors)
    assert result["valid"], f"Patient mapping validation failed: {result['errors']}"


@pytest.mark.requires_csv
def test_table_filtering(patients_table):
    """Test using Table filtering to find patients."""
    # Filter patients by gender using Table DSL
    male_patients = patients_table.filter("GENDER = 'M'")
    female_patients = patients_table.filter("GENDER = 'F'")
    
    # Verify filtering worked
    assert len(male_patients) > 0
    assert len(female_patients) > 0
    
    # Map a filtered patient
    for male_patient in male_patients.head(1):
        our_fhir = map_patient(male_patient)
        assert our_fhir["gender"] == "male"
        break
    
    for female_patient in female_patients.head(1):
        our_fhir = map_patient(female_patient)
        assert our_fhir["gender"] == "female"
        break


@pytest.mark.requires_csv
def test_table_select(patients_table):
    """Test using Table select to project specific fields."""
    # Select only specific fields
    patient_names = patients_table.select("Id, FIRST, LAST, GENDER")
    
    # Verify select worked - should have limited fields
    for patient in patient_names.head(1):
        assert "Id" in patient
        assert "FIRST" in patient
        assert "LAST" in patient
        assert "GENDER" in patient
        # These should not be present after select
        assert "BIRTHDATE" not in patient
        assert "ADDRESS" not in patient
        break


@pytest.mark.parametrize("gender_csv,gender_fhir", [
    ("M", "male"),
    ("F", "female"),
    ("O", "other"),
    ("U", "unknown"),
])
def test_gender_mapping(sample_csv_patient, gender_csv, gender_fhir):
    """Test gender mapping for all possible values."""
    sample_csv_patient["GENDER"] = gender_csv
    fhir_patient = map_patient(sample_csv_patient)
    assert fhir_patient["gender"] == gender_fhir


@pytest.mark.parametrize("marital_csv,marital_fhir_code", [
    ("M", "M"),  # Married
    ("S", "S"),  # Single  
    ("D", "D"),  # Divorced
    ("W", "W"),  # Widowed
])
def test_marital_status_mapping(sample_csv_patient, marital_csv, marital_fhir_code):
    """Test marital status mapping."""
    sample_csv_patient["MARITAL"] = marital_csv
    fhir_patient = map_patient(sample_csv_patient)
    
    assert "maritalStatus" in fhir_patient
    marital_status = fhir_patient["maritalStatus"]
    assert marital_status["coding"][0]["code"] == marital_fhir_code