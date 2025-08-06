"""
Test cases for Observation resource mapping using chidian Tables.
"""

import unittest
from pathlib import Path

from chidian import Table

from fhir_x_synthea_csv.to_fhir import map_observation
from .loaders import (
    load_observations_csv,
    get_patient_bundle_table,
    get_patient_resources,
    get_csv_patient_observations,
)
from .validators import assert_observation_equivalence


class TestObservationMapping(unittest.TestCase):
    """Test Observation CSV to FHIR mapping."""
    
    @classmethod
    def setUpClass(cls):
        """Load test data once for all tests."""
        cls.observations_csv = load_observations_csv()
        cls.test_patient_id = "8c8e1c9a-b310-43c6-33a7-ad11bad21c40"  # Britt177
    
    def test_observation_mapping_vital_signs(self):
        """Test mapping for vital sign observations."""
        # Get CSV observations for the patient
        patient_obs_csv = get_csv_patient_observations(
            self.observations_csv, 
            self.test_patient_id
        )
        
        # Filter to vital signs only
        vital_signs_csv = patient_obs_csv.filter("CATEGORY = 'vital-signs'")
        self.assertGreater(len(vital_signs_csv), 0, "No vital signs found")
        
        # Get first vital sign for detailed testing
        first_vital = None
        for obs in vital_signs_csv.head(1):
            first_vital = obs
            break
        
        self.assertIsNotNone(first_vital)
        
        # Transform using our mapper
        our_fhir_obs = map_observation(first_vital)
        self.assertIsNotNone(our_fhir_obs)
        self.assertEqual(our_fhir_obs["resourceType"], "Observation")
        
        # Verify core fields
        self.assertEqual(our_fhir_obs["status"], "final")
        self.assertIn("code", our_fhir_obs)
        self.assertIn("effectiveDateTime", our_fhir_obs)
        self.assertIn("subject", our_fhir_obs)
        
        # Verify subject reference
        self.assertEqual(
            our_fhir_obs["subject"]["reference"],
            f"Patient/{self.test_patient_id}"
        )
        
        # Verify category
        self.assertIn("category", our_fhir_obs)
        self.assertEqual(len(our_fhir_obs["category"]), 1)
        category = our_fhir_obs["category"][0]
        self.assertEqual(
            category["coding"][0]["code"],
            "vital-signs"
        )
    
    def test_observation_value_types(self):
        """Test different value types in observations."""
        patient_obs_csv = get_csv_patient_observations(
            self.observations_csv,
            self.test_patient_id
        )
        
        # Test numeric value with units
        numeric_obs = patient_obs_csv.filter("CODE = '8302-2'")  # Body Height
        for obs in numeric_obs.head(1):
            our_fhir = map_observation(obs)
            
            # Should have valueQuantity
            self.assertIn("valueQuantity", our_fhir)
            value_qty = our_fhir["valueQuantity"]
            
            self.assertIn("value", value_qty)
            self.assertIn("unit", value_qty)
            self.assertIn("code", value_qty)
            self.assertIn("system", value_qty)
            
            # Check UCUM system
            self.assertEqual(value_qty["system"], "http://unitsofmeasure.org")
            break
    
    def test_observation_loinc_codes(self):
        """Test that LOINC codes are preserved correctly."""
        patient_obs_csv = get_csv_patient_observations(
            self.observations_csv,
            self.test_patient_id
        )
        
        # Get observations with known LOINC codes
        loinc_codes = {
            "8302-2": "Body Height",
            "29463-7": "Body Weight",
            "8480-6": "Systolic Blood Pressure",
            "8462-4": "Diastolic Blood Pressure"
        }
        
        for loinc_code, description in loinc_codes.items():
            obs_table = patient_obs_csv.filter(f"CODE = '{loinc_code}'")
            
            if len(obs_table) > 0:
                for obs in obs_table.head(1):
                    our_fhir = map_observation(obs)
                    
                    # Check LOINC coding
                    self.assertIn("code", our_fhir)
                    codings = our_fhir["code"]["coding"]
                    self.assertGreater(len(codings), 0)
                    
                    loinc_coding = codings[0]
                    self.assertEqual(loinc_coding["system"], "http://loinc.org")
                    self.assertEqual(loinc_coding["code"], loinc_code)
                    self.assertIn(description, loinc_coding.get("display", ""))
                    break
    
    def test_observation_categories(self):
        """Test that observation categories are mapped correctly."""
        # Test different category mappings
        category_mappings = {
            "vital-signs": "vital-signs",
            "laboratory": "laboratory",
            "survey": "survey",
            "social-history": "social-history"
        }
        
        for csv_category, fhir_category in category_mappings.items():
            # Find observations with this category
            category_obs = self.observations_csv.filter(f"CATEGORY = '{csv_category}'")
            
            if len(category_obs) > 0:
                for obs in category_obs.head(1):
                    our_fhir = map_observation(obs)
                    
                    self.assertIn("category", our_fhir)
                    categories = our_fhir["category"]
                    self.assertGreater(len(categories), 0)
                    
                    cat_coding = categories[0]["coding"][0]
                    self.assertEqual(cat_coding["code"], fhir_category)
                    self.assertEqual(
                        cat_coding["system"],
                        "http://terminology.hl7.org/CodeSystem/observation-category"
                    )
                    break
    
    def test_observation_with_encounter(self):
        """Test that encounter references are included."""
        patient_obs_csv = get_csv_patient_observations(
            self.observations_csv,
            self.test_patient_id
        )
        
        # Find observation with encounter
        for obs in patient_obs_csv.head(5):
            if obs.get("ENCOUNTER"):
                our_fhir = map_observation(obs)
                
                self.assertIn("encounter", our_fhir)
                self.assertEqual(
                    our_fhir["encounter"]["reference"],
                    f"Encounter/{obs['ENCOUNTER']}"
                )
                break
    
    def test_observation_datetime_format(self):
        """Test that datetime formatting is correct."""
        patient_obs_csv = get_csv_patient_observations(
            self.observations_csv,
            self.test_patient_id
        )
        
        for obs in patient_obs_csv.head(1):
            our_fhir = map_observation(obs)
            
            # Check effectiveDateTime format
            self.assertIn("effectiveDateTime", our_fhir)
            dt_str = our_fhir["effectiveDateTime"]
            
            # Should be ISO 8601 format with timezone
            self.assertRegex(
                dt_str,
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}'
            )
            
            # Check issued datetime
            self.assertIn("issued", our_fhir)
            self.assertEqual(our_fhir["issued"], dt_str)
            break
    
    def test_table_grouping_observations(self):
        """Test using Table group_by for observations."""
        # Group observations by patient
        obs_by_patient = self.observations_csv.group_by("PATIENT")
        
        # Should have multiple patients
        self.assertGreater(len(obs_by_patient), 0)
        
        # Check our test patient's group
        if self.test_patient_id in obs_by_patient:
            patient_group = obs_by_patient[self.test_patient_id]
            self.assertIsInstance(patient_group, Table)
            self.assertGreater(len(patient_group), 0)
            
            # All observations should be for the same patient
            for obs in patient_group:
                self.assertEqual(obs["PATIENT"], self.test_patient_id)
    
    def test_table_unique_codes(self):
        """Test extracting unique LOINC codes using Table."""
        patient_obs_csv = get_csv_patient_observations(
            self.observations_csv,
            self.test_patient_id
        )
        
        # Get unique codes
        unique_codes = patient_obs_csv.unique("CODE")
        
        self.assertIsInstance(unique_codes, list)
        self.assertGreater(len(unique_codes), 0)
        
        # All should be valid LOINC-like codes
        for code in unique_codes:
            if code:  # Skip None values
                # LOINC codes typically have format like "8302-2"
                self.assertRegex(code, r'^\d+(-\d+)?$')
    
    def test_observation_comparison_with_synthea(self):
        """Test comparing our mapped observation with Synthea's FHIR output."""
        # Get CSV observations
        patient_obs_csv = get_csv_patient_observations(
            self.observations_csv,
            self.test_patient_id
        )
        
        # Get Synthea's FHIR bundle
        synthea_bundle_table = get_patient_bundle_table(self.test_patient_id)
        
        if synthea_bundle_table:
            # Get observations from FHIR bundle
            synthea_obs = get_patient_resources(
                synthea_bundle_table,
                self.test_patient_id,
                "Observation"
            )
            
            if len(synthea_obs) > 0 and len(patient_obs_csv) > 0:
                # Compare first observation
                for csv_obs in patient_obs_csv.head(1):
                    our_fhir = map_observation(csv_obs)
                    
                    # Find matching Synthea observation by code and date
                    our_code = our_fhir["code"]["coding"][0]["code"]
                    
                    for synthea_ob in synthea_obs:
                        synthea_code = synthea_ob.get("code", {}).get("coding", [{}])[0].get("code")
                        if synthea_code == our_code:
                            result = assert_observation_equivalence(our_fhir, synthea_ob)
                            
                            # Print comparison for debugging
                            if not result["valid"] or result["warnings"]:
                                print(f"\nObservation {our_code} comparison:")
                                print(f"  Matches: {result['matches']}")
                                if result["errors"]:
                                    print(f"  Errors: {result['errors']}")
                                if result["warnings"]:
                                    print(f"  Warnings: {result['warnings']}")
                            
                            break
                    break


if __name__ == "__main__":
    unittest.main()