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
CZECH_FIRST_NAMES_GENDER = {}  # {name_lowercase: gender} např. {'irene': 'F', 'pavel': 'M'}

# Mužská příjmení končící na -a v nominativu
# DŮLEŽITÉ: Používá se v infer_surname_nominative a variants_for_surname
# Obsahuje tvary S diakritikou i BEZ diakritiky (pro normalizaci)
MALE_SURNAMES_WITH_A = {
    'svoboda', 'skala', 'hora', 'kula', 'hala', 'krejca', 'krejča',
    'liska', 'liška', 'vrba', 'ryba', 'kocka', 'kočka', 'sluka', 'janda',
    'prochazka', 'procházka', 'blaha', 'kafka', 'smetana', 'brabec',
    'kuratka', 'kuřátka', 'kubicka', 'kubíčka', 'marecka', 'marečka', 'vasicka', 'vašíčka',
    'sembera', 'šembera', 'klement', 'slama', 'sláma', 'seda', 'šeda',
    'vrana', 'vala', 'vála', 'pala',
    'vojta', 'hruska', 'hruška',  # Can be both first names and surnames
    'krupicka', 'krupička', 'popelka', 'vlna'  # Male surnames with -a (some with vložné e)
}

# =============== Načítání knihovny jmen ===============
def load_names_library(json_path: str = "cz_names.v1.json") -> Set[str]:
    """Načte česká jména z JSON souboru a uloží i gender informace."""
    global CZECH_FIRST_NAMES_GENDER

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
            CZECH_FIRST_NAMES_GENDER = {}

            if isinstance(data, dict):
                # Nová struktura: {"firstnames": {"M": [...], "F": [...], "U": [...]}}
                if 'firstnames' in data:
                    firstnames = data['firstnames']
                    if isinstance(firstnames, dict):
                        for gender_key in ['M', 'F', 'U']:
                            if gender_key in firstnames:
                                for name in firstnames[gender_key]:
                                    names.add(name)
                                    # Uložení gender informace
                                    CZECH_FIRST_NAMES_GENDER[name.lower()] = gender_key
                # Stará struktura: {"male": [...], "female": [...]}
                else:
                    for name in data.get('male', []):
                        names.add(name)
                        CZECH_FIRST_NAMES_GENDER[name.lower()] = 'M'
                    for name in data.get('female', []):
                        names.add(name)
                        CZECH_FIRST_NAMES_GENDER[name.lower()] = 'F'
            elif isinstance(data, list):
                names.update(data)
                # Pro list formát nemáme gender info

            # Převod na lowercase pro jednodušší porovnávání
            names = {name.lower() for name in names}
            print(f"✓ Načteno {len(names)} jmen z knihovny (gender info: {len(CZECH_FIRST_NAMES_GENDER)})")
            return names
    except Exception as e:
        print(f"⚠️  Chyba při načítání {json_path}: {e}")
        return set()

# =============== Varianty pro nahrazování ===============
def variants_for_first(first: str) -> set:
    """Generuje základní pádové varianty křestního jména (optimalizováno pro výkon)."""
    f = first.strip()
    if not f: return {''}

    V = {f, f.lower(), f.capitalize()}
    low = f.lower()

    # Ženská jména na -a
    if low.endswith('a'):
        stem = f[:-1]
        # 7 pádů: nominativ, genitiv, dativ, akuzativ, vokativ, lokál, instrumentál
        V |= {stem+'y', stem+'e', stem+'ě', stem+'u', stem+'ou', stem+'o'}
    else:
        # Mužská jména
        V |= {f+'a', f+'ovi', f+'e', f+'em', f+'u', f+'om'}
        # Speciální případy
        if low.endswith('ek'): V.add(f[:-2] + 'ka')
        if low.endswith('el'): V.add(f[:-2] + 'la')
        if low.endswith('ec'): V.add(f[:-2] + 'ce')

    # Bez diakritiky
    V |= {unicodedata.normalize('NFKD', v).encode('ascii','ignore').decode('ascii') for v in list(V)}
    return V

def variants_for_surname(surname: str) -> set:
    """Generuje základní pádové varianty příjmení (optimalizováno pro výkon)."""
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

    # Mužská příjmení končící na -a (Šembera, Svoboda, Procházka, Vrána, atd.)
    if low.endswith('a') and len(s) >= 3:
        # Používáme GLOBÁLNÍ seznam MALE_SURNAMES_WITH_A
        if low in MALE_SURNAMES_WITH_A:
            # Správné pádové varianty (BEZ přidání další 'a'!)
            stem = s[:-1]
            out |= {
                s,  # nominativ: Šembera
                stem+'y',  # genitiv: Šembery
                stem+'ovi',  # dativ: Šemberovi
                stem+'u',  # akuzativ: Šemberu
                stem+'o',  # vokativ: Šembero
                stem+'ou',  # instrumentál: Šemberou
                stem+'ův',  # přivlastňovací: Šemberův
                stem+'ova', stem+'ovo', stem+'ovou', stem+'ovu', stem+'ově', stem+'ovy', stem+'ových', stem+'ovým',  # přivlastňovací pády
            }
            return out

    # Standardní mužská příjmení (končí na souhlásku)
    out |= {s+'a', s+'ovi', s+'e', s+'em', s+'u', s+'ům', s+'em'}
    # Množné číslo: u Nováků
    out |= {s+'ů', s+'ům'}

    return out

# =============== Inference funkcí ===============
def _male_genitive_to_nominative(obs: str) -> Optional[str]:
    """Převede pozorovaný tvar (např. genitiv) na nominativ pro mužská jména.

    DŮLEŽITÉ: Testuje koncovky s PRIORITOU - nejdřív -u, pak -a.
    Důvod: "Petra" může být genitiv od "Petr" (správně) nebo "Petro" (chybně).
    """
    lo = obs.lower()

    # DEBUG: Trace execution (disabled)
    debug_this = False  # Set to True to enable debug output
    if debug_this:
        print(f"      [_male_gen] INPUT: obs='{obs}', lo='{lo}'")

    # FIRST: Hardcoded list of common feminine names that should NEVER be converted
    # This is necessary because the name library is incomplete (missing Martina, etc.)
    common_feminine_names = {
        'martina', 'jana', 'petra', 'eva', 'anna', 'marie', 'lenka', 'kateřina',
        'alena', 'hana', 'lucie', 'veronika', 'monika', 'jitka', 'zuzana', 'ivana',
        'tereza', 'barbora', 'andrea', 'michaela', 'simona', 'nikola', 'pavla',
        'daniela', 'alexandra', 'kristýna', 'markéta', 'renata', 'šárka', 'karolína'
    }

    if lo in common_feminine_names:
        return None  # Don't convert feminine names to masculine

    # PRIORITA 0: Pokud jméno končí na 'a'/'u' a base forma je v knihovně nebo vypadá jako mužské jméno, preferuj ji
    # Důvod: "davida" je v knihovně jako zastaralá forma, ale měli bychom preferovat "David"
    # "petru" je v knihovně, ale "petr" také → preferuj "Petr"
    if lo.endswith(('a', 'u')) and len(obs) > 2:
        base = obs[:-1]
        base_lo = base.lower()

        if debug_this:
            print(f"      [_male_gen] PRIORITA 0: base='{base}', base_lo='{base_lo}'")
            print(f"      [_male_gen] base_lo in CZECH_FIRST_NAMES: {base_lo in CZECH_FIRST_NAMES}")
            print(f"      [_male_gen] lo in CZECH_FIRST_NAMES: {lo in CZECH_FIRST_NAMES}")

        # Strategie 1: Pokud base je v knihovně a není ženské jméno
        if base_lo in CZECH_FIRST_NAMES:
            # Base existuje - preferuj ho pokud není ženské (nekončí na 'a' v nominativu)
            # nebo je known male name
            if not base_lo.endswith('a') or base_lo in {'kuba', 'míla', 'nikola', 'saša', 'jirka', 'honza'}:
                if debug_this:
                    print(f"      [_male_gen] STRATEGIE 1 RETURN: '{base.capitalize()}'")
                return base.capitalize()

        # Strategie 2: Pokud base končí na souhlásku (typické pro mužská jména)
        # a obs je v knihovně s -a nebo -u (může být genitiv/dativ)
        elif len(base_lo) > 0 and base_lo[-1] not in 'aeiouáéíóúůýě' and lo in CZECH_FIRST_NAMES:
            # "davida" končí na 'a', base "david" končí na 'd' (souhláska)
            # → pravděpodobně genitiv od "David"
            if debug_this:
                print(f"      [_male_gen] STRATEGIE 2 RETURN: '{base.capitalize()}'")
            return base.capitalize()

    # Also check library if available
    if lo in CZECH_FIRST_NAMES and lo.endswith('a'):
        return None  # Don't convert, let the caller handle it

    cands = []

    # PRIORITA 1: Speciální případy -ka → -ek, -la → -el, -ce → -ec
    if lo.endswith('ka') and len(obs) > 2:
        cand = obs[:-2] + 'ek'
        if cand.lower() in CZECH_FIRST_NAMES:
            return cand.capitalize()
        # FALLBACK: Pokud cand vypadá jako validní mužské jméno (5-6 znaků), použij ho
        if 5 <= len(cand) <= 6:
            return cand.capitalize()
        cands.append(cand)

    if lo.endswith('la') and len(obs) > 2:
        cand = obs[:-2] + 'el'
        if cand.lower() in CZECH_FIRST_NAMES:
            return cand.capitalize()
        # FALLBACK: Pokud cand vypadá jako validní mužské jméno
        if 5 <= len(cand) <= 6:
            return cand.capitalize()
        cands.append(cand)

    if lo.endswith('ce') and len(obs) > 2:
        cand = obs[:-2] + 'ec'
        if cand.lower() in CZECH_FIRST_NAMES:
            return cand.capitalize()
        # FALLBACK: Pokud cand vypadá jako validní mužské jméno
        if 5 <= len(cand) <= 6:
            return cand.capitalize()
        cands.append(cand)

    # PRIORITA 2: Dativ/vokativ -ovi → remove (Petrovi → Petr, Tomášovi → Tomáš)
    if lo.endswith('ovi') and len(obs) > 3:
        cand = obs[:-3]

        # EXPLICITNÍ mapování POUZE pro jména, která VÍME, že mají 'o' formu
        # Marc → Marco, Hug → Hugo, Dieg → Diego, Brun → Bruno (tyto jsou VÝJIMKY)
        explicit_o_forms = {
            'marc': 'Marco',
            'hug': 'Hugo',
            'dieg': 'Diego',
            'brun': 'Bruno'
        }
        if cand.lower() in explicit_o_forms:
            return explicit_o_forms[cand.lower()]

        # PRIORITA 1: Standardní check - pokud cand je v knihovně, použij ho
        # Albertovi → Albert (ne Alberto), Olegovi → Oleg (ne Olego), Mihailovi → Mihail (ne Mihailo)
        cand_lo = cand.lower()
        if cand_lo in CZECH_FIRST_NAMES:
            return cand.capitalize()

        # PRIORITA 2: Zkus vložné 'e' (Pavlovi → Pavel)
        cand_o = cand + 'o'

        # Zkus vložné 'e' (Pavlovi → Pavel, Marckovi → Marek)
        if len(cand) >= 2 and cand[-1] in 'lntr':
            cand_with_e = cand[:-1] + 'e' + cand[-1]
            if cand_with_e.lower() in CZECH_FIRST_NAMES:
                return cand_with_e.capitalize()
            # Přidej obě varianty jako kandidáty
            cands.append(cand_with_e)

        # Zkus vložné 'a' na konci (Oldovi → Olda, Renovi → Rena)
        # POUZE pro krátké kmeny (3-4 znaky) které vypadají jako zdrobněliny
        # ALE: NE pro jména končící na 'x' (Alexovi → Alex, ne Alexa)
        if len(cand) >= 2 and len(cand) <= 4 and not cand.lower().endswith('x'):
            cand_with_a = cand + 'a'
            if cand_with_a.lower() in CZECH_FIRST_NAMES:
                return cand_with_a.capitalize()
            # FALLBACK: Pokud cand_with_a vypadá jako validní jméno (končí na souhláska+a)
            if cand[-1] not in 'aeiouáéíóúůýě':
                cands.append(cand_with_a)

        cands.append(cand)

    # PRIORITA 2b: Dativ/vokativ -i → remove (Tomáši → Tomáš, Aleši → Aleš, Lukáši → Lukáš)
    # Ale ne pro jména končící na -i v nominativu (Igor...)
    # DŮLEŽITÉ: Vylučuje -ovi (to se zpracovává výše)
    if lo.endswith('i') and not lo.endswith('ovi') and len(obs) > 2:
        cand = obs[:-1]
        # Zkontroluj, zda odstranění -i dává smysl
        if cand.lower() in CZECH_FIRST_NAMES:
            return cand.capitalize()
        # Fallback: pokud cand končí na š/č/ř/ž (měkké souhlásky), pravděpodobně je to vokativ
        if cand and cand[-1] in 'ščřžj' and len(cand) >= 3:
            return cand.capitalize()
        # Také pro ostatní souhlásky, pokud vypadá jako validní nominativ
        if cand and cand[-1] in 'nldťpbvjk' and len(cand) >= 4:
            return cand.capitalize()

    # PRIORITA 3: Instrumentál -em → remove (Petrem → Petr, Markem → Marek)
    # DŮLEŽITÉ: Vložné 'e' má PRIORITU před knihovnou pro známé kmeny (Markem → Marek, ne Mark)
    if lo.endswith('em') and len(obs) > 2:
        cand = obs[:-2]

        # NEJPRVE zkontroluj, jestli cand není UŽ správný nominativ
        if cand.lower() in CZECH_FIRST_NAMES:
            return cand.capitalize()

        # Zkontroluj, jestli cand VYPADÁ jako validní nominativ (bez potřeby vložného 'e')
        # Validní mužské nominativy typicky končí na: souhlásky kromě několika výjimek
        # DŮLEŽITÉ: Musí být >= 5 znaků, aby "Pavl", "Radk" neprošly
        cand_lo = cand.lower()
        valid_male_endings = ('š', 'n', 'l', 'r', 'm', 'd', 't', 'p', 'b', 'v', 'c', 'č', 'j', 'z', 'ž', 'ň', 'ř', 'ť', 'ď')
        if len(cand) >= 5 and cand_lo[-1] in valid_male_endings:
            # Vypadá jako validní nominativ (Tomáš, Filip, Adrian...)
            return cand.capitalize()

        # Pak zkontroluj vložné 'e' pro známé kmeny
        if len(cand) >= 2:
            vlozne_e_stems = {'mar', 'pav', 'pet', 'ale', 'dan', 'tom', 'jos', 'luk', 'filip', 'petr', 'alex'}
            stem = cand.lower()[:3]
            if stem in vlozne_e_stems or cand.lower() in vlozne_e_stems:
                # Tento kmen vyžaduje vložné 'e'
                cand_with_e = cand[:-1] + 'e' + cand[-1]
                return cand_with_e.capitalize()

        # Nakonec zkus vložné 'e' pro ostatní případy
        if len(cand) >= 2:
            cand_with_e = cand[:-1] + 'e' + cand[-1]
            if cand_with_e.lower() in CZECH_FIRST_NAMES:
                return cand_with_e.capitalize()

        cands.append(cand)

    # PRIORITA 3.5: Ženský instrumentál -ou → -a (Andreou → Andrea, Martinou → Martina)
    # MUSÍ být PŘED zpracováním -u, protože -ou také končí na -u!
    if lo.endswith('ou') and len(obs) > 2:
        stem = obs[:-2]  # "Andreou" → "Andre"
        stem_a = stem + 'a'  # "Andre" + "a" → "Andrea"
        stem_a_lo = stem_a.lower()

        # OBECNÁ HEURISTIKA: Je stem+a pravděpodobně ženské jméno?

        # 1. Zkontroluj knihovnu
        if stem_a_lo in CZECH_FIRST_NAMES:
            return None  # Ženské jméno → zpracuj v infer_first_name_nominative

        # 2. Zkontroluj common_feminine_names
        if stem_a_lo in common_feminine_names:
            return None

        # 3. Pattern matching - typické ženské vzory
        female_patterns = (
            'ina', 'ana', 'ela', 'ara', 'ona', 'ika', 'ála', 'éta',
            'ata', 'ita', 'ota', 'uta', 'ora', 'ura', 'yna', 'ína',
            'éna', 'ána', 'una', 'ia', 'ea'
        )
        if stem_a_lo.endswith(female_patterns):
            return None  # Pravděpodobně ženské → zpracuj v infer_first_name_nominative

        # 4. Krátký kmen (≤4 znaky) + 'a' je pravděpodobně ženské
        if len(stem) <= 4:
            return None

    # PRIORITA 4: Dativ -u → remove (Petru → Petr) - PŘED -a!
    # Důležité: testovat PŘED -a, protože "Petra" může být "Petr" + -a
    if lo.endswith('u') and len(obs) > 1:
        cand = obs[:-1]
        if cand.lower() in CZECH_FIRST_NAMES:
            return cand.capitalize()

        # Zkus vložné 'e' (Hynku → Hynek, Radku → Radek)
        if len(cand) >= 2 and cand[-1] in 'klntr':
            cand_with_e = cand[:-1] + 'e' + cand[-1]
            if cand_with_e.lower() in CZECH_FIRST_NAMES:
                return cand_with_e.capitalize()
            # Přidej obě varianty jako kandidáty
            cands.append(cand_with_e)

        cands.append(cand)

    # PRIORITA 5: Genitiv/Akuzativ -a → remove (Petra → Petr, ale i Jana → Jan)
    if lo.endswith('a') and len(obs) > 1:
        cand = obs[:-1]
        cand_lo = cand.lower()
        if debug_this:
            print(f"      [_male_gen] PRIORITA 5: -a branch, cand='{cand}', in library: {cand_lo in CZECH_FIRST_NAMES}")
        if cand_lo in CZECH_FIRST_NAMES:
            if debug_this:
                print(f"      [_male_gen] PRIORITA 5 RETURN: '{cand.capitalize()}'")
            return cand.capitalize()

        # HEURISTIKA: I když není v knihovně, pokud vypadá jako typické mužské jméno
        # (končí na -el, -il, -im, -om, -eš, -oš, -ch, atd.), je to pravděpodobně genitiv
        male_name_patterns = ('el', 'il', 'im', 'om', 'eš', 'oš', 'an', 'en', 'on', 'ín', 'ír',
                             'it', 'át', 'út', 'ek', 'ík', 'ák', 'uk', 'av', 'ev', 'iv', 'oj', 'aj',
                             'ch', 'ich', 'ích')
        if any(cand_lo.endswith(pattern) for pattern in male_name_patterns):
            if debug_this:
                print(f"      [_male_gen] PRIORITA 5 HEURISTIC RETURN: '{cand.capitalize()}' (matches male pattern)")
            return cand.capitalize()

        cands.append(cand)

    # Vrať první kandidát (pokud existuje)
    result = cands[0].capitalize() if cands else None
    if debug_this:
        print(f"      [_male_gen] FINAL RETURN: {result}, cands={cands}")
    return result

def _get_gender_from_library(name_lower: str) -> str:
    """Vrací gender z knihovny jmen ('M', 'F', 'U') nebo '' pokud jméno není v knihovně."""
    return CZECH_FIRST_NAMES_GENDER.get(name_lower, '')

def get_first_name_gender(name: str) -> str:
    """Určí rod křestního jména. Vrací 'M' (mužský), 'F' (ženský), nebo 'U' (neznámý)."""
    lo = name.lower().strip()

    # PRIORITA 1: Kontrola v knihovně - použij SKUTEČNÝ gender z JSON
    # Knihovna má strukturu: {"firstnames": {"M": [...], "F": [...], "U": [...]}}
    gender_from_lib = _get_gender_from_library(lo)
    if gender_from_lib:
        return gender_from_lib

    # PRIORITA 2: Specifická mužská jména končící na -e (francouzská)
    male_e_names = {'rene', 'pierre', 'andre', 'antoine'}
    if lo in male_e_names:
        return 'M'

    # PRIORITA 3: Specifická ženská jména (včetně těch končících na -e)
    female_exceptions = {
        'ruth', 'esther', 'carmen', 'mercedes', 'dagmar', 'ingrid', 'margit',
        'alice', 'beatrice', 'rose', 'marie', 'sophie', 'chloe', 'irene',
        'elvira', 'elena', 'nadie', 'nadia'
    }
    if lo in female_exceptions:
        return 'F'

    # PRIORITA 4: Heuristika podle koncovky
    # Ženská jména typicky končí na -a, -e, -ie
    if lo.endswith('a') and lo not in {'joshua', 'luca', 'nicola', 'andrea'}:
        return 'F'
    if lo.endswith(('ie', 'y')) and len(lo) > 2:
        return 'F'

    # Default: pokud nekončí na -a, pravděpodobně mužské
    return 'M' if not lo.endswith('a') else 'F'

def is_valid_surname_variant(surname_obs: str, surname_nom: str, gender: str) -> bool:
    """
    Kontroluje, zda pozorovaný tvar příjmení odpovídá rodu osoby.

    Args:
        surname_obs: Pozorovaný tvar příjmení (např. "Vránou")
        surname_nom: Kanonický nominativ (např. "Vráný")
        gender: 'M' nebo 'F'

    Returns:
        True pokud je tvar validní pro daný rod, False jinak
    """
    obs_lo = surname_obs.lower()
    nom_lo = surname_nom.lower()

    # Pokud jsou stejné, vždy validní
    if obs_lo == nom_lo:
        return True

    # Pro přídavná jména na -ý/-á (Černý, Malý, Vráný...)
    if nom_lo.endswith('ý'):
        # Mužský rod - platné koncovky: -ý, -ého, -ému, -ým, -ém, -í
        if gender == 'M':
            male_endings = ('ý', 'ého', 'ému', 'ým', 'ém', 'í')
            base = nom_lo[:-1]  # "vrán" z "vráný"

            # Kontrola, že obs začíná správným základem
            if not obs_lo.startswith(base):
                return False

            # Kontrola koncovky
            for ending in male_endings:
                if obs_lo == base + ending:
                    return True
            return False

        # Ženský rod - platné koncovky: -á, -é, -ou
        elif gender == 'F':
            female_endings = ('á', 'é', 'ou')
            base = nom_lo[:-1]  # "vrán" z "vráný"

            if not obs_lo.startswith(base):
                return False

            for ending in female_endings:
                if obs_lo == base + ending:
                    return True
            return False

    # Pro přídavná jména na -ský/-cký
    if nom_lo.endswith(('ský', 'cký')):
        stem = nom_lo[:-2]  # "novot" z "novotský"

        if gender == 'M':
            male_endings = ('ský', 'ského', 'skému', 'ským', 'ském', 'cký', 'ckého', 'ckému', 'ckým', 'ckém')
            for ending in male_endings:
                if obs_lo == stem + ending:
                    return True
            return False
        elif gender == 'F':
            female_endings = ('ská', 'ské', 'skou', 'cká', 'cké', 'ckou')
            for ending in female_endings:
                if obs_lo == stem + ending:
                    return True
            return False

    # Pro ženská příjmení na -ová
    if nom_lo.endswith('ová'):
        # Tato příjmení jsou POUZE ženská
        if gender == 'F':
            base = nom_lo[:-1]  # "novákov" z "nováková"
            valid_endings = ('ová', 'ové', 'ou')
            for ending in valid_endings:
                if obs_lo == base + ending:
                    return True
            return False
        else:
            # Mužský rod by neměl mít -ová příjmení
            return False

    # Pro běžná příjmení (Novák, Dvořák, Klíma...)
    # Tato příjmení se obvykle skloňují stejně pro muže i ženy (kromě -ová formy)
    return True

def infer_first_name_nominative(obs: str) -> str:
    """Odhadne nominativ křestního jména z pozorovaného tvaru.

    Pokrývá všechny české pády + speciální vzory (ice→ika, ře→ra, apod.).
    """

    lo = obs.lower()

    # DEBUG: Trace execution for specific names
    debug_names = ['artur', 'viktor', 'albert', 'alberta']
    debug_this = any(name in lo for name in debug_names)
    if debug_this:
        print(f"    [infer_first] INPUT: obs='{obs}', lo='{lo}'")

    # SPECIÁLNÍ PŘÍPADY: Některá jména mohou být genitiv od jiného jména
    # Musí být PŘED kontrolou knihovny!

    # Roberta může být genitiv od Robert
    # (Roberta je v knihovně jako ženské jméno, ale častěji je to genitiv od Robert)
    if lo == 'roberta':
        return 'Robert'

    # Radka/Marka/Karla může být genitiv od Radek/Marek/Karel (není v knihovně jmen)
    # Přidány všechny pádové formy pro tyto časté případy
    if lo in ('radka', 'radku', 'radkem', 'radkovi', 'radko'):
        return 'Radek'
    if lo in ('marka', 'marku', 'markem', 'markovi'):
        return 'Marek'
    if lo in ('karla', 'karlu', 'karlem', 'karlovi', 'karlo'):
        return 'Karel'

    # Jména s vložným 'e/ě' a zdvojením souhlásky
    # Otto: nominativ Otto, genitiv Otta, dativ Ottovi
    if lo in ('otta', 'ottovi', 'ottem', 'otto'):
        return 'Otto'

    # Zdeněk: nominativ Zdeněk, genitiv Zdeňka (měkčení ě→ň), dativ Zdeňkovi
    if lo in ('zdeňka', 'zdeňku', 'zdeňkovi', 'zdeňkem', 'zdeněk'):
        return 'Zdeněk'

    # František: nominativ František, genitiv Františka, dativ Františkovi
    if lo in ('františka', 'františku', 'františkovi', 'františkem', 'františk'):
        return 'František'

    # Čeněk: nominativ Čeněk, genitiv Čeňka
    if lo in ('čeňka', 'čeňku', 'čeňkovi', 'čeňkem', 'čeněk'):
        return 'Čeněk'

    # Hany může být genitiv od Hana
    # (Hany může být v knihovně, ale standardní nominativ je Hana)
    if lo == 'hany':
        return 'Hana'

    # Alica je spelling varianta Alice (sjednoť je)
    if lo == 'alica':
        return 'Alice'

    # Rene je mužské francouzské jméno končící na -e (ne "Rena")
    # "Renem" (instrumentál) → "Rene", ne "Ren"
    if lo in ('rene', 'renem', 'renemu'):
        return 'Rene'

    # Dativ/Lokál -ě formy (Unicode normalization může způsobit problémy s endswith)
    # Používám přesný match místo endswith
    dative_e_forms = {
        'adéle': 'Adéla',
        'zuzaně': 'Zuzana',
        'barbaře': 'Barbara',
        'heleně': 'Helena',
        'simoně': 'Simona',
        'nikole': 'Nikola',
        'gabriele': 'Gabriela',
        'terezě': 'Tereza',
        'lence': 'Lenka',  # lokál -ce → -ka
        'evě': 'Eva',
        'anně': 'Anna',
        'janě': 'Jana',
        'petře': 'Petra',
        'kateřině': 'Kateřina',
        'radce': 'Radka',
        'elišce': 'Eliška',
        'šárce': 'Šárka',
        'blance': 'Blanka',  # dativ/lokál -ce → -ka
        'helze': 'Helga',  # dativ/lokál -ze → -ga
        'ele': 'Ela',  # dativ/lokál -e → -a
        'andreo': 'Andrea',  # dativ -eo pro -ea jména
        'andree': 'Andrea',  # lokál "Andree Říhové" → Andrea
        'alicí': 'Alice',  # instrumentál -í → -ie
        'alici': 'Alice',  # dativ/lokál -i → -ie
        'monice': 'Monika',
        'veronice': 'Veronika',
        'lucií': 'Lucie'  # instrumentál -ií → -ie
    }
    if lo in dative_e_forms:
        return dative_e_forms[lo]

    # PRIORITA: Jména končící na -ie (Julie, Valerie, Antonie, Lucie, Marie)
    # V ČESKÝCH dokumentech preferuj -ie (Julie) před -ia (Julia)
    # -ie je českýtvar, -ia je mezinárodní tvar
    if lo.endswith('ie') and len(obs) > 2:
        # Pokud -ie forma je v knihovně, je to pravděpodobně nominativ
        if lo in CZECH_FIRST_NAMES:
            # Lucie, Marie - to jsou nominativy, ne pády
            if debug_this:
                print(f"    [infer_first] -ie is nominativ RETURN: '{obs.capitalize()}'")
            return obs.capitalize()

        # KRITICKÁ ZMĚNA: Pokud -ie forma NENÍ v knihovně, ZACHOVEJ -ie jako správný český tvar
        # Julie, Antonie, Valerie, Nadie jsou správné české tvary (i když nejsou v knihovně)
        # NEKONVERTUJ na -ia (Julia, Antonia, Valeria), to jsou mezinárodní tvary
        if debug_this:
            print(f"    [infer_first] -ie not in lib, keeping Czech -ie form RETURN: '{obs.capitalize()}'")
        return obs.capitalize()

    # KRITICKY DŮLEŽITÉ: Nejdřív zkontroluj, zda už je v nominativu (v knihovně jmen)
    # MUSÍ být PRVNÍ, aby se předešlo nesprávnému zpracování jako "Eliška" → "Elišk"
    # PRIORITA: Jména končící na 'e' (Beatrice, Elvira, atd.) - zkontroluj PŘED zpracováním jako genitiv!
    if lo.endswith('e') and lo in CZECH_FIRST_NAMES:
        # Jméno končí na 'e' a JE v knihovně → je to nominativ, NE genitiv
        # Beatrice, Rose, Chloe, atd.
        if debug_this:
            print(f"    [infer_first] Name ending in 'e' found in library RETURN: '{obs.capitalize()}'")
        return obs.capitalize()

    if lo in CZECH_FIRST_NAMES:
        # VÝJIMKA 1: Některá jména v knihovně jsou ve skutečnosti pády od jiných jmen
        # "petru" (dativ od Petr), "davida" (ženské jméno ale genitiv od David), "kamila" (genitiv od Kamil)
        # Pro VŠECHNA jména končící na -a/-u zkontroluj, zda base forma je také v knihovně
        if lo.endswith(('a', 'u')) and len(obs) > 2:
            base = obs[:-1]
            base_lo = base.lower()

             # PRIORITA 1: Zkontroluj knihovnu nebo známá mužská jména NEJPRVE
            # Alberta → Albert (base v knihovně), ne Alberto
            # Bruna → Bruno (base NENÍ v knihovně, ale base+o ANO)
            common_male_names = {'petr', 'david', 'marek', 'pavel', 'tomáš', 'lukáš', 'jan', 'jiří', 'kamil',
                               'daniel', 'filip', 'aleš', 'stanislav', 'jaroslav', 'rostislav', 'ladislav'}
            if base_lo in CZECH_FIRST_NAMES or base_lo in common_male_names:
                if debug_this:
                    print(f"    [infer_first] Ambiguous form, base in lib, preferring base RETURN: '{base.capitalize()}'")
                return base.capitalize()

            # PRIORITA 2: Zkus base+o pro jména jako Bruna → Bruno
            # POUZE když base NENÍ v knihovně, ale base+o ANO
            # Pokud jak "bruna" (F), tak "bruno" (M) jsou v knihovně, preferuj "bruno"
            if lo.endswith('a'):
                base_o = base + 'o'
                if base_o.lower() in CZECH_FIRST_NAMES:
                    if debug_this:
                        print(f"    [infer_first] Ambiguous form (F in lib, base NOT), preferring base+o RETURN: '{base_o.capitalize()}'")
                    return base_o.capitalize()

        # VÝJIMKA 2: Preferuj české varianty před slovenskými
        # "alica" (SK) → "alice" (CZ), "lucia" (SK) → "lucie" (CZ)
        slovak_to_czech = {
            'alica': 'alice',
            'lucia': 'lucie'
        }
        if lo in slovak_to_czech:
            if debug_this:
                print(f"    [infer_first] Slovak variant, preferring Czech RETURN: '{slovak_to_czech[lo].capitalize()}'")
            return slovak_to_czech[lo].capitalize()

        if debug_this:
            print(f"    [infer_first] Already in library RETURN: '{obs.capitalize()}'")
        return obs.capitalize()

    # PRIORITA: Instrumentál -ou → -a (Renatou → Renata, Marcelou → Marcela)
    # MUSÍ být PŘED zpracováním samostatného -u, protože -ou také končí na -u!
    if lo.endswith('ou') and len(obs) > 2:
        stem = obs[:-2]
        stem_a = stem + 'a'
        stem_a_lo = stem_a.lower()

        # PRVNÍ zkontroluj knihovnu
        if stem_a_lo in CZECH_FIRST_NAMES:
            return stem_a.capitalize()

        # FALLBACK: OBECNÁ HEURISTIKA pro ženská jména mimo knihovnu
        # Pattern 1: končí na typické ženské vzory
        female_patterns = (
            'ina', 'ana', 'ela', 'ara', 'ona', 'ika', 'ála', 'éta',
            'ata', 'ita', 'ota', 'uta', 'ora', 'ura', 'yna', 'ína',
            'éna', 'ána', 'una', 'ia', 'ea'
        )
        if stem_a_lo.endswith(female_patterns):
            return stem_a.capitalize()

        # Pattern 2: krátký/středně dlouhý kmen (≤6 znaky) + 'a' je pravděpodobně ženské
        if len(stem) <= 6:
            return stem_a.capitalize()

    # PRIORITA: Pokud jméno končí na 'a'/'u' a base forma je v knihovně, preferuj base
    # Důvod: "petru" je v knihovně, ale "petr" také → preferuj "petr"
    # "davida" je v knihovně, "david" ne, ale "david" končí na souhlásku → preferuj "david"
    if lo.endswith(('a', 'u')) and len(obs) > 2:
        base = obs[:-1]
        base_lo = base.lower()

        if debug_this:
            print(f"    [infer_first] PRIORITA a/u: base='{base}', base_lo='{base_lo}'")
            print(f"    [infer_first] base_lo in library: {base_lo in CZECH_FIRST_NAMES}")

        # PRIORITA 1: Pro jména končící na 'a', zkus base+el NEJPRVE (Pavla → Pavel, ne Pavlo)
        # České varianty s -el mají přednost před zahraničními variantami s -o
        if lo.endswith('a'):
            base_el = base + 'el'
            if base_el.lower() in CZECH_FIRST_NAMES:
                if debug_this:
                    print(f"    [infer_first] PRIORITA a: base+el in library RETURN: '{base_el.capitalize()}'")
                return base_el.capitalize()

        # PRIORITA 2: Pokud base je v knihovně, preferuj ho (např. "Petru" → "Petr")
        if base_lo in CZECH_FIRST_NAMES:
            if debug_this:
                print(f"    [infer_first] PRIORITA a/u RETURN base: '{base.capitalize()}'")
            return base.capitalize()

        # PRIORITA 2.5: Male pattern heuristic PŘED base+o checkem
        # Pavla → Pavl končí na 'vl' (male pattern) → zkus base+el
        # To zabezpečí, že Pavla → Pavel, ne Pavlo
        if lo.endswith('a'):
            male_name_patterns_check = (
                'el', 'il', 'im', 'om', 'eš', 'oš', 'aš', 'iš', 'uš', 'yš',
                'an', 'en', 'on', 'ín', 'ír', 'it', 'át', 'út',
                'ek', 'ík', 'ák', 'uk', 'av', 'ev', 'iv', 'oj', 'aj', 'ej', 'ij',
                'áš', 'éš', 'íš', 'óš', 'úš',
                'š', 'ž', 'č', 'ř',
                'is', 'us', 'os', 'as',
                'ich', 'ích', 'ch',
                'vl', 'rl'
            )
            if any(base_lo.endswith(pattern) for pattern in male_name_patterns_check) and len(base) >= 3:
                # Base vypadá jako mužské jméno → zkus rekonstruovat
                # Pro "vl" nebo "rl" shluky: Pavl → Pav+el = Pavel
                # Pro ostatní: zkus base+el nebo použij known_truncations
                base_el = None

                # PRIORITA 1: Specifická known_truncations
                known_male_truncations = {
                    'pavl': 'Pavel', 'karl': 'Karel', 'petr': 'Petr'
                }
                if base_lo in known_male_truncations:
                    if debug_this:
                        print(f"    [infer_first] Male pattern known_truncation: '{known_male_truncations[base_lo]}'")
                    return known_male_truncations[base_lo]

                # PRIORITA 2: Pro souhlásková shluky (vl, rl): odstraň poslední 'l' a přidej 'el'
                # Pavl → Pav+el = Pavel
                if base_lo.endswith(('vl', 'rl')) and len(base) >= 4:
                    base_stem = base[:-1]  # Odstraň poslední 'l'
                    base_el = base_stem + 'el'
                    if debug_this:
                        print(f"    [infer_first] Male vl/rl pattern: '{base}' → '{base_stem}' + 'el' = '{base_el}'")

                # PRIORITA 3: Pro ostatní patterny: zkus base+el
                if base_el is None:
                    base_el = base + 'el'

                # Zkontroluj, jestli je base_el v knihovně
                if base_el.lower() in CZECH_FIRST_NAMES:
                    if debug_this:
                        print(f"    [infer_first] Male pattern, returning base_el: '{base_el.capitalize()}'")
                    return base_el.capitalize()

                # FALLBACK: Pokud base+el není v knihovně, vrať aspoň base
                if debug_this:
                    print(f"    [infer_first] Male pattern, base_el NOT in lib, returning base: '{base.capitalize()}'")
                return base.capitalize()

        # PRIORITA 3: Pro jména končící na 'a', zkus base+o (Huga → Hugo, Bruna → Bruno, Marca → Marco)
        # POUZE pro specifické kmeny nebo když base+o je v knihovně a base NENÍ
        if lo.endswith('a'):
            base_o = base + 'o'
            base_o_lo = base_o.lower()
            # Explicitní whitelist pro známé případy
            if base_lo in ('hug', 'brun', 'marc', 'dieg'):
                if base_o_lo in CZECH_FIRST_NAMES:
                    if debug_this:
                        print(f"    [infer_first] PRIORITA a: base+o (whitelisted) RETURN: '{base_o.capitalize()}'")
                    return base_o.capitalize()
            # Nebo pokud base+o je v knihovně a vypadá jako zahraniční jméno končící na -co/-go/-no
            elif base_o_lo in CZECH_FIRST_NAMES and base_o_lo.endswith(('co', 'go', 'no', 'io')):
                if debug_this:
                    print(f"    [infer_first] PRIORITA a: base+o foreign pattern RETURN: '{base_o.capitalize()}'")
                return base_o.capitalize()

        # HEURISTIKA: I když base NENÍ v knihovně, pokud vypadá jako typické mužské jméno
        # (končí na -el, -il, -im, -om, -eš, -š, -is, -ch atd.), je to pravděpodobně genitiv/dativ
        # Např. "Daniela" → "Daniel", "Borisa" → "Boris", "Bedřicha" → "Bedřich", "Pavla" → "Pavel"
        male_name_patterns = (
            'el', 'il', 'im', 'om', 'eš', 'oš', 'aš', 'iš', 'uš', 'yš',
            'an', 'en', 'on', 'ín', 'ír', 'it', 'át', 'út',
            'ek', 'ík', 'ák', 'uk', 'av', 'ev', 'iv', 'oj', 'aj', 'ej', 'ij',
            'áš', 'éš', 'íš', 'óš', 'úš',  # S diakritikou
            'š', 'ž', 'č', 'ř',  # Samotné měkké souhlásky
            'is', 'us', 'os', 'as',  # Latinská jména (Boris, Marcus)
            'ich', 'ích', 'ch',  # Jména jako Bedřich, Jindřich
            'vl', 'rl'  # Pavl (Pavel), Karl (Karel)
        )
        if any(base_lo.endswith(pattern) for pattern in male_name_patterns) and len(base) >= 3:
            if debug_this:
                print(f"    [infer_first] PRIORITA a/u HEURISTIC RETURN base: '{base.capitalize()}' (male pattern)")
            return base.capitalize()

    # PRIORITA: Jména končící na 'o' - zkontroluj PŘED truncation
    # Hugo, Diego, Marco, Bruno, atd. by neměly být převedeny na Huga, Diega, atd.
    if lo.endswith('o') and len(obs) >= 3:
        stem = obs[:-1]  # Odstraň 'o'
        stem_lo = stem.lower()

        # PRIORITA 1: Zkus stem+el (Pavlo → Pavel, Alberto → Albert)
        # České/evropské varianty mají přednost (Pavel před Pavlo, Albert před Alberto)
        stem_el = stem + 'el'
        if stem_el.lower() in CZECH_FIRST_NAMES:
            if debug_this:
                print(f"    [infer_first] Name ending in 'o', preferring stem+el RETURN: '{stem_el.capitalize()}'")
            return stem_el.capitalize()

        # PRIORITA 2: Zkus samotný stem (Olego → Oleg, Mihailo → Mihail)
        if stem_lo in CZECH_FIRST_NAMES:
            if debug_this:
                print(f"    [infer_first] Name ending in 'o', preferring stem RETURN: '{stem.capitalize()}'")
            return stem.capitalize()

        # PRIORITA 3: Zachovej 'o' formu, pokud je v knihovně (Hugo, Diego, Marco, Bruno)
        if lo in CZECH_FIRST_NAMES:
            if debug_this:
                print(f"    [infer_first] Name ending in 'o' found in library RETURN: '{obs.capitalize()}'")
            return obs.capitalize()

        # PRIORITA 4: Fallback pro zahraniční jména mimo knihovnu
        # POUZE pro specifické vzory (končí na -co/-go/-io)
        if lo.endswith(('co', 'go', 'io', 'eo')) and len(obs) >= 4 and len(obs) <= 8:
            if debug_this:
                print(f"    [infer_first] Name ending in 'o' (foreign pattern) RETURN: '{obs.capitalize()}'")
            return obs.capitalize()

    # Zkontroluj TRUNKACE - pokud jméno vypadá jako zkrácené (končí souhláskou)
    # a přidání 'a'/'el'/'ek' dá známé jméno, preferuj úplnou formu
    # ALE POUZE pokud jméno vypadá zkrácené (krátké nebo končí na typické zkratky)
    if len(obs) >= 3 and obs[-1] not in 'aeiouyáéíóúůýěiu':
        if debug_this:
            print(f"    [infer_first] Checking TRUNCATION branch")
        # Kontrola: jméno musí vypadat skutečně zkrácené
        # - Buď je krátké (< 5 písmen)
        # - Nebo končí na typické zkrácené tvary (n, l, k, r po souhlásce)
        looks_truncated = (len(obs) < 5 or
                          lo.endswith(('zn', 'vl', 'dn', 'rk', 'nk', 'hk', 'ol', 'il')))

        if debug_this:
            print(f"    [infer_first] looks_truncated: {looks_truncated}")

        if looks_truncated:
            # PRIORITA 1: 'el' (Pavl → Pavel, ne Pavlo)
            # České varianty mají přednost před zahraničními (Pavel před Pavlo, Albert před Alberto)
            if (lo + 'el') in CZECH_FIRST_NAMES:
                if debug_this:
                    print(f"    [infer_first] TRUNCATION +el RETURN: '{(obs + 'el').capitalize()}'")
                return (obs + 'el').capitalize()

            # PRIORITA 2: 'a' (Zuzan → Zuzana)
            if (lo + 'a') in CZECH_FIRST_NAMES:
                if debug_this:
                    print(f"    [infer_first] TRUNCATION +a RETURN: '{(obs + 'a').capitalize()}'")
                return (obs + 'a').capitalize()

            # PRIORITA 3: 'ek' (Radk → Radek, Hynk → Hynek)
            if (lo + 'ek') in CZECH_FIRST_NAMES:
                if debug_this:
                    print(f"    [infer_first] TRUNCATION +ek RETURN: '{(obs + 'ek').capitalize()}'")
                return (obs + 'ek').capitalize()

            # PRIORITA 4: 'o' (Hug → Hugo, Marc → Marco, Dieg → Diego)
            # POUZE pro specifické kmeny, které víme, že mají 'o' formu
            # Ne pro obecné jako "Pavl" (Pavel ne Pavlo), "Albert" (Albert ne Alberto)
            if lo in ('hug', 'marc', 'dieg'):  # Explicitní whitelist
                if (lo + 'o') in CZECH_FIRST_NAMES:
                    if debug_this:
                        print(f"    [infer_first] TRUNCATION +o (whitelisted) RETURN: '{(obs + 'o').capitalize()}'")
                    return (obs + 'o').capitalize()

        # FALLBACK: Běžná jména, která nejsou v knihovně
        known_truncations = {
            'zuzan': 'Zuzana', 'pavl': 'Pavel', 'radk': 'Radek', 'hynk': 'Hynek',
            'radec': 'Radka', 'elišec': 'Eliška', 'šárec': 'Šárka',
            'jiř': 'Jiří', 'petr': 'Petr', 'jan': 'Jan', 'tom': 'Tomáš',
            'nikol': 'Nikola', 'mark': 'Marek',
            'hug': 'Hugo', 'marc': 'Marco', 'dieg': 'Diego'
        }
        if lo in known_truncations:
            if debug_this:
                print(f"    [infer_first] known_truncations RETURN: '{known_truncations[lo]}'")
            return known_truncations[lo]

    # SPECIÁLNÍ VZORY - PRIORITA (před obecnými pravidly)

    # 1. ice → ika (Anice → Anika, Clarice → Clarika)
    if lo.endswith('ice') and len(obs) > 3:
        stem_ika = obs[:-3] + 'ika'
        if stem_ika.lower() in CZECH_FIRST_NAMES:
            return stem_ika.capitalize()

    # 2. ře → ra (Barbaře → Barbara, Saře → Sara)
    if lo.endswith('ře') and len(obs) > 2:
        stem_ra = obs[:-2] + 'ra'
        if stem_ra.lower() in CZECH_FIRST_NAMES:
            return stem_ra.capitalize()

    # 3. Zkrácená jména (Han → Hana, Mart → Marta, ale NE David → Davida)
    # POUZE pro krátká jména (max 4 znaky) aby se předešlo chybám jako David → Davida
    if len(obs) <= 4:
        # Priorita: nejdřív zkus +ina (pro Mart → Martina), pak +a
        if lo + 'ina' in CZECH_FIRST_NAMES:
            return (obs + 'ina').capitalize()
        if lo + 'a' in CZECH_FIRST_NAMES:
            return (obs + 'a').capitalize()

    # ŽENSKÁ JMÉNA - pádové varianty
    # Akuzativ/Lokál/Dativ: -í/-ií/-ii → -ia nebo -ie (Lívii → Lívia, Lucií → Lucie, Marii → Marie)
    if lo.endswith(('í', 'ií', 'ii')) and len(obs) > 2:
        if lo.endswith(('ií', 'ii')):
            stem = obs[:-2]
        else:
            stem = obs[:-1]

        stem_ia = stem + 'ia'
        stem_ie = stem + 'ie'
        stem_e = stem + 'e'
        stem_a = stem + 'a'

        # Check library presence
        stem_ia_in_lib = stem_ia.lower() in CZECH_FIRST_NAMES
        stem_ie_in_lib = stem_ie.lower() in CZECH_FIRST_NAMES
        stem_e_in_lib = stem_e.lower() in CZECH_FIRST_NAMES
        stem_a_in_lib = stem_a.lower() in CZECH_FIRST_NAMES

        # KRITICKÁ LOGIKA: Koncovky "ii" a "ií" jsou pády od "-ie" nebo "-ia" jmen
        # - "ii" je dativ: Julie→Julii (Czech -ie), Otilia→Otilii (international -ia)
        # - "ií" je instrumentál: Julie→Julií, Otilia→Otilií
        # POZOR: "Jule" a "Elvir" jsou v knihovně, ale "Julii/Elviri" jsou pády od "Julie/Elvira"!
        # Řešení: Preferuj stem+"ie" nebo stem+"ia" (co je v knihovně), NIKDY stem+"e"!
        if lo.endswith(('ii', 'ií')):
            # Dativ/Instrumentál ending → zkontroluj -ie a -ia (ne -e!)
            stem_lo = stem.lower()

            # HEURISTIKA: Pokud OBOJÍ (-ie i -ia) jsou v knihovně, rozhoduj podle kmene:
            # Stem končící na 'il' → preferuj -ia (Otilia, Natalia, Cecilia, Emilia)
            # Ostatní → preferuj -ie (Julie, Valerie, Antonie, Marie)
            # Pokud jen jedna forma nebo žádná: VŽDY preferuj -ie (českší vzor)!
            if stem_ie_in_lib and stem_ia_in_lib:
                # Obojí v knihovně → použij heuristiku
                if stem_lo.endswith('il'):
                    # Otil+ia = Otilia, Natal+ia = Natalia
                    if debug_this:
                        print(f"    [infer_first] -ii/-ií + both in lib, stem ends 'il' → stem+ia RETURN: '{stem_ia.capitalize()}'")
                    return stem_ia.capitalize()
                else:
                    # Jul+ie = Julie (i když není v knihovně, Otilie je)
                    if debug_this:
                        print(f"    [infer_first] -ii/-ií + both in lib, stem NOT 'il' → stem+ie RETURN: '{stem_ie.capitalize()}'")
                    return stem_ie.capitalize()
            else:
                # Buď jen jedna forma v knihovně, nebo žádná → VŽDY preferuj -ie
                # "Julií" → "Julie" (i když Julie není v knihovně, ale Julia je)
                # "Valerií" → "Valerie" (i když Valerie není v knihovně, ale Valeria je)
                # Důvod: -ie je českší vzor, v českých dokumentech je častější
                if debug_this:
                    if stem_ie_in_lib:
                        print(f"    [infer_first] -ii/-ií + only stem_ie in lib → stem+ie RETURN: '{stem_ie.capitalize()}'")
                    elif stem_ia_in_lib:
                        print(f"    [infer_first] -ii/-ií + only stem_ia in lib BUT forcing stem+ie RETURN: '{stem_ie.capitalize()}'")
                    else:
                        print(f"    [infer_first] -ii/-ií + neither in lib → stem+ie RETURN: '{stem_ie.capitalize()}'")
                return stem_ie.capitalize()

        # Pro ostatní případy (-í pouze): použij prioritu podle kmene
        # KRITICKÁ LOGIKA: Pro stem končící na "ic" (Beatric), preferuj -e (Beatrice) před -ie (Beatricie)
        stem_lo = stem.lower()

        if stem_lo.endswith(('ic', 'íc')):
            # Pro jména jako Beatrice: preferuj stem+e před stem+ie
            # Beatricí → Beatrice (ne Beatricie)
            if stem_e_in_lib:
                if debug_this:
                    print(f"    [infer_first] stem ends 'ic', preferring stem_e RETURN: '{stem_e.capitalize()}'")
                return stem_e.capitalize()
            elif stem_ie_in_lib:
                if debug_this:
                    print(f"    [infer_first] stem ends 'ic', stem_e not in lib, trying stem_ie RETURN: '{stem_ie.capitalize()}'")
                return stem_ie.capitalize()
        else:
            # Pro ostatní jména: preferuj -ie (češtější) před -e
            # PRIORITA: -ie > -e > -ia > -a
            if stem_ie_in_lib:
                # -ie forma existuje → preferuj ji (Lucie před Lucia)
                if debug_this:
                    print(f"    [infer_first] stem_ie in lib RETURN: '{stem_ie.capitalize()}'")
                return stem_ie.capitalize()
            elif stem_e_in_lib:
                # -e forma existuje → použij ji
                if debug_this:
                    print(f"    [infer_first] stem_e in lib RETURN: '{stem_e.capitalize()}'")
                return stem_e.capitalize()

        # Pokračování prioritizace pro "-í" endings
        # KRITICKÁ LOGIKA: Pro stem končící na "ir/ur/or" (Elvir), preferuj -a (Elvira) před -ia
        if stem_lo.endswith(('ir', 'ur', 'or')):
            # Pro jména jako Elvira: preferuj stem+a před stem+ia
            # Elviri → Elvira (ne Elviria)
            if stem_a_in_lib:
                if debug_this:
                    print(f"    [infer_first] stem ends 'ir/ur/or', preferring stem_a RETURN: '{stem_a.capitalize()}'")
                return stem_a.capitalize()
            elif stem_ia_in_lib:
                if debug_this:
                    print(f"    [infer_first] stem ends 'ir/ur/or', stem_a not in lib, trying stem_ia RETURN: '{stem_ia.capitalize()}'")
                return stem_ia.capitalize()
        elif stem_ia_in_lib:
            # -ia forma existuje → použij ji (Lívia, Otilia)
            if debug_this:
                print(f"    [infer_first] stem_ia in lib RETURN: '{stem_ia.capitalize()}'")
            return stem_ia.capitalize()
        elif stem_a_in_lib:
            # -a forma existuje → použij ji (Elvira)
            if debug_this:
                print(f"    [infer_first] stem_a in lib RETURN: '{stem_a.capitalize()}'")
            return stem_a.capitalize()
        else:
            # FALLBACK: Žádná forma v knihovně → použij heuristiku
            # Preferuj české vzory: -ie > -e > -ia > -a
            stem_lo = stem.lower()

            # Preferuj -e pokud stem končí na 'ic' (Beatric+e = Beatrice)
            if stem_lo.endswith(('ic', 'íc')):
                if debug_this:
                    print(f"    [infer_first] heuristic -ic → stem_e RETURN: '{stem_e.capitalize()}'")
                return stem_e.capitalize()

            # Preferuj -a pokud stem končí na 'ir', 'ur', 'or' (Elvir+a = Elvira)
            if stem_lo.endswith(('ir', 'ur', 'or')):
                if debug_this:
                    print(f"    [infer_first] heuristic -ir/-ur/-or → stem_a RETURN: '{stem_a.capitalize()}'")
                return stem_a.capitalize()

            # Preferuj -ia pokud stem končí na 'il', 'ol' (Otil+ia = Otilia)
            if stem_lo.endswith(('il', 'yl', 'ol')):
                if debug_this:
                    print(f"    [infer_first] heuristic -il/-ol → stem_ia RETURN: '{stem_ia.capitalize()}'")
                return stem_ia.capitalize()

            # Default: preferuj -ie (nejčastější v češtině)
            if debug_this:
                print(f"    [infer_first] default → stem_ie RETURN: '{stem_ie.capitalize()}'")
            return stem_ie.capitalize()

    # Genitiv/Dativ/Lokál: -y/-ě/-e → -a
    if lo.endswith(('y', 'ě', 'e')):
        stem = obs[:-1]
        stem_a = stem + 'a'
        stem_a_lo = stem_a.lower()
        stem_lo = stem.lower()

        # SPECIÁLNÍ: Dativ s vložným 'e' (Mirce → Mirka, Stánce → Stánka)
        # Pokud stem končí na -rc, -nc, -lc → odstraň 'c' a přidej 'ka'
        if lo.endswith('ce') and len(stem) >= 3:
            prev_chars = stem[-2:].lower()
            if prev_chars in ('rc', 'nc', 'lc'):
                # Mirce: stem="Mirc" → odstraň 'c' → "Mir" + "ka" = "Mirka"
                stem_without_c = obs[:-2]  # Odstraň 'ce'
                stem_ka = stem_without_c + 'ka'
                if stem_ka.lower() in CZECH_FIRST_NAMES:
                    if debug_this:
                        print(f"    [infer_first] DATIV -ce → -ka RETURN: '{stem_ka.capitalize()}'")
                    return stem_ka.capitalize()

        if debug_this:
            print(f"    [infer_first] FEMALE -y/-ě/-e: stem='{stem}', stem_a='{stem_a}'")
            print(f"    [infer_first] stem_lo in library: {stem_lo in CZECH_FIRST_NAMES}")
            print(f"    [infer_first] stem_a_lo in library: {stem_a_lo in CZECH_FIRST_NAMES}")

        # PRIORITA: Rozhodování mezi stem a stem_a
        # Když OBOJÍ je v knihovně → preferuj stem_a (ženská forma: Milada před Milad)
        # Když POUZE stem je v knihovně → kontroluj, zda je to mužské nebo ženské jméno

        stem_a_in_lib = stem_a_lo in CZECH_FIRST_NAMES
        stem_in_lib = stem_lo in CZECH_FIRST_NAMES

        if stem_in_lib and stem_a_in_lib:
            # OBOJÍ v knihovně → preferuj stem_a (ženská forma)
            # VÝJIMKA: Pokud stem končí na mužskou koncovku (x, s, š, l, n, r), preferuj stem
            # Felix/Felixa → preferuj Felix, Boris/Borisa → preferuj Boris
            male_endings_both = ('x', 's', 'š', 'l', 'n', 'r', 'ch')
            if any(stem_lo.endswith(ending) for ending in male_endings_both) and len(stem) >= 4:
                if debug_this:
                    print(f"    [infer_first] Both in library, but stem looks male, preferring stem: '{stem.capitalize()}'")
                return stem.capitalize()
            # Default: preferuj stem_a
            if debug_this:
                print(f"    [infer_first] Both in library, preferring stem_a: '{stem_a.capitalize()}'")
            return stem_a.capitalize()
        elif stem_in_lib:
            # POUZE stem v knihovně
            # Kontrola: Je to mužské jméno v genitivu (Boris, Tomáš, Aleš)?
            # Nebo ženský genitiv (Milad od Milada)?

            # Heuristika: Mužská jména v genitivu typicky končí na souhlásky, zejména:
            # -s (Boris, Tomáš), -š (Aleš, Miloš), -ch (Bedřich), -k, -l, -n, -r, -x (Max, Felix, Alex)
            male_nom_endings = ('s', 'š', 'č', 'ř', 'ž', 'ch', 'k', 'l', 'n', 'r', 'm', 'd', 't', 'p', 'b', 'v', 'j', 'x')
            if any(stem_lo.endswith(ending) for ending in male_nom_endings) and len(stem) >= 4:
                # Vypadá jako mužské jméno v nominativu → vrať stem
                if debug_this:
                    print(f"    [infer_first] Stem looks like male nom, RETURN stem: '{stem.capitalize()}'")
                return stem.capitalize()

            # Pro krátká jména (≤4 znaky) nebo jména končící na neobvyklé koncovky → zkus stem_a
            # Kriste → Krista, Petře → Petra (vokativ)
            if len(stem) <= 4 or not stem_lo[-1].isalpha():
                if debug_this:
                    print(f"    [infer_first] Short stem or unusual ending, FALLBACK stem_a: '{stem_a.capitalize()}'")
                return stem_a.capitalize()

            # Default: vrať stem
            if debug_this:
                print(f"    [infer_first] RETURN stem (in library): '{stem.capitalize()}'")
            return stem.capitalize()
        elif stem_a_in_lib:
            # POUZE stem_a v knihovně → vrať stem_a
            if debug_this:
                print(f"    [infer_first] Only stem_a in library, RETURN: '{stem_a.capitalize()}'")
            return stem_a.capitalize()

        # PŘED FALLBACKEM: Check pro mužská jména mimo knihovnu
        # Maxe → Max (max končí na 'x', vypadá jako mužské)
        # Alexe → Alex (alex končí na 'x', vypadá jako mužské)
        male_stem_endings = ('x', 's', 'š', 'k', 'l', 'n', 'r', 'ch')
        if any(stem_lo.endswith(ending) for ending in male_stem_endings) and len(stem) >= 3:
            if debug_this:
                print(f"    [infer_first] Stem looks like male (ends with {stem_lo[-1]}), RETURN stem: '{stem.capitalize()}'")
            return stem.capitalize()

        # FALLBACK: OBECNÁ HEURISTIKA pro ženská jména mimo knihovnu
        # Pattern 1: končí na typické ženské vzory
        # DŮLEŽITÉ: Nejdřív kontroluj invalid endings (např. "Líviia", "Elisca")
        invalid_endings = ('sc', 'ii', 'ií', 'íi', 'iě', 'ýč', 'šc', 'žc')
        if not stem_a_lo.endswith(('sca', 'iia', 'íia', 'ií', 'ii')) and not stem.lower().endswith(invalid_endings):
            female_patterns = (
                'ina', 'ana', 'ela', 'ara', 'ona', 'ika', 'ála', 'éta',
                'ata', 'ita', 'ota', 'uta', 'ora', 'ura', 'yna', 'ína',
                'éna', 'ána', 'una', 'ia', 'ea'
            )
            if stem_a_lo.endswith(female_patterns):
                if debug_this:
                    print(f"    [infer_first] FEMALE -y RETURN (pattern): '{stem_a.capitalize()}'")
                return stem_a.capitalize()

        # Pattern 2: krátký/středně dlouhý kmen (≤6 znaky) + 'a' je pravděpodobně ženské
        # Zvýšeno z 4 na 6 pro zachycení jmen jako Vlasta (Vlast=5 znaků), Krista (Krist=5)
        # DŮLEŽITÉ: Kontroluj, že stem nevypadá jako divný (např. "Elisc", "Lívii")
        # ALE: nekontroluj, pokud stem vypadá jako mužské (např. Max, Alex)
        if len(stem) <= 6:
            # Nesmí končit na divné kombinace: sc, ii, ií, ... nebo mužské koncovky
            invalid_endings = ('sc', 'ii', 'ií', 'íi', 'iě', 'ýč', 'šc', 'žc')
            # NOVÝ CHECK: Pokud stem končí na mužskou koncovku, neskáč do fallbacku
            if any(stem_lo.endswith(ending) for ending in male_stem_endings):
                if debug_this:
                    print(f"    [infer_first] Stem ends with male pattern, skipping female fallback")
                # Pokračuj dál, nevrátíme stem_a
            elif not stem_a_lo.endswith(invalid_endings) and not stem.lower().endswith(invalid_endings):
                if debug_this:
                    print(f"    [infer_first] FEMALE -y RETURN (short stem): '{stem_a.capitalize()}'")
                return stem_a.capitalize()

    # Vokativ: -o → -a (Renato → Renata, Marcelo → Marcela, Petro → Petra)
    # Ženská jména v 5. pádě (oslovení) mají koncovku -o místo -a
    if lo.endswith('o') and len(obs) > 2:
        stem = obs[:-1]
        stem_a = stem + 'a'
        stem_a_lo = stem_a.lower()

        # PRVNÍ zkontroluj knihovnu
        if stem_a_lo in CZECH_FIRST_NAMES:
            return stem_a.capitalize()

        # FALLBACK: OBECNÁ HEURISTIKA pro ženská jména mimo knihovnu
        # Pattern 1: končí na typické ženské vzory
        female_patterns = (
            'ina', 'ana', 'ela', 'ara', 'ona', 'ika', 'ála', 'éta',
            'ata', 'ita', 'ota', 'uta', 'ora', 'ura', 'yna', 'ína',
            'éna', 'ána', 'una', 'ia', 'ea'
        )
        if stem_a_lo.endswith(female_patterns):
            return stem_a.capitalize()

        # Pattern 2: krátký/středně dlouhý kmen (≤6 znaky) + 'a' je pravděpodobně ženské
        if len(stem) <= 6:
            return stem_a.capitalize()

        # Pattern 3: Check for specific problematic patterns like "Radko" → "Radka"
        # (Radko is vocative, Radka is nominative)
        # For names ending in consonant + 'ko', try removing 'o'
        if len(stem) >= 3 and stem[-1] == 'k':
            # Radko → stem=Radk, stem_a=Radka
            # This should match the short stem rule above, but adding explicit check
            return stem_a.capitalize()

    # Dativ/Akuzativ: -u → -a (Hanu → Hana, Martinu → Martina)
    if lo.endswith('u') and len(obs) > 1:
        stem = obs[:-1]
        # PRVNÍ zkontroluj knihovnu
        if (stem + 'a').lower() in CZECH_FIRST_NAMES:
            return (stem + 'a').capitalize()
        # FALLBACK pro běžná ženská jména -ina/-ýna (Martinu→Martina, Pavlinu→Pavlina)
        if stem.lower().endswith(('tin', 'lin', 'rin', 'din', 'nin', 'stýn')):
            return (stem + 'a').capitalize()
        # REKURZIVNÍ: pokud stem stále vypadá declined (končí -em, -ovi), zpracuj znovu
        # Renemu → Renem (po strip -u) → Ren (po strip -em)
        if stem.lower().endswith(('em', 'ovi', 'ím')):
            return infer_first_name_nominative(stem)

    # Lokál: -i → -a nebo -e pro ženská jména (Milici → Milica, Alici → Alice, Kristi → Krista)
    # MUSÍ být PŘED zpracováním mužských jmen s -i (Tomáši → Tomáš)
    # A PO zpracování -í/-ií/-ii
    if lo.endswith('i') and not lo.endswith(('ovi', 'í', 'ií', 'ii')) and len(obs) > 2:
        stem = obs[:-1]
        stem_a = stem + 'a'
        stem_e = stem + 'e'
        stem_a_lo = stem_a.lower()
        stem_e_lo = stem_e.lower()

        # PRIORITA 1a: České varianty končící na -e (i když nejsou v knihovně)
        # Preferujeme Alice před Alica, Beatrice před Beatrica
        czech_e_names = {'alice', 'beatrice', 'clarice', 'berenice'}
        if stem_e_lo in czech_e_names:
            if debug_this:
                print(f"    [infer_first] LOKÁL -i → -e (česká varianta) RETURN: '{stem_e.capitalize()}'")
            return stem_e.capitalize()

        # PRIORITA 1b: Zkontroluj stem+e v knihovně
        if stem_e_lo in CZECH_FIRST_NAMES:
            if debug_this:
                print(f"    [infer_first] LOKÁL -i → -e RETURN: '{stem_e.capitalize()}'")
            return stem_e.capitalize()

        # PRIORITA 2: Zkontroluj stem+a (Milica, Krista)
        # ALE: Pokud stem (bez 'a') je také v knihovně nebo je mužské jméno, preferuj stem
        # Např. "Aleši" → stem="Aleš" (mužské), stem_a="Aleša" (ženské) → preferuj "Aleš"
        # VÝJIMKA: Pro stem končící na "ir/ur/or" (Elvir → Elvira), preferuj stem+a
        if stem_a_lo in CZECH_FIRST_NAMES:
            # Kontrola: Je stem mužské jméno?
            stem_lo = stem.lower()

            # KRITICKÁ VÝJIMKA: Pro stem končící na "ir/ur/or", VŽDY preferuj stem+a
            # Elviri → Elvira (ne Elvir)
            if stem_lo.endswith(('ir', 'ur', 'or')):
                if debug_this:
                    print(f"    [infer_first] LOKÁL -i: stem ends 'ir/ur/or', preferring stem_a RETURN: '{stem_a.capitalize()}'")
                return stem_a.capitalize()

            if stem_lo in CZECH_FIRST_NAMES:
                # Obojí je v knihovně → preferuj stem (mužské jméno v dativu)
                if debug_this:
                    print(f"    [infer_first] LOKÁL -i: both in library, preferring stem RETURN: '{stem.capitalize()}'")
                return stem.capitalize()
            # Pokud stem končí na měkkou souhlásku (š, ž, č, ř), je to pravděpodobně mužské jméno v dativu
            if stem_lo.endswith(('š', 'ž', 'č', 'ř', 'ň', 'ť', 'ď', 'j')) and len(stem) >= 3:
                if debug_this:
                    print(f"    [infer_first] LOKÁL -i: stem ends with soft consonant, preferring stem RETURN: '{stem.capitalize()}'")
                return stem.capitalize()
            # Jinak vrať stem+a (ženské jméno)
            if debug_this:
                print(f"    [infer_first] LOKÁL -i → -a RETURN: '{stem_a.capitalize()}'")
            return stem_a.capitalize()

        # FALLBACK: Pokud stem+a končí na typické ženské vzory
        female_patterns = ('ica', 'ina', 'ana', 'ela', 'ara', 'ona', 'ika', 'ista', 'eta', 'ata', 'ira', 'ura', 'ora')
        if stem_a_lo.endswith(female_patterns):
            if debug_this:
                print(f"    [infer_first] LOKÁL -i RETURN (pattern): '{stem_a.capitalize()}'")
            return stem_a.capitalize()

    # MUŽSKÁ JMÉNA - genitiv/dativ/instrumentál
    # DŮLEŽITÉ: Přeskoč male branch pro invalid tvary (např. "Elisce" s kmene "Elisc")
    invalid_stems_for_male = ('sc', 'ii', 'ií')
    stem_for_check = obs[:-1] if len(obs) > 1 else obs
    if not stem_for_check.lower().endswith(invalid_stems_for_male):
        if debug_this:
            print(f"    [infer_first] Calling _male_genitive_to_nominative('{obs}')")
        male_nom = _male_genitive_to_nominative(obs)
        if debug_this:
            print(f"    [infer_first] _male_genitive_to_nominative returned: {male_nom}")
        if male_nom:
            if debug_this:
                print(f"    [infer_first] RETURN from male branch: '{male_nom}'")
            return male_nom
    elif debug_this:
        print(f"    [infer_first] SKIP male branch - invalid stem: '{stem_for_check}'")

    # POSSESSIVE FORMS - Petřin → Petra, Janin → Jana
    if lo.endswith('in') and len(obs) > 2:
        stem = obs[:-2]
        # Zkus ženskou variantu (Petřin → Petra)
        if (stem + 'a').lower() in CZECH_FIRST_NAMES:
            return (stem + 'a').capitalize()

    # Pokud nic nepomohlo, vrať původní tvar s velkým písmenem
    result = obs.capitalize()
    if debug_this:
        print(f"    [infer_first] FALLBACK RETURN: '{result}'")

    return result

def infer_surname_nominative(obs: str) -> str:
    """Odhadne nominativ příjmení z pozorovaného tvaru.

    Pokrývá:
    - Ženská příjmení (-ová, -á)
    - Přídavná jména (-ský, -cký, -ý)
    - Vložné 'e' (Havl → Havel, Petr → Petra)
    - Zvířecí příjmení (Liška, Vrba)
    - Všechny pády
    """
    lo = obs.lower()

    # DEBUG
    debug_surname = (lo in {'horňákové', 'horňák', 'hladká', 'hladký', 'hladeková'})
    if debug_surname:
        print(f"    [infer_surname] INPUT: obs='{obs}', lo='{lo}'")

    # ========== ŽENSKÁ PŘÍJMENÍ ==========

    # -é → -á (genitiv/dativ/lokál žen: Pokorné → Pokorná, Houfové → Houfová)
    if lo.endswith('é') and len(obs) > 3:
        # Kontrola, že není -ské/-cké (přídavné jméno)
        if not lo.endswith(('ské', 'cké')):
            result = obs[:-1] + 'á'
            if debug_surname:
                print(f"    [infer_surname] -é → -á RETURN: '{result}'")
            return result

    # -ou → může být -a (mužské příjmení Vrána → Vránou) nebo -á (ženské příjmení)
    # ALE TAKÉ může být -ek (Pavelek → Pavelkou s vložným e)
    if lo.endswith('ou') and len(obs) > 3:
        # Kontrola, že není -skou/-ckou (přídavné jméno)
        if not lo.endswith(('skou', 'ckou')):
            base = obs[:-2]
            base_lo = base.lower()

            # PRIORITA 1: Zkontroluj jestli base končí na 'k' a může být vložné e (Pavelkou → Pavelek)
            # ALE POUZE pokud stem není příliš krátký (< 6 znaků) - to by bylo spíše -á
            # Pavelkou: base="Pavelk" (6 znaků) → může být Pavelek s vložným e
            # Hladkou: base="Hladk" (5 znaků) → pravděpodobně Hladká (ne Hladek) ✓
            if base_lo.endswith('k') and len(base) >= 6:
                # OBECNÉ PRAVIDLO: Příjmení končící na -ek mají v instrumentálu vložné 'e' vypuštěné
                # Pavelkou (base="Pavelk") → Pavelek (přidat 'e')
                # Krupičkou (base="Krupičk") → Krupičěk (přidat 'ě' po měkké souhlásce)

                # Zkontroluj jestli předposlednísouhláska je měkká
                if len(base) >= 2:
                    prev_char = base[-2].lower()
                    # Měkké souhlásky: č, š, ž, ř, ď, ť, ň, c, j
                    soft_consonants = 'čšžřďťňcj'

                    # Pokud je předchozí znak měkká souhláska, přidej 'ě'
                    if prev_char in soft_consonants:
                        return base[:-1] + 'ěk'
                    # Pokud je předchozí znak souhláska, přidej 'e'
                    elif prev_char in 'bcdfghjklmnpqrstvwxzž':
                        return base[:-1] + 'ek'

            # PRIORITA 2: Mužská příjmení končící na -a v nominativu (normalizovaná bez diakritiky)
            norm = unicodedata.normalize('NFD', base_lo)
            base_norm = ''.join(c for c in norm if unicodedata.category(c) != 'Mn')

            # Pokud je to známé mužské příjmení (porovnej base+a proti GLOBÁLNÍMU seznamu)
            # base_norm="vran" → base_norm+"a"="vrana"
            # base_norm="sember" → base_norm+"a"="sembera" (bez diakritiky)
            if base_norm + 'a' in MALE_SURNAMES_WITH_A:
                return base + 'a'
            # Jinak (pravděpodobně ženské) → vrať dlouhé -á
            else:
                return base + 'á'

    # ========== PŘÍDAVNÁ JMÉNA (-ský, -cký, -ý) ==========

    if lo.endswith(('ého', 'ému', 'ým', 'ém')):
        # Všechny tyto koncovky → -ý
        if lo.endswith('ého'):
            return obs[:-3] + 'ý'
        elif lo.endswith('ému'):
            return obs[:-3] + 'ý'
        elif lo.endswith('ým'):
            return obs[:-2] + 'ý'
        elif lo.endswith('ém'):
            return obs[:-2] + 'ý'

    # Neohebná příjmení na -í: instrumentál -ím → -í
    # Krejčím → Krejčí, Dlouhím → Dlouhí
    if lo.endswith('ím') and len(obs) > 3:
        # Kontrola že to není -ským/-ckým (to jsou skutečné přídavné tvary)
        if not lo.endswith(('ským', 'ckým')):
            return obs[:-2] + 'í'  # Odstranit "ím", přidat "í"

    # -skou/-ckou → -ská/-cká (ženská přídavná)
    if lo.endswith(('skou', 'ckou')):
        return obs[:-2] + 'á'  # Hrabovskou → Hrabovská (ne Hrabovsá!)

    # -ské/-cké → -ská/-cká (genitiv/dativ/lokál ženská přídavná)
    if lo.endswith(('ské', 'cké')):
        return obs[:-1] + 'á'  # Hrabovské → Hrabovská

    # ========== VLOŽNÉ 'E' - Havl/Havla → Havel, Petr/Petra → Petra ==========

    # Seznam kmenů vyžadujících vložné e
    vlozne_e_stems = {
        'havl', 'sed', 'pes', 'koz', 'voj', 'pav', 'petr', 'jos',
        'alex', 'filip', 'luk', 'mar', 'dan', 'tom', 'jar', 'stef'
    }

    # Vložné 'e' pro genitiv -a: Havla → Havel, Pavla → Pavel
    if lo.endswith('a') and len(obs) > 3:
        stem = obs[:-1]  # např. "Havl" z "Havla"
        stem_lo = stem.lower()

        # Kontrola známých kmenů vyžadujících vložné e
        if stem_lo in vlozne_e_stems:
            # Vlož 'e' mezi poslední dvě souhlásky: "Havl" → "Havel"
            return stem[:-1] + 'e' + stem[-1]

        # Obecný případ: pokud stem končí na dvě souhlásky
        consonants = 'bcčdďfghjklmnňpqrřsštťvwxzž'
        if len(stem) >= 2 and stem_lo[-2] in consonants and stem_lo[-1] in consonants:
            # Zkontroluj, jestli výsledek dává smysl
            if stem_lo + 'e' + 'l' in ['havel', 'pavel'] or stem_lo in vlozne_e_stems:
                return stem[:-1] + 'e' + stem[-1]

    # ========== ZVÍŘECÍ PŘÍJMENÍ ==========
    # Liška, Vrba, Ryba, Kočka, Panda, atd. - končí na -a v nominativu!
    # NEODSTRAŇUJ -a, pokud je to zvířecí nebo rostlinné příjmení

    animal_plant_surnames = {
        'liška', 'vrba', 'ryba', 'kočka', 'panda', 'veverka',
        'sova', 'holub', 'vraná', 'zajíc', 'koza', 'ovečka',
        'bříza', 'dub', 'jeřábek', 'jílková', 'kaštanka'
    }

    if lo in animal_plant_surnames:
        return obs  # Zachovej nominativ

    # ========== SPECIÁLNÍ PŘÍPADY: -ka, -la, -ce → -ek, -el, -ec ==========

    # Ale POUZE pokud to NENÍ běžné příjmení končící na -a v nominativu
    # Používáme GLOBÁLNÍ seznam MALE_SURNAMES_WITH_A

    # Genitiv -ka/-la/-ce pouze pokud jde o známé kmeny s vložným e
    vlozne_e_surname_patterns = {
        'hav', 'pav', 'sed', 'koz', 'peš', 'pes', 'vojt', 'maš'
    }

    if lo.endswith('ka') and len(obs) > 3 and lo not in MALE_SURNAMES_WITH_A:
        stem = obs[:-2]  # Straka → Stra

        # KONTROLA: Pokud příjmení vypadá jako typické české příjmení s -ka
        # Příklady: Straka (Str+a+ka), Koudelka (Koudel+ka)
        if len(stem) >= 2:
            last_char = stem[-1].lower()
            consonants = 'bcčdďfghjklmnňpqrřsštťvwxzž'
            vowels = 'aeiouyáéíóúůýě'

            # Pokud stem končí souhláskou (Koudel → 'l'), pravděpodobně je to příjmení s -ka
            if last_char in consonants and len(stem) >= 4:
                return obs

            # Pokud stem končí samohláskou (Stra → 'a'), kontroluj znak PŘED ní
            # Straka: stem="Stra", stem[-2]='r' → souhláska + samohláska + ka
            if last_char in vowels and len(stem) >= 2:
                char_before_vowel = stem[-2].lower()
                if char_before_vowel in consonants:
                    # Vypadá jako Str+a+ka → zachovej
                    return obs

        stem = stem.lower()
        # Pouze pokud kmen vyžaduje vložné e: Hájka → Hájek, Pavelka → Pavelek
        # NEBO pokud je kmen krátký (≤4 znaky) → pravděpodobně vyžaduje vložné e
        short_stem = len(stem) <= 4
        if any(stem.startswith(p) or stem.endswith(p) or stem == p for p in vlozne_e_surname_patterns) or short_stem:
            return obs[:-2] + 'ek'

    if lo.endswith('la') and len(obs) > 3 and lo not in MALE_SURNAMES_WITH_A:
        stem_without_a = obs[:-1].lower()  # odstranit jen -a
        # Pokud kmen (bez -a) vyžaduje vložné e: Havla → Havel, Pavla → Pavel
        if any(stem_without_a[:-1].endswith(p) or stem_without_a[:-1] == p for p in vlozne_e_surname_patterns):
            # Vlož 'e' před poslední 'l': "havl" → "havel"
            return obs[:-2] + 'el'
        # Jinak jen odstranění -a: Dohnala → Dohnal
        elif stem_without_a.endswith('l'):
            return obs[:-1]  # odstranit jen -a

    if lo.endswith('ce') and len(obs) > 3:
        # Genitiv -ce může být od -ec (Němec) nebo -c (Švec)
        # Pokud stem je krátký (≤4 znaky), pravděpodobně je to prostě -c
        stem = obs[:-2]  # Šve z Švece, Něm z Němce
        if len(stem) <= 3:
            # Krátký kmen: Švece → Šve + c = Švec (bez vložného e)
            return obs[:-1]  # odstranit jen -e
        else:
            # Delší kmen: Němce → Něm + ec = Němec (s vložným e)
            return stem + 'ec'

    # ========== DATIV: -ovi → REMOVE ==========

    if lo.endswith('ovi') and len(obs) > 5:
        # Novákovi → Novák, ale Vaňkovi → Vaněk (vložné e)
        stem = obs[:-3]  # odstranit -ovi
        stem_lo = stem.lower()

        # Kontrola pro vložné 'e': příjmení končící na -ňk, -šk, -řk, -žk, -čk
        # NEBO krátké kmeny (≤4 znaky) končící na -k
        # "Vaňk" → "Vaněk", "Kotk" → "Kotek"
        short_k_stem = len(stem) <= 4 and stem_lo.endswith('k')

        if stem_lo.endswith(('ňk', 'šk', 'řk', 'žk', 'čk', 'ďk', 'ťk')):
            # Převeď měkkou souhlásku zpět na tvrdou před vložným 'ě'
            if stem_lo[-2] in 'ňďť':
                hardening = {'ň': 'n', 'ď': 'd', 'ť': 't'}
                stem = stem[:-2] + hardening[stem[-2]] + stem[-1]
            return stem[:-1] + 'ěk'  # Vaňk → Vaněk
        elif short_k_stem:
            # Kotk → Kotek, Hájk → Hájek
            return stem[:-1] + 'ek'

        # NOVÁ HEURISTIKA: Pokud stem+'a' dá typické české příjmení, přidej 'a'
        # Koudelkovi → stem="Koudelk" → candidate_a="Koudelka" (končí -ka) → vrať "Koudelka"
        candidate_a = stem + 'a'
        candidate_a_lo = candidate_a.lower()
        typical_surname_endings = ('ka', 'la', 'na', 'ra', 'ta', 'da', 'ma', 'ba', 'va', 'ha', 'ča', 'ša', 'ga', 'pa')
        if any(candidate_a_lo.endswith(ending) for ending in typical_surname_endings):
            # Dodatečná kontrola: stem musí končit souhláskou (ne samohláskou)
            consonants = 'bcčdďfghjklmnňpqrřsštťvwxzž'
            if stem_lo[-1] in consonants:
                return candidate_a

        # Default: jen odstranit -ovi
        return stem

    # ========== INSTRUMENTÁL: -em → REMOVE ==========

    # Ale POUZE pokud to není součást příjmení (Šembera, Chlumec, atd.)
    if lo.endswith('em') and len(obs) > 4:
        # Speciální případ: -alem, -elem, -olem, -ilem → pravděpodobně instrumentál od -al, -el, -ol, -il
        if lo.endswith(('alem', 'elem', 'olem', 'ilem', 'ílem', 'élem', 'ýlem', 'úlem')):
            # Doležalem → Doležal, Havlem → Havel, Kratochvílem → Kratochvíl
            if lo.endswith(('alem', 'álem')):
                return obs[:-2]  # Doležalem → Doležal
            elif lo.endswith(('elem', 'élem')):
                return obs[:-2]  # ?elem → ?el
            elif lo.endswith(('olem', 'ólem')):
                return obs[:-2]  # ?olem → ?ol
            elif lo.endswith(('ilem', 'ílem', 'ýlem')):
                return obs[:-2]  # Kratochvílem → Kratochvíl, ?ylem → ?yl
            elif lo.endswith('úlem'):
                return obs[:-2]  # ?úlem → ?úl

        # Speciální případ: -kem může být buď -ek+em nebo prostě -k+em
        elif lo.endswith('kem') and len(obs) > 5:
            # Většina příjmení: Novákem → Novák (odstranit -em)
            # Vzácně: Štefánkem → Štefánek (vložné e)
            # Zkontroluj pattern pro vložné 'e': obvykle -ánek, -íček, -oušek, atd.
            stem_without_kem = obs[:-3].lower()  # "štefán" z "štefánkem"

            # Známé patterny vyžadující vložné 'e'
            long_patterns = ['ánek', 'ínek', 'ýnek', 'ůnek', 'ůn', 'án', 'ín', 'ýn', 'éček', 'ášek', 'oušek', 'áček', 'íček']

            # Speciální: krátké kmeny (≤3 znaky) končící na ň, š, ř pravděpodobně vyžadují vložné e
            # Vaň → Vaněk, Paš → Pašek
            short_soft_endings = len(stem_without_kem) <= 3 and stem_without_kem[-1] in 'ňšř'

            # OBECNÉ PRAVIDLO: Krátké kmeny (≤4 znaky) pravděpodobně vyžadují vložné e
            # Kotkem → Kotek, Hájkem → Hájek (ne Kotk, Hájk)
            short_stem = len(stem_without_kem) <= 4

            if any(stem_without_kem.endswith(p) for p in long_patterns):
                # Štefánkem → Štefánek, Šimůnkem → Šimůnek
                return obs[:-3] + 'ek'
            elif short_soft_endings:
                # Vaňkem → Vaněk (vložné ě způsobuje měkčení: n→ň před -kem)
                stem = obs[:-3]
                if stem and stem[-1] in 'ňďť':
                    # Převeď měkkou souhlásku zpět na tvrdou
                    hardening = {'ň': 'n', 'ď': 'd', 'ť': 't'}
                    stem = stem[:-1] + hardening[stem[-1]]
                return stem + 'ěk'
            elif short_stem:
                # Kotkem → Kotek, Hájkem → Hájek
                return obs[:-3] + 'ek'
            # Default: odstranit jen -em (většina případů)
            else:
                return obs[:-2]  # Novákem → Novák

        # Obecný instrumentál -em → odstranění
        # Ale pozor na příjmení, kde -em je součást kmene (Šembera, Klement)
        else:
            cand = obs[:-2]  # odstranění -em
            cand_lo = cand.lower()

            # Kontrola: jestli cand+a je protected surname (Šemberem → Šembera)
            if (cand_lo + 'a') in MALE_SURNAMES_WITH_A:
                return cand + 'a'

            # Kontrola: jestli výsledek vypadá jako validní nominativ
            # Validní nominativy končí na souhlásky nebo -ý/-í/-á
            if len(cand) > 2:
                # Zkontroluj, že nekončí na -b, -d, -c, -s, -š, -ch, -g v krátkých formách
                # (ty naznačují, že -em je součást příjmení, ne koncovka)
                if cand_lo.endswith(('šemb', 'klem', 'chlum')) and len(cand) <= 5:
                    # Příliš krátké - pravděpodobně součást příjmení
                    return obs
                else:
                    # Běžný instrumentál: Novákem → Novák, Králem → Král, Švecem → Švec
                    return cand

    # ========== GENITIV: -e → REMOVE (mužská příjmení) ==========
    # Genitiv mužských příjmení končících na souhlásku: Bartoš → Bartoše, Kolář → Koláře
    # Ale pozor na příjmení, která skutečně končí na -e v nominativu (Nebeský, Nové, atd.)
    if lo.endswith('e') and len(obs) > 3:
        # Skip pokud to je přídavné jméno (-ské, -cké, -né)
        if not lo.endswith(('ské', 'cké', 'né', 'ré', 'lé')):
            stem = obs[:-1]  # Bartoše → Bartoš, Koláře → Kolář
            stem_lo = stem.lower()

            # Kontrola: odstranění -e musí dát validní příjmení (končí souhláskou)
            consonants = 'bcčdďfghjklmnňpqrřsštťvwxzž'
            if len(stem) >= 3 and stem_lo[-1] in consonants:
                # Validní genitiv → vrať nominativ bez -e
                return stem

    # ========== GENITIV: -a → CONDITIONAL ==========
    # Mnoho příjmení končí na -a v nominativu (Svoboda, Skála, Liška, atd.)
    # ALE některá jsou genitiv od příjmení končících na souhlásku (Hofmana → Hofman)

    if lo.endswith('a') and len(obs) > 3:
        # Protected surnames ending with -a in nominative
        if lo not in MALE_SURNAMES_WITH_A:
            stem_without_a = obs[:-1]

            # NOVÁ KONTROLA: Pokud obs končí na typický vzor pro česká příjmení s -a,
            # ZACHOVEJ ho jako nominativ (Koudelka, Malina, Straka)
            typical_surname_endings = ('ka', 'la', 'na', 'ra', 'ta', 'da', 'ma', 'ba', 'va', 'ha', 'ča', 'ša', 'ga', 'pa')
            if any(lo.endswith(ending) for ending in typical_surname_endings):
                # Vypadá jako typické příjmení s -a v nominativu → ZACHOVEJ
                return obs

            # Pokud po odstranění -a dostaneme validní příjmení končící na souhlásku
            # (ne na samohlásku), pravděpodobně je to genitiv
            consonants = 'bcčdďfghjklmnňpqrřsštťvwxzž'
            if stem_without_a.lower()[-1] in consonants:
                # Hofmana → Hofman, Dohnala → Dohnal (pokud už nebylo zpracováno výše)
                return stem_without_a

    # ========== GENITIV: -y → -a nebo odstranit -y ==========
    # Klímy → Klíma (genitiv mužů), Procházky → Procházka
    # ALE POUZE pokud to NENÍ přídavné jméno (-ský/-cký/-ný)
    if lo.endswith('y') and len(obs) > 3:
        # Skip if it's adjective form
        if not lo.endswith(('ský', 'cký', 'ný')):
            # Zkus nejprve -y → -a (pro Klíma, Procházka, Šembera)
            candidate_a = obs[:-1] + 'a'
            # Použij GLOBÁLNÍ seznam MALE_SURNAMES_WITH_A místo lokálního
            if candidate_a.lower() in MALE_SURNAMES_WITH_A:
                return candidate_a

            # Heuristika: -y → -a pro příjmení jako Klíma
            if obs[:-1].lower().endswith(('klím', 'dvořák', 'svobod')):
                return candidate_a

            # NOVÁ HEURISTIKA: Pokud candidate_a končí na typické české příjmenné vzory,
            # pravděpodobně je to správný nominativ s 'a'
            # Koudelka (končí -ka), Malina (končí -na), Straka (končí -ka), Bláha (končí -ha)
            candidate_a_lo = candidate_a.lower()
            typical_surname_endings = ('ka', 'la', 'na', 'ra', 'ta', 'da', 'ma', 'ba', 'va', 'ha', 'ča', 'ša', 'ga', 'pa')
            if any(candidate_a_lo.endswith(ending) for ending in typical_surname_endings):
                # Dodatečná kontrola: stem (bez 'a') musí končit souhláskou
                stem_without_a = obs[:-1]  # Maliny → Malin (stem před přidáním 'a')
                consonants = 'bcčdďfghjklmnňpqrřsštťvwxzž'
                if stem_without_a and stem_without_a[-1].lower() in consonants:
                    return candidate_a

            # Běžný případ: jen odstraň -y (Nováky → Novák)
            return obs[:-1]

    # ========== TRUNKOVANÉ PŘÍJMENÍ ==========
    # Pokud příjmení vypadá zkrácené (krátké, končí souhláskou)
    # a přidání 'a' dá známé mužské příjmení, preferuj úplnou formu
    if len(obs) >= 3 and obs[-1] not in 'aeiouyáéíóúůýěiu':
        if (lo + 'a') in MALE_SURNAMES_WITH_A:
            return obs + 'a'

    return obs

# =============== Varianty pro nahrazování ===============
def variants_for_first(first: str) -> set:
    """
    Generuje všechny pádové varianty křestního jména včetně:
    - Nominativ, Genitiv, Dativ, Akuzativ, Vokativ, Lokál, Instrumentál
    - Přivlastňovací přídavná jména (Petrův, Janin, atd.)
    """
    f = first.strip()
    if not f: return {''}
    V = {f, f.lower(), f.capitalize()}
    low = f.lower()

    # ========== Ženská jména končící na -a ==========
    if low.endswith('a'):
        stem = f[:-1]
        # Základní pády: Gen/Dat/Akuz/Vok/Lok/Instr
        V |= {stem+'y', stem+'e', stem+'ě', stem+'u', stem+'ou', stem+'o'}

        # Přivlastňovací přídavná jména (Janin dům, Petřina kniha)
        V |= {stem+s for s in ['in','ina','iny','iné','inu','inou','iným','iných','ino']}

        # Speciální případy pro měkčení (Petra → Petře, Veronka → Verunce)
        if stem.endswith('k'):
            V.add(stem[:-1] + 'c' + 'e')
            V.add(stem[:-1] + 'c' + 'i')

        # Speciální měkčení tr → tř (Petra → Petřin)
        if stem.endswith('tr'):
            soft_stem = stem[:-1] + 'ř'
            V |= {soft_stem+s for s in ['in','ina','iny','iné','inu','inou','iným','iných','ino']}

        # Speciální měkčení h → z, ch → š, k → c, r → ř
        if stem.endswith('h'):
            soft_stem = stem[:-1] + 'z'
            V.add(soft_stem + 'e')
            V.add(soft_stem + 'i')
        if stem.endswith('ch'):
            soft_stem = stem[:-2] + 'š'
            V.add(soft_stem + 'e')
            V.add(soft_stem + 'i')
        if stem.endswith(('k', 'g')):
            soft_stem = stem[:-1] + 'c'
            V.add(soft_stem + 'e')
            V.add(soft_stem + 'i')
        if stem.endswith('r') and not stem.endswith('tr'):
            soft_stem = stem[:-1] + 'ř'
            V.add(soft_stem + 'e')
            V.add(soft_stem + 'i')

    # ========== Mužská jména ==========
    else:
        # Základní pády
        V |= {f+'a', f+'ovi', f+'e', f+'em', f+'u', f+'om'}

        # Přivlastňovací přídavná jména (Petrův dům, Petrova kniha)
        V |= {f+'ův', f+'ova', f+'ovo', f+'ovu', f+'ovou', f+'ově'}
        V |= {f+'ov'+s for s in ['a','o','y','ě','ým','ých','ou','u','e']}

        # Speciální případy pro zakončení -ek, -el
        if low.endswith('ek'):
            stem_k = f[:-2] + 'k'
            V |= {stem_k+'a', stem_k+'ovi', stem_k+'em', stem_k+'u', stem_k+'e'}
            V.add(f[:-2] + 'ka')

        if low.endswith('el'):
            stem_l = f[:-2] + 'l'
            V |= {stem_l+'a', stem_l+'ovi', stem_l+'em', stem_l+'u', stem_l+'e'}
            V.add(f[:-2] + 'la')

        # Speciální případy pro zakončení -ec
        if low.endswith('ec'):
            stem_c = f[:-2] + 'c'
            V |= {stem_c+'e', stem_c+'i', stem_c+'em', stem_c+'u'}

        # Speciální případ: Jiří → Jiřího, Jiřímu, Jiřím, Jiřího
        if low.endswith('í'):
            stem = f[:-1]
            V |= {stem+'ího', stem+'ímu', stem+'ím', stem+'íh'}

        # Speciální případ: -iš/-aš → měkčení (Lukáš, Tomáš)
        if low.endswith(('áš', 'iš')):
            stem_base = f[:-1]
            V |= {stem_base+'e', stem_base+'i', stem_base+'em', stem_base+'ovi'}

        # Lokál s měkčením
        if not low.endswith(('i', 'í')):
            V |= {f+'ovi', f+'e'}

    return V

def variants_for_surname(surname: str) -> set:
    """
    Generuje všechny pádové varianty příjmení včetně:
    - Všechny pády jednotného i množného čísla
    - Přivlastňovací přídavná jména (Novákův, Novákova)
    - Speciální případy pro -ová, -ský, -ek, -ec, atd.
    """
    s = surname.strip()
    if not s: return {''}
    out = {s, s.lower(), s.capitalize()}
    low = s.lower()

    # ========== Příjmení typu -ová (ženská) ==========
    if low.endswith('ová'):
        base = s[:-1]
        out |= {
            s,
            base+'é',
            base+'ou',
            base+'á',
        }
        base_stem = s[:-3]
        out |= {
            base_stem+'ových',
            base_stem+'ovým',
            base_stem+'ové',
        }
        return out

    # ========== Příjmení typu -ský/-cký (přídavná jména) ==========
    if low.endswith(('ský','cký')):
        stem = s[:-2]
        out |= {
            stem+'ý', stem+'ého', stem+'ému', stem+'ým', stem+'ém',
            stem+'á', stem+'é', stem+'ou',
            stem+'ých', stem+'ými'
        }
        return out

    # ========== Obecná přídavná jména končící na -ý ==========
    if low.endswith('ý'):
        stem = s[:-1]
        out |= {
            stem+'ý', stem+'ého', stem+'ému', stem+'ým', stem+'ém',
            stem+'á', stem+'é', stem+'ou',
            stem+'ých', stem+'ými'
        }
        return out

    # ========== Ženská příjmení na -á (ne -ová) ==========
    if low.endswith('á') and not low.endswith('ová'):
        stem = s[:-1]
        out |= {s, stem+'é', stem+'ou', stem+'á'}
        return out

    # ========== Příjmení typu -ek (Dvořáček, Hájek) ==========
    if low.endswith('ek') and len(s) >= 3:
        stem_k = s[:-2] + 'k'
        out |= {
            s,
            stem_k+'a', stem_k+'ovi', stem_k+'em', stem_k+'u', stem_k+'e',
            stem_k+'y', stem_k+'ou',
        }
        out |= {
            stem_k+'ův', stem_k+'ova', stem_k+'ovo',
            stem_k+'ovu', stem_k+'ovou', stem_k+'ově'
        }
        out |= {
            stem_k+'ů', stem_k+'ům', stem_k+'y',
        }
        return out

    # ========== Příjmení typu -ec (Němec, Konec) ==========
    if low.endswith('ec') and len(s) >= 3:
        stem_c = s[:-2] + 'c'
        out |= {
            s,
            stem_c+'e', stem_c+'i', stem_c+'em', stem_c+'u', stem_c+'y',
        }
        out |= {
            stem_c+'ů', stem_c+'ům', stem_c+'ích', stem_c+'ech', stem_c+'emi',
        }
        out |= {
            stem_c+'ův', stem_c+'ova', stem_c+'ovo',
            stem_c+'ovu', stem_c+'ovou', stem_c+'ově'
        }
        return out

    # ========== Příjmení na -a (mužská i ženská) ==========
    if low.endswith('a') and len(s) >= 2 and not low.endswith('ová'):
        stem = s[:-1]
        out |= {
            s,
            stem+'y', stem+'ovi', stem+'ou', stem+'u', stem+'e', stem+'o',
        }
        out |= {
            stem+'ův', stem+'ova', stem+'ovo',
            stem+'ovu', stem+'ovou', stem+'ově'
        }
        out |= {
            stem+'ů', stem+'ům', stem+'y',
        }
        return out

    # ========== Obecná mužská příjmení (konsonantní kmeny) ==========
    out |= {
        s+'a', s+'ovi', s+'e', s+'em', s+'u',
    }
    out |= {
        s+'ův', s+'ova', s+'ovo',
        s+'ovu', s+'ovou', s+'ově'
    }
    out |= {
        s+'ov'+suf for suf in ['a','o','y','ě','ým','ých','ou','u','e','i']
    }
    out |= {
        s+'ů', s+'ům', s+'y', s+'ích', s+'ech',
    }

    return out

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
    r'[a-záčďéěíňóřšťúůýž ]{2,50}?'  # Změněno: pouze mezera, ne \s (který zahrnuje \n)
    r'[ \t]+\d{1,4}(?:/\d{1,4})?'  # Změněno: pouze mezera/tab, ne \s
    r',[ \t]*'  # Změněno: pouze mezera/tab
    r'\d{3}\s?\d{2}'
    r'(?:[ \t]+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž ]{1,30})?'  # Změněno: nepovinné město, pouze mezera
    r'(?:[ \t]+\d{1,2})?'  # Změněno: pouze mezera/tab
    r'(?=\s|$|,|\.|;|:|\n|\r|Rodné|IČO|DIČ|Tel|E-mail|Kontakt|OP|Datum|Narozen)',
    re.IGNORECASE | re.UNICODE
)

# SPZ/RZ (Státní poznávací značky)
# České SPZ formáty:
# - Formát XYZ NNNN: 4A5 6789, 1P2 3456 (číslice-písmeno-číslice mezera 4 číslice)
# - Formát XYY NNNN: 1AB 2345 (číslice-2písmena mezera 4 číslice)
# - S prefixem: "SPZ: ...", "RZ: ...", "reg. značka: ..."
LICENSE_PLATE_RE = re.compile(
    r'(?:'
    r'(?:SPZ|RZ|reg\.?\s*(?:značka|číslo)?)\s*:?\s*'  # Volitelný prefix
    r')?'
    r'('  # Capture group pro samotnou SPZ
    r'\d[A-Z]\d\s+\d{4}|'  # 4A5 6789 (číslice-písmeno-číslice mezera 4číslice)
    r'\d[A-Z]{2}\s+\d{4}|'  # 1AB 2345 (číslice-2písmena mezera 4číslice)
    r'\d[A-Z]{2}\d{4}|'  # 1AB2345 (bez mezery)
    r'[A-Z]{2}\d{4,5}'  # AB12345
    r')',
    re.IGNORECASE
)

# VIN (Vehicle Identification Number) - 17 znaků
# Formát: TMBCF61Z0L7654321, 1HGBH41JXMN109186
VIN_RE = re.compile(
    r'(?:VIN|Vehicle\s+ID|Identifikační\s+číslo\s+vozidla)\s*[:\-]?\s*([A-HJ-NPR-Z0-9]{17})\b|'
    r'\b([A-HJ-NPR-Z0-9]{17})\b(?=\s*(?:VIN|vozidlo|auto|vehicle))',
    re.IGNORECASE
)

# MAC adresa (Media Access Control)
# Formát: 00:1B:44:11:3A:B7, 00-1B-44-11-3A-B7, 001B.4411.3AB7
MAC_RE = re.compile(
    r'(?:MAC\s+(?:address|adresa)?)\s*[:\-]?\s*([0-9A-F]{2}[:\-][0-9A-F]{2}[:\-][0-9A-F]{2}[:\-][0-9A-F]{2}[:\-][0-9A-F]{2}[:\-][0-9A-F]{2})|'
    r'\b([0-9A-F]{2}[:\-][0-9A-F]{2}[:\-][0-9A-F]{2}[:\-][0-9A-F]{2}[:\-][0-9A-F]{2}[:\-][0-9A-F]{2})\b|'
    r'\b([0-9A-F]{4}\.[0-9A-F]{4}\.[0-9A-F]{4})\b',
    re.IGNORECASE
)

# IMEI (International Mobile Equipment Identity)
# Formát: 15 číslic (např. 123456789012345)
IMEI_RE = re.compile(
    r'(?:IMEI|International\s+Mobile\s+Equipment\s+Identity)\s*[:\-]?\s*(\d{15})\b|'
    r'\b(\d{15})\b(?=\s*(?:IMEI|mobil|telefon|mobile))',
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
# DŮLEŽITÉ: Musí mít SILNÝ kontext (RČ, Rodné číslo, nar.) - PRIORITA!
# Regex má 2 capture groups - první pro context match, druhý pro standalone
BIRTH_ID_RE = re.compile(
    r'(?:'
    r'(?:RČ|Rodné\s+číslo|r\.?\s?č\.?|nar\.|narozen[aáý]?|Narození)\s*:?\s*(\d{6}/?\d{3,4})|'  # S kontextem (CAPTURE GROUP 1)
    r'(?<!FÚ-)(?<!KS-)(?<!VS-)(?<!čj-)(?<!\d)(\d{6}/\d{3,4})(?!\d)'  # Bez kontextu, ale ne po FÚ-/KS-/VS- (CAPTURE GROUP 2)
    r')',
    re.IGNORECASE
)

# Číslo OP (formát: AB 123456 nebo OP: 123456789)
# DŮLEŽITÉ: Musí být před PHONE_RE!
ID_CARD_RE = re.compile(
    r'(?:'
    r'\b([A-Z]{2}\s?\d{6})\b|'  # Standardní formát: AB 123456
    r'(?:OP|pas|pas\.|pas\.č\.|č\.OP)\s*[:\-]?\s*(\d{6,9})'  # OP: 123456789 nebo Pas: 123456
    r')',
    re.IGNORECASE
)

# Email - OPRAVENO: Podpora pro diakritiku v lokální části
# Zachytí: martina.horáková@neoteam.cz, jan.novák@firma.cz, atd.
EMAIL_RE = re.compile(
    r'\b([a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
)

# Telefon (CZ formáty) - NESMÍ zachytit prefix do hodnoty!
# Prefix je mimo capture group, telefon je uvnitř
# DŮLEŽITÉ: Whitelist - NEchytej biometrické/technické prefixy!
# DŮLEŽITÉ: NEchytej částky (čísla následovaná Kč, EUR, USD)
PHONE_RE = re.compile(
    r'(?!'  # Negative lookahead - NEchytej pokud předchází:
    r'(?:IRIS_SCAN|VOICE_RK|HASH_BIO|FINGERPRINT|FACIAL_|RETINA_|PALM_|DNA_)_[A-Z0-9_]*'
    r')'
    r'(?:tel\.?|telefon|mobil|GSM)?\s*:?\s*'  # Volitelný prefix (MIMO capture group!)
    r'('  # START capture group - jen samotné číslo
    r'\+420\s?\d{3}\s?\d{3}\s?\d{3}|'  # +420 xxx xxx xxx
    r'\+420\s?\d{3}\s?\d{2}\s?\d{2}\s?\d{2}|'  # +420 xxx xx xx xx
    r'(?<!\d)\d{3}\s?\d{3}\s?\d{3}(?!\s*(?:Kč|EUR|USD|CZK)\b)(?!\d)|'  # xxx xxx xxx (NE pokud následuje měna!)
    r'(?<!\d)\d{3}\s?\d{2}\s?\d{2}\s?\d{2}(?!\d)'  # xxx xx xx xx
    r')',  # END capture group
    re.IGNORECASE
)

# Bankovní účet (formát: číslo/kód banky NEBO dlouhé číslo s kontextem)
# DŮLEŽITÉ: IBAN je samostatný regex níže!
# NESMÍ zachytit spisové značky (FÚ-xxx/xxxx, KS-xxx/xxxx, VS-xxx)
# DŮLEŽITÉ: Kód banky musí být součástí zachyceného účtu!
BANK_RE = re.compile(
    r'(?:'
    # Standardní formát s předčíslím: 3622-1234567890/0710
    r'(?<!FÚ-)(?<!KS-)(?<!VS-)(?<!čj-)(\d{1,6}-\d{6,16}/\d{4})|'
    # Standardní formát: 123456/2010, 1234567890/3210
    r'(?<!FÚ-)(?<!KS-)(?<!VS-)(?<!čj-)(\d{6,16}/\d{4})|'
    # S kontextem: "číslo účtu: 123456789/0800" - zachytí i s kódem pokud je
    r'(?:číslo\s+účtu|účet|účtu|platba\s+na\s+účet|bankovní\s+účet)\s*:?\s*(\d{6,16}(?:/\d{4})?)'
    r')\b',
    re.IGNORECASE
)

# IBAN (mezinárodní formát bankovního účtu)
# CZ IBAN: CZ + 2 číslice + 20 číslic = 24 znaků celkem
# KRITICKÉ: Musí být před CARD_RE, protože obsahuje dlouhé sekvence číslic!
IBAN_RE = re.compile(
    r'\b(CZ\d{2}(?:\s?\d{4}){5})\b',
    re.IGNORECASE
)

# Datum (DD.MM.YYYY nebo DD. MM. YYYY)
# Obecný pattern pro všechna data
DATE_RE = re.compile(
    r'\b(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})\b'
)

# Datum narození (DOB) - specificky pro "Datum narození:" kontext
DOB_RE = re.compile(
    r'(?:Datum\s+narození|Narozen[aý]?|Nar\.|Narození)\s*:?\s*(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})\b',
    re.IGNORECASE
)

# Datum slovně (např. "15. března 2024")
DATE_WORDS_RE = re.compile(
    r'\b(\d{1,2}\.\s?(?:ledna|února|března|dubna|května|června|července|srpna|září|října|listopadu|prosince)\s?\d{4})\b',
    re.IGNORECASE
)

# Hesla a credentials (KRITICKÉ - hodnotu neukládat!)
PASSWORD_RE = re.compile(
    r'(?:password|heslo|passwd|pwd|pass)\s*[:\-=]\s*([^\s,;\.]{3,50})',
    re.IGNORECASE
)

# Credentials pattern - "Credentials: username / password"
CREDENTIALS_RE = re.compile(
    r'(?i)\b(credentials?|login|přihlašovací\s+údaje)\s*:\s*([A-Za-z0-9._\-@]+)\s*/\s*(\S+)',
    re.IGNORECASE
)

# API klíče, Secrets, Tokens (KRITICKÉ - hodnotu neukládat!)
API_KEY_RE = re.compile(
    r'(?:AWS\s+)?(?:Access\s+)?(?:Key(?:\s+ID)?|Secret(?:\s+Access\s+Key)?|Token|API[_\s]?Key)\s*[:\-=]\s*([A-Za-z0-9+/=_\-]{16,})',
    re.IGNORECASE
)

SECRET_RE = re.compile(
    r'(?:Stripe|SendGrid|GitHub|Secret|Client[_\s]?Secret|Access\s+Token|Personal\s+Access\s+Token)\s*[:\-=]\s*([A-Za-z0-9+/=_\-]{16,})',
    re.IGNORECASE
)

SSH_KEY_RE = re.compile(
    r'(?:ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256)\s+([A-Za-z0-9+/=]{50,})',
    re.IGNORECASE
)

# Usernames, Account IDs, Hostnames
USERNAME_RE = re.compile(
    r'(?:Login|Username|Uživatel|User|GitHub|Jira|AWS\s+Console)\s*[:\-=]\s*([A-Za-z0-9._\-@]+)',
    re.IGNORECASE
)

ACCOUNT_ID_RE = re.compile(
    r'(?:Account\s+ID|AWS\s+Account)\s*[:\-=]\s*(\d{12})',
    re.IGNORECASE
)

HOSTNAME_RE = re.compile(
    r'(?:hostname|host|server|RDS|endpoint)\s*[:\-=]\s*([a-z0-9\-\.]+\.[a-z]{2,})',
    re.IGNORECASE
)

# IP adresy (IPv4)
IP_RE = re.compile(
    r'\b(?<!\d\.)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?!\.\d)\b'
)

# Platební karty (13-19 číslic)
# Rozšířený pattern: Visa/MC (16), AmEx (15), Diners (14), atd.
# DŮLEŽITÉ: IBAN se zpracovává PŘED tímto regexem!
# DŮLEŽITÉ: Zachytí i "Číslo:" když je to 16-19 číslic (typicky karta)
CARD_RE = re.compile(
    r'(?:'
    # S prefixem: "Číslo karty:", "Karta:", "Card Number:", "Číslo:" (když 16 číslic)
    r'(?:Číslo\s+(?:platební\s+)?karty|Číslo|(?:Platební\s+)?(?:Karta|Card)(?:\s+\d+)?(?:\s+Number)?)\s*[:\-=]?\s*'
    r'('
    r'\d{4}[\s\-]?\d{6}[\s\-]?\d{5}|'  # AmEx: 4-6-5 (15 číslic)
    r'\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{2,3})?|'  # Visa/MC: 16-19
    r'\d{4}[\s\-]?\d{6}[\s\-]?\d{4}'  # Diners: 4-6-4 (14 číslic)
    r')'
    r')',
    re.IGNORECASE
)

# Čísla pojištěnce
INSURANCE_ID_RE = re.compile(
    r'(?:Číslo\s+pojištěnce|Pojišťovna|VZP|ČPZP|ZPŠ|OZP)[,\s:]+(?:číslo\s*:?\s*)?(\d{10})',
    re.IGNORECASE
)

# RFID/Badge čísla
RFID_RE = re.compile(
    r'(?:RFID\s+karta|badge|ID\s+karta)\s*[:#]?\s*([A-Za-z0-9\-_/]+)',
    re.IGNORECASE
)

# ========== SOCIAL MEDIA (KRITICKÉ - PII) ==========

# LinkedIn profily
LINKEDIN_RE = re.compile(
    r'(?:LinkedIn|linkedin)?\s*:?\s*(https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_]+)',
    re.IGNORECASE
)

# Facebook profily
FACEBOOK_RE = re.compile(
    r'(?:Facebook|facebook)?\s*:?\s*(https?://(?:www\.)?facebook\.com/[A-Za-z0-9\._\-]+)',
    re.IGNORECASE
)

# Instagram handle - POUZE s explicitním kontextem nebo URL
# NEchytej @ z emailů!
INSTAGRAM_RE = re.compile(
    r'(?:Instagram|instagram)\s*:?\s*(@[A-Za-z0-9_]+)|'  # Handle pouze s prefixem "Instagram:"
    r'(https?://(?:www\.)?instagram\.com/[A-Za-z0-9_\.]+)',  # Nebo plné URL
    re.IGNORECASE
)

# Skype ID
SKYPE_RE = re.compile(
    r'(?:Skype|skype)\s*:?\s*([A-Za-z0-9\._\-]+)',
    re.IGNORECASE
)

# ========== BIOMETRIC IDs (KRITICKÉ - GDPR Článek 9) ==========

# Voice ID / Hlasový profil
VOICE_ID_RE = re.compile(
    r'(?:Hlasový\s+profil|Voice\s+ID|VOICE_ID|Voice\s+Profile)\s*[:\-=]?\s*([A-Z0-9_\-]+)',
    re.IGNORECASE
)

# Biometric hash (otisk prstu, sítnice, atd.)
# Zachytí pouze hodnoty po explicitním "hash:", "Hash:", nebo samostatné hash kódy
BIO_HASH_RE = re.compile(
    r'(?:hash|Hash):\s*([A-Z][A-Z0-9_\-]{10,})|'  # hash: HASH_BIO_JP_2024_0156
    r'\b((?:HASH_BIO|IRIS|RETINA|FINGERPRINT|PALM|DNA)_[A-Z0-9_\-]{8,})\b'  # Standalone hash codes
)

# Photo ID / Face ID files
PHOTO_ID_RE = re.compile(
    r'(photo_id_[A-Za-z0-9_\-]+\.(?:jpg|jpeg|png|gif|bmp))|'
    r'(face_id_[A-Za-z0-9_\-]+\.(?:jpg|jpeg|png|gif|bmp))|'
    r'(?:Fotografie|Photo\s+ID|Face\s+ID)\s*[:\-=]?\s*[Uu]loženo.*?\(([A-Za-z0-9_\-]+\.(?:jpg|jpeg|png|gif|bmp))\)',
    re.IGNORECASE
)

# Enhanced API Key - zachytí i složitější formáty
API_KEY_ENHANCED_RE = re.compile(
    r'(?:API\s+klíč|API\s+Key|api_key)\s*[:\-=]?\s*([A-Za-z0-9_\-]+)',
    re.IGNORECASE
)

# Genetické identifikátory (rs...) - NESMÍ být zachyceny jako ICO!
# Pattern: rs28897696, rs1234567
GENETIC_ID_RE = re.compile(
    r'\b(rs\d{6,})\b',
    re.IGNORECASE
)

# ========== DOPLNĚNÉ GDPR KATEGORIE ==========

# Datum narození (samostatné, ne v rodném čísle)
# Formáty: dd.mm.yyyy, dd/mm/yyyy, dd-mm-yyyy
# S kontextem: "datum narození:", "nar.", "narozen(a)"
BIRTH_DATE_RE = re.compile(
    r'(?:datum\s+narození|nar\.|narozen[aáý]?)\s*[:\-]?\s*'
    r'(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{4})',
    re.IGNORECASE
)

# Číslo pasu
# Formáty: 12345678 (8 číslic), AB123456 (2 písmena + 6 číslic)
PASSPORT_RE = re.compile(
    r'(?:pas|passport|č\.\s*pasu)\s*(?:č\.)?\s*[:\-]?\s*([A-Z]{0,2}\d{6,9})\b',
    re.IGNORECASE
)

# Číslo řidičského průkazu
# Formáty: AB123456, 12345678
DRIVER_LICENSE_RE = re.compile(
    r'(?:ŘP|řidičák|řidičský\s+průkaz|driver\'?s?\s*license)\s*(?:č\.)?\s*[:\-]?\s*([A-Z]{0,2}\d{6,9})\b',
    re.IGNORECASE
)

# Benefitní karty (MultiSport, Sodexo, Edenred, atd.) - DŮLEŽITÉ PII!
# Formáty: 9876543210, MS-123456, SOD/123456, "ID karty: 9876543210"
# Důvod přidání: Unikátní identifikátor osoby, jednoznačně PII
BENEFIT_CARD_RE = re.compile(
    r'(?:'
    r'(?:MultiSport|Sodexo|Edenred|benefitní\s+karta|benefit\s+card)\s*(?:karta|č\.?|ID)?\s*[:\-]?\s*([A-Z]{0,3}[\-/]?\d{6,12})|'
    r'ID\s+karty\s*[:\-]\s*(\d{6,12})'
    r')\b',
    re.IGNORECASE
)

# =============== Třída Anonymizer ===============
class Anonymizer:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.counter = defaultdict(int)
        self.canonical_persons = []  # list of {first, last, tag}
        self.person_index = {}  # (first_norm, last_norm) -> tag
        self.person_variants = {}  # tag -> set of all variants
        self.entity_map = defaultdict(lambda: defaultdict(set))  # typ -> original -> varianty
        self.entity_index_cache = defaultdict(dict)  # OPTIMIZATION: typ -> original -> idx cache
        self.entity_reverse_map = defaultdict(dict)  # OPTIMIZATION: typ -> variant -> original
        self.source_text = ""  # Store original text for validation

    def _get_or_create_label(self, typ: str, original: str, store_value: bool = True) -> str:
        """Vrátí existující nebo vytvoří nový štítek pro entitu.

        Args:
            typ: Typ entity (PASSWORD, EMAIL, atd.)
            original: Původní hodnota
            store_value: False pro citlivá data (hesla, API klíče) - uloží jen "***REDACTED***"
        """
        # Normalizace
        orig_norm = original.strip()

        # Speciální cleanup pro ADDRESS - odstraň prefixy "Sídlo:", "Trvalé bydliště:", "Trvalý pobyt:" atd.
        if typ == 'ADDRESS':
            orig_norm = re.sub(r'^(Sídlo|Trvalé\s+bydliště|Trvalý\s+pobyt|Bydliště|Adresa|Místo\s+podnikání|Se\s+sídlem|Bytem)\s*:\s*', '', orig_norm, flags=re.IGNORECASE)

        # OPTIMIZATION: Use reverse_map for O(1) lookup instead of O(n) iteration
        # Check if this variant already exists
        if orig_norm in self.entity_reverse_map[typ]:
            existing_orig = self.entity_reverse_map[typ][orig_norm]
            existing_idx = self.entity_index_cache[typ][existing_orig]
            return f"[[{typ}_{existing_idx}]]"

        # Vytvoř nový
        idx = len(self.entity_map[typ]) + 1

        # Pro citlivá data: unikátní placeholder pro každý item
        # Pro běžná data: ukládej skutečnou hodnotu
        if store_value:
            map_key = orig_norm
        else:
            # Každý citlivý item má unikátní klíč, ale zobrazí se jako ***REDACTED***
            map_key = f"***REDACTED_{idx}***"

        self.entity_map[typ][map_key].add(orig_norm)
        self.entity_index_cache[typ][map_key] = idx  # Cache the index
        self.entity_reverse_map[typ][orig_norm] = map_key  # Reverse lookup
        return f"[[{typ}_{idx}]]"

    def _normalize_for_matching(self, text: str) -> str:
        """Normalizuje text pro porovnávání (odstranění diakritiky, lowercase)."""
        if not text: return ""
        n = unicodedata.normalize('NFD', text)
        no_diac = ''.join(c for c in n if not unicodedata.combining(c))
        normalized = re.sub(r'[^A-Za-z]', '', no_diac).lower()

        # Slovak→Czech varianty pro matching
        # Alica→Alice, Lucia→Lucie, aby se považovaly za stejnou osobu
        slovak_to_czech = {
            'alica': 'alice',
            'lucia': 'lucie'
        }
        normalized = slovak_to_czech.get(normalized, normalized)

        return normalized

    def _ensure_person_tag(self, first_nom: str, last_nom: str) -> str:
        """Zajistí, že pro danou osobu existuje tag a vrátí ho."""

        key = (self._normalize_for_matching(first_nom), self._normalize_for_matching(last_nom))

        # DEBUG (disabled)
        # debug_names = ['jul', 'valer', 'beatr', 'elvir']
        # if any(name in first_nom.lower() or name in last_nom.lower() for name in debug_names):
        #     exists = key in self.person_index
        #     print(f"    [ENSURE] first_nom='{first_nom}', last_nom='{last_nom}', key={key}, exists={exists}")

        if key in self.person_index:
            return self.person_index[key]

        # Vytvoř nový tag
        self.counter['PERSON'] += 1
        tag = f'[[PERSON_{self.counter["PERSON"]}]]'

        # Ulož do indexu
        self.person_index[key] = tag
        self.canonical_persons.append({'first': first_nom, 'last': last_nom, 'tag': tag})

        # Vygeneruj všechny pádové varianty
        fvars = variants_for_first(first_nom)
        svars = variants_for_surname(last_nom)
        self.person_variants[tag] = {f'{f} {s}' for f in fvars for s in svars}

        # Ulož kanonickou formu do entity_map
        canonical_full = f'{first_nom} {last_nom}'
        self.entity_map['PERSON'][canonical_full].add(canonical_full)
        self.entity_index_cache['PERSON'][canonical_full] = self.counter['PERSON']
        self.entity_reverse_map['PERSON'][canonical_full] = canonical_full

        return tag

    def _apply_known_people(self, text: str) -> str:
        """Aplikuje známé osoby (již detekované) - nahrazuje všechny pádové varianty stejným tagem."""
        # FÁZE 1: Nahrazení plných jmen (křestní + příjmení)
        for p in self.canonical_persons:
            tag = p['tag']

            # Pro každou variantu této osoby (seřazeno od nejdelší)
            for pat in sorted(self.person_variants[tag], key=len, reverse=True):
                # FILTR: Odmítni zkrácené genitivy
                parts = pat.split()
                if len(parts) == 2:
                    fv, lv = parts
                    fv_lo = fv.lower()

                    # Pokud křestní jméno má 3-5 znaků a končí na 'k' → zkrácený genitiv
                    if 3 <= len(fv) <= 5 and fv_lo[-1] == 'k':
                        continue

                    # Pokud křestní jméno má 3 znaky a nekončí na samohlásku/n/l/r → zkrácený
                    if len(fv) == 3 and not fv_lo[-1] in 'aeiouyáéíóúůýnlr':
                        continue

                rx = re.compile(r'(?<!\w)'+re.escape(pat)+r'(?!\w)', re.IGNORECASE)

                def repl(m):
                    surf = m.group(0)
                    # Zaznamenej tuto variantu
                    canonical = f'{p["first"]} {p["last"]}'
                    self.entity_map['PERSON'][canonical].add(surf)
                    return tag

                text = rx.sub(repl, text)

        return text

    def _replace_remaining_people(self, text: str) -> str:
        """Detekuje a nahradí zbývající osoby.

        FÁZE detekce (v pořadí):
        1. FÁZE 3.5: Maiden names - (rozená Novotná), (dříve Svobodová)
        2. FÁZE 3: Samostatná příjmení - "Novák uvedl", "pan Dvořák"
        3. FÁZE 3.7: Samostatná křestní jména - "Jakub pracoval", "Eva řekla"
        4. Jména s titulem - "MUDr. Jan Novák"
        5. Běžná jména - "Jan Novák", "Eva Malá"
        """

        # ========== FÁZE 3.5: MAIDEN NAMES (RODNÁ PŘÍJMENÍ) ==========
        # Pattern: (rozená Novotná), (dříve Svobodová), (roz. Malá)
        # Tyto jsou velmi specifické a mají vysokou prioritu

        def replace_maiden_name(match):
            prefix = match.group(1)  # "rozená", "dříve", "roz."
            surname = match.group(2)  # "Novotná"

            # Odhadni nominativ
            surname_nom = infer_surname_nominative(surname)

            # Vytvoř tag pro příjmení (použijeme prázdné křestní jméno jako marker)
            tag = self._ensure_person_tag("", surname_nom)

            return f"({prefix} {tag})"

        maiden_name_pattern = re.compile(
            r'\((rozená|rozenou|roz\.|dříve|dřív|původně)\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\)',
            re.UNICODE | re.IGNORECASE
        )

        text = maiden_name_pattern.sub(replace_maiden_name, text)

        # ========== FÁZE 3: SAMOSTATNÁ PŘÍJMENÍ ==========
        # Pattern: "Novák uvedl", "pan Dvořák", "Novákovi bylo", "od Maláové"
        # DŮLEŽITÉ: Nenahrazuj, pokud následuje křestní jméno (to je full name)

        def replace_standalone_surname(match):
            prefix = match.group(1) if match.groups()[0] else ""  # "pan", "paní", ""
            surname = match.group(2) if len(match.groups()) > 1 else match.group(1)

            # Odhadni nominativ
            surname_nom = infer_surname_nominative(surname)

            # Vytvoř tag (prázdné křestní jméno pro standalone příjmení)
            tag = self._ensure_person_tag("", surname_nom)

            if prefix:
                return f"{prefix} {tag}"
            else:
                return tag

        # Pattern pro samostatné příjmení s kontextem
        # Zachytí: "pan Novák", "paní Malá", "Novák uvedl", "Novákovi bylo"
        standalone_surname_pattern = re.compile(
            r'(?:'
            r'(?:pan|paní|pana|paní|panu)\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)|'  # pan Novák
            r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+ov[ia])\s+(?:uvedl|uvedla|řekl|řekla|byl|byla|měl|měla)|'  # Novákovi uvedl
            r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\s+(?:uvedl|uvedla|řekl|řekla|potvrdil|potvrdila)'  # Novák uvedl
            r')',
            re.UNICODE | re.IGNORECASE
        )

        # POZOR: Tento pattern může zachytit i false positives, takže musíme být opatrní
        # Raději ho zatím zakomentujeme a přidáme později po testování
        # text = standalone_surname_pattern.sub(replace_standalone_surname, text)

        # ========== FÁZE 3.7: SAMOSTATNÁ KŘESTNÍ JMÉNA ==========
        # Pattern: "Jakub pracoval jako...", "Eva řekla...", ale NE "Praha", "Česká", atd.
        def replace_standalone_first_name(match):
            name = match.group(1)
            name_lower = name.lower()

            # Kontrola, zda je to křestní jméno z knihovny
            if name_lower not in CZECH_FIRST_NAMES:
                return match.group(0)

            # Ignore list - slova která vypadají jako jména, ale nejsou
            ignore_words = {
                'praha', 'brno', 'ostrava', 'plzeň', 'česká', 'slovenská',
                'evropa', 'amerika', 'asie', 'afrika', 'čech', 'moravia'
            }
            if name_lower in ignore_words:
                return match.group(0)

            # INFERENCE: Převeď na nominativ (Petru → Petr, Tomáši → Tomáš)
            name_nom = infer_first_name_nominative(name)

            # Vytvoř/najdi tag pro samostatné křestní jméno (v nominativu!)
            tag = self._ensure_person_tag(name_nom, "")

            return tag

        # Pattern pro samostatné křestní jméno následované slovesem nebo "jako"
        # Rozšířeno o uvozovky a další slovesa
        standalone_first_name_pattern = re.compile(
            r'(?:^|["\s])([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\s+(?:pracoval|pracovala|řekl|řekla|uvedl|uvedla|jako|byl|byla|je|jsou|měl|měla|dělal|dělala)',
            re.UNICODE | re.MULTILINE
        )

        def replace_standalone_wrapper(match):
            # Zachovej prefix (uvozovky nebo mezeru)
            prefix = match.group(0)[0] if match.group(0)[0] in ('"', ' ', '\n', '\t') else ''
            result = replace_standalone_first_name(match)
            # Pokud bylo nahrazeno, přidej prefix
            if result != match.group(0):
                return prefix + result[len(prefix):] if prefix else result
            return match.group(0)

        text = standalone_first_name_pattern.sub(replace_standalone_wrapper, text)

        # DÁLE: Pattern pro jména s titulem (MUDr. Eva Malá)
        # Tento musí jít PŘED obecným pattern aby titul nebyl ztracen
        titled_pattern = re.compile(
            r'(Ing\.|Mgr\.|Bc\.|MUDr\.|JUDr\.|PhDr\.|RNDr\.|Prof\.|Doc\.|Ph\.D\.|MBA|CSc\.|DrSc\.)\s+'
            r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\s+'
            r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)',
            re.UNICODE
        )

        def replace_titled(match):
            title = match.group(1)
            first = match.group(2)
            last = match.group(3)

            # ========== VALIDACE - STEJNÁ JAKO V replace_person() ==========

            # 1. Blacklist kritických slov
            critical_blacklist = {
                's.r.o.', 'a.s.', 'spol.', 'k.s.', 'v.o.s.', 'o.p.s.',
                'ltd', 'inc', 'corp', 'gmbh', 'llc',
                'czech', 'republic', 'synlab', 'gymnázium', 'gymnasium',
                'university', 'univerzita', 'fakulta', 'klinika', 'nemocnice',
                'centrum', 'ústav', 'institute', 'academy', 'akademie',
                'kaspersky', 'endpoint', 'latitude', 'archer', 'classic',
                'windows', 'linux', 'android', 'ios', 'office', 'excel',
                'ředitelka', 'ředitel', 'jednatel', 'jednatelka',
                'manager', 'director', 'chief', 'officer',
                'vyšetřující', 'vyšetřovatel', 'lékař', 'doktor', 'sestra'
            }

            combined = f"{first} {last}".lower()
            for word in critical_blacklist:
                if word in combined:
                    return match.group(0)  # Není osoba

            # 2. Role detection - pokud první slovo je role
            role_words = {
                'ředitelka', 'ředitel', 'jednatel', 'jednatelka',
                'manager', 'director', 'chief', 'officer',
                'specialist', 'consultant', 'coordinator',
                'developer', 'architect', 'engineer', 'analyst',
                'vyšetřující', 'vyšetřovatel', 'lékař', 'doktor'
            }
            if first.lower() in role_words:
                return match.group(0)  # Role, ne osoba

            # 3. Validace křestního jména
            first_lo = first.lower()
            common_czech_names = {'jan', 'petr', 'pavel', 'jiří', 'josef', 'tomáš', 'martin', 'jakub', 'david', 'daniel'}

            if first_lo not in CZECH_FIRST_NAMES and first_lo not in common_czech_names:
                # Zkrácené genitivy (Han, Elišk, Radk) - odmítnout
                if len(first) < 3:
                    return match.group(0)
                # Pokud má 3 znaky a nekončí na samohlásku ani n/l/r
                if len(first) == 3 and not first_lo[-1] in 'aeiouyáéíóúůýnlr':
                    return match.group(0)
                # Zkrácené tvary končící na 'k' (4-5 znaků)
                if 4 <= len(first) <= 5 and first_lo[-1] == 'k':
                    return match.group(0)

            # Vytvoř/najdi tag pro osobu (s inferencí nominativu)
            last_nom = infer_surname_nominative(last)
            first_nom = infer_first_name_nominative(first) or first

            # DEBUG: Inference logging (disabled)
            # if first != first_nom or last != last_nom:
            #     print(f"[DEBUG-TITLED] '{first} {last}' → '{first_nom} {last_nom}'")

            tag = self._ensure_person_tag(first_nom, last_nom)

            # Ulož původní formu jako variantu (pokud je jiná než kanonická)
            original_form = f"{first} {last}"
            canonical = f"{first_nom} {last_nom}"
            if original_form.lower() != canonical.lower():
                # Kontrola shody rodu před uložením varianty
                gender = get_first_name_gender(first_nom)
                if is_valid_surname_variant(last, last_nom, gender):
                    self.entity_map['PERSON'][canonical].add(original_form)

            # Vrať titul + tag
            return f"{title} {tag}"

        # Nahraď titulované osoby NEJPRVE
        text = titled_pattern.sub(replace_titled, text)

        # Pak běžný pattern pro jména bez titulu
        titles = r'(?:Ing\.|Mgr\.|Bc\.|MUDr\.|JUDr\.|PhDr\.|RNDr\.|Ph\.D\.|MBA|CSc\.|DrSc\.)'

        # Pattern pro jméno příjmení
        person_pattern = re.compile(
            r'\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)'
            r'\s+'
            r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)\b',
            re.UNICODE
        )

        def replace_person(match):
            first_obs = match.group(1)
            last_obs = match.group(2)

            # DEBUG (disabled)
            # debug_names = ['radek', 'radk', 'marek', 'mark', 'karel', 'karl', 'řehoř', 'blank', 'vlast']
            # if any(name in first_obs.lower() or name in last_obs.lower() for name in debug_names):
            #     print(f"    [MATCH] first_obs='{first_obs}', last_obs='{last_obs}'")

            # ========== A) BLACKLIST NE-OSOB ==========

            # 1. Blacklist kritických slov (firmy, instituce, produkty, role)
            critical_blacklist = {
                # Firmy a právní formy
                's.r.o.', 'a.s.', 'spol.', 'k.s.', 'v.o.s.', 'o.p.s.',
                'ltd', 'inc', 'corp', 'gmbh', 'llc',
                # Instituce
                'czech', 'republic', 'synlab', 'gymnázium', 'gymnasium',
                'university', 'univerzita', 'fakulta', 'klinika', 'nemocnice',
                'centrum', 'ústav', 'institute', 'academy', 'akademie',
                'motol', 'bulovka', 'thomayer', 'center',
                # Produkty/Software
                'kaspersky', 'endpoint', 'latitude', 'archer', 'classic',
                'windows', 'linux', 'android', 'ios', 'office', 'excel',
                # Role/Pozice (když jsou samostatně)
                'ředitelka', 'ředitel', 'jednatel', 'jednatelka',
                'manager', 'director', 'chief', 'officer',
                'vyšetřující', 'vyšetřovatel', 'lékař', 'doktor', 'sestra'
            }

            # Kontrola, zda hodnota obsahuje blacklist slovo
            combined = f"{first_obs} {last_obs}".lower()
            for word in critical_blacklist:
                if word in combined:
                    return match.group(0)  # Není osoba

            # 2. Rozšířený ignore list (původní)
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
                # Finance/Investment
                'capital', 'equity', 'value', 'crescendo', 'investment',
                'fund', 'holdings', 'partners', 'assets', 'portfolio',
                # Pozice/role
                'jednatel', 'jednatelka', 'ředitel', 'ředitelka',
                'auditor', 'manager', 'consultant', 'specialist',
                'assistant', 'coordinator', 'analyst', 'pacient',
                'scrum', 'master', 'developer', 'architect', 'engineer',
                'officer', 'professional', 'certified', 'advanced',
                'management', 'legal', 'counsel', 'executive',
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
                'cisco', 'processing', 'notářská',
                # Zdravotnictví + Léky/Produkty
                'nemocnice', 'poliklinika', 'polikliniek', 'nemocniec',
                'healthcare', 'symbicort', 'turbuhaler', 'spirometr',
                'jaeger', 'medical', 'health', 'pharma', 'pharmaceutical',
                # Další
                'care', 'plus', 'minus', 'service', 'services',
                'group', 'company', 'corp', 'ltd', 'gmbh', 'inc'
            }

            # Kontrola proti ignore listu
            if first_obs.lower() in ignore_words or last_obs.lower() in ignore_words:
                return match.group(0)

            # 3. Detekce firem, produktů, institucí (neměly by být PERSON)
            non_person_patterns = [
                # Tech/Software
                r'\b(tech|cloud|web|solutions?|data|digital|software|analytics)\b',
                r'\b(team|hub|enterprise|premium|standard|professional)\b',
                r'\b(google|amazon|microsoft|apple|facebook|splunk|cisco|samsung)\b',
                r'\b(repository|authenticator|vision|protection|security|galaxy)\b',
                r'\b(legamedis|společností)\b',  # Konkrétní společnosti
                r'\b(některé|některý|některá|subjekt|subjekty|subjektů)\b',  # Obecná slova ("některé subjekty")
                # Finance/Investment
                r'\b(capital|equity|value|investment|fund|holdings|assets)\b',
                r'\b(crescendo|ventures|partners|portfolio)\b',
                # Management/Business
                r'\b(management|processing|executive|legal|counsel)\b',
                r'\b(clinic|series|launch|innovate|healthcare)\b',
                # Products/Medical
                r'\b(symbicort|turbuhaler|spirometr|jaeger)\b',
                r'\b(pharma|pharmaceutical|medical)\b',
                # Company suffixes když jsou uprostřed
                r'\b(group|company|corp|ltd|gmbh|inc|services?)\b',
                # Religious/Geographic (kostely, náměstí, ulice...)
                r'\b(svaté|svatého|svatý|kostel)\b'
            ]
            for pattern in non_person_patterns:
                if re.search(pattern, combined):
                    return match.group(0)

            # 4. Detekce názvů firem (končí na s.r.o., a.s., spol., Ltd. atd.)
            context_after = text[match.end():match.end()+20]
            if re.search(r'^\s*(s\.r\.o\.|a\.s\.|spol\.|k\.s\.|v\.o\.s\.|ltd\.?|inc\.?)', context_after, re.IGNORECASE):
                return match.group(0)

            # ========== B) VALIDACE ČESKÉ OSOBY ==========

            # 5. Požadované patterny pro skutečnou osobu
            # Max 2-3 tokeny (již splněno regex patternem)
            # Každý token začíná velkým písmenem (již splněno)

            # 6. Validace českého příjmení (poslední token)
            last_lo = last_obs.lower()

            # Typické české příjmení koncovky
            valid_surname_suffixes = (
                'ová', 'á',  # ženské
                'ek', 'ák', 'ík', 'ský', 'cký', 'čák', 'ec', 'el',  # mužské
                'a',  # Svoboda, Skála, Liška
                'ý', 'í',  # přídavná jména
                # Další běžné koncovky
                'an', 'en', 'in', 'on', 'un',  # Urban, Marin, Kubín, atd.
                'eš', 'iš', 'uš', 'áš', 'íš',  # Beneš, Kříž, Lukáš, atd.
                'or', 'ar', 'ir', 'ur',  # Gregor, Kohár, atd.
                'ov', 'ev', 'av', 'iv',  # Petrov, Medveděv, atd.
                'áč', 'ič', 'oč', 'ůč',  # Horváč, Novič, atd.
                'át', 'ůt', 'ut', 'et'   # Sovát, Kůt, atd.
            )

            # Pokud příjmení nekončí na typickou koncovku → pravděpodobně není osoba
            # ALE: pokud je to jednoslabičné anglické slovo (např. "Met", "Hub"), může to být produkt/firma
            if not last_lo.endswith(valid_surname_suffixes):
                # Zkontroluj, jestli je to jednoslabičné anglické slovo (firma/produkt)
                # Např: "Met London", "Hub Team", "Pro Series"
                if len(last_obs) <= 3 or last_obs.lower() in {'hub', 'pro', 'met', 'net', 'web', 'app', 'lab', 'dev'}:
                    return match.group(0)  # Pravděpodobně firma/produkt
                # Jinak je to OK (může to být méně běžné české příjmení)

            # 7. Validace křestního jména (musí být v knihovně nebo mít typickou českou strukturu)
            first_lo = first_obs.lower()

            # Whitelist běžných českých jmen (nejsou v knihovně, ale jsou validní)
            common_czech_names = {'jan', 'petr', 'pavel', 'jiří', 'josef', 'tomáš', 'martin', 'jakub', 'david', 'daniel'}

            # Pokud křestní jméno JE v knihovně nebo v whitelistu → OK
            if first_lo in CZECH_FIRST_NAMES or first_lo in common_czech_names:
                pass  # OK
            else:
                # Není v knihovně ani v whitelistu → kontroluj strukturu

                # Pokud má méně než 3 znaky → není validní (např. "Me", "Jo")
                if len(first_obs) < 3:
                    return match.group(0)

                # Pokud má 3 znaky:
                if len(first_obs) == 3:
                    # Pokud nekončí na samohlásku ani na 'n', 'l', 'r' → zkrácený genitiv
                    # "Jan", "Dan", "Ivo" = OK
                    # "Han" (z "Hana"), "Jev" (z "Eva") = NENÍ OK
                    if not first_lo[-1] in 'aeiouyáéíóúůýnlr':
                        return match.group(0)

                # Pokud má 4-5 znaků:
                if 4 <= len(first_obs) <= 5:
                    # Pokud končí na 'k' → skoro vždy zkrácený genitiv (Elišk, Radk)
                    if first_lo[-1] == 'k':
                        return match.group(0)
                    # Pokud nekončí na samohlásku ani na typickou mužskou koncovku
                    if not first_lo[-1] in 'aeiouyáéíóúůýnlršm':
                        return match.group(0)

            # 8. Detekce rolí ("Ředitelka Centrum")
            # Pokud první slovo je role → není to osoba
            role_words = {
                'ředitelka', 'ředitel', 'jednatel', 'jednatelka',
                'manager', 'director', 'chief', 'officer',
                'specialist', 'consultant', 'coordinator',
                'developer', 'architect', 'engineer', 'analyst'
            }
            if first_obs.lower() in role_words:
                return match.group(0)  # Role, ne osoba

            # ========== C) INFERENCE KANONICKÉHO JMÉNA ==========

            # DEBUG (disabled)
            debug_jul = False

            # Nejdřív inference příjmení
            last_nom = infer_surname_nominative(last_obs)

            if debug_jul:
                print(f"    [REPLACE_PERSON] After surname inference: last_nom='{last_nom}'")

            # DŮLEŽITÉ: Oprava kanonického příjmení
            # Pokud už máme v canonical_persons nějaký tvar tohoto příjmení (např. "Procházka"),
            # použij ten existující kmen místo nového inference
            # Např: "Jakub Procházka" → canonical = "Procházka"
            #       "Petra Procházková" → canonical by měl být "Procházková" (ne "Procházek")

            # Hledej existující kmen příjmení v canonical_persons
            # ALE POUZE pokud mají STEJNÝ ROD (mužské vs ženské)
            existing_surname_stem = None

            # Nejdřív zjisti rod aktuálního příjmení
            current_is_female = last_nom.lower().endswith(('ová', 'á'))

            for p in self.canonical_persons:
                existing_last = p['last']
                if not existing_last:
                    continue

                existing_last_lo = existing_last.lower()

                # Zjisti rod existujícího příjmení
                existing_is_female = existing_last_lo.endswith(('ová', 'á'))

                # MUSÍ být stejný rod!
                if existing_is_female != current_is_female:
                    continue  # Různý rod → skip

                # Porovnej kmeny příjmení
                # Procházka vs Procházka → kmen = "Procházk" (oba mužské) ✓
                # Procházková vs Procházková → kmen = "Procházk" (obě ženské) ✓
                # Procházka vs Procházková → skip (různý rod) ✗

                # Jednoduché pravidlo: odstraň koncovky -ová, -a, -ek, -el, -ec
                # A normalizuj vložné 'e' aby Hruška a Hrušěk měly stejný kmen
                def get_stem(surname):
                    s = surname.lower()
                    if s.endswith('ová'):
                        return s[:-3]  # Procházková → Procházk
                    elif s.endswith('ěk'):
                        # Hrušěk → hruš + k = hrušk (kmen bez vložného ě)
                        return s[:-2] + 'k'
                    elif s.endswith('ek'):
                        # Hájek → háj + k = hájk (kmen bez vložného e)
                        return s[:-2] + 'k'
                    elif s.endswith('ka'):
                        # Hruška → hruš + k = hrušk (stejný kmen jako Hrušěk!)
                        # Krupička → krupič + k = krupičk (stejný kmen jako Krupičěk!)
                        return s[:-2] + 'k'
                    elif s.endswith('el'):
                        return s[:-2] + 'l'  # Havel → Havl
                    elif s.endswith('ec'):
                        return s[:-2] + 'c'  # Němec → Němc
                    elif s.endswith('a'):
                        return s[:-1]  # Procházka → Procházk (ale ne -ka!)
                    elif s.endswith('á'):
                        return s[:-1]  # Malá → Mal
                    else:
                        return s  # Novák → Novák

                existing_stem = get_stem(existing_last)
                current_stem = get_stem(last_nom)

                # Pokud kmeny se shodují A mají stejný rod → použij existující tvar
                if existing_stem == current_stem:
                    existing_surname_stem = existing_last
                    break

            # Pokud jsme našli existující kmen (STEJNÝ ROD), použij ho místo inference
            if existing_surname_stem:
                # DEBUG
                if any(name in last_obs.lower() for name in ['hofman', 'chytr']):
                    print(f"    [STEM] Using existing surname: '{existing_surname_stem}' instead of '{last_nom}'")
                last_nom = existing_surname_stem

            # Určení rodu podle příjmení
            last_lo = last_nom.lower()

            # Indeclinable surnames ending in -í/-ý/-cí can be both M/F
            # Determine gender from first name instead
            is_indeclinable = last_lo.endswith(('í', 'ý', 'cí'))
            is_female_surname = last_lo.endswith(('ová', 'á'))

            # Inference křestního jména podle rodu příjmení
            first_lo = first_obs.lower()

            # For indeclinable surnames, determine expected gender from first name
            # KRITICKÁ OPRAVA: Inferuj jméno NEJPRVE, pak check gender!
            # Artura (genitiv) → Artur (nominativ) → rod M, ne F!
            if is_indeclinable:
                # Infer nominativ first, THEN check gender
                first_nom_for_gender = infer_first_name_nominative(first_obs)
                first_gender = get_first_name_gender(first_nom_for_gender)
                is_female_surname = (first_gender == 'F')

            # Pokud příjmení je ženské, jméno musí být ženské
            if is_female_surname:
                # Han → Hana, Martin → Martina
                # Pravidlo: pokud jméno končí na souhlásku, přidej 'a'
                # Samohlásky včetně diakritiky: a, á, e, é, ě, i, í, o, ó, u, ú, ů, y, ý
                if not first_lo.endswith(('a', 'á', 'e', 'é', 'ě', 'i', 'í', 'o', 'ó', 'u', 'ú', 'ů', 'y', 'ý')):
                    # Jméno končí na souhlásku → přidej 'a'
                    first_nom = (first_obs + 'a').capitalize()
                elif first_lo.endswith('a'):
                    # Jméno už končí na 'a' → je to pravděpodobně nominativ ženského jména
                    # VÝJIMKA: Slovak varianty konvertuj na Czech
                    slovak_to_czech = {'alica': 'alice', 'lucia': 'lucie'}
                    if first_lo in slovak_to_czech:
                        first_nom = slovak_to_czech[first_lo].capitalize()
                    else:
                        first_nom = first_obs.capitalize()
                elif first_lo.endswith('u') and not first_lo.endswith('ou') and len(first_obs) > 2:
                    # KRITICKÁ OPRAVA: "Martinu" (dativ) s ženským příjmením → "Martina"
                    # Odstraň 'u', přidej 'a' (Martinu → Martin + a = Martina)
                    # POZOR: Ne pro 'ou' (instrumental), to nechť řeší inference
                    first_nom = (first_obs[:-1] + 'a').capitalize()
                else:
                    # Jiné koncovky → zkus inference
                    first_nom = infer_first_name_nominative(first_obs)
            else:
                # Příjmení je mužské, jméno musí být mužské
                # Jana → Jan, Petra → Petr, Radka → Radek (použij inference!)
                if first_lo.endswith('a') and len(first_lo) > 2:
                    # Výjimky - skutečná mužská jména končící na 'a'
                    male_names_with_a = {'kuba', 'míla', 'nikola', 'saša', 'jirka', 'honza'}
                    if first_lo in male_names_with_a:
                        first_nom = first_obs.capitalize()
                    else:
                        # Použij inference místo FORCE převodu
                        # Inference má lepší logiku pro rozlišování vzorů (Kamila vs Pavla)
                        debug_names = ['radka', 'radk', 'marka', 'mark', 'karel', 'karla', 'artur', 'viktor', 'albert']
                        if any(name in first_obs.lower() for name in debug_names):
                            print(f"    [BRANCH-1] Calling infer for male surname, first_obs='{first_obs}'")
                        first_nom = infer_first_name_nominative(first_obs)
                        if any(name in first_obs.lower() for name in debug_names):
                            print(f"    [BRANCH-1] first_nom='{first_nom}'")
                elif first_lo.endswith(('u', 'e', 'em', 'ovi', 'ům', 'y', 'í', 'ou', 'ě', 'i', 'a')):
                    # Typické pádové koncovky → použij inference
                    # Přidáno 'ě' (Zuzaně, Evě), 'i' (Pavlovi, Tomáši)
                    debug_names = ['radka', 'radk', 'marka', 'mark', 'radku']
                    if any(name in first_obs.lower() for name in debug_names):
                        print(f"    [BRANCH-2] Typical endings, first_obs='{first_obs}'")
                    first_nom = infer_first_name_nominative(first_obs)
                    if any(name in first_obs.lower() for name in debug_names):
                        print(f"    [BRANCH-2] first_nom='{first_nom}'")
                elif first_lo in CZECH_FIRST_NAMES:
                    # Jméno je v knihovně → pravděpodobně nominativ
                    # Inference funkce už sama řeší ambiguous forms (petru, davida, atd.)
                    first_nom = infer_first_name_nominative(first_obs)
                else:
                    # Není v knihovně a nemá typickou koncovku → zkus inference
                    # To zachytí Zuzan, Pavl, Radk, Hynk atd.
                    debug_names = ['radk', 'mark']
                    if any(name in first_obs.lower() for name in debug_names):
                        print(f"    [BRANCH-3] Not in library, first_obs='{first_obs}'")
                    inferred = infer_first_name_nominative(first_obs)
                    if any(name in first_obs.lower() for name in debug_names):
                        print(f"    [BRANCH-3] inferred='{inferred}'")
                    # Pokud inference vrátila stejný výsledek, použij capitalize
                    if inferred.lower() == first_lo:
                        first_nom = first_obs.capitalize()
                        if any(name in first_obs.lower() for name in debug_names):
                            print(f"    [BRANCH-3] Same result, using capitalize: '{first_nom}'")
                    else:
                        first_nom = inferred
                        if any(name in first_obs.lower() for name in debug_names):
                            print(f"    [BRANCH-3] Different, using inferred: '{first_nom}'")

            # DEBUG: Log final first_nom for jul names
            if debug_jul:
                print(f"    [REPLACE_PERSON] After first name inference: first_nom='{first_nom}'")

            # POST-PROCESSING: Oprava příjmení podle pohlaví křestního jména
            # Pokud máme ženské jméno ale mužské příjmení (nebo naopak), oprav to
            #
            # KRITICKÁ KONTROLA: Pokud OBOJÍ (jméno i příjmení) vypadají jako pády,
            # je to pravděpodobně mužská osoba v pádu (např. "Daniela Mlynáře" genitiv)
            # V takovém případě NEPROVÁDÍME post-processing
            first_looks_declined = (
                first_obs.lower() != first_nom.lower() and
                first_obs.lower().endswith(('a', 'e', 'u', 'y', 'ovi', 'em', 'i', 'ou'))
            )
            last_looks_declined = (
                last_obs.lower() != last_nom.lower() and
                last_obs.lower().endswith(('a', 'e', 'y', 'ovi', 'em', 'ou', 'ě', 'i'))
            )

            # Pokud OBOJÍ vypadají jako pády, je to pravděpodobně mužská osoba v pádu
            # Inference možná selhala, ale post-processing by to jen zhoršil
            both_declined = first_looks_declined and last_looks_declined

            # Další kontrola: Pokud first_nom končí na -a, ale first_obs také,
            # a last_obs končil na pádové koncovce, je to pravděpodobně genitiv
            # Příklad: "Daniela Mlynáře" → first_nom="Daniela", last_nom="Mlynář"
            # first_nom končí -a (vypadá žensky), ale je to genitiv od Daniel
            genitiv_pattern = (
                first_nom.lower().endswith('a') and
                first_obs.lower().endswith('a') and
                last_obs.lower().endswith(('e', 'a', 'y', 'e'))
            )

            if both_declined or genitiv_pattern:
                # Pravděpodobně mužská osoba v pádu → inference selhala
                # NEVYKONÁVEJ post-processing, použij inference znovu nebo nech tak
                # DEBUG: pro analýzu
                debug_declined = ['daniel', 'kamil', 'aleš', 'filip', 'samuel', 'stanislav',
                                'rostislav', 'bedřich', 'vít', 'štefan', 'boris', 'radomír',
                                'albín', 'jaromír', 'vladimír', 'dalimil', 'lubomír', 'jaroslav', 'bohdan',
                                'artur', 'viktor', 'albert']
                if any(name in first_nom.lower() for name in debug_declined):
                    print(f"    [POST-SKIP] Both declined: first_obs='{first_obs}', last_obs='{last_obs}'")
                    print(f"    [POST-SKIP] Inferred: first_nom='{first_nom}', last_nom='{last_nom}'")
                    print(f"    [POST-SKIP] Skipping post-processing, likely male in case")
            else:
                # Normální post-processing
                first_gender = get_first_name_gender(first_nom)
                last_is_female = last_nom.lower().endswith(('ová', 'á'))

                if first_gender == 'F' and not last_is_female:
                    # Ženské jméno, ale příjmení není ženské → přidej -ová/-á
                    last_lo = last_nom.lower()
                    if last_lo.endswith('a') and last_nom[-1] == 'a':  # končí na krátké 'a'
                        # Novotna → Novotná, Plíškova → Plíšková, Konečna → Konečná
                        last_nom = last_nom[:-1] + 'á'
                    elif last_nom.lower()[-1] in 'bcčdďfghjklmnňpqrřsštťvwxzž':
                        # Končí na souhlásku → přidej -ová
                        last_nom = last_nom + 'ová'
                elif first_gender == 'M' and last_is_female:
                    # Mužské jméno, ale příjmení je ženské → odstraň -ová/-á
                    last_lo = last_nom.lower()
                    if last_lo.endswith('ová'):
                        # Jeřábková → Jeřábek (s vložným 'e')
                        base = last_nom[:-3]  # Odstraň "ová"
                        # Zkontroluj jestli potřebuje vložné 'e'
                        if len(base) >= 2 and base[-1].lower() in 'kbc':
                            prev = base[-2].lower() if len(base) >= 2 else ''
                            if prev in 'bcdfghjklmnpqrstvwxzž':
                                # Přidej vložné 'e' před poslední souhláskou
                                soft = base[-1].lower() in 'čšžřcj'
                                e_char = 'ě' if soft else 'e'
                                last_nom = base[:-1] + e_char + base[-1]
                            else:
                                last_nom = base
                        else:
                            last_nom = base
                    elif last_lo.endswith('á'):
                        # Malá → Malý, Nová → Nový
                        last_nom = last_nom[:-1] + 'ý'

            # DEBUG: Log final values before tag creation for jul names
            if debug_jul:
                print(f"    [REPLACE_PERSON] FINAL (before _ensure_person_tag): first_nom='{first_nom}', last_nom='{last_nom}'")

            # Vytvoř nebo najdi tag pro tuto osobu
            tag = self._ensure_person_tag(first_nom, last_nom)

            # Ulož původní formu jako variantu (pokud je jiná než kanonická)
            original_form = f"{first_obs} {last_obs}"
            canonical = f"{first_nom} {last_nom}"
            if original_form.lower() != canonical.lower():
                # Kontrola shody rodu před uložením varianty
                gender = get_first_name_gender(first_nom)
                if is_valid_surname_variant(last_obs, last_nom, gender):
                    self.entity_map['PERSON'][canonical].add(original_form)

            return tag

        # ITERATIVNÍ zpracování místo batch sub()
        # Důvod: Když odstavec obsahuje více pádů stejné osoby (např. "Radek Hofman - pro Radka Hofmana"),
        # musíme je zpracovat postupně, aby druhý match viděl už vytvořený PERSON_63
        offset = 0
        result_text = text
        matches_list = list(person_pattern.finditer(text))

        # DEBUG pro Radek/Marek
        debug_names = ['radek', 'radk', 'marek', 'mark']
        if any(name in text.lower() for name in debug_names):
            print(f"\n[DEBUG] Processing text with {len(matches_list)} person matches")
            for idx, m in enumerate(matches_list):
                if any(name in m.group(0).lower() for name in debug_names):
                    print(f"  Match {idx}: '{m.group(0)}'")

        for match in matches_list:
            # Přepočítej pozici s offsetem (text se mění při nahrazování)
            start = match.start() + offset
            end = match.end() + offset

            # Zavolej replace_person s aktuálním matchem
            replacement = replace_person(match)

            # DEBUG
            if any(name in match.group(0).lower() for name in debug_names):
                print(f"    -> {replacement} (person_index size: {len(self.person_index)})")

            # Nahraď text
            result_text = result_text[:start] + replacement + result_text[end:]

            # Update offset pro další matche
            offset += len(replacement) - (end - start)

        return result_text

    def anonymize_entities(self, text: str) -> str:
        """Anonymizuje všechny entity (adresy, kontakty, IČO, atd.)."""

        # DŮLEŽITÉ: Pořadí je klíčové! Od nejvíce specifických po nejméně specifické
        # KRITICKÉ: Credentials (hesla, API klíče) PRVNÍ s store_value=False!

        # 1. CREDENTIALS (username / password) - NEJPRVE!
        def replace_credentials(match):
            username = match.group(2)
            password = match.group(3)
            username_tag = self._get_or_create_label('USERNAME', username)
            # TEST MODE: store_value=True (ukládá plnou hodnotu)
            password_tag = self._get_or_create_label('PASSWORD', password, store_value=True)
            return f"{match.group(1)}: {username_tag} / {password_tag}"
        text = CREDENTIALS_RE.sub(replace_credentials, text)

        # 2. HESLA (TEST MODE: store_value=True)
        def replace_password(match):
            return self._get_or_create_label('PASSWORD', match.group(1), store_value=True)
        text = PASSWORD_RE.sub(replace_password, text)

        # 2. API KLÍČE, SECRETS (TEST MODE: store_value=True)
        def replace_api_key(match):
            return self._get_or_create_label('API_KEY', match.group(1), store_value=True)
        text = API_KEY_RE.sub(replace_api_key, text)

        def replace_secret(match):
            return self._get_or_create_label('SECRET', match.group(1), store_value=True)
        text = SECRET_RE.sub(replace_secret, text)

        # 3. SSH KLÍČE (TEST MODE: store_value=True)
        def replace_ssh_key(match):
            return self._get_or_create_label('SSH_KEY', match.group(1), store_value=True)
        text = SSH_KEY_RE.sub(replace_ssh_key, text)

        # 3.5. IBAN (PŘED kartami! IBAN má dlouhé číselné sekvence)
        # TEST MODE: store_value=True (ukládá plnou hodnotu)
        def replace_iban(match):
            return self._get_or_create_label('IBAN', match.group(1), store_value=True)
        text = IBAN_RE.sub(replace_iban, text)

        # 4. PLATEBNÍ KARTY (TEST MODE: store_value=True)
        def replace_card(match):
            # CARD_RE má 1 capture group
            card = match.group(1)
            if card:
                return self._get_or_create_label('CARD', card, store_value=True)
            return match.group(0)
        text = CARD_RE.sub(replace_card, text)

        # 5. USERNAMES, ACCOUNTS, HOSTNAMES
        def replace_username(match):
            return self._get_or_create_label('USERNAME', match.group(1))
        text = USERNAME_RE.sub(replace_username, text)

        def replace_account_id(match):
            return self._get_or_create_label('ACCOUNT_ID', match.group(1))
        text = ACCOUNT_ID_RE.sub(replace_account_id, text)

        def replace_hostname(match):
            return self._get_or_create_label('HOST', match.group(1))
        text = HOSTNAME_RE.sub(replace_hostname, text)

        # 6. IP ADRESY
        def replace_ip(match):
            return self._get_or_create_label('IP', match.group(1))
        text = IP_RE.sub(replace_ip, text)

        # 7. ČÍSLA POJIŠTĚNCE
        def replace_insurance_id(match):
            return self._get_or_create_label('INSURANCE_ID', match.group(1))
        text = INSURANCE_ID_RE.sub(replace_insurance_id, text)

        # 8. RFID/BADGE
        def replace_rfid(match):
            return self._get_or_create_label('RFID', match.group(1))
        text = RFID_RE.sub(replace_rfid, text)

        # 8.1. SOCIÁLNÍ SÍTĚ (KRITICKÉ - PII)
        def replace_linkedin(match):
            return self._get_or_create_label('LINKEDIN', match.group(1))
        text = LINKEDIN_RE.sub(replace_linkedin, text)

        def replace_facebook(match):
            return self._get_or_create_label('FACEBOOK', match.group(1))
        text = FACEBOOK_RE.sub(replace_facebook, text)

        def replace_instagram(match):
            # Instagram má 2 capture groups - handle nebo URL
            handle = match.group(1) if match.group(1) else match.group(2)
            return self._get_or_create_label('INSTAGRAM', handle)
        text = INSTAGRAM_RE.sub(replace_instagram, text)

        def replace_skype(match):
            return self._get_or_create_label('SKYPE', match.group(1))
        text = SKYPE_RE.sub(replace_skype, text)

        # 8.2. BIOMETRICKÉ IDENTIFIKÁTORY (KRITICKÉ - GDPR Článek 9)
        def replace_voice_id(match):
            return self._get_or_create_label('VOICE_ID', match.group(1))
        text = VOICE_ID_RE.sub(replace_voice_id, text)

        def replace_bio_hash(match):
            # BIO_HASH_RE má 2 capture groups
            bio_hash = match.group(1) if match.group(1) else match.group(2)
            return self._get_or_create_label('BIO_HASH', bio_hash)
        text = BIO_HASH_RE.sub(replace_bio_hash, text)

        def replace_photo_id(match):
            # Photo ID má 3 capture groups
            photo_id = match.group(1) if match.group(1) else (match.group(2) if match.group(2) else match.group(3))
            return self._get_or_create_label('PHOTO_ID', photo_id)
        text = PHOTO_ID_RE.sub(replace_photo_id, text)

        def replace_api_key_enhanced(match):
            return self._get_or_create_label('API_KEY', match.group(1))
        text = API_KEY_ENHANCED_RE.sub(replace_api_key_enhanced, text)

        # 9. ADRESY (před jmény, aby "Novákova 45" nebylo osobou)
        def replace_address(match):
            return self._get_or_create_label('ADDRESS', match.group(0))
        text = ADDRESS_RE.sub(replace_address, text)

        # 10. EMAILY (před ostatními, protože obsahují speciální znaky)
        def replace_email(match):
            return self._get_or_create_label('EMAIL', match.group(1))
        text = EMAIL_RE.sub(replace_email, text)

        # 11. DATUM NAROZENÍ (před BIRTH_ID a všemi daty)
        def replace_dob(match):
            return self._get_or_create_label('DATE', match.group(1))
        text = DOB_RE.sub(replace_dob, text)

        # 12. RODNÁ ČÍSLA (PŘED BANK! Jinak "Rodné číslo: 850123/1234" by se rozpadlo)
        # KRITICKÁ PRIORITA: Silný kontext ("Rodné číslo:") má přednost před bank účty
        def replace_birth_id(match):
            birth_id = match.group(1) if match.group(1) else match.group(2)
            if birth_id:
                # Odstranit lomítko pokud není přítomné
                birth_id_clean = birth_id.replace(' ', '')
                return self._get_or_create_label('BIRTH_ID', birth_id_clean)
            return match.group(0)
        text = BIRTH_ID_RE.sub(replace_birth_id, text)

        # 13. BANKOVNÍ ÚČTY (po BIRTH_ID, aby RČ nebylo zachyceno jako účet)
        # DŮLEŽITÉ: Kód banky musí být součástí tagu (BANK_RE ho zachytí pokud je přítomen)
        def replace_bank(match):
            # BANK_RE má 3 capture groups - získej první non-None
            account = match.group(1) or match.group(2) or match.group(3)
            if account:
                # TEST MODE: store_value=True (ukládá plnou hodnotu)
                return self._get_or_create_label('BANK', account, store_value=True)
            return match.group(0)
        text = BANK_RE.sub(replace_bank, text)

        # 14. ČÍSLA OP (KRITICKÉ: MUSÍ být PŘED telefony!)
        def replace_id_card(match):
            id_card = match.group(1) if match.group(1) else match.group(2)
            if id_card:
                return self._get_or_create_label('ID_CARD', id_card)
            return match.group(0)
        text = ID_CARD_RE.sub(replace_id_card, text)

        # 14.5. VARIABILNÍ SYMBOL (PŘED telefony! VS čísla nejsou telefony)

        # 14.6. KONSTANTNÍ SYMBOL

        # 14.7. SPECIFICKÝ SYMBOL

        # 14.8. ČÍSLO LÉKAŘE / LICENSE ID

        # 14.9. ČÍSLO JEDNACÍ / CASE ID

        # 14.10. SPISOVÁ ZNAČKA SOUDU

        # 14.11. ČÍSLO POJISTNÉ SMLOUVY

        # 14.12. ČÍSLO SMLOUVY (generické)

        # 15. TELEFONY (po ID_CARD a VS, ale PŘED částkami!)
        def replace_phone(match):
            # PHONE_RE má capture group (1) pro samotné číslo (bez prefixu!)
            return self._get_or_create_label('PHONE', match.group(1))
        text = PHONE_RE.sub(replace_phone, text)

        # 16. DIČ (před IČO)
        def replace_dic(match):
            return self._get_or_create_label('DIC', match.group(1))
        text = DIC_RE.sub(replace_dic, text)

        # 16.5. GENETICKÉ IDENTIFIKÁTORY (PŘED IČO! rs... nejsou IČO)
        def replace_genetic_id(match):
            return self._get_or_create_label('GENETIC_ID', match.group(1))
        text = GENETIC_ID_RE.sub(replace_genetic_id, text)

        # 16.6. DATUM NAROZENÍ
        def replace_birth_date(match):
            return self._get_or_create_label('BIRTH_DATE', match.group(1))
        text = BIRTH_DATE_RE.sub(replace_birth_date, text)

        # 16.7. ČÍSLO PASU
        def replace_passport(match):
            return self._get_or_create_label('PASSPORT', match.group(1))
        text = PASSPORT_RE.sub(replace_passport, text)

        # 16.8. ŘIDIČSKÝ PRŮKAZ
        def replace_driver_license(match):
            return self._get_or_create_label('DRIVER_LICENSE', match.group(1))
        text = DRIVER_LICENSE_RE.sub(replace_driver_license, text)

        # 16.9. BENEFITNÍ KARTY (MultiSport, Sodexo) - PII!
        def replace_benefit_card(match):
            card_id = match.group(1) if match.group(1) else match.group(2)
            if card_id:
                return self._get_or_create_label('BENEFIT_CARD', card_id)
            return match.group(0)
        text = BENEFIT_CARD_RE.sub(replace_benefit_card, text)

        # 17. IČO
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

        # 18. SPZ / License Plates
        def replace_license_plate(match):
            # LICENSE_PLATE_RE má capture group (1) pro celou SPZ
            plate = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)

            # Filtruj false positives
            # Nesmí být jen číslice (789456, 456789)
            if plate.replace(' ', '').isdigit():
                return match.group(0)

            # Nesmí začínat "EU " (EU 2016)
            if plate.upper().startswith('EU '):
                return match.group(0)

            # Kontrola kontextu - nesmí být po "od", "z", "do", "roku"
            start_pos = match.start()
            context_before = text[max(0, start_pos-10):start_pos].lower()
            if any(word in context_before for word in ['od ', 'z ', 'do ', 'roku ']):
                return match.group(0)

            return self._get_or_create_label('LICENSE_PLATE', plate)
        text = LICENSE_PLATE_RE.sub(replace_license_plate, text)

        # 18.1. VIN (Vehicle Identification Number)
        def replace_vin(match):
            vin = match.group(1) if match.group(1) else match.group(2)
            if vin:
                return self._get_or_create_label('VIN', vin)
            return match.group(0)
        text = VIN_RE.sub(replace_vin, text)

        # 18.2. MAC ADRESA
        def replace_mac(match):
            mac = match.group(1) or match.group(2) or match.group(3)
            if mac:
                return self._get_or_create_label('MAC', mac)
            return match.group(0)
        text = MAC_RE.sub(replace_mac, text)

        # 18.3. IMEI (International Mobile Equipment Identity)
        def replace_imei(match):
            imei = match.group(1) if match.group(1) else match.group(2)
            if imei:
                return self._get_or_create_label('IMEI', imei)
            return match.group(0)
        text = IMEI_RE.sub(replace_imei, text)

        # 19. ČÁSTKY (AŽ NAKONEC! Po telefonech a všech číselných identifikátorech)

        # 20. MASKOVÁNÍ CVV/EXPIRACE u karet
        # Nahradí "CVV: 123" → "CVV: ***" a "exp: 12/26" → "exp: **/**"
        text = re.sub(r'(CVV|CVC)\s*:\s*\d{3,4}', r'\1: ***', text, flags=re.IGNORECASE)
        text = re.sub(r'exp(?:\.|\s+|iration)?\s*:?\s*\d{2}/\d{2,4}', r'exp: **/**', text, flags=re.IGNORECASE)

        # 20.5. CLEANUP biometrických identifikátorů - odstraň [[PHONE_*]] z bio prefixů
        # "IRIS_SCAN_PD_[[PHONE_10]]" → "IRIS_SCAN_PD_10"
        # "VOICE_RK_[[PHONE_11]]" → "VOICE_RK_11"
        text = re.sub(
            r'(IRIS_SCAN|VOICE_RK|HASH_BIO|FINGERPRINT|FACIAL|RETINA|PALM|DNA)_([A-Z0-9_]*)\[\[PHONE_(\d+)\]\]',
            r'\1_\2\3',
            text
        )

        # 20.6. BANK FRAGMENTS - zachyť fragmenty účtů s vloženým [[BIRTH_ID_*]]
        # "1928[[BIRTH_ID_6]]" → "[[BANK_x]]"
        # "Číslo účtu: 6677[[BIRTH_ID_21]]" → "Číslo účtu: [[BANK_x]]"
        def replace_bank_fragment(match):
            # Celý fragment (čísla před + [[BIRTH_ID_*]] + čísla po) → [[BANK_*]]
            # TEST MODE: store_value=True
            return self._get_or_create_label('BANK', match.group(1), store_value=True)

        # Pattern: číslice (volitelně) + [[BIRTH_ID_*]] + číslice (volitelně) v kontextu "účt"
        bank_fragment_pattern = re.compile(
            r'(?:číslo\s+účtu|účet|účtu|platba\s+na\s+účet|bankovní\s+účet)\s*:?\s*(\d{0,10}\[\[BIRTH_ID_\d+\]\]\d{0,10})',
            re.IGNORECASE
        )
        text = bank_fragment_pattern.sub(replace_bank_fragment, text)

        # 21. END-SCAN - finální kontrola citlivých dat (chytá zbytky nalepené na ]])
        text = self._end_scan(text)

        return text

    def _luhn_check(self, card_number: str) -> bool:
        """Validace Luhn algoritmem pro platební karty."""
        digits = [int(d) for d in card_number if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False

        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit

        return checksum % 10 == 0

    def _end_scan(self, text: str) -> str:
        """Finální sken po všech náhradách - chytá případné zbytky citlivých dat."""

        # LUHN END-SCAN - zachytí všechny Luhn-validní karty (13-19 číslic)
        luhn_pattern = re.compile(r'\b(\d[\s\-]?){12,18}\d\b')
        def final_luhn_card(match):
            candidate = match.group(0)
            # Přeskoč pokud už je v [[CARD_*]]
            if '[[CARD_' in text[max(0, match.start()-10):match.end()+10]:
                return match.group(0)
            # Validuj Luhn
            if self._luhn_check(candidate):
                # TEST MODE: store_value=True
                return self._get_or_create_label('CARD', candidate, store_value=True)
            return match.group(0)
        text = luhn_pattern.sub(final_luhn_card, text)

        # IBAN (pokud unikl) - TEST MODE
        def final_iban(match):
            if not '[[IBAN_' in text[max(0, match.start()-10):match.start()+30]:
                return self._get_or_create_label('IBAN', match.group(1), store_value=True)
            return match.group(0)
        text = IBAN_RE.sub(final_iban, text)

        # Platební karty (pokud unikly nebo mají CVV/exp. datum) - TEST MODE
        def final_card(match):
            card = match.group(1) if match.group(1) else match.group(2)
            if card and not '[[CARD_' in text[max(0, match.start()-10):match.start()+len(card)+10]:
                return self._get_or_create_label('CARD', card, store_value=True)
            return match.group(0)
        text = CARD_RE.sub(final_card, text)

        # Hesla (pokud unikla nebo jsou nalepená na jiných entitách) - TEST MODE
        def final_password(match):
            return self._get_or_create_label('PASSWORD', match.group(1), store_value=True)
        text = PASSWORD_RE.sub(final_password, text)

        # IP adresy (pokud unikly)
        def final_ip(match):
            # Přeskoč pokud už je součástí URL/hostname
            if not re.search(r'[a-z]', text[max(0, match.start()-10):match.start()], re.IGNORECASE):
                return self._get_or_create_label('IP', match.group(1))
            return match.group(0)
        text = IP_RE.sub(final_ip, text)

        # Usernames (pokud unikly)
        def final_username(match):
            return self._get_or_create_label('USERNAME', match.group(1))
        text = USERNAME_RE.sub(final_username, text)

        # API klíče, secrets (pokud unikly) - TEST MODE
        def final_api(match):
            return self._get_or_create_label('API_KEY', match.group(1), store_value=True)
        text = API_KEY_RE.sub(final_api, text)

        def final_secret(match):
            return self._get_or_create_label('SECRET', match.group(1), store_value=True)
        text = SECRET_RE.sub(final_secret, text)

        # Pojištěnce (pokud unikla)
        def final_insurance(match):
            return self._get_or_create_label('INSURANCE_ID', match.group(1))
        text = INSURANCE_ID_RE.sub(final_insurance, text)

        # RFID (pokud uniklo)
        def final_rfid(match):
            return self._get_or_create_label('RFID', match.group(1))
        text = RFID_RE.sub(final_rfid, text)

        # POST-PASS: Karty v kontextu "Číslo:" které unikly hlavnímu CARD_RE
        # Hledáme specificky "Číslo: 4532..." v blízkosti slov karta/card/platební
        card_context_pattern = re.compile(
            r'(?:platební\s+karta|karta|card)[\s\S]{0,100}?'  # Lookforward pro kontext
            r'Číslo\s*:\s*'
            r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{1,3})?)',  # 16-19 číslic
            re.IGNORECASE
        )

        def replace_card_context(match):
            card = match.group(1)
            # Check if already tagged
            if f"[[CARD_" not in text[max(0, match.start()-20):min(len(text), match.end()+20)]:
                return match.group(0).replace(card, self._get_or_create_label('CARD', card, store_value=True))
            return match.group(0)

        text = card_context_pattern.sub(replace_card_context, text)

        # POST-PASS: ALL_CAPS jména bez diakritiky (ALENA DVORAKOVA)
        # Najdi známé osoby a nahraď jejich ALL_CAPS varianty bez diakritiky
        for p in self.canonical_persons:
            # Vytvoř ALL_CAPS verzi bez diakritiky
            import unicodedata
            def remove_dia(s):
                nfd = unicodedata.normalize('NFD', s)
                return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

            if p['first'] and p['last']:
                first_caps = remove_dia(p['first']).upper()
                last_caps = remove_dia(p['last']).upper()
                # Nahraď pokud nalezeno
                pattern = rf'\b{re.escape(first_caps)}\s+{re.escape(last_caps)}\b'
                text = re.sub(pattern, p['tag'], text)

        # POST-PASS: Místo narození
        birth_place_pattern = re.compile(
            r'(Místo\s+narození\s*:)\s*([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)',
            re.IGNORECASE
        )
        def replace_birth_place(match):
            prefix = match.group(1)
            place = match.group(2)
            # Simple tag - don't reuse ADDRESS tags
            tag = self._get_or_create_label('BIRTH_PLACE', place)
            return f"{prefix} {tag}"
        text = birth_place_pattern.sub(replace_birth_place, text)

        # POST-PASS: Jednoduché adresy (ulice číslo, město) které unikly ADDRESS_RE
        # Pattern: Ulice 123/45, Praha 3  (bez PSČ nebo kontextu)
        simple_addr_pattern = re.compile(
            r'\b([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)?)\s+'  # Ulice (1-2 slova)
            r'(\d+(?:/\d+)?)\s*,\s*'  # Číslo
            r'(Praha\s+\d+|Brno|Ostrava|Plzeň)',  # Město
            re.IGNORECASE
        )
        def replace_simple_addr(match):
            addr = match.group(0)
            # Přeskoč pokud už je tagovaná
            if '[[ADDRESS_' not in text[max(0, match.start()-10):min(len(text), match.end()+10)]:
                return self._get_or_create_label('ADDRESS', addr)
            return addr
        text = simple_addr_pattern.sub(replace_simple_addr, text)

        # POST-PASS: Adresy - nahraď všechny výskyty známých adres (i bez PSČ)
        # Projdi všechny adresy v entity_map a nahraď všechny jejich částečné výskyty
        if 'ADDRESS' in self.entity_map:
            for addr_key in self.entity_map['ADDRESS'].keys():
                # Získej tag
                if addr_key in self.entity_index_cache.get('ADDRESS', {}):
                    idx = self.entity_index_cache['ADDRESS'][addr_key]
                    tag = f"[[ADDRESS_{idx}]]"

                    # Generuj varianty: bez PSČ, bez čárek, atd.
                    # Např. "Karlovo náměstí 12/34, 120 00 Praha 2" → "Karlovo náměstí 12/34, Praha 2"
                    # Odstran PSČ pattern: \d{3}\s?\d{2}
                    addr_no_psc = re.sub(r',?\s*\d{3}\s?\d{2}\s*', ', ', addr_key).strip(', ')

                    # Nahraď varianty (ale pouze pokud nejsou už tagované)
                    for variant in [addr_key, addr_no_psc]:
                        if variant and len(variant) > 15:  # Min. délka
                            # Najdi a nahraď všechny výskyty kromě již tagovaných
                            if variant in text:
                                # Split by variant
                                parts = text.split(variant)
                                if len(parts) > 1:
                                    # Nahraď pouze pokud kolem není tag
                                    new_parts = []
                                    for i, part in enumerate(parts[:-1]):
                                        new_parts.append(part)
                                        # Check if not already tagged (look at end of previous part and start of next)
                                        if not (part.endswith('[[') or parts[i+1].startswith(']]')):
                                            new_parts.append(tag)
                                        else:
                                            new_parts.append(variant)  # Keep original if tagged
                                    new_parts.append(parts[-1])
                                    text = ''.join(new_parts)

        return text

    def anonymize_docx(self, input_path: str, output_path: str, json_map: str, txt_map: str):
        """Hlavní metoda pro anonymizaci DOCX dokumentu."""
        print(f"\n🔍 Zpracovávám: {Path(input_path).name}")

        # Načti dokument
        import time
        start_time = time.time()
        doc = Document(input_path)
        print(f"  [DEBUG] Document loaded in {time.time() - start_time:.1f}s")

        # Zpracuj všechny odstavce
        start_time = time.time()
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

        print(f"  [DEBUG] Paragraphs processed in {time.time() - start_time:.1f}s")

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
        start_time = time.time()
        doc.save(output_path)
        print(f"  [DEBUG] Document saved in {time.time() - start_time:.1f}s")

        # Vytvoř mapy (předej doc a path aby se nečetl znovu)
        start_time = time.time()
        self._create_maps(json_map, txt_map, input_path, doc)
        print(f"  [DEBUG] Maps created in {time.time() - start_time:.1f}s")

        print(f"✅ Hotovo! Nalezeno {len(self.canonical_persons)} osob")

    def _create_maps(self, json_path: str, txt_path: str, source_file: str, doc=None):
        """Vytvoří JSON a TXT mapy náhrad."""

        # Cleanup nepoužitých tagů před vytvořením map
        # Použij předaný dokument nebo načti z disku
        if doc is None:
            from docx import Document
            doc = Document(txt_path.replace('_map.txt', '_anon.docx'))

        anon_text = "\n".join([p.text for p in doc.paragraphs])
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    anon_text += "\n".join([p.text for p in cell.paragraphs])

        # SKIP cleanup - not needed in TEST MODE and causes issues with index mapping
        # Všechny entity zůstanou v mapě i když nejsou použity v textu

        # JSON mapa
        json_data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "source_file": Path(source_file).name,
            "entities": []
        }

        # Osoby
        for p in self.canonical_persons:
            canonical_full = f'{p["first"]} {p["last"]}'
            json_data["entities"].append({
                "type": "PERSON",
                "label": p['tag'],
                "original": canonical_full,
                "occurrences": 1
            })

        # Ostatní entity (kromě PERSON, který už je v canonical_persons)
        for typ, entities in self.entity_map.items():
            if typ == 'PERSON':
                continue  # Skip PERSON - already handled in canonical_persons
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
                f.write("-----\n")
                for p in self.canonical_persons:
                    canonical_full = f'{p["first"]} {p["last"]}'
                    f.write(f"{p['tag']}: {canonical_full}\n")

                    # Vypsat všechny nalezené varianty této osoby
                    if canonical_full in self.entity_map['PERSON']:
                        variants = self.entity_map['PERSON'][canonical_full]
                        # Vypsat pouze varianty odlišné od kanonického tvaru
                        for variant in sorted(variants):
                            if variant.lower() != canonical_full.lower():
                                f.write(f"  - {variant}\n")
                f.write("\n")

            # Ostatní entity (kromě PERSON, který už je v OSOBY)
            for typ, entities in sorted(self.entity_map.items()):
                if typ == 'PERSON':
                    continue  # Skip PERSON - already handled in OSOBY section
                if entities:
                    f.write(f"{typ}\n")
                    f.write("-" * len(typ) + "\n")  # Přidán oddělovač
                    for idx, (original, variants) in enumerate(entities.items(), 1):
                        label = f"[[{typ}_{idx}]]"
                        # Pro citlivá data zobraz jen ***REDACTED*** bez čísla
                        display_value = "***REDACTED***" if original.startswith("***REDACTED_") else original
                        f.write(f"{label}: {display_value}\n")
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