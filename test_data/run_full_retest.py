#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-anonymize ALL contracts with the updated anon72 (with standalone firstname post-pass)."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from anon72 import Anonymizer

INPUT_DIR = Path(__file__).parent
OUT_DIR = INPUT_DIR / "anon_output"
OUT_DIR.mkdir(exist_ok=True)

docx_files = sorted(
    [f for f in INPUT_DIR.glob("*.docx") if "_anon" not in f.stem and "_deanon" not in f.stem],
    key=lambda p: p.name,
)

print(f"Found {len(docx_files)} contracts to process.\n")
t0 = time.time()
errors = []
postpass_total = 0

for i, f in enumerate(docx_files, 1):
    base = f.stem
    out_docx = OUT_DIR / f"{base}_anon.docx"
    out_json = OUT_DIR / f"{base}_map.json"
    out_txt = OUT_DIR / f"{base}_map.txt"

    try:
        a = Anonymizer()
        a.anonymize_docx(str(f), str(out_docx), str(out_json), str(out_txt))
    except Exception as e:
        errors.append((f.name, str(e)))
        print(f"  [ERROR] {f.name}: {e}")

    if i % 20 == 0:
        elapsed = time.time() - t0
        print(f"\n--- Progress: {i}/{len(docx_files)} ({elapsed:.0f}s elapsed) ---\n")

elapsed = time.time() - t0
print(f"\n{'='*60}")
print(f"Done: {len(docx_files)} contracts in {elapsed:.0f}s")
if errors:
    print(f"ERRORS: {len(errors)}")
    for name, err in errors:
        print(f"  {name}: {err}")
else:
    print("No errors!")
