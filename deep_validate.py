#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hluboká validace anonymizace – porovnání mapy s dokumentem.

Kontroly:
1. Kanonické formy – správný nominativ, diakritika (-ová ne -ova)
2. Úniky – žádný tvar jména nezůstal v anonymizovaném dokumentu
3. Phantom osoby – každá osoba v mapě má tag v anon dokumentu
4. Konzistence – varianty v mapě odpovídají obsahu zdrojového dokumentu
5. Nepokryté tvary – jména ve zdroji, která nejsou v mapě

Použití:
  python deep_validate.py <src.docx> [<anon.docx>] [<map.txt>]
  Nebo bez argumentů: validuje nejnovější výstupy pro smlouvy v test_data/
"""

import sys
import re
import os
import json
import glob
from pathlib import Path
from docx import Document
from collections import defaultdict


def load_names_library(json_path: str = "cz_names.v1.json") -> set:
    """Načte česká křestní jména z JSON (validace proti names.json)."""
    try:
        script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        json_file = script_dir / json_path
        if not json_file.exists():
            json_file = Path.cwd() / json_path
        if not json_file.exists():
            return set()
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        names = set()
        if isinstance(data, dict):
            if 'firstnames' in data:
                for gender_key in ['M', 'F', 'U']:
                    if gender_key in data.get('firstnames', {}):
                        names.update(data['firstnames'][gender_key])
            if 'firstnames_no_diac' in data:
                for gender_key in ['M', 'F', 'U']:
                    if gender_key in data.get('firstnames_no_diac', {}):
                        names.update(data['firstnames_no_diac'][gender_key])
            if not names:
                names.update(data.get('male', []))
                names.update(data.get('female', []))
        elif isinstance(data, list):
            names.update(data)
        return {n.lower() for n in names}
    except Exception:
        return set()


def get_doc_text(doc_path: str) -> str:
    """Vrátí celý text dokumentu (odstavce + tabulky)."""
    doc = Document(doc_path)
    parts = []
    for p in doc.paragraphs:
        if p.text.strip():
            parts.append(p.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p.text.strip():
                        parts.append(p.text)
    return '\n'.join(parts)


def parse_txt_map(map_path: str) -> dict:
    """
    Parsuje _map.txt do struktury:
    { tag: { 'canonical': 'Jméno Příjmení', 'variants': ['tvar1', 'tvar2', ...] } }
    """
    result = {}
    with open(map_path, encoding='utf-8') as f:
        current_tag = None
        current_canonical = None
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            m = re.match(r'^(\[\[PERSON_\d+\]\]):\s*(.+)$', line)
            if m:
                current_tag = m.group(1)
                current_canonical = m.group(2).strip()
                result[current_tag] = {'canonical': current_canonical, 'variants': []}
                continue
            if line.strip().startswith('-') and current_tag:
                v = line.strip().lstrip('-').strip()
                if v and v != current_canonical:
                    result[current_tag]['variants'].append(v)
    return result


def check_canonical_forms(map_data: dict) -> list:
    """Kontrola kanonických forem – nominativ, diakritika."""
    errors = []
    for tag, data in map_data.items():
        canonical = data['canonical']
        if not canonical:
            continue
        parts = canonical.split(None, 1)
        first = parts[0] if parts else ''
        last = parts[1] if len(parts) > 1 else ''
        last_lo = last.lower()

        # Ženská příjmení: musí končit -ová (s dlouhým ó), ne -ova
        if last_lo.endswith('ova') and not last_lo.endswith('ová'):
            errors.append(f"{tag}: '{canonical}' – má být -ová (dlouhé ó), ne -ova")

        # Oříznutá / chybná mužská příjmení (známé chyby)
        truncations = [
            ('Zík', 'Zíka'), ('Chrástk', 'Chrástek'), ('Kolísk', 'Kolísek'),
            ('Havličk', 'Havlíček'), ('Šember', 'Šembera'), ('Rendlo', 'Rendl'),
            ('Holasa', 'Holas'), ('Berana', 'Beran'), ('Konráda', 'Konrád'),
            ('Frydrycha', 'Frydrych'), ('Přikryla', 'Přikryl'),
            ('Štik', 'Štika'), ('Havl', 'Havel'),
            ('Dvořáek', 'Dvořák'), ('Vlná', 'Vlna'), ('Vlnou', 'Vlna'),
        ]
        for wrong, right in truncations:
            if last == wrong:
                errors.append(f"{tag}: '{canonical}' – má být '{right}'")

        # Gender mismatch: mužské -o + ženské příjmení -ová (Martino Jeřábková → Martina)
        first_lo = first.lower()
        if first_lo.endswith('o') and last_lo.endswith(('ová', 'á')):
            if first_lo not in ('bruno', 'dušan', 'kamil', 'renato', 'emil', 'daniel'):  # legitimní mužská -o
                errors.append(f"{tag}: '{canonical}' – gender mismatch (křestní -o + příjmení -ová)")

        # Špatné inference: Martino/Romano/Mirko + -ová (mělo být Martina/Romana/Mirka)
        bad_male_o_for_female = ('martino', 'romano', 'mirko')
        if first_lo in bad_male_o_for_female and last_lo.endswith(('ová', 'á')):
            errors.append(f"{tag}: '{canonical}' – chybný tvar křestního jména (mělo být -a)")

    return errors


def check_canonical_errors_in_variants(map_data: dict) -> list:
    """Chyby v variantách (známé typo v příjmení)."""
    errors = []
    bad_surname_typos = ('dvořáek', 'vlná')  # Dvořák, Vlna
    for tag, data in map_data.items():
        for v in data.get('variants', []):
            if not v or len(v) < 5:
                continue
            parts = v.split(None, 1)
            if len(parts) < 2:
                continue
            first, last = parts[0].lower(), parts[1].lower()
            if last in bad_surname_typos:
                errors.append(f"{tag} variant: '{v}' – pravděpodobný typo v příjmení")
    return errors


def check_first_name_in_library(map_data: dict, czech_first_names: set) -> list:
    """Kontrola: křestní jméno (první slovo) musí být v names.json – role/nesmysly nepatří do mapy."""
    if not czech_first_names:
        return []
    errors = []
    # Rozšíření o běžná česká jména, která mohou chybět v MVČR knihovně
    # (sync s anon72 common_czech_names + jména z validace co unikla)
    extended = czech_first_names | {
        'jan', 'petr', 'pavel', 'jiří', 'josef', 'tomáš', 'martin', 'jakub', 'david', 'daniel',
        'karel', 'marek', 'ondřej', 'filip', 'matěj', 'dominik', 'adámek', 'vojtěch',
        'jana', 'marie', 'eva', 'anna', 'lenka', 'kateřina', 'lucie', 'teresa', 'tereza',
        'veronika', 'kristýna', 'petra', 'markéta', 'barbora', 'alena', 'iva',
        'hana', 'věra', 'zdeněk', 'laura', 'alois',
        'alice', 'krista', 'antonie', 'nadie', 'vito', 'marco', 'methoděj', 'nikola',
        'ladislav', 'stanislav', 'jaroslav', 'miroslav', 'vlastimil',
        'vladimír', 'bohumil', 'miloslav', 'lubomír', 'oldřich', 'bedřich',
        'přemysl', 'ctibor', 'radek', 'radka', 'šárka', 'dagmar',
        'blanka', 'jitka', 'ivana', 'monika', 'soňa', 'drahomíra',
        'růžena', 'libuše', 'milada', 'anežka', 'hedvika', 'květoslava',
        'nikol', 'sona', 'soňa',
        'vlasta', 'lenora', 'žanina', 'rene', 'pavla', 'alex', 'max',
    }
    for tag, data in map_data.items():
        canonical = data.get('canonical') or ''
        parts = canonical.split(None, 1)
        first = (parts[0] if parts else '').lower()
        if not first or len(first) < 2:
            continue
        if first not in extended:
            errors.append(f"{tag}: '{canonical}' – '{first}' není v names.json (role/nesmysl)")
    return errors


def check_blacklist_in_persons(map_data: dict) -> list:
    """Osoby v mapě obsahující blacklist slova – nesmí to být osoby (Prosím David, Firma Horáková, role)."""
    blacklist = {
        'prosím', 'firma', 'manager', 'services', 'risk', 'account',
        'senior', 'developer', 'architect', 'director', 'chief', 'officer',
    }
    errors = []
    for tag, data in map_data.items():
        canonical = data['canonical'] or ''
        all_forms = [canonical] + list(data.get('variants', []))
        for form in all_forms:
            if not form:
                continue
            words = set(form.lower().split())
            hit = words & blacklist
            if hit:
                errors.append(f"{tag}: '{canonical}' – obsahuje blacklist slovo: {hit}")
                break
    return errors


def check_leaks(anon_text: str, map_data: dict) -> list:
    """Kontrola, že žádný tvar z mapy nezůstal v anonymizovaném dokumentu."""
    leaks = []
    for tag, data in map_data.items():
        canonical = data['canonical']
        all_forms = [canonical] + data['variants']
        for form in all_forms:
            if not form or len(form) < 4:
                continue
            # Hledáme celé slovo (ne substring)
            pat = re.compile(r'(?<![a-záčďéěíňóřšťúůýž])({}) (?=[a-záčďéěíňóřšťúůýž])|(?<= )({})[^a-záčďéěíňóřšťúůýž]'.format(
                re.escape(form), re.escape(form)), re.IGNORECASE)
            if re.search(r'\b' + re.escape(form) + r'\b', anon_text, re.IGNORECASE):
                leaks.append(form)
    return list(set(leaks))


def check_phantoms(anon_text: str, map_data: dict) -> list:
    """Osoby v mapě, jejichž tag není v anonymizovaném dokumentu."""
    phantoms = []
    for tag in map_data:
        if tag not in anon_text:
            phantoms.append((tag, map_data[tag]['canonical']))
    return phantoms


def check_variants_in_source(src_text: str, map_data: dict) -> list:
    """Varianty v mapě, které nejsou ve zdrojovém dokumentu (možná chyba)."""
    missing = []
    for tag, data in map_data.items():
        for v in [data['canonical']] + data['variants']:
            if v and v not in src_text and v.replace(' ', '  ') not in src_text:
                # tolerance pro extra mezery
                if re.search(re.escape(v.replace(' ', r'\s+')), src_text):
                    continue
                missing.append((tag, v))
    return missing


# Slovní spojení, která NEJSOU jména (role, místa, firmy)
SKIP_2WORD = {
    'tento dokument', 'celkem kč', 'datum vydání', 'hlavní smlouva', 'bankovní účet',
    'brno telefon', 'praha telefon', 'ostrava telefon', 'digital solutions', 'marketing plus',
    'backend developer', 'customer success', 'nova kolářská', 'škoda octavia', 'czech republic',
    'karlovy vary', 'hradec králové', 'české budějovice', 'staré město', 'nový jičín',
    'prosím davide', 'bohnice dětské', 'pobočka praha', 'google authenticator', 'dell latitude',
    'home credit', 'provident financial', 'ford transit', 'škoda karoq', 'visa classic',
    'microsoft azure', 'prague eye', 'credo ventures', 'account manager', 'senior developer',
    'cloud architect', 'team lead', 'scrum master', 'data protection', 'amazon web',
    'mayo clinic',
}

def find_uncovered_names(src_text: str, map_data: dict) -> list:
    """Potenciální jména ve zdroji, která nejsou v mapě."""
    all_mapped = set()
    for data in map_data.values():
        all_mapped.add(data['canonical'].lower())
        for v in data['variants']:
            all_mapped.add(v.lower())

    CZ_UPPER = r'A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ'
    CZ_LOWER = r'a-záčďéěíňóřšťúůýž'
    pattern = rf'\b([{CZ_UPPER}][{CZ_LOWER}]+)\s+([{CZ_UPPER}][{CZ_LOWER}]+)\b'
    found = []
    for m in re.finditer(pattern, src_text):
        name = f"{m.group(1)} {m.group(2)}"
        if name.lower() in SKIP_2WORD or name.lower() in all_mapped:
            continue
        if len(m.group(1)) >= 3 and len(m.group(2)) >= 3:
            found.append(name)
    return list(set(found))[:50]


def find_uncovered_real_names(src_text: str, map_data: dict, czech_first_names: set,
                              anon_text: str = None) -> list:
    """Pouze jména, kde první slovo je v knihovně křestních jmen – pravděpodobné úniky."""
    all_mapped = set()
    for data in map_data.values():
        all_mapped.add(data['canonical'].lower())
        for v in data['variants']:
            all_mapped.add(v.lower())

    extended = czech_first_names | {
        'nikol', 'nikola', 'kateřina', 'vlasta', 'lenora', 'žanina', 'čeněk', 'pavla', 'radka',
        'romana', 'mirka', 'otakar', 'rene', 'renáta', 'iva', 'max', 'alex', 'radko',
    }
    CZ_UPPER = r'A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ'
    CZ_LOWER = r'a-záčďéěíňóřšťúůýž'
    pattern = rf'\b([{CZ_UPPER}][{CZ_LOWER}]+)\s+([{CZ_UPPER}][{CZ_LOWER}]+)\b'
    real = []
    for m in re.finditer(pattern, src_text):
        first, last = m.group(1).lower(), m.group(2).lower()
        if first not in extended:
            continue
        full_lower = f"{m.group(1)} {m.group(2)}".lower()
        if full_lower in all_mapped or full_lower in SKIP_2WORD:
            continue
        if last in ('pacient', 'pacientka', 'zaměstnanec', 'klient', 'datum'):
            continue
        full_orig = f"{m.group(1)} {m.group(2)}"
        if anon_text and full_orig not in anon_text:
            continue
        real.append(full_orig)
    return list(set(real))


def compute_score(errors_canonical, errors_blacklist, errors_names_lib, leaks, phantoms,
                  uncovered_real=None, errors_canonical_variants=None) -> tuple:
    """Výpočet skóre 0–10."""
    score = 10
    if errors_canonical:
        score -= min(3, len(errors_canonical) * 0.5)
    if errors_canonical_variants:
        score -= min(2, len(errors_canonical_variants) * 0.3)
    if errors_blacklist:
        score -= min(2, len(errors_blacklist) * 0.5)
    if errors_names_lib:
        score -= min(2, len(errors_names_lib) * 0.5)
    if leaks:
        score -= min(3, len(leaks) * 1)
    if phantoms:
        score -= min(2, len(phantoms) * 0.5)
    if uncovered_real:
        score -= min(3, len(uncovered_real) * 0.5)
    return max(0, round(score, 1)), 10


def run_validation(src_path: str, anon_path: str = None, map_path: str = None) -> dict:
    """Spustí všechny kontroly a vrátí strukturovaný výsledek."""
    base = Path(src_path).stem.replace('.docx', '')
    base_dir = Path(src_path).parent

    if not anon_path:
        candidates = sorted(glob.glob(str(base_dir / f'{base}_anon_*.docx')), key=os.path.getmtime, reverse=True)
        simple_anon = base_dir / f'{base}_anon.docx'
        if simple_anon.exists():
            candidates = [str(simple_anon)] + candidates
            candidates = sorted(candidates, key=os.path.getmtime, reverse=True)
        anon_path = candidates[0] if candidates else base_dir / f'{base}_anon.docx'
    if not map_path:
        candidates = sorted(glob.glob(str(base_dir / f'{base}_map_*.txt')), key=os.path.getmtime, reverse=True)
        simple_map = base_dir / f'{base}_map.txt'
        if simple_map.exists():
            candidates = [str(simple_map)] + candidates
            candidates = sorted(candidates, key=os.path.getmtime, reverse=True)
        map_path = candidates[0] if candidates else base_dir / f'{base}_map.txt'

    if not os.path.exists(anon_path):
        return {'error': f'Anonymizovaný dokument nenalezen: {anon_path}'}
    if not os.path.exists(map_path):
        return {'error': f'Mapa nenalezena: {map_path}'}

    src_text = get_doc_text(src_path)
    anon_text = get_doc_text(anon_path)
    map_data = parse_txt_map(map_path)

    czech_first_names = load_names_library()
    errors_canonical = check_canonical_forms(map_data)
    errors_canonical_variants = check_canonical_errors_in_variants(map_data)
    errors_blacklist = check_blacklist_in_persons(map_data)
    errors_names_lib = check_first_name_in_library(map_data, czech_first_names)
    leaks = check_leaks(anon_text, map_data)
    phantoms = check_phantoms(anon_text, map_data)
    variants_not_in_src = check_variants_in_source(src_text, map_data)
    uncovered = find_uncovered_names(src_text, map_data)
    uncovered_real = find_uncovered_real_names(src_text, map_data, czech_first_names, anon_text=anon_text)

    score, max_score = compute_score(
        errors_canonical, errors_blacklist, errors_names_lib, leaks, phantoms,
        uncovered_real=uncovered_real,
        errors_canonical_variants=errors_canonical_variants,
    )

    return {
        'src_path': src_path,
        'anon_path': anon_path,
        'map_path': map_path,
        'score': score,
        'max_score': max_score,
        'persons_count': len(map_data),
        'errors_canonical': errors_canonical,
        'errors_canonical_variants': errors_canonical_variants,
        'errors_blacklist': errors_blacklist,
        'errors_names_lib': errors_names_lib,
        'leaks': leaks,
        'phantoms': phantoms,
        'variants_not_in_src': variants_not_in_src[:20],
        'uncovered': uncovered,
        'uncovered_real': uncovered_real,
    }


def print_report(result: dict):
    """Vytiskne detailní report."""
    if 'error' in result:
        print(f"[CHYBA] {result['error']}")
        return

    s = result['score']
    m = result['max_score']
    print('\n' + '=' * 70)
    print('HLOUBOKÁ VALIDACE ANONYMIZACE')
    print('=' * 70)
    print(f"Zdroj:     {result['src_path']}")
    print(f"Anon:      {result['anon_path']}")
    print(f"Mapa:      {result['map_path']}")
    print(f"Osob:      {result['persons_count']}")
    print()
    print(f"SKÓRE:     {s}/{m}  {'✓ OK' if s >= 9 else '✗ VYŽADUJE OPRAVU'}")
    print()

    if result['errors_canonical']:
        print('--- 1. CHYBY KANONICKÝCH FOREM (základní tvar) ---')
        for e in result['errors_canonical']:
            print(f'  ✗ {e}')
        print()
    else:
        print('--- 1. Kanonické formy: ✓ OK')

    if result.get('errors_canonical_variants'):
        print('--- 1a. CHYBY VE VARIANTÁCH (typo v příjmení) ---')
        for e in result['errors_canonical_variants']:
            print(f'  ✗ {e}')
        print()

    if result.get('errors_blacklist'):
        print('--- 1b. OSOBY S BLACKLIST SLOVEM (Prosím, Firma, role...) ---')
        for e in result['errors_blacklist']:
            print(f'  ✗ {e}')
        print()
    elif 'errors_blacklist' in result:
        print('--- 1b. Blacklist v osobách: ✓ OK')

    if result.get('errors_names_lib'):
        print('--- 1c. KŘESTNÍ JMÉNO MIMO names.json (role/nesmysl) ---')
        for e in result['errors_names_lib']:
            print(f'  ✗ {e}')
        print()
    elif 'errors_names_lib' in result:
        print('--- 1c. Křestní jméno v names.json: ✓ OK')

    if result['leaks']:
        print('--- 2. ÚNIKY JMEN (zůstaly v anonymizovaném dokumentu) ---')
        for l in result['leaks'][:30]:
            print(f'  ✗ {l}')
        if len(result['leaks']) > 30:
            print(f'  ... a dalších {len(result["leaks"]) - 30}')
        print()
    else:
        print('--- 2. Úniky: ✓ žádné')

    if result['phantoms']:
        print('--- 3. PHANTOM OSOBY (v mapě, tag není v dokumentu) ---')
        for tag, canonical in result['phantoms']:
            print(f'  ✗ {tag}: {canonical}')
        print()
    else:
        print('--- 3. Phantom osoby: ✓ žádné')

    if result.get('uncovered_real'):
        print('--- 3a. NEPOKRYTÁ JMÉNA (ve zdroji, křestní v knihovně, chybí v mapě) ---')
        for u in result['uncovered_real'][:20]:
            print(f'  ✗ {u}')
        if len(result['uncovered_real']) > 20:
            print(f'  ... a dalších {len(result["uncovered_real"]) - 20}')
        print()

    if result['variants_not_in_src']:
        print('--- 4. Varianty v mapě bez odpovídajícího textu ve zdroji ---')
        for tag, v in result['variants_not_in_src'][:15]:
            print(f'  ? {tag}: "{v}"')
        print()
    else:
        print('--- 4. Konzistence mapy se zdrojem: ✓ OK')

    if result['uncovered']:
        print('--- 5. Potenciálně nepokrytá jména ve zdroji ---')
        for u in result['uncovered'][:15]:
            print(f'  ? {u}')
        print()

    print('=' * 70)


def main():
    if len(sys.argv) < 2:
        # Bez argumentů: validuj smlouvy 10-33, shrnutí na konci
        base = Path('test_data')
        if not base.exists():
            print("Použití: python deep_validate.py <src.docx> [anon.docx] [map.txt]")
            print("  nebo bez argumentů v adresáři s test_data/")
            sys.exit(1)
        results = []
        for n in range(10, 34):
            if n == 30:
                continue
            src = base / f'smlouva{n}.docx'
            if src.exists():
                r = run_validation(str(src))
                if 'error' not in r:
                    results.append((n, r))
                    print_report(r)
        # Souhrnná tabulka
        if results:
            print('\n' + '=' * 70)
            print('SOUHRN VŠECH SMLUV')
            print('=' * 70)
            print(f"{'Smlouva':<12} {'Skóre':<10} {'Kanon':<6} {'Var':<5} {'Nepokr':<6} {'Úniky':<6} {'Phantom':<7} {'Status'}")
            print('-' * 70)
            for n, r in results:
                ec = len(r['errors_canonical'])
                ev = len(r.get('errors_canonical_variants', []))
                ur = len(r.get('uncovered_real', []))
                lk = len(r['leaks'])
                ph = len(r['phantoms'])
                s = r['score']
                status = '✓' if s >= 9 else '✗'
                print(f"smlouva{n:<6} {s}/{r['max_score']:<6} {ec:<6} {ev:<5} {ur:<6} {lk:<6} {ph:<7} {status}")
            avg = sum(r['score'] for _, r in results) / len(results)
            print('-' * 70)
            print(f"Průměr: {avg:.1f}/10")
            failed = [n for n, r in results if r['score'] < 9]
            if failed:
                sys.exit(1)
    else:
        src = sys.argv[1]
        anon = sys.argv[2] if len(sys.argv) > 2 else None
        mp = sys.argv[3] if len(sys.argv) > 3 else None
        r = run_validation(src, anon, mp)
        print_report(r)
        if 'error' not in r and r.get('score', 10) < 9:
            sys.exit(1)


if __name__ == '__main__':
    main()
