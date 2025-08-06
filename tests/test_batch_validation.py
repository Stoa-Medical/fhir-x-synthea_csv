"""
Batch validation tests for multiple patients using chidian Tables.
"""

import unittest
from pathlib import Path
from typing import Dict, List, Any

from chidian import Table

from fhir_x_synthea_csv.to_fhir import (
    map_patient,
    map_observation,
    map_condition,
)
from .loaders import (
    load_patients_csv,
    load_observations_csv,
    load_conditions_csv,
    list_available_patients,
    get_patient_bundle_table,
    extract_resources_by_type,
    get_csv_patient_data,
    get_csv_patient_observations,
    get_csv_patient_conditions,
)
from .validators import (
    assert_patient_equivalence,
    assert_observation_equivalence,
    assert_condition_equivalence,
)


class TestBatchValidation(unittest.TestCase):
    """Test batch processing and validation across multiple patients."""
    
    @classmethod
    def setUpClass(cls):
        """Load all test data."""
        cls.patients_csv = load_patients_csv()
        cls.observations_csv = load_observations_csv()
        cls.conditions_csv = load_conditions_csv()
        cls.patient_ids = list_available_patients()
    
    def test_batch_patient_mapping(self):
        """Test mapping multiple patients."""
        # Test first 5 patients
        test_count = min(5, len(self.patient_ids))
        success_count = 0
        failures = []
        
        for patient_id in self.patient_ids[:test_count]:
            csv_patient = get_csv_patient_data(self.patients_csv, patient_id)
            
            if csv_patient:
                try:
                    our_fhir = map_patient(csv_patient)
                    
                    # Basic validation
                    self.assertEqual(our_fhir["resourceType"], "Patient")
                    self.assertEqual(our_fhir["id"], patient_id)
                    self.assertIn("gender", our_fhir)
                    self.assertIn("birthDate", our_fhir)
                    
                    success_count += 1
                except Exception as e:
                    failures.append({
                        "patient_id": patient_id,
                        "error": str(e)
                    })
        
        # Report results
        print(f"\nBatch patient mapping: {success_count}/{test_count} successful")
        if failures:
            print(f"Failures: {failures}")
        
        # Should have high success rate
        self.assertGreaterEqual(success_count, test_count * 0.8)
    
    def test_statistical_validation(self):
        """Test statistical properties across all patients."""
        # Group patients by gender
        gender_groups = self.patients_csv.group_by("GENDER")
        
        # Count by gender
        gender_counts = {
            gender: len(table) 
            for gender, table in gender_groups.items()
        }
        
        print(f"\nGender distribution: {gender_counts}")
        
        # Should have both M and F
        self.assertIn("M", gender_counts)
        self.assertIn("F", gender_counts)
        
        # Map and validate gender mappings
        for gender, table in gender_groups.items():
            # Test first patient in each group
            for patient in table.head(1):
                our_fhir = map_patient(patient)
                
                expected_fhir_gender = {
                    "M": "male",
                    "F": "female",
                    "O": "other",
                    "U": "unknown"
                }.get(gender, "unknown")
                
                self.assertEqual(our_fhir["gender"], expected_fhir_gender)
                break
    
    def test_table_statistics(self):
        """Test using Table methods for statistical analysis."""
        # Get unique values for various fields
        unique_races = self.patients_csv.unique("RACE")
        unique_ethnicities = self.patients_csv.unique("ETHNICITY")
        unique_marital = self.patients_csv.unique("MARITAL")
        
        print(f"\nUnique races: {unique_races}")
        print(f"Unique ethnicities: {unique_ethnicities}")
        print(f"Unique marital statuses: {unique_marital}")
        
        # Verify expected values
        self.assertIn("white", unique_races)
        self.assertIn("nonhispanic", unique_ethnicities)
    
    def test_observation_volume_by_patient(self):
        """Test observation counts per patient."""
        # Group observations by patient
        obs_by_patient = self.observations_csv.group_by("PATIENT")
        
        # Calculate statistics
        obs_counts = {
            patient_id: len(table)
            for patient_id, table in obs_by_patient.items()
        }
        
        # Find min, max, average
        if obs_counts:
            min_obs = min(obs_counts.values())
            max_obs = max(obs_counts.values())
            avg_obs = sum(obs_counts.values()) / len(obs_counts)
            
            print(f"\nObservation statistics:")
            print(f"  Patients with observations: {len(obs_counts)}")
            print(f"  Min observations per patient: {min_obs}")
            print(f"  Max observations per patient: {max_obs}")
            print(f"  Average observations per patient: {avg_obs:.1f}")
            
            # Validate reasonable ranges
            self.assertGreater(min_obs, 0)
            self.assertLess(max_obs, 10000)  # Sanity check
    
    def test_condition_categories(self):
        """Test distribution of condition types."""
        # Get unique condition codes
        unique_codes = self.conditions_csv.unique("CODE")
        
        print(f"\nUnique condition codes: {len(unique_codes)}")
        
        # Group by encounter to see conditions per encounter
        cond_by_encounter = self.conditions_csv.group_by("ENCOUNTER")
        
        # Calculate conditions per encounter
        if cond_by_encounter:
            cond_per_enc = [len(table) for table in cond_by_encounter.values()]
            avg_cond = sum(cond_per_enc) / len(cond_per_enc)
            
            print(f"Average conditions per encounter: {avg_cond:.1f}")
    
    def test_cross_reference_integrity(self):
        """Test that references between resources are valid."""
        # Get all patient IDs from patients table
        patient_ids = set(self.patients_csv.unique("Id"))
        
        # Check observations reference valid patients
        obs_patient_refs = set(self.observations_csv.unique("PATIENT"))
        invalid_obs_refs = obs_patient_refs - patient_ids
        
        if invalid_obs_refs:
            print(f"\nWarning: Observations reference non-existent patients: {invalid_obs_refs}")
        
        self.assertEqual(len(invalid_obs_refs), 0, "Observations have invalid patient references")
        
        # Check conditions reference valid patients
        cond_patient_refs = set(self.conditions_csv.unique("PATIENT"))
        invalid_cond_refs = cond_patient_refs - patient_ids
        
        if invalid_cond_refs:
            print(f"\nWarning: Conditions reference non-existent patients: {invalid_cond_refs}")
        
        self.assertEqual(len(invalid_cond_refs), 0, "Conditions have invalid patient references")
    
    def test_batch_mapping_performance(self):
        """Test performance of batch mapping operations."""
        import time
        
        # Test mapping 10 patients
        test_count = min(10, len(self.patient_ids))
        
        start_time = time.time()
        
        for patient_id in self.patient_ids[:test_count]:
            # Get all data for patient
            patient = get_csv_patient_data(self.patients_csv, patient_id)
            observations = get_csv_patient_observations(self.observations_csv, patient_id)
            conditions = get_csv_patient_conditions(self.conditions_csv, patient_id)
            
            # Map to FHIR
            if patient:
                map_patient(patient)
            
            for obs in observations.head(5):  # Limit to 5 per patient for performance
                map_observation(obs)
            
            for cond in conditions.head(5):  # Limit to 5 per patient
                map_condition(cond)
        
        elapsed = time.time() - start_time
        
        print(f"\nBatch mapping performance:")
        print(f"  Processed {test_count} patients in {elapsed:.2f} seconds")
        print(f"  Average per patient: {elapsed/test_count:.3f} seconds")
        
        # Should be reasonably fast
        self.assertLess(elapsed/test_count, 1.0, "Mapping too slow (>1s per patient)")
    
    def test_table_select_projection(self):
        """Test using Table select for efficient data projection."""
        # Select only needed fields for mapping
        patient_subset = self.patients_csv.select(
            "Id, GENDER, BIRTHDATE, FIRST, LAST"
        )
        
        # Should have all patients but fewer fields
        self.assertEqual(len(patient_subset), len(self.patients_csv))
        
        # Check first patient has only selected fields
        for patient in patient_subset.head(1):
            self.assertIn("Id", patient)
            self.assertIn("GENDER", patient)
            self.assertIn("BIRTHDATE", patient)
            self.assertIn("FIRST", patient)
            self.assertIn("LAST", patient)
            
            # Should not have other fields
            self.assertNotIn("ADDRESS", patient)
            self.assertNotIn("CITY", patient)
            break
    
    def test_table_filter_chaining(self):
        """Test chaining Table operations."""
        # Chain multiple filters
        filtered = (
            self.observations_csv
            .filter("CATEGORY = 'vital-signs'")
            .filter("UNITS = 'mm[Hg]'")  # Blood pressure observations
        )
        
        # Should have filtered results
        if len(filtered) > 0:
            for obs in filtered.head(5):
                self.assertEqual(obs["CATEGORY"], "vital-signs")
                self.assertEqual(obs["UNITS"], "mm[Hg]")
                
                # Should be blood pressure codes
                self.assertIn(obs["CODE"], ["8480-6", "8462-4"])  # Systolic or Diastolic
    
    def test_comprehensive_patient_validation(self):
        """Test complete validation for a subset of patients."""
        # Test first 3 patients comprehensively
        test_patients = self.patient_ids[:3]
        
        results = {
            "patients": {"success": 0, "failed": 0},
            "observations": {"success": 0, "failed": 0},
            "conditions": {"success": 0, "failed": 0},
        }
        
        for patient_id in test_patients:
            print(f"\nValidating patient {patient_id}...")
            
            # Get CSV data
            csv_patient = get_csv_patient_data(self.patients_csv, patient_id)
            csv_observations = get_csv_patient_observations(self.observations_csv, patient_id)
            csv_conditions = get_csv_patient_conditions(self.conditions_csv, patient_id)
            
            # Map to FHIR
            if csv_patient:
                try:
                    our_patient = map_patient(csv_patient)
                    
                    # Get Synthea's version if available
                    synthea_bundle = get_patient_bundle_table(patient_id)
                    if synthea_bundle:
                        synthea_patients = extract_resources_by_type(synthea_bundle, "Patient")
                        if len(synthea_patients) > 0:
                            for synthea_patient in synthea_patients:
                                validation = assert_patient_equivalence(our_patient, synthea_patient)
                                if validation["valid"]:
                                    results["patients"]["success"] += 1
                                else:
                                    results["patients"]["failed"] += 1
                                break
                except Exception as e:
                    print(f"  Patient mapping error: {e}")
                    results["patients"]["failed"] += 1
            
            # Test some observations
            for obs in csv_observations.head(3):
                try:
                    our_obs = map_observation(obs)
                    results["observations"]["success"] += 1
                except Exception:
                    results["observations"]["failed"] += 1
            
            # Test some conditions
            for cond in csv_conditions.head(3):
                try:
                    our_cond = map_condition(cond)
                    results["conditions"]["success"] += 1
                except Exception:
                    results["conditions"]["failed"] += 1
        
        # Print summary
        print("\nComprehensive validation results:")
        for resource_type, counts in results.items():
            total = counts["success"] + counts["failed"]
            if total > 0:
                success_rate = counts["success"] / total * 100
                print(f"  {resource_type}: {counts['success']}/{total} ({success_rate:.1f}%)")


if __name__ == "__main__":
    unittest.main()