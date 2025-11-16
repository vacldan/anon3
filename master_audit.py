#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MASTER AUDIT PRO GDPR/PII ANONYMIZACI
Seniorní auditor - nekompromisní, konstruktivní
"""
import re
import json
from pathlib import Path
from docx import Document

def load_names_library(json_path="cz_names.v1.json"):
    """Načte knihovnu jmen."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            names = set()
            if 'firstnames' in data:
                for gender in ['M', 'F', 'U']:
                    if gender in data['firstnames']:
                        names.update([n.lower() for n in data['firstnames'][gender]])
            return names
    except:
        return set()

def normalize_name(name):
    """Normalizuje jméno (bez diakritiky, lowercase)."""
    import unicodedata
    return unicodedata.normalize('NFKD', name.lower()).encode('ascii', 'ignore').decode('ascii')

def audit_contract(contract_name, names_lib):
    """Provede master audit jedné smlouvy."""
    
    anon_file = f"{contract_name}_anon.docx"
    map_file = f"{contract_name}_map.txt"
    
    if not Path(anon_file).exists():
        return None
    
    # Načti anonymizovaný text
    doc = Document(anon_file)
    anon_text = '\n'.join([p.text for p in doc.paragraphs])
    
    # Načti mapu
    with open(map_file, 'r', encoding='utf-8') as f:
        map_text = f.read()
    
    # Scoring - start 10/10
    score = 10.0
    issues = []
    
    # ========================================
    # KRITICKÉ LEAKY (každý -3 body)
    # ========================================
    
    # 1. PLATEBNÍ KARTY v čistém textu
    card_patterns = [
        r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{2,3})?)\b',  # 13-19 číslic
        r'(?i)(?:karta|card)[\s\d:]*(\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4})',
    ]
    for pattern in card_patterns:
        cards_found = re.findall(pattern, anon_text)
        clean_cards = [c for c in cards_found if not c.startswith('[[') and len(c.replace(' ', '').replace('-', '')) >= 13]
        if clean_cards:
            for card in clean_cards[:3]:  # max 3 příklady
                issues.append(f"❌ KRITICKÝ LEAK: Platební karta v čistém textu: {card[:20]}...")
                score -= 3.0
    
    # 2. E-MAILY v čistém textu
    emails = re.findall(r'(?<!\w)([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?!\w)', anon_text)
    clean_emails = [e for e in emails if not e.startswith('[[')]
    if clean_emails:
        issues.append(f"❌ KRITICKÝ LEAK: E-maily v čistém textu: {len(clean_emails)}x - {clean_emails[:2]}")
        score -= 3.0
    
    # 3. RODNÁ ČÍSLA v čistém textu
    birth_ids = re.findall(r'\b(\d{6}/\d{3,4})\b', anon_text)
    clean_birth = [b for b in birth_ids if not '[[BIRTH_ID' in anon_text[max(0, anon_text.find(b)-10):anon_text.find(b)+len(b)+10]]
    if clean_birth:
        issues.append(f"❌ KRITICKÝ LEAK: Rodná čísla: {len(clean_birth)}x")
        score -= 3.0
    
    # 4. HESLA - kontrola konzistence s mapou
    password_tags_in_text = re.findall(r'\[\[PASSWORD_(\d+)\]\]', anon_text)
    password_tags_in_map = re.findall(r'\[\[PASSWORD_(\d+)\]\]', map_text)
    if set(password_tags_in_text) != set(password_tags_in_map):
        missing = set(password_tags_in_text) - set(password_tags_in_map)
        if missing:
            issues.append(f"❌ MAJOR: PASSWORD tagy v textu chybí v mapě: {missing}")
            score -= 1.0
    
    # 5. API KLÍČE, SECRETS v čistém textu
    api_keys = re.findall(r'(?i)(?:AWS|Access|Secret|API|Token)\s*[:\-=]\s*([A-Za-z0-9+/=_\-]{16,})', anon_text)
    clean_api = [k for k in api_keys if not k.startswith('[[')]
    if clean_api:
        issues.append(f"❌ KRITICKÝ LEAK: API klíče/Secrets: {len(clean_api)}x")
        score -= 3.0
    
    # 6. IP ADRESY v čistém textu
    ips = re.findall(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', anon_text)
    clean_ips = [ip for ip in ips if not ip.startswith('[[') and not '[[IP' in anon_text[max(0, anon_text.find(ip)-5):anon_text.find(ip)+len(ip)+5]]
    if clean_ips:
        issues.append(f"⚠️  IP adresy v čistém textu: {len(clean_ips)}x - {clean_ips[:2]}")
        score -= 1.5
    
    # 7. USERNAMES v čistém textu
    usernames = re.findall(r'(?i)(?:Login|Username|User)\s*:\s*([A-Za-z0-9._\-@]+)', anon_text)
    clean_users = [u for u in usernames if not u.startswith('[[')]
    if clean_users:
        issues.append(f"⚠️  Usernames v čistém textu: {len(clean_users)}x")
        score -= 1.0
    
    # ========================================
    # MAJOR PROBLÉMY (každý -1 bod)
    # ========================================
    
    # 8. TELEFONY vs AMOUNT - špatná klasifikace
    phone_as_amount = re.findall(r'(?i)(?:telefon|mobil|tel\.?|GSM)\s*:?\s*(?:\+420\s*)?\[\[AMOUNT_\d+\]\]', anon_text)
    if phone_as_amount:
        issues.append(f"❌ MAJOR: Telefony klasifikované jako AMOUNT: {len(phone_as_amount)}x")
        score -= 1.0
    
    # 9. ČÍSLO OP jako PHONE
    op_as_phone = re.findall(r'(?i)(?:číslo\s+OP|OP\s*:)\s*\[\[PHONE_\d+\]\]', anon_text)
    if op_as_phone:
        issues.append(f"❌ MAJOR: Čísla OP klasifikovaná jako PHONE: {len(op_as_phone)}x - mělo by být ID_CARD")
        score -= 1.0
    
    # 10. PHONE hodnoty se šumem v mapě (": 123456789")
    phone_noise = re.findall(r'\[\[PHONE_\d+\]\]:\s+(:\s*\d+)', map_text)
    if phone_noise:
        issues.append(f"⚠️  PHONE hodnoty v mapě mají šum (':' prefix): {len(phone_noise)}x")
        score -= 0.5
    
    # 11. ADDRESS tagy bez záznamu v mapě
    address_tags_text = set(re.findall(r'\[\[ADDRESS_(\d+)\]\]', anon_text))
    address_tags_map = set(re.findall(r'\[\[ADDRESS_(\d+)\]\]', map_text))
    missing_addr = address_tags_text - address_tags_map
    if missing_addr:
        issues.append(f"❌ MAJOR: ADDRESS tagy bez záznamu v mapě: {len(missing_addr)}x")
        score -= 1.0
    
    # ========================================
    # MINOR PROBLÉMY (každý -0.5 bodu)
    # ========================================
    
    # 12. Typografie - ".]" pattern
    typo_artifacts = len(re.findall(r'\]\]\s*\.', anon_text))
    if typo_artifacts > 5:
        issues.append(f"⚠️  MINOR: Typografické artefakty (']].'): {typo_artifacts}x")
        score -= 0.5
    
    # 13. Slepené tagy
    glued_tags = re.findall(r'\]\]\[', anon_text)
    if glued_tags:
        issues.append(f"⚠️  MINOR: Slepené tagy (']][['): {len(glued_tags)}x")
        score -= 0.5
    
    # ========================================
    # POZITIVNÍ KONTROLY
    # ========================================
    ok_items = []
    
    if '[[BANK_' in map_text or '[[IBAN_' in map_text:
        ok_items.append("BANK/IBAN tagované")
    if '[[BIRTH_ID_' in map_text:
        ok_items.append("RČ (BIRTH_ID)")
    if '[[EMAIL_' in map_text:
        ok_items.append("EMAIL")
    if '[[ADDRESS_' in map_text:
        ok_items.append("ADDRESS")
    if '[[IP_' in map_text:
        ok_items.append("IP")
    if '[[USERNAME_' in map_text:
        ok_items.append("USERNAME")
    if '[[INSURANCE_ID_' in map_text:
        ok_items.append("INSURANCE_ID")
    if '[[HOST_' in map_text:
        ok_items.append("HOST")
    
    # ========================================
    # VERDIKT
    # ========================================
    score = max(0.0, min(10.0, score))  # clamp 0-10
    
    # NO-GO pokud <9 nebo jsou kritické leaky
    has_critical = any('KRITICKÝ LEAK' in i for i in issues)
    verdict = "✅ GO" if score >= 9.0 and not has_critical else "❌ NO-GO"
    
    return {
        'score': round(score, 1),
        'verdict': verdict,
        'issues': issues,
        'ok_items': ok_items
    }

# ========================================
# MAIN
# ========================================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python master_audit.py <contract_base_name>")
        print("Example: python master_audit.py smlouva13")
        sys.exit(1)
    
    contract = sys.argv[1]
    names_lib = load_names_library()
    
    print("=" * 80)
    print(f"MASTER AUDIT - {contract}")
    print("=" * 80)
    
    result = audit_contract(contract, names_lib)
    
    if not result:
        print(f"❌ Soubory nenalezeny: {contract}_anon.docx nebo {contract}_map.txt")
        sys.exit(1)
    
    print(f"\n📊 Verdikt: {result['score']}/10 → {result['verdict']}")
    
    if result['issues']:
        print(f"\n❌ Kritické/Major nálezy:")
        for i, issue in enumerate(result['issues'], 1):
            print(f"   {i}. {issue}")
    else:
        print(f"\n✅ Žádné problémy")
    
    if result['ok_items']:
        print(f"\n✅ Co je OK:")
        print(f"   {', '.join(result['ok_items'])}")
    
    # Doporučení fixů
    if result['score'] < 9.0:
        print(f"\n🔧 Doporučené fixy:")
        if any('Platební karta' in i for i in result['issues']):
            print(f"   - Rozšířit CARD_RE regex pro všechny varianty karet")
            print(f"   - Přidat end-scan pro karty s CVV/exp. datem")
        if any('PASSWORD' in i for i in result['issues']):
            print(f"   - Opravit _get_or_create_label pro konzistentní mapování")
        if any('Telefony klasifikované jako AMOUNT' in i for i in result['issues']):
            print(f"   - Upravit AMOUNT_RE aby nevybíral telefony")
        if any('Čísla OP' in i for i in result['issues']):
            print(f"   - Vytvořit samostatnou kategorii ID_CARD")
        if any('šum' in i for i in result['issues']):
            print(f"   - Očistit hodnoty v mapě od regexového šumu")
        
        print(f"\n📈 Očekávané skóre po fixech: 9.3-9.6/10 → GO")
    
    print("\n" + "=" * 80)

