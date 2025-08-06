"""
Test cases for Condition resource mapping using chidian Tables.
"""

import unittest
from pathlib import Path

from chidian import Table

from fhir_x_synthea_csv.to_fhir import map_condition
from .loaders import (
    load_conditions_csv,
    get_patient_bundle_table,
    get_patient_resources,
    get_csv_patient_conditions,
)
from .validators import assert_condition_equivalence


class TestConditionMapping(unittest.TestCase):
    """Test Condition CSV to FHIR mapping."""
    
    @classmethod
    def setUpClass(cls):
        """Load test data once for all tests."""
        cls.conditions_csv = load_conditions_csv()
        cls.test_patient_id = "8c8e1c9a-b310-43c6-33a7-ad11bad21c40"  # Britt177
    
    def test_condition_mapping_basic(self):
        """Test basic condition mapping."""
        # Get CSV conditions for the patient
        patient_cond_csv = get_csv_patient_conditions(
            self.conditions_csv,
            self.test_patient_id
        )
        
        self.assertGreater(len(patient_cond_csv), 0, "No conditions found for patient")
        
        # Get first condition for detailed testing
        first_condition = None
        for cond in patient_cond_csv.head(1):
            first_condition = cond
            break
        
        self.assertIsNotNone(first_condition)
        
        # Transform using our mapper
        our_fhir_cond = map_condition(first_condition)
        self.assertIsNotNone(our_fhir_cond)
        self.assertEqual(our_fhir_cond["resourceType"], "Condition")
        
        # Verify core fields
        self.assertIn("clinicalStatus", our_fhir_cond)
        self.assertIn("verificationStatus", our_fhir_cond)
        self.assertIn("code", our_fhir_cond)
        self.assertIn("subject", our_fhir_cond)
        self.assertIn("onsetDateTime", our_fhir_cond)
        
        # Verify subject reference
        self.assertEqual(
            our_fhir_cond["subject"]["reference"],
            f"Patient/{self.test_patient_id}"
        )
    
    def test_condition_clinical_status(self):
        """Test that clinical status is determined correctly."""
        patient_cond_csv = get_csv_patient_conditions(
            self.conditions_csv,
            self.test_patient_id
        )
        
        # Find active condition (no STOP date)
        active_condition = None
        for cond in patient_cond_csv:
            if not cond.get("STOP"):
                active_condition = cond
                break
        
        if active_condition:
            our_fhir = map_condition(active_condition)
            clinical_status = our_fhir["clinicalStatus"]["coding"][0]
            self.assertEqual(clinical_status["code"], "active")
            self.assertNotIn("abatementDateTime", our_fhir)
        
        # Find resolved condition (has STOP date)
        resolved_condition = None
        for cond in patient_cond_csv:
            if cond.get("STOP"):
                resolved_condition = cond
                break
        
        if resolved_condition:
            our_fhir = map_condition(resolved_condition)
            clinical_status = our_fhir["clinicalStatus"]["coding"][0]
            self.assertEqual(clinical_status["code"], "resolved")
            self.assertIn("abatementDateTime", our_fhir)
    
    def test_condition_snomed_codes(self):
        """Test that SNOMED codes are preserved correctly."""
        patient_cond_csv = get_csv_patient_conditions(
            self.conditions_csv,
            self.test_patient_id
        )
        
        for cond in patient_cond_csv.head(3):
            our_fhir = map_condition(cond)
            
            # Check SNOMED coding
            self.assertIn("code", our_fhir)
            codings = our_fhir["code"]["coding"]
            self.assertGreater(len(codings), 0)
            
            snomed_coding = codings[0]
            self.assertEqual(snomed_coding["system"], "http://snomed.info/sct")
            self.assertEqual(snomed_coding["code"], cond["CODE"])
            self.assertEqual(snomed_coding["display"], cond["DESCRIPTION"])
    
    def test_condition_verification_status(self):
        """Test that verification status is always confirmed."""
        patient_cond_csv = get_csv_patient_conditions(
            self.conditions_csv,
            self.test_patient_id
        )
        
        for cond in patient_cond_csv.head(3):
            our_fhir = map_condition(cond)
            
            self.assertIn("verificationStatus", our_fhir)
            ver_status = our_fhir["verificationStatus"]["coding"][0]
            self.assertEqual(ver_status["code"], "confirmed")
            self.assertEqual(
                ver_status["system"],
                "http://terminology.hl7.org/CodeSystem/condition-ver-status"
            )
    
    def test_condition_category(self):
        """Test that condition category is set correctly."""
        patient_cond_csv = get_csv_patient_conditions(
            self.conditions_csv,
            self.test_patient_id
        )
        
        for cond in patient_cond_csv.head(1):
            our_fhir = map_condition(cond)
            
            self.assertIn("category", our_fhir)
            categories = our_fhir["category"]
            self.assertEqual(len(categories), 1)
            
            category = categories[0]["coding"][0]
            self.assertEqual(category["code"], "encounter-diagnosis")
            self.assertEqual(
                category["system"],
                "http://terminology.hl7.org/CodeSystem/condition-category"
            )
            break
    
    def test_condition_dates(self):
        """Test onset and abatement date formatting."""
        patient_cond_csv = get_csv_patient_conditions(
            self.conditions_csv,
            self.test_patient_id
        )
        
        # Find condition with both START and STOP
        for cond in patient_cond_csv:
            if cond.get("START") and cond.get("STOP"):
                our_fhir = map_condition(cond)
                
                # Check onset
                self.assertIn("onsetDateTime", our_fhir)
                onset = our_fhir["onsetDateTime"]
                self.assertRegex(
                    onset,
                    r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}'
                )
                
                # Check abatement
                self.assertIn("abatementDateTime", our_fhir)
                abatement = our_fhir["abatementDateTime"]
                self.assertRegex(
                    abatement,
                    r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}'
                )
                break
    
    def test_condition_id_generation(self):
        """Test that condition IDs are generated consistently."""
        patient_cond_csv = get_csv_patient_conditions(
            self.conditions_csv,
            self.test_patient_id
        )
        
        for cond in patient_cond_csv.head(1):
            our_fhir = map_condition(cond)
            
            self.assertIn("id", our_fhir)
            cond_id = our_fhir["id"]
            
            # Should contain patient ID and code
            self.assertIn(self.test_patient_id, cond_id)
            self.assertIn(cond["CODE"], cond_id)
            
            # Should start with "cond-"
            self.assertTrue(cond_id.startswith("cond-"))
            break
    
    def test_table_filter_active_conditions(self):
        """Test filtering for active conditions using Table."""
        # Filter for conditions without STOP date
        # Since STOP can be empty string or None, we need a custom filter
        active_conditions = self.conditions_csv.filter(
            lambda row: not row.get("STOP")
        )
        
        # Map some active conditions
        for cond in active_conditions.head(3):
            our_fhir = map_condition(cond)
            
            # Verify it's marked as active
            clinical_status = our_fhir["clinicalStatus"]["coding"][0]
            self.assertEqual(clinical_status["code"], "active")
    
    def test_table_filter_by_system(self):
        """Test filtering conditions by terminology system."""
        # All conditions should use SNOMED
        snomed_conditions = self.conditions_csv.filter(
            "SYSTEM = 'http://snomed.info/sct'"
        )
        
        # Should have conditions
        self.assertGreater(len(snomed_conditions), 0)
        
        # Verify all use SNOMED
        for cond in snomed_conditions.head(5):
            self.assertEqual(cond["SYSTEM"], "http://snomed.info/sct")
    
    def test_condition_comparison_with_synthea(self):
        """Test comparing our mapped condition with Synthea's FHIR output."""
        # Get CSV conditions
        patient_cond_csv = get_csv_patient_conditions(
            self.conditions_csv,
            self.test_patient_id
        )
        
        # Get Synthea's FHIR bundle
        synthea_bundle_table = get_patient_bundle_table(self.test_patient_id)
        
        if synthea_bundle_table:
            # Get conditions from FHIR bundle
            synthea_conditions = get_patient_resources(
                synthea_bundle_table,
                self.test_patient_id,
                "Condition"
            )
            
            if len(synthea_conditions) > 0 and len(patient_cond_csv) > 0:
                # Compare conditions
                for csv_cond in patient_cond_csv.head(1):
                    our_fhir = map_condition(csv_cond)
                    
                    # Find matching Synthea condition by SNOMED code
                    our_code = our_fhir["code"]["coding"][0]["code"]
                    
                    for synthea_cond in synthea_conditions:
                        synthea_code = synthea_cond.get("code", {}).get("coding", [{}])[0].get("code")
                        if synthea_code == our_code:
                            result = assert_condition_equivalence(our_fhir, synthea_cond)
                            
                            # Print comparison for debugging
                            if not result["valid"] or result["warnings"]:
                                print(f"\nCondition {our_code} comparison:")
                                print(f"  Matches: {result['matches']}")
                                if result["errors"]:
                                    print(f"  Errors: {result['errors']}")
                                if result["warnings"]:
                                    print(f"  Warnings: {result['warnings']}")
                            
                            break
                    break


if __name__ == "__main__":
    unittest.main()