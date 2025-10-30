# -*- coding: utf-8 -*-
"""
Czech DOCX Anonymizer – v6.1
- Načítá jména z JSON knihovny (cz_names.v1.json)
- Opraveno: BANK vs OP, falešné osoby, adresy
Výstupy: <basename>_anon.docx / _map.json / _map.txt
"""

import sys, re, json, unicodedata
from typing import Optional, Set
from pathlib import Path
from collections import defaultdict, OrderedDict
from docx import Document

# ... (rest of original code remains unchanged until main)

def batch_anonymize(folder_path, names_json="cz_names.v1.json"):
    folder = Path(folder_path)
    docx_files = list(folder.glob("*.docx"))
    if not docx_files:
        print(f"Nebyly nalezeny žádné .docx soubory v adresáři {folder_path}")
        return
    print(f"Zpracovávám {len(docx_files)} souborů v adresáři {folder_path}")
    global CZECH_FIRST_NAMES
    CZECH_FIRST_NAMES = load_names_library(names_json)
    for path in docx_files:
        print(f"\n🔍 Zpracovávám: {path.name}")
        base = path.stem
        out_docx = path.parent / f"{base}_anon.docx"
        out_json = path.parent / f"{base}_map.json"
        out_txt  = path.parent / f"{base}_map.txt"
        a = Anonymizer(verbose=False)
        a.anonymize_docx(str(path), str(out_docx), str(out_json), str(out_txt))
        print(f"✅ Výstupy: {out_docx}, {out_json}, {out_txt}")

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Anonymizace českých DOCX s JSON knihovnou jmen")
    ap.add_argument("docx_path", nargs='?', help="Cesta k .docx souboru nebo adresáři")
    ap.add_argument("--names-json", default="cz_names.v1.json", help="Cesta k JSON knihovně jmen")
    ap.add_argument("--batch", action="store_true", help="Zpracovat všechny .docx v adresáři")
    args = ap.parse_args()

    try:
        if args.names_json != "cz_names.v1.json":
            global CZECH_FIRST_NAMES
            CZECH_FIRST_NAMES = load_names_library(args.names_json)
        if args.batch and args.docx_path:
            batch_anonymize(args.docx_path, args.names_json)
            return 0
        # Původní single file anonymizace zde:
        path = Path(args.docx_path) if args.docx_path else Path(input("Přetáhni sem .docx soubor nebo napiš cestu: ").strip().strip('"'))
        if not path.exists():
            print("❌ Soubor nenalezen:", path)
            input("\nStiskni Enter pro ukončení...")
            return 2

        base = path.stem
        out_docx = path.parent / f"{base}_anon.docx"
        out_json = path.parent / f"{base}_map.json"
        out_txt  = path.parent / f"{base}_map.txt"

        files_locked = False
        for out_file in [out_docx, out_json, out_txt]:
            if out_file.exists():
                try:
                    with open(out_file, 'a'):
                        pass
                except PermissionError:
                    files_locked = True
                    break

        if files_locked:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_docx = path.parent / f"{base}_anon_{timestamp}.docx"
            out_json = path.parent / f"{base}_map_{timestamp}.json"
            out_txt  = path.parent / f"{base}_map_{timestamp}.txt"
            print(f"\n⚠️  Výstupní soubory jsou otevřené v jiné aplikaci!")
            print(f"   Vytvářím nové soubory s časovým razítkem: {timestamp}")
            print()

        print(f"\n🔍 Zpracovávám: {path.name}")
        a = Anonymizer(verbose=False)
        a.anonymize_docx(str(path), str(out_docx), str(out_json), str(out_txt))

        print("\n✅ Výstupy:")
        print(f" - {out_docx}")
        print(f" - {out_json}")
        print(f" - {out_txt}")
        print(f"\n📊 Statistiky:")
        print(f" - Nalezeno osob: {len(a.canonical_persons)}")
        print(f" - Celkem tagů: {sum(a.counter.values())}")

        if sys.stdin.isatty():
            input("\n✅ Hotovo! Stiskni Enter pro ukončení...")
        return 0

    except Exception as e:
        print(f"\n❌ CHYBA: {e}")
        print(f"\n📋 Detail chyby:")
        import traceback
        traceback.print_exc()
        try:
            input("\n⚠️  Stiskni Enter pro ukončení...")
        except:
            import time
            print("\n⚠️  Zavírám za 10 sekund...")
            time.sleep(10)
        return 1

if __name__ == "__main__":
    sys.exit(main())