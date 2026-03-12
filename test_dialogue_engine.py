#!/usr/bin/env python3
"""
Dialogue Testing Engine Test Runner
Automated testing script for dialogue flow validation

This script provides command-line testing capabilities for FMF dialogue files.
It can test individual files or entire directories recursively.

Features:
- Single file testing with detailed reports
- Batch testing of multiple files/directories
- Recursive directory scanning
- Output file generation for CI/CD integration
- Proper exit codes (0 for success, 1 for failures)

Usage:
    python test_dialogue_engine.py file.fmf                    # Test single file
    python test_dialogue_engine.py --recursive directory/     # Test directory recursively
    python test_dialogue_engine.py --output results.txt file.fmf  # Save results to file

Exit Codes:
    0: All tests passed
    1: One or more tests failed or critical errors found
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Optional

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from core.dialog_manager import DialogManager
from core.settings import Settings
from core.dialogue_testing_engine import TestResult

def setup_logging():
    """Configure logging for test runner"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('dialogue_test.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_single_file(file_path: Path, dialog_manager: DialogManager) -> bool:
    """Test a single dialogue file"""
    print(f"\n{'='*60}")
    print(f"Testing dialogue file: {file_path}")
    print(f"{'='*60}")

    try:
        # For testing purposes, load directly without the async worker
        from core.fmf_parser import FMFParser
        parser = FMFParser()
        dialogue = parser.load_from_file(file_path)

        # Set the dialogue in the manager
        dialog_manager.current_dialogue = dialogue
        dialog_manager.current_file = file_path
        dialog_manager.is_modified = False

        print(f"Loaded dialogue: {dialogue.npcname} with {len(dialogue.nodes)} nodes")

        # Run tests
        report = dialog_manager.test_dialogue()
        if not report:
            print(f"ERROR: Failed to generate test report for: {file_path}")
            return False

        # Display results
        report_text = dialog_manager.get_test_report_text(report)
        print(report_text)

        # Return success based on critical issues
        has_critical = report.has_critical_issues()
        if has_critical:
            print(f"\nCRITICAL ISSUES FOUND in {file_path}")
            return False
        else:
            print(f"\nPASSED: {file_path}")
            return True

    except Exception as e:
        print(f"ERROR testing {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_directory(directory_path: Path, dialog_manager: DialogManager, recursive: bool = False) -> tuple[int, int]:
    """Test all .fmf files in a directory"""
    if not directory_path.exists():
        print(f"Directory not found: {directory_path}")
        return 0, 0

    pattern = "**/*.fmf" if recursive else "*.fmf"
    fmf_files = list(directory_path.glob(pattern))

    if not fmf_files:
        print(f"No .fmf files found in {directory_path}")
        return 0, 0

    print(f"\nFound {len(fmf_files)} dialogue files to test")

    passed = 0
    total = 0

    for file_path in sorted(fmf_files):
        total += 1
        if test_single_file(file_path, dialog_manager):
            passed += 1

    return passed, total

def main():
    """Main test runner function"""
    setup_logging()
    logger = logging.getLogger(__name__)

    print("Dialogue Testing Engine - Test Runner")
    print("=====================================")

    # Initialize components
    settings = Settings()
    dialog_manager = DialogManager(settings)

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Test dialogue files for flow and structural issues')
    parser.add_argument('paths', nargs='*', help='Dialogue files or directories to test')
    parser.add_argument('--recursive', '-r', action='store_true', help='Recursively test directories')
    parser.add_argument('--output', '-o', type=str, help='Output results to file')

    args = parser.parse_args()

    # Default to current directory if no paths provided
    if not args.paths:
        args.paths = ['.']

    total_passed = 0
    total_tested = 0
    all_results = []

    # Test each path
    for path_str in args.paths:
        path = Path(path_str)

        if path.is_file():
            total_tested += 1
            success = test_single_file(path, dialog_manager)
            if success:
                total_passed += 1
            all_results.append((str(path), success))

        elif path.is_dir():
            passed, tested = test_directory(path, dialog_manager, args.recursive)
            total_passed += passed
            total_tested += tested
            all_results.extend([(str(path), True) for _ in range(passed)] +
                             [(str(path), False) for _ in range(tested - passed)])

        else:
            print(f"Path not found: {path}")

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total files tested: {total_tested}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tested - total_passed}")
    print(".1f")

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("Dialogue Testing Results\n")
                f.write("========================\n\n")
                f.write(f"Total files tested: {total_tested}\n")
                f.write(f"Passed: {total_passed}\n")
                f.write(f"Failed: {total_tested - total_passed}\n")
                f.write(".1f")
                f.write("\n\nDetailed Results:\n")
                for path, success in all_results:
                    status = "✅ PASSED" if success else "❌ FAILED"
                    f.write(f"{status}: {path}\n")
            print(f"Results written to: {args.output}")
        except Exception as e:
            print(f"Failed to write output file: {e}")

    # Exit with appropriate code
    success = total_passed == total_tested
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()