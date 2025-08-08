# ImagingStudy (FHIR R4 ➜ Synthea imaging_studies.csv)

## Semantic Context
Maps a FHIR R4 `ImagingStudy` resource to a Synthea `imaging_studies.csv` row. Each output row corresponds to one series-instance pair in the FHIR resource.

## Field Mappings
| Target Field | Source Field | Semantic Concept | Transform | Semantic Notes |
|--------------|--------------|------------------|-----------|----------------|
| Id (UUID, required) | `identifier[0].value` | Business identifier of study | Prefer first identifier value; empty if none | FHIR `id` is not used here |
| Date (iso8601 UTC, required) | `started` | Study start datetime | Pass through/normalize | If absent, empty |
| Patient (UUID, required) | `subject.reference` → `Patient/{id}` | Patient reference | Extract `{id}` | |
| Encounter (UUID, required) | `encounter.reference` → `Encounter/{id}` | Encounter reference | Extract `{id}` | |
| Series UID (String, required) | `series[n].uid` | DICOM Series UID | Per series | One row per series-instance |
| Body Site Code (String, required) | `series[n].bodySite.coding[0].code` | Body site (SNOMED) | Prefer SNOMED coding; else first coding | |
| Body Site Description (String, required) | Prefer `coding.display`, else `bodySite.text` | Human-readable body site | As available | |
| Modality Code (String, required) | `series[n].modality.code` | Imaging modality (DICOM) | Prefer DICOM-DCM system; else use `.code` | |
| Modality Description (String, required) | `series[n].modality.display` | Modality display | As available | |
| Instance UID (String, required) | `series[n].instance[m].uid` | DICOM SOP Instance UID | Per instance | |
| SOP Code (String, required) | From `series[n].instance[m].sopClass.code` | SOP Class UID | If value starts with `urn:oid:`, strip prefix; else use as is | |
| SOP Description (String, required) | `series[n].instance[m].sopClass.display` | SOP class display | As available | |
| Procedure Code (String, required) | `procedureCode[0].coding` | Procedure Code (SNOMED) | Prefer SNOMED coding; else first coding `.code` | |

## Accepted FHIR Variants
- If `bodySite.coding` has multiple entries, prefer SNOMED (`http://snomed.info/sct`).
- If `modality` includes system, prefer DICOM-DCM (`http://dicom.nema.org/resources/ontology/DCM`).
- `sopClass.code` may be a full URN (e.g., `urn:oid:1.2.840...`) or just an OID fragment; CSV expects the OID only.

## Implementation Notes
- Multiple output rows are produced by iterating `series` and their `instance` arrays.
- Implementation in `fhir_x_synthea_csv/to_synthea_csv/imaging_study.py`.
