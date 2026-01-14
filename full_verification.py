#!/usr/bin/env python3
"""
Kompletní verifikace mapy - kontrola že:
1. Všechna jména v mapě (canonical i varianty) jsou v dokumentu
2. Žádná duplicita - stejné jméno není pod více anonymizátory
"""
import sys
import re
from docx import Document
from collections import defaultdict

def verify_map(docx_path, map_path):
    """Verifikuj mapu proti dokumentu."""

    # Load document
    doc = Document(docx_path)
    doc_text = ' '.join([p.text for p in doc.paragraphs])

    # Parse map
    persons = []
    current_person = None

    with open(map_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('[[PERSON_'):
                # New person
                match = re.match(r'\[\[PERSON_(\d+)\]\]: (.+)', line)
                if match:
                    person_id = int(match.group(1))
                    canonical = match.group(2).strip()
                    current_person = {
                        'id': person_id,
                        'canonical': canonical,
                        'variants': []
                    }
                    persons.append(current_person)
            elif line.strip().startswith('- ') and current_person:
                # Variant
                variant = line.strip()[2:].strip()
                current_person['variants'].append(variant)

    print(f"\n{'='*70}")
    print(f"VERIFIKACE: {docx_path}")
    print(f"{'='*70}\n")

    # Check 1: All names in map are in document
    not_in_doc = []
    for person in persons:
        # Check canonical
        if person['canonical'] not in doc_text:
            not_in_doc.append(('canonical', person['id'], person['canonical']))

        # Check variants
        for variant in person['variants']:
            if variant not in doc_text:
                not_in_doc.append(('variant', person['id'], variant))

    if not_in_doc:
        print(f"❌ PROBLÉM: {len(not_in_doc)} jmen v mapě NENÍ v dokumentu:\n")
        for typ, pid, name in not_in_doc[:20]:
            print(f"  PERSON_{pid} ({typ}): {name}")
    else:
        print(f"✅ KONTROLA 1: Všechna jména v mapě ({sum(1 + len(p['variants']) for p in persons)} celkem) jsou v dokumentu")

    # Check 2: No duplicates - same name under multiple anonymizers
    all_names = defaultdict(list)  # name -> list of person IDs

    for person in persons:
        # Add canonical
        all_names[person['canonical'].lower()].append(('PERSON_' + str(person['id']), 'canonical'))

        # Add variants
        for variant in person['variants']:
            all_names[variant.lower()].append(('PERSON_' + str(person['id']), 'variant'))

    duplicates = []
    for name, occurrences in all_names.items():
        if len(occurrences) > 1:
            # Same name appears multiple times
            person_ids = set(occ[0] for occ in occurrences)
            if len(person_ids) > 1:
                # Under different persons - that's a duplicate!
                duplicates.append((name, occurrences))

    if duplicates:
        print(f"\n❌ PROBLÉM: {len(duplicates)} jmen se vyskytuje pod více anonymizátory:\n")
        for name, occurrences in duplicates[:20]:
            print(f"  '{name.title()}':")
            for person_id, typ in occurrences:
                print(f"    - {person_id} ({typ})")
    else:
        print(f"✅ KONTROLA 2: Žádné duplicity - každé jméno je pod jedním anonymizátorem")

    # Summary
    print(f"\n{'='*70}")
    print(f"SHRNUTÍ:")
    print(f"  Celkem osob v mapě: {len(persons)}")
    print(f"  Celkem jmen (canonical + varianty): {sum(1 + len(p['variants']) for p in persons)}")

    if not not_in_doc and not duplicates:
        print(f"\n✅✅✅ MAPA JE PERFEKTNÍ! ✅✅✅")
        return True
    else:
        print(f"\n❌ MAPA MÁ PROBLÉMY - je třeba opravit")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python full_verification.py <contract_number>")
        print("Example: python full_verification.py 24")
        sys.exit(1)

    contract_num = sys.argv[1]
    docx_path = f'smlouva{contract_num}.docx'
    map_path = f'smlouva{contract_num}_map.txt'

    verify_map(docx_path, map_path)
