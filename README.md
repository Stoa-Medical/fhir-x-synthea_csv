# fhir-x-synthea-csv

This project contains mappings between FHIR and Synthea CSV files.

## Usage

```python
from fhir.resources import Patient
from synthea_pydantic import Patient as SyntheaPatient
from fhir_x_synthea_csv.to_fhir import to_fhir

fhir_patient = Patient()
synthea_patient = SyntheaPatient()
fhir_patient = to_fhir(synthea_patient)
synthea_patient = to_synthea_csv(fhir_patient)
```

## Goals for this repo

On the Synthea downloads page, you can find the same semantic data in both FHIR and Synthea CSV formats. So strictly speaking, you can just import those and apply the pydantic models to the data correctly.

This library is a tool to convert between these two formats in code, and honestly is moreso a demonstrate of the mapping framework introduced in [chidian](https://github.com/ericpan64/chidian).

## Citations

FHIR is a registered trademark of Health Level Seven International.

> HL7 International. FHIR. 2025. https://www.hl7.org/fhir/

Synthea is a registered trademark of The MITRE Corporation.

> Jason Walonoski, Mark Kramer, Joseph Nichols, Andre Quina, Chris Moesel, Dylan Hall, Carlton Duffett, Kudakwashe Dube, Thomas Gallagher, Scott McLachlan, Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record, Journal of the American Medical Informatics Association, Volume 25, Issue 3, March 2018, Pages 230–238, https://doi.org/10.1093/jamia/ocx079
