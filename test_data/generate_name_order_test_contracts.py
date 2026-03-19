#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generuje 10 testovacích smluv s různými formáty jmen:
- Jan Novák (normální slovosled)
- Novák Jan (obrácený slovosled)
- Novák, Jan (obrácený s čárkou)
- Různé pády a tvary
"""

from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "test_data"

# Mužská jména – nominativ, genitiv, dativ, akuzativ, instrumentál
MALE_CASES = {
    "Jan Novák": {
        "nom": "Jan Novák",
        "gen": "Jana Nováka",
        "dat": "Janovi Novákovi",
        "acc": "Jana Nováka",
        "ins": "Janem Novákem",
    },
    "Pavel Dvořák": {
        "nom": "Pavel Dvořák",
        "gen": "Pavla Dvořáka",
        "dat": "Pavlovi Dvořákovi",
        "acc": "Pavla Dvořáka",
        "ins": "Pavlem Dvořákem",
    },
    "Tomáš Svoboda": {
        "nom": "Tomáš Svoboda",
        "gen": "Tomáše Svobody",
        "dat": "Tomášovi Svobodovi",
        "acc": "Tomáše Svobodu",
        "ins": "Tomášem Svobodou",
    },
}

# Ženská jména
FEMALE_CASES = {
    "Jana Nováková": {
        "nom": "Jana Nováková",
        "gen": "Jany Novákové",
        "dat": "Janě Novákové",
        "acc": "Janu Novákovou",
        "ins": "Janou Novákovou",
    },
    "Petra Svobodová": {
        "nom": "Petra Svobodová",
        "gen": "Petry Svobodové",
        "dat": "Petře Svobodové",
        "acc": "Petru Svobodovou",
        "ins": "Petrou Svobodovou",
    },
}

# Obrácené formáty (Příjmení Jméno, Příjmení, Jméno)
def reversed_nom(last: str, first: str) -> str:
    return f"{last} {first}"

def reversed_comma(last: str, first: str) -> str:
    return f"{last}, {first}"


def write_docx(stem: str, text: str) -> Path:
    docx_path = OUT_DIR / f"{stem}.docx"
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(docx_path)
    return docx_path


def main() -> None:
    contracts = []

    # 1. Normální slovosled – Jan Novák
    contracts.append(("smlouva_name_order_01", """
SMLOUVA O DÍLO – TEST JMÉNA 1

Smluvní strany:
1. Poskytovatel: Jan Novák
2. Příjemce: Jana Nováková

Smlouva uzavřena mezi Janem Novákem a Janou Novákovou.
Platba bude provedena na účet Jana Nováka.
"""))

    # 2. Obrácený slovosled – Novák Jan
    contracts.append(("smlouva_name_order_02", """
SMLOUVA O DÍLO – TEST JMÉNA 2

Smluvní strany:
1. Poskytovatel: Novák Jan
2. Příjemce: Nováková Jana

Smlouva uzavřena mezi Novákem Janem a Novákovou Janou.
Platba bude provedena na účet Nováka Jana.
"""))

    # 3. Obrácený s čárkou – Novák, Jan
    contracts.append(("smlouva_name_order_03", """
SMLOUVA O DÍLO – TEST JMÉNA 3

Smluvní strany:
1. Poskytovatel: Novák, Jan
2. Příjemce: Nováková, Jana

Smlouva uzavřena mezi Novákem, Janem a Novákovou, Janou.
Platba bude provedena na účet Nováka, Jana.
"""))

    # 4. Mix – normální + obrácený v jednom dokumentu
    contracts.append(("smlouva_name_order_04", """
SMLOUVA O POSKYTOVÁNÍ SLUŽEB

Kupující: Pavel Dvořák
Prodávající: Dvořák, Pavel (zastoupený jednatelem)

Předmět smlouvy mezi Pavlem Dvořákem a firmou zastoupenou Pavlem Dvořákem.
Kontakt: Dvořák Pavel, e-mail: dvorak@example.com
"""))

    # 5. Různé pády – genitiv, dativ, instrumentál
    contracts.append(("smlouva_name_order_05", """
PLNÁ MOC

Zastoupený: Tomáš Svoboda
Zastupující: Svoboda Tomáš

Plná moc udělena Tomášovi Svobodovi zastupovat Tomáše Svobodu.
Podpis Svobody Tomáše.
"""))

    # 6. Obrácený v různých pádech
    contracts.append(("smlouva_name_order_06", """
SMLOUVA O NÁJMU

Nájemce: Novák, Jan
Pronajímatel: Nováková, Jana

Nájemní smlouva mezi Novákem, Janem a Novákovou, Janou.
Platba od Nováka, Jana na účet Novákové, Jany.
"""))

    # 7. Tabulkový styl – jméno příjmení v záhlaví
    contracts.append(("smlouva_name_order_07", """
ZÁVAZNÁ PŘIHLÁŠKA

Účastník: Svoboda, Tomáš
Kontaktní osoba: Tomáš Svoboda

Potvrzujeme přijetí přihlášky od Svobody Tomáše.
Odpověď zasílejte Tomáši Svobodovi.
"""))

    # 8. Mix formátů v odstavcích
    contracts.append(("smlouva_name_order_08", """
SOUHLAS S OŠETŘENÍM

Pacient: Dvořáková, Petra
Lékař: Pavel Dvořák

Souhlas udělen Petrou Dvořákovou.
Ošetření provedl Dvořák Pavel.
Kontakt na příbuzného: Dvořák Pavel, tel. +420 777 123 456
"""))

    # 9. Seznam osob – různé formáty
    contracts.append(("smlouva_name_order_09", """
ČLENOVÉ PŘEDSTAVENSTVA

1. Jan Novák – předseda
2. Novák Pavel – místopředseda
3. Svobodová, Jana – členka
4. Tomáš Dvořák – člen
5. Dvořáková, Petra – členka

Smlouva podepsána všemi členy: Janem Novákem, Novákem Pavlem, Janou Svobodovou.
"""))

    # 10. Komplexní mix – všechny formáty
    contracts.append(("smlouva_name_order_10", """
SMLOUVA O SPOLUPRÁCI

Strana A: Marek Procházka
Strana B: Procházka, Marek (jednatel)

Pro Stranu A: Marek Procházka
Pro Stranu B: Procházka, Marek

Smlouva uzavřena mezi Markem Procházkou a Markem Procházkou (jednatelem).
Platba od Procházky Marka na účet Marka Procházky.
Kontakt: Procházka Marek, Procházka Marek – oba podepsáni níže.
"""))

    for stem, text in contracts:
        path = write_docx(stem, text.strip())
        print(f"Vytvořeno: {path.name}")

    print(f"\nCelkem: {len(contracts)} smluv")


if __name__ == "__main__":
    main()
