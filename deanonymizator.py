#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Document Deanonymizer with Czech Name Normalization
Production version - converts names back to nominative case
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


# -------------------- Name Normalization to Nominative --------------------
# Global name library
CZECH_FIRST_NAMES = set()

def load_names_library(json_path="cz_names.v1.json"):
    """Load Czech names library from JSON"""
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
        CZECH_FIRST_NAMES = set()
        return set()

def remove_diacritics(text):
    """Remove diacritics from text"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def infer_first_name_nominative(name):
    """Convert first name to nominative case (1st case)"""
    if not name or len(name) < 2:
        return name

    obs = name.strip()
    lo = obs.lower()

    # SPECIAL CASE: Roberta can be genitive of Robert
    if lo == 'roberta':
        return 'Robert'

    # If name is directly in library, return it
    if lo in CZECH_FIRST_NAMES:
        return obs.capitalize()

    # Protected female names that end with typical declension endings
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

    # Genitive/Accusative male names: -a → remove (Ivana → Ivan, Roberta → Robert)
    if lo.endswith('a') and len(obs) > 3:
        base = obs[:-1]
        base_lo = base.lower()

        if base_lo in protected_male_names:
            return base.capitalize()
        if base_lo in CZECH_FIRST_NAMES:
            return base.capitalize()
        if CZECH_FIRST_NAMES and remove_diacritics(base_lo) in {remove_diacritics(n) for n in CZECH_FIRST_NAMES}:
            return base.capitalize()

    # Genitive -e → remove (Matěje → Matěj, Martine → Martin)
    if lo.endswith('e') and len(obs) > 3 and not lo.endswith(('ové', 'ice', 'ové')):
        base = obs[:-1]
        base_lo = base.lower()
        common_male_e = {'matěj', 'martin', 'bohumil', 'milan', 'dan', 'jan', 'stan'}
        if base_lo in common_male_e or base_lo in protected_male_names:
            return base.capitalize()
        if CZECH_FIRST_NAMES and base_lo in CZECH_FIRST_NAMES:
            return base.capitalize()

    # Dative -u → remove (Martinu → Martin, Pavlu → Pavel)
    if lo.endswith('u') and len(obs) > 3:
        base = obs[:-1]
        base_lo = base.lower()
        if base_lo in protected_male_names or (CZECH_FIRST_NAMES and base_lo in CZECH_FIRST_NAMES):
            return base.capitalize()

    # Genitive female names: -y → -a (Pavlíny → Pavlína)
    if lo.endswith('y') and len(obs) > 3:
        base = obs[:-1] + 'a'
        if base.lower() in CZECH_FIRST_NAMES or base.lower() in protected_female_names:
            return base

    # Instrumental female names: -ou → -a (Pavlínou → Pavlína)
    if lo.endswith('ou') and len(obs) > 4:
        base = obs[:-2] + 'a'
        if base.lower() in CZECH_FIRST_NAMES or base.lower() in protected_female_names:
            return base

    # Dative/Locative: -ovi → remove (Ivanovi → Ivan)
    if lo.endswith('ovi') and len(obs) > 5:
        base = obs[:-3]
        if CZECH_FIRST_NAMES and (base.lower() in CZECH_FIRST_NAMES or remove_diacritics(base.lower()) in {remove_diacritics(n) for n in CZECH_FIRST_NAMES}):
            return base.capitalize()

    # Instrumental male names: -em → remove (Ivanem → Ivan, Tomášem → Tomáš)
    if lo.endswith('em') and len(obs) > 4:
        base = obs[:-2]
        base_lo = base.lower()

        if base_lo.endswith(('slav', 'stav', 'měr')):
            return base.capitalize()

        if CZECH_FIRST_NAMES and (base_lo in CZECH_FIRST_NAMES or base_lo in protected_male_names or remove_diacritics(base_lo) in {remove_diacritics(n) for n in CZECH_FIRST_NAMES}):
            return base.capitalize()

    return obs

def infer_surname_nominative(surname):
    """Convert surname to nominative case (1st case)"""
    if not surname or len(surname) < 3:
        return surname

    obs = surname.strip()
    lo = obs.lower()

    # Protected surnames that end with declension patterns but are already nominative
    protected_surnames = {
        'procházka', 'němec', 'sedláček', 'kučera', 'fiala', 'dušek',
        'kozel', 'šembera', 'havel', 'pavel', 'klíma', 'svoboda',
        'valach', 'štrunc', 'jůza'
    }
    if lo in protected_surnames:
        return obs

    # Genitive/Dative/Locative female: -é → -á (Pokorné → Pokorná)
    if lo.endswith('é') and len(obs) > 3:
        return obs[:-1] + 'á'

    # Instrumental: -ou → can be -á (female) or -ý (male)
    if lo.endswith('ou') and len(obs) > 4:
        base = obs[:-2]
        if base.lower().endswith(('vrán', 'novot', 'malý', 'černý')):
            return base + 'ý'
        return obs[:-2] + 'á'

    # Genitive male: -y → -a (Klímy → Klíma)
    if lo.endswith('y') and len(obs) > 3:
        base_a = obs[:-1] + 'a'
        if base_a.lower() in protected_surnames:
            return base_a
        if obs[:-1].lower().endswith(('klím', 'dvořák', 'svobod')):
            return base_a
        return obs[:-1]

    # Genitive male: -a → remove (Nováka → Novák)
    if lo.endswith('a') and len(obs) > 3 and lo not in protected_surnames:
        base = obs[:-1]
        return base

    # Dative/Locative: -ovi → remove (Novákovi → Novák)
    if lo.endswith('ovi') and len(obs) > 5:
        base = obs[:-3]
        base_lo = base.lower()

        if base_lo.endswith('k') and len(base) > 2:
            before_k = base_lo[-2] if len(base_lo) >= 2 else ''
            if before_k in ('č', 'š', 'ž', 'ť', 'ď', 'ň', 'ř'):
                return base[:-1] + 'ek'

        return base

    # Instrumental male: -em → remove
    if lo.endswith('em') and len(obs) > 4:
        if lo.endswith(('alem', 'elem', 'olem', 'ilem')):
            return obs[:-2]
        if lo.endswith('kem') and len(obs) > 5:
            if obs[-4] in ('í', 'ý'):
                return obs[:-2]
            else:
                return obs[:-3] + 'ek'
        elif not lo.endswith(('lem', 'rem', 'sem', 'šem', 'cem', 'dem', 'nem', 'bem', 'gem', 'chem')):
            return obs[:-2]

    # Genitive -ka → -ek (Hájka → Hájek)
    if lo.endswith('ka') and len(obs) > 4:
        if not lo.endswith(('ková', 'ská', 'ná')):
            return obs[:-2] + 'ek'

    return obs

def normalize_person_name(full_name):
    """
    Normalize full person name to nominative case.
    Handles "FirstName Surname" format.
    """
    if not full_name:
        return full_name

    full_name = full_name.strip()

    # Don't modify tags
    if full_name.startswith('[['):
        return full_name

    parts = full_name.split()

    if len(parts) == 0:
        return full_name
    elif len(parts) == 1:
        nom_first = infer_first_name_nominative(parts[0])
        if nom_first != parts[0]:
            return nom_first
        return infer_surname_nominative(parts[0])
    elif len(parts) == 2:
        first_nom = infer_first_name_nominative(parts[0])
        last_nom = infer_surname_nominative(parts[1])
        return f"{first_nom} {last_nom}"
    else:
        # More than 2 parts (multiple first names)
        normalized_parts = []
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                normalized_parts.append(infer_surname_nominative(part))
            else:
                normalized_parts.append(infer_first_name_nominative(part))
        return " ".join(normalized_parts)


# -------------------- Load names library at startup --------------------
try:
    script_dir = Path(__file__).parent
    names_path = script_dir / "cz_names.v1.json"
    if names_path.exists():
        load_names_library(str(names_path))
except:
    pass


# -------------------- UTF-8 encoding --------------------
# Only set UTF-8 wrapping in TTY mode, not when piped from Electron
try:
    import io
    if sys.stdout.isatty():
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8")
except:
    pass


# -------------------- Helper functions --------------------
def _load_txt_map_base_values(txt_path: Path, verbose=False):
    """
    Load base values of PERSON entities from TXT map.
    Returns dictionary: "PERSON_2" -> "Martin Havlíček"
    """
    base_values = {}

    if not txt_path.exists():
        return base_values

    if verbose:
        print(f"Loading TXT map: {txt_path}")

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            current_tag = None
            for line in f:
                line = line.rstrip('\n\r')

                if line.startswith('[[PERSON_') and ']]:' in line:
                    match = re.match(r'\[\[(PERSON_\d+)\]\]:\s*(.+)', line)
                    if match:
                        tag = match.group(1)
                        value = match.group(2).strip()
                        base_values[tag] = value
                        current_tag = tag

                elif line.startswith('  - ') and current_tag:
                    pass

                elif not line.strip() or not line.startswith(' '):
                    current_tag = None

        if verbose:
            print(f"TXT map loaded: {len(base_values)} base PERSON values")
        return base_values

    except Exception as e:
        if verbose:
            print(f"Warning: Error loading TXT map: {e}")
        return base_values


def _load_json(path: Path, verbose=False):
    """Load JSON file with error handling"""
    if verbose:
        print(f"Loading JSON: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if verbose:
            print(f"JSON loaded successfully")
        return data
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}")
        raise
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format at line {e.lineno}, column {e.colno}: {e.msg}")
        raise
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        raise


def _flatten_mapping(obj, txt_base_values=None, verbose=False):
    """
    Extract tag->original mapping from various JSON structures.
    For PERSON entities, uses base value for all tag variants.
    """
    flat = {}
    person_base_values = txt_base_values.copy() if txt_base_values else {}

    def walk(x):
        if x is None:
            return

        if isinstance(x, dict):
            if "entities" in x and isinstance(x["entities"], list):
                # PHASE 1: Load base values for PERSON entities
                for entity in x["entities"]:
                    if isinstance(entity, dict) and "label" in entity and "original" in entity:
                        label = entity["label"]
                        original = entity["original"]
                        entity_type = entity.get("type", "")

                        if entity_type == "PERSON" and isinstance(label, str) and isinstance(original, str):
                            match = re.match(r'\[\[(PERSON_\d+)\]\]$', label)
                            if match:
                                base_tag = match.group(1)
                                if base_tag not in person_base_values:
                                    normalized = normalize_person_name(original)
                                    person_base_values[base_tag] = normalized

                # PHASE 2: Create mapping for all entities
                for entity in x["entities"]:
                    if isinstance(entity, dict) and "label" in entity and "original" in entity:
                        label = entity["label"]
                        original = entity["original"]
                        entity_type = entity.get("type", "")

                        if isinstance(label, str) and label.startswith("[[") and label.endswith("]]"):
                            if label not in flat:
                                if entity_type == "PERSON" and isinstance(original, str):
                                    match = re.match(r'\[\[(PERSON_\d+)(?:_[a-z]+)?\]\]$', label)
                                    if match:
                                        base_tag = match.group(1)
                                        if base_tag in person_base_values:
                                            flat[label] = person_base_values[base_tag]
                                        else:
                                            flat[label] = normalize_person_name(original)
                                    else:
                                        flat[label] = normalize_person_name(original)
                                else:
                                    flat[label] = str(original)
                return

            if "mapping" in x and isinstance(x["mapping"], (dict, list)):
                walk(x["mapping"])
                return

            for k, v in x.items():
                if isinstance(k, str) and k.startswith("[[") and k.endswith("]]"):
                    if isinstance(v, str):
                        flat[k] = v
                    else:
                        flat[k] = json.dumps(v, ensure_ascii=False)
                else:
                    walk(v)
            return

        if isinstance(x, list):
            for item in x:
                if isinstance(item, dict) and "label" in item and "original" in item:
                    label = item["label"]
                    original = item["original"]
                    if isinstance(label, str) and label.startswith("[[") and label.endswith("]]"):
                        if label not in flat:
                            flat[label] = str(original)
                elif isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], str):
                    k = item[0]
                    v = item[1]
                    if isinstance(k, str) and k.startswith("[[") and k.endswith("]]"):
                        flat[k] = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                else:
                    walk(item)
            return

    walk(obj)

    if verbose:
        print(f"Found {len(flat)} tags in mapping")

    return flat


def _sorted_replacements(mapping: dict):
    """Sort tags by length (longer first) to avoid partial replacements"""
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
    Apply replacements to paragraph, handling tags split across runs.
    """
    if not para.runs:
        return 0

    full = "".join(r.text for r in para.runs)
    if not full.strip():
        return 0

    new_text, changed = _replace_all(full, rep_items)
    if not changed:
        return 0

    para.runs[0].text = new_text
    for r in para.runs[1:]:
        r.text = ""

    return 1


def deanonymize_document(anon_doc_path: Path, map_path: Path, output_path: Path, verbose: bool = False) -> bool:
    """
    Deanonymize document using mapping file.

    Args:
        anon_doc_path: Path to anonymized document
        map_path: Path to JSON mapping file
        output_path: Path for deanonymized output
        verbose: Enable detailed logging

    Returns:
        True if successful, False otherwise
    """

    if verbose:
        print("=" * 80)
        print("DEANONYMIZATION")
        print("=" * 80)
        print(f"Input:  {anon_doc_path}")
        print(f"Map:    {map_path}")
        print(f"Output: {output_path}")
        print()

    # Load TXT map for correct base values (if available)
    txt_base_values = {}
    try:
        txt_map_path = map_path.with_suffix('.txt')
        if txt_map_path.exists():
            txt_base_values = _load_txt_map_base_values(txt_map_path, verbose)
            if verbose and txt_base_values:
                print(f"Using base values from TXT map: {len(txt_base_values)} persons")
    except Exception as e:
        if verbose:
            print(f"Warning: Could not load TXT map: {e}")

    # Load JSON map
    try:
        raw = _load_json(map_path, verbose)
    except Exception as e:
        print(f"ERROR: Failed to load mapping file: {e}")
        return False

    # Parse map structure
    try:
        mapping = _flatten_mapping(raw, txt_base_values, verbose)
        if not mapping:
            print("ERROR: Map is empty or has no tags in [[...]] format")
            return False
    except Exception as e:
        print(f"ERROR: Failed to parse mapping: {e}")
        return False

    # Prepare replacements
    rep_items = _sorted_replacements(mapping)

    # Load document
    try:
        if verbose:
            print(f"Loading document: {anon_doc_path}")
        doc = Document(str(anon_doc_path))
        if verbose:
            print(f"Paragraphs: {len(doc.paragraphs)}, Tables: {len(doc.tables)}")
    except Exception as e:
        print(f"ERROR: Failed to load document: {e}")
        return False

    # Apply replacements
    if verbose:
        print("Applying replacements...")

    total_changed_paras = 0

    try:
        # Main paragraphs
        for para in doc.paragraphs:
            total_changed_paras += _apply_to_paragraph(para, rep_items)

        # Tables
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        total_changed_paras += _apply_to_paragraph(para, rep_items)

        if verbose:
            print(f"Changed {total_changed_paras} paragraphs")

    except Exception as e:
        print(f"ERROR: Failed during text replacement: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Save document
    try:
        if verbose:
            print(f"Saving to: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle locked files
        if output_path.exists():
            try:
                output_path.unlink()
            except PermissionError:
                # File is locked, save to temp
                temp_dir = Path(tempfile.gettempdir())
                temp_name = f"deanon_temp_{int(time.time())}_{output_path.name}"
                temp_path = temp_dir / temp_name

                doc.save(str(temp_path))

                try:
                    output_path.unlink()
                    shutil.move(str(temp_path), str(output_path))
                except:
                    print(f"Warning: Saved to temporary location: {temp_path}")
                    output_path = temp_path

        if not output_path.exists():
            doc.save(str(output_path))

        if output_path.exists():
            size = output_path.stat().st_size
            if verbose:
                print(f"Saved successfully: {size:,} bytes")
        else:
            print("ERROR: Output file was not created")
            return False

    except PermissionError as perm_err:
        print(f"ERROR: Permission denied: {perm_err}")
        print(f"File may be open in another program: {output_path.name}")
        return False

    except Exception as e:
        print(f"ERROR: Failed to save document: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Success
    if verbose:
        print("=" * 80)
        print("DEANONYMIZATION COMPLETE")
        print("=" * 80)
        print(f"Changed paragraphs: {total_changed_paras}")
        print(f"Total tags in map: {len(mapping)}")
        print(f"Output file: {output_path}")
        print("=" * 80)
    else:
        print("DEANONYMIZATION COMPLETE")
        print(f"Output: {output_path}")

    return True


# -------------------- CLI --------------------
def main():
    args = sys.argv[1:]

    # Defaults
    IN_DOC = Path("smlouva_anon.docx")
    IN_MAP = Path("smlouva_map.json")
    OUT_DOC = Path("smlouva_deanon.docx")
    VERBOSE = False

    # Auto-detect from single argument
    if len(args) == 1 and not args[0].startswith("--"):
        input_file = Path(args[0])
        stem = input_file.stem
        parent = input_file.parent

        if stem.endswith("_anon"):
            base = stem[:-5]
            map_name = f"{base}_map.json"
            output_name = f"{base}_deanon.docx"
        else:
            base = stem
            map_name = f"{base}_map.json"
            output_name = f"{base}_deanon.docx"

        IN_DOC = input_file
        IN_MAP = parent / map_name
        OUT_DOC = parent / output_name

    # 3 positional arguments
    elif len(args) >= 3 and not args[0].startswith("--"):
        IN_DOC = Path(args[0])
        IN_MAP = Path(args[1])
        OUT_DOC = Path(args[2])
    else:
        # Flag-based arguments
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

        if "--verbose" in args or "-v" in args:
            VERBOSE = True

    IN_DOC = IN_DOC.resolve()
    IN_MAP = IN_MAP.resolve()
    OUT_DOC = OUT_DOC.resolve()

    # Validate input files
    if not IN_DOC.exists():
        print(f"ERROR: Input document not found: {IN_DOC}")
        print(f"Current directory: {os.getcwd()}")
        sys.exit(1)

    if not IN_MAP.exists():
        print(f"ERROR: Map file not found: {IN_MAP}")
        print(f"Current directory: {os.getcwd()}")
        sys.exit(1)

    # Run deanonymization
    ok = deanonymize_document(IN_DOC, IN_MAP, OUT_DOC, verbose=VERBOSE)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
