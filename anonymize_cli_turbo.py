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

# Ensure the script directory is in the path for imports
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Import the anonymizer from anon7.2 (original working version)
import importlib.util
spec = importlib.util.spec_from_file_location("anon72", "anon7.2 - s padama.py")
anon72 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anon72)

# Use the classes from anon7.2
Anonymizer = anon72.Anonymizer
load_names_library = anon72.load_names_library
CZECH_FIRST_NAMES = anon72.CZECH_FIRST_NAMES


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
        # Load names library (silently in turbo mode)
        global CZECH_FIRST_NAMES
        CZECH_FIRST_NAMES = load_names_library("cz_names.v1.json")

        # Create anonymizer instance
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

        # Print minimal progress for user
        print(f"✅ Dokončeno! Osoby: {result['persons_found']}, Entity: {result['entities_total']}")

        # Output JSON on last line for parsing
        print(json.dumps(result))

        return 0

    except Exception as e:
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
