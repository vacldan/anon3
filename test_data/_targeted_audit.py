"""Targeted audit: find REAL false positives in ADDRESS entries."""
import os, re

maps_dir = os.path.dirname(os.path.abspath(__file__))
all_entries = []

for f in sorted(os.listdir(maps_dir)):
    if not f.endswith('_map.txt'):
        continue
    path = os.path.join(maps_dir, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    m = re.search(r'ADDRESS\n(.*?)(?:\n\n|\Z)', content, re.DOTALL)
    if not m:
        continue
    for line in m.group(1).strip().split('\n'):
        if not line.startswith('[[ADDRESS_'):
            continue
        parts = line.split(']]: ', 1)
        if len(parts) < 2:
            continue
        tag = parts[0] + ']]'
        val = parts[1].strip()
        all_entries.append((f, tag, val))

fp_word_keywords = [
    'volkswagen', 'passat', 'fabia', 'octavia', 'superb',
    'latitude', 'thinkpad', 'samsung',
    'toyota', 'renault', 'kia', 'bmw', 'audi', 'mercedes',
    'maraton', 'maratón',
    'krevní', 'anamnéze', 'anamnéza', 'alkoholu', 'léčení',
    'celkem',
    'stadium', 'zbaven', 'způsobilosti',
    'ksos', 'ksul', 'ksph', 'kscb', 'ksbr',
    'přestal', 'přestala',
    'náleží', 'výživné',
    'poškozená', 'poškozený', 'podstoupila',
]
fp_boundary_patterns = [
    (r'\bVIN\b', 'VIN'),
    (r'\bSPZ\b', 'SPZ'),
    (r'\bSN\b', 'SN'),
    (r'\bMAC\b', 'MAC address'),
    (r'\bCVC\b', 'CVC'),
    (r'\bCVV\b', 'CVV'),
    (r'\bDell\b', 'Dell'),
    (r'\bCisco\b', 'Cisco'),
    (r'\bŠkoda\b(?!\s+(?:[A-Z][a-z]+\s+)?\d)', 'Škoda (car)'),
    (r'\bFord\b(?!\s+(?:[A-Z][a-z]+\s+)?\d)', 'Ford (car)'),
    (r'\bExekuce\b', 'Exekuce'),
    (r'\bExekutor\b', 'Exekutor'),
]

issues = []
for fn, tag, val in all_entries:
    val_lower = val.lower()
    val_words = set(re.findall(r'[a-záčďéěíňóřšťúůýž]+', val_lower))
    found_kw = None
    for kw in fp_word_keywords:
        if kw in val_words:
            found_kw = kw
            break
    if found_kw:
        issues.append((fn, tag, val, f"keyword: {found_kw}"))
        continue
    found_pat = None
    for pat, desc in fp_boundary_patterns:
        if re.search(pat, val):
            found_pat = desc
            break
    if found_pat:
        issues.append((fn, tag, val, f"pattern: {found_pat}"))
        continue
    if len(val) > 80:
        issues.append((fn, tag, val[:80] + "...", "too long (>80 chars)"))
        continue
    if re.search(r'Rodné\s+číslo|číslo\s+OP|číslo\s+účtu', val):
        issues.append((fn, tag, val, "absorbed field label"))
        continue
    if val.endswith(' OP') or val.endswith(' RČ'):
        issues.append((fn, tag, val, "absorbed field label (trailing)"))
        continue
    lc_ignore = re.compile(
        r'^(?:v\s+|na\s+adrese\s+|adrese\s+|bytem\s+|bydlištěm?\s+|'
        r'pobytu\s+|nám\.\s*|ul\.\s*|n\.\s*|nábřeží\s+|náměstí\s+)')
    if val[0].islower() and not lc_ignore.match(val):
        issues.append((fn, tag, val, "starts with lowercase"))
        continue

# Check for duplicates within same map
from collections import defaultdict
map_addrs = defaultdict(list)
for fn, tag, val in all_entries:
    clean = re.sub(r'\s+', ' ', val.strip().lower())
    clean = re.sub(r'[,.]', '', clean)
    map_addrs[fn].append((tag, val, clean))

dup_issues = []
for fn, entries in sorted(map_addrs.items()):
    if fn == 'test_pypy_map.txt':
        continue
    seen = {}
    for tag, val, clean in entries:
        for prev_tag, prev_clean in seen.items():
            if clean in prev_clean or prev_clean in clean:
                if len(clean) > 5 and len(prev_clean) > 5:
                    dup_issues.append((fn, tag, val, f"substring of {prev_tag}"))
        seen[tag] = clean

print(f"TOTAL ADDRESS ENTRIES: {len(all_entries)}")
print()
print(f"FALSE POSITIVE ISSUES: {len(issues)}")
print("=" * 100)
for fn, tag, val, reason in issues:
    print(f"  [{reason:30s}] {fn:45s} {tag}: {val}")

print()
print(f"DUPLICATE ISSUES: {len(dup_issues)}")
print("=" * 100)
for fn, tag, val, reason in dup_issues:
    print(f"  [{reason:30s}] {fn:45s} {tag}: {val}")

# Also check PERSON entries for false positives
print()
print("=" * 100)
print("PERSON FALSE POSITIVE CHECK")
print("=" * 100)
person_fp_words = [
    'expres', 'business', 'měsíční', 'poplatek', 'specifikace', 'specifikaec',
    'běžný', 'běžném', 'běžného', 'pojištění', 'smlouva', 'podmínky',
    'banka', 'úvěr', 'dohoda', 'prohlášení', 'příloha', 'dodatek',
]
person_issues = []
for f in sorted(os.listdir(maps_dir)):
    if not f.endswith('_map.txt'):
        continue
    path = os.path.join(maps_dir, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    m = re.search(r'OSOBY\n-----\n(.*?)(?:\n\n|\Z)', content, re.DOTALL)
    if not m:
        continue
    for line in m.group(1).strip().split('\n'):
        if not line.startswith('[[PERSON_'):
            continue
        parts = line.split(']]: ', 1)
        if len(parts) < 2:
            continue
        tag = parts[0] + ']]'
        val = parts[1].strip()
        val_lower = val.lower()
        for kw in person_fp_words:
            if kw in val_lower:
                person_issues.append((f, tag, val, f"keyword: {kw}"))
                break

print(f"PERSON FALSE POSITIVES: {len(person_issues)}")
for fn, tag, val, reason in person_issues:
    print(f"  [{reason:30s}] {fn:45s} {tag}: {val}")
