#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LOKÁLNÍ DEANONYMIZÁTOR PRO DEBUGGING
Verze s podrobným logováním pro diagnostiku problémů
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime


print("=" * 80)
print("DEANONYMIZÁTOR - LOKÁLNÍ DEBUG VERZE")
print("=" * 80)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# -------------------- Info o prostředí --------------------
print(">>> INFORMACE O PROSTŘEDÍ:")
print(f"Python verze: {sys.version}")
print(f"Aktuální složka: {os.getcwd()}")
print(f"Script cesta: {os.path.abspath(__file__)}")
print()

# -------------------- UTF-8 pro Windows konzoli --------------------
# DŮLEŽITÉ: Když jsme voláni z Electronu (přes spawn), stdout/stderr jsou už pipe objekty
# a encoding je nastaven přes PYTHONIOENCODING. Detach() by způsobil chybu!
# UTF-8 wrapping použijeme pouze v interaktivním TTY režimu.
print(">>> Kontroluji encoding...")
try:
    import io
    # Pokud je stdout TTY (interaktivní konzole), nastavíme UTF-8 wrapping
    if sys.stdout.isatty():
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8")
        print("✓ UTF-8 wrapping nastaven (TTY režim)")
    else:
        # Pipe režim (Electron) - encoding je už nastaven přes PYTHONIOENCODING
        print("✓ Pipe režim detekován, encoding nastaven přes prostředí")
except Exception as e:
    print(f"⚠ UTF-8 wrapping se nepodařilo nastavit: {e}")
    print(f"  Používám výchozí encoding: {sys.stdout.encoding}")
print()

# -------------------- Kontrola knihoven --------------------
print(">>> Kontroluji dostupnost knihoven...")
libraries_ok = True

try:
    from docx import Document
    print("✓ python-docx je nainstalována")
except ImportError as e:
    print(f"✗ CHYBA: python-docx není nainstalována!")
    print(f"  Detaily: {e}")
    print(f"  Řešení: pip install python-docx")
    libraries_ok = False

try:
    import json
    print("✓ json je dostupný (standardní knihovna)")
except ImportError as e:
    print(f"✗ CHYBA: json není dostupný: {e}")
    libraries_ok = False

print()

if not libraries_ok:
    print("=" * 80)
    print("KRITICKÁ CHYBA: Některé knihovny chybí!")
    print("=" * 80)
    input("\nStiskni ENTER pro ukončení...")
    sys.exit(1)


# -------------------- Helpers --------------------
def _load_json(path: Path):
    """Načte JSON soubor s error handlingem"""
    print(f"  → Načítám JSON: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  ✓ JSON načten úspěšně")
        return data
    except FileNotFoundError:
        print(f"  ✗ CHYBA: Soubor nenalezen!")
        raise
    except json.JSONDecodeError as e:
        print(f"  ✗ CHYBA: Neplatný JSON formát!")
        print(f"    Řádek {e.lineno}, sloupec {e.colno}: {e.msg}")
        raise
    except Exception as e:
        print(f"  ✗ CHYBA: {type(e).__name__}: {e}")
        raise


def _flatten_mapping(obj):
    """
    Vytáhne mapping tag->original i z nestandardních JSON struktur.
    Podporuje:
    - { "[[TAG]]": "value", ... }
    - { "mapping": { ... } }
    - { "entities": [{"label": "[[TAG]]", "original": "value"}, ...] }
    - listy dvojic, nebo listy dictů
    - vnořené dicty (projde rekurzivně)
    """
    print("  → Parsuju strukturu mappingu...")
    flat = {}

    def walk(x):
        if x is None:
            return

        # Nejčastější případ: dict
        if isinstance(x, dict):
            # Pokud je to náš formát s entities
            if "entities" in x and isinstance(x["entities"], list):
                print(f"    Nalezen formát 'entities' s {len(x['entities'])} záznamy")
                for entity in x["entities"]:
                    if isinstance(entity, dict) and "label" in entity and "original" in entity:
                        label = entity["label"]
                        original = entity["original"]
                        if isinstance(label, str) and label.startswith("[[") and label.endswith("]]"):
                            # Použij pouze první výskyt (základní tvar), ignoruj ostatní varianty
                            if label not in flat:
                                flat[label] = str(original)
                return

            # Pokud je to "obal" s mapping klíčem
            if "mapping" in x and isinstance(x["mapping"], (dict, list)):
                print(f"    Nalezen formát s klíčem 'mapping'")
                walk(x["mapping"])
                return

            # Pokud v dictu jsou přímo TAG:VALUE
            tag_count = 0
            for k, v in x.items():
                if isinstance(k, str) and k.startswith("[[") and k.endswith("]]"):
                    # value může být string / číslo / dict...
                    if isinstance(v, str):
                        flat[k] = v
                    else:
                        flat[k] = json.dumps(v, ensure_ascii=False)
                    tag_count += 1
                else:
                    walk(v)
            if tag_count > 0:
                print(f"    Nalezeno {tag_count} tagů přímo v dictu")
            return

        # List: buď list dictů nebo list párů
        if isinstance(x, list):
            for item in x:
                # Zkontroluj jestli to není náš formát entity
                if isinstance(item, dict) and "label" in item and "original" in item:
                    label = item["label"]
                    original = item["original"]
                    if isinstance(label, str) and label.startswith("[[") and label.endswith("]]"):
                        # Použij pouze první výskyt (základní tvar)
                        if label not in flat:
                            flat[label] = str(original)
                # ["[[TAG]]","value"]
                elif isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], str):
                    k = item[0]
                    v = item[1]
                    if isinstance(k, str) and k.startswith("[[") and k.endswith("]]"):
                        flat[k] = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                else:
                    walk(item)
            return

        # Ostatní typy ignorujeme
        return

    walk(obj)
    print(f"  ✓ Celkem nalezeno {len(flat)} tagů")

    # Vypíšeme prvních 5 tagů jako ukázku
    if flat:
        print("    Ukázka prvních tagů:")
        for i, (tag, val) in enumerate(list(flat.items())[:5]):
            print(f"      {tag} → {val[:50] if len(val) > 50 else val}")
        if len(flat) > 5:
            print(f"      ... a dalších {len(flat) - 5} tagů")

    return flat


def _sorted_replacements(mapping: dict):
    # Delší tagy první, aby se nepřepisovaly částečně
    print("  → Třídím tagy podle délky...")
    items = [(k, str(v)) for k, v in mapping.items()]
    items.sort(key=lambda x: len(x[0]), reverse=True)
    print(f"  ✓ Seřazeno {len(items)} tagů")
    return items


def _replace_all(text: str, rep_items):
    changed = False
    for tag, original in rep_items:
        if tag in text:
            text = text.replace(tag, original)
            changed = True
    return text, changed


def _apply_to_paragraph(para, rep_items):
    """
    Robustní: vezme celý text odstavce přes všechny runy, provede replacements,
    a pak ho vrátí zpátky tak, aby to fungovalo i když tag byl rozsekaný přes runy.

    Pozn.: Může to zjednodušit formátování v místě, kde byl tag (typicky OK).
    """
    if not para.runs:
        return 0

    full = "".join(r.text for r in para.runs)
    if not full.strip():
        return 0

    new_text, changed = _replace_all(full, rep_items)
    if not changed:
        return 0

    # Zachovej první run (aby zůstala aspoň základní style informace),
    # ostatní vyprázdni:
    para.runs[0].text = new_text
    for r in para.runs[1:]:
        r.text = ""

    return 1


def deanonymize_document(anon_doc_path: Path, map_path: Path, output_path: Path) -> bool:
    print("\n" + "=" * 80)
    print("SPOUŠTÍM DEANONYMIZACI")
    print("=" * 80)
    print(f"Anonymní dokument: {anon_doc_path}")
    print(f"JSON mapa:         {map_path}")
    print(f"Výstupní dokument: {output_path}")
    print()

    # Krok 1: Načtení mapy
    print(">>> KROK 1: Načítání JSON mapy")
    try:
        raw = _load_json(map_path)
        print(f"  ✓ JSON načten, velikost: {len(str(raw))} znaků")
    except Exception as e:
        print(f"\n✗✗✗ KRITICKÁ CHYBA při načítání mapy ✗✗✗")
        print(f"Typ chyby: {type(e).__name__}")
        print(f"Popis: {e}")
        return False

    # Krok 2: Parsování mapy
    print("\n>>> KROK 2: Parsování struktury mapy")
    try:
        mapping = _flatten_mapping(raw)
        if not mapping:
            print("✗ CHYBA: Mapa je prázdná nebo nemá tagy ve formátu [[...]]")
            print("  Zkontroluj, jestli JSON obsahuje správnou strukturu")
            return False
    except Exception as e:
        print(f"\n✗✗✗ CHYBA při parsování mapy ✗✗✗")
        print(f"Typ chyby: {type(e).__name__}")
        print(f"Popis: {e}")
        return False

    # Krok 3: Příprava náhrad
    print("\n>>> KROK 3: Příprava náhrad")
    try:
        rep_items = _sorted_replacements(mapping)
    except Exception as e:
        print(f"✗ CHYBA při třídění tagů: {e}")
        return False

    # Krok 4: Načtení dokumentu
    print("\n>>> KROK 4: Načítání Word dokumentu")
    try:
        print(f"  → Otevírám: {anon_doc_path}")
        doc = Document(str(anon_doc_path))
        para_count = len(doc.paragraphs)
        table_count = len(doc.tables)
        print(f"  ✓ Dokument načten")
        print(f"    Počet odstavců: {para_count}")
        print(f"    Počet tabulek: {table_count}")
    except Exception as e:
        print(f"\n✗✗✗ CHYBA při načítání dokumentu ✗✗✗")
        print(f"Typ chyby: {type(e).__name__}")
        print(f"Popis: {e}")
        return False

    # Krok 5: Nahrazování v dokumentu
    print("\n>>> KROK 5: Provádím náhrady v dokumentu")
    total_changed_paras = 0

    try:
        # Main paragraphs
        print("  → Zpracovávám hlavní odstavce...")
        for i, para in enumerate(doc.paragraphs):
            total_changed_paras += _apply_to_paragraph(para, rep_items)
            if (i + 1) % 50 == 0:
                print(f"    Zpracováno {i + 1}/{para_count} odstavců...")

        print(f"  ✓ Hlavní odstavce hotovo")

        # Tables
        if table_count > 0:
            print("  → Zpracovávám tabulky...")
            for tbl_idx, tbl in enumerate(doc.tables):
                for row in tbl.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            total_changed_paras += _apply_to_paragraph(para, rep_items)
            print(f"  ✓ Tabulky hotovo")

        print(f"  ✓ Celkem změněno {total_changed_paras} odstavců")

    except Exception as e:
        print(f"\n✗✗✗ CHYBA při nahrazování textů ✗✗✗")
        print(f"Typ chyby: {type(e).__name__}")
        print(f"Popis: {e}")
        import traceback
        print("\nStacktrace:")
        traceback.print_exc()
        return False

    # Krok 6: Uložení výsledku
    print("\n>>> KROK 6: Ukládání výstupního dokumentu")
    try:
        print(f"  → Vytvářím složku: {output_path.parent}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  → Ukládám do: {output_path}")
        doc.save(str(output_path))
        print(f"  ✓ Dokument úspěšně uložen")

        # Ověření existence
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"  ✓ Výstupní soubor existuje, velikost: {size:,} bytů")
        else:
            print(f"  ⚠ VAROVÁNÍ: Výstupní soubor nebyl vytvořen!")
            return False

    except Exception as e:
        print(f"\n✗✗✗ CHYBA při ukládání dokumentu ✗✗✗")
        print(f"Typ chyby: {type(e).__name__}")
        print(f"Popis: {e}")
        import traceback
        print("\nStacktrace:")
        traceback.print_exc()
        return False

    # Finální report
    print("\n" + "=" * 80)
    print("✓✓✓ DEANONYMIZACE DOKONČENA ÚSPĚŠNĚ ✓✓✓")
    print("=" * 80)
    print(f"Změněné odstavce: {total_changed_paras}")
    print(f"Celkem tagů v mapě: {len(mapping)}")
    print(f"Výstupní soubor: {output_path}")
    print("=" * 80)

    return True


# -------------------- CLI --------------------
def main():
    try:
        # Podporuje i původní "3 argumenty", ale přidává --input/--map/--output styl
        args = sys.argv[1:]

        print(">>> PARSOVÁNÍ ARGUMENTŮ PŘÍKAZOVÉ ŘÁDKY")
        print(f"Argumenty: {args if args else '(žádné)'}")
        print()

        # Defaulty
        IN_DOC = Path("smlouva_anon.docx")
        IN_MAP = Path("smlouva_map.json")
        OUT_DOC = Path("smlouva_deanon.docx")

        # AUTOMATICKÁ DETEKCE: pokud je jen 1 argument, odvozuj ostatní
        if len(args) == 1 and not args[0].startswith("--"):
            input_file = Path(args[0])
            print("  → Detekuji pouze 1 argument, automaticky odvozuji ostatní soubory...")

            # Odvoď cestu k mapě a outputu
            # Např: smlouva29_anon.docx -> smlouva29_map.json, smlouva29_deanon.docx
            stem = input_file.stem  # smlouva29_anon
            parent = input_file.parent  # složka

            # Nahraď _anon za _map/_deanon
            if stem.endswith("_anon"):
                base = stem[:-5]  # smlouva29
                map_name = f"{base}_map.json"
                output_name = f"{base}_deanon.docx"
            else:
                # Fallback: přidej _map/_deanon
                base = stem
                map_name = f"{base}_map.json"
                output_name = f"{base}_deanon.docx"

            IN_DOC = input_file
            IN_MAP = parent / map_name
            OUT_DOC = parent / output_name

            print(f"    Input:  {IN_DOC.name}")
            print(f"    Mapa:   {IN_MAP.name}")
            print(f"    Output: {OUT_DOC.name}")

        # 3 poziční argumenty
        elif len(args) >= 3 and not args[0].startswith("--"):
            IN_DOC = Path(args[0])
            IN_MAP = Path(args[1])
            OUT_DOC = Path(args[2])
            print("  → Použity 3 poziční argumenty")
        else:
            # jednoduchý parser pro --input --map --output
            def get_flag(flag):
                if flag in args:
                    i = args.index(flag)
                    if i + 1 < len(args):
                        return args[i + 1]
                return None

            in_doc = get_flag("--input")
            in_map = get_flag("--map")
            out_doc = get_flag("--output")

            if in_doc:
                IN_DOC = Path(in_doc)
            if in_map:
                IN_MAP = Path(in_map)
            if out_doc:
                OUT_DOC = Path(out_doc)

            if not args:
                print("  → Použity výchozí hodnoty")
            else:
                print("  → Použity flagy (--input, --map, --output)")

        IN_DOC = IN_DOC.resolve()
        IN_MAP = IN_MAP.resolve()
        OUT_DOC = OUT_DOC.resolve()

        print(f"\nNastavené cesty:")
        print(f"  Input:  {IN_DOC}")
        print(f"  Mapa:   {IN_MAP}")
        print(f"  Output: {OUT_DOC}")
        print()

        # Kontrola existence vstupních souborů
        print(">>> KONTROLA VSTUPNÍCH SOUBORŮ")

        if not IN_DOC.exists():
            print(f"✗ CHYBA: Anonymní dokument neexistuje!")
            print(f"  Cesta: {IN_DOC}")
            print(f"  Aktuální složka: {os.getcwd()}")
            print(f"\n.docx soubory v aktuální složce:")
            try:
                docx_files = sorted(Path(IN_DOC).parent.glob("*.docx"))[:15]
                if docx_files:
                    for f in docx_files:
                        marker = " ← TEN" if f.name == IN_DOC.name else ""
                        print(f"    - {f.name}{marker}")
                else:
                    print("    (žádné .docx soubory)")
            except:
                pass
            return False

        print(f"✓ Anonymní dokument existuje")
        print(f"  Velikost: {IN_DOC.stat().st_size:,} bytů")

        if not IN_MAP.exists():
            print(f"✗ CHYBA: Mapa neexistuje!")
            print(f"  Cesta: {IN_MAP}")
            print(f"  Aktuální složka: {os.getcwd()}")
            print(f"\n.json soubory v aktuální složce:")
            try:
                json_files = sorted(Path(IN_MAP).parent.glob("*.json"))[:15]
                if json_files:
                    for f in json_files:
                        marker = " ← TEN" if f.name == IN_MAP.name else ""
                        print(f"    - {f.name}{marker}")
                else:
                    print("    (žádné .json soubory)")
            except:
                pass
            return False

        print(f"✓ JSON mapa existuje")
        print(f"  Velikost: {IN_MAP.stat().st_size:,} bytů")
        print()

        # Spuštění deanonymizace
        ok = deanonymize_document(IN_DOC, IN_MAP, OUT_DOC)
        return ok

    except Exception as e:
        print("\n" + "=" * 80)
        print("✗✗✗ NEOČEKÁVANÁ CHYBA ✗✗✗")
        print("=" * 80)
        print(f"Typ: {type(e).__name__}")
        print(f"Popis: {e}")
        print("\nStacktrace:")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = main()

    print("\n" + "=" * 80)
    if result:
        print("PROGRAM UKONČEN: ÚSPĚCH")
    else:
        print("PROGRAM UKONČEN: CHYBA")
    print("=" * 80)
    print(f"Konec: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # PAUZA - pouze když je spuštěno interaktivně v terminálu
    # V Electron aplikaci nesmíme čekat na input, jinak proces nikdy neskončí!
    if sys.stdin.isatty():
        input("\n>>> Stiskni ENTER pro ukončení...")

    sys.exit(0 if result else 1)
