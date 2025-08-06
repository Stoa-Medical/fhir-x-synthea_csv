# Testing Guide

This document describes the comprehensive test suite for the FHIR x Synthea CSV mapping library, built using `chidian.Table` for data processing.

## Quick Start

```bash
# Run all unit tests (no external data required)
uv run pytest -m unit -v

# Run comprehensive test suite
python test_runner.py

# Run specific test categories
uv run pytest -m requires_csv -v    # Tests requiring CSV data
uv run pytest -m requires_both -v   # Tests requiring both CSV and FHIR data
```

## Test Architecture

The test suite demonstrates the power of using `chidian.Table` for healthcare data validation:

### 🗂️ **Table-Based Data Loading**

```python
# CSV files become Tables automatically
patients = load_patients_csv()          # Table with patient IDs as keys
observations = load_observations_csv()  # Table with auto-indexed rows

# FHIR Bundles become Tables of resources  
bundle_table = get_patient_bundle_table(patient_id)
patients = extract_resources_by_type(bundle_table, "Patient")
```

### 🔍 **Declarative Filtering**

```python
# Filter using SQL-like syntax instead of manual loops
male_patients = patients.filter("GENDER = 'M'")
vital_signs = observations.filter("CATEGORY = 'vital-signs'")

# Chain filters elegantly
blood_pressure = (
    observations
    .filter("CATEGORY = 'vital-signs'")
    .filter("UNITS = 'mm[Hg]'")
)
```

### 📊 **Data Projection and Grouping**

```python
# Select specific fields (like SQL SELECT)
patient_names = patients.select("Id, FIRST, LAST, GENDER")

# Group data for analysis
obs_by_patient = observations.group_by("PATIENT")
unique_codes = observations.unique("CODE")
```

## Test Categories

### 🧪 **Unit Tests** (`-m unit`)
- Test mappers with synthetic data
- No external data dependencies
- Fast execution (< 0.1s)
- Parametrized tests for edge cases

### 📋 **CSV Integration Tests** (`-m requires_csv`)  
- Test with real Synthea CSV data
- Validate Table operations
- Statistical analysis across patients

### 🔬 **Full Validation Tests** (`-m requires_both`)
- Compare our mappings vs Synthea's FHIR output
- End-to-end semantic validation
- Field-by-field equivalence checking

## Test Data Setup

### Option 1: Skip Data-Dependent Tests
```bash
# Just run unit tests
uv run pytest -m unit
```

### Option 2: Full Testing with Real Data
1. Download from [Synthea Downloads](https://synthea.mitre.org/downloads):
   - 100 Sample CSV files (latest)
   - 100 Sample FHIR R4 files (latest)

2. Extract to test directories:
```bash
# CSV files go here
tests/data/csv/
├── patients.csv
├── observations.csv
├── conditions.csv
└── ...

# FHIR bundles go here  
tests/data/fhir/
├── Britt177_Keeling57_8c8e1c9a-b310-43c6-33a7-ad11bad21c40.json
└── ...
```

3. Run full suite:
```bash
uv run pytest -v
```

## Key Test Examples

### Patient Mapping Validation
```python
@pytest.mark.requires_both
def test_patient_comparison_with_synthea(test_patient_data, test_patient_bundle):
    # Map CSV → FHIR using our library
    our_fhir_patient = map_patient(test_patient_data)
    
    # Extract Synthea's FHIR Patient  
    synthea_patients = extract_resources_by_type(test_patient_bundle, "Patient")
    synthea_patient = synthea_patients[0]
    
    # Semantic validation
    result = assert_patient_equivalence(our_fhir_patient, synthea_patient)
    assert result["valid"], f"Mapping failed: {result['errors']}"
```

### Table Operations Testing
```python
@pytest.mark.requires_csv  
def test_table_filtering(patients_table):
    # Demonstrate Table DSL usage
    male_patients = patients_table.filter("GENDER = 'M'")
    female_patients = patients_table.filter("GENDER = 'F'")
    
    # Verify results
    for patient in male_patients:
        fhir_patient = map_patient(patient)
        assert fhir_patient["gender"] == "male"
```

## Benefits of Table-Based Testing

### ✨ **Clean & Readable**
```python
# Before: Manual dict manipulation
matching_obs = []
for obs in observations:
    if obs.get("PATIENT") == patient_id and obs.get("CATEGORY") == "vital-signs":
        matching_obs.append(obs)

# After: Declarative Table operations  
patient_vitals = observations.filter(f"PATIENT = '{patient_id}' AND CATEGORY = 'vital-signs'")
```

### 🚀 **Powerful Analytics**
```python
# Statistical analysis with Tables
gender_distribution = patients.group_by("GENDER")
unique_loinc_codes = observations.unique("CODE")
avg_obs_per_patient = sum(len(group) for group in obs_by_patient.values()) / len(obs_by_patient)
```

### 🔗 **Consistent Data Model**
- CSV rows and FHIR resources both become Table rows
- Uniform API for filtering, selection, grouping
- Natural handling of sparse/missing healthcare data

## Running Specific Tests

```bash
# Test specific mapper
uv run pytest tests/test_patient_mapping.py::test_patient_core_fields -v

# Test with specific markers
uv run pytest -m "unit and not slow" -v

# Test parametrized cases
uv run pytest -k "gender_mapping" -v

# Show test coverage
uv run pytest --cov=fhir_x_synthea_csv --cov-report=html
```

## Continuous Integration

The test suite is designed to work in CI environments:

```yaml
# Example GitHub Actions
- name: Run unit tests
  run: uv run pytest -m unit --tb=short

- name: Run integration tests  
  run: uv run pytest -m requires_csv --tb=short
  if: ${{ env.HAS_TEST_DATA == 'true' }}
```

## Performance

- **Unit tests**: ~0.02s (6 tests)
- **Full patient tests**: ~0.05s (18 tests)  
- **CSV integration**: ~0.04s (with test data)

The Table-based architecture provides excellent performance for healthcare data processing while maintaining readability and correctness.

---

**Next Steps**: Download test data and run `uv run pytest -v` to see the full validation in action!