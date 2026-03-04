#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# audit.py – GDPR/PII audit anonymizovaných dokumentů
#
# Funguje jako náš “engine”:
# - kontroluje POUZE anonymizovaný dokument (.docx/.txt)
# - mapa (.txt/.json) slouží jen pro kontrolu tagů (žádný audit PII v mapě)
# - detekuje jen MUST-HAVE GDPR PII v TEXTU:
#     * IBAN
#     * čísla platebních karet (Luhn)
#     * e-maily
#     * rodná čísla / birth id
#     * telefony
#     * SPZ/RZ (s kontextem)
#
# Použití:
#   python audit.py --anon smlouva13_anon.docx --map smlouva13_map.txt
#
# Nebo drag&drop:
#   přetáhni 1–2 soubory na audit.py (anonymní doc + mapu)

import re
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set, Optional

# ================== I/O ==================

def load_text_from_docx_or_txt(path: Path) -> str:
    """Načte text z .docx nebo .txt souboru."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Soubor neexistuje: {p}")
    if p.suffix.lower() == ".docx":
        try:
            from docx import Document  # pip install python-docx
        except Exception as e:
            raise RuntimeError(
                "Chybí balíček 'python-docx'. Nainstaluj: python -m pip install python-docx"
            ) from e
        doc = Document(str(p))
        return "\n".join(par.text for par in doc.paragraphs)
    else:
        return p.read_text(encoding="utf-8", errors="ignore")


def parse_map_file(path: Path) -> Dict[str, Dict[str, str]]:
    """
    Podporované mapy:

    JSON:
    {
      "OSOBY": {"[[PERSON_1]]":"Jan Novák", ...},
      "ADDRESS": {"[[ADDRESS_1]]":"...", ...},
      ...
    }

    TXT (sekční):
      OSOBY
      [[PERSON_1]]: Jan Novák
      [[PERSON_2]]: ...

      ADDRESS
      [[ADDRESS_1]]: ...
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Mapa neexistuje: {p}")

    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        norm: Dict[str, Dict[str, str]] = {}
        for section, pairs in data.items():
            section_map: Dict[str, str] = {}
            if isinstance(pairs, dict):
                for k, v in pairs.items():
                    tag = k if str(k).startswith("[[") else f"[[{k}]]"
                    section_map[tag] = str(v)
            norm[section] = section_map
        return norm

    # TXT parser
    raw = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    sections: Dict[str, Dict[str, str]] = {}
    current = None
    for ln in raw:
        line = ln.strip()
        if not line:
            continue
        # sekce velkými písmeny bez dvojtečky
        if re.match(r"^[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ ]{3,}$", line) and ":" not in line and "[[" not in line:
            current = line
            sections.setdefault(current, {})
            continue
        m = re.match(r"(\[\[[A-Z_]+\d+\]\])\s*:\s*(.*)$", line)
        if m and current:
            tag = m.group(1).strip()
            val = m.group(2).strip()
            sections[current][tag] = val
    return sections


def extract_tags_from_text(text: str) -> Set[str]:
    """Najde všechny [[TAG_X]] v textu a vrátí je bez vnějších [[ ]]."""
    return set(re.findall(r"\[\[([A-Z_]+\d+)\]\]", text))


def pick_file_dialog(title: str, filetypes: list) -> Optional[Path]:
    """Jednoduchý file dialog (pokud existuje tkinter)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None
    root = tk.Tk()
    root.withdraw()
    fp = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return Path(fp) if fp else None

# ================== Detekce plaintext PII v anonymizovaném TEXTU ==================

IBAN_RE   = re.compile(r"\b(CZ\d{2}(?:\s?\d{4}){5})\b")
CARD_RE   = re.compile(r"\b(?:\d[\s-]?){13,19}\b")
EMAIL_RE  = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Český rodný / birth id: YYMMDD/XXX(X) nebo podobné
BIRTH_RE  = re.compile(r"\b\d{2}[01]\d[0-3]\d/?\d{3,4}\b")
PHONE_RE  = re.compile(r"(?<!\d)(\+?\d{3}[\s-]?\d{3}[\s-]?\d{3,4})(?!\d)")


def in_tag_context(text: str, start: int, end: int) -> bool:
    """
    Je daný úsek uvnitř [[TAG ... ]]? (tj. patří k anonymizovanému tagu, ne k plaintextu)
    Stačí hrubá kontrola malého okolí.
    """
    before = text[max(0, start-8):start]
    after = text[end:min(len(text), end+8)]
    return ("[[" in before) and ("]]" in after)


def detect_plain_iban(text: str) -> List[Tuple[str, int]]:
    out = []
    for m in IBAN_RE.finditer(text):
        if not in_tag_context(text, m.start(), m.end()):
            line = text[:m.start()].count("\n") + 1
            out.append((m.group(1), line))
    return out


def luhn_check(number: str) -> bool:
    s = re.sub(r"[\s-]", "", number)
    if not (s.isdigit() and 13 <= len(s) <= 19):
        return False
    digits = list(map(int, s))
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def detect_plain_cards(text: str) -> List[Tuple[str, int]]:
    out = []
    for m in CARD_RE.finditer(text):
        if in_tag_context(text, m.start(), m.end()):
            continue
        raw = m.group()
        if luhn_check(raw):
            line = text[:m.start()].count("\n") + 1
            out.append((raw, line))
    return out


def detect_plain_emails(text: str) -> List[Tuple[str, int]]:
    out = []
    for m in EMAIL_RE.finditer(text):
        if not in_tag_context(text, m.start(), m.end()):
            line = text[:m.start()].count("\n") + 1
            out.append((m.group(), line))
    return out


def detect_plain_birth_ids(text: str) -> List[Tuple[str, int]]:
    out = []
    for m in BIRTH_RE.finditer(text):
        if not in_tag_context(text, m.start(), m.end()):
            line = text[:m.start()].count("\n") + 1
            out.append((m.group(), line))
    return out


def detect_plain_phones(text: str) -> List[Tuple[str, int]]:
    out = []
    for m in PHONE_RE.finditer(text):
        if in_tag_context(text, m.start(), m.end()):
            continue
        val = m.group(1)
        # vyřadíme příliš dlouhé stringy (část IBANu apod.)
        if len(re.sub(r"\D", "", val)) <= 11:
            line = text[:m.start()].count("\n") + 1
            out.append((val, line))
    return out


# ===== SPZ/RZ (jen pokud kontext jasně říká, že jde o registrační značku) =====

CZ_PLATE_PATTERNS = [
    re.compile(r"\b[1-9][A-Z]{2}\s?\d{4}\b"),  # 1AB 2345
    re.compile(r"\b[1-9][A-Z]\d\s?\d{4}\b"),   # 1A3 4567
]

PLATE_CONTEXT_KEYWORDS = [
    "spz", "rz", "registrační zna", "registrační čí", "evidenční číslo", "ev. číslo"
]


def _has_plate_context(text: str, start: int, end: int) -> bool:
    window = text[max(0, start-24):min(len(text), end+24)].lower()
    return any(k in window for k in PLATE_CONTEXT_KEYWORDS)


def detect_plain_license_plates(text: str) -> List[Tuple[str, int]]:
    """Vrací SPZ/RZ v textu, které nejsou uvnitř tagu a mají jasný SPZ kontext."""
    out: List[Tuple[str, int]] = []
    for pat in CZ_PLATE_PATTERNS:
        for m in pat.finditer(text):
            if in_tag_context(text, m.start(), m.end()):
                continue
            plate = m.group().strip()
            line = text[:m.start()].count("\n") + 1
            if _has_plate_context(text, m.start(), m.end()):
                out.append((plate, line))
    return out

# ================== Map & coverage ==================

def map_to_tagset(map_data: Dict[str, Dict[str, str]]) -> Set[str]:
    """Všechny tagy z mapy (bez vnějších [[ ]])."""
    tags: Set[str] = set()
    for _, kv in map_data.items():
        for t in kv.keys():
            t2 = t if str(t).startswith("[[") else f"[[{t}]]"
            tags.add(re.sub(r"^\[\[|\]\]$", "", t2))
    # fallback pro případ flat JSONu
    if not tags and isinstance(map_data, dict):
        for k, v in map_data.items():
            if isinstance(v, str):
                tags.add(re.sub(r"^\[\[|\]\]$", "", k if str(k).startswith("[[") else f"[[{k}]]"))
    return tags


def tag_values_flat(map_data: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """Mapu zploští: TAG -> hodnota."""
    flat: Dict[str, str] = {}
    for _, kv in map_data.items():
        for t, v in kv.items():
            key = re.sub(r"^\[\[|\]\]$", "", t)
            flat[key] = str(v)
    return flat

# ================== Scoring ==================

def calculate_score(hard_fails: int, majors: int, minors: int, positives: int) -> Tuple[float, str]:
    score = 10.0
    score -= 3.0 * hard_fails
    score -= 1.0 * majors
    score -= 0.4 * minors
    score += min(0.5, 0.25 * positives)
    score = round(max(0.0, min(10.0, score)), 1)
    verdict = "GO" if (score >= 9.3 and hard_fails == 0) else "NO-GO"
    return score, verdict

# ================== Audit ==================

def looks_like_map_file(path: Path) -> bool:
    """Jednoduchý test, jestli soubor nevypadá jako mapa."""
    if "map" in path.stem.lower():
        return True
    if path.suffix.lower() == ".txt":
        text = path.read_text(encoding="utf-8", errors="ignore")
        # heuristika: obsahuje sekce OSOBY/ADDRESS + [[PERSON_1]]:
        if "OSOBY" in text and "[[PERSON_1]]" in text:
            return True
    return False


def run_audit(anon_path: Path, map_path: Path, test_mode: bool=False) -> Dict[str, Any]:
    # Bezpečnost: nespouštět audit na mapě jako na dokumentu
    if looks_like_map_file(anon_path):
        raise RuntimeError(
            f"Soubor '{anon_path.name}' vypadá jako MAPA, ne anonymizovaný dokument.\n"
            f"Použij ho jako --map a jako --anon zadej smlouvu (_anon.docx)."
        )

    doc_text = load_text_from_docx_or_txt(anon_path)
    map_data = parse_map_file(map_path)

    hard_fails: List[Dict[str, str]] = []
    majors: List[Dict[str, str]] = []
    minors: List[Dict[str, str]] = []
    positives: List[str] = []

    # ---- 1) MUST-HAVE GDPR PII v ANONYMIZOVANÉM TEXTU → HARD FAIL ----

    for iban, line in detect_plain_iban(doc_text):
        hard_fails.append({"type": "any_plain_IBAN", "details": f"Line {line}: {iban}"})

    for card, line in detect_plain_cards(doc_text):
        masked = re.sub(r"\d", "X", card[:-4]) + card[-4:]
        hard_fails.append({"type": "any_plain_CARD", "details": f"Line {line}: {masked}"})

    for email, line in detect_plain_emails(doc_text):
        hard_fails.append({"type": "any_plain_EMAIL", "details": f"Line {line}: {email}"})

    for rc, line in detect_plain_birth_ids(doc_text):
        hard_fails.append({"type": "any_plain_BIRTH_ID", "details": f"Line {line}: {rc}"})

    for ph, line in detect_plain_phones(doc_text):
        hard_fails.append({"type": "any_plain_PHONE", "details": f"Line {line}: {ph}"})

    for plate, line in detect_plain_license_plates(doc_text):
        hard_fails.append({"type": "any_plain_LICENSE_PLATE", "details": f"Line {line}: {plate}"})

    # ---- 2) TAG & MAP sanity (HARD FAILS) ----

    text_tags = extract_tags_from_text(doc_text)
    map_tags  = map_to_tagset(map_data)
    flat_map  = tag_values_flat(map_data)

    # a) Tag v textu chybí v mapě
    missing = sorted(text_tags - map_tags)
    for tag in missing:
        hard_fails.append({"type": "tag_in_text_missing_in_map", "details": tag})

    # b) Mapa má prázdné hodnoty nebo REDACTED (v test_mode)
    for tag, val in flat_map.items():
        if val is None or str(val).strip() == "":
            hard_fails.append({"type": "map_value_missing_or_empty", "details": tag})
        if test_mode and "REDACTED" in str(val).upper():
            hard_fails.append({"type": "map_value_contains_redacted", "details": tag})

    # ---- 3) Pozitivní signály (žádný plaintext PII) → malé + body ----
    if not detect_plain_iban(doc_text):
        positives.append("no_plain_IBAN")
    if not detect_plain_cards(doc_text):
        positives.append("no_plain_CARD")
    if not detect_plain_emails(doc_text):
        positives.append("no_plain_EMAIL")
    if not detect_plain_birth_ids(doc_text):
        positives.append("no_plain_BIRTH_ID")
    if not detect_plain_phones(doc_text):
        positives.append("no_plain_PHONE")
    if not detect_plain_license_plates(doc_text):
        positives.append("no_plain_LICENSE_PLATE")

    # max +0.5
    positives = positives[:2]

    score, verdict = calculate_score(len(hard_fails), len(majors), len(minors), len(positives))

    return {
        "score": score,
        "verdict": verdict,
        "hard_fails": hard_fails,
        "majors": majors,
        "minors": minors,
        "positives": positives,
        "breakdown": {
            "hard_fails_count": len(hard_fails),
            "majors_count": len(majors),
            "minors_count": len(minors),
            "positives_count": len(positives),
            "hard_fails_penalty": round(3.0 * len(hard_fails), 1),
            "majors_penalty": round(1.0 * len(majors), 1),
            "minors_penalty": round(0.4 * len(minors), 1),
            "positives_bonus": round(min(0.5, 0.25 * len(positives)), 1),
        }
    }


def render_report_text(result: Dict[str, Any], anon_path: Path, map_path: Path) -> str:
    b = result["breakdown"]
    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("UNIFIED GDPR/PII AUDIT REPORT")
    lines.append("=" * 78)
    lines.append(f"Dokument: {anon_path.name}")
    lines.append(f"Mapa:     {map_path.name}")
    lines.append("")
    lines.append(f"SCORE:   {result['score']}/10")
    lines.append(f"VERDIKT: {result['verdict']}")
    lines.append("")
    lines.append("BREAKDOWN:")
    total_pen = b['hard_fails_penalty'] + b['majors_penalty'] + b['minors_penalty']
    lines.append(f"  Hard Fails: {b['hard_fails_count']} × -3.0 = -{b['hard_fails_penalty']}")
    lines.append(f"  Majors:     {b['majors_count']} × -1.0 = -{b['majors_penalty']}")
    lines.append(f"  Minors:     {b['minors_count']} × -0.4 = -{b['minors_penalty']}")
    lines.append(f"  Bonusy:     {b['positives_count']} → +{b['positives_bonus']}")
    lines.append(f"  ─────────────────────────────────────────────")
    lines.append(f"  TOTAL: 10.0 - {total_pen} + {b['positives_bonus']} = {result['score']}")
    if result["hard_fails"]:
        lines.append("")
        lines.append(f"HARD FAILS ({b['hard_fails_count']}):")
        for i, hf in enumerate(result["hard_fails"][:80], 1):
            lines.append(f"  {i}. {hf['type']}: {hf.get('details','')}")
        if b['hard_fails_count'] > 80:
            lines.append(f"  ... +{b['hard_fails_count']-80} dalších")
    if result["majors"]:
        lines.append("")
        lines.append(f"MAJORS ({b['majors_count']}):")
        for i, m in enumerate(result["majors"][:40], 1):
            lines.append(f"  {i}. {m['type']}: {m.get('details','')}")
    if result["minors"]:
        lines.append("")
        lines.append(f"MINORS ({b['minors_count']}):")
        for i, m in enumerate(result["minors"][:40], 1):
            lines.append(f"  {i}. {m['type']}: {m.get('details','')}")
    return "\n".join(lines)

# ================== UX (argparse / drag&drop) ==================

def resolve_inputs_dragdrop() -> tuple[Path, Path, bool, bool, Optional[Path]]:
    """
    Vrací (anon_path, map_path, test_mode, no_pause, out_path).
    Podporuje:
      - parametry --anon/--map/--out
      - přetažené soubory (argv bez přepínačů)
      - file dialog pro doplnění chybějících
    """
    ap = argparse.ArgumentParser(description="GDPR/PII Audit anonymizovaných dokumentů")
    ap.add_argument("--anon", help="anonymizovaný dokument (.docx/.txt)")
    ap.add_argument("--map", help="mapa (.txt/.json)")
    ap.add_argument("--out", help="cesta k výstupnímu TXT reportu")
    ap.add_argument("--test-mode", action="store_true", help="přísnější kontrola mapy (žádné REDACTED)")
    ap.add_argument("--no-pause", action="store_true", help="nečekat na Enter na konci")
    args, unknown = ap.parse_known_args()

    anon_path = Path(args.anon) if args.anon else None
    map_path  = Path(args.map) if args.map else None
    test_mode = bool(args.test_mode)
    no_pause  = bool(args.no_pause)
    out_path  = Path(args.out) if args.out else None

    # přetažené soubory (bez přepínačů)
    files = [Path(u) for u in unknown if Path(u).exists()]

    for f in files:
        ext = f.suffix.lower()
        if not anon_path and ext in {".docx", ".txt"}:
            anon_path = f
        elif not map_path and ext in {".txt", ".json"}:
            map_path = f

    if not anon_path:
        anon_path = pick_file_dialog(
            "Vyber anonymizovaný dokument (.docx/.txt)",
            [("DOCX/TXT", "*.docx *.txt"), ("DOCX", "*.docx"), ("TXT", "*.txt"), ("All files", "*.*")]
        )
    if not map_path:
        map_path = pick_file_dialog(
            "Vyber mapu (.txt/.json)",
            [("TXT/JSON", "*.txt *.json"), ("TXT", "*.txt"), ("JSON", "*.json"), ("All files", "*.*")]
        )

    if not anon_path or not map_path:
        raise SystemExit("Nebyl vybrán anonymizovaný dokument a/nebo mapa.")

    return anon_path, map_path, test_mode, no_pause, out_path

# ================== main ==================

def main():
    try:
        anon_path, map_path, test_mode, no_pause, out_path = resolve_inputs_dragdrop()
        result = run_audit(anon_path, map_path, test_mode=test_mode)
        report = render_report_text(result, anon_path, map_path)

        # výstupní soubor
        if out_path:
            out_file = out_path
        else:
            out_dir = anon_path.parent
            out_name = f"AUDIT_{anon_path.stem}.txt"
            out_file = out_dir / out_name

        out_file.write_text(report, encoding="utf-8")
        print(report)
        print("\nUloženo jako:", out_file)

        exit_code = 0 if result["verdict"] == "GO" else 1

    except Exception as e:
        print("\n[ERROR]")
        print(e)
        exit_code = 2

    finally:
        if "--no-pause" not in sys.argv:
            try:
                input("\nHotovo. Stiskni Enter pro zavření…")
            except Exception:
                pass
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
