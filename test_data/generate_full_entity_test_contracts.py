#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generuje 5 testovacích smluv obsahujících VŠECHNY typy entit, které SKRYI detekuje.
Každá smlouva pokrývá jiné entity pro kompletní test detekce.
"""

from __future__ import annotations

import random
import unicodedata
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "test_data"

MALE_FIRST = ["Jan", "Pavel", "Tomáš", "Václav", "Marek"]
FEMALE_FIRST = ["Petra", "Jana", "Lucie", "Markéta", "Veronika"]
MALE_LAST = ["Novák", "Svoboda", "Dvořák", "Černý", "Procházka"]
FEMALE_LAST = ["Nováková", "Svobodová", "Dvořáková", "Černá", "Procházková"]

STREETS = [
    ("Vinohradská", "Praha 3", "130 00"),
    ("Křenová", "Brno", "602 00"),
    ("Technologická", "Praha 6", "160 00"),
    ("Pojišťovací", "Praha 1", "110 00"),
    ("Na Kopci", "Praha 10", "100 00"),
]


def rnd_phone(r: random.Random) -> str:
    return f"+420 {r.randint(600, 799)} {r.randint(100, 999):03d} {r.randint(100, 999):03d}"


def rnd_email(first: str, last: str, r: random.Random, domain: str = "example.com") -> str:
    local = f"{first}.{last}".lower().replace(" ", ".")
    local = "".join(c for c in unicodedata.normalize("NFD", local) if unicodedata.category(c) != "Mn")
    local = local.replace(" ", "")
    return f"{local}@{domain}"


def rnd_birth_id(r: random.Random) -> str:
    yy = r.choice([r.randint(60, 99), r.randint(0, 10)])
    mm = r.randint(1, 12)
    dd = r.randint(1, 28)
    suffix = r.randint(1000, 9999)
    return f"{yy:02d}{mm:02d}{dd:02d}/{suffix}"


def rnd_date(r: random.Random) -> str:
    return f"{r.randint(1, 28):02d}. {r.randint(1, 12):02d}. {r.randint(1960, 2010)}"


def rnd_address(r: random.Random) -> str:
    street, city, psc = r.choice(STREETS)
    return f"{street} {r.randint(1, 99)}/{r.randint(1, 20)}, {psc} {city}"


def rnd_bank(r: random.Random) -> str:
    return f"{r.randint(100000000, 999999999)}/{r.choice(['0100', '0300', '5500', '0600'])}"


def rnd_iban(r: random.Random) -> str:
    bank = r.choice(["0100", "0300", "0600", "0800", "5500"])
    acct = f"{r.randint(0, 9999999999999999):016d}"
    return f"CZ{r.randint(10, 99)} {bank} 0000 {acct[:4]} {acct[4:8]} {acct[8:12]} {acct[12:16]}"


def rnd_mac(r: random.Random) -> str:
    return ":".join(f"{r.randint(0, 255):02X}" for _ in range(6))


def rnd_ip(r: random.Random) -> str:
    return f"{r.randint(10, 223)}.{r.randint(0, 255)}.{r.randint(0, 255)}.{r.randint(1, 254)}"


def inflect_person(first: str, last: str) -> dict:
    is_female = last.endswith("á") or last.endswith("ová")
    if is_female:
        return {"nom": f"{first} {last}", "gen": f"{first} {last}", "dat": f"{first} {last}", "ins": f"{first} {last}", "acc": f"{first} {last}"}
    return {"nom": f"{first} {last}", "gen": f"{first}a {last}a", "dat": f"{first}ovi {last}ovi", "ins": f"{first}em {last}em", "acc": f"{first}a {last}a"}


def contract_1_all_basic(r: random.Random) -> str:
    """Smlouva 1: Osobní údaje, kontakty, finance, doklady"""
    p = {"first": "Jan", "last": "Novák", "birth_id": rnd_birth_id(r), "birth_date": rnd_date(r),
         "address": rnd_address(r), "phone": rnd_phone(r), "email": rnd_email("Jan", "Novák", r)}
    p_forms = inflect_person("Jan", "Novák")
    c = {"first": "Petra", "last": "Svobodová", "birth_id": rnd_birth_id(r), "birth_date": rnd_date(r),
         "address": rnd_address(r), "phone": rnd_phone(r), "email": rnd_email("Petra", "Svobodová", r)}
    c_forms = inflect_person("Petra", "Svobodová")

    id_card = "AB 123456"  # Formát OP
    passport = "pas: 12345678"
    driver_license = "ŘP: 987654321"
    bank = rnd_bank(r)
    iban = rnd_iban(r)
    card = f"{r.randint(4000, 4999)} {r.randint(1000, 9999)} {r.randint(1000, 9999)} {r.randint(1000, 9999)}"
    ico = "12345678"
    dic = "CZ12345678"

    return f"""SMLOUVA O POSKYTOVÁNÍ SLUŽEB – TEST ENTIT 1

I. SMLUVNÍ STRANY

1. Poskytovatel: {p_forms['nom']}
   Datum narození: {p['birth_date']}
   Rodné číslo: {p['birth_id']}
   Místo narození: Praha
   Adresa: {p['address']}
   Občanský průkaz č.: {id_card}
   Číslo pasu: {passport}
   Řidičský průkaz: {driver_license}
   Telefon: {p['phone']}
   E-mail: {p['email']}

2. Příjemce: {c_forms['nom']}
   Datum narození: {c['birth_date']}
   Rodné číslo: {c['birth_id']}
   Adresa: {c['address']}
   Telefon: {c['phone']}
   E-mail: {c['email']}

II. PLATBY

Účet: {bank}
IBAN: {iban}
IČO: {ico}
DIČ: {dic}
Platební karta: {card}

III. ZÁVĚR

Smlouva uzavřena mezi {p_forms['ins']} a {c_forms['ins']}.
"""


def contract_2_tech_social(r: random.Random) -> str:
    """Smlouva 2: Technické identifikátory, sociální sítě, biometrie"""
    p = {"first": "Pavel", "last": "Dvořák", "email": rnd_email("Pavel", "Dvořák", r)}
    p_forms = inflect_person("Pavel", "Dvořák")

    ip = rnd_ip(r)
    mac = rnd_mac(r)
    imei = "123456789012345"
    host = "server.production.example.com"
    username = "pavel.dvorak"
    password = "SecretPass123!xyz"
    api_key = "AKIAIOSFODNN7EXAMPLE"
    secret = "Secret: sk_live_51H8xYz1234567890abcdef"
    ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7x8K9vZ1q2w3e4r5t6y7u8i9o0p1q2w3e4r5t6y7u8i9o0p1q2w3e4r5t6y7u8i9o0p1q2w3e4r5t6y7u8i9o0p user@host"
    linkedin = "https://www.linkedin.com/in/pavel-dvorak"
    facebook = "https://www.facebook.com/pavel.dvorak"
    instagram = "Instagram: @pavel_dvorak"
    skype = "Skype: pavel.dvorak"
    voice_id = "Voice ID: VOICE_JP_2024_0156"
    bio_hash = "Hash: HASH_BIO_JP_2024_0156"
    photo_id = "Fotografie: Uloženo v (photo_id_jan_novak_001.jpg)"

    return f"""SMLOUVA O IT SLUŽBÁCH – TEST ENTIT 2

I. ÚDAJE O KLIENTOVI

Klient: {p_forms['nom']}
E-mail: {p['email']}

II. PŘÍSTUPOVÉ ÚDAJE

Credentials: {username} / {password}
Login: {username}
API Key: {api_key}
{secret}
SSH klíč: {ssh_key}

III. SÍŤOVÉ IDENTIFIKÁTORY

IP adresa: {ip}
MAC adresa: {mac}
IMEI: {imei}
Hostname: {host}

IV. SOCIÁLNÍ SÍTĚ

LinkedIn: {linkedin}
Facebook: {facebook}
{instagram}
{skype}

V. BIOMETRICKÉ ÚDAJE (GDPR čl. 9)

{voice_id}
{bio_hash}
{photo_id}

VI. ZÁVĚR

Smlouva uzavřena s {p_forms['ins']}.
"""


def contract_3_health_benefits(r: random.Random) -> str:
    """Smlouva 3: Zdravotnictví, pojištění, benefitní karty, genetika"""
    p = {"first": "Lucie", "last": "Černá", "birth_id": rnd_birth_id(r), "birth_date": rnd_date(r),
         "address": rnd_address(r), "phone": rnd_phone(r)}
    p_forms = inflect_person("Lucie", "Černá")

    insurance = "Číslo pojištěnce: 1234567890"
    benefit_card = "MultiSport karta: MS-123456"
    benefit_card2 = "Sodexo ID: 9876543210"
    genetic_id = "Genetický marker rs28897696"
    rfid = "RFID karta: BADGE-2024-001"
    account_id = "Account ID: 123456789012"

    return f"""SOUHLAS S HOSPITALIZACÍ – TEST ENTIT 3

I. PACIENT

Jméno: {p_forms['nom']}
Datum narození: {p['birth_date']}
Rodné číslo: {p['birth_id']}
Místo narození: Brno
Adresa: {p['address']}
Telefon: {p['phone']}
{insurance}
{benefit_card}
{benefit_card2}
{rfid}
{account_id}

II. ZDRAVOTNÍ ÚDAJE

Genetický profil obsahuje variantu {genetic_id}.

III. ZÁVĚR

Pacientka {p_forms['nom']} souhlasí s léčbou.
"""


def contract_4_vehicles_addresses(r: random.Random) -> str:
    """Smlouva 4: Vozidla, adresy, data"""
    p = {"first": "Marek", "last": "Procházka", "birth_date": rnd_date(r), "address": rnd_address(r)}
    p_forms = inflect_person("Marek", "Procházka")

    spz = "SPZ: 1AB 2345"
    vin = "WAUZZZ8V0FA123456"  # 17 znaků, bez I,O,Q
    date1 = "15. 3. 2025"
    date2 = "28. října 2024"
    addr1 = "Václavské nám. 12, 110 00 Praha 1"
    addr2 = "17. listopadu 45, 602 00 Brno"

    return f"""KUPNÍ SMLOUVA NA VOZIDLO – TEST ENTIT 4

I. KUPUJÍCÍ

{p_forms['nom']}
Datum narození: {p['birth_date']}
Adresa: {p['address']}

II. VOZIDLO

Registrační značka: {spz}
VIN vozidla: {vin}

III. DATA A ADRESY

Datum podpisu: {date1}
Datum předání: {date2}
Sídlo prodávajícího: {addr1}
Korespondenční adresa: {addr2}

IV. ZÁVĚR

Smlouva uzavřena dne {date1} mezi stranami.
"""


def contract_5_mixed_all(r: random.Random) -> str:
    """Smlouva 5: Kombinace všech zbývajících entit"""
    p = {"first": "Veronika", "last": "Králová", "birth_id": rnd_birth_id(r), "birth_date": rnd_date(r),
         "address": rnd_address(r), "phone": rnd_phone(r), "email": rnd_email("Veronika", "Králová", r)}
    p_forms = inflect_person("Veronika", "Králová")
    w = {"first": "Tomáš", "last": "Svoboda", "birth_id": rnd_birth_id(r), "phone": rnd_phone(r)}
    w_forms = inflect_person("Tomáš", "Svoboda")

    id_card = "Číslo občanského průkazu: 123456789"
    passport = "č. pasu: CZ1234567"
    bank = "číslo účtu: 123456789/0800"
    iban = rnd_iban(r)
    card = "Platební karta: 4532 1234 5678 9010"
    ico = "IČO: 87654321"
    dic = "DIČ: CZ87654321"
    insurance = "VZP, číslo: 1234567890"
    benefit = "Edenred karta: ED-654321"
    rfid = "ID karta: EMP-2024-5678"
    genetic = "rs1234567"
    ip = rnd_ip(r)
    mac = rnd_mac(r)
    spz = "RZ: 2AC 9876"
    vin = "VIN: WAUZZZ8V0GA654321"  # 17 znaků (bez I,O,Q)

    return f"""PLNÁ MOC – TEST ENTIT 5 (KOMPLETNÍ)

I. ZASTOUPENÝ

{p_forms['nom']}
Narozena: {p['birth_date']}
Rodné číslo: {p['birth_id']}
Místo narození: Olomouc
Adresa: {p['address']}
{id_card}
{passport}
Telefon: {p['phone']}
E-mail: {p['email']}
{bank}
IBAN: {iban}
{card}
{ico}
{dic}
{insurance}
{benefit}
{rfid}
Genetický kód: {genetic}
IP: {ip}
MAC: {mac}
{spz}
VIN vozidla: {vin}

II. ZASTUPUJÍCÍ

{w_forms['nom']}
RČ: {w['birth_id']}
Tel: {w['phone']}

III. ZÁVĚR

Plná moc udělena {w_forms['dat']} zastupovat {p_forms['acc']}.
"""


def write_docx(stem: str, text: str) -> Path:
    docx_path = OUT_DIR / f"{stem}.docx"
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(docx_path)
    return docx_path


def main() -> None:
    r = random.Random(42)
    contracts = [
        ("smlouva_full_entity_test_01", contract_1_all_basic),
        ("smlouva_full_entity_test_02", contract_2_tech_social),
        ("smlouva_full_entity_test_03", contract_3_health_benefits),
        ("smlouva_full_entity_test_04", contract_4_vehicles_addresses),
        ("smlouva_full_entity_test_05", contract_5_mixed_all),
    ]
    for stem, fn in contracts:
        text = fn(r)
        path = write_docx(stem, text)
        print(f"Vytvořeno: {path.name}")


if __name__ == "__main__":
    main()
