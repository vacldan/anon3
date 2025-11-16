#!/usr/bin/env python3
"""GDPR Audit skript pro anonymizované smlouvy"""
import re
import sys
from pathlib import Path
from docx import Document

def audit_contract(contract_num):
    """Provede GDPR audit jedné smlouvy."""
    
    base = f"smlouva{contract_num}" if contract_num != "" else "smlouva"
    anon_file = f"{base}_anon.docx"
    map_file = f"{base}_map.txt"
    
    if not Path(anon_file).exists():
        return None
    
    # Načti anonymizovaný dokument
    doc = Document(anon_file)
    text = '\n'.join([p.text for p in doc.paragraphs])
    
    # Načti mapu
    with open(map_file, 'r', encoding='utf-8') as f:
        map_text = f.read()
    
    issues = []
    score = 10.0
    
    # 1. Kontrola hesel v čistém textu
    passwords = re.findall(r'(?i)(?:password|heslo|passwd|pwd|pass)\s*[:\-=]\s*([^\s,;\.\[]{3,50})', text)
    if passwords and not all('[[PASSWORD' in p for p in passwords):
        clean_passwords = [p for p in passwords if not p.startswith('[[')]
        if clean_passwords:
            issues.append(f"❌ KRITICKÉ: Hesla v čistém textu: {len(clean_passwords)}x")
            score -= 3.0
    
    # Kontrola že hesla jsou ***REDACTED*** v mapě
    if '[[PASSWORD_' in map_text:
        redacted_count = map_text.count('***REDACTED***')
        password_count = len(re.findall(r'\[\[PASSWORD_\d+\]\]', map_text))
        if password_count > 0 and redacted_count < password_count:
            issues.append(f"⚠️  Hesla NEJSOU redacted v mapě")
            score -= 1.5
    
    # 2. IP adresy v čistém textu
    ips = re.findall(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', text)
    clean_ips = [ip for ip in ips if not ip.startswith('[[') and ip != '127.0.0.1']
    if clean_ips:
        issues.append(f"❌ IP adresy v čistém textu: {len(clean_ips)}x - {clean_ips[:3]}")
        score -= 1.5
    
    # 3. API klíče, secrets
    api_keys = re.findall(r'(?i)(?:AWS|Access|Secret|API|Stripe|SendGrid)\s+(?:Key|Token|Secret):\s*([A-Za-z0-9+/=_\-]{16,})', text)
    if api_keys and not all('[[' in k for k in api_keys):
        clean_keys = [k for k in api_keys if not k.startswith('[[')]
        if clean_keys:
            issues.append(f"❌ KRITICKÉ: API klíče/Secrets v čistém textu: {len(clean_keys)}x")
            score -= 3.0
    
    # 4. Platební karty
    cards = re.findall(r'(?i)(?:číslo\s+karty|card\s+number|card):\s*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})', text)
    if cards and not all('[[CARD' in c for c in cards):
        clean_cards = [c for c in cards if not c.startswith('[[')]
        if clean_cards:
            issues.append(f"❌ KRITICKÉ: Karty v čistém textu: {len(clean_cards)}x")
            score -= 2.5
    
    # 5. Usernames
    usernames = re.findall(r'(?i)(?:Login|Username|User|GitHub|Jira|AWS\s+Console)\s*:\s*([a-z0-9._\-@]+)', text)
    if usernames and not all('[[USERNAME' in u for u in usernames):
        clean_users = [u for u in usernames if not u.startswith('[[')]
        if clean_users:
            issues.append(f"⚠️  Usernames v čistém textu: {len(clean_users)}x")
            score -= 0.8
    
    # 6. Pojištěnce
    insurance = re.findall(r'(?i)(?:Číslo\s+pojištěnce|VZP|ČPZP)[,\s:]+(?:číslo\s*:?\s*)?(\d{10})', text)
    if insurance and not all('[[INSURANCE' in i for i in insurance):
        clean_ins = [i for i in insurance if not i.startswith('[[')]
        if clean_ins:
            issues.append(f"❌ Čísla pojištěnce v čistém textu: {len(clean_ins)}x")
            score -= 1.5
    
    # 7. RFID/Badge
    rfid = re.findall(r'(?i)(?:RFID\s+karta|badge|ID\s+karta)\s*[:#]?\s*([A-Za-z0-9\-_/]+)', text)
    if rfid and not all('[[RFID' in r for r in rfid):
        clean_rfid = [r for r in rfid if not r.startswith('[[')]
        if clean_rfid:
            issues.append(f"⚠️  RFID/Badge v čistém textu: {len(clean_rfid)}x")
            score -= 0.5
    
    # 8. Částky vs PHONE - kontrola mapy
    phone_amounts = re.findall(r'\[\[PHONE_\d+\]\]:\s+[:\s]*(\d{1,3}\s+\d{3}\s+\d{3}(?:\s+\d{3})*)\b', map_text)
    if phone_amounts:
        # Kontroluj jestli jsou to skutečně velké částky (>10 mil)
        large_amounts = [a for a in phone_amounts if len(a.replace(' ', '')) >= 9]
        if large_amounts:
            issues.append(f"⚠️  Částky v PHONE: {len(large_amounts)}x - {large_amounts[:2]}")
            score -= 0.8
    
    # 9. False positive PERSON - firmy/produkty
    person_lines = re.findall(r'\[\[PERSON_\d+\]\]:\s+(.+)', map_text)
    false_positives = []
    for name in person_lines:
        name_lower = name.lower()
        if any(term in name_lower for term in ['capital', 'equity', 'value', 'fund', 'holdings',
                                                 'symbicort', 'turbuhaler', 'spirometr', 'jaeger',
                                                 'healthcare', 'management', 'processing', 'solutions',
                                                 'cisco', 'ventures', 'crescendo', 'clinic']):
            false_positives.append(name)
    
    if false_positives:
        issues.append(f"⚠️  False positive PERSON (firmy/produkty): {len(false_positives)}x")
        score -= 0.5
    
    # 10. Kontrola že citlivá data JSOU v mapě (ne chybějící)
    categories_found = {
        'PASSWORD': '[[PASSWORD_' in map_text,
        'API_KEY': '[[API_KEY_' in map_text,
        'SECRET': '[[SECRET_' in map_text,
        'USERNAME': '[[USERNAME_' in map_text,
        'IP': '[[IP_' in map_text,
        'CARD': '[[CARD_' in map_text,
        'INSURANCE_ID': '[[INSURANCE_ID_' in map_text,
        'AMOUNT': '[[AMOUNT_' in map_text,
    }
    
    # Verdikt
    if score >= 9.3:
        verdict = "✅ GO"
    elif score >= 8.5:
        verdict = "⚠️  CONDITIONAL GO (minor fixes)"
    else:
        verdict = "❌ NO-GO"
    
    return {
        'score': round(score, 1),
        'verdict': verdict,
        'issues': issues,
        'categories': categories_found
    }

# Main
if __name__ == '__main__':
    contracts = [""] + [str(i) for i in range(16)]
    
    print("=" * 80)
    print("GDPR COMPLIANCE AUDIT - Anonymizace dat")
    print("=" * 80)
    
    results = {}
    for contract in contracts:
        result = audit_contract(contract)
        if result:
            results[contract if contract else "0"] = result
    
    # Zobraz výsledky
    for contract, result in results.items():
        print(f"\n📄 Smlouva {contract}:")
        print(f"   Skóre: {result['score']}/10")
        print(f"   Verdikt: {result['verdict']}")
        
        if result['issues']:
            print(f"   Problémy:")
            for issue in result['issues']:
                print(f"      {issue}")
        else:
            print(f"   ✅ Žádné problémy")
    
    # Souhrn
    print("\n" + "=" * 80)
    print("SOUHRN AUDITU:")
    print("=" * 80)
    
    avg_score = sum(r['score'] for r in results.values()) / len(results)
    go_count = sum(1 for r in results.values() if '✅ GO' in r['verdict'])
    conditional = sum(1 for r in results.values() if '⚠️' in r['verdict'])
    no_go = sum(1 for r in results.values() if '❌ NO-GO' in r['verdict'])
    
    print(f"Průměrné skóre: {round(avg_score, 1)}/10")
    print(f"GO: {go_count}, CONDITIONAL GO: {conditional}, NO-GO: {no_go}")
    
    if avg_score >= 9.3 and no_go == 0:
        print("\n🎉 CELKOVÝ VERDIKT: GO - Produkčně připraveno")
    elif avg_score >= 8.5 and no_go == 0:
        print("\n⚠️  CELKOVÝ VERDIKT: CONDITIONAL GO - Drobné opravy")
    else:
        print("\n❌ CELKOVÝ VERDIKT: NO-GO - Kritické mezery")

