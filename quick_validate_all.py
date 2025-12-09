#!/usr/bin/env python3
"""
Rychlá validace všech existujících map bez regenerace.
"""

from docx import Document
import json
from pathlib import Path

def validate_contract(num):
    """Validuj jednu smlouvu."""
    docx_file = f"smlouva{num}.docx"
    map_file = f"smlouva{num}_map.json"

    if not Path(docx_file).exists():
        return None
    if not Path(map_file).exists():
        return None

    # Load original document
    doc = Document(docx_file)
    doc_text = '\n'.join([p.text for p in doc.paragraphs])

    # Load map
    with open(map_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check errors
    errors = []
    entities = data.get('entities', [])
    for entity in entities:
        canonical = entity.get('original', '')
        if canonical and canonical not in doc_text:
            errors.append(canonical)

    total = len(entities)
    return total, errors

print("=" * 80)
print("🔍 RYCHLÁ VALIDACE EXISTUJÍCÍCH MAP (smlouvy 13-24)")
print("=" * 80)

results = []
total_persons = 0
total_errors = 0

for num in range(13, 25):
    result = validate_contract(num)
    if result is None:
        continue

    total, errors = result
    results.append((num, total, errors))
    total_persons += total
    total_errors += len(errors)

    if errors:
        print(f"❌ smlouva{num}: {total} osob, {len(errors)} chyb = {100*(total-len(errors))/total:.1f}%")
        for err in errors[:3]:  # Show first 3 errors
            print(f"   - {err}")
        if len(errors) > 3:
            print(f"   ... a {len(errors)-3} dalších")
    else:
        print(f"✅ smlouva{num}: {total} osob, 0 chyb = 100.0%")

print("\n" + "=" * 80)
print(f"📊 CELKOVÁ STATISTIKA")
print("=" * 80)
overall = 100 * (total_persons - total_errors) / total_persons if total_persons > 0 else 0
print(f"Celkem osob: {total_persons}")
print(f"Celkem chyb: {total_errors}")
print(f"Celková úspěšnost: {overall:.1f}%")
print("=" * 80)
