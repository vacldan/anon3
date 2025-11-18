#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Přísný GDPR/PII Audit podle audit.txt
Hledá plain karty pomocí Luhn, plain IBAN, emails, atd.
"""

import json
import re
import time
from pathlib import Path
from docx import Document

def luhn_check(card_number):
    """Validate card number using Luhn algorithm"""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    checksum = 0
    reverse_digits = digits[::-1]

    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    return checksum % 10 == 0

def strict_audit_contract_14():
    """Přísný audit smlouvy 14 podle audit.txt"""

    start_time = time.time()

    print("=" * 80)
    print("PŘÍSNÝ AUDIT SMLOUVY 14 (podle audit.txt)")
    print("=" * 80)
    print()

    # Load files
    map_file = Path("smlouva14_map.json")
    anon_file = Path("smlouva14_anon.docx")

    if not map_file.exists() or not anon_file.exists():
        print("❌ Chybějící soubory!")
        return

    print("📂 Načítám soubory...")
    with open(map_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        entities_list = data['entities']
        # Convert to dict
        entity_map = {}
        for ent in entities_list:
            typ = ent['type']
            label = ent['label']
            original = ent['original']
            if typ not in entity_map:
                entity_map[typ] = {}
            entity_map[typ][label] = original

    doc = Document(anon_file)
    anon_text = '\n'.join([p.text for p in doc.paragraphs])

    print("✓ Soubory načteny")
    print()

    # Initialize scoring
    score = 10.0
    hard_fails = 0
    major_errors = 0
    minor_errors = 0
    bonuses = 0

    issues = []

    print("🔍 Kontrola HARD FAILs...")
    print()

    # ======== HARD FAIL 1: Plain CARD (v kontextu karta/Číslo/card) ========
    print("  [1/7] Hledám plain karty (context + pattern)...")

    # Pattern pro karty v kontextu: "Číslo:", "Karta:", "Card Number:"
    # Nejen Luhn - i nevalidní karty jsou PII!
    card_context_pattern = re.compile(
        r'(?:Číslo|Karta|Card(?:\s+Number)?|Platební\s+karta)\s*:?\s*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{1,7})',
        re.IGNORECASE
    )

    plain_cards = []
    for match in card_context_pattern.finditer(anon_text):
        card = match.group(1)

        # Skip if already tagged (check if [[CARD_ is nearby)
        match_pos = match.start()
        nearby_text = anon_text[max(0, match_pos-20):min(len(anon_text), match_pos+len(match.group())+20)]

        if "[[CARD_" not in nearby_text:
            plain_cards.append(card)
            # Get context
            context = anon_text[max(0, match_pos-50):min(len(anon_text), match_pos+len(match.group())+50)]
            issues.append(f"HARD FAIL: Plain CARD in text: {card}")
            issues.append(f"  Context: ...{context}...")
            print(f"    ❌ PLAIN CARD FOUND: {card}")
            print(f"       Context: ...{context[:80]}...")
            print(f"       Luhn-valid: {luhn_check(card)}")

    if plain_cards:
        hard_fails += len(plain_cards)
        print(f"    ❌ {len(plain_cards)} plain card(s) found!")
    else:
        print(f"    ✓ No plain cards")

    # ======== HARD FAIL 2: Plain IBAN ========
    print("  [2/7] Hledám plain IBAN...")
    iban_pattern = re.compile(r'\bCZ\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', re.IGNORECASE)
    plain_ibans = iban_pattern.findall(anon_text)

    if plain_ibans:
        hard_fails += len(plain_ibans)
        print(f"    ❌ {len(plain_ibans)} plain IBAN(s) found!")
        for iban in plain_ibans[:2]:
            issues.append(f"HARD FAIL: Plain IBAN: {iban}")
    else:
        print(f"    ✓ No plain IBANs")

    # ======== HARD FAIL 3: Plain EMAIL ========
    print("  [3/7] Hledám plain emails...")
    email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
    plain_emails = email_pattern.findall(anon_text)

    if plain_emails:
        hard_fails += len(plain_emails)
        print(f"    ❌ {len(plain_emails)} plain email(s) found!")
        for email in plain_emails[:2]:
            issues.append(f"HARD FAIL: Plain EMAIL: {email}")
    else:
        print(f"    ✓ No plain emails")

    # ======== HARD FAIL 4: Tags in text missing in map ========
    print("  [4/7] Kontrola tag ↔ map konzistence...")
    tag_pattern = re.compile(r'\[\[([A-Z_]+)_(\d+)\]\]')
    tags_in_text = set(tag_pattern.findall(anon_text))
    tags_in_map = set()

    for entity_type, entities in entity_map.items():
        for label in entities.keys():
            match = tag_pattern.match(label)
            if match:
                tags_in_map.add(match.groups())

    missing_in_map = tags_in_text - tags_in_map
    if missing_in_map:
        hard_fails += len(missing_in_map)
        print(f"    ❌ {len(missing_in_map)} tag(s) in text missing in map!")
        for typ, num in list(missing_in_map)[:3]:
            issues.append(f"HARD FAIL: [[{typ}_{num}]] in text but not in map")
    else:
        print(f"    ✓ All tags have map entries")

    # ======== HARD FAIL 5: REDACTED in map (TEST MODE violation) ========
    print("  [5/7] Kontrola ***REDACTED*** v mapě (TEST MODE)...")
    redacted_count = 0
    for entity_type, entities in entity_map.items():
        for label, value in entities.items():
            if "***REDACTED***" in str(value):
                redacted_count += 1
                issues.append(f"HARD FAIL: {label} has REDACTED in map (TEST MODE violation)")

    if redacted_count > 0:
        hard_fails += redacted_count
        print(f"    ❌ {redacted_count} REDACTED value(s) in map!")
    else:
        print(f"    ✓ No REDACTED values (TEST MODE OK)")

    # ======== HARD FAIL 6: Empty map values ========
    print("  [6/7] Kontrola prázdných hodnot v mapě...")
    empty_count = 0
    for entity_type, entities in entity_map.items():
        for label, value in entities.items():
            if not value or str(value).strip() == "":
                empty_count += 1
                issues.append(f"HARD FAIL: {label} has empty value in map")

    if empty_count > 0:
        hard_fails += empty_count
        print(f"    ❌ {empty_count} empty value(s) in map!")
    else:
        print(f"    ✓ No empty values in map")

    # ======== HARD FAIL 7: Plain passwords/API keys ========
    print("  [7/7] Hledám plain passwords/API keys...")
    password_pattern = re.compile(r'(?:password|heslo|passwd|pwd)\s*[:\-=]\s*([^\s,;\.]{3,})', re.IGNORECASE)
    apikey_pattern = re.compile(r'(?:API[_\s]?Key|Access\s+Key)\s*[:\-=]\s*([A-Za-z0-9+/=_\-]{16,})', re.IGNORECASE)

    plain_passwords = password_pattern.findall(anon_text)
    plain_apikeys = apikey_pattern.findall(anon_text)

    if plain_passwords:
        hard_fails += len(plain_passwords)
        print(f"    ❌ {len(plain_passwords)} plain password(s) found!")
    elif plain_apikeys:
        hard_fails += len(plain_apikeys)
        print(f"    ❌ {len(plain_apikeys)} plain API key(s) found!")
    else:
        print(f"    ✓ No plain passwords/API keys")

    print()
    print("🔍 Kontrola MAJOR chyb...")
    print()

    # ======== MAJOR 1: Card value mismatch (card in text vs card in map) ========
    print("  [1/3] Kontrola shody CARD hodnot text ↔ mapa...")

    # Check if plain card matches any card in map
    if plain_cards and 'CARD' in entity_map:
        for plain_card in plain_cards:
            plain_digits = ''.join(c for c in plain_card if c.isdigit())
            found_in_map = False

            for label, map_value in entity_map['CARD'].items():
                map_digits = ''.join(c for c in str(map_value) if c.isdigit())
                if plain_digits == map_digits:
                    found_in_map = True
                    break

            if not found_in_map:
                major_errors += 1
                map_cards_str = ', '.join([str(v) for v in entity_map['CARD'].values()])
                issues.append(f"MAJOR: CARD {plain_card} in text ≠ map values ({map_cards_str})")
                print(f"    ❌ Card mismatch: text={plain_card}, map={map_cards_str}")
    elif plain_cards and 'CARD' not in entity_map:
        major_errors += 1
        issues.append(f"MAJOR: CARD {plain_cards[0]} in text but no CARD in map at all")
        print(f"    ❌ Card in text but no CARD entities in map")

    # ======== MAJOR 2: Phone misclassified as AMOUNT ========
    print("  [2/3] Kontrola PHONE vs AMOUNT...")
    if 'PHONE' in entity_map:
        amount_contexts = ['Kč', 'EUR', 'USD', 'CZK', 'kapitál', 'valuác', 'invest']
        for label, value in entity_map['PHONE'].items():
            # Check context in text
            tag_pattern_str = re.escape(label)
            context_pattern = re.compile(rf'(.{{0,30}}){tag_pattern_str}(.{{0,30}})', re.IGNORECASE)
            matches = context_pattern.findall(anon_text)

            for before, after in matches:
                combined = before + after
                if any(ctx in combined for ctx in amount_contexts):
                    major_errors += 1
                    issues.append(f"MAJOR: {label} = {value} is AMOUNT, not PHONE")
                    print(f"    ❌ {label} misclassified (is AMOUNT)")
                    break

    # ======== MAJOR 3: Birth ID misclassified ========
    print("  [3/3] Kontrola BIRTH_ID klasifikace...")
    if 'BANK' in entity_map:
        birth_id_pattern = re.compile(r'\d{6}/\d{3,4}')
        for label, value in entity_map['BANK'].items():
            if birth_id_pattern.fullmatch(str(value).strip()):
                major_errors += 1
                issues.append(f"MAJOR: {label} = {value} should be BIRTH_ID, not BANK")
                print(f"    ❌ {label} is BIRTH_ID, not BANK")

    if major_errors == 0:
        print(f"    ✓ No major misclassifications")

    print()
    print("🔍 Kontrola MINOR chyb...")
    print()

    # ======== MINOR 1: Stuck characters ========
    print("  [1/3] Hledám nalepené znaky...")
    stuck_pattern = re.compile(r'([a-zA-Z0-9\-:\.]+)\[\[([A-Z_]+_\d+)\]\]')
    stuck_chars = stuck_pattern.findall(anon_text)

    stuck_count = len(stuck_chars) if stuck_chars else 0
    if stuck_count > 0:
        # Počítáme jako 1 minor issue (celkově), ne každý zvlášť
        minor_errors += 1
        print(f"    ⚠️  {stuck_count} stuck character(s) found")
        for chars, tag in stuck_chars[:3]:
            issues.append(f"MINOR: Stuck characters '{chars}' before [[{tag}]]")
    else:
        print(f"    ✓ No stuck characters")

    # ======== MINOR 2: Address prefixes ========
    print("  [2/3] Kontrola address prefixů...")
    if 'ADDRESS' in entity_map:
        prefix_pattern = re.compile(r'^(Sídlo|Trvalý\s+pobyt|Bydliště|Adresa)\s*:', re.IGNORECASE)
        addr_with_prefix = 0
        for label, value in entity_map['ADDRESS'].items():
            if prefix_pattern.search(str(value)):
                addr_with_prefix += 1
                issues.append(f"MINOR: {label} has prefix in map value")

        if addr_with_prefix > 0:
            minor_errors += addr_with_prefix
            print(f"    ⚠️  {addr_with_prefix} address(es) with prefixes")
        else:
            print(f"    ✓ No address prefixes")
    else:
        print(f"    ✓ No ADDRESS entities")

    # ======== MINOR 3: Unused tags ========
    print("  [3/3] Kontrola nepoužitých tagů...")
    unused = tags_in_map - tags_in_text
    if unused:
        minor_errors += len(unused)
        print(f"    ⚠️  {len(unused)} unused tag(s) in map")
        for typ, num in list(unused)[:3]:
            issues.append(f"MINOR: [[{typ}_{num}]] in map but not used")
    else:
        print(f"    ✓ No unused tags")

    # ======== BONUSES ========
    print()
    print("✨ Bonusy...")
    entity_count = sum(len(entities) for entities in entity_map.values())
    if entity_count > 100:
        bonuses += 0.2
        print(f"  +0.2 Comprehensive detection ({entity_count} entities)")

    if 'BIRTH_ID' in entity_map and len(entity_map['BIRTH_ID']) > 0:
        bonuses += 0.2
        print(f"  +0.2 Birth ID detection")

    if 'GENETIC_ID' in entity_map or 'VARIABLE_SYMBOL' in entity_map:
        bonuses += 0.1
        print(f"  +0.1 New entity types (GENETIC_ID/VARIABLE_SYMBOL)")

    # ======== CALCULATE SCORE ========
    score -= hard_fails * 3.0
    score -= major_errors * 1.0
    score -= minor_errors * 0.4  # Per audit.txt: stuck chars = -0.4
    score += min(0.5, bonuses)

    verdict = "✅ GO" if score >= 9.3 and hard_fails == 0 else "❌ NO-GO"

    elapsed = time.time() - start_time

    # ======== FINAL REPORT ========
    print()
    print("=" * 80)
    print("VERDIKT")
    print("=" * 80)
    print()
    print(f"Skóre: {score:.1f}/10.0 → {verdict}")
    print()
    print(f"Hard fails: {hard_fails} (-{hard_fails * 3.0:.1f} bodů)")
    print(f"Major chyby: {major_errors} (-{major_errors * 1.0:.1f} bodů)")
    print(f"Minor chyby: {minor_errors} (-{minor_errors * 0.4:.1f} bodů)")
    print(f"Bonusy: +{min(0.5, bonuses):.1f} bodů")
    print()
    print("=" * 80)
    print(f"Audit dokončen za {elapsed:.1f}s")
    print("=" * 80)
    print()

    if issues:
        print("KRITICKÉ NÁLEZY:")
        print()
        for issue in issues[:15]:
            print(f"  • {issue}")
        if len(issues) > 15:
            print(f"  ... a {len(issues) - 15} dalších")

    print()
    print("=" * 80)
    print()

    # Return values for programmatic use
    return {
        'score': score,
        'verdict': verdict,
        'hard_fails': hard_fails,
        'major_errors': major_errors,
        'minor_errors': minor_errors,
        'issues': issues
    }

if __name__ == '__main__':
    result = strict_audit_contract_14()

    print()
    print("Stiskněte ENTER pro ukončení...")
    try:
        input()
    except EOFError:
        # Running in non-interactive mode
        pass
