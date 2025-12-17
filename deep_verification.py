#!/usr/bin/env python3
"""
DŮKLADNÁ verifikace - extrahuje VŠECHNA jména z dokumentu a kontroluje že jsou v mapě.
"""
import sys
import re
from docx import Document
from collections import defaultdict

def extract_all_names_from_document(doc_text):
    """Extrahuj VŠECHNA jména z dokumentu pomocí regex."""
    # Pattern pro česká jména (Jméno Příjmení)
    # Velké písmeno na začátku, pak lowercase s diakritikou
    name_pattern = r'\b([A-ZČŘŠŽÝÁÍÉÚŮĎŤŇ][a-zčřšžýáíéúůďťňěöü]+)\s+([A-ZČŘŠŽÝÁÍÉÚŮĎŤŇ][a-zčřšžýáíéúůďťňěöüa-]+)\b'

    names_in_doc = []
    for match in re.finditer(name_pattern, doc_text):
        first = match.group(1)
        last = match.group(2)
        full_name = f"{first} {last}"
        names_in_doc.append(full_name)

    return names_in_doc

def parse_map(map_path):
    """Parse mapy - vrátí seznam osob s canonical a variantami."""
    persons = []
    current_person = None

    with open(map_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('[[PERSON_'):
                match = re.match(r'\[\[PERSON_(\d+)\]\]: (.+)', line)
                if match:
                    person_id = int(match.group(1))
                    canonical = match.group(2).strip()
                    current_person = {
                        'id': person_id,
                        'tag': f'PERSON_{person_id}',
                        'canonical': canonical,
                        'variants': []
                    }
                    persons.append(current_person)
            elif line.strip().startswith('- ') and current_person:
                variant = line.strip()[2:].strip()
                current_person['variants'].append(variant)

    return persons

def deep_verify(docx_path, map_path):
    """DŮKLADNÁ verifikace mapy proti dokumentu."""

    print(f"\n{'='*80}")
    print(f"DŮKLADNÁ VERIFIKACE: {docx_path}")
    print(f"{'='*80}\n")

    # Load document
    doc = Document(docx_path)
    doc_text = ' '.join([p.text for p in doc.paragraphs])

    # Extract ALL names from document
    print("Krok 1: Extrakce VŠECH jmen z dokumentu...")
    names_in_doc = extract_all_names_from_document(doc_text)
    unique_names_in_doc = list(set(names_in_doc))

    print(f"  Nalezeno {len(names_in_doc)} výskytů jmen")
    print(f"  Unikátních jmen: {len(unique_names_in_doc)}")

    # Parse map
    print("\nKrok 2: Parsování mapy...")
    persons = parse_map(map_path)

    # Build index: name -> list of persons
    name_to_persons = defaultdict(list)
    for person in persons:
        # Add canonical
        name_to_persons[person['canonical']].append((person['tag'], 'canonical'))
        # Add variants
        for variant in person['variants']:
            name_to_persons[variant].append((person['tag'], 'variant'))

    all_names_in_map = set(name_to_persons.keys())

    print(f"  Osob v mapě: {len(persons)}")
    print(f"  Celkem jmen v mapě (canonical + varianty): {len(all_names_in_map)}")

    # Check 1: All names from document are in map
    print("\n" + "="*80)
    print("KONTROLA 1: Každé jméno z dokumentu je v mapě")
    print("="*80)

    names_not_in_map = []
    for name in unique_names_in_doc:
        if name not in name_to_persons:
            names_not_in_map.append(name)

    if names_not_in_map:
        print(f"\n❌ PROBLÉM: {len(names_not_in_map)} jmen z dokumentu CHYBÍ v mapě:\n")
        for name in sorted(names_not_in_map)[:50]:
            # Count occurrences
            count = names_in_doc.count(name)
            print(f"  {name:40} (vyskytuje se {count}x)")
        if len(names_not_in_map) > 50:
            print(f"\n  ... a dalších {len(names_not_in_map) - 50} jmen")
    else:
        print(f"✅ Všech {len(unique_names_in_doc)} unikátních jmen z dokumentu je v mapě")

    # Check 2: No duplicates - same name under multiple persons
    print("\n" + "="*80)
    print("KONTROLA 2: Žádné duplicity - každé jméno pod jedním anonymizátorem")
    print("="*80)

    duplicates = []
    for name, occurrences in name_to_persons.items():
        person_tags = set(occ[0] for occ in occurrences)
        if len(person_tags) > 1:
            duplicates.append((name, occurrences))

    if duplicates:
        print(f"\n❌ PROBLÉM: {len(duplicates)} jmen je pod VÍCE anonymizátory:\n")
        for name, occurrences in sorted(duplicates)[:30]:
            print(f"  '{name}':")
            for tag, typ in occurrences:
                print(f"    - {tag} ({typ})")
        if len(duplicates) > 30:
            print(f"\n  ... a dalších {len(duplicates) - 30} duplicit")
    else:
        print(f"✅ Žádné duplicity - každé jméno je pod jedním anonymizátorem")

    # Check 3: All names in map are in document
    print("\n" + "="*80)
    print("KONTROLA 3: Každé jméno z mapy je v dokumentu")
    print("="*80)

    names_in_map_not_in_doc = []
    for name in all_names_in_map:
        if name not in doc_text:
            names_in_map_not_in_doc.append(name)

    if names_in_map_not_in_doc:
        print(f"\n❌ PROBLÉM: {len(names_in_map_not_in_doc)} jmen z mapy NENÍ v dokumentu:\n")
        for name in sorted(names_in_map_not_in_doc)[:30]:
            # Find which person
            persons_with_name = name_to_persons[name]
            for tag, typ in persons_with_name:
                print(f"  {tag} ({typ}): {name}")
        if len(names_in_map_not_in_doc) > 30:
            print(f"\n  ... a dalších {len(names_in_map_not_in_doc) - 30} jmen")
    else:
        print(f"✅ Všech {len(all_names_in_map)} jmen z mapy je v dokumentu")

    # Final summary
    print("\n" + "="*80)
    print("FINÁLNÍ SHRNUTÍ")
    print("="*80)
    print(f"  Jmen v dokumentu (unikátních): {len(unique_names_in_doc)}")
    print(f"  Jmen v mapě: {len(all_names_in_map)}")
    print(f"  Osob v mapě: {len(persons)}")
    print()

    all_ok = (
        len(names_not_in_map) == 0 and
        len(duplicates) == 0 and
        len(names_in_map_not_in_doc) == 0
    )

    if all_ok:
        print("✅✅✅ MAPA JE 100% SPRÁVNÁ! ✅✅✅")
        print("\n  Všechna jména z dokumentu jsou v mapě")
        print("  Žádné duplicity")
        print("  Všechna jména z mapy jsou v dokumentu")
        return True
    else:
        print("❌❌❌ MAPA MÁ PROBLÉMY! ❌❌❌")
        print()
        if names_not_in_map:
            print(f"  ❌ {len(names_not_in_map)} jmen z dokumentu chybí v mapě")
        if duplicates:
            print(f"  ❌ {len(duplicates)} duplicit (jméno pod více anonymizátory)")
        if names_in_map_not_in_doc:
            print(f"  ❌ {len(names_in_map_not_in_doc)} jmen z mapy není v dokumentu")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python deep_verification.py <contract_number>")
        print("Example: python deep_verification.py 24")
        sys.exit(1)

    contract_num = sys.argv[1]
    docx_path = f'smlouva{contract_num}.docx'
    map_path = f'smlouva{contract_num}_map.txt'

    result = deep_verify(docx_path, map_path)
    sys.exit(0 if result else 1)
