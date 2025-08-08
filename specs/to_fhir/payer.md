### Synthea payers.csv ➜ FHIR R4 Organization (plus extensions)

This spec defines how a Synthea `payers.csv` row maps to a FHIR R4 `Organization` resource representing the payer entity. Aggregate/statistical fields are represented via a custom extension, since they are not first-class Organization attributes.

## Field Mappings

| Source Field | Target Field | Notes |
|--------------|--------------|-------|
| payers.Id | Organization.id | Required primary key (UUID) |
| payers.Name | Organization.name | Required payer display name |
| payers.Ownership | Organization.extension url=`http://synthea.mitre.org/fhir/StructureDefinition/payer-ownership` valueCode | Values such as "Government" or "Private"; case-insensitive mapping; stored as lowercase code in extension |
| payers.Address | Organization.address[0].line[0] | Optional street address |
| payers.City | Organization.address[0].city | Optional city |
| payers.State_Headquartered | Organization.address[0].state | Optional state/province (US state abbreviation) |
| payers.Zip | Organization.address[0].postalCode | Optional postal code |
| payers.Phone | Organization.telecom[n].system=`phone`, value | Split multiple numbers on `[,;/|]` and trim |

In addition, the Organization will include `type` with a coding of Insurance Company for broader categorization:

- Organization.type[0].coding[0]: system=`http://terminology.hl7.org/CodeSystem/organization-type`, code=`ins`, display=`Insurance Company`

## Aggregate Statistics (Custom Extension)

All numeric/statistical columns are mapped into a single extension on the Organization with nested sub-extensions. URL: `http://synthea.mitre.org/fhir/StructureDefinition/payer-stats`.

| Source Field | Sub-extension url | FHIR value[x] |
|--------------|-------------------|---------------|
| Amount_Covered | amountCovered | valueDecimal |
| Amount_Uncovered | amountUncovered | valueDecimal |
| Revenue | revenue | valueDecimal |
| Covered_Encounters | coveredEncounters | valueInteger |
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

Only present sub-extensions are included.

## Semantic Notes

- The payer entity is captured as `Organization`. Specific offerings would be modeled with `InsurancePlan`, and patient enrollment under a plan with `Coverage`. The CSV does not contain per-plan/enrollment records, so those resources are not directly produced here.
- Aggregate statistics are not standard elements and therefore are placed into a custom extension as described above.
- Ownership is stored as an extension to preserve the original Synthea semantics. A separate `type` coding of insurance company is included to broadly classify the organization.


