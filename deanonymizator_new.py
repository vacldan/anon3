#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from pathlib import Path

from docx import Document


# -------------------- UTF-8 for Windows console --------------------
# (bezpečné – když nejde, tak to jen přeskočíme)
try:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8")
except Exception:
    pass


# -------------------- Helpers --------------------
def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    flat = {}

    def walk(x):
        if x is None:
            return

        # Nejčastější případ: dict
        if isinstance(x, dict):
            # Pokud je to náš formát s entities
            if "entities" in x and isinstance(x["entities"], list):
                for entity in x["entities"]:
                    if isinstance(entity, dict) and "label" in entity and "original" in entity:
                        label = entity["label"]
                        original = entity["original"]
                        if isinstance(label, str) and label.startswith("[[") and label.endswith("]]"):
                            flat[label] = str(original)
                return

            # Pokud je to "obal" s mapping klíčem
            if "mapping" in x and isinstance(x["mapping"], (dict, list)):
                walk(x["mapping"])
                return

            # Pokud v dictu jsou přímo TAG:VALUE
            for k, v in x.items():
                if isinstance(k, str) and k.startswith("[[") and k.endswith("]]"):
                    # value může být string / číslo / dict...
                    if isinstance(v, str):
                        flat[k] = v
                    else:
                        flat[k] = json.dumps(v, ensure_ascii=False)
                else:
                    walk(v)
            return

        # List: buď list dictů nebo list párů
        if isinstance(x, list):
            for item in x:
                # Zkontroluj jestli to není náš formát entity
                if isinstance(item, dict) and "label" in item and "original" in item:
                    label = item["label"]
                    original = item["original"]
                    if isinstance(label, str) and label.startswith("[[") and label.endswith("]]"):
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
    return flat


def _sorted_replacements(mapping: dict):
    # Delší tagy první, aby se nepřepisovaly částečně
    items = [(k, str(v)) for k, v in mapping.items()]
    items.sort(key=lambda x: len(x[0]), reverse=True)
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


def deanonymize_document(anon_doc_path: Path, map_path: Path, output_path: Path, verbose: bool = True) -> bool:
    if verbose:
        print("DEANONYMIZER - obnoveni puvodniho dokumentu...")
        print(f"Vstupni anonymni dokument: {anon_doc_path}")
        print(f"JSON mapa: {map_path}")
        print(f"Vystupni dokument: {output_path}")

    try:
        raw = _load_json(map_path)
        mapping = _flatten_mapping(raw)
        if not mapping:
            print("ERROR: Mapa je prazdna nebo nema tagy ve formatu [[...]].")
            return False
    except Exception as e:
        print(f"ERROR: Nepodarilo se nacist mapu: {e}")
        return False

    rep_items = _sorted_replacements(mapping)

    try:
        doc = Document(str(anon_doc_path))
    except Exception as e:
        print(f"ERROR: Nepodarilo se nacist dokument: {e}")
        return False

    total_changed_paras = 0

    # Main paragraphs
    for para in doc.paragraphs:
        total_changed_paras += _apply_to_paragraph(para, rep_items)

    # Tables
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    total_changed_paras += _apply_to_paragraph(para, rep_items)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))
    except Exception as e:
        print(f"ERROR: Chyba pri ukladani: {e}")
        return False

    if verbose:
        print("DEANONYMIZACE DOKONCENA!")
        print(f"Zmenene odstavce: {total_changed_paras}")
        print(f"Celkem tagu v mape: {len(mapping)}")

    return True


# -------------------- CLI --------------------
def main():
    # Podporuje i původní “3 argumenty”, ale přidává --input/--map/--output styl
    args = sys.argv[1:]

    # Defaulty
    IN_DOC = Path("smlouva_anon.docx")
    IN_MAP = Path("smlouva_map.json")
    OUT_DOC = Path("smlouva_deanon.docx")

    # 3 poziční argumenty
    if len(args) >= 3 and not args[0].startswith("--"):
        IN_DOC = Path(args[0])
        IN_MAP = Path(args[1])
        OUT_DOC = Path(args[2])
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

    IN_DOC = IN_DOC.resolve()
    IN_MAP = IN_MAP.resolve()
    OUT_DOC = OUT_DOC.resolve()

    if not IN_DOC.exists():
        print(f"ERROR: Anonymni dokument neexistuje: {IN_DOC}")
        print(f"Aktualni slozka: {os.getcwd()}")
        sys.exit(1)

    if not IN_MAP.exists():
        print(f"ERROR: Mapa neexistuje: {IN_MAP}")
        print(f"Aktualni slozka: {os.getcwd()}")
        sys.exit(1)

    ok = deanonymize_document(IN_DOC, IN_MAP, OUT_DOC, verbose=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
