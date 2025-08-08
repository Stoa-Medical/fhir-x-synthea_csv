### FHIR R4 Organization ➜ Synthea payers.csv

This spec defines how a FHIR R4 `Organization` resource representing a payer maps back to a Synthea `payers.csv` row. Aggregate/statistical fields are expected in a custom extension.

## Field Mappings

| Target Field | Source | Notes |
|--------------|--------|-------|
| Id | Organization.id | Required |
| Name | Organization.name | Required |
| Ownership | Organization.extension url=`http://synthea.mitre.org/fhir/StructureDefinition/payer-ownership` → valueCode | Optional; if missing, output empty string |
| Address | Organization.address[0].line[0] | Optional |
| City | Organization.address[0].city | Optional |
| State_Headquartered | Organization.address[0].state | Optional |
| Zip | Organization.address[0].postalCode | Optional |
| Phone | Organization.telecom where system=`phone` → join values with `; ` | Optional |

## Aggregate Statistics (Custom Extension)

Expect a top-level Organization extension at URL `http://synthea.mitre.org/fhir/StructureDefinition/payer-stats`. If present, extract the following sub-extensions into the corresponding CSV fields. If absent, output empty strings for required numeric fields to preserve CSV schema.

| CSV Field | Sub-extension url | Value |
|-----------|-------------------|-------|
| Amount_Covered | amountCovered | valueDecimal (stringified) |
| Amount_Uncovered | amountUncovered | valueDecimal |
| Revenue | revenue | valueDecimal |
| Covered_Encounters | coveredEncounters | valueInteger (string) |
| Uncovered_Encounters | uncoveredEncounters | valueInteger |
| Covered_Medications | coveredMedications | valueInteger |
| Uncovered_Medications | uncoveredMedications | valueInteger |
| Covered_Procedures | coveredProcedures | valueInteger |
| Uncovered_Procedures | uncoveredProcedures | valueInteger |
| Covered_Immunizations | coveredImmunizations | valueInteger |
| Uncovered_Immunizations | uncoveredImmunizations | valueInteger |
| Unique_Customers | uniqueCustomers | valueInteger |
| QOLS_Avg | qolsAvg | valueDecimal |
| Member_Months | memberMonths | valueInteger |

Values should be stringified without additional formatting. Missing values should be rendered as empty strings.


