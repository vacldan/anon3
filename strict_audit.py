#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STRICT GDPR/PII Audit - podle MASTER AUDIT PROMPT (STRICT + FULL VALUES)
Verze: 2.0 - Přísný režim s full value logging a HARD_FAIL kontrolami
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
    """Provede přísný audit anonymizované smlouvy."""

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
    ok_items = []

    print("=" * 80)
    print(f"STRICT AUDIT - {contract_name}")
    print("=" * 80)
    print()

    # ==================== HARD_FAIL KONTROLY ====================

    # 1. PLATEBNÍ KARTY - Luhn-validní 13-19 číslic v čistém textu
    print("🔍 Kontroluji platební karty (Luhn)...")
    card_pattern = re.compile(r'\b(\d[\s\-]?){12,18}\d\b')
    for match in card_pattern.finditer(full_text):
        candidate = match.group(0)
        # Přeskoč pokud je už v [[CARD_*]]
        if '[[CARD_' in full_text[max(0, match.start()-10):match.end()+10]:
            continue
        # Validuj Luhn
        if luhn_check(candidate):
            hard_fails.append(f"❌ KRITICKÝ LEAK: Platební karta v čistém textu: {candidate[:4]} ... {candidate[-4:]}")
            score -= 3.0

    # 2. IBAN - CZ + 2 číslice + 20 číslic
    print("🔍 Kontroluji IBAN...")
    iban_pattern = re.compile(r'\bCZ\d{2}[\s\d]{20,30}\b', re.IGNORECASE)
    for match in iban_pattern.finditer(full_text):
        candidate = match.group(0)
        if '[[IBAN_' not in full_text[max(0, match.start()-10):match.end()+10]:
            hard_fails.append(f"❌ KRITICKÝ LEAK: IBAN v čistém textu: {candidate[:8]}...")
            score -= 3.0

    # 3. HESLA - credentials/password patterns
    print("🔍 Kontroluji hesla a credentials...")
    password_patterns = [
        r'(?i)\b(password|heslo|passwd|pwd)\s*[:\-=]\s*(\S+)',
        r'(?i)\b(credentials?)\s*:\s*([A-Za-z0-9._\-@]+)\s*/\s*(\S+)',
    ]
    for pattern in password_patterns:
        for match in re.finditer(pattern, full_text):
            if '[[PASSWORD_' not in match.group(0):
                hard_fails.append(f"❌ KRITICKÝ LEAK: Heslo v čistém textu: {match.group(0)[:40]}...")
                score -= 3.0

    # 4. EMAIL adresy
    print("🔍 Kontroluji e-maily...")
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    for match in email_pattern.finditer(full_text):
        if '[[EMAIL_' not in full_text[max(0, match.start()-10):match.end()+10]:
            hard_fails.append(f"❌ KRITICKÝ LEAK: Email v čistém textu: {match.group(0)}")
            score -= 3.0

    # 5. Rodná čísla
    print("🔍 Kontroluji rodná čísla...")
    birth_id_pattern = re.compile(r'\b\d{6}/\d{3,4}\b')
    for match in birth_id_pattern.finditer(full_text):
        if '[[BIRTH_ID_' not in full_text[max(0, match.start()-10):match.end()+10]:
            # Kontrola false positive - spisová značka "FÚ-"
            context_before = full_text[max(0, match.start()-5):match.start()]
            if 'FÚ-' not in context_before and 'KS-' not in context_before:
                hard_fails.append(f"❌ KRITICKÝ LEAK: Rodné číslo v čistém textu: {match.group(0)}")
                score -= 3.0

    # ==================== MIS-KLASIFIKACE ====================

    # 6. Čísla OP klasifikovaná jako PHONE
    print("🔍 Kontroluji klasifikaci čísel OP...")
    op_phone_pattern = re.compile(r'(?:Číslo\s+OP|OP\s*:)\s*\[\[PHONE_\d+\]\]', re.IGNORECASE)
    op_phone_matches = op_phone_pattern.findall(full_text)
    if op_phone_matches:
        major_issues.append(f"❌ MAJOR: Čísla OP klasifikovaná jako PHONE: {len(op_phone_matches)}x - mělo by být ID_CARD")
        score -= 1.0

    # 7. Telefony klasifikované jako AMOUNT
    print("🔍 Kontroluji klasifikaci telefonů...")
    phone_amount_pattern = re.compile(r'(?:Telefon|Tel\.|Mobil)\s*:?\s*\+?\[\[AMOUNT_\d+\]\]', re.IGNORECASE)
    phone_amount_matches = phone_amount_pattern.findall(full_text)
    if phone_amount_matches:
        major_issues.append(f"❌ MAJOR: Telefony klasifikované jako AMOUNT: {len(phone_amount_matches)}x")
        score -= 1.0

    # 8. Biometrické identifikátory klasifikované jako PHONE
    print("🔍 Kontroluji biometrické identifikátory...")
    bio_phone_pattern = re.compile(r'(IRIS_SCAN|VOICE_RK|HASH_BIO|FINGERPRINT)_[A-Z0-9_]+\[\[PHONE_\d+\]\]')
    bio_phone_matches = bio_phone_pattern.findall(full_text)
    if bio_phone_matches:
        major_issues.append(f"❌ MAJOR: Biometrické identifikátory jako PHONE: {len(bio_phone_matches)}x")
        score -= 1.0

    # ==================== CVV/EXPIRACE ====================

    # 9. CVV u tokenizovaných karet
    print("🔍 Kontroluji CVV a expirace...")
    cvv_pattern = re.compile(r'\[\[CARD_\d+\]\][^\[]*?(CVV|CVC)\s*:\s*\d{3,4}', re.IGNORECASE)
    cvv_matches = cvv_pattern.findall(full_text)
    if cvv_matches:
        hard_fails.append(f"❌ KRITICKÝ: CVV v čistém textu u tokenizovaných karet: {len(cvv_matches)}x")
        score -= 3.0

    # ==================== MAPA KONZISTENCE ====================

    # 10. Kontrola tagů v textu vs. mapě
    print("🔍 Kontroluji konzistenci mapy...")
    tags_in_text = set(re.findall(r'\[\[([A-Z_]+)_(\d+)\]\]', full_text))
    for tag_type, tag_num in tags_in_text:
        tag_label = f"[[{tag_type}_{tag_num}]]"
        if tag_label not in map_content:
            major_issues.append(f"❌ MAJOR: Tag {tag_label} v textu, ale chybí v mapě")
            score -= 1.0

    # ==================== POLISH ISSUES ====================

    # 11. BIRTH_ID falešné pozitivy (spisové značky)
    print("🔍 Kontroluji falešné pozitivy BIRTH_ID...")
    false_birth_pattern = re.compile(r'(FÚ|KS|VS)-\[\[BIRTH_ID_\d+\]\]')
    false_birth_matches = false_birth_pattern.findall(full_text)
    if false_birth_matches:
        minor_issues.append(f"⚠️  MINOR: BIRTH_ID použitý pro spisové značky: {len(false_birth_matches)}x")
        score -= 0.5

    # ==================== CO JE OK ====================

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

    # ==================== VÝSTUP ====================

    print()
    verdict = "✅ GO" if score >= 9.3 and len(hard_fails) == 0 else "❌ NO-GO"
    print(f"📊 Verdikt: {score:.1f}/10 → {verdict}")
    print()

    if hard_fails:
        print("❌ Kritické nálezy (HARD_FAILS):")
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

    if ok_items:
        print("✅ Co je OK:")
        for item in ok_items:
            print(f"   {item}")
        print()

    # Doporučené fixy
    if hard_fails or major_issues:
        print("🔧 Doporučené fixy:")
        if any('Platební karta' in f for f in hard_fails):
            print("   - Přidat Luhn end-scan do _end_scan() metody")
        if any('CVV' in f for f in hard_fails):
            print("   - Maskovat CVV/exp u všech [[CARD_*]]")
        if any('Heslo' in f or 'credentials' in f.lower() for f in hard_fails):
            print("   - Přidat credentials pattern s USERNAME + PASSWORD tagy")
        if any('OP' in i for i in major_issues):
            print("   - Opravit ID_CARD_RE a zpracovat před PHONE_RE")
        if any('biometric' in i.lower() for i in major_issues):
            print("   - Přidat whitelist pro biometrické prefixy")
        if any('spisové' in i for i in minor_issues):
            print("   - Zpřesnit BIRTH_ID pattern s kontextovými klíčovými slovy")
        print()

    print(f"📈 Očekávané skóre po fixech: 9.5-9.8/10 → GO")
    print()
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python strict_audit.py <contract_name>")
        print("Example: python strict_audit.py smlouva13")
        sys.exit(1)

    audit_contract(sys.argv[1])
