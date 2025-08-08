### FHIR R4 Organization ➜ Synthea organizations.csv

This spec defines how a FHIR R4 `Organization` resource for providers maps back to a Synthea `organizations.csv` row.

## Field Mappings

| Target Field | Source | Transform/Notes |
|--------------|--------|-----------------|
| Id | Organization.id | Required |
| Name | Organization.name | Required |
| Address | Organization.address[0].line[0] | Optional |
| City | Organization.address[0].city | Optional |
| State | Organization.address[0].state | Optional |
| Zip | Organization.address[0].postalCode | Optional |
| Lat | Organization.address[0].extension url=`http://hl7.org/fhir/StructureDefinition/geolocation` → `latitude` | Extract `valueDecimal`; stringify |
| Lon | Organization.address[0].extension url=`http://hl7.org/fhir/StructureDefinition/geolocation` → `longitude` | Extract `valueDecimal`; stringify |
| Phone | Organization.telecom where `system=phone` | Join multiple values with `; ` |
| Revenue | Organization.extension url=`http://synthea.mitre.org/fhir/StructureDefinition/organization-stats` → subext `revenue` | valueDecimal; stringify |
| Utilization | Organization.extension url=`http://synthea.mitre.org/fhir/StructureDefinition/organization-stats` → subext `utilization` | valueInteger; stringify |

## Notes
- If fields are missing in FHIR, output empty strings to preserve CSV schema.
- If no geolocation extension is present, `Lat` and `Lon` are empty.
- If multiple phone numbers are present, join with `; ` in the CSV.


