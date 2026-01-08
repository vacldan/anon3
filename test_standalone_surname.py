#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to debug standalone surname matching issue
"""

import sys
import importlib.util
from pathlib import Path

# Import anon7.2 module
spec = importlib.util.spec_from_file_location("anon72", "anon7.2 - s padama.py")
anon72 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anon72)

# Load names library
anon72.CZECH_FIRST_NAMES = anon72.load_names_library("cz_names.v1.json")

# Create anonymizer
anonymizer = anon72.Anonymizer(verbose=True)

# Test sequence: First full name, then standalone surname
print("=" * 60)
print("TEST: Standalone surname matching")
print("=" * 60)

# Step 1: Create tag for full name "Drahomíra Dvořáková"
print("\n1. Creating tag for 'Drahomíra Dvořáková':")
first_nom_1 = anon72.infer_first_name_nominative("Drahomíra")
last_nom_1 = anon72.infer_surname_nominative("Dvořáková")
print(f"   Inferred nominatives: '{first_nom_1}' '{last_nom_1}'")

tag1, canonical1 = anonymizer._ensure_person_tag(first_nom_1, last_nom_1)
print(f"   Result: {tag1} → {canonical1}")
print(f"   Person index: {dict(anonymizer.person_index)}")

# Step 2: Try to get/create tag for standalone surname "Dvořáková" (empty first name)
print("\n2. Creating tag for standalone 'Dvořáková' (empty first name):")
last_nom_2 = anon72.infer_surname_nominative("Dvořáková")
print(f"   Inferred nominative: '' '{last_nom_2}'")

tag2, canonical2 = anonymizer._ensure_person_tag("", last_nom_2)
print(f"   Result: {tag2} → {canonical2}")
print(f"   Person index: {dict(anonymizer.person_index)}")

# Analysis
print("\n" + "=" * 60)
print("ANALYSIS:")
print("=" * 60)
if tag1 == tag2:
    print("✓ CORRECT: Both references use the same tag!")
    print(f"  Both map to: {tag1}")
else:
    print("✗ BUG: Different tags were created!")
    print(f"  Full name:          {tag1} → {canonical1}")
    print(f"  Standalone surname: {tag2} → {canonical2}")
    print("\nThis is the bug! Standalone surname should reuse existing tag.")

print("\nAll persons created:")
for p in anonymizer.canonical_persons:
    print(f"  {p['tag']}: '{p['first']}' '{p['last']}'")
