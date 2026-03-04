#!/usr/bin/env python3
"""
Build script for PyArmor TRIAL version
Only obfuscates critical files (license validation)
Skips large files that exceed trial limits

Usage: python build/build_with_trial_pyarmor.py
"""

import subprocess
import sys
import shutil
from pathlib import Path

# Files to obfuscate (CRITICAL - contains MASTER_SECRET)
CRITICAL_FILES = [
    "validate_license_standalone.py",
]

# Files to obfuscate if trial allows (may fail for large files)
OPTIONAL_FILES = [
    "anonymize_cli.py",
    "deanonymizator_lokal.py",
    "pdf2docx_cli.py",
]

# Files to SKIP (too large for trial, or not critical)
SKIP_FILES = [
    "anon7.2 - s padama.py",  # Too large for PyArmor trial
]

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*50}")
    print(f"  {description}")
    print(f"{'='*50}")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FAILED: {result.stderr}")
        return False

    print(f"SUCCESS")
    if result.stdout:
        print(result.stdout[:500])
    return True


def obfuscate_file(filepath):
    """Obfuscate a single file with PyArmor"""
    cmd = ["pyarmor", "gen", "-O", "dist_obfuscated/", str(filepath)]
    return run_command(cmd, f"Obfuscating {filepath}")


def main():
    project_root = Path(__file__).parent.parent

    print("="*60)
    print("  PyArmor TRIAL Build Script")
    print("  (Skips large files that exceed trial limits)")
    print("="*60)

    # Create output directory
    dist_dir = project_root / "dist_obfuscated"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    success_count = 0
    failed_files = []

    # 1. Obfuscate CRITICAL files (must succeed)
    print("\n" + "="*60)
    print("  PHASE 1: Critical files (license validation)")
    print("="*60)

    for filename in CRITICAL_FILES:
        filepath = project_root / filename
        if filepath.exists():
            if obfuscate_file(filepath):
                success_count += 1
            else:
                print(f"\nCRITICAL ERROR: Failed to obfuscate {filename}")
                print("The license validation MUST be obfuscated!")
                print("\nOptions:")
                print("  1. Purchase PyArmor Pro license")
                print("  2. Check if PyArmor is properly installed")
                sys.exit(1)
        else:
            print(f"WARNING: {filename} not found")

    # 2. Try optional files (may fail due to trial limits)
    print("\n" + "="*60)
    print("  PHASE 2: Optional files (best effort)")
    print("="*60)

    for filename in OPTIONAL_FILES:
        filepath = project_root / filename
        if filepath.exists():
            if obfuscate_file(filepath):
                success_count += 1
            else:
                failed_files.append(filename)
                print(f"INFO: {filename} skipped (trial limit)")

    # 3. Copy skipped files as-is (not obfuscated)
    print("\n" + "="*60)
    print("  PHASE 3: Copying non-obfuscated files")
    print("="*60)

    for filename in SKIP_FILES:
        filepath = project_root / filename
        if filepath.exists():
            dest = dist_dir / filename
            shutil.copy(filepath, dest)
            print(f"  Copied (not obfuscated): {filename}")

    # Also copy any failed optional files
    for filename in failed_files:
        filepath = project_root / filename
        if filepath.exists():
            dest = dist_dir / filename
            shutil.copy(filepath, dest)
            print(f"  Copied (not obfuscated): {filename}")

    # 4. Copy pyarmor_runtime if created
    runtime_dirs = list(dist_dir.glob("pyarmor_runtime_*"))
    if runtime_dirs:
        print(f"\n  PyArmor runtime: {runtime_dirs[0].name}")

    # Summary
    print("\n" + "="*60)
    print("  BUILD SUMMARY")
    print("="*60)
    print(f"  Obfuscated files: {success_count}")
    print(f"  Skipped/copied files: {len(SKIP_FILES) + len(failed_files)}")

    if success_count > 0:
        print("\n  LICENSE VALIDATION IS PROTECTED!")
        print("  MASTER_SECRET is obfuscated.")
        print("\n  Output directory: dist_obfuscated/")
        print("\n  Next step:")
        print("    1. Copy obfuscated files to project root")
        print("    2. Run: npm run dist")
        return 0
    else:
        print("\n  ERROR: No files were obfuscated!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
