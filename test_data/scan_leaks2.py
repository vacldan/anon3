#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan for standalone first names / possessive forms in anon text."""
import json, re, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

anon_dir = Path(__file__).parent / "anon_output"
txt_dir = Path(__file__).parent / "anon_txt"

results = []

for map_f in sorted(anon_dir.glob("*_map.json")):
    base = map_f.stem.replace("_map", "")
    txt_f = txt_dir / f"{base}_anon.txt"
    if not txt_f.exists():
        continue

    text = txt_f.read_text(encoding="utf-8")
    data = json.loads(map_f.read_text(encoding="utf-8"))
    entities = data.get("entities", [])

    issues = []

    for ent in entities:
        if ent.get("type") != "PERSON":
            continue
        orig = str(ent.get("original", "")).strip()
        if not orig or len(orig) < 4:
            continue
        parts = orig.split()
        if len(parts) < 2:
            continue
        first_name = parts[0]
        if len(first_name) < 3:
            continue

        # Check possessive form (Petřina, Janina, Martinův etc.)
        poss_suffixes = ["ina", "iny", "ině", "inu", "inou",
                         "ův", "ova", "ově", "ovu", "ovým"]
        for suf in poss_suffixes:
            poss_form = first_name.rstrip("a") + suf if first_name.endswith("a") else first_name + suf
            if len(poss_form) < 5:
                continue
            pattern = r"\b" + re.escape(poss_form) + r"\b"
            for m in re.finditer(pattern, text, re.IGNORECASE):
                before = text[max(0, m.start() - 5) : m.start()]
                if "[[" not in before:
                    ctx = text[max(0, m.start() - 30) : m.end() + 30].replace("\n", " ")
                    issues.append(f"POSSESSIVE '{m.group()}' (from {orig}): ...{ctx}...")

        # Check standalone first name (not inside tag) - at least 4 chars to avoid false positives
        if len(first_name) >= 4:
            for m in re.finditer(r"\b" + re.escape(first_name) + r"(?:[aoueiyěíů]\w{0,3})?\b", text):
                before = text[max(0, m.start() - 5) : m.start()]
                after = text[m.end() : m.end() + 5]
                if "[[" not in before and "]]" not in before:
                    ctx = text[max(0, m.start() - 30) : m.end() + 30].replace("\n", " ")
                    issues.append(f"FIRST_NAME '{m.group()}' (from {orig}): ...{ctx}...")

    if issues:
        results.append((map_f.stem.replace("_map", ""), issues))

print(f"Files with first-name/possessive leaks: {len(results)}")
for fname, issues in results:
    print(f"\n=== {fname} ===")
    for iss in issues[:10]:
        print(f"  {iss}")
    if len(issues) > 10:
        print(f"  ... and {len(issues) - 10} more")
