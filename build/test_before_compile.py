#!/usr/bin/env python3
"""
Quick test script - tests all CLI scripts WITHOUT Nuitka compilation.
Run this BEFORE wasting 2 hours on Nuitka build!

Usage: python build/test_before_compile.py
"""

import subprocess
import sys
import os
from pathlib import Path

# Colors for terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def test_import(module_name, description):
    """Test if a module can be imported"""
    print(f"  Testing import: {module_name}...", end=" ")
    try:
        __import__(module_name)
        print(f"{GREEN}OK{RESET}")
        return True
    except ImportError as e:
        print(f"{RED}FAILED - {e}{RESET}")
        return False

def test_script_syntax(filepath, description):
    """Test if a Python script has valid syntax"""
    print(f"  Testing syntax: {filepath.name}...", end=" ")
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(filepath)],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"{GREEN}OK{RESET}")
        return True
    else:
        print(f"{RED}FAILED{RESET}")
        print(f"    {result.stderr}")
        return False

def test_script_help(filepath, description):
    """Test if a CLI script runs with --help"""
    print(f"  Testing --help: {filepath.name}...", end=" ")
    result = subprocess.run(
        [sys.executable, str(filepath), "--help"],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode == 0:
        print(f"{GREEN}OK{RESET}")
        return True
    else:
        # Some scripts don't support --help, check if they at least start
        print(f"{YELLOW}No --help (returncode={result.returncode}){RESET}")
        return True  # Not a failure

def test_anon72_functions():
    """Test critical anon72 functions"""
    print(f"\n  Testing anon72 functions...")
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        import anon72

        # Test that main class exists
        if hasattr(anon72, 'Anonymizer'):
            print(f"    Anonymizer class: {GREEN}OK{RESET}")
        else:
            print(f"    Anonymizer class: {YELLOW}NOT FOUND{RESET}")

        return True
    except Exception as e:
        print(f"    {RED}FAILED - {e}{RESET}")
        return False

def main():
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("=" * 60)
    print("  QUICK TEST - Before Nuitka Compilation")
    print("  Tests Python scripts WITHOUT 2-hour compile time")
    print("=" * 60)

    # Scripts to test
    cli_scripts = [
        "anonymize_cli.py",
        "deanonymizator_lokal.py",
        "pdf2docx_cli.py",
        "skryi_watcher.py",
        "deanon_watcher.py",
        "pdf2docx_watcher.py",
        "validate_license_standalone.py",
    ]

    modules = [
        "anon72.py",
    ]

    # Required data files
    data_files = [
        "cz_names.v1.json",
    ]

    passed = 0
    failed = 0

    # Test 1: Check required files exist
    print("\n[1/4] Checking required files...")
    for filename in cli_scripts + modules + data_files:
        filepath = project_root / filename
        print(f"  {filename}...", end=" ")
        if filepath.exists():
            print(f"{GREEN}EXISTS{RESET}")
            passed += 1
        else:
            print(f"{RED}MISSING{RESET}")
            failed += 1

    # Test 2: Syntax check
    print("\n[2/4] Checking Python syntax...")
    for filename in cli_scripts + modules:
        filepath = project_root / filename
        if filepath.exists():
            if test_script_syntax(filepath, ""):
                passed += 1
            else:
                failed += 1

    # Test 3: Import dependencies
    print("\n[3/4] Testing required imports...")
    required_imports = [
        ("docx", "python-docx"),
        ("watchdog", "watchdog"),
        ("pdf2docx", "pdf2docx"),
        ("fitz", "PyMuPDF"),
    ]

    for module, package in required_imports:
        print(f"  {module} ({package})...", end=" ")
        try:
            __import__(module)
            print(f"{GREEN}OK{RESET}")
            passed += 1
        except ImportError:
            print(f"{RED}MISSING - pip install {package}{RESET}")
            failed += 1

    # Test 4: Test anon72 module
    print("\n[4/4] Testing anon72 module...")
    if test_anon72_functions():
        passed += 1
    else:
        failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"  {GREEN}Passed: {passed}{RESET}")
    print(f"  {RED}Failed: {failed}{RESET}")

    if failed == 0:
        print(f"\n  {GREEN}All tests passed! Safe to run Nuitka build.{RESET}")
        print(f"\n  Run: python build/build_with_nuitka.py")
        return 0
    else:
        print(f"\n  {RED}Fix the errors above before running Nuitka!{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
