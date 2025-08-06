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
