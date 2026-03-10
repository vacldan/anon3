#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ruční audit všech 185 smluv - smlouva po smlouvě.
Pro každou smlouvu: načte anon text + mapu, hledá originály z mapy v textu.
Vypíše každý nález s kontextem. Žádné filtry.
"""
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent / "anon_output"
INPUT_DIR = Path(__file__).parent

def get_all_text_from_docx(docx_path):
    from docx import Document
    doc = Document(str(docx_path))
    parts = []
    for p in doc.paragraphs:
        parts.append(p.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    parts.append(p.text)
    return "\n".join(parts)

def is_inside_tag(text, pos):
    """Check if position is inside [[...]] tag."""
    before = text[:pos]
    open_count = before.count("[[") - before.count("]]")
    return open_count > 0

def audit_one(base_name):
    anon_docx = OUT_DIR / f"{base_name}_anon.docx"
    map_json = OUT_DIR / f"{base_name}_map.json"
    if not anon_docx.exists() or not map_json.exists():
        return None, "MISSING_FILES"

    text = get_all_text_from_docx(anon_docx)
    data = json.loads(map_json.read_text(encoding="utf-8"))
    entities = data.get("entities", [])

    leaks = []
    for ent in entities:
        orig = str(ent.get("original", "")).strip()
        etype = ent.get("type", "")
        tag = ent.get("tag", "")
        if len(orig) < 2:
            continue

        for m in re.finditer(re.escape(orig), text, re.IGNORECASE):
            if is_inside_tag(text, m.start()):
                continue
            ctx = text[max(0, m.start() - 50) : min(len(text), m.end() + 50)].replace("\n", " ")
            leaks.append({
                "type": etype,
                "original": orig,
                "tag": tag,
                "context": ctx,
            })

    return leaks, text

def main():
    docx_files = sorted(
        [f for f in INPUT_DIR.glob("*.docx") if "_anon" not in f.stem and "_deanon" not in f.stem],
        key=lambda p: p.name,
    )
    # Filter out temp files
    docx_files = [f for f in docx_files if not f.name.startswith("~$")]

    report = []
    for i, f in enumerate(docx_files, 1):
        base = f.stem
        leaks, text = audit_one(base)
        if leaks is None:
            report.append((i, base, "MISSING", []))
            continue

        report.append((i, base, "OK" if not leaks else "LEAKS", leaks))

    # Output
    print("=" * 80)
    print("RUČNÍ AUDIT: 185 smluv, smlouva po smlouvě")
    print("=" * 80)

    total_leaks = 0
    contracts_with_leaks = []

    for i, base, status, leaks in report:
        if status == "MISSING":
            print(f"\n[{i:3d}/185] {base}: CHYBÍ SOUBORY")
            continue

        if leaks:
            total_leaks += len(leaks)
            contracts_with_leaks.append(base)
            print(f"\n[{i:3d}/185] {base}: NALEZENO {len(leaks)} LEAKŮ")
            for j, L in enumerate(leaks, 1):
                print(f"       -> {j}. [{L['type']}] '{L['original'][:50]}...' " if len(L['original']) > 50 else f"       -> {j}. [{L['type']}] '{L['original']}'")
                print(f"          Kontext: ...{L['context']}...")
        else:
            print(f"[{i:3d}/185] {base}: OK")

    print("\n" + "=" * 80)
    print("SOUHRN")
    print(f"  Smluv s leaky: {len(contracts_with_leaks)}")
    print(f"  Celkem leaků: {total_leaks}")
    if contracts_with_leaks:
        print(f"  Smlouvy s leaky: {', '.join(contracts_with_leaks)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
