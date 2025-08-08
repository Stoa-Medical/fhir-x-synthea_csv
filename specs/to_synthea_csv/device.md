# Device

## Semantic Context
Maps FHIR R4 `Device` resources to Synthea `devices.csv`. The CSV captures a patient association window, encounter context, device type (SNOMED), description, and UDI.

## Field Mappings
| Source Field | Target Field | Semantic Concept | Transform | Semantic Notes |
|--------------|--------------|------------------|-----------|----------------|
| `Device.extension[url="http://synthea.tools/fhir/StructureDefinition/device-use-period"].valuePeriod.start` OR `Device.meta.lastUpdated` fallback | START | Association start | Parse FHIR datetime to Synthea datetime | Prefer explicit use-period.start; if absent, leave empty if unknown |
| `Device.extension[url="http://synthea.tools/fhir/StructureDefinition/device-use-period"].valuePeriod.end` | STOP | Association end | Parse FHIR datetime to Synthea datetime | Optional |
| `Device.patient.reference` | PATIENT | Device subject | Extract `Patient/{id}` → `{id}` | Required |
| `Device.extension[url="http://hl7.org/fhir/StructureDefinition/resource-encounter"].valueReference` | ENCOUNTER | Encounter | Extract `Encounter/{id}` → `{id}` | Optional; Synthea dictionary marks it required, but may be absent in general FHIR |
| `Device.type` (SNOMED) | CODE | Device type | Extract SNOMED coding code | Fall back to first available coding |
| `Device.type.text` or `coding.display` | DESCRIPTION | Description | Copy | Prefer display, fallback to text |
| `Device.udiCarrier[0].deviceIdentifier` or `carrierHRF` | UDI | Unique Device Identifier | Copy | Prefer deviceIdentifier; fallback to carrierHRF |

## Semantic Rules and Constraints
- Derive START/STOP only from the explicit period extension defined by this toolkit; absence yields empty values.
- SNOMED CT preferred for `CODE`.
- If both `deviceIdentifier` and `carrierHRF` exist, use `deviceIdentifier`.

## Implementation Notes
- Keep output strings; convert None to empty strings for CSV compatibility.
- Do not infer values beyond the available resource content to avoid semantic drift.
