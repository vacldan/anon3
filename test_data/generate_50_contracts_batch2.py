# -*- coding: utf-8 -*-
"""
Generuje 50 fiktivních smluv (smlouva_gdpr_test_101 až 150).
Každá smlouva má min. 3 strany, podobné pracovní a smluvní prostředí jako batch 1.
"""
from __future__ import annotations

import random
import unicodedata
from datetime import date
from pathlib import Path

from docx import Document

# Import sdílených pomocníků z existujícího generátoru
from generate_20_contracts import (
    STREETS,
    COMPANIES,
    MALE_FIRST,
    FEMALE_FIRST,
    MALE_LAST,
    FEMALE_LAST,
    make_person,
    inflect_person,
    rnd_phone,
    rnd_email,
    rnd_birth_id,
    rnd_date,
    rnd_address,
    rnd_bank,
    rnd_iban,
    rnd_mac,
    rnd_ip,
    OUT_DIR,
)

# Další scénáře pro rozmanitost (pracovní a smluvní prostředí)
SCENARIOS = [
    ("Smlouva o zpracování osobních údajů dle GDPR čl. 28", "zdravotnictví", True),
    ("Smlouva o právním zastoupení a plná moc", "advokátní kancelář", False),
    ("Smlouva o poskytování zdravotních služeb", "nemocnice", True),
    ("Dohoda o zpracování osobních údajů v rámci vzdělávání", "školství", False),
    ("Smlouva o sociálních službách a ochraně údajů", "sociální služby", True),
    ("Smlouva o advokátní úschově a zpracování údajů", "právo", False),
    ("Informovaný souhlas a smlouva o péči", "zdravotnictví", True),
    ("Smlouva o mediaci a ochraně osobních údajů", "mediace", False),
    ("Smlouva o praxi studenta a zpracování údajů", "školství / zdravotnictví", True),
    ("Smlouva o rehabilitačních službách", "zdravotnictví", True),
    ("Smlouva o poskytování právních služeb", "právo", False),
    ("Souhlas se zpracováním údajů v informačním systému", "veřejná správa", False),
    ("Smlouva o zastupování v řízení před úřadem", "advokátní kancelář", False),
    ("Smlouva o účetním servisu a zpracování údajů", "účetnictví", False),
    ("Smlouva o personálním zajištění projektu", "HR / consulting", False),
    ("Smlouva o IT podpoře a zpracování přístupových údajů", "IT", False),
    ("Smlouva o úklidových službách a přístupu k osobním údajům", "služby", False),
    ("Smlouva o pojištění a zpracování údajů pojistníka", "pojišťovnictví", False),
    ("Smlouva o pronájmu a zpracování údajů nájemce", "nemovitosti", False),
    ("Smlouva o dodávce a zpracování údajů odběratele", "obchod", False),
    ("Smlouva o provozování stravování a údajích strávníků", "stravování", True),
    ("Smlouva o zabezpečení objektu a záznamech z kamer", "bezpečnost", False),
    ("Smlouva o právní pomoci a ochraně údajů klienta", "právo", False),
    ("Smlouva o psychologickém poradenství", "zdravotnictví", True),
    ("Smlouva o archivaci dokumentů a osobních údajů", "archivace", False),
    ("Smlouva o mzdovém účetnictví a zpracování údajů zaměstnanců", "personalistika", False),
    ("Smlouva o údržbě zeleně a přístupu k údajům objednatele", "služby", False),
    ("Smlouva o překladatelských službách a důvěrnosti údajů", "překlady", False),
    ("Smlouva o pořádání školení a zpracování údajů účastníků", "vzdělávání", False),
    ("Smlouva o provozování recepce a evidence návštěv", "služby", False),
    ("Smlouva o právní pomoci v insolvenci", "právo", False),
    ("Smlouva o zajištění úklidu a přístupu k osobním údajům", "facility", False),
    ("Smlouva o provozování kantýny a údajích zaměstnanců", "stravování", True),
    ("Smlouva o technické podpoře a přístupu k systémům", "IT", False),
    ("Smlouva o provádění auditu a zpracování údajů", "audit", False),
    ("Smlouva o vedení personální agendy", "HR", False),
    ("Smlouva o právní pomoci v pracovněprávních sporech", "právo", False),
    ("Smlouva o údržbě IT infrastruktury a logování přístupů", "IT", False),
    ("Smlouva o dodávce energií a zpracování údajů odběratele", "energetika", False),
    ("Smlouva o provozování dětské skupiny a údajích o dětech", "školství", True),
    ("Smlouva o zajištění bezpečnosti a evidence osob", "bezpečnost", False),
    ("Smlouva o právním servisu pro podnikatele", "právo", False),
    ("Smlouva o údržbě budov a přístupu k údajům správce", "správa budov", False),
    ("Smlouva o provozování knihovny a čtenářských údajů", "kultura", False),
    ("Smlouva o zajištění údržby vozidel a údajů řidičů", "doprava", False),
    ("Smlouva o provozování fitness a údajích členů", "sport", True),
    ("Smlouva o právní pomoci v občanskoprávních věcech", "právo", False),
    ("Smlouva o zajištění cateringových služeb a údajů objednatele", "catering", False),
    ("Smlouva o provozování lékárny a zpracování údajů zákazníků", "zdravotnictví", True),
    ("Smlouva o údržbě výpočetní techniky a přístupu k datům", "IT", False),
    ("Smlouva o právní pomoci při nákupu nemovitosti", "právo", False),
    ("Smlouva o zajištění úklidu v nemocnici a přístupu k údajům", "zdravotnictví", False),
    ("Smlouva o provozování domova pro seniory a údajích klientů", "sociální služby", True),
    ("Smlouva o právní pomoci v rodinném právu", "právo", False),
    ("Smlouva o zajištění poštovních služeb a doručování", "služby", False),
    ("Smlouva o provozování jídelny a údajích strávníků", "stravování", True),
]


def long_contract_text(idx: int, r: random.Random) -> str:
    """Vrátí text smlouvy o délce cca 3+ stran (rozšířené sekce, více článků)."""
    provider = make_person(r, female=(idx % 3 == 1))
    client = make_person(r, female=(idx % 4 == 0))
    witness = make_person(r, female=(idx % 5 == 0))
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

    scenario_idx = (idx - 101) % len(SCENARIOS)
    title, sector, health_sensitive = SCENARIOS[scenario_idx]

    p, c, w, g = provider.forms, client.forms, witness.forms, guardian.forms

    health_block = ""
    if health_sensitive:
        health_block = f"""
III. ZDRAVOTNÍ ÚDAJE A ZVLÁŠTNÍ KATEGORIE

1. Klient {c['nom']} bere na vědomí, že v rámci plnění smlouvy mohou být zpracovány údaje o zdravotním stavu.
2. Tyto údaje budou zpracovávány v souladu s čl. 9 GDPR a příslušnými vnitřními předpisy.
3. Výsledky vyšetření nebo záznamy mohou být předány {c['dat']} nebo zákonnému zástupci {g['dat']} na e‑mail {client.email}.
4. Pacient/klient souhlasí s tím, že údaje o užívaných lécích a diagnózách mohou být vedeny v elektronické dokumentaci.
"""

    text = f"""{title.upper()}

I. IDENTIFIKACE SMLUVNÍCH STRAN

1. Poskytovatel / organizace:
   Název: {comp_name}
   Sídlo: {comp_addr}
   IČO: {comp_ico}
   Telefon: {comp_phone}
   E‑mail: {comp_email}

2. Odpovědná osoba ze strany poskytovatele:
   Jméno a příjmení: {p['nom']}
   Datum narození: {provider.birth_date}
   Rodné číslo: {provider.birth_id}
   Adresa: {provider.address}
   Číslo OP: {id_card}
   Telefon: {provider.phone}
   E‑mail: {provider.email}

3. Klient / objednatel / pacient:
   Jméno a příjmení: {c['nom']}
   Datum narození: {client.birth_date}
   Rodné číslo: {client.birth_id}
   Adresa: {client.address}
   Číslo pasu: {passport}
   Telefon: {client.phone}
   E‑mail: {client.email}
   Platební karta: {card}, platnost 08/28

II. PŘEDMĚT A ROZSAH SMLOUVY

1. Tato smlouva upravuje vzájemná práva a povinnosti mezi {p['ins']} zastupujícím {comp_name} a {c['ins']}.
2. Smlouva se uzavírá v oblasti: {sector}.
3. Smluvní strany potvrzují, že údaje o {c['gen']} budou zpracovávány pouze k účelům stanoveným v této smlouvě.
4. Pro účely komunikace a doručování budou použity kontaktní údaje {provider.email}, {provider.phone} a {client.email}, {client.phone}.
5. V dokumentaci se vyskytují tvary jmen: „s {c['ins']}“, „k {c['dat']}“, „bez {c['gen']}“, „{c['voc']}“ a obdobně „s {p['ins']}“, „k {p['dat']}“, „{p['voc']}“.
{health_block}
IV. ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ (GDPR)

1. Správcem osobních údajů je {comp_name}, {comp_addr}, IČO {comp_ico}.
2. Kontaktní osoba pro ochranu údajů: {p['nom']}, e‑mail {provider.email}, telefon {provider.phone}.
3. Osobní údaje {c['gen']} budou zpracovávány v rozsahu: jméno, příjmení, datum narození, rodné číslo, adresa {client.address}, e‑mail {client.email}, telefon {client.phone}.
4. Účel zpracování: plnění smlouvy, komunikace, evidence, fakturace a plnění právních povinností.
5. Právní základ: plnění smlouvy (čl. 6 odst. 1 písm. b) GDPR), případně souhlas nebo oprávněný zájem.
6. Doba uchování: po dobu trvání smlouvy a dle zákonných lhůt (např. 10 let u účetních dokladů).
7. Subjekt údajů má právo na přístup, opravu, výmaz, omezení zpracování a přenositelnost údajů; dále právo podat stížnost u dozorového úřadu.
8. Pověřenec pro ochranu osobních údajů (pokud je určen) je k dispozici na vyžádání u {p['gen']} nebo na {comp_email}.
9. Při předávání údajů subdodavatelům bude sjednána písemná smlouva dle čl. 28 GDPR; klient {c['nom']} má právo na seznam příjemců.
10. V případě bezpečnostního incidentu budou subjekty údajů ({c['nom']}, případně {g['nom']}) informovány bez zbytečného odkladu dle čl. 33 a 34 GDPR.

V. PLATBY A FAKTURACE

1. Úhrady budou prováděny na účet: {bank}; IBAN: {iban}.
2. Variabilní symbol: {client.birth_id.replace('/', '')}.
3. Fakturační údaje: {c['nom']}, {client.address}, IČO nebo rodné číslo dle typu plátce.
4. Doručování faktur a zpráv: e‑mailem na {client.email} nebo {provider.email}, případně písemně na adresu {client.address}.
5. V případě platební neschopnosti může být věc předána k vymáhání; v takovém případě mohou být údaje o {c['dat']} předány oprávněným subjektům.

VI. PŘÍSTUPY A BEZPEČNOST

1. Přístup do interního systému: uživatelské jméno {username}, heslo (předáno odděleně).
2. Přihlášení mohou být logována včetně IP adres ({ip4}, {ip6}) a MAC adresy {mac}.
3. Klient {c['nom']} je povinen zachovávat důvěrnost přístupových údajů a neprodávat je třetím osobám.
4. V případě ztráty nebo zneužití má {c['nom']} povinnost neprodleně kontaktovat {p['dat']} na {provider.phone} nebo {provider.email}.

VII. DALŠÍ OSOBY A KONTAKTY

1. Svědek / doprovod: {w['nom']}, datum narození {witness.birth_date}, RČ {witness.birth_id}, telefon {witness.phone}, e‑mail {witness.email}.
2. Zákonný zástupce / kontaktní osoba: {g['nom']}, datum narození {guardian.birth_date}, RČ {guardian.birth_id}, telefon {guardian.phone}, e‑mail {guardian.email}.
3. V dokumentaci se vyskytují tvary: „s {w['ins']}“, „k {w['dat']}“, „bez {w['gen']}“, „{w['voc']}“ a „s {g['ins']}“, „k {g['dat']}“.

VIII. DOPLŇKOVÉ IDENTIFIFIKÁTORY

1. Registrační značka vozidla: {license_plate}
2. VIN vozidla: {vin}

IX. ZÁVAZKY STRAN

1. Poskytovatel se zavazuje zpracovávat osobní údaje v souladu s GDPR a vnitřními předpisy.
2. Objednatel {c['nom']} se zavazuje poskytovat údaje pravdivé a včas aktualizovat změny (adresa, telefon, e‑mail).
3. Obě strany jsou povinny zachovávat mlčenlivost o údajích druhé strany, s výjimkou zákonných povinností.
4. V případě změny kontaktních údajů bude {c['nom']} informovat {p['dat']} písemně nebo e‑mailem na {provider.email}.
5. Poskytovatel zajistí technická a organizační opatření tak, aby nedošlo k neoprávněnému přístupu k údajům o {c['dat']}.
6. Objednatel je povinen neprodleně oznámit ztrátu nebo zneužití přístupových údajů na kontakt {provider.phone} nebo {comp_phone}.
7. Veškerá korespondence mezi {p['ins']} a {c['ins']} může být vedena e‑mailem na adresy {provider.email} a {client.email}; písemné doručení na adresu {client.address}.
8. Smluvní strany prohlašují, že mají plnou způsobilost k právním úkonům a že vstupují do smlouvy dobrovolně.

X. DOBA PLATNOSTI A UKONČENÍ

1. Smlouva nabývá účinnosti dnem podpisu.
2. Smlouva se uzavírá na dobu určitou/neurčitou dle vzájemné dohody; ukončení je možné písemnou výpovědí s dodržením výpovědní lhůty.
3. Po skončení smlouvy budou osobní údaje vymazány nebo anonymizovány, s výjimkou údajů, které musí být uchovány ze zákona.
4. O vymazání nebo předání údajů může {c['nom']} požádat na adrese {provider.email} nebo {comp_email}.

XI. ZÁVĚREČNÁ USTANOVENÍ

1. Tento dokument je vyhotoven ve dvou stejnopisech, po jednom pro každou smluvní stranu.
2. Na důkaz souhlasu připojují podpisy: za poskytovatele {p['nom']}, za objednatele {c['nom']}.
3. Smlouva vstupuje v platnost dnem podpisu oběma stranami.

XII. PŘÍLOHY (POKUD JSOU)

1. Příloha č. 1: Seznam zpracovávaných údajů a účelů zpracování.
2. Příloha č. 2: Kontakty na pověřence pro ochranu osobních údajů (pokud je určen).
3. Další přílohy mohou být doplněny písemnou dohodou mezi {p['ins']} a {c['ins']}.

XIII. ZMĚNY A DOPLŇKY

1. Změny a doplňky této smlouvy jsou platné pouze písemně a vyžadují podpis obou stran.
2. Smluvní strany mohou kontaktní údaje upravit písemným oznámením; poskytovatel oznamuje na {comp_email}, objednatel {c['nom']} na adresu {provider.email} nebo písemně na sídlo poskytovatele.
3. V případě sporu se strany pokusí o dohodu; nedojde-li k ní, příslušný je obecný soud podle sídla odpůrce. Pro účely doručování se používá adresa {client.address} pro {c['dat']} a {provider.address} pro {p['dat']}.

V {sector} dne {date.today().strftime('%d. %m. %Y')}

……………………..............................
{p['nom']}

……………………..............................
{c['nom']}
"""
    return text


def write_docx(stem: str, text: str) -> None:
    docx_path = OUT_DIR / f"{stem}.docx"
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(docx_path)


def main() -> None:
    r = random.Random(20260224)
    for idx in range(101, 151):
        stem = f"smlouva_gdpr_test_{idx}"
        text = long_contract_text(idx, r)
        write_docx(stem, text)
        print("Wrote", stem + ".docx")


if __name__ == "__main__":
    main()
