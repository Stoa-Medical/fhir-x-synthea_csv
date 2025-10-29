# fhir-x-synthea-csv

A mapping library between FHIR R4 and Synthea CSV formats, demonstrating the use of the [chidian](https://github.com/ericpan64/chidian) mapping framework for semantic healthcare data transformations.

## Overview

This library provides semantic mappings to convert Synthea CSV data into HL7 FHIR R4 resources. It focuses on preserving clinical meaning while transforming between these two formats.

## Installation

```bash
pip install fhir-x-synthea-csv
```

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
