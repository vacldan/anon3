#!/usr/bin/env python3
"""Test surname inference for -ské endings"""

def infer_surname_nominative(obs):
    """Infer nominative form of Czech surname"""
    lo = obs.lower()

    # -é → -á (genitiv/dativ/lokál žen: Pokorné → Pokorná, Houfové → Houfová)
    if lo.endswith('é') and len(obs) > 3:
        # SPECIÁLNÍ: "-ské" může být genitiv od "-ská" (Panské → Panská)
        # nebo přídavné jméno (Novákské zůstává)
        # Heuristika: pokud je krátké (max 8 znaků) a nezačíná velkým písmenem uvnitř,
        # je to pravděpodobně genitiv příjmení
        if lo.endswith('ské'):
            # Pokud je to krátké slovo bez velkých písmen uprostřed → genitiv příjmení
            if len(obs) <= 10:  # Krátké příjmení
                return obs[:-1] + 'á'  # -ské → -ská (Panské → Panská, Horské → Horská)
        # Pro ostatní -é (ne -ské/-cké)
        elif not lo.endswith('cké'):
            return obs[:-1] + 'á'

    return obs

# Test cases
test_cases = [
    ("Horské", "Horská"),
    ("Panské", "Panská"),
    ("Houfové", "Houfová"),
    ("Pokorné", "Pokorná"),
]

print("Testing surname inference:")
print("=" * 50)

all_passed = True
for input_name, expected in test_cases:
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
