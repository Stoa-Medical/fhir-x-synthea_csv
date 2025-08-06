# fhir-x-synthea-csv

A mapping library between FHIR R4 and Synthea CSV formats, demonstrating the use of the [chidian](https://github.com/ericpan64/chidian) mapping framework for semantic healthcare data transformations.

## Overview

This library provides semantic mappings to convert Synthea CSV data into HL7 FHIR R4 resources. It focuses on preserving clinical meaning while transforming between these two formats.

### Supported Resources

- **Patient**: Demographics, identifiers, addresses with US Core extensions
- **Observation**: Vital signs, laboratory results with proper categorization  
- **Condition**: Diagnoses with SNOMED CT codes and clinical status

## Installation

```bash
pip install fhir-x-synthea-csv
```

## Quick Start

```python
from fhir_x_synthea_csv.to_fhir import (
    map_patient,
    map_observation,
    map_condition,
)

# Transform individual resources
synthea_patient_data = {...}  # From patients.csv
fhir_patient = map_patient(synthea_patient_data)

synthea_observation_data = {...}  # From observations.csv  
fhir_observation = map_observation(synthea_observation_data)

synthea_condition_data = {...}  # From conditions.csv
fhir_condition = map_condition(synthea_condition_data)
```

## Example Usage

Run the demonstration:

```bash
python example_usage.py
```

This creates a complete FHIR Bundle with Patient, Observation, and Condition resources, showing the semantic transformations in action.

## Key Features

- **Semantic Preservation**: Maintains clinical meaning during transformation
- **Standards Compliance**: Uses proper FHIR R4 resource structures
- **Terminology Mapping**: SNOMED CT, LOINC, US Core extensions
- **chidian Integration**: Demonstrates the chidian mapping framework

## Mapping Specifications

Detailed mapping specifications are in the `specs/` directory:
- [`specs/to_fhir/patient.md`](specs/to_fhir/patient.md)
- [`specs/to_fhir/observation.md`](specs/to_fhir/observation.md)  
- [`specs/to_fhir/condition.md`](specs/to_fhir/condition.md)

## Goals

This repository serves as:

1. **Demonstration**: Shows how to use chidian for healthcare data mapping
2. **QA Tool**: Validates semantic correctness by comparing Synthea's CSV and FHIR outputs
3. **Reference Implementation**: Provides patterns for healthcare data transformation

## Citations

FHIR is a registered trademark of Health Level Seven International.

> HL7 International. FHIR. 2025. https://www.hl7.org/fhir/

Synthea is a registered trademark of The MITRE Corporation.

> Jason Walonoski, Mark Kramer, Joseph Nichols, Andre Quina, Chris Moesel, Dylan Hall, Carlton Duffett, Kudakwashe Dube, Thomas Gallagher, Scott McLachlan, Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record, Journal of the American Medical Informatics Association, Volume 25, Issue 3, March 2018, Pages 230–238, https://doi.org/10.1093/jamia/ocx079
