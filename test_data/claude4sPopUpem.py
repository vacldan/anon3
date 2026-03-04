# -*- coding: utf-8 -*-
"""
Czech DOCX Anonymizer – v7.2
- Opravená detekce - adresy se zpracují první
- Lepší detekce skloňovaných tvarů
- Rozšířený blacklist pro části adres
"""

import sys, re, json, unicodedata
from typing import Optional, Set, List, Tuple
from pathlib import Path
from collections import defaultdict, OrderedDict
from docx import Document
import tkinter as tk
from tkinter import messagebox

# =============== Utility ===============
INVISIBLE = '\u00ad\u200b\u200c\u200d\u2060\ufeff'

def clean_invisibles(text: str) -> str:
    if not text: return ''
    text = text.replace('\u00a0', ' ')
    return re.sub('['+re.escape(INVISIBLE)+']', '', text)

def normalize_for_matching(text: str) -> str:
    if not text: return ""
    n = unicodedata.normalize('NFD', text)
    no_diac = ''.join(c for c in n if not unicodedata.combining(c))
    return re.sub(r'[^A-Za-z]', '', no_diac).lower()

def iter_paragraphs(doc: Document):
    for p in doc.paragraphs:
        yield p
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    yield p

def get_text(p) -> str:
    return ''.join(r.text or '' for r in p.runs) or p.text or ''

def set_text(p, s: str):
    if p.runs:
        p.runs[0].text = s
        for r in p.runs[1:]: r.text = ''
    else:
        p.text = s

def preserve_case(surface: str, tag: str) -> str:
    if surface.isupper(): return tag.upper()
    if surface.istitle(): return tag
    return tag

# =============== Načtení knihovny jmen ===============
def load_names_library(json_path: str = "cz_names.v1.json") -> Set[str]:
    try:
        script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        json_file = script_dir / json_path
        
        if not json_file.exists():
            print(f"⚠️  Varování: {json_path} nenalezen!")
            return set()
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        names = set()
        if 'firstnames_no_diac' in data:
            names.update(data['firstnames_no_diac'].get('M', []))
            names.update(data['firstnames_no_diac'].get('F', []))
        
        print(f"✔ Načteno {len(names)} jmen z knihovny")
        return names
        
    except Exception as e:
        print(f"⚠️  Chyba při načítání: {e}")
        return set()

CZECH_FIRST_NAMES = load_names_library()

# =============== Rozšířené Blacklisty ===============
ADDRESS_PARTS = {
    'ulice', 'náměstí', 'třída', 'nábřeží', 'sady', 'alej', 'cesta',
    'pod', 'nad', 'před', 'mezi', 'horní', 'dolní', 'malá', 'velká',
    'nová', 'stará', 'severní', 'jižní', 'východní', 'západní',
    'budějovice', 'české', 'hradec', 'králové', 'brno', 'praha',
    'ostrava', 'plzeň', 'liberec', 'olomouc', 'pardubice', 'zlín',
    'ústí', 'labem', 'jihlava', 'havířov', 'kladno', 'most', 'opava',
    'frýdek', 'místek', 'karviná', 'děčín', 'teplice', 'chomutov',
    'přerov', 'jablonec', 'mladá', 'boleslav', 'prostějov',
    'třebíč', 'šumperk', 'studánky', 'hrázi', 'skalkou', 'lesu',
    'družstevní', 'školní', 'zahradní', 'polní', 'lesní', 'luční',
    'květná', 'růžová', 'lipová', 'březová', 'dubová', 'smrková'
}

SURNAME_BLACKLIST = {
    'smlouva','smlouvě','smlouvy','smlouvou','článek','článku','články',
    'datum','číslo','adresa','bydliště','průkaz','občanský','rodné','zákon','sb','kč','čr',
    'ustanovení','příloha','titul','oddíl','bod','pověřený','zástupce','nájem','pronájem',
    'byt','nájemci','nájemce','pronajímatel','pronajímateli',
    'užívat','hlásit','nepřenechávat','elektřina','plyn','sconto','bolton','předat','předání',
    'cena','kauce','záloha','platba','sankce','odpovědnost','poškození','opravy','závady',
    'přepis','přepisem','vyúčtování','paušálně','roční','měsíční'
}

ROLE_STOP = {
    'pronajímatel','nájemce','dlužník','věřitel','objednatel','zhotovitel',
    'zaměstnanec','zaměstnavatel','ručitel','spoludlužník','jednatel','svědek',
    'statutární','zástupce','pojistník','pojištěný','odesílatel','příjemce'
}

# =============== Validace jmen z knihovny ===============
def is_valid_firstname_or_variant(name: str) -> Tuple[bool, Optional[str]]:
    """Kontroluje, zda je jméno nebo jeho varianta v knihovně, vrací (je_validní, nominativ)"""
    if not name:
        return False, None
    
    norm = normalize_for_matching(name)
    
    # Přímá shoda
    if norm in CZECH_FIRST_NAMES:
        return True, name
    
    # Genitiv mužských jmen (Lukáše -> Lukáš)
    if name.lower().endswith('e') and len(name) > 2:
        # Odstranit -e a zkusit najít
        cand = name[:-1]
        if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return True, cand
        # Může být také genitiv od jména končícího na -ek/-ík
        if name.lower().endswith('ka'):
            cand = name[:-2] + 'ek'
            if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
                return True, cand
    
    # Genitiv typu Tomáše -> Tomáš
    if name.lower().endswith('še') and len(name) > 3:
        cand = name[:-2] + 'š'
        if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return True, cand
    
    # Ženská jména
    if name.lower().endswith('y') and len(name) > 2:
        cand = name[:-1] + 'a'
        if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return True, cand
    
    if name.lower().endswith('ou') and len(name) > 3:
        cand = name[:-2] + 'a'
        if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return True, cand
    
    # Mužská jména - dativ/lokál
    if name.lower().endswith('ovi') and len(name) > 4:
        cand = name[:-3]
        if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return True, cand
    
    if name.lower().endswith('u') and len(name) > 2:
        cand = name[:-1]
        if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return True, cand
    
    if name.lower().endswith('em') and len(name) > 3:
        cand = name[:-2]
        if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return True, cand
    
    # Speciální případy
    if name.lower().endswith('la') and len(name) > 3:
        cand = name[:-2] + 'el'
        if normalize_for_matching(cand) in CZECH_FIRST_NAMES:
            return True, cand
    
    return False, None

def is_address_part(word: str) -> bool:
    """Kontroluje, zda je slovo typická část adresy"""
    return normalize_for_matching(word) in ADDRESS_PARTS

# =============== Inference nominativu ===============
def infer_surname_nominative(observed: str) -> str:
    """Inferuje nominativ příjmení"""
    if not observed: return observed
    obs = observed.strip()
    low = obs.lower()

    # Ženská příjmení
    if low.endswith('ové') and len(obs) > 4: 
        return obs[:-3] + 'á'
    if low.endswith('ovou') and len(obs) > 4: 
        return obs[:-4] + 'ová'
    if low.endswith('é') and len(obs) > 2: 
        return obs[:-1] + 'á'
    if low.endswith('ou') and not low.endswith('ovou') and len(obs) > 2:
        return obs[:-2] + 'á'
    
    # Mužská příjmení
    if low.endswith('ovi') and len(obs) > 4: 
        return obs[:-3] + 'a'
    
    # Genitiv typu Marečka -> Mareček
    if low.endswith('ka') and not low.endswith('nka') and len(obs) > 3:
        # Může být Mareček v genitivu
        cand = obs[:-1]  # Marečk -> nepomůže
        # Zkusit přidat -ek
        if low.endswith('čka'):
            return obs[:-2] + 'ek'
        if low.endswith('ška'):
            return obs[:-2] + 'ek'
    
    for suf in ('em','e','u'):
        if low.endswith(suf) and len(obs) > len(suf)+1:
            return obs[:-len(suf)] + 'a'
    
    return obs

# =============== Varianty pro nahrazování ===============
def variants_for_first(first: str) -> set:
    """Generuje všechny možné tvary křestního jména"""
    f = first.strip()
    if not f: return {''}
    V = {f, f.lower(), f.capitalize()}
    low = f.lower()
    
    # Ženská jména
    if low.endswith('a'):
        stem = f[:-1]
        V |= {stem+'y', stem+'e', stem+'ě', stem+'u', stem+'ou', stem+'o'}
    else:
        # Mužská jména
        V |= {f+'a', f+'ovi', f+'e', f+'em', f+'u', f+'om'}
        # Genitiv může být také jméno+e (Lukáš -> Lukáše)
        if low.endswith('š'):
            V.add(f+'e')
        if low.endswith('s'):
            V.add(f[:-1]+'še')
        if low.endswith('ek'): 
            V.add(f[:-2] + 'ka')
        if low.endswith('el'): 
            V.add(f[:-2] + 'la')
    
    return V

def variants_for_surname(surname: str) -> set:
    """Generuje všechny možné tvary příjmení"""
    s = surname.strip()
    if not s: return {''}
    out = {s, s.lower(), s.capitalize()}
    low = s.lower()

    if low.endswith('ová'):
        base = s[:-1]
        out |= {s, base+'é', base+'ou'}
        return out
    
    if low.endswith('á'):
        stem = s[:-1]
        out |= {s, stem+'é', stem+'ou', stem+'ové'}
        return out
    
    # Mareček -> Marečka, Marečkovi...
    if low.endswith('ek'):
        stem = s[:-2]
        out |= {s, stem+'ka', stem+'kovi', stem+'kem', stem+'ku'}
        return out
    
    # Říha -> Říhovi, Říhy...
    if low.endswith('a') and len(s) >= 2:
        stem = s[:-1]
        out |= {s, stem+'y', stem+'ovi', stem+'ou', stem+'u', stem+'e'}
        return out
    
    out |= {s+'a', s+'ovi', s+'e', s+'em', s+'u'}
    return out

# =============== Regexy ===============
ADDRESS_RE = re.compile(r'(?<!\[)\b[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^\n\r,\[\]]{2,50}?\s+\d{1,4}(?:/\d{1,4})?,[ \t]*\d{3}[ \t]?\d{2}[ \t]+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^\n\r,\[\]]{1,40}\b', re.UNICODE)
ACCT_RE    = re.compile(r'\b(?:\d{1,6}-)?\d{2,10}/\d{4}\b')
BIRTHID_RE = re.compile(r'\b\d{6}\s*/\s*\d{3,4}\b')
IDCARD_RE  = re.compile(r'\b\d{6,9}/\d{3,4}\b|\b\d{9}\b|[A-Z]{2,3}[ \t]?\d{6,9}\b')
PHONE_RE   = re.compile(r'(?<!\d)(?:\+420|00420)?[ \t\-]?\d{3}[ \t\-]?\d{3}[ \t\-]?\d{3}(?!\s*/\d{4})\b')
EMAIL_RE   = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
DATE_RE    = re.compile(r'\b\d{1,2}\.\s*\d{1,2}\.\s*\d{4}\b')
STATUTE_RE = re.compile(r'\b(Sb\.?|zákon(a|u)?|zákon\s*č\.)\b', re.IGNORECASE)
PAIR_RE    = re.compile(r'(?<!\w)([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{1,})\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{1,})(?!\w)')
TITLES_RE  = re.compile(r'\b(Mgr|Ing|Dr|Ph\.?D|RNDr|MUDr|JUDr|PhDr|PaedDr|ThDr|RCDr|MVDr|DiS|Bc|BcA|MBA|LL\.?M|prof|doc)\.?\s+', re.IGNORECASE)

CTX_PERSON = re.compile(
    r'(nar\.|narozen|rodn[ée]\s*č[íi]slo|RČ|bytem|trval[é]\s*bydlišt[ěi]|'
    r'(e-?mail)|tel\.?|telefon|č\.\s*účtu|IBAN|SPZ|Mgr\.|Ing\.|Bc\.|PhDr\.|JUDr\.|'
    r'dlužník|věřitel|pronajímatel|nájemce|svědek|paní|pan|pana)',
    re.IGNORECASE
)

# =============== Anonymizer ===============
class Anonymizer:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.counter = defaultdict(int)
        self.tag_map = defaultdict(list)
        self.value_to_tag = {}
        self.person_index = {}
        self.canonical_persons = []
        self.person_variants = {}
        self.source_text = ""
        self.uncertain_persons = []
        self.addresses_found = set()

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

    def _ensure_person_tag(self, first_nom: str, last_nom: str) -> str:
        """Zajistí vytvoření nebo nalezení tagu pro osobu"""
        key = (normalize_for_matching(first_nom), normalize_for_matching(last_nom))
        
        if key in self.person_index:
            return self.person_index[key]
        
        tag = self._get_or_create_tag('PERSON', f'{first_nom} {last_nom}')
        self.person_index[key] = tag
        self.canonical_persons.append({'first': first_nom, 'last': last_nom, 'tag': tag})
        
        fvars = variants_for_first(first_nom)
        svars = variants_for_surname(last_nom)
        self.person_variants[tag] = {f'{f} {s}' for f in fvars for s in svars}
        
        return tag

    def _extract_addresses_first(self, text: str):
        """Extrahuje a označí všechny adresy, aby nebyly detekovány jako jména"""
        for m in ADDRESS_RE.finditer(text):
            addr = m.group(0).strip()
            # Vyčistit adresu
            addr = re.sub(r'^(Trvalé\s+bydliště|Bydliště|Adresa|bytem)\s*:?\s*', '', addr, flags=re.IGNORECASE)
            addr = addr.strip()
            if addr:
                # Uložíme si všechna slova z adresy
                words = addr.split()
                for word in words:
                    if word and word[0].isupper():
                        self.addresses_found.add(normalize_for_matching(word))

    def _extract_persons_to_index(self, text: str):
        """Extrahuje osoby z textu - POUZE pokud nejsou součástí adresy"""
        text_no_titles = TITLES_RE.sub('', text)
        
        for m in PAIR_RE.finditer(text_no_titles):
            s, e = m.span()
            f_tok, l_tok = m.group(1), m.group(2)
            
            # Skip pokud je to část adresy
            if is_address_part(f_tok) or is_address_part(l_tok):
                continue
            if normalize_for_matching(f_tok) in self.addresses_found:
                continue
            if normalize_for_matching(l_tok) in self.addresses_found:
                continue
            
            # Skip role keywords
            if f_tok.lower() in ROLE_STOP or l_tok.lower() in ROLE_STOP:
                continue
            if normalize_for_matching(l_tok) in SURNAME_BLACKLIST:
                continue
            
            # Kontrola zda je křestní jméno v knihovně
            is_valid, f_nom = is_valid_firstname_or_variant(f_tok)
            
            if is_valid and f_nom:
                l_nom = infer_surname_nominative(l_tok)
                self._ensure_person_tag(f_nom, l_nom)
            else:
                # Pokud není jasné, přidáme do nejistých
                pre = text[max(0, s-80):s]
                post = text[e:e+80]
                if CTX_PERSON.search(pre+post):
                    # Ale ještě zkontrolujeme, že to není adresa
                    if not any(addr_word in pre+post for addr_word in ['bytem', 'bydliště', 'adrese']):
                        self.uncertain_persons.append(f"{f_tok} {l_tok}")

    def _apply_known_people(self, text: str) -> str:
        """Aplikuje všechny varianty již známých osob"""
        for p in self.canonical_persons:
            tag = p['tag']
            
            for pat in sorted(self.person_variants[tag], key=len, reverse=True):
                rx = re.compile(r'(?<!\w)'+re.escape(pat)+r'(?!\w)', re.IGNORECASE)
                def repl(m):
                    surf = m.group(0)
                    self._record_value(tag, surf)
                    return preserve_case(surf, tag)
                text = rx.sub(repl, text)
        
        return text

    def _is_statute(self, text: str, s: int, e: int) -> bool:
        pre = text[max(0, s-20):s]
        post = text[e:e+10]
        return bool(STATUTE_RE.search(pre) or STATUTE_RE.search(post))

    def _replace_entity(self, text: str, rx: re.Pattern, cat: str) -> str:
        def repl(m):
            v = m.group(0)
            tag = self._get_or_create_tag(cat, v)
            self._record_value(tag, v)
            return tag
        return rx.sub(repl, text)

    def anonymize_entities(self, text: str) -> str:
        # NEJDŘÍV zpracovat adresy
        def addr_repl(m):
            v = m.group(0).strip()
            v = re.sub(r'^(Trvalé\s+bydliště|Bydliště|Adresa)\s*:\s*', '', v, flags=re.IGNORECASE)
            v = re.sub(r'^.{0,30}?\b(na\s+adrese|v\s+domě|domu)\s+', '', v, flags=re.IGNORECASE)
            v = v.strip()
            if not v:
                return m.group(0)
            tag = self._get_or_create_tag('ADDRESS', v)
            self._record_value(tag, v)
            return tag
        text = ADDRESS_RE.sub(addr_repl, text)
        
        # Pak ostatní entity
        text = self._replace_entity(text, EMAIL_RE, 'EMAIL')
        text = self._replace_entity(text, DATE_RE, 'DATE')

        def phone_repl(m):
            v = m.group(0)
            s, e = m.span()
            if re.match(r'^\s*/\d{4}', text[e:e+6]):
                return v
            tag = self._get_or_create_tag('PHONE', v)
            self._record_value(tag, v)
            return tag
        text = PHONE_RE.sub(phone_repl, text)

        def acct_like(m):
            s, e = m.span()
            if self._is_statute(text, s, e):
                return m.group(0)
            raw = m.group(0)
            
            parts = raw.split('/')
            if len(parts) == 2:
                main_part = parts[0].replace('-', '')
                bank_code = parts[1]
                
                if len(main_part) >= 6 and len(bank_code) == 4:
                    tag = self._get_or_create_tag('BANK', raw)
                    self._record_value(tag, raw)
                    return tag
            
            return raw
        text = ACCT_RE.sub(acct_like, text)

        def birth_or_id_repl(m):
            v = m.group(0)
            tag = self._get_or_create_tag('BIRTH_ID', v)
            self._record_value(tag, v)
            return tag
        text = BIRTHID_RE.sub(birth_or_id_repl, text)

        return text

    def show_warnings(self):
        """Zobrazí varování pro nejisté případy"""
        if self.uncertain_persons:
            root = tk.Tk()
            root.withdraw()
            
            unique_uncertain = list(set(self.uncertain_persons))
            msg = f"Následující jména nebyla nalezena v knihovně a NEBYLA anonymizována:\n\n"
            msg += "\n".join(f"• {p}" for p in unique_uncertain[:15])
            if len(unique_uncertain) > 15:
                msg += f"\n... a dalších {len(unique_uncertain)-15} případů"
            msg += "\n\nZkontrolujte prosím výstup ručně!"
            
            messagebox.showwarning("⚠️ Nejistá jména", msg)
            root.destroy()

    def anonymize_docx(self, input_path: str, output_path: str, json_map: str, txt_map: str):
        doc = Document(input_path)
        pieces = []
        for p in iter_paragraphs(doc):
            pieces.append(clean_invisibles(get_text(p)))
        self.source_text = '\n'.join(pieces)

        # NEJDŘÍV analyzovat adresy
        self._extract_addresses_first(self.source_text)
        
        # PAK extrahovat osoby
        self._extract_persons_to_index(self.source_text)

        # Zpracovat každý odstavec
        for p in iter_paragraphs(doc):
            raw = get_text(p)
            if not raw.strip():
                continue
            txt = clean_invisibles(raw)
            # Nejdřív aplikovat známé osoby
            txt = self._apply_known_people(txt)
            # Pak anonymizovat entity
            txt = self.anonymize_entities(txt)
            if txt != raw:
                set_text(p, txt)

        # Uložit výsledky
        doc.save(output_path)

        # Vyčistit duplicity v tag_map
        for tag in self.tag_map:
            self.tag_map[tag] = list(set(self.tag_map[tag]))

        data = OrderedDict((tag, self.tag_map[tag]) for tag in sorted(self.tag_map.keys()))
        with open(json_map, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        with open(txt_map, 'w', encoding='utf-8') as f:
            sections = [
                ("OSOBY", "PERSON"),
                ("RODNÁ ČÍSLA", "BIRTH_ID"),
                ("BANKOVNÍ ÚČTY", "BANK"),
                ("TELEFONY", "PHONE"),
                ("EMAILY", "EMAIL"),
                ("OBČANSKÉ PRŮKAZY", "ID_CARD"),
                ("DATA", "DATE"),
                ("ADRESY", "ADDRESS"),
            ]
            for title, pref in sections:
                items = []
                for tag, vals in sorted(self.tag_map.items()):
                    if tag.startswith(f'[[{pref}_'):
                        for v in vals:
                            items.append(f"{tag}: {v}")
                if items:
                    f.write(f"{title}\n{'-'*len(title)}\n")
                    f.write("\n".join(items) + "\n\n")

        # Zobrazit varování
        self.show_warnings()

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Anonymizace českých DOCX s JSON knihovnou jmen")
    ap.add_argument("docx_path", nargs='?', help="Cesta k .docx souboru")
    ap.add_argument("--names-json", default="cz_names.v1.json", help="Cesta k JSON knihovně jmen")
    args = ap.parse_args()

    if args.names_json != "cz_names.v1.json":
        global CZECH_FIRST_NAMES
        CZECH_FIRST_NAMES = load_names_library(args.names_json)

    path = Path(args.docx_path) if args.docx_path else Path(input("Přetáhni sem .docx soubor nebo napiš cestu: ").strip().strip('"'))
    if not path.exists():
        print("❌ Soubor nenalezen:", path)
        return 2
    
    base = path.stem
    out_docx = path.parent / f"{base}_anon.docx"
    out_json = path.parent / f"{base}_map.json"
    out_txt  = path.parent / f"{base}_map.txt"
    
    print(f"\n📄 Zpracovávám: {path.name}")
    print(f"📚 Používám knihovnu: cz_names.v1.json")
    
    a = Anonymizer(verbose=False)
    a.anonymize_docx(str(path), str(out_docx), str(out_json), str(out_txt))
    
    print("\n✅ Výstupy:")
    print(f" - {out_docx}")
    print(f" - {out_json}")
    print(f" - {out_txt}")
    print(f"\n📊 Statistiky:")
    print(f" - Nalezeno osob: {len(a.canonical_persons)}")
    print(f" - Celkem tagů: {sum(a.counter.values())}")
    
    if a.uncertain_persons:
        print(f"\n⚠️  Nejistých jmen (zkontrolujte): {len(set(a.uncertain_persons))}")

if __name__ == "__main__":
    sys.exit(main())