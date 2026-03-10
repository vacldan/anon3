#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

txt_dir = Path(__file__).parent / "anon_txt"
results = []

for f in sorted(txt_dir.glob("*_anon.txt")):
    text = f.read_text(encoding="utf-8")
    issues = []

    # 1) Vietnamese names not inside tags
    for vp in [r"Nguy\u1ec5n", r"Tr\u1ea7n", r"Ph\u1ea1m", r"Ho\u00e0ng", r"V\u0103n"]:
        for m in re.finditer(vp, text):
            before = text[max(0, m.start() - 5) : m.start()]
            if "[[" not in before:
                ctx = text[max(0, m.start() - 40) : m.end() + 40].replace("\n", " ")
                issues.append(f"VIET '{m.group()}': ...{ctx}...")

    # 2) Names with nicknames in quotes: Firstname "Nick" Lastname
    for m in re.finditer(
        r'([A-Z\u00C0-\u017E][a-z\u00E0-\u017E]+)\s+[\u201E""]\w+[\u201C""]\s+([A-Z\u00C0-\u017E][a-z\u00E0-\u017E]+)',
        text,
    ):
        before = text[max(0, m.start() - 5) : m.start()]
        if "[[" not in before:
            issues.append(f"NICK '{m.group()}'")

    # 3) German surnames with umlauts
    for m in re.finditer(r"\b[A-Z][a-z]*[\u00fc\u00f6\u00e4\u00df][a-z]+\b", text):
        before = text[max(0, m.start() - 5) : m.start()]
        if "[[" not in before:
            ctx = text[max(0, m.start() - 30) : m.end() + 30].replace("\n", " ")
            issues.append(f"GERMAN '{m.group()}': ...{ctx}...")

    # 4) Standalone first names followed by "uhrad" or after "Pan/Pani" but not tagged
    for m in re.finditer(r"(?:Pan|Paní)\s+([A-Z\u00C0-\u017E][a-z\u00E0-\u017E]{2,})\b", text):
        name = m.group(1)
        before = text[max(0, m.start() - 2) : m.start()]
        after_region = text[m.end() : m.end() + 5]
        if "[[" not in before and "[[" not in m.group(0) and name not in (
            "Havl", "Kone", "Horn",
        ):
            ctx = text[max(0, m.start() - 20) : m.end() + 40].replace("\n", " ")
            issues.append(f"PAN+NAME '{m.group()}': ...{ctx}...")

    if issues:
        results.append((f.name, issues))

print(f"Files with potential leaks: {len(results)}")
for fname, issues in results:
    print(f"\n=== {fname} ===")
    for iss in issues[:8]:
        print(f"  {iss}")
    if len(issues) > 8:
        print(f"  ... and {len(issues) - 8} more")
