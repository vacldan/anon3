#!/usr/bin/env python3
"""Analyze all errors and categorize them"""
import json
from docx import Document
from collections import defaultdict

def validate_contract(num):
    """Validate single contract and return errors"""
    try:
        doc = Document(f"smlouva{num}.docx")
        doc_text = '\n'.join([p.text for p in doc.paragraphs])

        with open(f"smlouva{num}_map.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        errors = []
        for entity in data.get('entities', []):
            canonical = entity.get('original', '')
            if canonical and canonical not in doc_text:
                errors.append(canonical)

        return errors
    except Exception as e:
        return []

# Collect all errors
all_errors = []
for num in range(13, 25):
    errors = validate_contract(num)
    for err in errors:
        all_errors.append((num, err))

# Categorize errors
categories = defaultdict(list)

for num, err in all_errors:
    # Underscore errors
    if err.startswith('_'):
        categories['underscore'].append((num, err))
    # Double vowel (í+í, i+i, etc.)
    elif 'íí' in err or 'iia' in err.lower() or 'ěa' in err:
        categories['double_vowel'].append((num, err))
    # Instrumentál -em not removed
    elif err.endswith('em') and len(err) > 3:
        categories['instrumental_em'].append((num, err))
    # Dative/Genitive first names (ending in -ii, -ií)
    elif ' ' in err:
        parts = err.split()
        if len(parts) >= 2:
            first = parts[0]
            if first.endswith('ii') or first.endswith('ií'):
                categories['dative_firstname'].append((num, err))
            else:
                categories['other_fullname'].append((num, err))
    else:
        categories['other'].append((num, err))

# Print summary
print("=" * 80)
print("📊 KATEGORIZACE CHYB")
print("=" * 80)

for cat, items in sorted(categories.items()):
    print(f"\n🔹 {cat.upper()} ({len(items)} chyb):")
    for num, err in items[:10]:
        print(f"   smlouva{num}: {err}")
    if len(items) > 10:
        print(f"   ... a {len(items) - 10} dalších")

print(f"\n\nCelkem chyb: {len(all_errors)}")
