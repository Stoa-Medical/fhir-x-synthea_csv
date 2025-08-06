#!/usr/bin/env python
"""
Main test runner for FHIR x Synthea CSV mapping validation.

This script runs all tests and provides a comprehensive report on the
mapping quality using chidian Tables.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """Run all test suites."""
    # Create test loader
    loader = unittest.TestLoader()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test modules
    test_modules = [
        'tests.test_patient_mapping',
        'tests.test_observation_mapping',
        'tests.test_condition_mapping',
        'tests.test_batch_validation',
    ]
    
    for module in test_modules:
        try:
            suite.addTests(loader.loadTestsFromName(module))
            print(f"✓ Loaded tests from {module}")
        except Exception as e:
            print(f"✗ Failed to load {module}: {e}")
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_specific_test(test_name):
    """Run a specific test module or test case."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    try:
        suite.addTests(loader.loadTestsFromName(test_name))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result
    except Exception as e:
        print(f"Error running test {test_name}: {e}")
        return None


def run_quick_validation():
    """Run a quick validation test on sample data."""
    print("\n" + "="*60)
    print("QUICK VALIDATION TEST")
    print("="*60)
    
    from tests.loaders import (
        load_patients_csv,
        load_observations_csv,
        load_conditions_csv,
        get_csv_patient_data,
        get_csv_patient_observations,
        get_csv_patient_conditions,
    )
    from fhir_x_synthea_csv.to_fhir import (
        map_patient,
        map_observation,
        map_condition,
    )
    
    # Load data
    print("\nLoading CSV data as Tables...")
    patients = load_patients_csv()
    observations = load_observations_csv()
    conditions = load_conditions_csv()
    
    print(f"  Loaded {len(patients)} patients")
    print(f"  Loaded {len(observations)} observations")
    print(f"  Loaded {len(conditions)} conditions")
    
    # Test with first patient
    test_patient_id = "8c8e1c9a-b310-43c6-33a7-ad11bad21c40"
    print(f"\nTesting with patient {test_patient_id}...")
    
    # Get patient data
    patient_data = get_csv_patient_data(patients, test_patient_id)
    if patient_data:
        # Map patient
        fhir_patient = map_patient(patient_data)
        print(f"  ✓ Mapped patient: {fhir_patient['name'][0]['given'][0]} {fhir_patient['name'][0]['family']}")
        
        # Get and map observations
        patient_obs = get_csv_patient_observations(observations, test_patient_id)
        print(f"  ✓ Found {len(patient_obs)} observations")
        
        # Map first observation
        for obs in patient_obs.head(1):
            fhir_obs = map_observation(obs)
            print(f"    - Mapped observation: {fhir_obs['code']['coding'][0]['display']}")
            break
        
        # Get and map conditions
        patient_cond = get_csv_patient_conditions(conditions, test_patient_id)
        print(f"  ✓ Found {len(patient_cond)} conditions")
        
        # Map first condition
        for cond in patient_cond.head(1):
            fhir_cond = map_condition(cond)
            print(f"    - Mapped condition: {fhir_cond['code']['coding'][0]['display']}")
            break
        
        print("\n✅ Quick validation successful!")
        return True
    else:
        print(f"\n❌ Patient {test_patient_id} not found")
        return False


def print_summary(result):
    """Print test result summary."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if result:
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")
        
        if result.wasSuccessful():
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed")
            
            if result.failures:
                print("\nFailures:")
                for test, traceback in result.failures[:3]:  # Show first 3
                    print(f"  - {test}")
            
            if result.errors:
                print("\nErrors:")
                for test, traceback in result.errors[:3]:  # Show first 3
                    print(f"  - {test}")
    
    print("="*60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run FHIR x Synthea CSV mapping tests"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation test only"
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Run specific test (e.g., tests.test_patient_mapping)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    
    args = parser.parse_args()
    
    print("🔬 FHIR x Synthea CSV Mapping Test Suite")
    print("   Using chidian.Table for data processing")
    print()
    
    if args.quick:
        success = run_quick_validation()
        sys.exit(0 if success else 1)
    elif args.test:
        result = run_specific_test(args.test)
        if result:
            print_summary(result)
            sys.exit(0 if result.wasSuccessful() else 1)
        else:
            sys.exit(1)
    else:
        result = run_all_tests()
        print_summary(result)
        sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()