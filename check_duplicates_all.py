#!/usr/bin/env python3
"""
Systematická kontrola duplicit ve všech smlouvách 13-23.
"""

import re
import unicodedata
from pathlib import Path

def normalize_for_matching(text: str) -> str:
    """Normalizuje text pro porovnávání (odstranění diakritiky, lowercase)."""
    if not text:
        return ""
    n = unicodedata.normalize('NFD', text)
    no_diac = ''.join(c for c in n if not unicodedata.combining(c))
    normalized = re.sub(r'[^A-Za-z]', '', no_diac).lower()

    # Slovak→Czech varianty
    slovak_to_czech = {
        'alica': 'alice',
        'lucia': 'lucie'
    }
    normalized = slovak_to_czech.get(normalized, normalized)
    return normalized

def parse_map_file(filepath: str):
    """Parsuje _map.txt soubor a vrací seznam osob."""
    persons = []
    in_persons_section = False
    current_person = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')

            if line == 'OSOBY':
                in_persons_section = True
                continue
            elif line.startswith('[[USERNAME_'):
                in_persons_section = False
                break

            if not in_persons_section:
                continue

            # Hlavní osoba: [[PERSON_X]]: Jméno Příjmení
            match = re.match(r'\[\[PERSON_(\d+)\]\]: (.+)', line)
            if match:
                person_id = int(match.group(1))
                name = match.group(2).strip()
                current_person = {
                    'id': person_id,
                    'canonical': name,
                    'variants': []
                }
                persons.append(current_person)
            # Varianta:   - Jméno Příjmení
            elif line.startswith('  - ') and current_person:
                variant = line[4:].strip()
                current_person['variants'].append(variant)

    return persons

def find_duplicates(persons):
    """Najde potenciální duplicity mezi osobami."""
    duplicates = []

    # Index: normalized_name -> list of persons
    name_index = {}

    for person in persons:
        canonical = person['canonical']
        normalized = normalize_for_matching(canonical)

        if normalized not in name_index:
            name_index[normalized] = []
        name_index[normalized].append(person)

    # Najdi duplicity
    for normalized, person_list in name_index.items():
        if len(person_list) > 1:
            duplicates.append({
                'normalized': normalized,
                'persons': person_list
            })

    return duplicates

def analyze_contract(contract_num):
    """Analyzuje jednu smlouvu."""
    map_file = f'smlouva{contract_num}_map.txt'

    if not Path(map_file).exists():
        return None

    persons = parse_map_file(map_file)
    duplicates = find_duplicates(persons)

    return {
        'contract': contract_num,
        'total_persons': len(persons),
        'duplicates': duplicates
    }

def main():
    print("=" * 80)
    print("SYSTEMATICKÁ KONTROLA DUPLICIT - SMLOUVY 13-23")
    print("=" * 80)
    print()

    all_results = []
    total_duplicates = 0

    for i in range(13, 24):
        result = analyze_contract(i)
        if result is None:
            print(f"⚠️  smlouva{i}: Soubor nenalezen")
            continue

        all_results.append(result)
        num_dups = len(result['duplicates'])
        total_duplicates += num_dups

        if num_dups == 0:
            print(f"✅ smlouva{i}: {result['total_persons']} osob, ŽÁDNÉ DUPLICITY")
        else:
            print(f"⚠️  smlouva{i}: {result['total_persons']} osob, {num_dups} duplicit")

    print()
    print("=" * 80)
    print(f"CELKOVÝ POČET DUPLICIT: {total_duplicates}")
    print("=" * 80)
    print()

    # Detaily duplicit
    if total_duplicates > 0:
        print("DETAILY DUPLICIT:")
        print("=" * 80)

        for result in all_results:
            if result['duplicates']:
                print(f"\n📄 smlouva{result['contract']}:")
                for dup in result['duplicates']:
                    print(f"  • Normalizováno: '{dup['normalized']}'")
                    for person in dup['persons']:
                        variants_str = ""
                        if person['variants']:
                            variants_str = f" (varianty: {', '.join(person['variants'])})"
                        print(f"    - PERSON_{person['id']}: {person['canonical']}{variants_str}")

if __name__ == '__main__':
    main()
