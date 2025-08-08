# ImagingStudy (Synthea imaging_studies.csv ➜ FHIR R4 ImagingStudy)

## Semantic Context
Maps a single row from Synthea `imaging_studies.csv` to a FHIR R4 `ImagingStudy` resource. Each CSV row represents one series-instance tuple for a study; multiple rows can belong to the same study identifier. This mapping emits an `ImagingStudy` with a single `series` and single `instance` reflecting the row.

## Field Mappings
| Source Field | Target Field | Semantic Concept | Transform | Semantic Notes |
|--------------|--------------|------------------|-----------|----------------|
| Id (UUID, required) | `identifier[0]` | Business identifier of study | Create Identifier with `system` = `urn:synthea:imaging_studies`, `value` = Id | FHIR `id` remains separate and may be generated deterministically |
| Date (iso8601 UTC, required) | `started` | Study start datetime | Normalize to ISO 8601 dateTime | Represents when the study began |
| Patient (UUID, required) | `subject` | Patient reference | `Patient/{Patient}` | |
| Encounter (UUID, required) | `encounter` | Encounter reference | `Encounter/{Encounter}` | |
| Series UID (String, required) | `series[0].uid` | DICOM Series Instance UID | Copy | |
| Body Site Code (String, required) | `series[0].bodySite.coding[0].code` | Body site (SNOMED) | Set `system` = `http://snomed.info/sct`, `code` = Body Site Code, `display` = Body Site Description; also set `text` | |
| Body Site Description (String, required) | `series[0].bodySite.text` and `coding.display` | Human-readable body site | Copy | |
| Modality Code (String, required) | `series[0].modality.code` | Imaging modality (DICOM) | Set `system` = `http://dicom.nema.org/resources/ontology/DCM`, `code` = Modality Code, `display` = Modality Description | |
| Modality Description (String, required) | `series[0].modality.display` | Modality display | Copy | |
| Instance UID (String, required) | `series[0].instance[0].uid` | DICOM SOP Instance UID | Copy | |
| SOP Code (String, required) | `series[0].instance[0].sopClass.code` | SOP Class UID | Output Coding with `system` = `urn:ietf:rfc:3986`, `code` = `urn:oid:{SOP Code}` (prefix if missing), `display` = SOP Description | |
| SOP Description (String, required) | `series[0].instance[0].sopClass.display` | SOP class display | Copy | |
| Procedure Code (String, required) | `procedureCode[0]` | Procedure Code (SNOMED) | CodeableConcept with `system` = `http://snomed.info/sct`, `code` = Procedure Code | |

## Semantic Rules and Constraints
- `ImagingStudy.status` is set to `available`.
- Empty/missing source values are omitted from the target.
- When `SOP Code` already begins with `urn:oid:`, do not add another prefix.

## Implementation Notes
- Deterministic FHIR `id`: `imaging-{Patient}-{Date(clean)}-{Series UID}-{Instance UID}` to correlate rows. Not normative.
- This mapper does not group/aggregate multiple CSV rows into a single multi-series/instance resource by identifier.
- Implementation in `fhir_x_synthea_csv/to_fhir/imaging_study.py`.
