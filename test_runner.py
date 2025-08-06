#!/usr/bin/env python3
"""
Test runner script for FHIR x Synthea CSV mapping tests.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔹 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"   ✅ Success")
        if result.stdout.strip():
            # Show summary line if available
            lines = result.stdout.strip().split('\n')
            summary_line = next((line for line in reversed(lines) if 'passed' in line), None)
            if summary_line:
                print(f"   {summary_line}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed")
        if e.stdout:
            print("   STDOUT:")
            for line in e.stdout.split('\n')[-10:]:  # Last 10 lines
                if line.strip():
                    print(f"     {line}")
        if e.stderr:
            print("   STDERR:")
            for line in e.stderr.split('\n')[-5:]:  # Last 5 lines
                if line.strip():
                    print(f"     {line}")
        return False


def main():
    """Main test runner."""
    print("🧪 FHIR x Synthea CSV Test Suite")
    print("   Using chidian.Table for data processing")
    
    # Check if we're in the right directory
    if not Path("fhir_x_synthea_csv").exists():
        print("❌ Please run from the project root directory")
        sys.exit(1)
    
    success_count = 0
    total_count = 0
    
    # Test categories to run
    tests = [
        (["uv", "run", "pytest", "-m", "unit", "-v"], "Unit tests (no external data required)"),
        (["uv", "run", "pytest", "tests/test_patient_mapping.py", "-v"], "Patient mapping tests"),
        (["uv", "run", "pytest", "--collect-only", "-q"], "Test discovery"),
    ]
    
    # Run tests that might require data but gracefully skip
    optional_tests = [
        (["uv", "run", "pytest", "-m", "requires_csv", "--maxfail=1"], "CSV data tests (will skip if no data)"),
        (["uv", "run", "pytest", "-m", "requires_both", "--maxfail=1"], "Full validation tests (will skip if no data)"),
    ]
    
    for cmd, description in tests:
        total_count += 1
        if run_command(cmd, description):
            success_count += 1
    
    print(f"\n🔹 Optional tests (may skip if data unavailable)")
    for cmd, description in optional_tests:
        total_count += 1
        if run_command(cmd, description):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY: {success_count}/{total_count} test groups successful")
    print(f"{'='*60}")
    
    if success_count == total_count:
        print("✅ All test groups passed!")
        print("\nNext steps:")
        print("1. Download test data from https://synthea.mitre.org/downloads")
        print("2. Place CSV files in tests/data/csv/")
        print("3. Place FHIR bundles in tests/data/fhir/")
        print("4. Run: uv run pytest -v")
    else:
        print("❌ Some test groups failed")
    
    sys.exit(0 if success_count >= (total_count - len(optional_tests)) else 1)


if __name__ == "__main__":
    main()