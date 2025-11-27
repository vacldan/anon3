#!/usr/bin/env python3
"""Debug test pro Karel Řehoř."""

import sys
sys.path.insert(0, '.')

# Load the anonymizer
exec(open('anon7.2 - s padama.py').read().split('if __name__')[0])

# Create fresh anonymizer
anon = Anonymizer(verbose=False)

# Simuluj zpracování odstavce "Karel Řehoř – „bez Karla Řehoře", „k Karlu Řehořovi""
test_paragraph = 'Karel Řehoř – „bez Karla Řehoře", „k Karlu Řehořovi"'

print("=== TEST: Karel Řehoř ===")
print(f"Input: {test_paragraph}\n")

# FÁZE 1: Anonymizace entit
text_after_entities = anon.anonymize_entities(test_paragraph)
print(f"Po entitách: {text_after_entities}")

# FÁZE 2: _apply_known_people (prázdné na začátku)
text_after_known = anon._apply_known_people(text_after_entities)
print(f"Po known people: {text_after_known}")
print(f"Canonical persons: {len(anon.canonical_persons)}")

# FÁZE 3: _replace_remaining_people
print("\n=== FÁZE 3: _replace_remaining_people ===")
text_after_remaining = anon._replace_remaining_people(text_after_known)
print(f"Po remaining: {text_after_remaining}")
print(f"Canonical persons: {len(anon.canonical_persons)}")

print("\n=== VÝSLEDEK ===")
print("Canonical persons:")
for i, p in enumerate(anon.canonical_persons, 1):
    print(f"  {i}. {p['tag']}: '{p['first']}' '{p['last']}'")

print("\nEntity map PERSON:")
for canonical, variants in anon.entity_map['PERSON'].items():
    if canonical and ('Karel' in canonical or 'Karl' in canonical):
        print(f"  {canonical}:")
        for v in sorted(variants):
            if v.lower() != canonical.lower():
                print(f"    - {v}")
