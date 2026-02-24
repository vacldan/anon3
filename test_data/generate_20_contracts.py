from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from docx import Document
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "test_data"


MALE_FIRST = [
    "Jan", "Pavel", "Tomáš", "Václav", "Karel", "Marek", "Ondřej", "Aleš", "Roman", "Štěpán",
    "Matěj", "Filip", "Michal", "David", "Erik", "Jaroslav", "Oldřich",
]
FEMALE_FIRST = [
    "Petra", "Jana", "Lucie", "Markéta", "Veronika", "Barbora", "Renata", "Helena", "Klára",
    "Gabriela", "Adéla", "Simona", "Tereza", "Monika", "Alžběta",
]
MALE_LAST = [
    "Novák", "Svoboda", "Dvořák", "Černý", "Procházka", "Kříž", "Král", "Vlach", "Holík",
    "Hrubeš", "Řezníček", "Roubal", "Vaněk", "Beneš", "Malík", "Turek",
]
FEMALE_LAST = [
    "Nováková", "Svobodová", "Dvořáková", "Černá", "Procházková", "Křížová", "Králová",
    "Vlachová", "Holíková", "Hrubešová", "Řezníčková", "Roubalová", "Vaňková",
    "Benešová", "Malíková", "Turková",
]

STREETS = [
    ("Vinohradská", "Praha 3", "130 00"),
    ("Křenová", "Brno", "602 00"),
    ("Dlouhá", "Brno", "602 00"),
    ("Technologická", "Praha 6", "160 00"),
    ("Pojišťovací", "Praha 1", "110 00"),
    ("Na Kopci", "Praha 10", "100 00"),
    ("U Parku", "Olomouc", "779 00"),
    ("Jabloňová", "Ústí nad Labem", "400 01"),
    ("Sadová", "České Budějovice", "370 01"),
    ("Na Návsi", "Zábřeh", "789 01"),
]

COMPANIES = [
    ("PrivatMed Clinic s.r.o.", "Poliklinická 3, 120 00 Praha 2", "99887766", "recepce@privatmed.cz", "+420 224 333 444"),
    ("Krajská nemocnice Jih a.s.", "Nemocniční 1, 400 01 Ústí nad Labem", "44550011", "podatelna@knjih.cz", "+420 477 111 222"),
    ("Advokátní kancelář Lex & Partners s.r.o.", "Právnická 12, 110 00 Praha 1", "11223344", "info@lexpartners.cz", "+420 222 555 101"),
    ("Gymnázium Na Hradbách", "Na Hradbách 15, 702 00 Ostrava", "12398745", "sekretariat@gymhradby.cz", "+420 596 111 222"),
    ("Městský úřad Nový Brod", "Náměstí 1, 500 02 Hradec Králové", "00223344", "podatelna@novybrod.cz", "+420 495 888 111"),
    ("Univerzita Sever", "Kampus 9, 625 00 Brno", "00224466", "rektorat@unisever.cz", "+420 541 111 000"),
]


def rnd_phone(r: random.Random) -> str:
    return f"+420 {r.randint(600, 799)} {r.randint(100, 999):03d} {r.randint(100, 999):03d}"


def rnd_email(first: str, last: str, r: random.Random, domain: str = "example.com") -> str:
    local = f"{first}.{last}".lower().replace(" ", ".")
    # Strip accents for email local-part
    local = "".join(
        c for c in unicodedata.normalize("NFD", local)
        if unicodedata.category(c) != "Mn"
    )
    local = local.replace(" ", "")
    return f"{local}@{domain}"


def rnd_birth_id(r: random.Random) -> str:
    # two-digit year: either 60-99 (1960-1999) or 00-10 (2000-2010)
    yy = r.choice([r.randint(60, 99), r.randint(0, 10)])
    mm = r.randint(1, 12)
    dd = r.randint(1, 28)
    suffix = r.randint(1000, 9999)
    return f"{yy:02d}{mm:02d}{dd:02d}/{suffix}"


def rnd_date(r: random.Random) -> str:
    y = r.randint(1960, 2010)
    m = r.randint(1, 12)
    d = r.randint(1, 28)
    return f"{d:02d}. {m:02d}. {y}"


def rnd_address(r: random.Random) -> str:
    street, city, psc = r.choice(STREETS)
    house = r.randint(1, 199)
    apt = r.randint(1, 30)
    return f"{street} {house}/{apt}, {psc} {city}"


def rnd_bank(r: random.Random) -> str:
    return f"{r.randint(100000000, 999999999)}/{r.choice(['0100','0300','5500','0600'])}"


def rnd_iban(r: random.Random) -> str:
    # Fake-ish CZ IBAN
    bank = r.choice(["0100", "0300", "0600", "0800", "5500"])
    prefix = r.randint(0, 999999).to_bytes(3, "big").hex().upper()[:6]
    acct = f"{r.randint(0, 9999999999999999):016d}"
    return f"CZ{r.randint(10,99)} {bank} 0000 {acct[:4]} {acct[4:8]} {acct[8:12]} {acct[12:16]}"


def rnd_mac(r: random.Random) -> str:
    return ":".join(f"{r.randint(0,255):02X}" for _ in range(6))


def rnd_ip(r: random.Random) -> str:
    if r.random() < 0.2:
        return "192.168.11.22"
    return f"{r.randint(10, 223)}.{r.randint(0, 255)}.{r.randint(0, 255)}.{r.randint(1, 254)}"


def inflect_person(first: str, last: str) -> dict[str, str]:
    """
    Very rough Czech case forms for testing. Produces a few common variants.
    """
    is_female = last.endswith("á")

    def male_first_forms(name: str) -> dict[str, str]:
        if name.endswith("el"):
            stem = name[:-2]
            return {"gen": stem + "la", "dat": stem + "lovi", "ins": stem + "lem", "voc": stem + "le"}
        if name.endswith("áš"):
            stem = name[:-2]
            return {"gen": stem + "áše", "dat": stem + "ášovi", "ins": stem + "ášem", "voc": stem + "áši"}
        if name.endswith("ek"):
            stem = name[:-2]
            return {"gen": stem + "ka", "dat": stem + "kovi", "ins": stem + "kem", "voc": stem + "ku"}
        if name.endswith("a"):
            stem = name[:-1]
            return {"gen": stem + "y", "dat": stem + "ovi", "ins": stem + "ou", "voc": stem + "o"}
        # default
        return {"gen": name + "a", "dat": name + "ovi", "ins": name + "em", "voc": name + "e"}

    def female_first_forms(name: str) -> dict[str, str]:
        if name.endswith("a"):
            stem = name[:-1]
            return {"gen": stem + "y", "dat": stem + "ě", "ins": stem + "ou", "voc": stem + "o"}
        return {"gen": name, "dat": name, "ins": name, "voc": name}

    def male_last_forms(s: str) -> dict[str, str]:
        if s.endswith("ek"):
            stem = s[:-2]
            return {"gen": stem + "ka", "dat": stem + "kovi", "ins": stem + "kem", "voc": stem + "ku"}
        if s.endswith("a"):
            stem = s[:-1]
            return {"gen": stem + "y", "dat": stem + "ovi", "ins": stem + "ou", "voc": stem + "o"}
        return {"gen": s + "a", "dat": s + "ovi", "ins": s + "em", "voc": s + "e"}

    def female_last_forms(s: str) -> dict[str, str]:
        if s.endswith("ová"):
            stem = s[:-3]
            return {"gen": stem + "ové", "dat": stem + "ové", "ins": stem + "ovou", "voc": stem + "ová"}
        if s.endswith("á"):
            stem = s[:-1]
            return {"gen": stem + "é", "dat": stem + "é", "ins": stem + "ou", "voc": stem + "á"}
        return {"gen": s, "dat": s, "ins": s, "voc": s}

    if is_female:
        ff = female_first_forms(first)
        lf = female_last_forms(last)
    else:
        ff = male_first_forms(first)
        lf = male_last_forms(last)

    return {
        "nom": f"{first} {last}",
        "gen": f"{ff['gen']} {lf['gen']}",
        "dat": f"{ff['dat']} {lf['dat']}",
        "ins": f"{ff['ins']} {lf['ins']}",
        "voc": f"{ff['voc']} {lf['voc']}",
        "acc": f"{ff['gen']} {lf['gen']}",
    }


@dataclass
class Person:
    first: str
    last: str
    forms: dict[str, str]
    birth_id: str
    birth_date: str
    address: str
    phone: str
    email: str


def make_person(r: random.Random, female: bool) -> Person:
    first = r.choice(FEMALE_FIRST if female else MALE_FIRST)
    last = r.choice(FEMALE_LAST if female else MALE_LAST)
    forms = inflect_person(first, last)
    return Person(
        first=first,
        last=last,
        forms=forms,
        birth_id=rnd_birth_id(r),
        birth_date=rnd_date(r),
        address=rnd_address(r),
        phone=rnd_phone(r),
        email=rnd_email(first, last, r),
    )


def contract_text(idx: int, r: random.Random) -> str:
    """
    Returns a semi-legal Czech document with rich PII and several name case variants.
    """
    provider = make_person(r, female=False if idx % 2 == 0 else True)
    client = make_person(r, female=True if idx % 3 == 0 else False)
    witness = make_person(r, female=(idx % 4 == 0))
    guardian = make_person(r, female=True)

    company = r.choice(COMPANIES)
    comp_name, comp_addr, comp_ico, comp_email, comp_phone = company

    iban = rnd_iban(r)
    bank = rnd_bank(r)
    mac = rnd_mac(r)
    ip4 = rnd_ip(r)
    ip6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    card = f"{r.randint(4000,4999)} {r.randint(1000,9999)} {r.randint(1000,9999)} {r.randint(1000,9999)}"
    passport = f"{r.choice(['PP','CZ','EA'])}{r.randint(1000000,9999999)}"
    id_card = f"{r.randint(100000000,999999999)}"
    license_plate = f"{r.choice(['1AB','2AC','5AZ','7B8','3AA'])} {r.randint(1000,9999)}"
    vin = f"WAUZZZ8V0{r.choice(['FA','GA','HA','KA'])}{r.randint(100000,999999)}"

    username = f"{provider.first[0].lower()}{provider.last.lower()}"
    password = f"{provider.first[:2]}{r.randint(10,99)}!{r.randint(1000,9999)}"

    scenarios = [
        ("Souhlas s hospitalizací a zpracováním zdravotnické dokumentace", "nemocnice", True),
        ("Souhlas s ambulantním vyšetřením a laboratorními testy", "lékařství", True),
        ("Dohoda o právním zastoupení", "právníci", False),
        ("Plná moc pro zastupování u soudu", "soudy", False),
        ("Žádost a souhlas se zpracováním údajů žáka", "školy", False),
        ("Záznam o jednání a doručování soudních písemností", "soudy", False),
        ("Smlouva o zpracování osobních údajů pacientů (GDPR čl. 28)", "nemocnice", True),
        ("Smlouva o poskytování sociálních služeb", "sociální služby", True),
        ("Smlouva o psychologickém poradenství ve škole", "školy", True),
        ("Smlouva o archivaci zdravotnické dokumentace", "nemocnice", True),
        ("Smlouva o advokátní úschově", "právníci", False),
        ("Záznam o přijetí trestního oznámení", "policie", False),
        ("Smlouva o mediaci", "právníci", False),
        ("Smlouva o vzdělávání a praxi studenta v nemocnici", "nemocnice", True),
        ("Protokol o jednání školské rady", "školy", False),
        ("Smlouva o poskytování rehabilitačních služeb", "lékařství", True),
        ("Žádost o nahlížení do soudního spisu", "soudy", False),
        ("Smlouva o poskytování právních služeb pro školu", "školy/právo", False),
        ("Informovaný souhlas s operací", "nemocnice", True),
        ("Souhlas se zpracováním údajů v nemocničním informačním systému", "nemocnice", True),
    ]
    title, sector, health_sensitive = scenarios[(idx - 11) % len(scenarios)]

    # Sprinkle name cases
    p = provider.forms
    c = client.forms
    w = witness.forms
    g = guardian.forms

    health_lines = ""
    if health_sensitive:
        health_lines = (
            "\nIII. ZDRAVOTNÍ ÚDAJE (ZVLÁŠTNÍ KATEGORIE)\n\n"
            f"1. Pacient/klient bere na vědomí, že {c['nom']} poskytuje údaje o zdravotním stavu, "
            "např. diagnóza: hypertenze, alergie na penicilin, užívané léky: metoprolol.\n"
            f"2. Výsledky vyšetření budou zasílány {c['dat']} na e‑mail {client.email} a mohou být "
            f"sděleny i zákonnému zástupci {g['dat']}.\n"
        )

    text = f"""{title.upper()}

I. IDENTIFIKACE SUBJEKTŮ

1. Organizace / pracoviště:
   Název: {comp_name}
   Adresa: {comp_addr}
   IČO: {comp_ico}
   Telefon: {comp_phone}
   E‑mail: {comp_email}

2. Odpovědná osoba / pracovník:
   Jméno a příjmení: {p['nom']}
   Datum narození: {provider.birth_date}
   Rodné číslo: {provider.birth_id}
   Adresa: {provider.address}
   OP/Pas: {id_card}
   Telefon: {provider.phone}
   E‑mail: {provider.email}

3. Klient / účastník / pacient:
   Jméno a příjmení: {c['nom']}
   Datum narození: {client.birth_date}
   Rodné číslo: {client.birth_id}
   Adresa: {client.address}
   Číslo pasu: {passport}
   Telefon: {client.phone}
   E‑mail: {client.email}
   Platební karta: {card}, platnost 08/28, CVC: 123

II. ÚČEL A ROZSAH

1. Dokument upravuje pravidla komunikace a zpracování osobních údajů mezi {p['ins']} a {c['ins']}.
2. Smluvní strany potvrzují, že údaje o {c['gen']} mohou být použity pro účely evidence, komunikace a vyúčtování.
3. Příklady pádů jmen pro test:
   - „s {c['ins']}“, „k {c['dat']}“, „bez {c['gen']}“, „{c['voc']}“.
   - „s {p['ins']}“, „k {p['dat']}“, „bez {p['gen']}“, „{p['voc']}“.

{health_lines}
IV. PLATBY, FAKTURACE, DORUČOVÁNÍ

1. Úhrady budou prováděny na účet: {bank}; IBAN: {iban}.
2. Variabilní symbol: {client.birth_id.replace('/', '')}.
3. Doručování zpráv:
   a) e‑mailem na adresy {provider.email} a {client.email},
   b) telefonicky na čísla {provider.phone} a {client.phone},
   c) písemně na adresu {client.address}.

V. PŘÍSTUP A LOGOVÁNÍ

1. Přístup do interního systému:
   Uživatelské jméno: {username}
   Heslo: {password}
2. Přístupy mohou být logovány včetně IP adres {ip4} a {ip6} a MAC adresy {mac}.

VI. DALŠÍ OSOBY

1. Svědek / doprovod:
   {w['nom']}, nar. {witness.birth_date}, RČ {witness.birth_id}, tel. {witness.phone}, e‑mail {witness.email}.
2. Zákonný zástupce / kontakt:
   {g['nom']}, nar. {guardian.birth_date}, RČ {guardian.birth_id}, tel. {guardian.phone}, e‑mail {guardian.email}.
3. V textu se dále vyskytují tvary: „s {w['ins']}“, „k {w['dat']}“, „bez {w['gen']}“.

VII. DOPLŇKOVÉ IDENTIFIKÁTORY

1. Registrační značka vozidla: {license_plate}
2. VIN: {vin}

VIII. ZÁVĚREČNÁ USTANOVENÍ

1. Tento dokument je vyhotoven ve dvou stejnopisech.
2. Na důkaz souhlasu připojují podpisy {p['gen']} a {c['gen']}.

V {sector} dne {date.today().strftime('%d. %m. %Y')}

……………………..............................
{p['nom']}

……………………..............................
{c['nom']}
"""
    return text


def write_txt_and_docx(stem: str, text: str) -> None:
    txt_path = OUT_DIR / f"{stem}.txt"
    docx_path = OUT_DIR / f"{stem}.docx"

    txt_path.write_text(text, encoding="utf-8")

    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(docx_path)


def main() -> None:
    r = random.Random(20260224)
    for idx in range(11, 31):
        stem = f"smlouva_gdpr_test_{idx:02d}"
        text = contract_text(idx, r)
        write_txt_and_docx(stem, text)
        print("Wrote", stem)


if __name__ == "__main__":
    main()

