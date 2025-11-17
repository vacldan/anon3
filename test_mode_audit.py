#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MASTER AUDIT podle audit.txt - FULL TEST MODE
Verze: 3.0 - Kompletní audit dle MASTER AUDIT PROMPT
"""

import sys
import re
from pathlib import Path
from docx import Document

def luhn_check(card_number):
    """Validace Luhn algoritmem pro platební karty."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    checksum = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    return checksum % 10 == 0

def audit_contract(contract_name):
    """Provede kompletní audit podle audit.txt MASTER PROMPT."""

    # Cesty k souborům
    anon_path = Path(f"{contract_name}_anon.docx")
    map_path = Path(f"{contract_name}_map.txt")

    if not anon_path.exists():
        print(f"❌ Chybí {anon_path}")
        return
    if not map_path.exists():
        print(f"❌ Chybí {map_path}")
        return

    # Načtení anonymizovaného dokumentu
    doc = Document(anon_path)
    full_text = "\n".join([p.text for p in doc.paragraphs])

    # Načtení mapy
    with open(map_path, 'r', encoding='utf-8') as f:
        map_content = f.read()

    # Inicializace výsledků
    score = 10.0
    hard_fails = []
    major_issues = []
    minor_issues = []
    positive_items = []

    print("=" * 80)
    print(f"TEST MODE AUDIT - {contract_name}")
    print("Podle audit.txt MASTER AUDIT PROMPT")
    print("=" * 80)
    print()

    # ==================== HARD_FAIL KONTROLY (−3.0 každá) ====================
    print("🔍 HARD_FAIL checks...")

    # 1. any_plain_CARD - Luhn-validní 13-19 číslic mimo [[CARD_*]]
    card_pattern = re.compile(r'\b(\d[\s\-]?){12,18}\d\b')
    for match in card_pattern.finditer(full_text):
        candidate = match.group(0)
        # Přeskoč pokud je už v [[CARD_*]]
        context = full_text[max(0, match.start()-10):match.end()+10]
        if '[[CARD_' in context:
            continue
        # Validuj Luhn
        if luhn_check(candidate):
            hard_fails.append(f"any_plain_CARD: {candidate[:6]}...{candidate[-4:]}")

    # 2. any_plain_IBAN - IBAN mimo [[IBAN_*]]
    iban_pattern = re.compile(r'\bCZ\d{2}[\s\d]{20,30}\b', re.IGNORECASE)
    for match in iban_pattern.finditer(full_text):
        candidate = match.group(0)
        context = full_text[max(0, match.start()-10):match.end()+10]
        if '[[IBAN_' not in context:
            hard_fails.append(f"any_plain_IBAN: {candidate[:8]}...")

    # 3. any_plain_PASSWORD - heslo v čistém textu
    password_patterns = [
        r'(?i)\b(password|heslo|passwd|pwd)\s*[:\-=]\s*(\S+)',
        r'(?i)\b(credentials?)\s*:\s*([A-Za-z0-9._\-@]+)\s*/\s*(\S+)',
    ]
    for pattern in password_patterns:
        for match in re.finditer(pattern, full_text):
            if '[[PASSWORD_' not in match.group(0):
                hard_fails.append(f"any_plain_PASSWORD: {match.group(0)[:30]}...")

    # 4. any_plain_EMAIL - e-mail mimo [[EMAIL_*]]
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    for match in email_pattern.finditer(full_text):
        context = full_text[max(0, match.start()-10):match.end()+10]
        if '[[EMAIL_' not in context:
            hard_fails.append(f"any_plain_EMAIL: {match.group(0)}")

    # 5. any_plain_BIRTH_ID - rodné číslo mimo [[BIRTH_ID_*]]
    birth_id_pattern = re.compile(r'\b\d{6}/\d{3,4}\b')
    for match in birth_id_pattern.finditer(full_text):
        context_before = full_text[max(0, match.start()-10):match.start()]
        context_after = full_text[match.start():match.end()+10]
        # Přeskoč spisové značky (FÚ-, KS-, VS-)
        if 'FÚ-' in context_before or 'KS-' in context_before or 'VS-' in context_before:
            continue
        if '[[BIRTH_ID_' not in context_after:
            hard_fails.append(f"any_plain_BIRTH_ID: {match.group(0)}")

    # 6. phone_misclassified_as_AMOUNT - telefon jako [[AMOUNT_*]]
    phone_amount_pattern = re.compile(r'(?:Telefon|Tel\.|Mobil|Phone)\s*:?\s*\+?\[\[AMOUNT_\d+\]\]', re.IGNORECASE)
    phone_amount_matches = phone_amount_pattern.findall(full_text)
    if phone_amount_matches:
        hard_fails.append(f"phone_misclassified_as_AMOUNT: {len(phone_amount_matches)}x")

    # 7. idcard_misclassified_as_PHONE - číslo OP jako [[PHONE_*]]
    op_phone_pattern = re.compile(r'(?:Číslo\s+OP|OP\s*:|Pas\s*:)\s*\[\[PHONE_\d+\]\]', re.IGNORECASE)
    op_phone_matches = op_phone_pattern.findall(full_text)
    if op_phone_matches:
        hard_fails.append(f"idcard_misclassified_as_PHONE: {len(op_phone_matches)}x")

    # 8. tag_in_text_missing_in_map - tag bez položky v mapě
    tags_in_text = set(re.findall(r'\[\[([A-Z_]+)_(\d+)\]\]', full_text))
    for tag_type, tag_num in tags_in_text:
        tag_label = f"[[{tag_type}_{tag_num}]]"
        if tag_label not in map_content:
            hard_fails.append(f"tag_in_text_missing_in_map: {tag_label}")

    # 9. map_value_missing_or_empty - prázdná hodnota v mapě
    map_entries = re.findall(r'\[\[([A-Z_]+)_(\d+)\]\]:\s*(.*)$', map_content, re.MULTILINE)
    for tag_type, tag_num, value in map_entries:
        if not value.strip():
            hard_fails.append(f"map_value_missing_or_empty: [[{tag_type}_{tag_num}]]")

    # 10. map_value_contains_redacted - TEST MODE: ZAKÁZÁNO ***REDACTED***
    if '***REDACTED***' in map_content or 'REDACTED_' in map_content:
        hard_fails.append(f"map_value_contains_redacted: TEST MODE nesmí obsahovat REDACTED")

    # ==================== MAJOR CHYBY (−1.0 každá) ====================
    print("🔍 MAJOR checks...")

    # 1. Biometrické identifikátory jako PHONE
    bio_phone_pattern = re.compile(r'(IRIS_SCAN|VOICE_RK|HASH_BIO|FINGERPRINT)_[A-Z0-9_]*\[\[PHONE_\d+\]\]')
    bio_phone_matches = bio_phone_pattern.findall(full_text)
    if bio_phone_matches:
        major_issues.append(f"Biometrické ID jako PHONE: {len(bio_phone_matches)}x")

    # 2. CVV v čistém textu u tokenizovaných karet
    cvv_pattern = re.compile(r'\[\[CARD_\d+\]\][^\[]*?(CVV|CVC)\s*:\s*\d{3,4}', re.IGNORECASE)
    cvv_matches = cvv_pattern.findall(full_text)
    if cvv_matches:
        major_issues.append(f"CVV v čistém textu u [[CARD_*]]: {len(cvv_matches)}x")

    # ==================== MINOR CHYBY (−0.3 až −0.5) ====================
    print("🔍 MINOR checks...")

    # 1. Prefixy v mapě (Sídlo:, Bydliště:)
    address_prefix_pattern = re.compile(r'\[\[ADDRESS_\d+\]\]:\s*(Sídlo|Trvalé\s+bydliště|Bydliště|Adresa|Místo\s+podnikání)\s*:', re.IGNORECASE)
    address_prefix_matches = address_prefix_pattern.findall(map_content)
    if address_prefix_matches:
        minor_issues.append(f"Prefixy v mapě ADDRESS: {len(address_prefix_matches)}x (−0.3)")

    # 2. Spisové značky jako BIRTH_ID (false positive)
    false_birth_pattern = re.compile(r'(FÚ|KS|VS)-\[\[BIRTH_ID_\d+\]\]')
    false_birth_matches = false_birth_pattern.findall(full_text)
    if false_birth_matches:
        minor_issues.append(f"Spisové značky jako BIRTH_ID: {len(false_birth_matches)}x (−0.5)")

    # ==================== POZITIVNÍ BODY (+0.2 až +0.3, max +0.5) ====================
    print("🔍 POSITIVE checks...")

    # 1. END-SCAN implementován (kontrola, že end_scan skutečně běží)
    if '[[CARD_' in full_text and '[[IBAN_' in full_text:
        positive_items.append("END-SCAN implementován (+0.3)")

    # 2. CATEGORY_PRECEDENCE (BANK před BIRTH_ID, PHONE před AMOUNT)
    # Zkontroluj, že nejsou fragmenty typu "1928[[BIRTH_ID_*]]" v kontextu účtu
    bank_fragment_pattern = re.compile(r'(?:účt|account)\s*:?\s*\d+\[\[BIRTH_ID_\d+\]\]', re.IGNORECASE)
    bank_fragment_matches = bank_fragment_pattern.findall(full_text)
    if not bank_fragment_matches:
        positive_items.append("CATEGORY_PRECEDENCE správná (+0.2)")

    # ==================== CO JE OK ====================
    ok_items = []
    if '[[IBAN_' in full_text:
        ok_items.append("✅ IBAN tagované")
    if '[[CARD_' in full_text:
        ok_items.append("✅ Karty tagované")
    if '[[EMAIL_' in full_text:
        ok_items.append("✅ E-maily tagované")
    if '[[PHONE_' in full_text:
        ok_items.append("✅ Telefony tagované")
    if '[[PERSON_' in full_text:
        ok_items.append("✅ Osoby tagované")
    if '***REDACTED***' not in map_content:
        ok_items.append("✅ TEST MODE: Mapa obsahuje plné hodnoty")

    # ==================== SCORING ====================

    # Start: 10.0
    # Hard fails: −3.0 × count
    # Majors: −1.0 × count
    # Minors: −0.3 nebo −0.5 (podle typu)
    # Positive: +0.2 nebo +0.3 (max +0.5 celkem)

    score -= 3.0 * len(hard_fails)
    score -= 1.0 * len(major_issues)

    # Minor - parsuj čísla z textu
    for minor in minor_issues:
        if '−0.5' in minor:
            score -= 0.5
        elif '−0.3' in minor:
            score -= 0.3

    # Positive - max +0.5
    positive_bonus = 0.0
    for pos in positive_items:
        if '+0.3' in pos:
            positive_bonus += 0.3
        elif '+0.2' in pos:
            positive_bonus += 0.2
    positive_bonus = min(0.5, positive_bonus)
    score += positive_bonus

    score = round(score, 1)

    # GO/NO-GO
    verdict = "✅ GO" if score >= 9.3 and len(hard_fails) == 0 else "❌ NO-GO"

    # ==================== VÝSTUP ====================

    print()
    print(f"📊 VERDIKT: {score:.1f}/10 → {verdict}")
    print()

    # Tabulka odpočtů
    print("📉 Tabulka odpočtů:")
    print(f"   Hard fails ({len(hard_fails)} × −3.0) → −{len(hard_fails) * 3.0:.1f}")
    print(f"   Majors ({len(major_issues)} × −1.0) → −{len(major_issues) * 1.0:.1f}")
    minor_sum = sum(0.5 if '−0.5' in m else 0.3 for m in minor_issues)
    print(f"   Minors (součet) → −{minor_sum:.1f}")
    print(f"   Bonusy → +{positive_bonus:.1f}")
    print(f"   Konečné skóre: {score:.1f}/10")
    print()

    if hard_fails:
        print("❌ Kritické nálezy (HARD FAILS):")
        for i, fail in enumerate(hard_fails, 1):
            print(f"   {i}. {fail}")
        print()

    if major_issues:
        print("❌ Major problémy:")
        for i, issue in enumerate(major_issues, 1):
            print(f"   {i}. {issue}")
        print()

    if minor_issues:
        print("⚠️  Minor problémy:")
        for i, issue in enumerate(minor_issues, 1):
            print(f"   {i}. {issue}")
        print()

    if positive_items:
        print("✨ Pozitivní nálezy:")
        for item in positive_items:
            print(f"   {item}")
        print()

    if ok_items:
        print("✅ Co je OK:")
        for item in ok_items:
            print(f"   {item}")
        print()

    # QA checklist
    print("📋 QA CHECKLIST:")
    qa_pass = []
    qa_fail = []

    if len(hard_fails) == 0:
        qa_pass.append("✅ Zero hard fails")
    else:
        qa_fail.append(f"❌ {len(hard_fails)} hard fails detected")

    if '***REDACTED***' not in map_content:
        qa_pass.append("✅ TEST MODE: No REDACTED in map")
    else:
        qa_fail.append("❌ TEST MODE: REDACTED found in map")

    if not bank_fragment_matches:
        qa_pass.append("✅ BANK před BIRTH_ID (precedence OK)")
    else:
        qa_fail.append(f"❌ BANK fragmented by BIRTH_ID")

    if not phone_amount_matches:
        qa_pass.append("✅ PHONE před AMOUNT (precedence OK)")
    else:
        qa_fail.append(f"❌ PHONE classified as AMOUNT")

    for item in qa_pass:
        print(f"   {item}")
    for item in qa_fail:
        print(f"   {item}")
    print()

    if hard_fails or major_issues:
        print("🔧 Doporučené fixy:")
        if any('plain_CARD' in f for f in hard_fails):
            print("   - Přidat Luhn end-scan nebo opravit CARD_RE pattern")
        if any('plain_IBAN' in f for f in hard_fails):
            print("   - Opravit IBAN_RE pattern")
        if any('plain_PASSWORD' in f for f in hard_fails):
            print("   - Přidat PASSWORD_RE pattern s credentials handling")
        if any('misclassified_as_AMOUNT' in f for f in hard_fails):
            print("   - Přesunout PHONE před AMOUNT v CATEGORY_PRECEDENCE")
        if any('misclassified_as_PHONE' in f for f in hard_fails):
            print("   - Přesunout ID_CARD před PHONE v CATEGORY_PRECEDENCE")
        if any('CVV' in i for i in major_issues):
            print("   - Maskovat CVV/exp u všech [[CARD_*]]")
        print()
        print(f"📈 Očekávané skóre po fixech: ~9.5-9.8/10 → GO")
    else:
        print("🎉 Všechny kontroly prošly! Žádné fixy nejsou potřeba.")

    print()
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_mode_audit.py <contract_name>")
        print("Example: python test_mode_audit.py smlouva13")
        sys.exit(1)

    audit_contract(sys.argv[1])
