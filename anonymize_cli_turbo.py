#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Wrapper for SKRYI Document Anonymization - TURBO MODE
Ultra-optimized version with minimal output for maximum speed
"""

import sys
import os
import argparse
import json
from pathlib import Path
from io import StringIO

# Ensure the script directory is in the path for imports
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Import the optimized anonymizer
try:
    from anon_optimized import Anonymizer, load_names_library, CZECH_FIRST_NAMES
except ImportError:
    print("❌ Error: anon_optimized.py not found")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="SKRYI Document Anonymization - TURBO CLI"
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
        print(f"❌ Chyba: Vstupní soubor neexistuje: {input_path}")
        return 1

    if not input_path.suffix.lower() == '.docx':
        print(f"❌ Chyba: Vstupní soubor musí být .docx formát")
        return 1

    try:
        # TURBO MODE: Redirect stdout to suppress all print statements
        # Only final JSON result will be printed
        if not args.verbose:
            old_stdout = sys.stdout
            sys.stdout = StringIO()

        # Load names library
        global CZECH_FIRST_NAMES
        CZECH_FIRST_NAMES = load_names_library("cz_names.v1.json")

        # Create anonymizer instance
        anonymizer = Anonymizer(verbose=False)

        # Run anonymization
        anonymizer.anonymize_docx(
            str(input_path),
            args.output,
            args.map,
            args.map_txt
        )

        # Restore stdout for final output
        if not args.verbose:
            sys.stdout = old_stdout

        # Output JSON result for Electron to parse
        result = {
            "success": True,
            "output": args.output,
            "map_json": args.map,
            "map_txt": args.map_txt,
            "persons_found": len(anonymizer.canonical_persons),
            "entities_total": sum(len(entities) for entities in anonymizer.entity_map.values())
        }

        # Print minimal progress for user
        print(f"✅ Dokončeno! Osoby: {result['persons_found']}, Entity: {result['entities_total']}")

        # Output JSON on last line for parsing
        print(json.dumps(result))

        return 0

    except Exception as e:
        # Restore stdout in case of error
        if not args.verbose:
            sys.stdout = old_stdout

        print(f"\n❌ CHYBA: {e}")

        # Output error JSON
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result))
        return 1


if __name__ == "__main__":
    sys.exit(main())
