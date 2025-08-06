"""
Terminology mappings and lexicons for FHIR-Synthea CSV conversions.
"""

from chidian.lexicon import Lexicon


# Gender mapping between Synthea and FHIR
gender_lexicon = Lexicon(
    mappings={
        "M": "male",
        "F": "female",
        "O": "other",
        "U": "unknown",
    },
    default="unknown",
)

# Simple dictionary-based mappings for complex objects
# Using regular dicts since Lexicon seems to be for simple string mappings

marital_status_mapping = {
    "S": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                "code": "S",
                "display": "Never Married",
            }
        ],
        "text": "Never Married",
    },
    "M": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                "code": "M",
                "display": "Married",
            }
        ],
        "text": "Married",
    },
    "D": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                "code": "D",
                "display": "Divorced",
            }
        ],
        "text": "Divorced",
    },
    "W": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                "code": "W",
                "display": "Widowed",
            }
        ],
        "text": "Widowed",
    },
}

# Create a simple wrapper class for consistency
class MappingDict:
    def __init__(self, mappings, default=None):
        self.mappings = mappings
        self.default = default
    
    def forward_get(self, key):
        return self.mappings.get(key, self.default)
    
    def get(self, key):
        return self.forward_get(key)

marital_status_lexicon = MappingDict(marital_status_mapping)

# Encounter class mapping
encounter_class_mapping = {
    "ambulatory": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory",
    },
    "emergency": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "EMER",
        "display": "emergency",
    },
    "inpatient": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "IMP",
        "display": "inpatient encounter",
    },
    "urgentcare": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "ACUTE",
        "display": "inpatient acute",
    },
    "wellness": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory",
    },
    "outpatient": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory",
    },
}

encounter_class_lexicon = MappingDict(
    encounter_class_mapping,
    default={
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory",
    },
)

# Race mapping
race_mapping = {
    "white": {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": "2106-3",
                    "display": "White",
                },
            },
            {"url": "text", "valueString": "White"},
        ],
    },
    "black": {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": "2054-5",
                    "display": "Black or African American",
                },
            },
            {"url": "text", "valueString": "Black or African American"},
        ],
    },
    "asian": {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": "2028-9",
                    "display": "Asian",
                },
            },
            {"url": "text", "valueString": "Asian"},
        ],
    },
    "native": {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": "1002-5",
                    "display": "American Indian or Alaska Native",
                },
            },
            {"url": "text", "valueString": "American Indian or Alaska Native"},
        ],
    },
    "hawaiian": {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": "2076-8",
                    "display": "Native Hawaiian or Other Pacific Islander",
                },
            },
            {
                "url": "text",
                "valueString": "Native Hawaiian or Other Pacific Islander",
            },
        ],
    },
    "other": {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": "2131-1",
                    "display": "Other Race",
                },
            },
            {"url": "text", "valueString": "Other"},
        ],
    },
}

race_lexicon = MappingDict(race_mapping)

# Ethnicity mapping
ethnicity_mapping = {
    "hispanic": {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": "2135-2",
                    "display": "Hispanic or Latino",
                },
            },
            {"url": "text", "valueString": "Hispanic or Latino"},
        ],
    },
    "nonhispanic": {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": "2186-5",
                    "display": "Not Hispanic or Latino",
                },
            },
            {"url": "text", "valueString": "Not Hispanic or Latino"},
        ],
    },
}

ethnicity_lexicon = MappingDict(ethnicity_mapping)