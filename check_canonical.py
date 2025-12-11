#!/usr/bin/env python3
"""Check what's in canonical_persons after processing"""

import sys
import json

# Load the generated map
with open('smlouva24_map.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get unique person labels
person_entities = [e for e in data['entities'] if e['type'] == 'PERSON']
unique_labels = sorted(set(e['label'] for e in person_entities))

print(f"JSON map has {len(person_entities)} person entities")
print(f"Unique labels: {len(unique_labels)}")

# Load TXT map and count
with open('smlouva24_map.txt', 'r', encoding='utf-8') as f:
    txt_content = f.read()

import re
txt_persons = re.findall(r'^\[\[PERSON_\d+\]\]: (.+)$', txt_content, re.MULTILINE)
print(f"\nTXT map has {len(txt_persons)} person entries")

# Find Maria/Julia in TXT
maria_julia = [p for p in txt_persons if 'Maria' in p or 'Julia' in p or 'Alica' in p]
print(f"Maria/Julia/Alica in TXT: {len(maria_julia)}")
for p in maria_julia[:10]:
    print(f"  {p}")

# Find Maria/Julia in JSON
maria_julia_json = [e for e in person_entities if 'Maria' in e['original'] or 'Julia' in e['original'] or 'Alica' in e['original']]
print(f"\nMaria/Julia/Alica in JSON: {len(maria_julia_json)}")
for e in maria_julia_json[:10]:
    print(f"  {e['label']}: {e['original']}")
