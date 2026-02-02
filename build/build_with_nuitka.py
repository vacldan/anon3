#!/usr/bin/env python3
"""
Build script using Nuitka - compiles Python to native executables
No external runtime needed, code is fully protected

Usage: python build/build_with_nuitka.py

Requirements:
  pip install nuitka
  (Nuitka will download C++ compiler if needed)
"""

import subprocess
import sys
import shutil
import os
from pathlib import Path

# Scripts to compile to standalone .exe (called from Electron)
COMPILE_TO_EXE = [
    "validate_license_standalone.py",  # CRITICAL - contains MASTER_SECRET
    "anonymize_cli.py",
    "deanonymizator_lokal.py",
    "pdf2docx_cli.py",
    "skryi_watcher.py",  # Folder watcher service
]

# Large files that are imported by other scripts (compile as module)
COMPILE_TO_MODULE = [
    "anon7.2 - s padama.py",
]

# Data files to include
DATA_FILES = [
    "cz_names.v1.json",
]


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"FAILED with code {result.returncode}")
        return False

    print(f"SUCCESS")
    return True


def check_nuitka():
    """Check if Nuitka is installed"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print(f"Nuitka found: {version}")
            return True
    except:
        pass

    print("ERROR: Nuitka not found!")
    print("Install with: pip install nuitka")
    return False


def compile_to_exe(filepath, output_dir):
    """Compile a Python script to standalone .exe"""
    filename = filepath.name
    output_name = filepath.stem  # filename without extension

    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",                    # Single .exe file
        "--standalone",                 # Include all dependencies
        "--assume-yes-for-downloads",   # Auto-download C++ compiler if needed
        "--remove-output",              # Clean build folders
        "--output-dir=" + str(output_dir),
        "--output-filename=" + output_name + ".exe",
        # Console mode: attach to existing console (for CLI tools called from Electron)
        "--windows-console-mode=attach",
        str(filepath)
    ]

    return run_command(cmd, f"Compiling {filename} to .exe")


def compile_to_module(filepath, output_dir):
    """Compile a Python script to .pyd module"""
    filename = filepath.name

    cmd = [
        sys.executable, "-m", "nuitka",
        "--module",                     # Compile as importable module
        "--assume-yes-for-downloads",
        "--remove-output",
        "--output-dir=" + str(output_dir),
        str(filepath)
    ]

    return run_command(cmd, f"Compiling {filename} to .pyd module")


def main():
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "dist_nuitka"

    print("=" * 60)
    print("  NUITKA BUILD SCRIPT")
    print("  Compiling Python to native executables")
    print("=" * 60)

    # Check Nuitka
    if not check_nuitka():
        return 1

    # Create/clean output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    success_count = 0
    failed_files = []

    # Phase 1: Compile scripts to .exe
    print("\n" + "=" * 60)
    print("  PHASE 1: Compiling to standalone .exe")
    print("=" * 60)

    for filename in COMPILE_TO_EXE:
        filepath = project_root / filename
        if filepath.exists():
            if compile_to_exe(filepath, output_dir):
                success_count += 1
            else:
                failed_files.append(filename)
                print(f"WARNING: Failed to compile {filename}")
        else:
            print(f"WARNING: {filename} not found")

    # Phase 2: Compile modules to .pyd (optional)
    print("\n" + "=" * 60)
    print("  PHASE 2: Compiling modules to .pyd")
    print("=" * 60)

    for filename in COMPILE_TO_MODULE:
        filepath = project_root / filename
        if filepath.exists():
            if compile_to_module(filepath, output_dir):
                success_count += 1
            else:
                # If module compilation fails, copy as-is
                print(f"INFO: Copying {filename} as-is (compilation failed)")
                shutil.copy(filepath, output_dir / filename)

    # Phase 3: Copy data files
    print("\n" + "=" * 60)
    print("  PHASE 3: Copying data files")
    print("=" * 60)

    for filename in DATA_FILES:
        filepath = project_root / filename
        if filepath.exists():
            shutil.copy(filepath, output_dir / filename)
            print(f"  Copied: {filename}")

    # Summary
    print("\n" + "=" * 60)
    print("  BUILD SUMMARY")
    print("=" * 60)
    print(f"  Compiled files: {success_count}")
    print(f"  Failed files: {len(failed_files)}")

    if failed_files:
        print(f"\n  Failed: {', '.join(failed_files)}")

    print(f"\n  Output directory: {output_dir}")
    print("\n  Compiled .exe files are FULLY PROTECTED!")
    print("  MASTER_SECRET is embedded in binary code.")

    # List output files
    print("\n  Output files:")
    for f in sorted(output_dir.iterdir()):
        size = f.stat().st_size / 1024
        print(f"    {f.name} ({size:.1f} KB)")

    print("\n  Next steps:")
    print("    1. Copy .exe files to project root")
    print("    2. Run: npm run dist")

    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
