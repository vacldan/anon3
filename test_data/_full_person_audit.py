"""Full audit: dump ALL PERSON entries from ALL maps for manual review."""
import os, re

maps_dir = os.path.dirname(os.path.abspath(__file__))
all_entries = []

for f in sorted(os.listdir(maps_dir)):
    if not f.endswith('_map.txt'):
        continue
    path = os.path.join(maps_dir, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    # OSOBY section: from OSOBY/----- until ADDRESS or next section
    m = re.search(r'OSOBY\n-+\n(.*?)(?=\n(?:ADDRESS|BANK|BIRTH_ID|DATE|DIC|EMAIL|IBAN|ICO|ID_CARD|LICENSE_PLATE|PHONE)\s|\Z)', content, re.DOTALL)
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
        all_entries.append((f, tag, val))

# Categorize as OK / SUSPECT
# OK: typické jméno (české i s ü/ä/ö) – 2+ slova, každé začíná velkým, bez číslic
_letter = r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽÄÖÜa-záčďéěíňóřšťúůýžäöü\-]+'
person_ok = re.compile(r'^' + _letter + r'(?:\s+' + _letter + r')+$')
company_indicators = re.compile(r'\b(s\.r\.o\.|a\.s\.|spol\.|v\.o\.s\.|k\.s\.)\b', re.IGNORECASE)
has_digit = re.compile(r'\d')
has_special = re.compile(r'[@,;()]')

suspect = []
ok = []
for fn, tag, val in all_entries:
    val_stripped = val.strip()
    is_ok = False
    if person_ok.match(val_stripped):
        if not has_digit.search(val_stripped) and not company_indicators.search(val_stripped):
            is_ok = True
    # Jedno slovo – může být příjmení (OK) nebo firma (SUSPECT)
    elif re.match(r'^[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽÄÖÜ][a-záčďéěíňóřšťúůýžäöü\-]+$', val_stripped) and len(val_stripped) < 25:
        if not company_indicators.search(val_stripped):
            is_ok = True  # pravděpodobně jen příjmení

    if has_digit.search(val_stripped) or has_special.search(val_stripped):
        is_ok = False
    if company_indicators.search(val_stripped):
        is_ok = False
    if len(val_stripped) > 60:
        is_ok = False

    if is_ok:
        ok.append((fn, tag, val))
    else:
        suspect.append((fn, tag, val))

print(f"TOTAL PERSON ENTRIES: {len(all_entries)}")
print(f"  OK (pattern match): {len(ok)}")
print(f"  SUSPECT (needs review): {len(suspect)}")
print()
print("=" * 100)
print("SUSPECT ENTRIES (needs manual review):")
print("=" * 100)
for fn, tag, val in suspect:
    print(f"  {fn:45s} {tag}: {val}")
