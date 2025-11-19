#!/usr/bin/env python3
"""
GDPR Category Coverage Analysis
Compares implemented vs required categories
"""

print("="*80)
print("GDPR/PII CATEGORY COVERAGE ANALYSIS")
print("="*80)

implemented = {
    "CORE GDPR (Osobní data)": {
        "✅ Jména a příjmení": "PERSON_RE, _replace_remaining_people()",
        "✅ Datum narození": "BIRTH_DATE_RE",
        "✅ Adresy": "ADDRESS_RE",
        "✅ Telefony": "PHONE_RE",
        "✅ Emaily": "EMAIL_RE",
        "✅ Občanka": "ID_CARD_RE",
        "✅ Pas": "PASSPORT_RE",
        "✅ Řidičák": "DRIVER_LICENSE_RE",
        "✅ Číslo pojištěnce": "INSURANCE_ID_RE",
        "✅ Rodné číslo": "BIRTH_ID_RE",
        "✅ Bankovní účty": "BANK_RE, IBAN_RE",
        "✅ SPZ": "LICENSE_PLATE_RE",
    },
    "Zvláštní kategorie (citlivá data)": {
        "⚠️  Zdravotní údaje": "PARTIAL - no structured detection",
        "⚠️  Diagnózy": "PARTIAL - only if in specific context",
        "❌ Těhotenství/reprodukční": "MISSING (hard to detect)",
        "⚠️  Genetické údaje": "GENETIC_ID_RE (partial)",
        "❌ Sexuální život": "MISSING (hard to detect)",
        "❌ Trestní řízení": "MISSING (hard to detect)",
        "✅ NBÚ prověrky": "SECURITY_CLEARANCE_RE",
    },
    "Technické identifikátory (PII)": {
        "✅ MultiSport/Sodexo ID": "BENEFIT_CARD_RE",
        "✅ Číslo diplomu": "DIPLOMA_ID_RE",
        "✅ Lab ID": "LAB_ID_RE",
        "✅ Zaměstnanecké číslo": "EMPLOYEE_ID_RE",
        "✅ HR personal ID": "EMPLOYEE_ID_RE (same pattern)",
        "✅ Spisová čísla": "CASE_ID_RE",
    }
}

missing_count = 0
partial_count = 0
complete_count = 0

for category, items in implemented.items():
    print(f"\n{category}:")
    for item, status in items.items():
        print(f"  {item}: {status}")
        if item.startswith("❌"):
            missing_count += 1
        elif item.startswith("⚠️"):
            partial_count += 1
        else:
            complete_count += 1

print(f"\n{'='*80}")
print(f"SUMMARY:")
print(f"  ✅ Complete: {complete_count}")
print(f"  ⚠️  Partial:  {partial_count}")
print(f"  ❌ Missing:  {missing_count}")
print(f"{'='*80}")

print(f"\nRECENTLY ADDED ENTITY TYPES:")
print(f"  ✅ BIRTH_DATE_RE - datum narození (dd.mm.yyyy)")
print(f"  ✅ PASSPORT_RE - číslo pasu")
print(f"  ✅ DRIVER_LICENSE_RE - číslo řidičáku")
print(f"  ✅ BENEFIT_CARD_RE - MultiSport, Sodexo ID")
print(f"  ✅ DIPLOMA_ID_RE - VŠE/2015/12345")
print(f"  ✅ EMPLOYEE_ID_RE - zaměstnanecká čísla")
print(f"  ✅ SECURITY_CLEARANCE_RE - NBÚ/2023/VH/45678")
print(f"  ✅ LAB_ID_RE - GEN-2013-45678")
print(f"\nREMAINING GAPS (hard to detect patterns):")
print(f"  ⚠️  Těhotenství/reprodukční údaje - context-dependent")
print(f"  ⚠️  Sexuální život - context-dependent")
print(f"  ⚠️  Trestní řízení - context-dependent")
