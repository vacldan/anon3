#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive GDPR/PII Audit Script
Audits anonymized contracts according to audit.txt rules
"""

import json
import re
from pathlib import Path

def luhn_check(card_number):
    """Validate card number using Luhn algorithm"""
    digits = [int(d) for d in card_number if d.isdigit()]
    checksum = 0
    reverse_digits = digits[::-1]

    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    return checksum % 10 == 0

def audit_contract(contract_num):
    """Perform thorough audit on a contract"""
    print(f"\n{'='*80}")
    print(f"AUDITING CONTRACT {contract_num}")
    print(f"{'='*80}\n")

    # Load files
    map_file = Path(f"smlouva{contract_num}_map.json")
    anon_file = Path(f"smlouva{contract_num}_anon.docx")

    if not map_file.exists() or not anon_file.exists():
        print(f"❌ Missing files for contract {contract_num}")
        return

    with open(map_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Handle both old and new JSON formats
        if isinstance(data, dict) and 'entities' in data:
            # New format: list of entity objects
            entities_list = data['entities']
            # Convert to dict format for easier processing
            entity_map = {}
            for ent in entities_list:
                typ = ent['type']
                label = ent['label']
                original = ent['original']
                if typ not in entity_map:
                    entity_map[typ] = {}
                entity_map[typ][label] = original
        else:
            # Old format: already a dict
            entity_map = data

    # Read anonymized text
    from docx import Document
    doc = Document(anon_file)
    anon_text = '\n'.join([p.text for p in doc.paragraphs])

    # Initialize scoring
    score = 10.0
    hard_fails = 0
    major_errors = 0
    minor_errors = 0
    bonuses = 0

    issues = []

    # ======== HARD FAIL CHECKS (−3.0 each) ========

    # 1. Check for ***REDACTED*** in map values (TEST MODE violation)
    redacted_count = 0
    for entity_type, entities in entity_map.items():
        for tag, value in entities.items():
            if "***REDACTED***" in str(value):
                redacted_count += 1
                issues.append(f"HARD FAIL: {tag} has REDACTED value in map")

    if redacted_count > 0:
        hard_fails += redacted_count
        print(f"❌ HARD FAIL: {redacted_count} entities have ***REDACTED*** values (TEST MODE violation)")
    else:
        print(f"✅ No REDACTED values in map")

    # 2. Check for plain IBANs in text
    iban_pattern = re.compile(r'\bCZ\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', re.IGNORECASE)
    plain_ibans = iban_pattern.findall(anon_text)
    if plain_ibans:
        hard_fails += len(plain_ibans)
        print(f"❌ HARD FAIL: {len(plain_ibans)} plain IBANs found in text")
        for iban in plain_ibans[:3]:
            issues.append(f"HARD FAIL: Plain IBAN in text: {iban}")
    else:
        print(f"✅ No plain IBANs in text")

    # 3. Check for plain emails in text
    email_pattern = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
    plain_emails = email_pattern.findall(anon_text)
    if plain_emails:
        hard_fails += len(plain_emails)
        print(f"❌ HARD FAIL: {len(plain_emails)} plain emails found in text")
        for email in plain_emails[:3]:
            issues.append(f"HARD FAIL: Plain email in text: {email}")
    else:
        print(f"✅ No plain emails in text")

    # 4. Check for plain cards in text
    card_pattern = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
    potential_cards = card_pattern.findall(anon_text)
    plain_cards = [c for c in potential_cards if luhn_check(c)]
    if plain_cards:
        hard_fails += len(plain_cards)
        print(f"❌ HARD FAIL: {len(plain_cards)} plain card numbers found in text")
        for card in plain_cards[:3]:
            issues.append(f"HARD FAIL: Plain card in text: {card}")
    else:
        print(f"✅ No plain card numbers in text")

    # 5. Check for tags in text missing in map
    tag_pattern = re.compile(r'\[\[([A-Z_]+)_(\d+)\]\]')
    tags_in_text = set(tag_pattern.findall(anon_text))
    tags_in_map = set()
    for entity_type, entities in entity_map.items():
        for tag in entities.keys():
            match = tag_pattern.match(tag)
            if match:
                tags_in_map.add(match.groups())

    missing_in_map = tags_in_text - tags_in_map
    if missing_in_map:
        hard_fails += len(missing_in_map)
        print(f"❌ HARD FAIL: {len(missing_in_map)} tags in text missing in map")
        for typ, num in list(missing_in_map)[:5]:
            issues.append(f"HARD FAIL: [[{typ}_{num}]] in text but not in map")
    else:
        print(f"✅ All tags in text are in map")

    # ======== MAJOR ERROR CHECKS (−1.0 each) ========

    # 1. Check for birth IDs misclassified as BANK
    if 'BANK' in entity_map:
        birth_id_pattern = re.compile(r'\d{6}/\d{3,4}')
        misclassified = 0
        for tag, value in entity_map['BANK'].items():
            if birth_id_pattern.fullmatch(str(value).strip()):
                misclassified += 1
                issues.append(f"MAJOR: {tag} = {value} should be BIRTH_ID, not BANK")

        if misclassified > 0:
            major_errors += misclassified
            print(f"❌ MAJOR: {misclassified} birth IDs misclassified as BANK")
        else:
            print(f"✅ No birth IDs misclassified as BANK")

    # 2. Check for amounts tagged as PHONE
    if 'PHONE' in entity_map:
        # Check context in text for each PHONE tag
        amount_contexts = ['Kč', 'EUR', 'USD', 'CZK', 'kapitál', 'valuác', 'invest', 'fond']
        misclass_phones = 0
        for tag, value in entity_map['PHONE'].items():
            # Find tag in text with context
            tag_pattern_str = re.escape(tag)
            context_pattern = re.compile(rf'(.{{0,50}}){tag_pattern_str}(.{{0,50}})', re.IGNORECASE)
            matches = context_pattern.findall(anon_text)

            for before, after in matches:
                combined = before + after
                if any(ctx in combined for ctx in amount_contexts):
                    misclass_phones += 1
                    issues.append(f"MAJOR: {tag} = {value} is AMOUNT, not PHONE (context: ...{before[:20]}...{after[:20]}...)")
                    break

        if misclass_phones > 0:
            major_errors += misclass_phones
            print(f"❌ MAJOR: {misclass_phones} amounts misclassified as PHONE")
        else:
            print(f"✅ No amounts misclassified as PHONE")

    # 3. Check for VS (variable symbols) tagged as PHONE
    if 'PHONE' in entity_map:
        vs_pattern_in_text = re.compile(r'VS[\s:]*\[\[PHONE_\d+\]\]', re.IGNORECASE)
        vs_matches = vs_pattern_in_text.findall(anon_text)
        if vs_matches:
            major_errors += len(vs_matches)
            print(f"❌ MAJOR: {len(vs_matches)} VS symbols misclassified as PHONE")
            for match in vs_matches[:3]:
                issues.append(f"MAJOR: Variable symbol tagged as PHONE: {match}")
        else:
            print(f"✅ No VS symbols misclassified as PHONE")

    # 4. Check for genetic IDs (rs...) tagged as ICO
    if 'ICO' in entity_map:
        genetic_pattern = re.compile(r'rs\d{6,}', re.IGNORECASE)
        misclass_genetic = 0
        for tag, value in entity_map['ICO'].items():
            if genetic_pattern.fullmatch(str(value).strip()):
                misclass_genetic += 1
                issues.append(f"MAJOR: {tag} = {value} should be GENETIC_ID, not ICO")

        if misclass_genetic > 0:
            major_errors += misclass_genetic
            print(f"❌ MAJOR: {misclass_genetic} genetic IDs misclassified as ICO")
        else:
            print(f"✅ No genetic IDs misclassified as ICO")

    # ======== MINOR ERROR CHECKS (−0.3 each) ========

    # 1. Check for address prefixes in map values
    if 'ADDRESS' in entity_map:
        prefix_pattern = re.compile(r'^(Sídlo|Trvalý\s+pobyt|Trvalé\s+bydliště|Bydliště|Adresa|Se\s+sídlem)\s*:', re.IGNORECASE)
        addr_with_prefix = 0
        for tag, value in entity_map['ADDRESS'].items():
            if prefix_pattern.search(str(value)):
                addr_with_prefix += 1
                issues.append(f"MINOR: {tag} has prefix in value: {value[:50]}")

        if addr_with_prefix > 0:
            minor_errors += addr_with_prefix
            print(f"⚠️  MINOR: {addr_with_prefix} addresses have prefixes in map values")
        else:
            print(f"✅ No address prefixes in map values")

    # 2. Check for unused tags in map
    unused_in_text = tags_in_map - tags_in_text
    if unused_in_text:
        minor_errors += len(unused_in_text)
        print(f"⚠️  MINOR: {len(unused_in_text)} tags in map but not used in text")
        for typ, num in list(unused_in_text)[:5]:
            issues.append(f"MINOR: [[{typ}_{num}]] in map but not in text")
    else:
        print(f"✅ No unused tags in map")

    # 3. Check for stuck characters (characters directly before [[TAG]])
    stuck_pattern = re.compile(r'([a-zA-Z]+)\[\[([A-Z_]+_\d+)\]\]')
    stuck_chars = stuck_pattern.findall(anon_text)
    if stuck_chars:
        minor_errors += len(stuck_chars)
        print(f"⚠️  MINOR: {len(stuck_chars)} stuck characters found")
        for chars, tag in stuck_chars[:5]:
            issues.append(f"MINOR: Stuck characters '{chars}' before [[{tag}]]")
    else:
        print(f"✅ No stuck characters")

    # 4. Check for bank account fragments
    bank_fragment_pattern = re.compile(r'\d{1,6}-\[\[BANK_\d+\]\]')
    bank_fragments = bank_fragment_pattern.findall(anon_text)
    if bank_fragments:
        minor_errors += len(bank_fragments)
        print(f"⚠️  MINOR: {len(bank_fragments)} bank account fragments found")
        for frag in bank_fragments[:5]:
            issues.append(f"MINOR: Bank fragment in text: {frag}")
    else:
        print(f"✅ No bank account fragments")

    # ======== BONUSES (+0.5 max) ========

    # Check for comprehensive entity detection
    entity_count = sum(len(entities) for entities in entity_map.values())
    person_count = len(entity_map.get('PERSON', {}))
    birth_id_count = len(entity_map.get('BIRTH_ID', {}))

    if entity_count > 100:
        bonuses += 0.2
        print(f"✅ BONUS: Comprehensive detection ({entity_count} entities)")

    if birth_id_count > 0:
        bonuses += 0.2
        print(f"✅ BONUS: Birth ID detection ({birth_id_count} found)")

    if person_count > 0:
        bonuses += 0.1
        print(f"✅ BONUS: Person detection ({person_count} found)")

    # ======== CALCULATE FINAL SCORE ========

    score -= hard_fails * 3.0
    score -= major_errors * 1.0
    score -= minor_errors * 0.3
    score += bonuses

    # Determine verdict
    verdict = "✅ GO" if score >= 9.3 and hard_fails == 0 else "❌ NO-GO"

    print(f"\n{'-'*80}")
    print(f"FINAL SCORE: {score:.1f}/10.0")
    print(f"HARD FAILs: {hard_fails} (-{hard_fails * 3.0:.1f} points)")
    print(f"MAJOR errors: {major_errors} (-{major_errors * 1.0:.1f} points)")
    print(f"MINOR errors: {minor_errors} (-{minor_errors * 0.3:.1f} points)")
    print(f"BONUSES: +{bonuses:.1f} points")
    print(f"VERDICT: {verdict}")
    print(f"{'-'*80}\n")

    if issues:
        print(f"\nTOP ISSUES:")
        for issue in issues[:20]:
            print(f"  - {issue}")

    return {
        'contract': contract_num,
        'score': score,
        'hard_fails': hard_fails,
        'major_errors': major_errors,
        'minor_errors': minor_errors,
        'bonuses': bonuses,
        'verdict': verdict,
        'issues': issues
    }

if __name__ == '__main__':
    import sys

    contracts = [13, 14, 15] if len(sys.argv) == 1 else [int(x) for x in sys.argv[1:]]

    results = []
    for contract_num in contracts:
        result = audit_contract(contract_num)
        if result:
            results.append(result)

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")

    for r in results:
        print(f"Contract {r['contract']}: {r['score']:.1f}/10 - {r['verdict']} (HF:{r['hard_fails']}, MAJ:{r['major_errors']}, MIN:{r['minor_errors']})")

    avg_score = sum(r['score'] for r in results) / len(results) if results else 0
    all_go = all(r['verdict'] == "✅ GO" for r in results)

    print(f"\nAverage Score: {avg_score:.1f}/10")
    print(f"All GO: {'✅ YES' if all_go else '❌ NO'}")
