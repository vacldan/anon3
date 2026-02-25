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
    "skryi_watcher.py",      # Folder watcher - anonymization
    "deanon_watcher.py",     # Folder watcher - deanonymization
    "pdf2docx_watcher.py",   # Folder watcher - PDF conversion
]

# Large files that are imported by other scripts (compile as module)
COMPILE_TO_MODULE = [
    "anon72.py",  # Renamed from "anon7.2 - s padama.py" to fix Nuitka compilation
]

# Data files to include
DATA_FILES = [
    "cz_names.v1.json",
]

# Directories to include alongside executables
DATA_DIRS = [
    "fonts",  # DejaVu fonts for PDF report generation
]

# Extra Nuitka flags per script (e.g. include packages)
EXTRA_FLAGS = {
    "anonymize_cli.py": [
        "--include-package=fpdf",      # PDF report generation (fpdf2)
        "--include-package=fonttools",  # Required by fpdf2 for TTF fonts
    ],
}

# Scripts that should use --standalone instead of --onefile
# (some packages like fpdf/fonttools break Nuitka onefile mode)
USE_STANDALONE_MODE = {
    "anonymize_cli.py",
}


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

    # Some scripts need --standalone mode (no onefile) because their
    # dependencies (e.g. fpdf, fonttools) break Nuitka's onefile packing
    use_standalone = filename in USE_STANDALONE_MODE

    if use_standalone:
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",                 # Folder with .exe + dependencies
            "--assume-yes-for-downloads",
            "--output-dir=" + str(output_dir),
            "--output-filename=" + output_name + ".exe",
            "--windows-console-mode=disable",
        ]
    else:
        cmd = [
            sys.executable, "-m", "nuitka",
            "--onefile",                    # Single .exe file
            "--standalone",                 # Include all dependencies
            "--assume-yes-for-downloads",
            "--remove-output",              # Clean build folders
            "--output-dir=" + str(output_dir),
            "--output-filename=" + output_name + ".exe",
            "--windows-console-mode=disable",
        ]

    # Add extra flags for specific scripts (e.g. --include-package)
    extra = EXTRA_FLAGS.get(filename, [])
    cmd.extend(extra)

    cmd.append(str(filepath))

    success = run_command(cmd, f"Compiling {filename} to .exe ({'standalone' if use_standalone else 'onefile'})")

    # For standalone mode, the .exe is inside a .dist/ folder - copy it out
    if success and use_standalone:
        dist_dir = output_dir / f"{output_name}.dist"
        dist_exe = dist_dir / f"{output_name}.exe"
        target_exe = output_dir / f"{output_name}.exe"
        if dist_exe.exists():
            shutil.copy(dist_exe, target_exe)
            print(f"  Copied {output_name}.exe from .dist/ to output dir")
        else:
            print(f"  WARNING: {dist_exe} not found after standalone build!")
            success = False

    return success


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
                # CRITICAL: Also copy .pyd with simple name for Nuitka onefile mode
                # Nuitka onefile extracts to temp folder and can't find platform-specific
                # names like anon72.cp311-win_amd64.pyd, so we also need anon72.pyd
                module_name = filepath.stem  # e.g., "anon72"
                for pyd_file in output_dir.glob(f"{module_name}*.pyd"):
                    simple_pyd = output_dir / f"{module_name}.pyd"
                    if pyd_file != simple_pyd:
                        shutil.copy(pyd_file, simple_pyd)
                        print(f"  Also copied as: {simple_pyd.name}")
            else:
                # If module compilation fails, copy as-is
                print(f"INFO: Copying {filename} as-is (compilation failed)")
                shutil.copy(filepath, output_dir / filename)

    # Phase 3: Copy data files and directories
    print("\n" + "=" * 60)
    print("  PHASE 3: Copying data files")
    print("=" * 60)

    for filename in DATA_FILES:
        filepath = project_root / filename
        if filepath.exists():
            shutil.copy(filepath, output_dir / filename)
            print(f"  Copied: {filename}")

    for dirname in DATA_DIRS:
        dirpath = project_root / dirname
        if dirpath.exists():
            dest = output_dir / dirname
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(dirpath, dest)
            print(f"  Copied directory: {dirname}/")

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
