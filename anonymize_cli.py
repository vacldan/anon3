#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Wrapper for SKRYI Document Anonymization
Optimized version with performance improvements for Electron app
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Ensure the script directory is in the path for imports
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# For compiled exe, also check the exe's directory
exe_dir = Path(sys.executable).parent
if str(exe_dir) not in sys.path:
    sys.path.insert(0, str(exe_dir))

# CRITICAL: For Nuitka --onefile mode, the exe extracts to a temp folder
# but we need to find modules in the ORIGINAL directory where the exe is located
# sys.argv[0] contains the original exe path, not the temp extraction path
original_exe_dir = Path(os.path.abspath(sys.argv[0])).parent
if str(original_exe_dir) not in sys.path:
    sys.path.insert(0, str(original_exe_dir))

# Direct import - works with Nuitka compilation
try:
    import anon72
except ImportError:
    print("FATAL: anon72 module not found!")
    print(f"Script dir: {script_dir}")
    print(f"Exe dir: {exe_dir}")
    print(f"Original exe dir: {original_exe_dir}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)

# Use the classes from anon72
Anonymizer = anon72.Anonymizer
load_names_library = anon72.load_names_library
CZECH_FIRST_NAMES = anon72.CZECH_FIRST_NAMES


def main():
    parser = argparse.ArgumentParser(
        description="SKRYI Document Anonymization - CLI Interface"
    )
    parser.add_argument("--input", required=True, help="Input DOCX file path")
    parser.add_argument("--output", required=True, help="Output anonymized DOCX file path")
    parser.add_argument("--map", required=True, help="Output JSON map file path")
    parser.add_argument("--map_txt", required=True, help="Output TXT map file path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"CHYBA: Vstupni soubor neexistuje: {input_path}")
        return 1

    if not input_path.suffix.lower() == '.docx':
        print(f"CHYBA: Vstupni soubor musi byt .docx format")
        return 1

    try:
        # Load names library - find it in the same directory as the executable
        print("[INFO] Nacitam knihovnu ceskych jmen...")
        global CZECH_FIRST_NAMES

        # Find cz_names.v1.json in executable directory
        names_json_path = None
        for search_dir in [original_exe_dir, exe_dir, script_dir]:
            candidate = search_dir / "cz_names.v1.json"
            if candidate.exists():
                names_json_path = str(candidate)
                break

        if names_json_path:
            print(f"[INFO] Knihovna nalezena: {names_json_path}")
            CZECH_FIRST_NAMES = load_names_library(names_json_path)
        else:
            print("[VAROVANI] cz_names.v1.json nenalezeno, zkousim relativni cestu...")
            CZECH_FIRST_NAMES = load_names_library("cz_names.v1.json")

        if not CZECH_FIRST_NAMES:
            print("[VAROVANI] Knihovna jmen je prazdna, detekce bude omezena")

        # Create anonymizer instance
        print(f"\n[INFO] Zpracovavam: {input_path.name}")
        anonymizer = Anonymizer(verbose=args.verbose)

        # Run anonymization
        anonymizer.anonymize_docx(
            str(input_path),
            args.output,
            args.map,
            args.map_txt
        )

        # Output JSON result for Electron to parse
        result = {
            "success": True,
            "output": str(Path(args.output).absolute()),
            "map_json": str(Path(args.map).absolute()),
            "map_txt": str(Path(args.map_txt).absolute()),
            "persons_found": len(anonymizer.canonical_persons),
            "entities_total": sum(len(entities) for entities in anonymizer.entity_map.values())
        }

        print(f"\n[OK] Anonymizace dokoncena!")
        print(f"[INFO] Nalezeno osob: {result['persons_found']}")
        print(f"[INFO] Celkem entit: {result['entities_total']}")

        # Zaloguj statistiku
        try:
            from skryi_stats import log_anonymization
            log_anonymization(persons_found=result['persons_found'], entities_total=result['entities_total'])
        except Exception:
            pass  # Statistiky nejsou kritické

        # Output JSON on last line for parsing
        print(json.dumps(result))

        return 0

    except Exception as e:
        print(f"\n[CHYBA] {e}")
        import traceback
        traceback.print_exc()

        # Output error JSON
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result))
        return 1


if __name__ == "__main__":
    sys.exit(main())
