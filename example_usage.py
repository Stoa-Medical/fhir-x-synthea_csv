"""
Example usage of the FHIR x Synthea CSV mapping library.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from fhir_x_synthea_csv.to_fhir import (
    map_patient,
    map_observation,
    map_condition,
)


def load_csv_as_dict(csv_content: str, headers: List[str]) -> List[Dict[str, str]]:
    """
    Simple CSV parser for demonstration.
    In production, use pandas or csv.DictReader.
    """
    rows = []
    lines = csv_content.strip().split('\n')
    
    # Skip header if present
    if lines and lines[0].startswith(headers[0]):
        lines = lines[1:]
    
    for line in lines:
        if line:
            values = line.split(',')
            row = {header: value for header, value in zip(headers, values)}
            rows.append(row)
    
    return rows


def demo_patient_mapping():
    """Demonstrate patient mapping."""
    print("=" * 60)
    print("PATIENT MAPPING DEMO")
    print("=" * 60)
    
    # Sample Synthea patient CSV data
    sample_patient = {
        "Id": "b8b9c8d1-9821-4e1f-8f3a-2c1d3e4f5a6b",
        "BIRTHDATE": "1985-03-15",
        "DEATHDATE": "",
        "SSN": "999-12-3456",
        "DRIVERS": "S99998765",
        "PASSPORT": "X12345678X",
        "PREFIX": "Mr.",
        "FIRST": "John",
        "LAST": "Smith",
        "SUFFIX": "Jr.",
        "MAIDEN": "",
        "MARITAL": "M",
        "RACE": "white",
        "ETHNICITY": "nonhispanic",
        "GENDER": "M",
        "BIRTHPLACE": "Boston, Massachusetts",
        "ADDRESS": "123 Main Street",
        "CITY": "Boston",
        "STATE": "MA",
        "COUNTY": "Suffolk County",
        "ZIP": "02101",
        "LAT": "42.3601",
        "LON": "-71.0589",
    }
    
    print("\nInput (Synthea CSV):")
    print(json.dumps(sample_patient, indent=2))
    
    # Map to FHIR
    fhir_patient = map_patient(sample_patient)
    
    print("\nOutput (FHIR Patient):")
    print(json.dumps(fhir_patient, indent=2))
    
    return fhir_patient


def demo_observation_mapping():
    """Demonstrate observation mapping."""
    print("\n" + "=" * 60)
    print("OBSERVATION MAPPING DEMO")
    print("=" * 60)
    
    # Sample vital sign observation
    sample_observation_vital = {
        "DATE": "2024-01-15 10:30:00",
        "PATIENT": "b8b9c8d1-9821-4e1f-8f3a-2c1d3e4f5a6b",
        "ENCOUNTER": "enc-123456",
        "CODE": "8302-2",
        "DESCRIPTION": "Body Height",
        "VALUE": "175",
        "UNITS": "cm",
        "TYPE": "vital-signs",
    }
    
    print("\nInput (Synthea CSV - Vital Sign):")
    print(json.dumps(sample_observation_vital, indent=2))
    
    fhir_observation_vital = map_observation(sample_observation_vital)
    
    print("\nOutput (FHIR Observation - Vital Sign):")
    print(json.dumps(fhir_observation_vital, indent=2))
    
    # Sample lab observation
    sample_observation_lab = {
        "DATE": "2024-01-15 11:00:00",
        "PATIENT": "b8b9c8d1-9821-4e1f-8f3a-2c1d3e4f5a6b",
        "ENCOUNTER": "enc-123456",
        "CODE": "2093-3",
        "DESCRIPTION": "Cholesterol [Mass/volume] in Serum or Plasma",
        "VALUE": "195",
        "UNITS": "mg/dL",
        "TYPE": "laboratory",
    }
    
    print("\nInput (Synthea CSV - Lab Result):")
    print(json.dumps(sample_observation_lab, indent=2))
    
    fhir_observation_lab = map_observation(sample_observation_lab)
    
    print("\nOutput (FHIR Observation - Lab Result):")
    print(json.dumps(fhir_observation_lab, indent=2))
    
    return fhir_observation_vital, fhir_observation_lab


def demo_condition_mapping():
    """Demonstrate condition mapping."""
    print("\n" + "=" * 60)
    print("CONDITION MAPPING DEMO")
    print("=" * 60)
    
    # Sample active condition
    sample_condition_active = {
        "START": "2023-06-01 14:00:00",
        "STOP": "",  # No stop date = active
        "PATIENT": "b8b9c8d1-9821-4e1f-8f3a-2c1d3e4f5a6b",
        "ENCOUNTER": "enc-789012",
        "CODE": "44054006",
        "DESCRIPTION": "Diabetes mellitus type 2 (disorder)",
    }
    
    print("\nInput (Synthea CSV - Active Condition):")
    print(json.dumps(sample_condition_active, indent=2))
    
    fhir_condition_active = map_condition(sample_condition_active)
    
    print("\nOutput (FHIR Condition - Active):")
    print(json.dumps(fhir_condition_active, indent=2))
    
    # Sample resolved condition
    sample_condition_resolved = {
        "START": "2023-01-10 09:00:00",
        "STOP": "2023-02-15 10:30:00",  # Has stop date = resolved
        "PATIENT": "b8b9c8d1-9821-4e1f-8f3a-2c1d3e4f5a6b",
        "ENCOUNTER": "enc-345678",
        "CODE": "233604007",
        "DESCRIPTION": "Pneumonia (disorder)",
    }
    
    print("\nInput (Synthea CSV - Resolved Condition):")
    print(json.dumps(sample_condition_resolved, indent=2))
    
    fhir_condition_resolved = map_condition(sample_condition_resolved)
    
    print("\nOutput (FHIR Condition - Resolved):")
    print(json.dumps(fhir_condition_resolved, indent=2))
    
    return fhir_condition_active, fhir_condition_resolved


def demo_bundle_creation():
    """Demonstrate creating a FHIR Bundle with multiple resources."""
    print("\n" + "=" * 60)
    print("FHIR BUNDLE CREATION DEMO")
    print("=" * 60)
    
    # Create individual resources
    patient = demo_patient_mapping()
    vital, lab = demo_observation_mapping()
    active_cond, resolved_cond = demo_condition_mapping()
    
    # Create a FHIR Bundle
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": "2024-01-15T12:00:00+00:00",
        "entry": [
            {"resource": patient},
            {"resource": vital},
            {"resource": lab},
            {"resource": active_cond},
            {"resource": resolved_cond},
        ],
    }
    
    print("\n" + "=" * 60)
    print("FINAL FHIR BUNDLE")
    print("=" * 60)
    print(f"Bundle contains {len(bundle['entry'])} resources:")
    for i, entry in enumerate(bundle['entry'], 1):
        resource = entry['resource']
        print(f"  {i}. {resource['resourceType']} (id: {resource.get('id', 'N/A')})")
    
    # Save bundle to file for inspection
    output_file = Path("example_bundle.json")
    with open(output_file, "w") as f:
        json.dump(bundle, f, indent=2)
    
    print(f"\nBundle saved to: {output_file}")
    
    return bundle


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("FHIR x SYNTHEA CSV MAPPING DEMONSTRATION")
    print("Using the chidian mapping framework")
    print("=" * 60)
    
    # Run demos
    bundle = demo_bundle_creation()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nThis demo showed:")
    print("1. Patient resource mapping (demographics, identifiers, address)")
    print("2. Observation resource mapping (vital signs, lab results)")
    print("3. Condition resource mapping (active and resolved conditions)")
    print("4. Bundle creation with multiple resources")
    print("\nThe mappings preserve semantic meaning while transforming between")
    print("Synthea CSV format and HL7 FHIR R4 resources.")


if __name__ == "__main__":
    main()