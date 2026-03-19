#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyzuje detekované entity v JSON mapách z 5 testovacích smluv.
Vypíše přehled: které typy entit byly detekovány a v kterých smlouvách.
"""

import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "test_data"

# Očekávané entity v jednotlivých smlouvách (pro srovnání)
# Pozn.: BIRTH_DATE se často detekuje jako DATE (obecný pattern má přednost)
# SECRET se může detekovat jako API_KEY (Stripe klíč)
EXPECTED = {
    "01": ["PERSON", "BIRTH_ID", "ADDRESS", "ID_CARD", "PASSPORT", "DRIVER_LICENSE",
           "PHONE", "EMAIL", "BANK", "IBAN", "CARD", "ICO", "DIC", "DATE"],
    "02": ["PERSON", "EMAIL", "USERNAME", "PASSWORD", "API_KEY", "SSH_KEY", "IP", "MAC", "IMEI",
           "HOST", "LINKEDIN", "FACEBOOK", "INSTAGRAM", "SKYPE", "VOICE_ID", "BIO_HASH", "PHOTO_ID"],
    "03": ["PERSON", "BIRTH_ID", "ADDRESS", "PHONE", "INSURANCE_ID",
           "BENEFIT_CARD", "RFID", "ACCOUNT_ID", "GENETIC_ID", "DATE"],
    "04": ["PERSON", "ADDRESS", "LICENSE_PLATE", "VIN", "DATE"],
    "05": ["PERSON", "BIRTH_ID", "ADDRESS", "ID_CARD", "PASSPORT", "PHONE", "EMAIL",
           "BANK", "IBAN", "CARD", "ICO", "DIC", "INSURANCE_ID", "BENEFIT_CARD", "RFID", "GENETIC_ID",
           "IP", "MAC", "LICENSE_PLATE", "VIN", "DATE"],
}


def main():
    all_types = defaultdict(list)  # type -> [file1, file2, ...]
    by_file = defaultdict(set)  # file -> [types]

    map_files = sorted(TEST_DIR.glob("*_map.json"))
    for map_path in map_files:
        stem = map_path.stem.replace("_map", "")
        if not map_path.exists():
            continue

        with open(map_path, encoding="utf-8") as f:
            data = json.load(f)

        types_in_file = set()
        for ent in data.get("entities", []):
            t = ent.get("type")
            if t:
                types_in_file.add(t)
                all_types[t].append(stem)

        by_file[stem] = types_in_file

    # Výstup
    print("=" * 70)
    print(f"PŘEHLED DETEKOVANÝCH ENTIT ({len(by_file)} smluv)")
    print("=" * 70)

    print("\n--- DETEKOVANÉ TYPY ENTIT (podle souboru) ---\n")
    for stem in sorted(by_file.keys()):
        types = sorted(by_file[stem])
        print(f"  {stem}: {len(types)} typů")
        print(f"    {', '.join(types)}")
        print()

    print("\n--- VŠECHNY UNIKÁTNÍ TYPY ENTIT (celkem) ---\n")
    unique_types = sorted(all_types.keys())
    print(f"  Celkem {len(unique_types)} typů: {', '.join(unique_types)}")

    print("\n--- SROVNÁNÍ: OČEKÁVÁNO vs. DETEKOVÁNO (pouze full_entity_test 01-05) ---\n")
    for file_id, expected_types in EXPECTED.items():
        stem = f"smlouva_full_entity_test_{file_id}"
        detected = by_file.get(stem, set())
        expected_set = set(expected_types)
        missing = expected_set - detected
        extra = detected - expected_set
        print(f"  {stem}:")
        if missing:
            print(f"    CHYBÍ (nedetekováno): {', '.join(sorted(missing))}")
        if extra:
            print(f"    NAVÍC (neočekáváno): {', '.join(sorted(extra))}")
        if not missing and not extra:
            print(f"    OK – všechny očekávané entity detekovány")
        print()


if __name__ == "__main__":
    main()
