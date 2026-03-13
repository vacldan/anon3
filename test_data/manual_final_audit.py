#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manuální finální audit: smlouva po smlouvě, mapa po mapě.
Kontroluje leaky a nestabilní výsledky pro ruční review.
"""
import os
import sys
import json
import re
from collections import defaultdict
from pathlib import Path

# Ensure we can import anon72
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from docx import Document
except ImportError:
    Document = None

TEST_DIR = Path(__file__).resolve().parent
REPORT_FILE = TEST_DIR / 'manual_audit_report.txt'


def get_full_text_from_docx(path):
    """Extract all text from docx (paragraphs + tables)."""
    if not Document:
        return ''
    try:
        doc = Document(path)
        full_text = '\n'.join(p.text for p in doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    full_text += '\n' + '\n'.join(p.text for p in cell.paragraphs)
        return full_text
    except Exception as e:
        return f'[ERROR: {e}]'


def check_leak_in_anon(anon_path, map_path, src_name):
    """Check if original PII from map appears in anonymized doc (leak)."""
    issues = []
    if not anon_path.exists() or not map_path.exists():
        return issues

    full_text = get_full_text_from_docx(anon_path)
    if full_text.startswith('[ERROR'):
        return [('READ_ERROR', src_name, full_text)]

    with open(map_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            return [('MAP_JSON_ERROR', src_name, str(e))]

    persons = data.get('persons', data.get('PERSONS', {}))
    addresses = data.get('addresses', data.get('ADDRESS', {}))

    for tag, info in persons.items():
        if isinstance(info, str):
            variants = [info]
        elif isinstance(info, dict):
            canonical = info.get('canonical', '')
            variants = [canonical] + info.get('variants', [])
        elif isinstance(info, list):
            variants = info
        else:
            variants = [str(info)]

        for v in variants:
            if not v or len(v) < 3:
                continue
            v_clean = v.strip()
            if v_clean.lower() in {'bc.', 'ing.', 'mgr.', 'mudr.', 'judr.', 'phdr.',
                                    'rndr.', 'doc.', 'prof.', 'pan', 'paní', 'p.'}:
                continue
            if v_clean in full_text:
                ctx_idx = full_text.find(v_clean)
                nearby = full_text[max(0, ctx_idx-5):ctx_idx+len(v_clean)+5]
                tag_pattern = re.compile(r'\[\[[A-Z_]+_\d+\]\]')
                if not tag_pattern.search(nearby):
                    ctx = full_text[max(0, ctx_idx-30):ctx_idx+len(v_clean)+30].replace('\n', ' ')
                    issues.append(('PERSON_LEAK', src_name, f"'{v_clean}' ...{ctx[:60]}..."))

    for tag, info in addresses.items():
        if isinstance(info, str):
            variants = [info]
        elif isinstance(info, dict):
            canonical = info.get('canonical', '')
            variants = [canonical] + info.get('variants', [])
        elif isinstance(info, list):
            variants = info
        else:
            variants = [str(info)]

        for v in variants:
            if not v or len(v) < 5:
                continue
            v_clean = v.strip()
            if v_clean in full_text:
                ctx_idx = full_text.find(v_clean)
                nearby = full_text[max(0, ctx_idx-5):ctx_idx+len(v_clean)+5]
                tag_pattern = re.compile(r'\[\[[A-Z_]+_\d+\]\]')
                if not tag_pattern.search(nearby):
                    ctx = full_text[max(0, ctx_idx-30):ctx_idx+len(v_clean)+30].replace('\n', ' ')
                    issues.append(('ADDR_LEAK', src_name, f"'{v_clean[:40]}' ...{ctx[:50]}..."))

    return issues


def check_map_quality(map_path, src_name):
    """Check map for suspicious/false positive entries."""
    issues = []
    if not map_path.exists():
        return [('NO_MAP', src_name, 'Map file not found')]

    with open(map_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            return [('BAD_JSON', src_name, str(e))]

    KNOWN_FALSE_PERSONS = {
        'expres business', 'měsíční poplatek', 'specifikace běžný',
        'přemysla otakara', 'kutná hora', 'havlíčkův brod', 'mladá boleslav',
    }
    SUSPICIOUS_WORDS = {'poplatek', 'měsíční', 'specifikace', 'běžný', 'business',
                        'banka', 'smlouva', 'úvěr', 'splátka', 'klient'}

    persons = data.get('persons', data.get('PERSONS', {}))
    for tag, info in persons.items():
        canonical = info if isinstance(info, str) else (info.get('canonical', str(info)))
        canonical_lower = canonical.lower().strip() if isinstance(canonical, str) else ''
        if canonical_lower in KNOWN_FALSE_PERSONS:
            issues.append(('FALSE_PERSON', src_name, f"{tag}: {canonical}"))
        for w in canonical_lower.split():
            if w in SUSPICIOUS_WORDS:
                issues.append(('SUSPICIOUS_PERSON', src_name, f"{tag}: {canonical}"))
                break

    return issues


def find_contract_pairs():
    """Find all (source, anon, map) triples."""
    pairs = []
    for f in sorted(TEST_DIR.glob('smlouva*.docx')):
        if '_anon' in f.stem or '_deanon' in f.stem:
            continue
        base = f.stem
        anon = TEST_DIR / f'{base}_anon.docx'
        map_json = TEST_DIR / f'{base}_map.json'
        if anon.exists() and map_json.exists():
            pairs.append((f.name, str(anon), str(map_json)))
    return sorted(pairs, key=lambda x: x[0])


def main():
    pairs = find_contract_pairs()
    print(f"Nalezeno {len(pairs)} smluv k auditu")
    print("=" * 80)

    all_issues = []
    by_file = defaultdict(list)

    for i, (src_name, anon_path, map_path) in enumerate(pairs):
        src_name_short = src_name.replace('.docx', '')
        leak_issues = check_leak_in_anon(Path(anon_path), Path(map_path), src_name)
        map_issues = check_map_quality(Path(map_path), src_name)

        file_issues = leak_issues + map_issues
        if file_issues:
            all_issues.extend(file_issues)
            for iss in file_issues:
                by_file[src_name].append(iss)
            status = f"⚠ {len(file_issues)} issues"
        else:
            status = "✓ OK"

        print(f"[{i+1:3d}/{len(pairs)}] {src_name_short:50s} {status}")

    # Write detailed report
    with open(REPORT_FILE, 'w', encoding='utf-8') as out:
        out.write("=" * 80 + "\n")
        out.write("MANUÁLNÍ FINÁLNÍ AUDIT - SMLOUVY A MAPY\n")
        out.write("=" * 80 + "\n\n")
        out.write(f"Celkem smluv: {len(pairs)}\n")
        out.write(f"Celkem issues: {len(all_issues)}\n")
        out.write(f"Smlouvy s issues: {len(by_file)}\n\n")

        if by_file:
            out.write("=" * 80 + "\n")
            out.write("SMLOUVY S PROBLÉMY (pro ruční kontrolu)\n")
            out.write("=" * 80 + "\n\n")
            for fname in sorted(by_file.keys()):
                issues = by_file[fname]
                out.write(f"\n--- {fname} ---\n")
                for itype, _, detail in issues:
                    out.write(f"  [{itype}] {detail}\n")

        out.write("\n" + "=" * 80 + "\n")
        out.write("SHRNUTÍ PODLE TYPU\n")
        out.write("=" * 80 + "\n")
        by_type = defaultdict(int)
        for t, _, _ in all_issues:
            by_type[t] += 1
        for t in sorted(by_type.keys()):
            out.write(f"  {t}: {by_type[t]}\n")

    print()
    print("=" * 80)
    print(f"VÝSLEDEK: {len(all_issues)} celkových issues v {len(by_file)} smlouvách")
    print(f"Detailní report: {REPORT_FILE}")
    print("=" * 80)

    if all_issues:
        print("\nSmlouvy vyžadující ruční kontrolu:")
        for fname in sorted(by_file.keys())[:20]:
            print(f"  - {fname}")
        if len(by_file) > 20:
            print(f"  ... a dalších {len(by_file)-20}")


if __name__ == '__main__':
    main()
