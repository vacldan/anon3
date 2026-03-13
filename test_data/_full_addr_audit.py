"""Full audit: dump ALL ADDRESS entries from ALL maps for manual review."""
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

# Categorize as OK / SUSPECT
addr_pattern = re.compile(
    r'^(?:(?:nám\.|ul\.|n\.|nábřeží|náměstí|třída|ulice)\s+)?'
    r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž\-]+'
    r'(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽa-záčďéěíňóřšťúůýž][a-záčďéěíňóřšťúůýž\-]+){0,3}'
    r'\s+\d{1,4}(?:/\d{1,4}[a-zA-Z]?)?'
    r'(?:,\s*(?:\d{3}\s?\d{2}\s+)?'
    r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž\- ]*(?:\d{1,2})?)?$'
)
city_only = re.compile(
    r'^(?:v\s+)?(?:Praha|Brno|Ostrav|Plze|Olomouc|Liberec|Přerov|Pardubic|'
    r'Hradec|Karlovy|České|Ústí|Zlín|Jihlav|Tábor|Znojmo|Teplice|Chomutov|'
    r'Opava|Havířov|Karviná|Kladno|Děčín|Most|Chrudim|Svitavy|Kroměříž)',
    re.IGNORECASE
)
psc_city = re.compile(r'^\d{3}\s?\d{2}\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]', re.IGNORECASE)

suspect = []
ok = []
for fn, tag, val in all_entries:
    val_stripped = val.strip()
    is_ok = False
    if addr_pattern.match(val_stripped):
        is_ok = True
    elif city_only.match(val_stripped) and len(val_stripped) < 40:
        is_ok = True
    elif psc_city.match(val_stripped) and len(val_stripped) < 40:
        is_ok = True
    elif val_stripped.lower().startswith(('v praze', 'v brně', 'v plzni', 'v olomouci',
                                          'v ostravě', 'v liberci')):
        is_ok = True
    
    if is_ok:
        ok.append((fn, tag, val))
    else:
        suspect.append((fn, tag, val))

print(f"TOTAL ADDRESS ENTRIES: {len(all_entries)}")
print(f"  OK (pattern match): {len(ok)}")
print(f"  SUSPECT (needs review): {len(suspect)}")
print()
print("=" * 100)
print("SUSPECT ENTRIES (needs manual review):")
print("=" * 100)
for fn, tag, val in suspect:
    print(f"  {fn:45s} {tag}: {val}")
