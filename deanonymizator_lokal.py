#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LOKÁLNÍ DEANONYMIZÁTOR PRO DEBUGGING
Verze s podrobným logováním pro diagnostiku problémů
"""

import sys
import os
import json
import re
import time
import tempfile
import shutil
import unicodedata
from pathlib import Path
from datetime import datetime


# -------------------- Normalizace jmen do nominativu --------------------
# Globální proměnná pro knihovnu jmen
CZECH_FIRST_NAMES = set()

def load_names_library(json_path="cz_names.v1.json"):
    """Načte českou knihovnu jmen z JSON"""
    global CZECH_FIRST_NAMES
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        names = set()
        for gender in ['M', 'F']:
            for name in data.get('firstnames', {}).get(gender, []):
                names.add(name.lower())
        CZECH_FIRST_NAMES = names
        return names
    except:
        # Pokud se nepodaří načíst, použij prázdnou množinu
        CZECH_FIRST_NAMES = set()
        return set()

def remove_diacritics(text):
    """Odstraní diakritiku z textu"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def infer_first_name_nominative(name):
    """Převede křestní jméno do nominativu (1. pádu)"""
    if not name or len(name) < 2:
        return name

    obs = name.strip()
    lo = obs.lower()

    # SPECIÁLNÍ PŘÍPAD PRVNÍ: Roberta může být genitiv od Robert
    if lo == 'roberta':
        return 'Robert'

    # Pokud je jméno přímo v knihovně, vrátíme ho
    if lo in CZECH_FIRST_NAMES:
        return obs.capitalize()

    # Ochrana běžných jmen která končí na typické deklinační koncovky
    protected_female_names = {
        'martina', 'kristina', 'pavlína', 'karolína', 'jana', 'hana',
        'eva', 'anna', 'petra', 'daniela', 'michaela', 'andrea',
        'lenka', 'tereza', 'barbora', 'veronika', 'nikola', 'viktorie',
        'irena', 'sylva', 'šárka', 'alžběta', 'adéla', 'sára', 'lucie',
        'marie', 'kateřina', 'markéta', 'ivana', 'zuzana'
    }
    protected_male_names = {
        'david', 'martin', 'jakub', 'tomáš', 'jan', 'petr', 'pavel',
        'ivan', 'robert', 'ondřej', 'hynek', 'luděk', 'radovan', 'marek',
        'tobiáš', 'mark', 'radek', 'miroslav', 'matěj', 'bohumil',
        'milan', 'jiří', 'josef', 'václav', 'karel', 'lukáš', 'michal',
        'filip', 'adam', 'daniel', 'vojtěch', 'stanislav'
    }

    if lo in protected_female_names:
        return obs

    # Genitiv/Akuzativ mužských jmen: -a → odstranit (Ivana → Ivan, Roberta → Robert, Matěje → Matěj)
    if lo.endswith('a') and len(obs) > 3:
        base = obs[:-1]
        base_lo = base.lower()

        # Zkontroluj, zda základ je mužské jméno
        if base_lo in protected_male_names:
            return base.capitalize()
        if base_lo in CZECH_FIRST_NAMES:
            return base.capitalize()
        if CZECH_FIRST_NAMES and remove_diacritics(base_lo) in {remove_diacritics(n) for n in CZECH_FIRST_NAMES}:
            return base.capitalize()

    # Genitiv -e → odstranit (Matěje → Matěj, Martine → Martin)
    if lo.endswith('e') and len(obs) > 3 and not lo.endswith(('ové', 'ice', 'ové')):
        base = obs[:-1]
        base_lo = base.lower()
        # Kontrola: pokud je to známé mužské jméno
        common_male_e = {'matěj', 'martin', 'bohumil', 'milan', 'dan', 'jan', 'stan'}
        if base_lo in common_male_e or base_lo in protected_male_names:
            return base.capitalize()
        if CZECH_FIRST_NAMES and base_lo in CZECH_FIRST_NAMES:
            return base.capitalize()

    # Dativ -u → odstranit (Martinu → Martin, Pavlu → Pavel)
    if lo.endswith('u') and len(obs) > 3:
        base = obs[:-1]
        base_lo = base.lower()
        if base_lo in protected_male_names or (CZECH_FIRST_NAMES and base_lo in CZECH_FIRST_NAMES):
            return base.capitalize()

    # Genitiv ženských jmen: -y → -a (Pavlíny → Pavlína)
    if lo.endswith('y') and len(obs) > 3:
        base = obs[:-1] + 'a'
        if base.lower() in CZECH_FIRST_NAMES or base.lower() in protected_female_names:
            return base

    # Instrumentál ženských jmen: -ou → -a (Pavlínou → Pavlína)
    if lo.endswith('ou') and len(obs) > 4:
        base = obs[:-2] + 'a'
        if base.lower() in CZECH_FIRST_NAMES or base.lower() in protected_female_names:
            return base

    # Dativ/Lokál: -ovi, -emu → odstranit (Ivanovi → Ivan)
    if lo.endswith('ovi') and len(obs) > 5:
        base = obs[:-3]
        if CZECH_FIRST_NAMES and (base.lower() in CZECH_FIRST_NAMES or remove_diacritics(base.lower()) in {remove_diacritics(n) for n in CZECH_FIRST_NAMES}):
            return base.capitalize()

    # Instrumentál mužských jmen: -em → odstranit (Ivanem → Ivan, Tomášem → Tomáš)
    if lo.endswith('em') and len(obs) > 4:
        base = obs[:-2]
        base_lo = base.lower()

        # Speciální: jména končící na souhlásku+v → pravděpodobně potřebují normalizaci
        # Miroslavem → Miroslav (ne Miroslavem)
        # Břetislavem → Břetislav
        if base_lo.endswith(('slav', 'stav', 'měr')):
            return base.capitalize()

        # Běžná kontrola přes knihovnu jmen
        if CZECH_FIRST_NAMES and (base_lo in CZECH_FIRST_NAMES or base_lo in protected_male_names or remove_diacritics(base_lo) in {remove_diacritics(n) for n in CZECH_FIRST_NAMES}):
            return base.capitalize()

    return obs

def infer_surname_nominative(surname):
    """Převede příjmení do nominativu (1. pádu)"""
    if not surname or len(surname) < 3:
        return surname

    obs = surname.strip()
    lo = obs.lower()

    # Ochrana příjmení, která končí na deklinační vzory ale jsou už v nominativu
    protected_surnames = {
        'procházka', 'němec', 'sedláček', 'kučera', 'fiala', 'dušek',
        'kozel', 'šembera', 'havel', 'pavel', 'klíma', 'svoboda',
        'valach', 'štrunc', 'jůza'
    }
    if lo in protected_surnames:
        return obs

    # Genitiv/Dativ/Lokál žen: -é → -á (Pokorné → Pokorná, Houfové → Houfová)
    if lo.endswith('é') and len(obs) > 3:
        return obs[:-1] + 'á'

    # Instrumentál: -ou → může být -á (žena) nebo -ý (muž)
    if lo.endswith('ou') and len(obs) > 4:
        base = obs[:-2]
        # Pro příjmení jako "Vránou" → může být "Vráný" (muž) nebo "Vráná" (žena)
        if base.lower().endswith(('vrán', 'novot', 'malý', 'černý')):
            return base + 'ý'
        # Jinak ženský tvar
        return obs[:-2] + 'á'

    # Genitiv mužů: -y → -a (Klímy → Klíma, ale ne Nováky → Novák)
    if lo.endswith('y') and len(obs) > 3:
        # Kontrola: příjmení na -a v nominativu (Klíma, Procházka)
        base_a = obs[:-1] + 'a'
        if base_a.lower() in protected_surnames:
            return base_a
        # Obecná heuristika: -y → -a pro příjmení jako Klíma
        if obs[:-1].lower().endswith(('klím', 'dvořák', 'svobod')):
            return base_a
        # Jinak jen odstraň -y (Nováky → Novák)
        return obs[:-1]

    # Genitiv mužů: -a → odstranit (Nováka → Novák)
    if lo.endswith('a') and len(obs) > 3 and lo not in protected_surnames:
        base = obs[:-1]
        return base

    # Dativ/Lokál: -ovi → odstranit (Novákovi → Novák)
    if lo.endswith('ovi') and len(obs) > 5:
        base = obs[:-3]
        base_lo = base.lower()

        # Speciální: příjmení na -Xkovi → pravděpodobně -Xček nebo -Xšek v nominativu
        # Havlíčkovi → Havlíček (ne Havlíčk!)
        # Vašíčkovi → Vašíček
        # Kubíkovi → Kubík (ale toto už je správně, končí na -bík)
        if base_lo.endswith('k') and len(base) > 2:
            # Pokud před 'k' je "č", "š", "ž" nebo samohláska s háčkem
            # pravděpodobně potřebujeme přidat 'e' před 'k'
            # Havlíčk → Havlíček (před k je č)
            # Vašíčk → Vašíček
            before_k = base_lo[-2] if len(base_lo) >= 2 else ''
            if before_k in ('č', 'š', 'ž', 'ť', 'ď', 'ň', 'ř'):
                # Přidej 'e' před 'k'
                return base[:-1] + 'ek'

        # Jinak jen odstraň -ovi
        return base

    # Instrumentál mužů: -em → odstranit
    if lo.endswith('em') and len(obs) > 4:
        # Speciální: -alem, -elem, -olem (Doležalem → Doležal)
        if lo.endswith(('alem', 'elem', 'olem', 'ilem')):
            return obs[:-2]
        # Kontrola: -kem → -ek nebo -ík (Práškem → Prášek, Kubíkem → Kubík)
        if lo.endswith('kem') and len(obs) > 5:
            # Pokud před -kem je "í", pravděpodobně -ík (Kubíkem → Kubík)
            if obs[-4] in ('í', 'ý'):
                return obs[:-2]  # Kubíkem → Kubík (odstraň -em, nechej Kubík)
            else:
                return obs[:-3] + 'ek'  # Práškem → Prášek
        # Běžný instrumentál (Novákem → Novák)
        elif not lo.endswith(('lem', 'rem', 'sem', 'šem', 'cem', 'dem', 'nem', 'bem', 'gem', 'chem')):
            return obs[:-2]

    # Genitiv -ka → -ek (Hájka → Hájek, Štefánka → Štefánek)
    if lo.endswith('ka') and len(obs) > 4:
        # Kontrola: ne pro ženská příjmení jako "Procházková"
        if not lo.endswith(('ková', 'ská', 'ná')):
            return obs[:-2] + 'ek'

    return obs

def normalize_person_name(full_name):
    """
    Normalizuje celé jméno osoby do nominativu (1. pádu).
    Pokud je jméno ve tvaru "Křestní Příjmení", normalizuje obě části.
    """
    if not full_name:
        return full_name

    full_name = full_name.strip()

    # Detekuj, jestli je to tag (začíná [[) - ty neupravujeme
    if full_name.startswith('[['):
        return full_name

    # Rozděl jméno na části
    parts = full_name.split()

    if len(parts) == 0:
        return full_name
    elif len(parts) == 1:
        # Pouze jedno slovo - může to být křestní jméno nebo příjmení
        # Zkusíme nejprve jako křestní jméno, pak jako příjmení
        nom_first = infer_first_name_nominative(parts[0])
        if nom_first != parts[0]:
            return nom_first
        return infer_surname_nominative(parts[0])
    elif len(parts) == 2:
        # Standardní formát: Křestní Příjmení
        first_nom = infer_first_name_nominative(parts[0])
        last_nom = infer_surname_nominative(parts[1])
        return f"{first_nom} {last_nom}"
    else:
        # Více než 2 části (např. více křestních jmen)
        # Normalizuj první část jako křestní jméno, poslední jako příjmení
        normalized_parts = []
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Poslední část = příjmení
                normalized_parts.append(infer_surname_nominative(part))
            else:
                # Ostatní části = křestní jména
                normalized_parts.append(infer_first_name_nominative(part))
        return " ".join(normalized_parts)


print("=" * 80)
print("DEANONYMIZÁTOR - LOKÁLNÍ DEBUG VERZE")
print("=" * 80)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# -------------------- Načtení knihovny jmen --------------------
print(">>> Načítám knihovnu českých jmen...")
try:
    # Pro Nuitka onefile - najdi cz_names.v1.json v ruznych lokacich
    script_dir = Path(__file__).parent if '__file__' in dir() else Path.cwd()
    exe_dir = Path(sys.executable).parent
    original_exe_dir = Path(os.path.abspath(sys.argv[0])).parent

    names_path = None
    for search_dir in [original_exe_dir, exe_dir, script_dir]:
        candidate = search_dir / "cz_names.v1.json"
        if candidate.exists():
            names_path = candidate
            break

    if names_path and names_path.exists():
        load_names_library(str(names_path))
        print(f"[OK] Knihovna jmen načtena: {len(CZECH_FIRST_NAMES)} jmen")
        print(f"  Cesta: {names_path}")
    else:
        print(f"[!] Knihovna jmen nenalezena!")
        print(f"  Hledano v: {original_exe_dir}, {exe_dir}, {script_dir}")
        print(f"  Normalizace bude fungovat s omezenými heuristikami")
except Exception as e:
    print(f"[!] Chyba při načítání knihovny jmen: {e}")
    print(f"  Normalizace bude fungovat s omezenými heuristikami")
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
        print("[OK] UTF-8 wrapping nastaven (TTY režim)")
    else:
        # Pipe režim (Electron) - encoding je už nastaven přes PYTHONIOENCODING
        print("[OK] Pipe režim detekován, encoding nastaven přes prostředí")
except Exception as e:
    print(f"[!] UTF-8 wrapping se nepodařilo nastavit: {e}")
    print(f"  Používám výchozí encoding: {sys.stdout.encoding}")
print()

# -------------------- Kontrola knihoven --------------------
print(">>> Kontroluji dostupnost knihoven...")
libraries_ok = True

try:
    from docx import Document
    print("[OK] python-docx je nainstalována")
except ImportError as e:
    print(f"[X] CHYBA: python-docx není nainstalována!")
    print(f"  Detaily: {e}")
    print(f"  Řešení: pip install python-docx")
    libraries_ok = False

try:
    import json
    print("[OK] json je dostupný (standardní knihovna)")
except ImportError as e:
    print(f"[X] CHYBA: json není dostupný: {e}")
    libraries_ok = False

print()

if not libraries_ok:
    print("=" * 80)
    print("KRITICKÁ CHYBA: Některé knihovny chybí!")
    print("=" * 80)
    input("\nStiskni ENTER pro ukončení...")
    sys.exit(1)


# -------------------- Helpers --------------------
def _load_txt_map_base_values(txt_path: Path):
    """
    Načte základní hodnoty PERSON entit z TXT mapy.
    Vrací dictionary: "PERSON_2" -> "Martin Havlíček"

    Formát TXT mapy:
    [[PERSON_2]]: Martin Havlíček
      - Havlíčkovi
    """
    base_values = {}

    if not txt_path.exists():
        return base_values

    print(f"  → Načítám TXT mapu: {txt_path}")

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            current_tag = None
            for line in f:
                line = line.rstrip('\n\r')

                # Řádek s hlavním tagem: [[PERSON_2]]: Martin Havlíček
                if line.startswith('[[PERSON_') and ']]:' in line:
                    match = re.match(r'\[\[(PERSON_\d+)\]\]:\s*(.+)', line)
                    if match:
                        tag = match.group(1)  # "PERSON_2"
                        value = match.group(2).strip()  # "Martin Havlíček"
                        base_values[tag] = value
                        current_tag = tag

                # Řádek s variantou (začíná "  - ")
                elif line.startswith('  - ') and current_tag:
                    # Ignorujeme varianty, máme už základní hodnotu
                    pass

                # Prázdný řádek nebo sekce
                elif not line.strip() or not line.startswith(' '):
                    current_tag = None

        print(f"  [OK] TXT mapa načtena: {len(base_values)} základních PERSON hodnot")
        return base_values

    except Exception as e:
        print(f"  [!] Chyba při načítání TXT mapy: {e}")
        return base_values


def _load_json(path: Path):
    """Načte JSON soubor s error handlingem"""
    print(f"  → Načítám JSON: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  [OK] JSON načten úspěšně")
        return data
    except FileNotFoundError:
        print(f"  [X] CHYBA: Soubor nenalezen!")
        raise
    except json.JSONDecodeError as e:
        print(f"  [X] CHYBA: Neplatný JSON formát!")
        print(f"    Řádek {e.lineno}, sloupec {e.colno}: {e.msg}")
        raise
    except Exception as e:
        print(f"  [X] CHYBA: {type(e).__name__}: {e}")
        raise


def _flatten_mapping(obj, txt_base_values=None):
    """
    Vytáhne mapping tag->original i z nestandardních JSON struktur.
    Podporuje:
    - { "[[TAG]]": "value", ... }
    - { "mapping": { ... } }
    - { "entities": [{"label": "[[TAG]]", "original": "value"}, ...] }
    - listy dvojic, nebo listy dictů
    - vnořené dicty (projde rekurzivně)

    DŮLEŽITÉ: Pro PERSON entity používá základní hodnotu pro všechny tagy.
    Např. pokud [[PERSON_2]]: "Martin Havlíček", všechny tagy PERSON_2*
    (včetně variant) budou mít hodnotu "Martin Havlíček".

    Args:
        obj: JSON objekt s entitami
        txt_base_values: dict s hodnotami z TXT mapy ("PERSON_2" -> "Martin Havlíček")
    """
    print("  → Parsuju strukturu mappingu...")
    flat = {}

    # Slovník pro základní hodnoty PERSON entit: "PERSON_2" -> "Martin Havlíček"
    # PREFERUJ hodnoty z TXT mapy, pokud jsou dostupné!
    person_base_values = txt_base_values.copy() if txt_base_values else {}

    def walk(x):
        if x is None:
            return

        # Nejčastější případ: dict
        if isinstance(x, dict):
            # Pokud je to náš formát s entities
            if "entities" in x and isinstance(x["entities"], list):
                print(f"    Nalezen formát 'entities' s {len(x['entities'])} záznamy")

                # FÁZE 1: Načti základní hodnoty pro PERSON entity (např. [[PERSON_2]])
                for entity in x["entities"]:
                    if isinstance(entity, dict) and "label" in entity and "original" in entity:
                        label = entity["label"]
                        original = entity["original"]
                        entity_type = entity.get("type", "")

                        if entity_type == "PERSON" and isinstance(label, str) and isinstance(original, str):
                            # Extrahuj base tag (např. "PERSON_2" z "[[PERSON_2]]")
                            match = re.match(r'\[\[(PERSON_\d+)\]\]$', label)
                            if match:
                                base_tag = match.group(1)  # "PERSON_2"
                                # DŮLEŽITÉ: Neprepisuj hodnoty z TXT mapy!
                                if base_tag not in person_base_values:
                                    # Normalizuj do nominativu a ulož jako základní hodnotu
                                    normalized = normalize_person_name(original)
                                    person_base_values[base_tag] = normalized

                # FÁZE 2: Vytvoř mapping pro všechny entity
                person_count = 0
                for entity in x["entities"]:
                    if isinstance(entity, dict) and "label" in entity and "original" in entity:
                        label = entity["label"]
                        original = entity["original"]
                        entity_type = entity.get("type", "")

                        if isinstance(label, str) and label.startswith("[[") and label.endswith("]]"):
                            # Použij pouze první výskyt, ignoruj duplicity
                            if label not in flat:
                                # NORMALIZACE: Pro PERSON entity použij základní hodnotu
                                if entity_type == "PERSON" and isinstance(original, str):
                                    # Zkus najít base tag (např. "PERSON_2" z "[[PERSON_2_gen]]")
                                    match = re.match(r'\[\[(PERSON_\d+)(?:_[a-z]+)?\]\]$', label)
                                    if match:
                                        base_tag = match.group(1)  # "PERSON_2"
                                        # Použij základní hodnotu, pokud existuje
                                        if base_tag in person_base_values:
                                            flat[label] = person_base_values[base_tag]
                                            if person_base_values[base_tag] != original:
                                                person_count += 1
                                        else:
                                            # Fallback: normalizuj aktuální hodnotu
                                            normalized = normalize_person_name(original)
                                            flat[label] = normalized
                                            if normalized != original:
                                                person_count += 1
                                    else:
                                        # Fallback pro nestandardní formát
                                        normalized = normalize_person_name(original)
                                        flat[label] = normalized
                                        if normalized != original:
                                            person_count += 1
                                else:
                                    flat[label] = str(original)

                if person_count > 0:
                    print(f"    Použito {len(person_base_values)} základních hodnot pro PERSON entity")
                    print(f"    Normalizováno/sjednoceno {person_count} variant")
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
    print(f"  [OK] Celkem nalezeno {len(flat)} tagů")

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
    print(f"  [OK] Seřazeno {len(items)} tagů")
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

    # Krok 0.5: Načtení TXT mapy (pokud existuje) pro správné základní hodnoty
    print(">>> KROK 0.5: Hledám TXT mapu pro správné základní hodnoty")
    txt_base_values = {}
    try:
        # Vytvoř cestu k TXT mapě (změní .json na .txt)
        txt_map_path = map_path.with_suffix('.txt')
        if txt_map_path.exists():
            txt_base_values = _load_txt_map_base_values(txt_map_path)
            if txt_base_values:
                print(f"  [OK] Použiji základní hodnoty z TXT mapy: {len(txt_base_values)} osob")
        else:
            print(f"  [!] TXT mapa nenalezena: {txt_map_path}")
            print(f"    Použiji hodnoty z JSON (mohou být ve skloněném tvaru)")
    except Exception as e:
        print(f"  [!] Chyba při načítání TXT mapy: {e}")
        print(f"    Použiji hodnoty z JSON")
    print()

    # Krok 1: Načtení mapy
    print(">>> KROK 1: Načítání JSON mapy")
    try:
        raw = _load_json(map_path)
        print(f"  [OK] JSON načten, velikost: {len(str(raw))} znaků")
    except Exception as e:
        print(f"\n[X][X][X] KRITICKÁ CHYBA při načítání mapy [X][X][X]")
        print(f"Typ chyby: {type(e).__name__}")
        print(f"Popis: {e}")
        return False

    # Krok 2: Parsování mapy
    print("\n>>> KROK 2: Parsování struktury mapy")
    try:
        mapping = _flatten_mapping(raw, txt_base_values)
        if not mapping:
            print("[X] CHYBA: Mapa je prázdná nebo nemá tagy ve formátu [[...]]")
            print("  Zkontroluj, jestli JSON obsahuje správnou strukturu")
            return False
    except Exception as e:
        print(f"\n[X][X][X] CHYBA při parsování mapy [X][X][X]")
        print(f"Typ chyby: {type(e).__name__}")
        print(f"Popis: {e}")
        return False

    # Krok 3: Příprava náhrad
    print("\n>>> KROK 3: Příprava náhrad")
    try:
        rep_items = _sorted_replacements(mapping)
    except Exception as e:
        print(f"[X] CHYBA při třídění tagů: {e}")
        return False

    # Krok 4: Načtení dokumentu
    print("\n>>> KROK 4: Načítání Word dokumentu")
    try:
        print(f"  → Otevírám: {anon_doc_path}")
        doc = Document(str(anon_doc_path))
        para_count = len(doc.paragraphs)
        table_count = len(doc.tables)
        print(f"  [OK] Dokument načten")
        print(f"    Počet odstavců: {para_count}")
        print(f"    Počet tabulek: {table_count}")
    except Exception as e:
        print(f"\n[X][X][X] CHYBA při načítání dokumentu [X][X][X]")
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

        print(f"  [OK] Hlavní odstavce hotovo")

        # Tables
        if table_count > 0:
            print("  → Zpracovávám tabulky...")
            for tbl_idx, tbl in enumerate(doc.tables):
                for row in tbl.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            total_changed_paras += _apply_to_paragraph(para, rep_items)
            print(f"  [OK] Tabulky hotovo")

        print(f"  [OK] Celkem změněno {total_changed_paras} odstavců")

    except Exception as e:
        print(f"\n[X][X][X] CHYBA při nahrazování textů [X][X][X]")
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

        # OPRAVA: Zkontroluj, jestli výstupní soubor už existuje a je zamčený
        if output_path.exists():
            print(f"  → Výstupní soubor už existuje, pokouším se ho smazat...")
            try:
                # Zkus smazat soubor (pokud je otevřený, selže)
                output_path.unlink()
                print(f"  [OK] Starý soubor úspěšně smazán")

            except PermissionError:
                # Soubor je pravděpodobně otevřený v jiném programu
                print(f"  [!] VAROVÁNÍ: Nelze smazat existující soubor (je otevřený?)")
                print(f"  → Ukládám do dočasného souboru...")

                # Ulož do dočasného souboru v TEMP složce
                temp_dir = Path(tempfile.gettempdir())
                temp_name = f"deanon_temp_{int(time.time())}_{output_path.name}"
                temp_path = temp_dir / temp_name

                print(f"  → Dočasná cesta: {temp_path}")
                doc.save(str(temp_path))
                print(f"  [OK] Dokument uložen do dočasného souboru")

                # Zkus přejmenovat dočasný soubor na finální název
                try:
                    # Zkus znovu smazat původní soubor
                    output_path.unlink()
                    # Přesuň dočasný soubor na finální místo
                    shutil.move(str(temp_path), str(output_path))
                    print(f"  [OK] Dočasný soubor přesunut na finální místo")
                except Exception as move_err:
                    print(f"  [!] Nepodařilo se přesunout na finální místo")
                    print(f"  → Výstupní soubor je dostupný zde: {temp_path}")
                    # Použij dočasnou cestu jako výstup
                    output_path = temp_path

            except Exception as del_err:
                print(f"  [!] VAROVÁNÍ: Chyba při mazání souboru: {del_err}")

        # Pokud soubor neexistuje nebo byl úspěšně smazán, ulož normálně
        if not output_path.exists():
            print(f"  → Ukládám do: {output_path}")
            doc.save(str(output_path))
            print(f"  [OK] Dokument úspěšně uložen")

        # Ověření existence
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"  [OK] Výstupní soubor existuje, velikost: {size:,} bytů")
        else:
            print(f"  [!] VAROVÁNÍ: Výstupní soubor nebyl vytvořen!")
            return False

    except PermissionError as perm_err:
        print(f"\n[X][X][X] CHYBA OPRÁVNĚNÍ při ukládání dokumentu [X][X][X]")
        print(f"Soubor: {output_path}")
        print(f"Popis: {perm_err}")
        print(f"\nMožné příčiny:")
        print(f"  1. Soubor je otevřený v MS Word nebo jiném programu")
        print(f"  2. Složka má omezená oprávnění pro zápis")
        print(f"  3. Antivirus blokuje přístup k souboru")
        print(f"\nŘešení:")
        print(f"  1. Zavři soubor '{output_path.name}' pokud je otevřený")
        print(f"  2. Zkontroluj oprávnění složky")
        print(f"  3. Zkus spustit program jako administrátor")
        import traceback
        print("\nStacktrace:")
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"\n[X][X][X] CHYBA při ukládání dokumentu [X][X][X]")
        print(f"Typ chyby: {type(e).__name__}")
        print(f"Popis: {e}")
        import traceback
        print("\nStacktrace:")
        traceback.print_exc()
        return False

    # Finální report
    print("\n" + "=" * 80)
    print("[OK][OK][OK] DEANONYMIZACE DOKONČENA ÚSPĚŠNĚ [OK][OK][OK]")
    print("=" * 80)
    print(f"Změněné odstavce: {total_changed_paras}")
    print(f"Celkem tagů v mapě: {len(mapping)}")
    print(f"Výstupní soubor: {output_path}")
    print("=" * 80)

    # Zaloguj statistiku
    try:
        from skryi_stats import log_deanonymization
        log_deanonymization()
    except Exception:
        pass

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
            print(f"[X] CHYBA: Anonymní dokument neexistuje!")
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

        print(f"[OK] Anonymní dokument existuje")
        print(f"  Velikost: {IN_DOC.stat().st_size:,} bytů")

        if not IN_MAP.exists():
            print(f"[X] CHYBA: Mapa neexistuje!")
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

        print(f"[OK] JSON mapa existuje")
        print(f"  Velikost: {IN_MAP.stat().st_size:,} bytů")
        print()

        # Spuštění deanonymizace
        ok = deanonymize_document(IN_DOC, IN_MAP, OUT_DOC)
        return ok

    except Exception as e:
        print("\n" + "=" * 80)
        print("[X][X][X] NEOČEKÁVANÁ CHYBA [X][X][X]")
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
    # V Electron aplikaci nebo watcher režimu nesmíme čekat na input!
    if sys.stdin.isatty() and not os.environ.get('NO_PAUSE'):
        input("\n>>> Stiskni ENTER pro ukončení...")

    sys.exit(0 if result else 1)
