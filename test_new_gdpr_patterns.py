#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test nových GDPR entity typů"""

import re
from pathlib import Path
import sys

# Import patterns from main code
sys.path.insert(0, str(Path(__file__).parent))
from Claude_code_6_complete import (
    BIRTH_DATE_RE, PASSPORT_RE, DRIVER_LICENSE_RE,
    BENEFIT_CARD_RE, DIPLOMA_ID_RE, EMPLOYEE_ID_RE,
    SECURITY_CLEARANCE_RE, LAB_ID_RE
)

print("="*80)
print("TEST NOVÝCH GDPR ENTITY PATTERNS")
print("="*80)

# Test data pro každý nový pattern
test_cases = {
    "BIRTH_DATE": [
        ("datum narození: 15.3.1985", "15.3.1985"),
        ("nar. 1.1.1990", "1.1.1990"),
        ("narozená 12/05/1978", "12/05/1978"),
        ("datum narození: 28-11-1995", "28-11-1995"),
    ],

    "PASSPORT": [
        ("pas: 12345678", "12345678"),
        ("č. pasu AB123456", "AB123456"),
        ("passport: 87654321", "87654321"),
        ("pas č. 99887766", "99887766"),
    ],

    "DRIVER_LICENSE": [
        ("ŘP: 12345678", "12345678"),
        ("řidičák č. AB123456", "AB123456"),
        ("řidičský průkaz: 87654321", "87654321"),
        ("driver's license E1234567", "E1234567"),
    ],

    "BENEFIT_CARD": [
        ("MultiSport: MS-123456789", "MS-123456789"),
        ("Sodexo karta: SDX123456789", "SDX123456789"),
        ("Edenred č. EDN/12345678", "EDN/12345678"),
        ("benefitní karta: BEN123456", "BEN123456"),
    ],

    "DIPLOMA_ID": [
        ("diplom č.: VŠE/2015/12345", "VŠE/2015/12345"),
        ("matrika ČVUT-2020-45678", "ČVUT-2020-45678"),
        ("diploma number: UK/2018/98765", "UK/2018/98765"),
        ("diplom MU-2022-11223", "MU-2022-11223"),
    ],

    "EMPLOYEE_ID": [
        ("zaměstnanecké číslo: EMP-12345", "EMP-12345"),
        ("employee ID: ZAM/123456", "ZAM/123456"),
        ("personální číslo EMP12345", "EMP12345"),
        ("zaměstnanec ID: 654321", "654321"),
    ],

    "SECURITY_CLEARANCE": [
        ("NBÚ/2023/VH/45678", "2023/VH/45678"),
        ("prověrka: 2022-TAJ-12345", "2022-TAJ-12345"),
        ("NBÚ č. 2021/VT/98765", "2021/VT/98765"),
        ("security clearance: 2024/DUV/11223", "2024/DUV/11223"),
    ],

    "LAB_ID": [
        ("GEN-2013-45678", "GEN-2013-45678"),
        ("LAB/2023/12345", "LAB/2023/12345"),
        ("PL-Boh/2021/45879", "PL-Boh/2021/45879"),
        ("laboratorní ID: LAB-2020-99887", "LAB-2020-99887"),
    ],
}

# Mapování pattern → regex
patterns = {
    "BIRTH_DATE": BIRTH_DATE_RE,
    "PASSPORT": PASSPORT_RE,
    "DRIVER_LICENSE": DRIVER_LICENSE_RE,
    "BENEFIT_CARD": BENEFIT_CARD_RE,
    "DIPLOMA_ID": DIPLOMA_ID_RE,
    "EMPLOYEE_ID": EMPLOYEE_ID_RE,
    "SECURITY_CLEARANCE": SECURITY_CLEARANCE_RE,
    "LAB_ID": LAB_ID_RE,
}

total_tests = 0
passed = 0
failed = 0

for entity_type, test_list in test_cases.items():
    print(f"\n{'='*80}")
    print(f"Testing {entity_type}")
    print(f"{'='*80}")

    pattern = patterns[entity_type]

    for test_text, expected_value in test_list:
        total_tests += 1
        match = pattern.search(test_text)

        if match:
            # Získej první non-None capture group (pro patterns s více alternativami)
            captured = None
            for i in range(1, match.lastindex + 1 if match.lastindex else 1):
                if match.group(i) is not None:
                    captured = match.group(i)
                    break
            if captured is None:
                captured = match.group(0)

            if captured == expected_value:
                print(f"✅ PASS: '{test_text}' → '{captured}'")
                passed += 1
            else:
                print(f"❌ FAIL: '{test_text}'")
                print(f"   Expected: '{expected_value}'")
                print(f"   Got: '{captured}'")
                failed += 1
        else:
            print(f"❌ FAIL: '{test_text}' → NO MATCH")
            print(f"   Expected: '{expected_value}'")
            failed += 1

print(f"\n{'='*80}")
print(f"TEST SUMMARY")
print(f"{'='*80}")
print(f"Total: {total_tests}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"Success rate: {passed/total_tests*100:.1f}%")
print(f"{'='*80}")

if failed == 0:
    print("\n🎉 ALL TESTS PASSED - Patterns are working correctly!")
    sys.exit(0)
else:
    print(f"\n⚠️  {failed} tests failed - Review patterns")
    sys.exit(1)
