#!/usr/bin/env python3
"""
Test all contracts 13-24 and validate reverse check.
"""

import subprocess
import json
import sys
from pathlib import Path
from docx import Document

def load_doc_text(docx_path):
    """Load document text."""
    doc = Document(docx_path)
    return '\n'.join([p.text for p in doc.paragraphs])

def validate_contract(contract_num):
    """Run anonymization and validate one contract."""
    docx_file = f"smlouva{contract_num}.docx"
    map_file = f"smlouva{contract_num}_map.json"

    # Check if file exists
    if not Path(docx_file).exists():
        return None, None, f"File {docx_file} not found"

    # Run anonymization
    print(f"\n🔄 Processing {docx_file}...")
    result = subprocess.run(
        ['python3', 'anon7.2 - s padama.py', docx_file],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return None, None, f"Anonymization failed: {result.stderr}"

    # Load original document
    doc_text = load_doc_text(docx_file)

    # Load map
    with open(map_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate canonical forms
    errors = []
    entities = data.get('entities', [])
    for entity in entities:
        canonical = entity.get('original', '')
        if canonical and canonical not in doc_text:
            errors.append(canonical)

    total = len(entities)
    success_rate = 0.0 if total == 0 else 100.0 * (total - len(errors)) / total

    return total, len(errors), success_rate, errors

def main():
    """Test all contracts 13-24."""
    print("=" * 80)
    print("🧪 TESTOVÁNÍ VŠECH SMLUV 13-24")
    print("=" * 80)

    results = []
    total_persons = 0
    total_errors = 0

    for num in range(13, 25):
        total, errors, success_rate, error_list = validate_contract(num)

        if total is None:
            # File not found or error
            print(f"⚠️  smlouva{num}: {success_rate}")
            continue

        results.append({
            'num': num,
            'total': total,
            'errors': errors,
            'success_rate': success_rate,
            'error_list': error_list
        })

        total_persons += total
        total_errors += errors

        # Print result
        if errors == 0:
            print(f"✅ smlouva{num}: {total} osob, 0 chyb = 100.0% úspěšnost")
        else:
            print(f"❌ smlouva{num}: {total} osob, {errors} chyb = {success_rate:.1f}% úspěšnost")
            for err in error_list:
                print(f"   - {err}")

    # Print summary
    print("\n" + "=" * 80)
    print("📊 CELKOVÁ STATISTIKA (smlouvy 13-24)")
    print("=" * 80)
    overall_success = 0.0 if total_persons == 0 else 100.0 * (total_persons - total_errors) / total_persons
    print(f"Celkem osob: {total_persons}")
    print(f"Celkem chyb: {total_errors}")
    print(f"Celková úspěšnost: {overall_success:.1f}%")
    print("=" * 80)

    if total_errors == 0:
        print("\n🎉 PERFEKTNÍ! 100% ÚSPĚŠNOST NA VŠECH SMLOUVÁCH! 🎉\n")
        return 0
    else:
        print(f"\n⚠️  Zbývá opravit {total_errors} chyb\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
