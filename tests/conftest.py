"""
Pytest configuration and fixtures for FHIR x Synthea CSV tests.
"""

import pytest
from pathlib import Path
from chidian import Table

from .loaders import (
    load_patients_csv,
    load_observations_csv,
    load_conditions_csv,
    get_patient_bundle_table,
    get_csv_patient_data,
    get_csv_patient_observations,
    get_csv_patient_conditions,
)


# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "data"
CSV_DATA_DIR = TEST_DATA_DIR / "csv"
FHIR_DATA_DIR = TEST_DATA_DIR / "fhir"

# Standard test patient ID
TEST_PATIENT_ID = "8c8e1c9a-b310-43c6-33a7-ad11bad21c40"  # Britt177


@pytest.fixture(scope="session")
def csv_data_available():
    """Check if CSV test data is available."""
    patients_file = CSV_DATA_DIR / "patients.csv"
    if not patients_file.exists():
        pytest.skip(
            f"CSV test data not found at {CSV_DATA_DIR}. "
            "Please download test data from https://synthea.mitre.org/downloads"
        )
    return True


@pytest.fixture(scope="session")
def fhir_data_available():
    """Check if FHIR test data is available."""
    # Check for at least one FHIR bundle file
    json_files = list(FHIR_DATA_DIR.glob("*.json"))
    patient_bundles = [f for f in json_files if not f.name.startswith(("hospital", "practitioner"))]
    
    if not patient_bundles:
        pytest.skip(
            f"FHIR test data not found at {FHIR_DATA_DIR}. "
            "Please download test data from https://synthea.mitre.org/downloads"
        )
    return True


@pytest.fixture(scope="session")
def patients_table(csv_data_available) -> Table:
    """Load patients CSV as a Table (session-scoped for performance)."""
    return load_patients_csv()


@pytest.fixture(scope="session")
def observations_table(csv_data_available) -> Table:
    """Load observations CSV as a Table (session-scoped for performance)."""
    return load_observations_csv()


@pytest.fixture(scope="session")
def conditions_table(csv_data_available) -> Table:
    """Load conditions CSV as a Table (session-scoped for performance)."""
    return load_conditions_csv()


@pytest.fixture
def test_patient_data(patients_table):
    """Get test patient data from CSV."""
    data = get_csv_patient_data(patients_table, TEST_PATIENT_ID)
    if not data:
        pytest.skip(f"Test patient {TEST_PATIENT_ID} not found in CSV data")
    return data


@pytest.fixture
def test_patient_observations(observations_table):
    """Get test patient's observations from CSV."""
    return get_csv_patient_observations(observations_table, TEST_PATIENT_ID)


@pytest.fixture
def test_patient_conditions(conditions_table):
    """Get test patient's conditions from CSV."""
    return get_csv_patient_conditions(conditions_table, TEST_PATIENT_ID)


@pytest.fixture
def test_patient_bundle(fhir_data_available):
    """Get test patient's FHIR bundle."""
    bundle_table = get_patient_bundle_table(TEST_PATIENT_ID)
    if not bundle_table:
        pytest.skip(f"FHIR bundle for patient {TEST_PATIENT_ID} not found")
    return bundle_table


@pytest.fixture
def sample_csv_patient():
    """Provide a sample CSV patient dict for unit tests."""
    return {
        "Id": "test-patient-123",
        "BIRTHDATE": "1985-03-15",
        "DEATHDATE": "",
        "SSN": "999-12-3456",
        "DRIVERS": "S99998765",
        "PASSPORT": "X12345678X",
        "PREFIX": "Mr.",
        "FIRST": "John",
        "MIDDLE": "Michael",
        "LAST": "Smith",
        "SUFFIX": "Jr.",
        "MAIDEN": "",
        "MARITAL": "M",
        "RACE": "white",
        "ETHNICITY": "nonhispanic",
        "GENDER": "M",
        "BIRTHPLACE": "Boston, Massachusetts",
        "ADDRESS": "123 Main Street",
        "CITY": "Boston",
        "STATE": "Massachusetts",
        "COUNTY": "Suffolk County",
        "ZIP": "02101",
        "LAT": "42.3601",
        "LON": "-71.0589",
    }


@pytest.fixture
def sample_csv_observation():
    """Provide a sample CSV observation dict for unit tests."""
    return {
        "DATE": "2024-01-15T10:30:00Z",
        "PATIENT": "test-patient-123",
        "ENCOUNTER": "enc-123456",
        "CATEGORY": "vital-signs",
        "CODE": "8302-2",
        "DESCRIPTION": "Body Height",
        "VALUE": "175",
        "UNITS": "cm",
        "TYPE": "numeric",
    }


@pytest.fixture
def sample_csv_condition():
    """Provide a sample CSV condition dict for unit tests."""
    return {
        "START": "2023-06-01",
        "STOP": "",
        "PATIENT": "test-patient-123",
        "ENCOUNTER": "enc-789012",
        "SYSTEM": "http://snomed.info/sct",
        "CODE": "44054006",
        "DESCRIPTION": "Diabetes mellitus type 2 (disorder)",
    }


# Markers for test organization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "requires_csv: mark test as requiring CSV test data")
    config.addinivalue_line("markers", "requires_fhir: mark test as requiring FHIR test data")
    config.addinivalue_line("markers", "requires_both: mark test as requiring both CSV and FHIR data")