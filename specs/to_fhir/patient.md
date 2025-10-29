# Patient

## Semantic Context
The Patient resource contains demographics and administrative information about an individual receiving care. This mapping transforms Synthea CSV patient data into FHIR R4 Patient resources.

## Field Mappings
```python
# Synthea CSV patients → FHIR Patient mapping
# (source_field, target_field, semantic_concept, transform, notes)
patients_mapping = [
    ("patients.Id", "Patient.id", "Patient Identity", "Direct copy", "Primary identifier"),
    ("patients.Id", "Patient.identifier[0]", "Medical Record Number", "Create identifier object", "System: urn:oid:2.16.840.1.113883.19.5"),
    ("patients.BIRTHDATE", "Patient.birthDate", "Birth Date", "Format as YYYY-MM-DD", "Date of birth"),
    ("patients.DEATHDATE", "Patient.deceasedDateTime", "Death Date/Time", "Format as ISO 8601", "If present, patient is deceased"),
    ("patients.SSN", "Patient.identifier[1]", "Social Security Number", "Create identifier with type \"SS\"", "US SSN"),
    ("patients.DRIVERS", "Patient.identifier[2]", "Driver's License", "Create identifier with type \"DL\"", "State driver's license"),
    ("patients.PASSPORT", "Patient.identifier[3]", "Passport Number", "Create identifier with type \"PPN\"", "Passport identifier"),
    ("patients.PREFIX", "Patient.name[0].prefix", "Name Prefix", "Direct copy as array", "Title/honorific"),
    ("patients.FIRST", "Patient.name[0].given[0]", "First Name", "Direct copy", "Given name"),
    ("patients.LAST", "Patient.name[0].family", "Last Name", "Direct copy", "Family/surname"),
    ("patients.SUFFIX", "Patient.name[0].suffix", "Name Suffix", "Direct copy as array", "Generational suffix"),
    ("patients.MAIDEN", "Patient.name[1]", "Maiden Name", "Create separate name entry with use=\"maiden\"", "Previous name"),
    ("patients.MARITAL", "Patient.maritalStatus", "Marital Status", "Map to CodeableConcept", "S→Single, M→Married, D→Divorced, W→Widowed"),
    ("patients.RACE", "Patient.extension", "US Core Race", "Map to US Core Race extension", "CDC race categories"),
    ("patients.ETHNICITY", "Patient.extension", "US Core Ethnicity", "Map to US Core Ethnicity extension", "Hispanic/Non-Hispanic"),
    ("patients.GENDER", "Patient.gender", "Administrative Gender", "Map M→male, F→female", "Administrative gender"),
    ("patients.BIRTHPLACE", "Patient.extension", "Birth Place", "Create birthPlace extension", "City, State format"),
    ("patients.ADDRESS", "Patient.address[0].line[0]", "Street Address", "Direct copy", "Primary address line"),
    ("patients.CITY", "Patient.address[0].city", "City", "Direct copy", "City name"),
    ("patients.STATE", "Patient.address[0].state", "State", "Direct copy", "State/province code"),
    ("patients.COUNTY", "Patient.address[0].district", "County", "Direct copy", "County/district"),
    ("patients.ZIP", "Patient.address[0].postalCode", "Postal Code", "Direct copy", "ZIP/postal code"),
    ("patients.LAT", "Patient.address[0].extension", "Geolocation", "Create geolocation extension", "Latitude coordinate"),
    ("patients.LON", "Patient.address[0].extension", "Geolocation", "Create geolocation extension", "Longitude coordinate"),
]
```

## Semantic Rules and Constraints
- Patient.name[0].use is set to "official" for primary name
- Patient.address[0].use is set to "home" for primary address
- If DEATHDATE is present, set Patient.deceasedDateTime; otherwise Patient.deceasedBoolean = false
- All identifiers should include appropriate type coding from HL7 v2 Table 0203
- Race and ethnicity use US Core profile extensions
- Gender mapping follows FHIR administrative gender (not clinical sex)

## Implementation Notes
- Function: `fhir_x_synthea_csv.to_fhir.patient.patient_mapper`
- Uses chidian Mapper with DataMapping wrapper
- Leverages common transformers for date formatting
- Uses lexicons for gender and marital status mappings
- Handles missing/null values gracefully with skip_none=True
