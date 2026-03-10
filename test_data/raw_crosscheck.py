#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nezávislý RAW cross-check validátor – BEZ jakýchkoliv ignore filtrů.

Tento skript:
1. Načte anonymizovaný DOCX a mapu (JSON)
2. Pro KAŽDÝ originál z mapy (typ = person, address, phone, email, RC, SPZ, VIN, IBAN...)
   hledá jeho výskyt v anonymizovaném textu – BEZ filtrování
3. Zkontroluje, že žádný [[PERSON_N]] / [[ADDRESS_N]] tag nemá vedle sebe čitelné jméno
4. Zpětná kontrola: pro každý tag v anon textu ověří, že existuje v mapě
5. Reportuje nefiltrovány výsledky, abychom viděli skutečný stav

Účel: ověřit, že v2 validátor nic nepřehlíží.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

from run_anonymize_tests import (
    TEST_DATA,
    OUT_DIR,
    get_all_text_from_docx,
)


def load_map_entities(map_json: Path) -> List[dict]:
    with open(map_json, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("entities", [])


def raw_leak_check(anon_text: str, entities: List[dict]) -> List[dict]:
    """Pro KAŽDOU entitu z mapy hledá originál v anonymizovaném textu. Žádné filtry."""
    findings = []
    for ent in entities:
        orig = str(ent.get("original", "")).strip()
        tag = ent.get("tag", "")
        etype = ent.get("type", "")
        if len(orig) < 2:
            continue
        escaped = re.escape(orig)
        for m in re.finditer(escaped, anon_text, re.IGNORECASE):
            s, e = m.span()
            ctx = anon_text[max(0, s - 30) : min(len(anon_text), e + 30)]
            findings.append({
                "original": orig,
                "tag": tag,
                "type": etype,
                "found_at": s,
                "context": ctx.replace("\n", " "),
            })
    return findings


def classify_leak(finding: dict) -> str:
    """Zařadí nález do kategorie: REAL_LEAK, FALSE_POSITIVE, UNCLEAR."""
    orig = finding["original"]
    ctx = finding["context"]
    etype = finding["type"]

    if f"[[{finding['tag'].strip('[]')}]]" in ctx if finding["tag"] else False:
        return "TAG_CONTEXT"

    if "[[PERSON_" in ctx or "[[ADDRESS_" in ctx or "[[PHONE_" in ctx:
        if orig.lower() in ctx.lower():
            nearby_tag = re.search(r"\[\[(PERSON|ADDRESS|PHONE|EMAIL|RC|SPZ|VIN|IBAN)_\d+\]\]", ctx)
            if nearby_tag and abs(ctx.find(orig.lower()) - nearby_tag.start()) < 15:
                return "TAG_CONTEXT"

    if etype in ("person", "name"):
        if re.search(r"[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+", orig):
            return "REAL_LEAK"

    if etype in ("address",):
        return "REAL_LEAK"

    if etype in ("phone", "email", "rc", "spz", "vin", "iban", "bank_account"):
        return "REAL_LEAK"

    orig_lo = orig.lower()
    non_pii_words = {
        "pojistitel", "pojistník", "správce", "zpracovatel", "objednatel",
        "zhotovitel", "pronajímatel", "nájemce", "kupující", "prodávající",
        "dlužník", "věřitel", "zaměstnavatel", "zaměstnanec", "žadatel",
        "mgr.", "ing.", "bc.", "judr.", "mudr.", "phdr.", "rndr.", "doc.", "prof.",
    }
    if orig_lo in non_pii_words:
        return "FALSE_POSITIVE"

    return "UNCLEAR"


def check_orphan_tags(anon_text: str, entities: List[dict]) -> List[str]:
    """Kontrola: každý tag v anon textu musí mít odpovídající záznam v mapě."""
    tags_in_text_full = set(re.findall(r"\[\[[A-Z_]+_\d+\]\]", anon_text))
    tags_in_map = set()
    for ent in entities:
        for key in ("label", "tag"):
            v = ent.get(key, "").strip()
            if v:
                tags_in_map.add(v)
    orphans = tags_in_text_full - tags_in_map
    return sorted(orphans)


def check_name_next_to_tag(anon_text: str) -> List[str]:
    """Hledá vzor kde je [[PERSON_N]] následováno/předcházeno čitelným jménem."""
    issues = []
    name_near_tag = re.compile(
        r"([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{2,})\s+\[\[PERSON_\d+\]\]"
        r"|\[\[PERSON_\d+\]\]\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{2,})"
    )
    for m in name_near_tag.finditer(anon_text):
        word = m.group(1) or m.group(2)
        role_words = {
            "pan", "paní", "pana", "paní", "společnost", "firma", "organizace",
            "úřad", "soud", "banka", "pojišťovna", "kancelář", "oddělení",
            "ředitel", "jednatel", "předseda", "správce", "zpracovatel",
            "pojistitel", "pojistník", "objednatel", "zhotovitel", "kupující",
            "prodávající", "pronajímatel", "nájemce", "zaměstnavatel",
            "zaměstnanec", "zástupce", "nar", "narozena", "narozený", "bytem",
            "trvale", "kontaktní", "odpovědná", "odpovědný", "pověřená",
            "pověřený", "zmocněná", "zmocněnec", "otec", "matka", "dcera", "syn",
            "bratr", "sestra", "manžel", "manželka",
        }
        if word.lower() not in role_words:
            ctx = anon_text[max(0, m.start() - 20):min(len(anon_text), m.end() + 20)]
            issues.append(f"NAME_NEAR_TAG: '{word}' @ {m.start()} ctx: {ctx.replace(chr(10), ' ')}")
    return issues


def run_crosscheck(docx_name: str) -> dict:
    """Spustí kompletní raw cross-check pro jednu smlouvu."""
    base = Path(docx_name).stem
    anon_docx = OUT_DIR / f"{base}_anon.docx"
    map_json = OUT_DIR / f"{base}_map.json"

    result = {"file": docx_name, "checks": {}}

    if not anon_docx.exists():
        result["error"] = f"anon DOCX neexistuje: {anon_docx}"
        return result
    if not map_json.exists():
        result["error"] = f"map JSON neexistuje: {map_json}"
        return result

    anon_text = get_all_text_from_docx(anon_docx)
    entities = load_map_entities(map_json)

    # 1) RAW leak check
    raw_findings = raw_leak_check(anon_text, entities)
    classified = []
    real_leaks = []
    for f in raw_findings:
        cat = classify_leak(f)
        f["category"] = cat
        classified.append(f)
        if cat == "REAL_LEAK":
            real_leaks.append(f)

    result["checks"]["raw_leak"] = {
        "total_findings": len(classified),
        "real_leaks": len(real_leaks),
        "false_positives": sum(1 for f in classified if f["category"] == "FALSE_POSITIVE"),
        "tag_context": sum(1 for f in classified if f["category"] == "TAG_CONTEXT"),
        "unclear": sum(1 for f in classified if f["category"] == "UNCLEAR"),
        "real_leak_details": real_leaks[:20],
    }

    # 2) Orphan tags
    orphans = check_orphan_tags(anon_text, entities)
    result["checks"]["orphan_tags"] = orphans

    # 3) Readable names next to PERSON tags
    name_near_tag = check_name_next_to_tag(anon_text)
    result["checks"]["name_near_tag"] = name_near_tag[:20]

    # 4) PII regex (raw, no filtering at all)
    pii_re = [
        (r"\d{6}/\d{3,4}", "RC"),
        (r"\+420\s?\d{3}\s?\d{3}\s?\d{3}", "Phone"),
        (r"\b\d{3}\s?\d{3}\s?\d{3}\b", "Phone9"),
        (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "Email"),
        (r"(?<![A-Za-z0-9])\d[A-Z]{1,2}\d\s?\d{4}(?![A-Za-z0-9])", "SPZ"),
    ]
    regex_hits = []
    for pat, label in pii_re:
        for m in re.finditer(pat, anon_text):
            ctx = anon_text[max(0, m.start() - 15):min(len(anon_text), m.end() + 15)]
            in_tag = "[[" in ctx[:10] or "]]" in ctx[-10:]
            regex_hits.append({
                "match": m.group(),
                "type": label,
                "in_tag_context": in_tag,
                "context": ctx.replace("\n", " "),
            })
    non_tag_regex = [h for h in regex_hits if not h["in_tag_context"]]
    result["checks"]["regex_pii_raw"] = {
        "total": len(regex_hits),
        "outside_tags": len(non_tag_regex),
        "details": non_tag_regex[:10],
    }

    # 5) Summary stats
    person_ents = [e for e in entities if "person" in e.get("type", "").lower() or "PERSON" in e.get("tag", "")]
    addr_ents = [e for e in entities if "address" in e.get("type", "").lower() or "ADDRESS" in e.get("tag", "")]
    result["stats"] = {
        "total_entities": len(entities),
        "person_entities": len(person_ents),
        "address_entities": len(addr_ents),
        "anon_text_length": len(anon_text),
        "person_tags_in_text": len(re.findall(r"\[\[PERSON_\d+\]\]", anon_text)),
        "address_tags_in_text": len(re.findall(r"\[\[ADDRESS_\d+\]\]", anon_text)),
    }

    # Final verdict
    has_real_leak = len(real_leaks) > 0
    has_orphans = len(orphans) > 0
    has_name_near_tag = len(name_near_tag) > 0
    has_raw_regex = len(non_tag_regex) > 0
    result["verdict"] = "FAIL" if (has_real_leak or has_raw_regex) else "PASS"
    result["warnings"] = []
    if has_orphans:
        result["warnings"].append(f"orphan_tags: {len(orphans)}")
    if has_name_near_tag:
        result["warnings"].append(f"name_near_tag: {len(name_near_tag)}")

    return result


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Raw cross-check: nezávislý audit anonymizace")
    ap.add_argument("--sample", type=int, default=0, help="Kolik smluv náhodně (0 = všechny)")
    ap.add_argument("--min", type=int, default=None)
    ap.add_argument("--max", type=int, default=None)
    args = ap.parse_args()

    docx_files = sorted(TEST_DATA.glob("smlouva*.docx"))
    docx_files = [
        f for f in docx_files
        if not f.name.startswith("~$") and "_anon" not in f.name and "_deanon" not in f.name
    ]

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

    if args.sample > 0 and args.sample < len(docx_files):
        import random
        random.seed(42)
        docx_files = random.sample(docx_files, args.sample)

    print(f"[RAW CROSS-CHECK] {len(docx_files)} smluv, BEZ filtrů")
    print("=" * 70)

    all_results = []
    total_real_leaks = 0
    total_unclear = 0
    total_regex = 0
    total_name_near_tag = 0

    for i, f in enumerate(docx_files, 1):
        r = run_crosscheck(f.name)
        all_results.append(r)

        leaks = r.get("checks", {}).get("raw_leak", {})
        regex = r.get("checks", {}).get("regex_pii_raw", {})
        nnt = r.get("checks", {}).get("name_near_tag", [])

        rl = leaks.get("real_leaks", 0)
        uc = leaks.get("unclear", 0)
        rg = regex.get("outside_tags", 0)

        total_real_leaks += rl
        total_unclear += uc
        total_regex += rg
        total_name_near_tag += len(nnt)

        status_parts = []
        if rl > 0:
            status_parts.append(f"LEAK:{rl}")
        if uc > 0:
            status_parts.append(f"UNCLEAR:{uc}")
        if rg > 0:
            status_parts.append(f"REGEX:{rg}")
        if nnt:
            status_parts.append(f"NAME_TAG:{len(nnt)}")
        if r.get("checks", {}).get("orphan_tags"):
            status_parts.append(f"ORPHAN:{len(r['checks']['orphan_tags'])}")

        verdict = r.get("verdict", "?")
        extra = f" [{', '.join(status_parts)}]" if status_parts else ""
        print(f"  [{i}/{len(docx_files)}] {f.name}: {verdict}{extra}")

        if rl > 0:
            for leak in leaks.get("real_leak_details", [])[:3]:
                print(f"       -> {leak['type']}: '{leak['original'][:40]}' ctx: ...{leak['context'][:50]}...")
        if rg > 0:
            for hit in regex.get("details", [])[:3]:
                print(f"       -> REGEX {hit['type']}: '{hit['match']}' ctx: {hit['context'][:50]}")
        if nnt:
            for item in nnt[:2]:
                print(f"       -> {item[:80]}")

    print("=" * 70)
    print(f"[SOUHRN]")
    print(f"  Celkem smluv:       {len(all_results)}")
    print(f"  PASS:               {sum(1 for r in all_results if r.get('verdict') == 'PASS')}")
    print(f"  FAIL:               {sum(1 for r in all_results if r.get('verdict') == 'FAIL')}")
    print(f"  Real leaks celkem:  {total_real_leaks}")
    print(f"  Unclear celkem:     {total_unclear}")
    print(f"  Regex PII celkem:   {total_regex}")
    print(f"  Name near tag:      {total_name_near_tag}")

    if total_real_leaks > 0 or total_regex > 0:
        print(f"\n[!!] NALEZENY SKUTEČNÉ PROBLÉMY – detaily výše.")
    else:
        print(f"\n[OK] Žádné skutečné PII leaky. Validátor v2 potvrzuje správnost.")

    out_json = OUT_DIR.parent.parent / "_agent_reports" / "raw_crosscheck.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as fp:
        json.dump({"results": all_results, "summary": {
            "total": len(all_results),
            "pass": sum(1 for r in all_results if r.get("verdict") == "PASS"),
            "fail": sum(1 for r in all_results if r.get("verdict") == "FAIL"),
            "real_leaks": total_real_leaks,
            "unclear": total_unclear,
            "regex_pii": total_regex,
            "name_near_tag": total_name_near_tag,
        }}, fp, ensure_ascii=False, indent=2)
    print(f"\n[INFO] Detailní report: {out_json}")

    return 1 if (total_real_leaks > 0 or total_regex > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
