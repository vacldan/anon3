"""
Full corpus test: re-anonymize all source contracts and check for:
  1. Leaks (original PII found in anonymized text)
  2. False PERSON detections (common words detected as persons)
  3. ADDRESS duplicates (same logical address with multiple tags)
  4. Nonsense entities
"""
import sys, os, json, glob, re, time, traceback
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'anon72.pyd.off')):
    pass

import anon72

KNOWN_FALSE_PERSONS = {
    'expres business', 'měsíční poplatek', 'specifikace běžný',
    'specifikaec běžný', 'přemysla otakara', 'kutná hora',
    'havlíčkův brod', 'mladá boleslav', 'uherské hradiště',
    'valašské meziříčí', 'mariánské lázně', 'jablonec nisou',
    'česká lípa', 'jindřichův hradec', 'žďár sázavou',
    'český krumlov', 'nový jičín',
}

SUSPICIOUS_PERSON_WORDS = {
    'poplatek', 'poplatky', 'poplatku', 'poplatkem',
    'měsíční', 'měsíčního', 'měsíčním',
    'specifikace', 'specifikaec', 'běžný', 'běžného', 'běžném', 'běžným',
    'business', 'expres', 'express',
    'banka', 'banky', 'bankou', 'banku',
    'smlouva', 'smlouvy', 'smlouvou', 'smlouvu',
    'pojistka', 'pojistky', 'pojištění',
    'splátka', 'splátky', 'splátek',
    'úvěr', 'úvěru', 'úvěrem',
    'klient', 'klienta', 'klientem',
    'zpracovatel', 'správce', 'příjemce',
    'dodavatel', 'odběratel', 'objednatel',
    'stav', 'nový', 'nová', 'nové', 'nového',
}


def find_source_contracts(test_dir):
    sources = []
    for f in glob.glob(os.path.join(test_dir, 'smlouva*.docx')):
        base = os.path.basename(f)
        if '_anon' in base or '_deanon' in base:
            continue
        sources.append(f)
    return sorted(sources)


def run_anonymization(src_path):
    try:
        base = os.path.splitext(src_path)[0]
        output_path = base + '_anon.docx'
        json_map = base + '_map.json'
        txt_map = base + '_map.txt'
        pdf_report = base + '_report.pdf'

        anon = anon72.Anonymizer()
        result = anon.anonymize_docx(src_path, output_path, json_map, txt_map, pdf_report)
        return result, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def check_map_for_issues(map_path, src_name):
    issues = []
    if not os.path.exists(map_path):
        issues.append(('NO_MAP', src_name, 'Map file not found'))
        return issues

    with open(map_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            issues.append(('BAD_JSON', src_name, str(e)))
            return issues

    persons = data.get('persons', data.get('PERSONS', {}))
    addresses = data.get('addresses', data.get('ADDRESS', {}))

    for tag, info in persons.items():
        canonical = info if isinstance(info, str) else (info.get('canonical', str(info)))
        canonical_lower = canonical.lower().strip() if isinstance(canonical, str) else ''

        if canonical_lower in KNOWN_FALSE_PERSONS:
            issues.append(('FALSE_PERSON', src_name, f"{tag}: {canonical}"))

        words = canonical_lower.split()
        for w in words:
            if w in SUSPICIOUS_PERSON_WORDS:
                issues.append(('SUSPICIOUS_PERSON', src_name, f"{tag}: {canonical} (word: {w})"))
                break

    addr_values = {}
    for tag, info in addresses.items():
        if isinstance(info, str):
            canonical = info
        elif isinstance(info, dict):
            canonical = info.get('canonical', str(info))
        elif isinstance(info, list) and len(info) > 0:
            canonical = info[0] if isinstance(info[0], str) else str(info[0])
        else:
            canonical = str(info)
        addr_values[tag] = canonical

    tags_list = list(addr_values.keys())
    for i, tag_a in enumerate(tags_list):
        val_a = addr_values[tag_a].strip()
        for tag_b in tags_list[i+1:]:
            val_b = addr_values[tag_b].strip()
            if len(val_a) >= 4 and len(val_b) >= 4:
                if val_a in val_b or val_b in val_a:
                    issues.append(('ADDR_DUPLICATE', src_name,
                                   f"{tag_a}='{val_a}' vs {tag_b}='{val_b}'"))

    return issues


def check_leak_in_anon(anon_path, map_path, src_name):
    issues = []
    if not os.path.exists(anon_path) or not os.path.exists(map_path):
        return issues

    try:
        from docx import Document
        doc = Document(anon_path)
        full_text = '\n'.join(p.text for p in doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    full_text += '\n' + cell.text
    except Exception:
        return issues

    with open(map_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return issues

    persons = data.get('persons', data.get('PERSONS', {}))
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
                ctx = full_text[max(0, ctx_idx-30):ctx_idx+len(v_clean)+30].replace('\n', ' ')
                if f'[[' not in ctx or v_clean not in re.findall(r'\[\[[A-Z_]+\d*\]\]', ctx):
                    tag_pattern = re.compile(r'\[\[[A-Z_]+_\d+\]\]')
                    nearby = full_text[max(0, ctx_idx-5):ctx_idx+len(v_clean)+5]
                    if not tag_pattern.search(nearby):
                        issues.append(('PERSON_LEAK', src_name,
                                       f"'{v_clean}' found in anon doc: ...{ctx}..."))

    addresses = data.get('addresses', data.get('ADDRESS', {}))
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
                    issues.append(('ADDR_LEAK', src_name,
                                   f"'{v_clean}' found in anon doc: ...{ctx}..."))

    return issues


def main():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    sources = find_source_contracts(test_dir)
    print(f"Found {len(sources)} source contracts to test")
    print("=" * 80)

    all_issues = []
    success = 0
    fail = 0
    t0 = time.time()

    for i, src in enumerate(sources):
        name = os.path.basename(src)
        base = os.path.splitext(src)[0]
        anon_path = base + '_anon.docx'
        map_json = base + '_map.json'

        print(f"[{i+1}/{len(sources)}] {name}...", end=' ', flush=True)

        result, error = run_anonymization(src)
        if error:
            print(f"ERROR: {error}")
            all_issues.append(('ANON_ERROR', name, error))
            fail += 1
            continue

        print("OK", end=' ', flush=True)
        success += 1

        file_issues = []
        file_issues.extend(check_map_for_issues(map_json, name))
        file_issues.extend(check_leak_in_anon(anon_path, map_json, name))

        if file_issues:
            print(f"({len(file_issues)} issues)")
            all_issues.extend(file_issues)
        else:
            print("CLEAN")

    elapsed = time.time() - t0
    print()
    print("=" * 80)
    print(f"COMPLETED in {elapsed:.1f}s")
    print(f"  Success: {success}/{len(sources)}")
    print(f"  Failed:  {fail}/{len(sources)}")
    print(f"  Issues:  {len(all_issues)}")
    print()

    if all_issues:
        by_type = defaultdict(list)
        for issue_type, src_name, detail in all_issues:
            by_type[issue_type].append((src_name, detail))

        for itype in sorted(by_type.keys()):
            items = by_type[itype]
            print(f"\n--- {itype} ({len(items)} occurrences) ---")
            for src_name, detail in items[:30]:
                print(f"  [{src_name}] {detail}")
            if len(items) > 30:
                print(f"  ... and {len(items)-30} more")
    else:
        print("ALL CONTRACTS CLEAN - No issues found!")

    report = {
        'total': len(sources),
        'success': success,
        'fail': fail,
        'total_issues': len(all_issues),
        'issues_by_type': {k: len(v) for k, v in defaultdict(list, {t: [(s,d) for t2,s,d in all_issues if t2==t] for t in set(t2 for t2,_,_ in all_issues)}).items()},
        'details': [{'type': t, 'file': s, 'detail': d} for t, s, d in all_issues],
    }
    report_path = os.path.join(test_dir, 'full_test_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == '__main__':
    main()
