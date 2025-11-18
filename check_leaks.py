#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rychlá kontrola úniků v anonymizovaném dokumentu"""

import re
from docx import Document

doc = Document('smlouva14_anon.docx')

print("=" * 80)
print("KONTROLA ÚNIKŮ PII V ANONYMIZOVANÉM DOKUMENTU")
print("=" * 80)

all_text = []
for para in doc.paragraphs:
    all_text.append(para.text)

full_text = '\n'.join(all_text)

# 1. ALL_CAPS jména (2+ slova velkými písmeny)
print("\n1. ALL_CAPS JMÉNA (potenciální únik):")
all_caps_pattern = re.compile(r'\b[A-Z]{2,}\s+[A-Z]{2,}(?:\s+[A-Z]{2,})?\b')
all_caps_matches = all_caps_pattern.findall(full_text)
if all_caps_matches:
    unique = set(all_caps_matches)
    for match in sorted(unique):
        # Vynech zkratky typu "S R O", "A S"
        if len(match) > 6 and not re.match(r'^[A-Z]\s+[A-Z](?:\s+[A-Z])?$', match):
            print(f"  ⚠️  {match}")
            # Najdi kontext
            idx = full_text.find(match)
            if idx != -1:
                context = full_text[max(0, idx-40):min(len(full_text), idx+len(match)+40)]
                print(f"      Context: ...{context}...")
else:
    print("  ✓ Žádná ALL_CAPS jména")

# 2. Místo narození
print("\n2. MÍSTO NAROZENÍ (plaintext):")
birth_place_pattern = re.compile(r'Místo\s+narození\s*:\s*([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)?)', re.IGNORECASE)
birth_places = birth_place_pattern.findall(full_text)
if birth_places:
    for place in birth_places:
        print(f"  ⚠️  Místo narození: {place}")
else:
    print("  ✓ Žádná místa narození v plaintextu")

# 3. Adresy v plaintextu (heuristika: ulice číslo, město)
print("\n3. ADRESY V PLAINTEXTU:")
# Karlovo náměstí 12/34, Praha 2
addr_pattern = re.compile(
    r'\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+(?:\s+[a-záčďéěíňóřšťúůýž]+)*)\s+\d+(?:/\d+)?\s*,\s*([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+(?:\s+\d+)?)',
    re.IGNORECASE
)
addresses = addr_pattern.findall(full_text)
if addresses:
    for addr in addresses[:10]:  # Max 10
        print(f"  ⚠️  {addr[0]} ..., {addr[1]}")
else:
    print("  ✓ Žádné adresy v plaintextu")

# 4. Tituly + jména (MUDr., Ing., apod.)
print("\n4. TITULY + JMÉNA (plaintext):")
title_pattern = re.compile(
    r'\b(MUDr\.|Ing\.|Mgr\.|PhDr\.|RNDr\.|JUDr\.|Prof\.|Doc\.)\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)?)',
    re.IGNORECASE
)
titles = title_pattern.findall(full_text)
if titles:
    for title, name in titles[:10]:
        # Check if name is NOT followed by tag
        search_str = f"{title} {name}"
        idx = full_text.find(search_str)
        if idx != -1:
            context = full_text[idx:min(len(full_text), idx+len(search_str)+20)]
            if '[[PERSON_' not in context:
                print(f"  ⚠️  {title} {name}")
                print(f"      Context: {context}")
else:
    print("  ✓ Žádné tituly + jména v plaintextu")

# 5. Statistika tagů
print("\n5. STATISTIKA TAGŮ:")
tag_pattern = re.compile(r'\[\[([A-Z_]+)_\d+\]\]')
tags = tag_pattern.findall(full_text)
tag_counts = {}
for tag in tags:
    tag_counts[tag] = tag_counts.get(tag, 0) + 1

for tag_type, count in sorted(tag_counts.items()):
    print(f"  {tag_type}: {count}")

print("\n" + "=" * 80)
