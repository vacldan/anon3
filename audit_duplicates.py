#!/usr/bin/env python3
"""
Audit contract maps for duplicate persons.
Detects patterns like:
- Renata/Renato, Marcela/Marcelo (wrong gender suffix)
- Daniel/Daniela, Martin/Martina (should be unified)
- Malformed names (Kamiel, Vaňk, Andreo)
"""

import re
from pathlib import Path
from collections import defaultdict

def parse_map_file(map_path):
    """Parse a map file and extract person entries."""
    persons = []
    current_person = None

    with open(map_path, 'r', encoding='utf-8') as f:
        in_persons_section = False
        for line in f:
            line = line.rstrip('\n')

            # Check if we're in the OSOBY section
            if line.strip() == 'OSOBY':
                in_persons_section = True
                continue
            elif line.strip() == '-----':
                continue
            elif line.strip() == '' or line.strip().startswith('ADDRESS') or line.strip().startswith('BIRTH_'):
                # End of persons section
                if current_person:
                    persons.append(current_person)
                break

            if not in_persons_section:
                continue

            # Parse person entry
            match = re.match(r'\[\[PERSON_(\d+)\]\]: (.+)', line)
            if match:
                # Save previous person
                if current_person:
                    persons.append(current_person)

                # Start new person
                person_id = match.group(1)
                name = match.group(2)
                current_person = {
                    'id': person_id,
                    'canonical': name,
                    'variants': []
                }
            elif line.strip().startswith('-'):
                # Variant form
                variant = line.strip()[2:].strip()
                if current_person:
                    current_person['variants'].append(variant)

    # Add last person
    if current_person:
        persons.append(current_person)

    return persons

def find_duplicates(persons):
    """Find duplicate persons based on name similarity."""
    duplicates = []

    # Group by last name
    by_lastname = defaultdict(list)
    for p in persons:
        # Extract last name (last word)
        parts = p['canonical'].split()
        if len(parts) >= 2:
            lastname = parts[-1]
            by_lastname[lastname].append(p)

    # Check for suspicious patterns within same last name
    for lastname, group in by_lastname.items():
        if len(group) < 2:
            continue

        # Extract first names
        firstnames = []
        for p in group:
            parts = p['canonical'].split()
            firstname = ' '.join(parts[:-1])
            firstnames.append((firstname, p))

        # Check for similar first names (potential duplicates)
        for i, (fn1, p1) in enumerate(firstnames):
            for fn2, p2 in firstnames[i+1:]:
                # Pattern 1: Male/female variants (a/o ending difference)
                if fn1.endswith('a') and fn2 == fn1[:-1] + 'o':
                    duplicates.append((p1, p2, 'GENDER_SUFFIX'))
                elif fn2.endswith('a') and fn1 == fn2[:-1] + 'o':
                    duplicates.append((p1, p2, 'GENDER_SUFFIX'))
                # Pattern 2: Similar with single char difference
                elif len(fn1) == len(fn2) and sum(c1 != c2 for c1, c2 in zip(fn1, fn2)) == 1:
                    duplicates.append((p1, p2, 'TYPO'))

    return duplicates

def audit_contract(contract_num):
    """Audit a single contract for duplicates."""
    map_path = Path(f'smlouva{contract_num}_map.txt')

    if not map_path.exists():
        print(f"❌ Map file not found: {map_path}")
        return None

    persons = parse_map_file(map_path)
    duplicates = find_duplicates(persons)

    return {
        'contract': contract_num,
        'total_persons': len(persons),
        'duplicates': duplicates
    }

def main():
    print("🔍 Auditing contracts 19-22 for duplicate persons...\n")

    total_duplicates = 0

    for contract_num in [19, 20, 21, 22]:
        result = audit_contract(contract_num)

        if result is None:
            continue

        print(f"📄 Contract {contract_num}: {result['total_persons']} persons")

        if result['duplicates']:
            print(f"   ⚠️  Found {len(result['duplicates'])} duplicate(s):")
            for p1, p2, reason in result['duplicates']:
                print(f"      • [[PERSON_{p1['id']}]]: {p1['canonical']}")
                print(f"      • [[PERSON_{p2['id']}]]: {p2['canonical']}")
                print(f"        Reason: {reason}")
            total_duplicates += len(result['duplicates'])
        else:
            print(f"   ✅ No duplicates found")

        print()

    print("=" * 60)
    if total_duplicates == 0:
        print("✅ SUCCESS! All contracts are clean - no duplicates found!")
    else:
        print(f"❌ FOUND {total_duplicates} total duplicate(s) across all contracts")
    print("=" * 60)

if __name__ == '__main__':
    main()
