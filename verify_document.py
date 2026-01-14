#!/usr/bin/env python3
"""
Zkontroluje, zda všechna jména v mapě jsou skutečně v originálním dokumentu.
"""
import re
from docx import Document

# Načti originální dokument
doc = Document('smlouva24.docx')

# Extrahuj všechen text
all_text = []
for para in doc.paragraphs:
    all_text.append(para.text)

full_text = ' '.join(all_text)

# Pattern pro jména (Jméno Příjmení)
name_pattern = r'\b([A-ZČŘŠŽÝÁÍÉÚŮĎŤŇ][a-zčřšžýáíéúůďťňě]+)\s+([A-ZČŘŠŽÝÁÍÉÚŮĎŤŇ][a-zčřšžýáíéúůďťňěa]+)\b'

# Najdi všechna jména v dokumentu
names_in_doc = set()
for match in re.finditer(name_pattern, full_text):
    first = match.group(1)
    last = match.group(2)
    names_in_doc.add(f"{first} {last}")

# Načti mapu
with open('smlouva24_map.txt', 'r', encoding='utf-8') as f:
    map_content = f.read()

# Extrahuj canonical jména z mapy (řádky s [[PERSON_X]])
canonical_pattern = r'\[\[PERSON_\d+\]\]: (.+)'
canonical_in_map = []
for match in re.finditer(canonical_pattern, map_content):
    name = match.group(1).strip()
    canonical_in_map.append(name)

# Extrahuj varianty z mapy (řádky začínající "  - ")
variant_pattern = r'^\s+- (.+)$'
variants_in_map = []
for match in re.finditer(variant_pattern, map_content, re.MULTILINE):
    name = match.group(1).strip()
    variants_in_map.append(name)

print("=== KONTROLA CANONICAL JMEN ===\n")
print(f"Canonical jmen v mapě: {len(canonical_in_map)}")
print(f"Jmen nalezených v dokumentu: {len(names_in_doc)}")
print()

# Zkontroluj Pavel Zík, Pavla Zíková, Václav Holas
check_names = [
    "Pavel Zík",
    "Pavla Zíková", 
    "Václav Holas",
    "Pavel Zíka",
    "Pavla Zíky",
    "Václava Holase",
    "Pavlovi Zíkovi",
    "Václavovi Holasovi"
]

print("Kontrola specifických jmen:\n")
for name in check_names:
    in_doc = name in names_in_doc
    in_map_canonical = name in canonical_in_map
    in_map_variant = name in variants_in_map
    
    status = "✅ V DOKUMENTU" if in_doc else "❌ NENÍ v dokumentu"
    map_status = ""
    if in_map_canonical:
        map_status = " (canonical v mapě)"
    elif in_map_variant:
        map_status = " (varianta v mapě)"
    
    print(f"{status:30} {name:25} {map_status}")

print("\n=== CANONICAL KTERÁ NEJSOU V DOKUMENTU ===\n")
not_in_doc = []
for name in canonical_in_map:
    if name not in names_in_doc:
        not_in_doc.append(name)
        print(f"❌ {name}")

if not not_in_doc:
    print("✅ Všechna canonical jména jsou v dokumentu!")
else:
    print(f"\nCelkem {len(not_in_doc)} canonical jmen NENÍ v dokumentu!")
