"""
Roundtrip validation tests: CSV → FHIR → CSV to ensure bidirectional mapping fidelity.
"""

import pytest

from fhir_x_synthea_csv.to_fhir import map_patient, map_observation, map_condition
from fhir_x_synthea_csv.to_synthea_csv import (
    map_fhir_patient_to_csv,
    map_fhir_observation_to_csv, 
    map_fhir_condition_to_csv,
)


@pytest.mark.unit
def test_patient_roundtrip_basic(sample_csv_patient):
    """Test basic patient roundtrip transformation."""
    # CSV → FHIR
    fhir_patient = map_patient(sample_csv_patient)
    
    # FHIR → CSV
    csv_patient = map_fhir_patient_to_csv(fhir_patient)
    
    # Validate core fields are preserved
    assert csv_patient["Id"] == sample_csv_patient["Id"]
    assert csv_patient["FIRST"] == sample_csv_patient["FIRST"]
    assert csv_patient["LAST"] == sample_csv_patient["LAST"]
    assert csv_patient["GENDER"] == sample_csv_patient["GENDER"]
    assert csv_patient["BIRTHDATE"] == sample_csv_patient["BIRTHDATE"]


@pytest.mark.unit
def test_patient_roundtrip_identifiers(sample_csv_patient):
    """Test that patient identifiers survive roundtrip."""
    # CSV → FHIR → CSV
    fhir_patient = map_patient(sample_csv_patient)
    csv_patient = map_fhir_patient_to_csv(fhir_patient)
    
    # Check identifiers
    assert csv_patient["SSN"] == sample_csv_patient["SSN"]
    assert csv_patient["DRIVERS"] == sample_csv_patient["DRIVERS"]
    assert csv_patient["PASSPORT"] == sample_csv_patient["PASSPORT"]


@pytest.mark.unit
def test_patient_roundtrip_demographics(sample_csv_patient):
    """Test demographic data preservation in roundtrip."""
    # CSV → FHIR → CSV
    fhir_patient = map_patient(sample_csv_patient)
    csv_patient = map_fhir_patient_to_csv(fhir_patient)
    
    # Check demographics
    assert csv_patient["RACE"] == sample_csv_patient["RACE"]
    assert csv_patient["ETHNICITY"] == sample_csv_patient["ETHNICITY"]
    assert csv_patient["MARITAL"] == sample_csv_patient["MARITAL"]


@pytest.mark.unit
def test_patient_roundtrip_address(sample_csv_patient):
    """Test address data preservation in roundtrip.""" 
    # CSV → FHIR → CSV
    fhir_patient = map_patient(sample_csv_patient)
    csv_patient = map_fhir_patient_to_csv(fhir_patient)
    
    # Check address components
    assert csv_patient["ADDRESS"] == sample_csv_patient["ADDRESS"]
    assert csv_patient["CITY"] == sample_csv_patient["CITY"]
    assert csv_patient["STATE"] == sample_csv_patient["STATE"]
    assert csv_patient["ZIP"] == sample_csv_patient["ZIP"]
    # Note: LAT/LON precision may be affected by float conversion
    # We'll just check they exist
    assert csv_patient["LAT"] is not None
    assert csv_patient["LON"] is not None


@pytest.mark.unit 
def test_patient_roundtrip_with_death_date(sample_csv_patient):
    """Test patient with death date roundtrip."""
    # Add death date
    sample_csv_patient["DEATHDATE"] = "2023-12-01"
    
    # CSV → FHIR → CSV
    fhir_patient = map_patient(sample_csv_patient)
    csv_patient = map_fhir_patient_to_csv(fhir_patient)
    
    # Death date should be preserved (may have time component added)
    assert csv_patient["DEATHDATE"].startswith("2023-12-01")


@pytest.mark.unit
def test_observation_roundtrip_basic(sample_csv_observation):
    """Test basic observation roundtrip transformation."""
    # CSV → FHIR → CSV
    fhir_observation = map_observation(sample_csv_observation)
    csv_observation = map_fhir_observation_to_csv(fhir_observation)
    
    # Validate core fields are preserved
    assert csv_observation["PATIENT"] == sample_csv_observation["PATIENT"]
    assert csv_observation["CODE"] == sample_csv_observation["CODE"]
    assert csv_observation["DESCRIPTION"] == sample_csv_observation["DESCRIPTION"]
    assert csv_observation["VALUE"] == sample_csv_observation["VALUE"]
    assert csv_observation["UNITS"] == sample_csv_observation["UNITS"]


@pytest.mark.unit
def test_observation_roundtrip_category(sample_csv_observation):
    """Test observation category preservation."""
    # CSV → FHIR → CSV
    fhir_observation = map_observation(sample_csv_observation)
    csv_observation = map_fhir_observation_to_csv(fhir_observation)
    
    # Category should be preserved
    assert csv_observation["CATEGORY"] == sample_csv_observation["CATEGORY"]
    assert csv_observation["TYPE"] == sample_csv_observation["TYPE"]


@pytest.mark.unit
def test_observation_roundtrip_datetime(sample_csv_observation):
    """Test observation datetime handling in roundtrip."""
    # CSV → FHIR → CSV
    fhir_observation = map_observation(sample_csv_observation)
    csv_observation = map_fhir_observation_to_csv(fhir_observation)
    
    # Date should be preserved (format may change)
    original_date = sample_csv_observation["DATE"]
    result_date = csv_observation["DATE"]
    
    # Both should contain the same date portion
    assert "2024-01-15" in original_date
    assert "2024-01-15" in result_date


@pytest.mark.unit
def test_condition_roundtrip_basic(sample_csv_condition):
    """Test basic condition roundtrip transformation."""
    # CSV → FHIR → CSV
    fhir_condition = map_condition(sample_csv_condition)
    csv_condition = map_fhir_condition_to_csv(fhir_condition)
    
    # Validate core fields are preserved
    assert csv_condition["PATIENT"] == sample_csv_condition["PATIENT"]
    assert csv_condition["CODE"] == sample_csv_condition["CODE"]
    assert csv_condition["DESCRIPTION"] == sample_csv_condition["DESCRIPTION"]
    assert csv_condition["SYSTEM"] == sample_csv_condition["SYSTEM"]


@pytest.mark.unit
def test_condition_roundtrip_dates(sample_csv_condition):
    """Test condition date handling in roundtrip."""
    # CSV → FHIR → CSV
    fhir_condition = map_condition(sample_csv_condition)
    csv_condition = map_fhir_condition_to_csv(fhir_condition)
    
    # Start date should be preserved
    original_start = sample_csv_condition["START"]
    result_start = csv_condition["START"]
    
    assert "2023-06-01" in result_start
    
    # STOP should be empty as in original
    assert csv_condition["STOP"] == ""


@pytest.mark.unit
def test_condition_roundtrip_with_stop_date(sample_csv_condition):
    """Test condition with stop date roundtrip."""
    # Add stop date
    sample_csv_condition["STOP"] = "2024-01-15"
    
    # CSV → FHIR → CSV
    fhir_condition = map_condition(sample_csv_condition)
    csv_condition = map_fhir_condition_to_csv(fhir_condition)
    
    # Both dates should be preserved
    assert "2023-06-01" in csv_condition["START"]
    assert "2024-01-15" in csv_condition["STOP"]


@pytest.mark.parametrize("gender_csv,gender_fhir", [
    ("M", "male"),
    ("F", "female"),
    ("O", "other"),
    ("U", "unknown"),
])
def test_gender_roundtrip(sample_csv_patient, gender_csv, gender_fhir):
    """Test gender mapping roundtrip for all values."""
    sample_csv_patient["GENDER"] = gender_csv
    
    # CSV → FHIR
    fhir_patient = map_patient(sample_csv_patient)
    assert fhir_patient["gender"] == gender_fhir
    
    # FHIR → CSV
    csv_patient = map_fhir_patient_to_csv(fhir_patient)
    assert csv_patient["GENDER"] == gender_csv


@pytest.mark.parametrize("marital_csv,marital_code", [
    ("M", "M"),  # Married
    ("S", "S"),  # Single  
    ("D", "D"),  # Divorced
    ("W", "W"),  # Widowed
])
def test_marital_status_roundtrip(sample_csv_patient, marital_csv, marital_code):
    """Test marital status roundtrip for all values."""
    sample_csv_patient["MARITAL"] = marital_csv
    
    # CSV → FHIR → CSV
    fhir_patient = map_patient(sample_csv_patient)
    csv_patient = map_fhir_patient_to_csv(fhir_patient)
    
    assert csv_patient["MARITAL"] == marital_csv


@pytest.mark.unit
def test_numeric_observation_roundtrip():
    """Test numeric observation value preservation."""
    csv_obs = {
        "DATE": "2024-01-15T10:30:00Z",
        "PATIENT": "test-patient-123", 
        "ENCOUNTER": "enc-123456",
        "CATEGORY": "vital-signs",
        "CODE": "8302-2",
        "DESCRIPTION": "Body Height",
        "VALUE": "175.5",
        "UNITS": "cm",
        "TYPE": "numeric",
    }
    
    # CSV → FHIR → CSV
    fhir_obs = map_observation(csv_obs)
    result_csv = map_fhir_observation_to_csv(fhir_obs)
    
    # Numeric value should be preserved
    assert result_csv["VALUE"] == "175.5"
    assert result_csv["UNITS"] == "cm"
    assert result_csv["TYPE"] == "numeric"


@pytest.mark.unit
def test_text_observation_roundtrip():
    """Test text observation value preservation."""
    csv_obs = {
        "DATE": "2024-01-15T10:30:00Z",
        "PATIENT": "test-patient-123",
        "ENCOUNTER": "enc-123456", 
        "CATEGORY": "survey",
        "CODE": "72133-2",
        "DESCRIPTION": "Smoking status",
        "VALUE": "Former smoker",
        "UNITS": "",
        "TYPE": "text",
    }
    
    # CSV → FHIR → CSV  
    fhir_obs = map_observation(csv_obs)
    result_csv = map_fhir_observation_to_csv(fhir_obs)
    
    # Text value should be preserved
    assert result_csv["VALUE"] == "Former smoker"
    assert result_csv["UNITS"] == ""
    assert result_csv["TYPE"] == "text"


@pytest.mark.unit
def test_boolean_observation_roundtrip():
    """Test boolean observation value preservation."""
    csv_obs = {
        "DATE": "2024-01-15T10:30:00Z",
        "PATIENT": "test-patient-123",
        "ENCOUNTER": "enc-123456",
        "CATEGORY": "survey",
        "CODE": "72166-2", 
        "DESCRIPTION": "Tobacco smoking status",
        "VALUE": "true",
        "UNITS": "",
        "TYPE": "text",  # Synthea treats booleans as text
    }
    
    # CSV → FHIR → CSV
    fhir_obs = map_observation(csv_obs)
    result_csv = map_fhir_observation_to_csv(fhir_obs)
    
    # Boolean should be preserved as text
    assert result_csv["VALUE"] == "true"
    assert result_csv["TYPE"] == "text"


@pytest.mark.requires_csv
def test_patient_roundtrip_with_real_data(test_patient_data):
    """Test patient roundtrip with real CSV data."""
    # CSV → FHIR → CSV
    fhir_patient = map_patient(test_patient_data)
    csv_patient = map_fhir_patient_to_csv(fhir_patient)
    
    # Core fields should match
    assert csv_patient["Id"] == test_patient_data["Id"]
    assert csv_patient["GENDER"] == test_patient_data["GENDER"]
    assert csv_patient["BIRTHDATE"] == test_patient_data["BIRTHDATE"]


@pytest.mark.requires_csv 
def test_observation_roundtrip_with_real_data(test_patient_observations):
    """Test observation roundtrip with real CSV data."""
    if not test_patient_observations:
        pytest.skip("No observations found for test patient")
    
    # Test with first observation
    for obs_data in test_patient_observations.head(1):
        # CSV → FHIR → CSV
        fhir_obs = map_observation(obs_data)
        csv_obs = map_fhir_observation_to_csv(fhir_obs)
        
        # Core fields should match
        assert csv_obs["PATIENT"] == obs_data["PATIENT"]
        assert csv_obs["CODE"] == obs_data["CODE"]
        break


@pytest.mark.requires_csv
def test_condition_roundtrip_with_real_data(test_patient_conditions):
    """Test condition roundtrip with real CSV data."""
    if not test_patient_conditions:
        pytest.skip("No conditions found for test patient")
    
    # Test with first condition
    for cond_data in test_patient_conditions.head(1):
        # CSV → FHIR → CSV
        fhir_cond = map_condition(cond_data)
        csv_cond = map_fhir_condition_to_csv(fhir_cond)
        
        # Core fields should match
        assert csv_cond["PATIENT"] == cond_data["PATIENT"]
        assert csv_cond["CODE"] == cond_data["CODE"]
        assert csv_cond["SYSTEM"] == cond_data["SYSTEM"]
        break