# -*- coding: utf-8 -*-
"""
Czech DOCX Anonymizer – Complete v7.0
- Načítá jména z JSON knihovny (cz_names.v1.json)
- Kompletní anonymizace podle GDPR
- Vylepšená detekce adres, osob, kontaktů
Výstupy: <basename>_anon.docx / _map.json / _map.txt
"""

import sys, re, json, unicodedata
from typing import Optional, Set
from pathlib import Path
from collections import defaultdict, OrderedDict
from docx import Document
from datetime import datetime

# =============== Globální proměnné ===============
CZECH_FIRST_NAMES = set()

# =============== Načítání knihovny jmen ===============
def load_names_library(json_path: str = "cz_names.v1.json") -> Set[str]:
    """Načte česká jména z JSON souboru."""
    try:
        script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        json_file = script_dir / json_path

        if not json_file.exists():
            json_file = Path.cwd() / json_path

        if not json_file.exists():
            print(f"⚠️  Varování: {json_path} nenalezen, používám prázdnou knihovnu!")
            return set()

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            names = set()
            if isinstance(data, dict):
                # Nová struktura: {"firstnames": {"M": [...], "F": [...], "U": [...]}}
                if 'firstnames' in data:
                    firstnames = data['firstnames']
                    if isinstance(firstnames, dict):
                        for gender_key in ['M', 'F', 'U']:
                            if gender_key in firstnames:
                                names.update(firstnames[gender_key])
                # Stará struktura: {"male": [...], "female": [...]}
                else:
                    names.update(data.get('male', []))
                    names.update(data.get('female', []))
            elif isinstance(data, list):
                names.update(data)

            # Převod na lowercase pro jednodušší porovnávání
            names = {name.lower() for name in names}
            print(f"✓ Načteno {len(names)} jmen z knihovny")
            return names
    except Exception as e:
        print(f"⚠️  Chyba při načítání {json_path}: {e}")
        return set()

# =============== Varianty pro nahrazování ===============
def variants_for_first(first: str) -> set:
    """Generuje všechny pádové varianty křestního jména."""
    f = first.strip()
    if not f: return {''}

    V = {f, f.lower(), f.capitalize()}
    low = f.lower()

    # Ženská jména na -a
    if low.endswith('a'):
        stem = f[:-1]
        # 7 pádů: nominativ, genitiv, dativ, akuzativ, vokativ, lokál, instrumentál
        V |= {stem+'y', stem+'e', stem+'ě', stem+'u', stem+'ou', stem+'o'}
        # Přivlastňovací: Janin, Petřina
        V |= {stem+s for s in ['in','ina','iny','iné','inu','inou','iným','iných']}
        # Speciální případy
        if stem.endswith('tr'):
            V |= {stem[:-1]+'ř'+s for s in ['in','ina','iny','iné','inu','inou']}
    else:
        # Mužská jména
        V |= {f+'a', f+'ovi', f+'e', f+'em', f+'u', f+'om'}
        # Přivlastňovací: Petrův, Pavlův
        V |= {f+'ův'} | {f+'ov'+s for s in ['a','o','y','ě','ým','ých']}
        # Speciální případy
        if low.endswith('ek'): V.add(f[:-2] + 'ka')
        if low.endswith('el'): V.add(f[:-2] + 'la')
        if low.endswith('ec'): V.add(f[:-2] + 'ce')

    # Bez diakritiky
    V |= {unicodedata.normalize('NFKD', v).encode('ascii','ignore').decode('ascii') for v in list(V)}
    return V

def variants_for_surname(surname: str) -> set:
    """Generuje všechny pádové varianty příjmení."""
    s = surname.strip()
    if not s: return {''}

    out = {s, s.lower(), s.capitalize()}
    low = s.lower()

    # Ženská příjmení na -ová
    if low.endswith('ová'):
        base = s[:-1]
        out |= {s, base+'é', base+'ou'}
        return out

    # Přídavná jména -ský, -cký, -ý
    if low.endswith(('ský','cký','ý')):
        if low.endswith(('ský','cký')):
            stem = s[:-2]
        else:
            stem = s[:-1]
        out |= {stem+'ý', stem+'ého', stem+'ému', stem+'ým', stem+'ém'}
        out |= {stem+'á', stem+'é', stem+'ou'}
        return out

    # Ženská na -á
    if low.endswith('á'):
        stem = s[:-1]
        out |= {s, stem+'é', stem+'ou'}
        return out

    # Speciální případy
    if low.endswith('ek') and len(s) >= 3:
        stem_k = s[:-2] + 'k'
        out |= {s, stem_k+'a', stem_k+'ovi', stem_k+'em', stem_k+'u', stem_k+'e'}
        return out

    if low.endswith('el') and len(s) >= 3:
        stem_l = s[:-2] + 'l'
        out |= {s, stem_l+'a', stem_l+'ovi', stem_l+'em', stem_l+'u'}
        return out

    if low.endswith('ec') and len(s) >= 3:
        stem_c = s[:-2] + 'c'
        out |= {s, stem_c+'e', stem_c+'i', stem_c+'em', stem_c+'u'}
        return out

    # Standardní mužská příjmení
    out |= {s+'a', s+'ovi', s+'e', s+'em', s+'u', s+'ům', s+'em'}
    # Množné číslo: u Nováků
    out |= {s+'ů', s+'ům'}

    return out

# =============== Inference funkcí ===============
def _male_genitive_to_nominative(obs: str) -> Optional[str]:
    """Převede pozorovaný tvar (např. genitiv) na nominativ pro mužská jména."""
    lo = obs.lower()
    cands = []

    # Speciální případy: -ka → -ek, -la → -el
    if lo.endswith('ka') and len(obs) > 2:
        cands.append(obs[:-2] + 'ek')
    if lo.endswith('la') and len(obs) > 2:
        cands.append(obs[:-2] + 'el')
    if lo.endswith('ce') and len(obs) > 2:
        cands.append(obs[:-2] + 'ec')

    # Genitiv/Dativ: -a → remove
    if lo.endswith('a') and len(obs) > 1:
        cands.append(obs[:-1])

    # Dativ: -ovi → remove
    if lo.endswith('ovi') and len(obs) > 3:
        cands.append(obs[:-3])

    # Instrumentál: -em → remove
    if lo.endswith('em') and len(obs) > 2:
        cands.append(obs[:-2])

    for c in cands:
        if c.lower() in CZECH_FIRST_NAMES:
            return c.capitalize()

    return cands[0].capitalize() if cands else None

def infer_first_name_nominative(obs: str) -> str:
    """Odhadne nominativ křestního jména z pozorovaného tvaru."""
    lo = obs.lower()

    # DŮLEŽITÉ: Kontrola, zda už je v nominativu (v knihovně jmen)
    if lo in CZECH_FIRST_NAMES:
        return obs.capitalize()

    # Speciální případy - zkrácená jména (Han → Hana, Mart → Marta, Martin → Martina)
    # Priorita: nejdřív zkus +ina (pro Martin → Martina), pak +a
    if lo + 'ina' in CZECH_FIRST_NAMES:
        return (obs + 'ina').capitalize()
    if lo + 'a' in CZECH_FIRST_NAMES:
        return (obs + 'a').capitalize()

    # Ženská jména - pádové varianty
    if lo.endswith(('y', 'ě', 'e', 'u', 'ou')):
        # Zkus -a variantu
        stem = obs[:-1] if not lo.endswith('ou') else obs[:-2]
        if (stem + 'a').lower() in CZECH_FIRST_NAMES:
            return (stem + 'a').capitalize()

    # Mužská jména - genitiv/dativ/instrumentál
    male_nom = _male_genitive_to_nominative(obs)
    if male_nom:
        return male_nom

    # Pokud nic nepomohlo, vrať původní tvar s velkým písmenem
    return obs.capitalize()

def infer_surname_nominative(obs: str) -> str:
    """Odhadne nominativ příjmení z pozorovaného tvaru."""
    lo = obs.lower()

    # Ženská příjmení -ové, -ou → -ová
    if lo.endswith('é') and len(obs) > 3:
        return obs[:-1] + 'á'
    if lo.endswith('ou') and len(obs) > 3:
        return obs[:-2] + 'á'

    # Přídavná jména
    if lo.endswith(('ého', 'ému', 'ým', 'ém')):
        if lo.endswith('ého'):
            return obs[:-3] + 'ý'
        elif lo.endswith('ému'):
            return obs[:-3] + 'ý'
        elif lo.endswith('ým'):
            return obs[:-2] + 'ý'
        elif lo.endswith('ém'):
            return obs[:-2] + 'ý'

    # Speciální -ka, -la, -ce → -ek, -el, -ec (ale ne běžná příjmení!)
    common_surnames_a = {'svoboda', 'skála', 'hora', 'kula', 'hala'}
    if lo.endswith('ka') and len(obs) > 3 and lo not in common_surnames_a:
        return obs[:-2] + 'ek'
    if lo.endswith('la') and len(obs) > 3 and lo not in common_surnames_a:
        return obs[:-2] + 'el'
    if lo.endswith('ce') and len(obs) > 3:
        return obs[:-2] + 'ec'

    # Dativ -ovi → remove (ale jen pokud je to opravdu dativ, ne součást jména)
    if lo.endswith('ovi') and len(obs) > 5:
        return obs[:-3]

    # Instrumentál -em → remove (ale jen pokud je to opravdu instrumentál)
    if lo.endswith('em') and len(obs) > 4 and not lo.endswith(('em', 'lem', 'rem')):
        return obs[:-2]

    # Genitiv -a → NEODSTRAŇUJ! Mnoho příjmení končí na -a v nominativu (Svoboda, Skála, atd.)
    # Tato pravidla jsou příliš riskantní

    return obs

# =============== Regexy ===============

# Vylepšený ADDRESS_RE - zachytává adresy i bez prefixů
ADDRESS_RE = re.compile(
    r'(?<!\[)'
    r'(?:'
    r'(?:(?:trvale\s+)?bytem\s+|'
    r'(?:trvalé\s+)?bydlišt[eě]\s*:\s*|'
    r'(?:sídlo(?:\s+podnikání)?|se\s+sídlem)\s*:\s*|'
    r'(?:místo\s+podnikání)\s*:\s*|'
    r'(?:adresa|trvalý\s+pobyt)\s*:\s*|'
    r'(?:v\s+ulic[ií]|na\s+(?:adrese|ulici)|v\s+dom[eě])\s+)?'
    r')'
    r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]'
    r'[a-záčďéěíňóřšťúůýž\s]{2,50}?'
    r'\s+\d{1,4}(?:/\d{1,4})?'
    r',\s*'
    r'\d{3}\s?\d{2}'
    r'\s+'
    r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž\s]{1,30}'
    r'(?:\s+\d{1,2})?'
    r'(?=\s|$|,|\.|;|:|\n|\r|Rodné|IČO|DIČ|Tel|E-mail|Kontakt|OP|Datum|Narozen)',
    re.IGNORECASE | re.UNICODE
)

# SPZ/RZ
LICENSE_PLATE_RE = re.compile(
    r'\b\d[A-Z]{2}\s?\d{4}\b',
    re.IGNORECASE
)

# IČO (8 číslic)
ICO_RE = re.compile(
    r'(?:IČO?\s*:?\s*)?(?<!\d)(\d{8})(?!\d)',
    re.IGNORECASE
)

# DIČ (CZ + 8-10 číslic)
DIC_RE = re.compile(
    r'\b(CZ\d{8,10})\b',
    re.IGNORECASE
)

# Rodné číslo (6 číslic / 3-4 číslice)
BIRTH_ID_RE = re.compile(
    r'\b(\d{6}/\d{3,4})\b'
)

# Číslo OP (formát: AB 123456)
ID_CARD_RE = re.compile(
    r'\b([A-Z]{2}\s?\d{6})\b'
)

# Email
EMAIL_RE = re.compile(
    r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
)

# Telefon (CZ formáty) - vylepšený, aby nezachytával čísla OP a bankovní účty
PHONE_RE = re.compile(
    r'(?:tel\.?|telefon|mobil|GSM)?\s*:?\s*'  # Volitelný prefix
    r'(?:'
    r'\+420\s?\d{3}\s?\d{3}\s?\d{3}|'  # +420 xxx xxx xxx
    r'\+420\s?\d{3}\s?\d{2}\s?\d{2}\s?\d{2}|'  # +420 xxx xx xx xx
    r'(?<!\d)\d{3}\s?\d{3}\s?\d{3}(?!\d)|'  # xxx xxx xxx (bez okolních číslic)
    r'(?<!\d)\d{3}\s?\d{2}\s?\d{2}\s?\d{2}(?!\d)'  # xxx xx xx xx
    r')',
    re.IGNORECASE
)

# Bankovní účet (formát: číslo/kód banky nebo IBAN)
BANK_RE = re.compile(
    r'\b(\d{6,16}/\d{4})\b|'
    r'\b([A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}(?:\s?\d{0,4})?)\b',
    re.IGNORECASE
)

# Datum (DD.MM.YYYY nebo DD. MM. YYYY)
DATE_RE = re.compile(
    r'\b(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})\b'
)

# Datum slovně (např. "15. března 2024")
DATE_WORDS_RE = re.compile(
    r'\b(\d{1,2}\.\s?(?:ledna|února|března|dubna|května|června|července|srpna|září|října|listopadu|prosince)\s?\d{4})\b',
    re.IGNORECASE
)

# =============== Třída Anonymizer ===============
class Anonymizer:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.counter = defaultdict(int)
        self.canonical_persons = OrderedDict()  # canonical -> label
        self.entity_map = defaultdict(lambda: defaultdict(set))  # typ -> original -> varianty

    def _get_or_create_label(self, typ: str, original: str) -> str:
        """Vrátí existující nebo vytvoří nový štítek pro entitu."""
        # Normalizace
        orig_norm = original.strip()

        # Zkontroluj, zda už existuje
        for existing_orig, variants in self.entity_map[typ].items():
            if orig_norm in variants or orig_norm == existing_orig:
                self.counter[typ] += 1
                return f"[[{typ}_{list(self.entity_map[typ].keys()).index(existing_orig) + 1}]]"

        # Vytvoř nový
        self.counter[typ] += 1
        idx = len(self.entity_map[typ]) + 1
        self.entity_map[typ][orig_norm].add(orig_norm)
        return f"[[{typ}_{idx}]]"

    def _apply_known_people(self, text: str) -> str:
        """Aplikuje známé osoby (již detekované)."""
        for canonical, label in self.canonical_persons.items():
            # Vygeneruj všechny varianty
            parts = canonical.split()
            if len(parts) == 2:
                first, last = parts
                first_vars = variants_for_first(first)
                last_vars = variants_for_surname(last)

                # Všechny kombinace
                for fv in first_vars:
                    for lv in last_vars:
                        if fv and lv:
                            pattern = rf'\b{re.escape(fv)}\s+{re.escape(lv)}\b'
                            text = re.sub(pattern, label, text, flags=re.IGNORECASE)

        return text

    def _replace_remaining_people(self, text: str) -> str:
        """Detekuje a nahradí zbývající osoby."""
        # Hledá vzory: Jméno Příjmení
        # Nejprve tituly
        titles = r'(?:Ing\.|Mgr\.|Bc\.|MUDr\.|JUDr\.|PhDr\.|RNDr\.|Ph\.D\.|MBA|CSc\.|DrSc\.)'

        # Pattern pro jméno příjmení s volitelným titulem
        person_pattern = re.compile(
            rf'(?:{titles}\s+)?'
            r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)'
            r'\s+'
            r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)',
            re.UNICODE
        )

        def replace_person(match):
            first_obs = match.group(1)
            last_obs = match.group(2)

            # Rozšířený seznam slov k ignorování
            ignore_words = {
                # Běžná slova ve smlouvách
                'místo', 'datum', 'částku', 'bytem', 'sídlo', 'adresa',
                'číslo', 'kontakt', 'telefon', 'email', 'rodné', 'narozena',
                'vydán', 'uzavřena', 'podepsána', 'smlouva', 'dohoda',
                # Místa
                'staré', 'město', 'nové', 'město', 'malá', 'strana',
                'václavské', 'náměstí', 'hlavní', 'nádraží',
                # Organizace/instituce klíčová slova
                'česká', 'spořitelna', 'komerční', 'banka', 'raiffeisen',
                'credit', 'bank', 'financial', 'global', 'senior',
                'junior', 'lead', 'chief', 'head', 'director',
                # Pozice/role
                'jednatel', 'jednatelka', 'ředitel', 'ředitelka',
                'auditor', 'manager', 'consultant', 'specialist',
                'assistant', 'coordinator', 'analyst', 'pacient',
                'scrum', 'master', 'developer', 'architect', 'engineer',
                'officer', 'professional', 'certified', 'advanced',
                # Pozdravy/oslovení
                'ahoj', 'dobrý', 'den', 'vážený', 'vážená',
                # Značky aut
                'škoda', 'octavia', 'fabia', 'superb', 'kodiaq',
                'volkswagen', 'toyota', 'ford', 'bmw', 'audi',
                # Technologie a software
                'google', 'amazon', 'microsoft', 'apple', 'facebook',
                'cloud', 'web', 'tech', 'solutions', 'data', 'digital',
                'software', 'enterprise', 'premium', 'standard',
                'analytics', 'computer', 'vision', 'protection',
                'security', 'authenticator', 'repository', 'access',
                'personal', 'hub', 'book', 'pro', 'series', 'launch',
                'team', 'development', 'react', 'splunk', 'innovate',
                'ventures', 'credo', 'mayo', 'clinic', 'met', 'london',
                'avenue', 'contractual', 'plánovaná', 'diagno',
                # Zdravotnictví
                'nemocnice', 'poliklinika', 'polikliniek', 'nemocniec',
                # Další
                'care', 'plus', 'minus', 'medical', 'health',
                'service', 'services', 'group', 'company', 'corp', 'ltd'
            }

            # Kontrola proti ignore listu
            if first_obs.lower() in ignore_words or last_obs.lower() in ignore_words:
                return match.group(0)

            # Detekce anglických/technických názvů (obsahují typicky anglická slova)
            combined = f"{first_obs} {last_obs}".lower()
            tech_patterns = [
                r'\b(tech|cloud|web|solutions?|data|digital|software|analytics)\b',
                r'\b(team|hub|enterprise|premium|standard|professional)\b',
                r'\b(google|amazon|microsoft|apple|facebook|splunk)\b',
                r'\b(repository|authenticator|vision|protection|security)\b',
                r'\b(ventures|clinic|series|launch|innovate)\b'
            ]
            for pattern in tech_patterns:
                if re.search(pattern, combined):
                    return match.group(0)

            # Detekce názvů firem (končí na s.r.o., a.s., spol., Ltd. atd.)
            context_after = text[match.end():match.end()+20]
            if re.search(r'^\s*(s\.r\.o\.|a\.s\.|spol\.|k\.s\.|v\.o\.s\.|ltd\.?|inc\.?)', context_after, re.IGNORECASE):
                return match.group(0)

            # Nejdřív inference příjmení
            last_nom = infer_surname_nominative(last_obs)

            # Určení rodu podle příjmení
            is_female_surname = last_nom.lower().endswith(('ová', 'á'))

            # Inference křestního jména podle rodu příjmení
            first_lo = first_obs.lower()

            # Pokud příjmení je ženské, jméno musí být ženské
            if is_female_surname:
                # Han → Hana, Martin → Martina
                # Pravidlo: pokud jméno končí na souhlásku, přidej 'a'
                if not first_lo.endswith(('a', 'e', 'i', 'o', 'u', 'y')):
                    # Jméno končí na souhlásku → přidej 'a'
                    first_nom = (first_obs + 'a').capitalize()
                elif first_lo.endswith('a'):
                    # Jméno už končí na 'a' → je to pravděpodobně nominativ ženského jména, ponech
                    first_nom = first_obs.capitalize()
                else:
                    # Jiné koncovky → zkus inference
                    first_nom = infer_first_name_nominative(first_obs)
            else:
                # Příjmení je mužské, jméno musí být mužské
                # Jana → Jan, Petra → Petr (odstraň 'a' pokud je to genitiv)
                if first_lo.endswith('a') and len(first_lo) > 2:
                    # Výjimky - skutečná mužská jména končící na 'a'
                    male_names_with_a = {'kuba', 'míla', 'nikola', 'saša', 'jirka', 'honza'}
                    if first_lo in male_names_with_a:
                        first_nom = first_obs.capitalize()
                    else:
                        # Odstraň koncové 'a'
                        first_nom = first_obs[:-1].capitalize()
                elif first_lo.endswith(('u', 'e', 'em', 'ovi', 'ům')):
                    # Typické pádové koncovky → použij inference
                    first_nom = infer_first_name_nominative(first_obs)
                else:
                    # Jiné (pravděpodobně nominativ) → ponech jak je
                    first_nom = first_obs.capitalize()

            canonical = f"{first_nom} {last_nom}"

            # Získej nebo vytvoř label
            if canonical not in self.canonical_persons:
                idx = len(self.canonical_persons) + 1
                label = f"[[PERSON_{idx}]]"
                self.canonical_persons[canonical] = label
            else:
                label = self.canonical_persons[canonical]

            return label

        text = person_pattern.sub(replace_person, text)
        return text

    def anonymize_entities(self, text: str) -> str:
        """Anonymizuje všechny entity (adresy, kontakty, IČO, atd.)."""

        # DŮLEŽITÉ: Pořadí je klíčové! Od nejvíce specifických po nejméně specifické

        # 1. ADRESY (PRVNÍ! Předtím než se "Novákova 45" stane osobou)
        def replace_address(match):
            return self._get_or_create_label('ADDRESS', match.group(0))
        text = ADDRESS_RE.sub(replace_address, text)

        # 2. EMAILY (před telefony, protože obsahují čísla)
        def replace_email(match):
            return self._get_or_create_label('EMAIL', match.group(1))
        text = EMAIL_RE.sub(replace_email, text)

        # 3. RODNÁ ČÍSLA (před čísly OP a telefony)
        def replace_birth_id(match):
            return self._get_or_create_label('BIRTH_ID', match.group(1))
        text = BIRTH_ID_RE.sub(replace_birth_id, text)

        # 4. ČÍSLA OP (před telefony!)
        def replace_id_card(match):
            return self._get_or_create_label('ID_CARD', match.group(1))
        text = ID_CARD_RE.sub(replace_id_card, text)

        # 5. BANKOVNÍ ÚČTY (před telefony!)
        def replace_bank(match):
            account = match.group(1) if match.group(1) else match.group(2)
            if account:
                return self._get_or_create_label('BANK', account)
            return match.group(0)
        text = BANK_RE.sub(replace_bank, text)

        # 6. DIČ (před IČO)
        def replace_dic(match):
            return self._get_or_create_label('DIC', match.group(1))
        text = DIC_RE.sub(replace_dic, text)

        # 7. IČO
        def replace_ico(match):
            full = match.group(0)
            # Ale ne pokud je to DIČ (CZ prefix)
            if 'CZ' in full.upper():
                return full
            # A ne pokud je to rodné číslo
            if '/' in full:
                return full
            # A ne pokud je to číslo OP
            if match.group(1):
                return self._get_or_create_label('ICO', match.group(1))
            return full
        text = ICO_RE.sub(replace_ico, text)

        # 8. SPZ
        def replace_license_plate(match):
            return self._get_or_create_label('SPZ', match.group(0))
        text = LICENSE_PLATE_RE.sub(replace_license_plate, text)

        # 9. TELEFONY (AŽ NAKONEC! Po všech číselných identifikátorech)
        def replace_phone(match):
            return self._get_or_create_label('PHONE', match.group(0))
        text = PHONE_RE.sub(replace_phone, text)

        return text

    def anonymize_docx(self, input_path: str, output_path: str, json_map: str, txt_map: str):
        """Hlavní metoda pro anonymizaci DOCX dokumentu."""
        print(f"\n🔍 Zpracovávám: {Path(input_path).name}")

        # Načti dokument
        doc = Document(input_path)

        # Zpracuj všechny odstavce
        for para in doc.paragraphs:
            if not para.text.strip():
                continue

            original = para.text

            # POŘADÍ JE KLÍČOVÉ!
            # 1. Nejprve anonymizuj entity (adresy, IČO, telefony...)
            text = self.anonymize_entities(original)

            # 2. Potom aplikuj známé osoby
            text = self._apply_known_people(text)

            # 3. Nakonec detekuj nové osoby
            text = self._replace_remaining_people(text)

            if text != original:
                para.text = text

        # Zpracuj tabulky
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if not para.text.strip():
                            continue

                        original = para.text
                        text = self.anonymize_entities(original)
                        text = self._apply_known_people(text)
                        text = self._replace_remaining_people(text)

                        if text != original:
                            para.text = text

        # Ulož dokument
        doc.save(output_path)

        # Vytvoř mapy
        self._create_maps(json_map, txt_map, input_path)

        print(f"✅ Hotovo! Nalezeno {len(self.canonical_persons)} osob")

    def _create_maps(self, json_path: str, txt_path: str, source_file: str):
        """Vytvoří JSON a TXT mapy náhrad."""

        # JSON mapa
        json_data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "source_file": Path(source_file).name,
            "entities": []
        }

        # Osoby
        for canonical, label in self.canonical_persons.items():
            json_data["entities"].append({
                "type": "PERSON",
                "label": label,
                "original": canonical,
                "occurrences": 1
            })

        # Ostatní entity
        for typ, entities in self.entity_map.items():
            for idx, (original, variants) in enumerate(entities.items(), 1):
                json_data["entities"].append({
                    "type": typ,
                    "label": f"[[{typ}_{idx}]]",
                    "original": original,
                    "occurrences": len(variants)
                })

        # Ulož JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        # TXT mapa
        with open(txt_path, 'w', encoding='utf-8') as f:
            # Osoby
            if self.canonical_persons:
                f.write("OSOBY\n")
                for canonical, label in self.canonical_persons.items():
                    f.write(f"{label}: {canonical}\n")
                f.write("\n")

            # Ostatní entity
            for typ, entities in sorted(self.entity_map.items()):
                if entities:
                    f.write(f"{typ}\n")
                    for idx, (original, variants) in enumerate(entities.items(), 1):
                        label = f"[[{typ}_{idx}]]"
                        f.write(f"{label}: {original}\n")
                    f.write("\n")

# =============== Batch processing ===============
def batch_anonymize(folder_path, names_json="cz_names.v1.json"):
    """Zpracuje všechny DOCX soubory v adresáři."""
    folder = Path(folder_path)
    docx_files = sorted([f for f in folder.glob("*.docx") if not f.name.startswith('~') and '_anon' not in f.name])

    if not docx_files:
        print(f"Nebyly nalezeny žádné .docx soubory v adresáři {folder_path}")
        return

    print(f"\n📁 Zpracovávám {len(docx_files)} souborů v adresáři {folder_path}\n")

    global CZECH_FIRST_NAMES
    CZECH_FIRST_NAMES = load_names_library(names_json)

    for path in docx_files:
        print(f"\n{'='*60}")
        base = path.stem
        out_docx = path.parent / f"{base}_anon.docx"
        out_json = path.parent / f"{base}_map.json"
        out_txt = path.parent / f"{base}_map.txt"

        try:
            a = Anonymizer(verbose=False)
            a.anonymize_docx(str(path), str(out_docx), str(out_json), str(out_txt))
            print(f"✅ Výstupy: {out_docx.name}, {out_json.name}, {out_txt.name}")
        except Exception as e:
            print(f"❌ CHYBA při zpracování {path.name}: {e}")
            import traceback
            traceback.print_exc()

# =============== Main ===============
def main():
    import argparse
    ap = argparse.ArgumentParser(description="Anonymizace českých DOCX s JSON knihovnou jmen")
    ap.add_argument("docx_path", nargs='?', help="Cesta k .docx souboru nebo adresáři")
    ap.add_argument("--names-json", default="cz_names.v1.json", help="Cesta k JSON knihovně jmen")
    ap.add_argument("--batch", action="store_true", help="Zpracovat všechny .docx v adresáři")
    args = ap.parse_args()

    try:
        global CZECH_FIRST_NAMES
        CZECH_FIRST_NAMES = load_names_library(args.names_json)

        if args.batch and args.docx_path:
            batch_anonymize(args.docx_path, args.names_json)
            return 0

        if args.batch and not args.docx_path:
            # Batch mode v aktuálním adresáři
            batch_anonymize(".", args.names_json)
            return 0

        # Single file mode
        if not args.docx_path:
            print("❌ Chybí cesta k souboru. Použij: python script.py <soubor.docx>")
            print("   Nebo: python script.py --batch <adresář>")
            return 2

        path = Path(args.docx_path)
        if not path.exists():
            print(f"❌ Soubor nenalezen: {path}")
            return 2

        base = path.stem
        out_docx = path.parent / f"{base}_anon.docx"
        out_json = path.parent / f"{base}_map.json"
        out_txt = path.parent / f"{base}_map.txt"

        # Kontrola zamčených souborů
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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_docx = path.parent / f"{base}_anon_{timestamp}.docx"
            out_json = path.parent / f"{base}_map_{timestamp}.json"
            out_txt = path.parent / f"{base}_map_{timestamp}.txt"
            print(f"\n⚠️  Výstupní soubory jsou otevřené v jiné aplikaci!")
            print(f"   Vytvářím nové soubory s časovým razítkem: {timestamp}\n")

        a = Anonymizer(verbose=False)
        a.anonymize_docx(str(path), str(out_docx), str(out_json), str(out_txt))

        print(f"\n✅ Výstupy:")
        print(f" - {out_docx}")
        print(f" - {out_json}")
        print(f" - {out_txt}")
        print(f"\n📊 Statistiky:")
        print(f" - Nalezeno osob: {len(a.canonical_persons)}")
        print(f" - Celkem entit: {sum(len(e) for e in a.entity_map.values())}")

        return 0

    except Exception as e:
        print(f"\n❌ CHYBA: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
