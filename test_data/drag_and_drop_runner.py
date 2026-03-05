# -*- coding: utf-8 -*-
"""
Drag&Drop runner for Czech DOCX Anonymizer – STRICT
---------------------------------------------------
Použití:
- Umísti tento soubor do stejné složky jako:
    - Czech_Docx_Anonymizer_STRICT_v7_3.py
    - cz_names.v1.json
    - (volitelně) extra_firstnames.json
- Windows/macOS/Linux: prostě PŘETÁHNI .docx soubory na tento .py soubor (drag&drop).
  Cesty se předají jako argv a každý .docx se zpracuje.
- Když žádné argv nejsou: projede VŠECHNY *.docx v aktuální složce (kromě už *_anon.docx).

Výstupy: <název>_anon.docx, <název>_map.txt, <název>_map.json vedle vstupu.
"""

import sys, importlib.util
from pathlib import Path

HERE = Path(__file__).parent
MOD = HERE / "Czech_Docx_Anonymizer_STRICT_v7_3.py"
NAMES = HERE / "cz_names.v1.json"
EXTRA = HERE / "extra_firstnames.json"

if not MOD.exists():
    print("❌ Nenalezen Czech_Docx_Anonymizer_STRICT_v7_3.py ve stejné složce."); sys.exit(2)
if not NAMES.exists():
    print("❌ Nenalezen cz_names.v1.json ve stejné složce."); sys.exit(2)

# import anonymizer module dynamically
spec = importlib.util.spec_from_file_location("anon", str(MOD))
anon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anon)

# decide input files
inputs = [Path(p) for p in sys.argv[1:] if p.lower().endswith(".docx")]
if not inputs:
    inputs = [p for p in HERE.glob("*.docx") if not p.name.endswith("_anon.docx")]

if not inputs:
    print("❗ Nenalezen žádný .docx ke zpracování."); sys.exit(0)

# (re)load names with optional extras
fname_extra = str(EXTRA.name) if EXTRA.exists() else None
anon.CZECH_FIRST_NAMES = anon.load_names_library(NAMES.name, fname_extra)

ok = 0; fail = 0
for path in inputs:
    try:
        base = path.stem
        out_docx = path.parent / f"{base}_anon.docx"
        out_json = path.parent / f"{base}_map.json"
        out_txt  = path.parent / f"{base}_map.txt"

        a = anon.Anonymizer(verbose=False)
        a.anonymize_docx(str(path), str(out_docx), str(out_json), str(out_txt))

        print(f"✅ {path.name} → {out_docx.name}, {out_txt.name}, {out_json.name}")
        ok += 1
    except Exception as e:
        print(f"❌ Chyba při zpracování {path.name}: {e}")
        fail += 1

print(f"\nHotovo. OK: {ok}, Chyby: {fail}")
