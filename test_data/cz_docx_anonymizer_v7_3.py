# -*- coding: utf-8 -*-
"""
Czech DOCX Anonymizer – v7.3 (library-driven names, strict)
Autor: Nix (pro Dana / Nixminds)

Co dělá:
- ZACHOVÁVÁ původní logiku pro ostatní entity (banky, datum, IČO, RČ/ID, adresy – rozumná heuristika).
- Detekce osob je *striktně řízená* knihovnou jmen (JSON ve stejné složce).
- Pokud křestní jméno NENÍ v knihovně, osoba se NEoznačí (výjimka: velmi silný kontext – "nar.", "rč", "bytem", "dlužník", "věřitel", "zmocnitel", "zmocněnec"…).
- Lepší slučování variant: "Michal Říha" == "Michalu Říhovi" -> stejný [[PERSON_X]].
- Opravy pro příjmení typu "Říha" (…Říhovi → Říha), ženská příjmení (…ná/…á) apod.
- Umí číst dvě různé struktury knihoven:
    A) cz_names.v1.json:
       {
         "firstnames_no_diac": {"M": ["michal", ...], "F": ["petra", ...]},
         "surnames_no_diac": ["riha", "marecek", "mala", ...]
       }
    B) names_library.json:
       {
         "male_names": ["michal", ...],
         "female_names": ["petra", ...],
         "surnames": ["říha", "mareček", "malá", ...]
       }

Použití:
    python cz_docx_anonymizer_v7_3.py cesta/k/souboru.docx --names-json cz_names.v1.json

Výstupy:
    <soubor>_anon.docx
    <soubor>_map.json  (mapování tag -> nalezené výskyty)
    <soubor>_map.txt   (přehledná textová mapa pro rychlou kontrolu)

Poznámka:
- Knihovna *řídí* koho uznáme jako osobu. Pokud chybí příjmení "Říha" nebo "Mareček", prostě se to nechytí – doplňte do JSON.
- Tím snížíme falešné pozitivy typu "Na Hrázi" → [[PERSON_x]].
"""

import sys
import re
import json
import unicodedata
from typing import Optional, Set, Dict, Tuple, List
from pathlib import Path
from collections import defaultdict, OrderedDict

try:
    from docx import Document
except ImportError:
    raise SystemExit("Chybí balíček python-docx. Nainstalujte:  pip install python-docx")

# ===================== utils =====================

INVISIBLE = '\\u00ad\\u200b\\u200c\\u200d\\u2060\\ufeff'

def clean_invisibles(text: str) -> str:
    if not text: return ''
    text = text.replace('\\u00a0', ' ')
    return re.sub('[' + re.escape(INVISIBLE) + ']', '', text)

def normalize_for_matching(text: str) -> str:
    """Odstraní diakritiku + ne-alfabetické znaky, sníží na lower – pro porovnávání."""
    if not text: return ""
    n = unicodedata.normalize('NFD', text)
    no_diac = ''.join(c for c in n if not unicodedata.combining(c))
    return re.sub(r'[^A-Za-z]', '', no_diac).lower()

def preserve_case(surface: str, tag: str) -> str:
    """Zachovej 'styl' zápisu (uppercase/title/other) při nahrazení tagem."""
    if surface.isupper():
        return tag.upper()
    if surface.istitle():
        return tag
    return tag

def iter_paragraphs(doc: "Document"):
    for p in doc.paragraphs:
        yield p
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    yield p

def get_text(p) -> str:
    # Sloučení runů – potřebné pro korektní search/replace
    return ''.join(r.text or '' for r in p.runs) or (p.text or '')

def set_text(p, s: str):
    if p.runs:
        p.runs[0].text = s
        for r in p.runs[1:]:
            r.text = ''
    else:
        p.text = s

# ===================== knihovna jmen =====================

CZECH_FIRST_NAMES: Set[str] = set()
CZECH_SURNAMES: Set[str] = set()

def _ingest_firstnames_from_v1(data: dict, acc: Set[str]):
    # očekává: firstnames_no_diac: {"M": [...], "F": [...]}
    fn = data.get("firstnames_no_diac", {})
    for gender in ("M", "F"):
        for nm in fn.get(gender, []):
            acc.add(normalize_for_matching(nm))

def _ingest_surnames_from_v1(data: dict, acc: Set[str]):
    for sn in data.get("surnames_no_diac", []):
        acc.add(normalize_for_matching(sn))

def _ingest_from_library_alt(data: dict, first_acc: Set[str], sur_acc: Set[str]):
    # očekává: male_names, female_names, surnames (s diakritikou či bez)
    for key in ("male_names", "female_names"):
        for nm in data.get(key, []):
            first_acc.add(normalize_for_matching(nm))
    for sn in data.get("surnames", []):
        sur_acc.add(normalize_for_matching(sn))

def load_names_library(json_path: str = "cz_names.v1.json") -> Tuple[Set[str], Set[str]]:
    """Načte jména a příjmení ze zadaného JSON. Podporuje 2 formáty (viz hlavička)."""
    global CZECH_FIRST_NAMES, CZECH_SURNAMES
    firstnames, surnames = set(), set()

    json_file = Path(json_path)
    if not json_file.exists():
        # fallback: zkus sousední names_library.json
        alt_file = json_file.parent / "names_library.json"
        if alt_file.exists():
            json_file = alt_file
        else:
            print(f"⚠️ Varování: {json_path} ani {alt_file.name} neexistují – detekce osob bude vypnutá.")
            CZECH_FIRST_NAMES, CZECH_SURNAMES = set(), set()
            return CZECH_FIRST_NAMES, CZECH_SURNAMES

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "firstnames_no_diac" in data or "surnames_no_diac" in data:
        _ingest_firstnames_from_v1(data, firstnames)
        _ingest_surnames_from_v1(data, surnames)
    else:
        _ingest_from_library_alt(data, firstnames, surnames)

    CZECH_FIRST_NAMES, CZECH_SURNAMES = firstnames, surnames
    print(f"✔ Načteno {len(CZECH_FIRST_NAMES)} křestních jmen a {len(CZECH_SURNAMES)} příjmení z {json_file.name}")
    return CZECH_FIRST_NAMES, CZECH_SURNAMES

# ============== blacklisty / whitelisty kontextu ==============

ADDRESS_PARTS = {
    # obecné
    'ulice','náměstí','třída','cesta','nábřeží','nábreží','nábrezi','u','na','pod','nad','mezi','ve','v','bytem',
    # časté části názvů
    'hrázi','hráz','skalka','skalkou','les','lesu','studánka','studánky','pod','na',
    # města
    'praha','brno','ostrava','plzeň','olomouc','liberec','hradec','králové','kralove',
    'české','ceske','budějovice','budejovice','pardubice','zlin','opava','třebíč','trebic','šumperk','sumperk'
}

STRONG_PERSON_CONTEXT = {
    'nar.', 'narozen', 'rč', 'rodné číslo', 'rc',
    'bytem', 'trvale bytem', 'v místě bydliště',
    'dlužník', 'věřitel', 'žalobce', 'žalovaný', 'zmocnitel', 'zmocněnec',
    'manžel', 'manželka', 'syn', 'dcera', 'oprávněný', 'povinný'
}

# ============== lemmatizace / nominativy ==============

def infer_first_name_nominative(observed: str) -> Optional[str]:
    """Heuristika k nalezení nominativu křestního jména a validaci proti knihovně."""
    if not observed: return None
    obs = observed.strip()
    nobs = normalize_for_matching(obs)

    # Přímý hit
    if nobs in CZECH_FIRST_NAMES:
        return obs

    # Michalu -> Michal; Jakubovi -> Jakub; Lukáše -> Lukáš; Petry -> Petra; Veroniky -> Veronika
    rules = [
        (r'(.+)u$', r'\\1'),       # Michalu → Michal
        (r'(.+)ovi$', r'\\1'),     # Jakubovi → Jakub
        (r'(.+)e$', r'\\1'),       # Lukáše → Lukáš (pozor: může dát falešně, proto validace níže)
        (r'(.+)y$', r'\\1a'),      # Petry → Petra
        (r'(.+)i$', r'\\1a'),      # Veroniki -> Veronika (vzácné v textech, ale neuškodí)
    ]
    for pat, rep in rules:
        cand = re.sub(pat, rep, obs, flags=re.IGNORECASE)
        if cand != obs and normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return cand

    # fallback: nic
    return None

def infer_surname_nominative(observed: str) -> str:
    """Heuristika k nalezení nominativu příjmení. Nevynucujeme přítomnost v knihovně,
    ale později preferujeme páry, kde příjmení v knihovně je.
    """
    if not observed: return observed
    obs = observed.strip()
    low = obs.lower()

    # Říhovi -> Říha; Marečkovi -> Mareček; Doležalovi -> Doležal
    if re.search(r'(ovi|ovi)$', low):
        return re.sub(r'(ovi|ovi)$', 'a', obs, flags=re.IGNORECASE) if low.endswith('hovi') else re.sub(r'(ovi|ovi)$', '', obs, flags=re.IGNORECASE)

    # Říhou/Říhem/Říhu -> Říha; Marečkem/Marečka/Marečku -> Mareček
    endings = (
        ('hou','ha'), ('hem','ha'), ('hu','ha'),
        ('kem','ek'), ('ka','ek'), ('ku','ek'),
        ('alem','al'), ('ala','al'), ('alovi','al')
    )
    for src, dst in endings:
        if low.endswith(src) and len(obs) > len(src)+1:
            return obs[:-len(src)] + dst

    # ženská příjmení: Novotné -> Novotná, Malé -> Malá, Suché -> Suchá
    if low.endswith('é') and len(obs) > 2:
        return obs[:-1] + 'á'

    return obs

# ============== core anonymizer ==============

class Anonymizer:
    def __init__(self):
        self.counter = defaultdict(int)
        self.tag_map: Dict[str, List[str]] = defaultdict(list)
        self.value_to_tag: Dict[str, str] = {}
        self.person_index: Dict[Tuple[str, str], str] = {}
        self.canonical_persons: List[Dict[str, str]] = []

    # ----- tagging infra -----

    def _get_or_create_tag(self, cat: str, value: str) -> str:
        norm_val = ' '.join(value.split())
        lookup_key = f"{cat}:{norm_val}"
        if lookup_key in self.value_to_tag:
            return self.value_to_tag[lookup_key]
        self.counter[cat] += 1
        tag = f'[[{cat}_{self.counter[cat]}]]'
        self.value_to_tag[lookup_key] = tag
        self._record_value(tag, value)
        return tag

    def _record_value(self, tag: str, value: str):
        if value and value not in self.tag_map[tag]:
            self.tag_map[tag].append(value)

    # ----- person handling -----

    def _ensure_person_tag(self, first_nom: str, last_nom: str) -> str:
        key = (normalize_for_matching(first_nom), normalize_for_matching(last_nom))
        if key in self.person_index:
            return self.person_index[key]
        tag = self._get_or_create_tag('PERSON', f'{first_nom} {last_nom}')
        self.person_index[key] = tag
        self.canonical_persons.append({'first': first_nom, 'last': last_nom, 'tag': tag})
        return tag

    def _generate_variants(self, first: str, last: str) -> List[str]:
        """Vygeneruje běžné pády křestního jména a příjmení – pro robustní nahrazení.
        Speciální pravidla pro několik častých jmen; jinak vrací základní tvar.
        """
        variants = []

        def first_vars(f: str) -> List[str]:
            base = f.lower()
            if base == 'michal':   return ['Michal','Michala','Michalu','Michalovi','Michalem','Michale']
            if base == 'jakub':    return ['Jakub','Jakuba','Jakubovi','Jakubem','Jakube']
            if base == 'lukáš' or base == 'lukas': return ['Lukáš','Lukáše','Lukáši','Lukášovi','Lukášem']
            if base == 'petr':     return ['Petr','Petra','Petrovi','Petrem','Petře']
            if base == 'petra':    return ['Petra','Petry','Petře','Petru','Petrou']
            if base == 'klára' or base == 'klara': return ['Klára','Kláry','Kláře','Kláru','Klárou']
            if base == 'veronika': return ['Veronika','Veroniky','Veronice','Veroniku','Veronikou']
            return [f]

        def last_vars(l: str) -> List[str]:
            base = l.lower()
            if base in ('říha','riha'): return ['Říha','Říhy','Říhovi','Říhou','Říhu']
            if base == 'mareček' or base == 'marecek': return ['Mareček','Marečka','Marečkovi','Marečkem','Marečku']
            if base == 'doležal' or base == 'dolezal': return ['Doležal','Doležala','Doležalovi','Doležalem']
            if base == 'novotná' or base == 'novotna': return ['Novotná','Novotné','Novotnou']
            if base == 'malá' or base == 'mala': return ['Malá','Malé','Malou']
            if base == 'suchá' or base == 'sucha': return ['Suchá','Suché','Suchou']
            return [l]

        for f in first_vars(first):
            for l in last_vars(last):
                variants.append(f"{f} {l}")
        return variants

    def _looks_like_address_piece(self, token: str) -> bool:
        return normalize_for_matching(token) in ADDRESS_PARTS

    def _has_strong_person_context_nearby(self, text: str, start: int, end: int, window: int = 40) -> bool:
        s = max(0, start - window)
        e = min(len(text), end + window)
        ctx = text[s:e].lower()
        return any(kw in ctx for kw in STRONG_PERSON_CONTEXT)

    def _extract_persons(self, text: str):
        """Najde kandidáty na osoby a zaregistruje je do self.canonical_persons.
        Podmínka: křestní jméno *musí* být v knihovně, jinak pouze při silném kontextu.
        """
        # odeber běžné tituly před jmény
        text_clean = re.sub(r'\\b(Mgr|Ing|Dr|Bc|JUDr|MUDr|PhDr|Ph\\.D\\.|MBA)\\.?\\s+', '', text, flags=re.I)

        # kapitál-začínající dvojice tokenů
        pair_re = re.compile(r'\\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\\b')

        for m in pair_re.finditer(text_clean):
            first_tok, last_tok = m.group(1), m.group(2)

            # vyluč kousky adres
            if self._looks_like_address_piece(first_tok) or self._looks_like_address_piece(last_tok):
                continue

            first_nom = infer_first_name_nominative(first_tok)
            if not first_nom:
                # dovol "mimo knihovnu" jen v silném kontextu
                if not self._has_strong_person_context_nearby(text_clean, m.start(), m.end()):
                    continue
                # ještě jednou zkús nominativ triviálně
                first_nom = first_tok

            # striktně: musí být v knihovně, *pokud* není silný kontext
            if normalize_for_matching(first_nom) not in CZECH_FIRST_NAMES:
                if not self._has_strong_person_context_nearby(text_clean, m.start(), m.end()):
                    continue

            last_nom = infer_surname_nominative(last_tok)

            # volitelně preferuj příjmení v knihovně, ale nevyžaduj
            # (když je mimo knihovnu, pořád to může být správně)
            self._ensure_person_tag(first_nom, last_nom)

    def _replace_persons(self, text: str) -> str:
        """Nahraď všechny varianty již zaregistrovaných osob jejich tagy."""
        for person in self.canonical_persons:
            tag = person['tag']
            variants = self._generate_variants(person['first'], person['last'])
            # Delší výrazy nahrazuj dřív
            for var in sorted(variants, key=len, reverse=True):
                pattern = re.compile(r'\\b' + re.escape(var) + r'\\b', re.I)
                def repl(m):
                    self._record_value(tag, m.group(0))
                    return preserve_case(m.group(0), tag)
                text = pattern.sub(repl, text)
        return text

    # ----- ostatní entity (ponecháno / mírně rozšířeno) -----

    def _replace_other_entities(self, text: str) -> str:
        # Datum: 12. 10. 2025
        text = re.sub(
            r'\\b\\d{1,2}\\.\\s*\\d{1,2}\\.\\s*\\d{4}\\b',
            lambda m: self._get_or_create_tag('DATE', m.group(0)),
            text
        )

        # CZ IBAN: CZkk bbbb ssss cccc cccc cccc
        text = re.sub(
            r'\\bCZ\\d{2}(?:\\s?\\d{4}){5}\\b',
            lambda m: self._get_or_create_tag('BANK', m.group(0)),
            text,
            flags=re.I
        )

        # Bankovní účet: 1234567890/0100 apod.
        text = re.sub(
            r'\\b\\d{6,10}/\\d{4}\\b',
            lambda m: self._get_or_create_tag('BANK', m.group(0)),
            text
        )

        # Rodné číslo (zjednodušeně): 6 číslic / 3–4 číslice
        text = re.sub(
            r'\\b\\d{6}/\\d{3,4}\\b',
            lambda m: self._get_or_create_tag('IDCZ', m.group(0)),
            text
        )

        # IČO (8 číslic) – POZOR: může mít falešné zásahy, ale běžně funguje.
        text = re.sub(
            r'(?<!\\d)\\d{8}(?!\\d)',
            lambda m: self._get_or_create_tag('ICO', m.group(0)),
            text
        )

        # Jednoduchá adresa: "Ulice 12, 123 45 Město"
        addr_pattern = r'\\b[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^,\\n]{2,40}?\\s+\\d{1,4}[A-Za-z]?\\s*,\\s*\\d{3}\\s?\\d{2}\\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^,\\n]{2,30}\\b'
        text = re.sub(
            addr_pattern,
            lambda m: self._get_or_create_tag('ADDRESS', m.group(0)),
            text
        )

        return text

    # ----- main -----

    def anonymize_text(self, text: str) -> str:
        self._extract_persons(text)
        text = self._replace_persons(text)
        text = self._replace_other_entities(text)
        return text

    def anonymize_docx(self, input_path: str, output_path: str, json_map: str, txt_map: str):
        doc = Document(input_path)

        # seber celý text pro první průchod (registrace osob)
        full_text = []
        for p in iter_paragraphs(doc):
            full_text.append(clean_invisibles(get_text(p)))
        source_text = '\\n'.join(full_text)

        self._extract_persons(source_text)

        # nahraď v jednotlivých odstavcích
        for p in iter_paragraphs(doc):
            original = get_text(p)
            if not original.strip():
                continue
            cleaned = clean_invisibles(original)
            cleaned = self._replace_persons(cleaned)
            cleaned = self._replace_other_entities(cleaned)
            if cleaned != original:
                set_text(p, cleaned)

        # ulož dokument
        doc.save(output_path)

        # ulož mapy
        with open(json_map, 'w', encoding='utf-8') as f:
            json.dump({k: v for k, v in self.tag_map.items()}, f, ensure_ascii=False, indent=2)

        with open(txt_map, 'w', encoding='utf-8') as f:
            sections = [
                ("OSOBY", "PERSON"),
                ("BANKOVNÍ ÚČTY", "BANK"),
                ("IDENTIFIKÁTORY (IČO/RČ)", "ICO|IDCZ"),
                ("DATA", "DATE"),
                ("ADRESY", "ADDRESS"),
            ]
            for title, prefix in sections:
                f.write(f"{title}\\n{'-'*len(title)}\\n")
                for tag, vals in sorted(self.tag_map.items()):
                    if re.match(rf'^\\[\\[({prefix})_', tag):
                        for v in vals:
                            f.write(f"{tag}: {v}\\n")
                f.write("\\n")

# ===================== CLI =====================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CZ DOCX anonymizer – jména řízená knihovnou")
    parser.add_argument("docx_path", help="Vstupní .docx soubor")
    parser.add_argument("--names-json", default="cz_names.v1.json", help="Cesta ke knihovně jmen (JSON)")
    args = parser.parse_args()

    # načti knihovnu jmen
    load_names_library(args.names_json)

    in_path = Path(args.docx_path)
    if not in_path.exists():
        print(f"❌ Soubor nenalezen: {in_path}")
        return 1

    base = in_path.with_suffix('')
    out_docx = base.parent / f"{base.name}_anon.docx"
    out_json = base.parent / f"{base.name}_map.json"
    out_txt  = base.parent / f"{base.name}_map.txt"

    print(f"🔍 Zpracovávám: {in_path.name}")
    az = Anonymizer()
    az.anonymize_docx(str(in_path), str(out_docx), str(out_json), str(out_txt))

    print("✅ Hotovo:")
    print(f" - {out_docx}")
    print(f" - {out_json}")
    print(f" - {out_txt}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
