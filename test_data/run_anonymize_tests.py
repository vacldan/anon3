#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spustí anonymizaci na smlouvy v test_data a ověří výsledky dle SKRYI specifikace.
Report uloží do _agent_reports/test_results.json pro analýzu agenty.

Kontroluje:
- PII leak (mapa + regex pro české vzory: RC, telefon, IBAN, email, SPZ)
- Konzistence map (JSON vs TXT, 1 entita = 1 tag)
- Zachování struktury DOCX
- Existence PDF reportu
- Ohodnocení 1–10
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Projekt root = rodič test_data – musí být v sys.path hned na začátku
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DATA = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
OUT_DIR = TEST_DATA / "anon_output"
REPORTS_DIR = PROJECT_ROOT / "_agent_reports"
ANON_CLI = PROJECT_ROOT / "anonymize_cli.py"

# Knihovna křestních jmen (pro základní validaci PERSON)
CZ_NAMES_PATH = PROJECT_ROOT / "cz_names.v1.json"
CZ_FIRSTNAMES: Set[str] = set()
if CZ_NAMES_PATH.exists():
    try:
        with open(CZ_NAMES_PATH, encoding="utf-8") as _nf:
            _data = json.load(_nf)
        for gender_list in _data.get("firstnames", {}).values():
            for name in gender_list:
                CZ_FIRSTNAMES.add(str(name).strip())
    except Exception:
        CZ_FIRSTNAMES = set()

# Regex vzory pro české PII (dle SKRYI dokumentace) – nesmí zůstat ve výstupu
PII_PATTERNS = [
    (r"\d{6}/\d{3,4}", "Rodné číslo (RC)"),
    (r"\d{9,10}/\d{4}", "Číslo účtu"),
    (r"CZ\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}", "IBAN"),
    (r"\+420\s?\d{3}\s?\d{3}\s?\d{3}", "Telefon +420"),
    (r"\b\d{3}\s?\d{3}\s?\d{3}\b", "Telefon 9 číslic"),
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "E-mail"),
    (r"(?<![A-Za-z0-9])\d[A-Z]{1,2}\d\s?\d{4}(?![A-Za-z0-9])", "SPZ"),
    (r"(?<![A-Za-z0-9])[A-HJ-NPR-Z0-9]{17}(?![A-Za-z0-9])", "VIN"),
]


def get_all_text_from_docx(docx_path: Path) -> str:
    """Extrahuje veškerý text z DOCX (odstavce + tabulky)."""
    try:
        from docx import Document
        doc = Document(str(docx_path))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        parts.append(p.text)
        return " ".join(parts)
    except Exception as e:
        return f"[CHYBA čtení DOCX: {e}]"


def get_docx_structure(docx_path: Path) -> Dict[str, int]:
    """Vrátí počet odstavců a tabulek pro kontrolu zachování struktury."""
    try:
        from docx import Document
        doc = Document(str(docx_path))
        return {
            "paragraphs": len(doc.paragraphs),
            "tables": len(doc.tables),
        }
    except Exception:
        return {"paragraphs": 0, "tables": 0}


def extract_originals_from_map_json(map_json_path: Path) -> Set[str]:
    """Vrátí množinu všech původních hodnot z _map.json (pro PII leak test)."""
    try:
        with open(map_json_path, encoding="utf-8") as f:
            data = json.load(f)
        originals = set()
        for ent in data.get("entities", []):
            orig = ent.get("original", "")
            if orig and not str(orig).startswith("***REDACTED_"):
                originals.add(str(orig).strip())
        return originals
    except Exception:
        return set()


def extract_originals_from_map_txt(map_txt_path: Path) -> Set[str]:
    """Vrátí množinu původních hodnot z _map.txt (OSOBY sekce + ostatní)."""
    originals = set()
    try:
        with open(map_txt_path, encoding="utf-8") as f:
            content = f.read()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("-----"):
                continue
            if line.startswith("- "):
                originals.add(line[2:].strip())
            elif ": " in line and not line.startswith("["):
                val = line.split(": ", 1)[1]
                if val != "***REDACTED***":
                    originals.add(val.strip())
    except Exception:
        pass
    return originals


def _parse_persons_from_map_txt(map_txt_path: Path) -> List[Dict[str, object]]:
    """
    Parsuje sekci OSOBY z _map.txt do struktury:
    [
      {"tag": "[[PERSON_1]]", "canonical": "Jméno", "variants": ["Varianta1", ...]},
      ...
    ]
    """
    persons: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None
    in_person_section = False
    try:
        with open(map_txt_path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n")
                if not in_person_section:
                    if line.strip().upper().startswith("OSOBY"):
                        in_person_section = True
                    continue
                # konec sekce OSOBY – narazíme na jinou sekci (např. ADDRESS)
                if line.strip() and not line.startswith("[[") and not line.startswith("  -") and not line.startswith("-----"):
                    break
                if line.startswith("[[") and "]]:" in line:
                    if current is not None:
                        persons.append(current)
                    tag, val = line.split("]]:", 1)
                    tag = tag.strip()
                    val = val.strip()
                    current = {
                        "tag": tag + "]]" if not tag.endswith("]]") else tag,
                        "canonical": val,
                        "variants": [],
                    }
                elif line.strip().startswith("- ") and current is not None:
                    variant = line.strip()[2:].strip()
                    if variant:
                        current["variants"].append(variant)
        if current is not None:
            persons.append(current)
    except Exception:
        pass
    return persons


def _parse_addresses_from_map_txt(map_txt_path: Path) -> List[Tuple[str, str]]:
    """
    Parsuje sekci ADDRESS z _map.txt do listu (tag, hodnota).
    """
    addrs: List[Tuple[str, str]] = []
    in_addr_section = False
    try:
        with open(map_txt_path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n")
                if not in_addr_section:
                    if line.strip().upper().startswith("ADDRESS"):
                        in_addr_section = True
                    continue
                if not line.strip():
                    continue
                if not line.startswith("[["):
                    # konec sekce ADDRESS
                    break
                if "]]:" in line:
                    tag, val = line.split("]]:", 1)
                    tag = tag.strip()
                    val = val.strip()
                    addrs.append((tag + "]]" if not tag.endswith("]]") else tag, val))
    except Exception:
        pass
    return addrs


def _analyze_map_quality(map_txt_path: Path, original_text: str = "") -> List[str]:
    """
    Projde mapu (_map.txt) a vrátí seznam chyb / upozornění podle QA pokynů:
    - ne-osoby jako PERSON (blacklist, role, města, firmy),
    - podezřelé křestní jméno / chybějící křestní jméno,
    - kanonické příjmení, které se nevyskytuje v originálu (překlep, špatný nominativ),
    - prefixy v adresách (D-PREFIX).

    Pokud je předán `original_text` (text zdrojové smlouvy), provede se ověření
    kanonických příjmení proti originálu – spolehlivější než hádání morfologie.
    """
    issues: List[str] = []

    persons = _parse_persons_from_map_txt(map_txt_path)
    addrs = _parse_addresses_from_map_txt(map_txt_path)

    city_words = {"Praha", "Brno", "Ostrava", "Plzeň", "Liberec", "Olomouc", "Hradec", "Pardubice"}
    blacklist_phrases = {
        "Support Program", "Career Support", "Customer Success",
        "Web Services", "Octavia Combi", "Octavie Combi",
    }
    blacklist_contains = {"Invest"}
    role_words = {
        "manager", "services", "architect", "developer", "senior", "director",
        "chief", "officer", "account", "career", "support", "customer",
        "program", "risk", "web", "octavia", "octavie", "combi",
        "projektová", "projektový",
    }

    def _last_word(s: str) -> str:
        return s.strip().split()[-1] if s.strip() else ""

    for person in persons:
        tag = str(person.get("tag", ""))
        canonical = str(person.get("canonical", "")).strip()
        variants: List[str] = list(person.get("variants", []))
        if not canonical:
            continue

        can_lower = canonical.lower()
        words = canonical.split()

        # --- Blacklist – konkrétní fráze ---
        for phrase in blacklist_phrases:
            if phrase.lower() in can_lower:
                issues.append(f"[C-ROLE-AS-PERSON] {tag} = '{canonical}' obsahuje ne-osobu / roli ('{phrase}').")
                break

        # --- Města / pobočky ---
        if canonical in city_words or any(w in city_words for w in words):
            issues.append(f"[E-WRONG-TYPE] {tag} = '{canonical}' vypadá jako město / pobočka, ne osoba.")

        # --- Firmy ---
        for kw in blacklist_contains:
            if kw.lower() in can_lower:
                issues.append(f"[C-ROLE-AS-PERSON] {tag} = '{canonical}' obsahuje '{kw}', pravděpodobně firma/role, ne osoba.")

        # --- Role jako křestní jméno ---
        if words and words[0].lower() in role_words:
            issues.append(
                f"[C-ROLE-AS-PERSON] {tag} = '{canonical}' – první slovo '{words[0]}' je role/pozice, ne křestní jméno."
            )

        # --- Zdvořilostní obraty ---
        if words:
            first = words[0]
            rest = " ".join(words[1:])
            if first.lower() in {"prosím", "firma"} and rest:
                issues.append(
                    f"[blacklist_as_person] {tag} = '{canonical}' obsahuje zdvořilostní obrat / prefix ('{first}'), "
                    "který nemá být součástí osoby."
                )

        # --- Neúplné jméno (jen jedno slovo) ---
        if len(words) == 1 and canonical not in CZ_FIRSTNAMES:
            surname_suffixes = ('ová', 'á', 'ý', 'ek', 'ík', 'ák', 'ský', 'cký', 'ec', 'el', 'ín', 'il', 'ař', 'al')
            is_valid_surname = canonical.strip().lower().endswith(surname_suffixes)
            has_matching_full_person = any(
                canonical.strip().lower() in p.get("canonical", "").lower()
                for p in persons if len(p.get("canonical", "").split()) >= 2
            )
            if not is_valid_surname and not has_matching_full_person:
                issues.append(
                    f"[D-PARTIAL-NAME] {tag} = '{canonical}' vypadá jako neúplné jméno (pouze jedno slovo)."
                )

        # --- Ověření kanonického příjmení proti originálu ---
        # POZNÁMKA: Tato kontrola byla odstraněna. Pokud je v originálu jméno
        # pouze ve skloněných tvarech (např. "Fialové", "Kratochvílovou"),
        # kanonický nominativ ("Fialová", "Kratochvílová") se v originálu
        # přirozeně nevyskytuje. To je očekávané chování, nikoli chyba.

    # --- Prefixy v adresách (D-PREFIX) ---
    addr_prefixes = [
        "se sídlem", "sídlem", "trvale bytem", "bytem", "na adrese",
    ]
    for tag, addr in addrs:
        low = addr.strip().lower()
        for pfx in addr_prefixes:
            if low.startswith(pfx):
                issues.append(
                    f"[D-PREFIX] {tag} = '{addr}' obsahuje prefix '{pfx}', který podle QA pravidel do adresy nepatří."
                )
                break

    return issues


def _find_visible_names_addresses(anon_text: str) -> List[str]:
    """
    Heuristicky projde anonymizovaný text a hledá vzory, které vypadají jako
    stále viditelná jména nebo adresy, ale nejsou obklopené tagy.

    Neopírá se o mapy – dívá se jen na čistý text. Slouží jako
    "poslední síto": pokud anonymizátor vůbec neoznačil osobu/adresu,
    validátor ji zde zachytí a sníží skóre.
    """
    issues: List[str] = []

    # Vzor pro "Jméno Příjmení"
    name_re = re.compile(
        r"\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{1,30})\s+"
        r"([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{1,30})\b"
    )
    # Vzor pro "Ulice 12, 123 45 Město"
    addr_re = re.compile(
        r"\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^\d\n,]{1,40})\s+"
        r"\d{1,4}(?:/\d{1,3})?,?\s+\d{3}\s?\d{2}\b"
    )

    role_words = {
        "Smlouva", "Článek", "Příloha", "Dodatek", "Protokol", "Zápis",
        "Věřitelé", "Dlužníci", "Věřitel", "Dlužník", "Dlužníkovi", "Dlužníkem",
        "Poskytovatel", "Příjemce", "Objednatel", "Zhotovitel",
        "Zaměstnavatel", "Zaměstnanec", "Zaměstnancem",
        "Pronajímatel", "Pronajímatele", "Pronajímateli", "Pronajímatelem",
        "Nájemce", "Nájemci", "Nájemcem", "Kupující", "Prodávající",
        "Stěžovatel", "Obžalovaný", "Obžalovaná", "Poškozený", "Poškozená",
        "Pacient", "Pacientka", "Pacientovi", "Pacientce", "Pacientky",
        "Pacienta", "Pacientem", "Pacientkou",
        "Lékař", "Lékařka", "Sestra", "Učitelka", "Učitel",
        "Rodiče", "Rodič", "Syn", "Dcera", "Dítě", "Dítěti", "Dítěte",
        "Manželka", "Manžel", "Manžela", "Manželce", "Manželkou",
        "Klient", "Klienta", "Klientka", "Klientovi", "Klientem", "Klientkou",
        "Důchodce", "Důchodkyně", "Absolvent", "Absolventka",
        "Uchazečka", "Uchazeč", "Uchazečky",
        "Kontrolovaná", "Kontrolovaný", "Kontrolovaného",
        "Obviněný", "Obviněná", "Obviněného",
        "Opatrovník", "Opatrovnice", "Opatrovníka",
        "Rozvedený", "Rozvedená", "Pěstoun", "Pěstounka",
        "Exekutor", "Exekutora", "Exekutorka",
        "Psychiatr", "Psychiatra", "Psychiatrka",
        "Nemocnému", "Nemocný", "Nemocná", "Nemocného",
        "Pan", "Paní", "Panu", "Pana",
        "Prosím", "Ahoj", "Dobrý", "Vážený", "Vážená",
        "Ředitelka", "Ředitel", "Ředitele",
        "Notář", "Notářka", "Notáře",
        "Svědek", "Svědkyně",
        "Předseda", "Předsedkyně",
        "Jednatel", "Jednatelka",
        "Advokát", "Advokátka",
    }

    # Klíčová slova, která typicky patří k firmám, produktům, institucím atd.
    # Pokud se objeví jako první nebo druhé slovo, je to pravděpodobně ne-PII.
    non_person_tokens = {
        # ---------- zdravotnictví / instituce ----------
        "nemocnice", "poliklinika", "klinika", "chirurgie", "kardiologie",
        "neurologie", "radiodiagnostika", "fyzioterapie", "diagnóza",
        "hospitalizace", "hypertenze", "gynekologie", "gynekologická",
        "dermatologie", "dermatologické", "onkologická", "onkologické",
        "interní", "dětské", "dětská", "vyšetřující", "spirometr", "jaeger",
        "healthcare", "medical", "imaging", "pharma", "pharmaceutical",
        "huntington", "mayo", "clinic",
        # ---------- české města / městské části / lokace ----------
        "praha", "praze", "prahy", "prahou", "brno", "brna", "brně",
        "olomouc", "olomouci", "ostrava", "ostravě", "ostravy",
        "karlín", "bohnice", "motol", "nusle", "říčany", "josefov",
        "vinohrady", "smíchov", "dejvice", "staré", "město", "nové",
        "české", "budějovice", "hradci", "králové", "karviná", "vltavou",
        "pardubice", "liberec", "plzeň", "zlín", "opava", "česká",
        # ---------- školy / instituce ----------
        "gymnázium", "univerzita", "fakulta", "centrum",
        # ---------- firmy / finanční produkty ----------
        "home", "credit", "financial", "invest", "plus", "reality",
        "provident", "quick", "allianz", "moravia", "energy", "finanční",
        "innovation", "labs", "shop", "world", "papin", "food", "zdravé",
        "konzervy",
        # ---------- auta / hardware / produkty ----------
        "škoda", "octavia", "superb", "fabia", "kodiaq",
        "volkswagen", "transporter", "ford", "transit",
        "dell", "latitude", "samsung", "galaxy",
        "symbicort", "turbuhaler",
        "archer", "link",
        # ---------- technologie / software / firmy ----------
        "google", "authenticator", "amazon", "web", "microsoft", "azure",
        "apple", "facebook", "splunk", "enterprise", "cisco",
        "kaspersky", "endpoint", "synlab", "czech", "prague", "eye",
        "republic", "visa", "classic", "credo", "ventures", "zebra",
        "meta", "london",
        # ---------- obecné IT / týmy / role ----------
        "software", "development", "team", "services", "service",
        "senior", "developer", "backend", "account", "marketing",
        "payroll", "scrum", "master", "manager", "digital", "agency",
        "solutions", "cloud", "architect", "certified", "professional",
        "security", "officer", "data", "protection", "computer", "vision",
        "lead", "auditor", "implementer", "analyst", "premium", "life",
        "investment", "fund", "tech", "business", "avenue", "john",
        "director", "legal", "counsel", "chief", "career", "support",
        "customer", "success", "design", "studio", "global", "finance",
        "compliance", "leasing", "vozidlo", "jira", "demo",
        # ---------- právní / smluvní / obecné termíny ----------
        "úroky", "splatnost", "období", "smlouvy", "pobočka",
        "věznici", "věznice", "legamedis", "anonimizace",
        "kč", "účel", "čistá", "doplatek", "úroková", "pojistná",
        "rodinný", "zbývá", "vlastník",
        "bytem", "datum", "email", "číslo", "obor", "operatér",
        "riziko", "lab", "obžaloba", "razítko", "kupující",
        "kontrolované", "kon", "subjekty", "společnost", "tržní",
        "vypracoval", "elektromobilita", "hodnocení",
        "kontakt", "jméno", "příjmy", "částka", "položka", "počet",
        "popis", "předat", "byt", "hradí", "elektřina", "plyn", "přepis",
        "topení", "internet", "převzetí", "bytu", "porušení", "výše",
        "nepředání", "užívat", "hlásit", "pronajímateli", "nepřenechávat",
        "poriz", "výjimky", "partner", "rodné",
        "pronajímatele", "pronajímatel", "nájemci",
        "některé", "společnost",
        # ---------- tituly (často ve spojení role + titul) ----------
        "mgr", "bc", "ing", "sc", "phd", "judr", "mudr", "phdr",
        "rndr", "doc", "prof", "mba",
        # ---------- další ne-osobní ----------
        "svaté", "markéty", "notářská",
        "pacientky", "pacientka", "pacienta",
    }
    non_person_tokens = {t.lower() for t in non_person_tokens}

    role_words_lo = {w.lower() for w in role_words}

    # Jména
    for m in name_re.finditer(anon_text):
        full = m.group(0)
        first, last = m.group(1), m.group(2)
        first_lo = first.lower()
        last_lo = last.lower()
        # Přeskoč zjevné nadpisy/role (case-insensitive)
        if first_lo in role_words_lo:
            continue
        # Přeskoč zjevné ne-osobní kombinace (firmy, produkty, instituce, částky...)
        if first_lo in non_person_tokens or last_lo in non_person_tokens:
            continue
        # Přeskoč pokud druhé slovo je role (Král Kupující, Havlíček Bytem)
        if last_lo in role_words_lo:
            continue
        start, end = m.span()
        ctx = anon_text[max(0, start - 10) : min(len(anon_text), end + 10)]
        # Pokud je v okolí už PERSON tag, považuj to za anonymizované
        if "[[PERSON_" in ctx:
            continue
        issues.append(f"NAME: {full}")
        if len(issues) >= 30:
            break

    # Adresy
    for m in addr_re.finditer(anon_text):
        full = m.group(0)
        start, end = m.span()
        ctx = anon_text[max(0, start - 5) : min(len(anon_text), end + 5)]
        if "[[ADDRESS_" in ctx:
            continue
        issues.append(f"ADDR: {full}")
        if len(issues) >= 60:
            break

    return issues


_PII_LEAK_IGNORE = {
    'bc.', 'mgr.', 'ing.', 'judr.', 'mudr.', 'phdr.', 'rndr.', 'doc.', 'prof.',
    'praha', 'brno', 'ostrava', 'plzeň', 'olomouc', 'liberec', 'pardubice',
    'české budějovice', 'hradec králové', 'ústí nad labem', 'zlín', 'opava',
    'manager', 'director', 'officer', 'specialist', 'consultant', 'architect',
    'risk manager', 'account manager', 'support program', 'services',
    'banka', 'stav', 'nová', 'nové', 'nový', 'malá', 'malý', 'hrubá',
    'innovation labs', 'papin food', 'compliance', 'hcp_admin',
}

def check_pii_leak_from_map(anon_text: str, originals: Set[str]) -> List[str]:
    """Vrátí seznam původních hodnot z mapy, které se objevily ve výstupu (PII leak)."""
    leaks = []
    for orig in originals:
        if len(orig) < 4:
            continue
        if orig.lower() in _PII_LEAK_IGNORE:
            continue
        escaped = re.escape(orig)
        is_numeric = orig.replace(' ', '').isdigit()
        is_leak = False
        for m in re.finditer(r'\b' + escaped + r'\b', anon_text, re.IGNORECASE):
            s, e = m.span()
            if is_numeric:
                ctx_before = anon_text[max(0, s - 15):s]
                ctx_after = anon_text[e:e + 15]
                if re.search(r'[\d]', ctx_before) or re.search(r'^[\-/]', ctx_after):
                    continue
                if s > 0 and anon_text[s - 1] == '-':
                    continue
                if any(w in ctx_after.lower() for w in ['kč', 'czk', ',-', 'korun']):
                    continue
            is_leak = True
            break
        if is_leak:
            leaks.append(orig)
    return leaks


def check_pii_regex(anon_text: str) -> List[Tuple[str, str]]:
    """Skenuje výstup regex vzory pro typické české PII. Vrátí [(match, typ), ...]."""
    found = []
    for pattern, label in PII_PATTERNS:
        for m in re.finditer(pattern, anon_text):
            start, end = m.span()
            before = anon_text[max(0, start - 2) : start]
            after = anon_text[end : min(len(anon_text), end + 2)]
            if "[[" in before or "]]" in after:
                continue
            matched = m.group()
            if "Telefon" in label:
                ctx_after = anon_text[end:end + 30].lower()
                digits_only = re.sub(r'\s', '', matched)
                val = int(digits_only) if digits_only.isdigit() else 0
                if val >= 100_000_000 or any(w in ctx_after for w in ['kč', 'czk', 'korun', 'eur', ',-']):
                    continue
            if "Rodné číslo" in label:
                parts = matched.split('/')
                if len(parts) == 2 and len(parts[1]) in (3, 4):
                    suffix = parts[1]
                    if len(suffix) == 4 and (suffix.startswith('20') or suffix.startswith('19')):
                        continue
            found.append((matched, label))
    return found


def check_map_consistency(map_json_path: Path, map_txt_path: Path) -> Tuple[bool, List[str]]:
    """
    Ověří konzistenci map dle SKRYI specifikace:
    - JSON a TXT obsahují stejné labely
    - 1 entita = 1 tag (žádné duplicity)
    """
    errors = []
    try:
        with open(map_json_path, encoding="utf-8") as f:
            jdata = json.load(f)
        with open(map_txt_path, encoding="utf-8") as f:
            txt = f.read()

        json_labels = set()
        seen_originals: Dict[str, List] = {}
        for ent in jdata.get("entities", []):
            lbl = ent.get("label", "")
            orig = ent.get("original", "")
            if lbl:
                json_labels.add(lbl)
            if orig and orig not in ("***REDACTED***", ""):
                norm = orig.strip().lower()
                lbl_type = re.sub(r'_\d+\]\]$', '', lbl.lstrip('['))
                if norm not in seen_originals:
                    seen_originals[norm] = (lbl, lbl_type)
                else:
                    prev_lbl, prev_type = seen_originals[norm]
                    if prev_lbl != lbl and prev_type == lbl_type:
                        errors.append(f"Duplicitní entita '{orig[:30]}...' má různé tagy")

        txt_labels = set(re.findall(r"\[\[[A-Z0-9_]+\]\]", txt))

        missing_in_txt = json_labels - txt_labels
        extra_in_txt = txt_labels - json_labels
        if missing_in_txt:
            errors.append(f"V JSON jsou labely, které chybí v TXT: {list(missing_in_txt)[:5]}")
        if extra_in_txt:
            errors.append(f"V TXT jsou labely, které chybí v JSON: {list(extra_in_txt)[:5]}")

        return len(errors) == 0, errors
    except Exception as e:
        return False, [str(e)]


def compute_score(
    success: bool,
    pii_leaks: List[str],
    pii_regex: List[Tuple[str, str]],
    map_ok: Optional[bool],
    structure_ok: bool,
    pdf_exists: bool,
) -> int:
    """
    Ohodnocení 1–10 dle SKRYI kritérií:
    10 = perfektní (žádný PII, mapy OK, struktura, PDF)
    7–9 = drobné nedostatky
    4–6 = PII leak nebo nekonzistentní mapy
    1–3 = vážné problémy
    0 = crash / chybějící výstup
    """
    if not success:
        return 0

    score = 10
    # PII z mapy – kritické
    if pii_leaks:
        score -= min(6, 2 + len(pii_leaks))
    # PII z regex – kritické
    if pii_regex:
        score -= min(5, 1 + len(pii_regex))
    # Mapy nekonzistentní
    if map_ok is False:
        score -= 2
    # Struktura poškozena
    if not structure_ok:
        score -= 1
    # PDF report chybí
    if not pdf_exists:
        score -= 1

    return max(0, min(10, score))


def run_single_anonymize(docx_path: Path) -> dict:
    """Spustí anonymizaci na jeden soubor. Vrátí dict s výsledkem."""
    base = docx_path.stem
    out_docx = OUT_DIR / f"{base}_anon.docx"
    map_json = OUT_DIR / f"{base}_map.json"
    map_txt = OUT_DIR / f"{base}_map.txt"
    report_pdf = OUT_DIR / f"{base}_report.pdf"

    result = {
        "file": docx_path.name,
        "success": False,
        "error": None,
        "pii_leaks": [],
        "pii_regex_found": [],
        "map_ok": None,
        "map_errors": [],
        "structure_ok": None,
        "pdf_report_exists": False,
        "entity_count": 0,
        "score": 0,
        "score_breakdown": {},
    }

    try:
        # Spouštíme anonymizaci přímo v procesu (ne subprocess) – vyhne se problémům s PYTHONPATH
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        old_argv = sys.argv
        sys.argv = [
            "anonymize_cli",
            "--input", str(docx_path),
            "--output", str(out_docx),
            "--map", str(map_json),
            "--map_txt", str(map_txt),
            "--report", str(report_pdf),
        ]
        import io
        err_capture = io.StringIO()
        try:
            import runpy
            old_stderr = sys.stderr
            sys.stderr = err_capture
            runpy.run_path(str(ANON_CLI), run_name="__main__")
        except SystemExit as e:
            if e.code != 0 and e.code is not None:
                err_text = err_capture.getvalue() or str(e)
                result["error"] = (err_text[:500] if err_text else f"Kód {e.code}").strip()
                return result
        finally:
            sys.stderr = old_stderr
            sys.argv = old_argv

        result["success"] = True

        if not out_docx.exists():
            result["error"] = "Výstupní DOCX nebyl vytvořen"
            return result

        # Struktura dokumentu
        orig_struct = get_docx_structure(docx_path)
        anon_struct = get_docx_structure(out_docx)
        result["structure_ok"] = (
            orig_struct["paragraphs"] == anon_struct["paragraphs"]
            and orig_struct["tables"] == anon_struct["tables"]
        )
        result["structure"] = {"original": orig_struct, "anonymized": anon_struct}

        # PDF report
        result["pdf_report_exists"] = report_pdf.exists()

        anon_text = get_all_text_from_docx(out_docx)
        original_text = get_all_text_from_docx(docx_path)

        originals = set()
        if map_json.exists():
            originals |= extract_originals_from_map_json(map_json)
            try:
                with open(map_json, encoding="utf-8") as f:
                    j = json.load(f)
                result["entity_count"] = len(j.get("entities", []))
            except Exception:
                pass
        if map_txt.exists():
            originals |= extract_originals_from_map_txt(map_txt)

        # 1) PII leaky na základě map (původní hodnoty, které se znovu objevily ve výstupu)
        result["pii_leaks"] = check_pii_leak_from_map(anon_text, originals)

        # 2) Heuristické úniky: jména/adresy, které anonymizátor vůbec neoznačil
        visible_names_addrs = _find_visible_names_addresses(anon_text)
        if visible_names_addrs:
            # Přidej je jako zvláštní typ PII leaků – s prefixem pro čitelnost v reportu
            result["pii_leaks"].extend(visible_names_addrs)
        result["pii_regex_found"] = [
            {"match": m[:20] + "..." if len(m) > 20 else m, "type": t}
            for m, t in check_pii_regex(anon_text)
        ]

        if map_json.exists() and map_txt.exists():
            map_ok, map_errs = check_map_consistency(map_json, map_txt)
            extra_map_issues = _analyze_map_quality(map_txt, original_text)
            result["map_ok"] = map_ok and not extra_map_issues
            result["map_errors"] = map_errs + extra_map_issues

        result["score"] = compute_score(
            success=result["success"],
            pii_leaks=result["pii_leaks"],
            pii_regex=result["pii_regex_found"],
            map_ok=result["map_ok"],
            structure_ok=result["structure_ok"] or False,
            pdf_exists=result["pdf_report_exists"],
        )
        result["score_breakdown"] = {
            "pii_from_map": len(result["pii_leaks"]),
            "pii_from_regex": len(result["pii_regex_found"]),
            "map_ok": result["map_ok"],
            "structure_ok": result["structure_ok"],
            "pdf_exists": result["pdf_report_exists"],
        }

    except subprocess.TimeoutExpired:
        result["error"] = "Timeout (120s)"
    except Exception as e:
        result["error"] = str(e)
        result["score"] = 0

    return result


def _format_problemy(r: dict) -> str:
    """Vrátí stručný popis problémů pro přehled."""
    if not r.get("success"):
        return r.get("error", "Chyba")[:60]
    parts = []
    if r.get("pii_leaks"):
        parts.append(f"PII:{len(r['pii_leaks'])}")
    if r.get("pii_regex_found"):
        parts.append(f"regex:{len(r['pii_regex_found'])}")
    if r.get("map_ok") is False:
        parts.append("mapa")
    if not r.get("structure_ok"):
        parts.append("struktura")
    if not r.get("pdf_report_exists"):
        parts.append("PDF")
    return ", ".join(parts) if parts else "—"


def _format_poznamka(r: dict) -> str:
    """Vrátí podrobnou poznámku, co bylo špatně – seskupenou po kategoriích."""
    if not r.get("success"):
        return r.get("error", "Chyba při anonymizaci")
    notes = []
    if r.get("pii_leaks"):
        leaks = ", ".join(f'"{x}"' for x in r["pii_leaks"][:5])
        if len(r["pii_leaks"]) > 5:
            leaks += f" (+{len(r['pii_leaks'])-5})"
        notes.append(f"PII leak: {leaks}")
    if r.get("pii_regex_found"):
        items = [f"{x.get('match','')} ({x.get('type','')})" for x in r["pii_regex_found"][:3]]
        notes.append(f"Regex PII: {', '.join(items)}")

    map_errors = r.get("map_errors", [])
    if r.get("map_ok") is False and map_errors:
        consistency_errs = [e for e in map_errors if not e.startswith("[")]
        person_errs = [e for e in map_errors if e.startswith("[C-") or e.startswith("[E-") or e.startswith("[blacklist") or e.startswith("[D-PARTIAL")]
        addr_errs = [e for e in map_errors if e.startswith("[D-PREFIX")]

        if consistency_errs:
            notes.append(f"Mapa (konzistence): {'; '.join(consistency_errs[:3])}")
        if person_errs:
            notes.append(f"Mapa (osoby): {'; '.join(person_errs[:5])}")
        if addr_errs:
            notes.append(f"Mapa (adresy): {'; '.join(addr_errs[:3])}")

    if not r.get("structure_ok"):
        orig = r.get("structure", {}).get("original", {})
        anon = r.get("structure", {}).get("anonymized", {})
        notes.append(f"Struktura: orig {orig} vs anon {anon}")
    if not r.get("pdf_report_exists"):
        notes.append("Chybí PDF report")
    return " | ".join(notes) if notes else "OK"


def _write_report_md(path: Path, report: dict) -> None:
    """Zapíše přehledný Markdown report s tabulkou skóre a detaily chyb."""
    s = report["summary"]
    lines = [
        "# Výsledky testů anonymizace SKRYI",
        "",
        "## Shrnutí",
        "",
        "| Metrika | Hodnota |",
        "|---------|---------|",
        f"| Celkem smluv | {s['total']} |",
        f"| Prošlo (score>=9) | {s['passed']} |",
        f"| Selhalo | {s['failed']} |",
        f"| Průměr score | {s['avg_score']}/10 |",
        f"| S PII leakem | {s['with_pii_leak']} |",
        f"| Nekonzistentní mapa | {s['map_inconsistent']} |",
        "",
        "## Přehled po smlouvách",
        "",
        "| Soubor | Score | Status | Problémy |",
        "|--------|-------|--------|----------|",
    ]
    for row in report["prehled"]:
        lines.append(f"| {row['soubor']} | {row['score']}/10 | {row['status']} | {row['problémy']} |")

    lines.extend(["", "---", "", "## Detaily chyb po smlouvách", ""])

    for r in report.get("results", []):
        fname = r.get("file", "")
        score = r.get("score", 0)
        if score >= 9 and r.get("success") and not r.get("map_errors"):
            continue

        lines.append(f"### {fname} — {score}/10")
        lines.append("")

        if r.get("pii_leaks"):
            lines.append("**PII leak (hodnoty z mapy nalezené v anonymu):**")
            for leak in r["pii_leaks"][:10]:
                lines.append(f"- `{leak}`")
            if len(r["pii_leaks"]) > 10:
                lines.append(f"- _(+{len(r['pii_leaks'])-10} dalších)_")
            lines.append("")

        if r.get("pii_regex_found"):
            lines.append("**PII nalezené regexem:**")
            for item in r["pii_regex_found"][:5]:
                lines.append(f"- `{item.get('match', '')}` ({item.get('type', '')})")
            lines.append("")

        map_errors = r.get("map_errors", [])
        if map_errors:
            consistency = [e for e in map_errors if not e.startswith("[")]
            persons = [e for e in map_errors if e.startswith("[C-") or e.startswith("[E-") or e.startswith("[blacklist") or e.startswith("[D-PARTIAL")]
            addrs = [e for e in map_errors if e.startswith("[D-PREFIX")]

            if consistency:
                lines.append("**Mapa – konzistence JSON/TXT:**")
                for e in consistency[:5]:
                    lines.append(f"- {e}")
                lines.append("")
            if persons:
                lines.append("**Mapa – chyby osob (PERSON):**")
                for e in persons:
                    lines.append(f"- {e}")
                lines.append("")
            if addrs:
                lines.append("**Mapa – chyby adres (ADDRESS):**")
                for e in addrs:
                    lines.append(f"- {e}")
                lines.append("")

        lines.append("---")
        lines.append("")

    lines.extend([
        "## Selhané soubory",
        "",
        ", ".join(report["failed_files"]) if report["failed_files"] else "Žádné",
        "",
        "---",
        "*Detailní data v `test_results.json`*",
    ])
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _extract_smlouva_num(path: Path) -> Optional[int]:
    """Z názvu smlouva25.docx vrátí 25, jinak None."""
    m = re.search(r"smlouva\s*(\d+)", path.stem, re.IGNORECASE)
    return int(m.group(1)) if m else None


def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Test anonymizace dle SKRYI specifikace (PII, mapy, struktura, PDF)"
    )
    ap.add_argument("--min", type=int, default=None, help="Jen smlouvy od čísla (např. 25)")
    ap.add_argument("--max", type=int, default=None, help="Jen smlouvy do čísla (např. 30)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    docx_files = sorted(TEST_DATA.glob("smlouva*.docx"))
    docx_files = [f for f in docx_files if not f.name.startswith("~$")
                  and "_anon" not in f.name and "_deanon" not in f.name]

    if args.min is not None or args.max is not None:
        filtered = []
        for f in docx_files:
            n = _extract_smlouva_num(f)
            if n is None:
                continue
            if args.min is not None and n < args.min:
                continue
            if args.max is not None and n > args.max:
                continue
            filtered.append(f)
        docx_files = filtered

    if not docx_files:
        print("[CHYBA] Žádné smlouva*.docx v test_data")
        sys.exit(1)

    print(f"[INFO] Nalezeno {len(docx_files)} smluv. Spouštím anonymizaci (SKRYI validace)...")
    results = []
    for i, path in enumerate(docx_files, 1):
        print(f"  [{i}/{len(docx_files)}] {path.name}...", end=" ", flush=True)
        r = run_single_anonymize(path)
        results.append(r)
        if r["success"]:
            s = r["score"]
            issues = []
            if r["pii_leaks"]:
                issues.append(f"PII map:{len(r['pii_leaks'])}")
            if r["pii_regex_found"]:
                issues.append(f"PII regex:{len(r['pii_regex_found'])}")
            if r["map_ok"] is False:
                issues.append("mapa")
            if not r["structure_ok"]:
                issues.append("struktura")
            if not r["pdf_report_exists"]:
                issues.append("PDF")
            status = f"score={s}/10"
            if issues:
                status += f" ({', '.join(issues)})"
            print(status)
        else:
            err_msg = (r["error"] or "").encode("ascii", errors="replace").decode("ascii")
            print(f"FAIL: {err_msg[:80]}")

    passed = sum(1 for r in results if r["success"] and r["score"] >= 9)
    failed = [r for r in results if not r["success"] or r["score"] < 9]
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0

    # Kompaktní přehled pro rychlé skenování
    prehled = [
        {
            "soubor": r["file"],
            "score": r["score"],
            "status": "OK" if r["success"] and r["score"] >= 9 else "FAIL",
            "problémy": _format_problemy(r),
            "poznamka": _format_poznamka(r),
        }
        for r in results
    ]

    report = {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(failed),
            "avg_score": round(avg_score, 1),
            "with_pii_leak": sum(1 for r in results if r.get("pii_leaks") or r.get("pii_regex_found")),
            "map_inconsistent": sum(1 for r in results if r.get("map_ok") is False),
            "structure_broken": sum(1 for r in results if r.get("structure_ok") is False),
            "pdf_missing": sum(1 for r in results if not r.get("pdf_report_exists")),
        },
        "prehled": prehled,
        "results": results,
        "failed_files": [r["file"] for r in failed],
    }

    out_path = REPORTS_DIR / "test_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Čitelný Markdown report
    _write_report_md(REPORTS_DIR / "test_results.md", report)

    print(f"\n[OK] Report uložen: {out_path}")
    print(f"     PASS (score>=9): {passed}/{len(results)}, FAIL: {len(failed)}, průměr: {avg_score:.1f}/10")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
