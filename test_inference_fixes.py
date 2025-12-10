#!/usr/bin/env python3
"""Test inference fixes"""
import json

# Load Czech names
with open('cz_names.v1.json', 'r', encoding='utf-8') as f:
    names_data = json.load(f)
    CZECH_FIRST_NAMES = set(n.lower() for n in names_data['first_names'])

def infer_first_name_nominative(obs: str) -> str:
    """Simplified version for testing"""
    lo = obs.lower()

    # VARIANTY JMEN
    name_variants = {
        'karl': 'karel',
        'mark': 'marek',
    }
    if lo in name_variants:
        return name_variants[lo].capitalize()

    if lo in CZECH_FIRST_NAMES:
        return obs.capitalize()

    # Genitiv -a s vložným 'e'
    if lo.endswith('a') and len(obs) > 1:
        cand = obs[:-1]
        if cand.lower() in CZECH_FIRST_NAMES:
            return cand.capitalize()

        # Vložné 'e'
        if len(cand) >= 3:
            vowels = 'aeiouyáéěíóúůý'
            last_char = cand[-1]
            if last_char.lower() not in vowels:
                cand_with_e = cand[:-1] + 'e' + last_char
                if cand_with_e.lower() in CZECH_FIRST_NAMES:
                    return cand_with_e.capitalize()

    # -i → -a (Bei → Bea)
    if lo.endswith('i'):
        stem = obs[:-1]
        if (stem + 'a').lower() in CZECH_FIRST_NAMES:
            return (stem + 'a').capitalize()

    return obs

def infer_surname_nominative(obs: str) -> str:
    """Simplified version for testing"""
    lo = obs.lower()

    # Genitiv množného čísla -ů
    if lo.endswith('ů') and len(obs) > 2:
        return obs[:-1]

    # Genitiv -se → -s
    if lo.endswith('se') and len(obs) > 3:
        return obs[:-1]

    return obs

# Test cases
first_name_tests = [
    ("Pavla", "Pavel"),
    ("Karl", "Karel"),
    ("Mark", "Marek"),
    ("Bei", "Bea"),
]

surname_tests = [
    ("Šustrů", "Šustr"),
    ("Holase", "Holas"),
]

print("Testing first name inference:")
print("=" * 50)
all_passed = True
for input_name, expected in first_name_tests:
    result = infer_first_name_nominative(input_name)
    passed = result == expected
    all_passed = all_passed and passed
    status = "✓" if passed else "✗"
    print(f"{status} {input_name} → {result} (expected: {expected})")

print("\nTesting surname inference:")
print("=" * 50)
for input_name, expected in surname_tests:
    result = infer_surname_nominative(input_name)
    passed = result == expected
    all_passed = all_passed and passed
    status = "✓" if passed else "✗"
    print(f"{status} {input_name} → {result} (expected: {expected})")

print("=" * 50)
if all_passed:
    print("✓ All tests passed!")
else:
    print("✗ Some tests failed!")
