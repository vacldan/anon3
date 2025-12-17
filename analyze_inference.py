#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/user/anon3')

# Import inference funkce
exec(open('anon7.2 - s padama.py').read())

# Test co inference vrací
test_cases = [
    ("Pavel Zíka", "genitiv - v dokumentu"),
    ("Pavla Zíky", "genitiv - v dokumentu"),
    ("Pavlovi Zíkovi", "dativ - v dokumentu"),
    ("Václava Holase", "genitiv - v dokumentu")
]

print("=== TEST INFERENCE ===\n")
for surname, desc in test_cases:
    result = infer_surname_nominative(surname)
    print(f"{surname:20} ({desc:25}) → {result}")
