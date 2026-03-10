#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brute-force audit anonymizace:

- ŽÁDNÉ ignore seznamy, ŽÁDNÉ heuristiky.
- Pro každou smlouvu:
  - vezme originál DOCX, k němu _anon.docx a _map.json
  - pro KAŽDÝ "original" z mapy zkusí najít tu samou hodnotu v anon textu
  - navíc spustí jednoduché regexy pro typická PII (RC, tel., email, IBAN, SPZ, VIN, město+PSČ)
- Vše loguje do JSON reportu + krátký přehled do konzole.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

from run_anonymize_tests import TEST_DATA, OUT_DIR, get_all_text_from_docx

import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    # Přepneme konzoli na UTF-8, aby tisk kontextu nespadl na UnicodeEncodeError (Windows cp1250).
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_map_entities(map_json: Path) -> List[dict]:
    data = json.loads(map_json.read_text(encoding="utf-8"))
    return data.get("entities", [])


def find_originals_in_anon(anon_text: str, entities: List[dict]) -> List[Dict]:
    """
    Pro KAŽDÝ original z mapy:
    - žádné filtry (kromě velmi krátkých tokenů < 3 znaků)
    - čistý case-insensitive substring search
    """
    leaks: List[Dict] = []
    lowered = anon_text.lower()
    for ent in entities:
        orig = str(ent.get("original", "")).strip()
        if not orig or len(orig) < 3:
            continue
        if str(orig).startswith("***REDACTED_"):
            continue
        o_low = orig.lower()
        idx = lowered.find(o_low)
        if idx == -1:
            continue
        ctx = anon_text[max(0, idx - 60) : idx + len(orig) + 60].replace("\n", " ")
        leaks.append(
            {
                "original": orig,
                "label": ent.get("label", ""),
                "type": ent.get("type", ""),
                "first_index": idx,
                "context": ctx,
            }
        )
    return leaks


BRUTE_PII_PATTERNS = [
    (r"\d{6}/\d{3,4}", "RC"),
    (r"\+420\s?\d{3}\s?\d{3}\s?\d{3}", "PHONE_CZ"),
    (r"\b\d{3}\s?\d{3}\s?\d{3}\b", "PHONE9"),
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "EMAIL"),
    (r"CZ\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}", "IBAN"),
    (r"(?<![A-Za-z0-9])\d[A-Z]{1,2}\d\s?\d{4}(?![A-Za-z0-9])", "SPZ"),
    (r"(?<![A-Za-z0-9])[A-HJ-NPR-Z0-9]{17}(?![A-Za-z0-9])", "VIN"),
    # město + PSČ (adresní pattern)
    (
        r"\b[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž\-]{2,}"
        r"(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž\-]{2,})*"
        r"\s+\d{3}\s?\d{2}\b",
        "CITY_PSC",
    ),
]


def find_regex_pii(anon_text: str) -> List[Dict]:
    """Hrubé regex hledání PII – bez jakéhokoli filtrování."""
    hits: List[Dict] = []
    for pattern, label in BRUTE_PII_PATTERNS:
        for m in re.finditer(pattern, anon_text):
            start, end = m.span()
            ctx = anon_text[max(0, start - 40) : end + 40].replace("\n", " ")
            hits.append(
                {
                    "type": label,
                    "match": m.group(0),
                    "start": start,
                    "context": ctx,
                }
            )
    return hits


def audit_single(docx_path: Path) -> Dict:
    base = docx_path.stem
    anon_docx = OUT_DIR / f"{base}_anon.docx"
    map_json = OUT_DIR / f"{base}_map.json"

    result: Dict = {"file": docx_path.name}

    if not anon_docx.exists():
        result["error"] = f"anon DOCX neexistuje: {anon_docx}"
        return result
    if not map_json.exists():
        result["error"] = f"map JSON neexistuje: {map_json}"
        return result

    anon_text = get_all_text_from_docx(anon_docx)
    entities = load_map_entities(map_json)

    map_leaks = find_originals_in_anon(anon_text, entities)
    regex_hits = find_regex_pii(anon_text)

    result["map_leaks"] = map_leaks
    result["regex_hits"] = regex_hits
    result["stats"] = {
        "entities_total": len(entities),
        "map_leak_count": len(map_leaks),
        "regex_hit_count": len(regex_hits),
    }
    result["verdict"] = "FAIL" if (map_leaks or regex_hits) else "PASS"
    return result


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Brute-force audit anon výstupů proti mapám (bez ignore seznamů)"
    )
    ap.add_argument("--min", type=int, default=None, help="Jen smlouvy od čísla")
    ap.add_argument("--max", type=int, default=None, help="Jen smlouvy do čísla")
    args = ap.parse_args()

    docx_files = sorted(
        f
        for f in TEST_DATA.glob("smlouva*.docx")
        if not f.name.startswith("~$")
        and "_anon" not in f.name
        and "_deanon" not in f.name
    )

    if args.min is not None or args.max is not None:
        filtered = []
        for f in docx_files:
            m = re.search(r"(\d+)", f.stem)
            if not m:
                continue
            n = int(m.group(1))
            if args.min is not None and n < args.min:
                continue
            if args.max is not None and n > args.max:
                continue
            filtered.append(f)
        docx_files = filtered

    if not docx_files:
        print("[CHYBA] Žádné smlouva*.docx v test_data")
        return 1

    print(f"[BRUTE AUDIT] Smluv: {len(docx_files)} (bez ignore, čisté hledání)")
    print("=" * 72)

    all_results: List[Dict] = []
    total_map_leaks = 0
    total_regex = 0

    for i, docx_path in enumerate(docx_files, 1):
        r = audit_single(docx_path)
        all_results.append(r)

        stats = r.get("stats", {})
        ml = stats.get("map_leak_count", 0)
        rg = stats.get("regex_hit_count", 0)
        total_map_leaks += ml
        total_regex += rg

        flag_parts = []
        if ml:
            flag_parts.append(f"MAP:{ml}")
        if rg:
            flag_parts.append(f"REGEX:{rg}")
        flag_str = f" [{', '.join(flag_parts)}]" if flag_parts else ""

        print(f"  [{i}/{len(docx_files)}] {docx_path.name}: {r.get('verdict', '?')}{flag_str}")

        # Vypiš pár detailů, pokud něco našel
        if ml:
            for leak in r["map_leaks"][:3]:
                print(
                    f"      MAP '{leak['original']}' ({leak.get('type')}) "
                    f"ctx: ...{leak['context'][:80]}..."
                )
        if rg:
            for hit in r["regex_hits"][:3]:
                print(
                    f"      REGEX {hit['type']}: '{hit['match']}' "
                    f"ctx: ...{hit['context'][:80]}..."
                )

    print("=" * 72)
    print("[SOUHRN]")
    print(f"  Celkem smluv:     {len(all_results)}")
    print(f"  PASS:             {sum(1 for r in all_results if r.get('verdict') == 'PASS')}")
    print(f"  FAIL:             {sum(1 for r in all_results if r.get('verdict') == 'FAIL')}")
    print(f"  Map leaks celkem: {total_map_leaks}")
    print(f"  Regex hits celkem:{total_regex}")

    out_dir = TEST_DATA.parent / "_agent_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "bruteforce_audit.json"
    out_json.write_text(
        json.dumps(
            {
                "results": all_results,
                "summary": {
                    "total": len(all_results),
                    "pass": sum(1 for r in all_results if r.get("verdict") == "PASS"),
                    "fail": sum(1 for r in all_results if r.get("verdict") == "FAIL"),
                    "map_leaks": total_map_leaks,
                    "regex_hits": total_regex,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[INFO] Detailní JSON report: {out_json}")

    return 0 if total_map_leaks == 0 and total_regex == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

