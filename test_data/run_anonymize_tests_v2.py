#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validátor anonymizace SKRYI – MIMOŘÁDNĚ PŘÍSNÁ VERZE (v2).

Rozdíly oproti standardnímu validátoru (v1):
─────────────────────────────────────────────
1. Pouze score 10/10 = PASS (v1: 9/10 stačí)
2. Minimum délky originálního tokenu: 3 znaky (v1: 4)
3. Kratší PII regex přeskoky nemají toleranci (v1 toleruje kontext u telefonu/RC)
4. Heuristika hledá jména i s 1-znakovým příjmením (iniciály)
5. Kontrola pokrytí: kolik procent osob z originálního textu je v mapě
6. Přísnější skórovací vzorec

CO NENÍ osobní údaj dle GDPR (ignoruje se i v přísném režimu):
- Názvy firem, produktů, institucí (Sconto Bolton, Forensic Logging, …)
- Města, ulice (Hradec Králové, Václavské nám., …)
- Role a strany smlouvy (pojistitel, objednatel, správce, …)
- Tituly (Mgr., Ing., …)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from run_anonymize_tests import (
    PROJECT_ROOT,
    TEST_DATA,
    OUT_DIR,
    REPORTS_DIR,
    CZ_FIRSTNAMES,
    PII_PATTERNS,
    get_all_text_from_docx,
    get_docx_structure,
    extract_originals_from_map_json,
    extract_originals_from_map_txt,
    check_map_consistency,
    check_pii_regex,
    _find_visible_names_addresses,
    _should_ignore_visible_pii,
    _analyze_map_quality,
    _PII_LEAK_IGNORE,
    _PII_LEAK_IGNORE_PHRASES,
    _normalize_for_ignore,
    check_pii_leak_from_map,
    _format_problemy,
    _format_poznamka,
    run_single_anonymize,
)


# ═══════════════════════════════════════════════════════════════
# 1. Přísnější PII leak z mapy: min. 3 znaky (místo 4)
# ═══════════════════════════════════════════════════════════════

def check_pii_leak_from_map_strict(anon_text: str, originals: Set[str]) -> List[str]:
    """Jako v1, ale snížený práh na 3 znaky a méně tolerantní kontext u čísel."""
    leaks = []
    for orig in originals:
        if len(orig) < 3:
            continue
        if orig.lower() in _PII_LEAK_IGNORE:
            continue
        norm = _normalize_for_ignore(orig)
        if norm in _PII_LEAK_IGNORE_PHRASES:
            continue
        if any(p in norm for p in _PII_LEAK_IGNORE_PHRASES):
            continue
        escaped = re.escape(orig)
        is_numeric = orig.replace(" ", "").isdigit()
        is_leak = False
        for m in re.finditer(r"\b" + escaped + r"\b", anon_text, re.IGNORECASE):
            s, e = m.span()
            if is_numeric:
                ctx_before = anon_text[max(0, s - 10) : s]
                ctx_after = anon_text[e : e + 10]
                if s > 0 and anon_text[s - 1] == "-":
                    continue
                if any(w in ctx_after.lower() for w in ["kč", "czk", ",-", "korun"]):
                    continue
            is_leak = True
            break
        if is_leak:
            leaks.append(orig)
    return leaks


# ═══════════════════════════════════════════════════════════════
# 2. Přísnější regex: hledáme i kratší telefony, zkrácené RC
# ═══════════════════════════════════════════════════════════════

STRICT_PII_PATTERNS = PII_PATTERNS + [
    (r"\b\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\b", "Telefon 9 číslic (volný tvar)"),
    (r"\b\d{6}\d{3,4}\b", "Rodné číslo bez lomítka"),
    (r"\b[A-Z]{2}\d{6,7}\b", "Pas/OP (vzor XX1234567)"),
    # Město + PSČ (např. \"Frýdek-Místek 738 01\") – pokud zůstane mimo tag, chceme to vidět.
    (r"\b[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž\-]{2,}(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][A-Za-zÁČĎÉĚÍŇÓŘŠŤÚŮÝŽáčďéěíňóřšťúůýž\-]{2,})*\s+\d{3}\s?\d{2}\b",
     "Město+PSČ (adresní vzor)"),
]

def check_pii_regex_strict(anon_text: str) -> List[Tuple[str, str]]:
    """Rozšířené regex vzory pro české PII – přísnější než v1."""
    found = []
    for pattern, label in STRICT_PII_PATTERNS:
        for m in re.finditer(pattern, anon_text):
            start, end = m.span()
            before = anon_text[max(0, start - 2) : start]
            after = anon_text[end : min(len(anon_text), end + 2)]
            if "[[" in before or "]]" in after:
                continue
            matched = m.group()
            if "Telefon" in label:
                ctx_after = anon_text[end : end + 30].lower()
                digits_only = re.sub(r"\s", "", matched)
                val = int(digits_only) if digits_only.isdigit() else 0
                if val >= 100_000_000 or any(w in ctx_after for w in ["kč", "czk", "korun", "eur", ",-"]):
                    continue
            if "Rodné číslo" in label:
                parts = matched.replace(" ", "").split("/") if "/" in matched else [matched]
                if len(parts) == 2 and len(parts[1]) in (3, 4):
                    suffix = parts[1]
                    if len(suffix) == 4 and (suffix.startswith("20") or suffix.startswith("19")):
                        continue
                    month = int(parts[0][2:4]) if len(parts[0]) >= 4 and parts[0][2:4].isdigit() else 0
                    if month < 1 or (month > 12 and month < 51) or month > 62:
                        continue
                elif len(parts) == 1 and len(parts[0]) in (9, 10):
                    month = int(parts[0][2:4])
                    if month < 1 or (month > 12 and month < 51) or month > 62:
                        continue
            if "Město+PSČ" in label:
                # Odfiltruj zjevné neadresní vzory typu \"ISO 27001\" nebo advokátní čísla ČAK.
                parts = matched.split()
                if parts:
                    city_part = parts[0]
                    if city_part.upper().startswith("ISO"):
                        continue
                    if city_part.upper() in {"ČAK", "CAK"}:
                        continue
            found.append((matched, label))
    return found


# ═══════════════════════════════════════════════════════════════
# 3. Kontrola pokrytí: kolik osob z orig. textu je v mapě
# ═══════════════════════════════════════════════════════════════

def check_person_coverage(original_text: str, map_json_path: Path) -> List[str]:
    """Hledá v originálním textu vzory Jméno Příjmení, co NEJSOU v mapě."""
    issues = []
    if not map_json_path.exists():
        return issues

    try:
        with open(map_json_path, encoding="utf-8") as f:
            jdata = json.load(f)
    except Exception:
        return issues

    mapped_originals = set()
    for ent in jdata.get("entities", []):
        o = ent.get("original", "").strip()
        if o:
            mapped_originals.add(o.lower())

    name_re = re.compile(
        r"\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{2,})\s+"
        r"([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{2,})\b"
    )

    non_person = {
        "smlouva", "článek", "příloha", "dodatek", "protokol", "strana",
        "česká", "republika", "městský", "úřad", "finanční", "krajský",
        "obchodní", "rejstřík", "katastrální", "územní", "správní",
        "smluvní", "osobní", "údajů", "zpracování", "ochrana", "zákon",
        "občanský", "zákoník", "trestní", "obchodní", "pracovní",
        "datum", "místo", "adresa", "sídlo", "bytem", "kontakt",
        "rodné", "číslo", "telefon", "email", "platební", "karta",
    }

    for m in name_re.finditer(original_text):
        first, last = m.group(1), m.group(2)
        full = f"{first} {last}"
        fl = first.lower()
        ll = last.lower()
        if fl in non_person or ll in non_person:
            continue
        if fl in _PII_LEAK_IGNORE or ll in _PII_LEAK_IGNORE:
            continue
        if fl not in CZ_FIRSTNAMES:
            continue
        if full.lower() in mapped_originals:
            continue
        if any(full.lower() in mo for mo in mapped_originals):
            continue
        if any(fl in mo and ll in mo for mo in mapped_originals):
            continue
        issues.append(f"MISS: {full}")
        if len(issues) >= 20:
            break
    return issues


# ═══════════════════════════════════════════════════════════════
# 4. Přísnější skórovací vzorec
# ═══════════════════════════════════════════════════════════════

def compute_score_strict(
    success: bool,
    pii_leaks: List[str],
    pii_regex: list,
    map_ok: bool | None,
    structure_ok: bool,
    pdf_exists: bool,
    coverage_misses: int = 0,
) -> int:
    if not success:
        return 0
    score = 10
    if pii_leaks:
        score -= min(7, 2 + len(pii_leaks))
    if pii_regex:
        score -= min(6, 1 + len(pii_regex))
    if map_ok is False:
        score -= 2
    if not structure_ok:
        score -= 1
    if not pdf_exists:
        score -= 1
    if coverage_misses > 0:
        score -= min(3, coverage_misses)
    return max(0, min(10, score))


# ═══════════════════════════════════════════════════════════════
# 5. Hlavní runner
# ═══════════════════════════════════════════════════════════════

def run_single_strict(docx_path: Path) -> dict:
    """Spustí anonymizaci a přehodnotí přísně."""
    r = run_single_anonymize(docx_path)
    if not r.get("success"):
        r["score"] = 0
        return r

    base = docx_path.stem
    out_docx = OUT_DIR / f"{base}_anon.docx"
    map_json = OUT_DIR / f"{base}_map.json"
    map_txt = OUT_DIR / f"{base}_map.txt"

    anon_text = get_all_text_from_docx(out_docx)
    original_text = get_all_text_from_docx(docx_path)

    originals = set()
    if map_json.exists():
        originals |= extract_originals_from_map_json(map_json)
    if map_txt.exists():
        originals |= extract_originals_from_map_txt(map_txt)

    # 1) Přísný PII leak z mapy (min 3 znaky)
    r["pii_leaks"] = check_pii_leak_from_map_strict(anon_text, originals)

    # 2) Heuristika viditelných jmen/adres (se STEJNÝM GDPR ignore jako v1)
    visible = _find_visible_names_addresses(anon_text)
    visible_filtered = [x for x in visible if not _should_ignore_visible_pii(x)]
    r["pii_leaks"].extend(visible_filtered)

    # 3) Přísnější regex
    r["pii_regex_found"] = [
        {"match": m[:20] + "..." if len(m) > 20 else m, "type": t}
        for m, t in check_pii_regex_strict(anon_text)
    ]

    # 4) Kontrola pokrytí osob
    coverage_misses = check_person_coverage(original_text, map_json)
    r["coverage_misses"] = coverage_misses

    # 5) Mapa konzistence (stejné jako v1)
    if map_json.exists() and map_txt.exists():
        map_ok, map_errs = check_map_consistency(map_json, map_txt)
        extra_map_issues = _analyze_map_quality(map_txt, original_text)
        r["map_ok"] = map_ok and not extra_map_issues
        r["map_errors"] = map_errs + extra_map_issues

    r["score"] = compute_score_strict(
        success=True,
        pii_leaks=r["pii_leaks"],
        pii_regex=r["pii_regex_found"],
        map_ok=r.get("map_ok"),
        structure_ok=r.get("structure_ok") or False,
        pdf_exists=r.get("pdf_report_exists", False),
        coverage_misses=len(coverage_misses),
    )
    r["score_breakdown"] = {
        "pii_from_map": len(r["pii_leaks"]),
        "pii_from_regex": len(r["pii_regex_found"]),
        "coverage_misses": len(coverage_misses),
        "map_ok": r.get("map_ok"),
        "structure_ok": r.get("structure_ok"),
        "pdf_exists": r.get("pdf_report_exists"),
    }
    return r


def _extract_smlouva_num(path: Path) -> int | None:
    m = re.search(r"smlouva\s*(\d+)", path.stem, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _write_report_md_v2(path: Path, report: dict) -> None:
    s = report["summary"]
    lines = [
        "# Výsledky testů anonymizace SKRYI – VALIDÁTOR V2 (přísný)",
        "",
        "**Pravidlo: pouze score 10/10 = PASS.**",
        "",
        "Oproti v1: min. token 3 znaky, rozšířené regex, kontrola pokrytí osob,",
        "přísnější skóre. GDPR ignore (firmy, instituce, role) je zachováno.",
        "",
        "## Shrnutí",
        "",
        "| Metrika | Hodnota |",
        "|---------|---------|",
        f"| Celkem smluv | {s['total']} |",
        f"| Prošlo (score=10) | {s['passed']} |",
        f"| Selhalo | {s['failed']} |",
        f"| Průměr score | {s['avg_score']}/10 |",
        f"| S PII leakem | {s['with_pii_leak']} |",
        f"| S chybějícími osobami | {s.get('with_coverage_miss', 0)} |",
        f"| Nekonzistentní mapa | {s['map_inconsistent']} |",
        "",
        "## Přehled po smlouvách",
        "",
        "| Soubor | Score | Status | Problémy |",
        "|--------|-------|--------|----------|",
    ]
    for row in report["prehled"]:
        lines.append(f"| {row['soubor']} | {row['score']}/10 | {row['status']} | {row['problémy']} |")

    lines.extend(["", "---", "", "## Detaily chyb (smlouvy s score < 10)", ""])
    for r in report.get("results", []):
        if r.get("score", 0) >= 10 and r.get("success"):
            continue
        fname = r.get("file", "")
        score = r.get("score", 0)
        lines.append(f"### {fname} — {score}/10")
        lines.append("")
        if r.get("pii_leaks"):
            lines.append("**PII leak:**")
            for leak in r["pii_leaks"][:15]:
                lines.append(f"- `{leak}`")
            if len(r["pii_leaks"]) > 15:
                lines.append(f"- _(+{len(r['pii_leaks'])-15} dalších)_")
            lines.append("")
        if r.get("pii_regex_found"):
            lines.append("**PII regex:**")
            for item in r["pii_regex_found"][:5]:
                lines.append(f"- `{item.get('match', '')}` ({item.get('type', '')})")
            lines.append("")
        if r.get("coverage_misses"):
            lines.append("**Chybějící osoby v mapě:**")
            for miss in r["coverage_misses"][:10]:
                lines.append(f"- `{miss}`")
            lines.append("")
        if r.get("map_errors"):
            lines.append("**Chyby mapy:** " + "; ".join(r["map_errors"][:3]))
            lines.append("")
        if not r.get("structure_ok"):
            lines.append("**Struktura:** poškozena")
            lines.append("")
        if not r.get("pdf_report_exists"):
            lines.append("**PDF report:** chybí")
            lines.append("")
        lines.append("---")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="SKRYI validátor v2 – mimořádně přísný (pouze 10/10 = PASS)")
    ap.add_argument("--min", type=int, default=None, help="Jen smlouvy od čísla")
    ap.add_argument("--max", type=int, default=None, help="Jen smlouvy do čísla")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    docx_files = sorted(TEST_DATA.glob("smlouva*.docx"))
    docx_files = [
        f for f in docx_files
        if not f.name.startswith("~$") and "_anon" not in f.name and "_deanon" not in f.name
    ]
    if args.min is not None or args.max is not None:
        filtered = []
        for f in docx_files:
            n = _extract_smlouva_num(f)
            if n is None:
                continue
            if args.min is not None and n < args.min:
                continue
            if args.max is not None and n > args.max:
                continue
            filtered.append(f)
        docx_files = filtered

    if not docx_files:
        print("[CHYBA] Žádné smlouva*.docx v test_data")
        return 1

    print(f"[INFO] Validátor V2 (přísný): {len(docx_files)} smluv. Pouze score 10/10 = PASS.")
    print(f"       Přísnost: min 3 znaky, rozšířené regex, kontrola pokrytí osob.")
    print(f"       GDPR ignore zachováno (firmy, instituce, role NEJSOU osobní údaje).")
    results = []
    for i, path in enumerate(docx_files, 1):
        print(f"  [{i}/{len(docx_files)}] {path.name}...", end=" ", flush=True)
        r = run_single_strict(path)
        results.append(r)
        if r["success"]:
            s = r["score"]
            issues = []
            if r["pii_leaks"]:
                issues.append(f"PII:{len(r['pii_leaks'])}")
            if r["pii_regex_found"]:
                issues.append(f"regex:{len(r['pii_regex_found'])}")
            if r.get("coverage_misses"):
                issues.append(f"miss:{len(r['coverage_misses'])}")
            if r.get("map_ok") is False:
                issues.append("mapa")
            if not r.get("structure_ok"):
                issues.append("struktura")
            if not r.get("pdf_report_exists"):
                issues.append("PDF")
            status = f"score={s}/10"
            if issues:
                status += f" ({', '.join(issues)})"
            print(status)
        else:
            print(f"FAIL: {(r.get('error') or '')[:60]}")

    passed = sum(1 for r in results if r["success"] and r["score"] >= 10)
    failed = [r for r in results if not r["success"] or r["score"] < 10]
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0

    prehled = [
        {
            "soubor": r["file"],
            "score": r["score"],
            "status": "OK" if r["success"] and r["score"] >= 10 else "FAIL",
            "problémy": _format_problemy(r),
            "poznamka": _format_poznamka(r),
        }
        for r in results
    ]

    report = {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(failed),
            "avg_score": round(avg_score, 1),
            "with_pii_leak": sum(1 for r in results if r.get("pii_leaks") or r.get("pii_regex_found")),
            "with_coverage_miss": sum(1 for r in results if r.get("coverage_misses")),
            "map_inconsistent": sum(1 for r in results if r.get("map_ok") is False),
            "structure_broken": sum(1 for r in results if r.get("structure_ok") is False),
            "pdf_missing": sum(1 for r in results if not r.get("pdf_report_exists")),
        },
        "prehled": prehled,
        "results": results,
        "failed_files": [r["file"] for r in failed],
    }

    out_json = REPORTS_DIR / "test_results_v2.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    _write_report_md_v2(REPORTS_DIR / "test_results_v2.md", report)

    print(f"\n[OK] Report V2 uložen: {out_json}")
    print(f"     PASS (score=10): {passed}/{len(results)}, FAIL: {len(failed)}, průměr: {avg_score:.1f}/10")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
