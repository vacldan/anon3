# -*- coding: utf-8 -*-
"""
Generuje 15 fiktivních smluv (smlouva_final_01 – smlouva_final_15).
Každá smlouva je 4–6 stran. Obsah pokrývá scénáře a entity, které
v předchozích generátorech nebyly — zahraniční jména, přezdívky,
vícenásobné adresy, RFID, SSH klíče, LinkedIn, datové schránky,
kombinované pádové varianty atd.
"""
from __future__ import annotations

import random
import unicodedata
from datetime import date
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "test_data"

# ───────── Nová jména (česká + mezinárodní mix) ─────────

MALE_FIRST = [
    "Vladimír", "Zbyněk", "Radek", "Lukáš", "Vojtěch",
    "Dominik", "Kryštof", "Sebastian", "Theodor", "Maxmilián",
    "Nguyen Duc", "Aleksandr", "Hans", "Giovanni", "Patrik",
]
FEMALE_FIRST = [
    "Kateřina", "Anežka", "Eliška", "Daniela", "Natálie",
    "Kristýna", "Žaneta", "Blanka", "Iveta", "Růžena",
    "Mai Linh", "Olga", "Ingrid", "Francesca", "Beáta",
]
MALE_LAST = [
    "Bártl", "Zeman", "Havlíček", "Šimek", "Dostál",
    "Kratochvíl", "Jandák", "Polák", "Nguyen", "Müller",
    "Horváth", "Petrov", "Rossi", "Kopecký", "Brož",
]
FEMALE_LAST = [
    "Bártlová", "Zemanová", "Havlíčková", "Šimková", "Dostálová",
    "Kratochvílová", "Jandáková", "Poláková", "Nguyenová", "Müllerová",
    "Horváthová", "Petrova", "Rossiová", "Kopecká", "Brožová",
]

# ───────── Nové ulice a adresy ─────────

STREETS = [
    ("Revoluční", "Praha 1", "110 00", "Staré Město"),
    ("Kolínská", "Praha 3", "130 00", "Vinohrady"),
    ("Čelakovského sady", "Praha 2", "120 00", "Nové Město"),
    ("Palackého", "Brno", "612 00", "Královo Pole"),
    ("Stodolní", "Ostrava", "702 00", "Moravská Ostrava"),
    ("Masarykovo náměstí", "Jihlava", "586 01", None),
    ("Pražská", "Plzeň", "301 00", None),
    ("Nádražní", "Frýdek-Místek", "738 01", None),
    ("Sokolovská", "Karlovy Vary", "360 01", None),
    ("Komenského", "Zlín", "760 01", None),
    ("Tyršova", "Pardubice", "530 02", None),
    ("Palackého třída", "Olomouc", "779 00", "Nová Ulice"),
]

COMPANIES = [
    ("CyberShield Technologies s.r.o.", "Revoluční 15, 110 00 Praha 1 - Staré Město", "15926837", "security@cybershield.cz", "+420 226 111 222"),
    ("Notářská kancelář JUDr. Helena Šťastná", "Kolínská 3, 130 00 Praha 3 - Vinohrady", "09182736", "notarka@stastna.cz", "+420 222 888 333"),
    ("Fakultní nemocnice Ostrava", "17. listopadu 1790/5, 702 00 Ostrava", "00843989", "podatelna@fno.cz", "+420 597 371 111"),
    ("Střední průmyslová škola stavební", "Pražská 55, 301 00 Plzeň", "48379212", "sekretariat@spss-plzen.cz", "+420 377 321 111"),
    ("Česká spořitelna a.s.", "Olbrachtova 1929/62, 140 00 Praha 4", "45244782", "info@csas.cz", "+420 800 207 207"),
    ("Exekutorský úřad Brno-město", "Palackého 28, 612 00 Brno - Královo Pole", "66240913", "podatelna@exekutor-brno.cz", "+420 541 235 678"),
    ("MedVet Klinika s.r.o.", "Masarykovo náměstí 7, 586 01 Jihlava", "27304501", "info@medvet-jihlava.cz", "+420 567 123 456"),
    ("Městská knihovna v Praze", "Mariánské náměstí 1, 115 72 Praha 1", "00064467", "info@mlp.cz", "+420 222 113 555"),
]


def strip_diacritics(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def rnd_phone(r: random.Random) -> str:
    return f"+420 {r.randint(600, 799)} {r.randint(100, 999):03d} {r.randint(100, 999):03d}"


def rnd_email(first: str, last: str, r: random.Random, domain: str | None = None) -> str:
    domains = ["email.cz", "seznam.cz", "gmail.com", "firma.cz", "post.cz"]
    d = domain or r.choice(domains)
    local = f"{first}.{last}".lower().replace(" ", ".")
    local = strip_diacritics(local)
    return f"{local}@{d}"


def rnd_birth_id(r: random.Random, female: bool = False) -> str:
    yy = r.choice([r.randint(55, 99), r.randint(0, 12)])
    mm = r.randint(1, 12) + (50 if female else 0)
    dd = r.randint(1, 28)
    suffix = r.randint(1000, 9999)
    return f"{yy:02d}{mm:02d}{dd:02d}/{suffix}"


def rnd_date(r: random.Random, start: int = 1955, end: int = 2005) -> str:
    y = r.randint(start, end)
    m = r.randint(1, 12)
    d = r.randint(1, 28)
    return f"{d}. {m}. {y}"


def rnd_address(r: random.Random) -> tuple[str, str | None]:
    street, city, psc, district = r.choice(STREETS)
    house = r.randint(1, 250)
    apt = r.randint(1, 50)
    addr = f"{street} {house}/{apt}, {psc} {city}"
    if district:
        addr += f" - {district}"
    return addr, district


def rnd_bank(r: random.Random) -> str:
    return f"{r.randint(100000000, 999999999)}/{r.choice(['0100', '0300', '5500', '0600', '0800', '2010', '6210'])}"


def rnd_iban(r: random.Random) -> str:
    bank = r.choice(["0100", "0300", "0600", "0800", "5500"])
    acct = f"{r.randint(0, 9999999999999999):016d}"
    return f"CZ{r.randint(10, 99)} {bank} 0000 {acct[:4]} {acct[4:8]} {acct[8:12]} {acct[12:16]}"


def rnd_mac(r: random.Random) -> str:
    return ":".join(f"{r.randint(0, 255):02X}" for _ in range(6))


def rnd_ip(r: random.Random) -> str:
    return f"{r.randint(10, 223)}.{r.randint(0, 255)}.{r.randint(0, 255)}.{r.randint(1, 254)}"


def rnd_spz(r: random.Random) -> str:
    return f"{r.choice(['1AB', '2AC', '5AZ', '7B8', '3AA', '4AP', '6SM', '8TU'])} {r.randint(1000, 9999)}"


def rnd_vin(r: random.Random) -> str:
    return f"TMBJP6NJ{r.randint(1, 9)}{r.choice(['L', 'M', 'N', 'P'])}{r.randint(100000, 999999)}"


def rnd_rfid(r: random.Random) -> str:
    return f"RFID:{r.randint(0xA0000000, 0xFFFFFFFF):08X}"


def rnd_ssh_key_fragment(r: random.Random) -> str:
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    body = "".join(r.choice(chars) for _ in range(40))
    return f"ssh-rsa AAAA{body}...truncated user@host"


def rnd_linkedin(r: random.Random, first: str, last: str) -> str:
    slug = strip_diacritics(f"{first}-{last}".lower().replace(" ", "-"))
    return f"https://www.linkedin.com/in/{slug}-{r.randint(100, 999)}"


def rnd_facebook(r: random.Random, first: str, last: str) -> str:
    slug = strip_diacritics(f"{first}.{last}".lower().replace(" ", "."))
    return f"https://www.facebook.com/{slug}.{r.randint(10, 99)}"


def rnd_instagram(r: random.Random, first: str) -> str:
    slug = strip_diacritics(first.lower().replace(" ", ""))
    return f"@{slug}_{r.randint(10, 99)}"


def rnd_data_box(r: random.Random) -> str:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(r.choice(chars) for _ in range(7))


def inflect_cz(first: str, last: str, female: bool) -> dict[str, str]:
    """Hrubá deklinace pro testování."""
    if female:
        fg = first[:-1] + "y" if first.endswith("a") else first
        fd = first[:-1] + "ě" if first.endswith("a") else first
        fi = first[:-1] + "ou" if first.endswith("a") else first
        fp = first[:-1] + "in" if first.endswith("a") else first + "in"
        lg = last[:-1] + "é" if last.endswith("á") else (last[:-3] + "ové" if last.endswith("ová") else last)
        ld = lg
        li = last[:-1] + "ou" if last.endswith("á") else (last[:-3] + "ovou" if last.endswith("ová") else last)
    else:
        fg = first + "a"
        fd = first + "ovi"
        fi = first + "em"
        fp = first + "ův"
        if first.endswith("el"):
            fg = first[:-2] + "la"
            fd = first[:-2] + "lovi"
            fi = first[:-2] + "lem"
        elif first.endswith("ek"):
            fg = first[:-2] + "ka"
            fd = first[:-2] + "kovi"
            fi = first[:-2] + "kem"
        lg = last + "a"
        ld = last + "ovi"
        li = last + "em"
        if last.endswith("ek"):
            lg = last[:-2] + "ka"
            ld = last[:-2] + "kovi"
            li = last[:-2] + "kem"
        elif last.endswith("ý"):
            lg = last[:-1] + "ého"
            ld = last[:-1] + "ému"
            li = last[:-1] + "ým"

    return {
        "nom": f"{first} {last}",
        "gen": f"{fg} {lg}",
        "dat": f"{fd} {ld}",
        "ins": f"{fi} {li}",
        "poss": fp,
    }


# ═══════════════════════════════════════════════════════════
# SMLOUVY 1–15: každá je unikátní scénář
# ═══════════════════════════════════════════════════════════

def gen_01_exekuce(r: random.Random) -> str:
    """Exekuční příkaz k srážkám ze mzdy — exekutor, povinný, oprávněný, zaměstnavatel."""
    ex = inflect_cz("Radek", "Dostál", False)
    pov = inflect_cz("Vladimír", "Šimek", False)
    opr = inflect_cz("Kateřina", "Bártlová", True)
    zam = "CyberShield Technologies s.r.o."
    return f"""EXEKUČNÍ PŘÍKAZ K PROVEDENÍ SRÁŽEK ZE MZDY
Č.j. 205 EX 1478/2026-45

Soudní exekutor {ex['nom']}, Exekutorský úřad Brno-město, se sídlem Palackého 28, 612 00 Brno - Královo Pole, IČO: 66240913, pověřený provedením exekuce na základě usnesení Okresního soudu v Brně ze dne 12. 1. 2026, č.j. 48 EXE 567/2026-8, vydává tento

EXEKUČNÍ PŘÍKAZ

I. Účastníci řízení

Oprávněná: {opr['nom']}, nar. {rnd_date(r)}, r.č. {rnd_birth_id(r, True)},
   bytem {rnd_address(r)[0]},
   telefon: {rnd_phone(r)}, e-mail: {rnd_email("Kateřina", "Bártlová", r)},
   zast. JUDr. Petrem Kopeckým, advokátem, sídlem Tyršova 44, 530 02 Pardubice,
   LinkedIn: {rnd_linkedin(r, "Petr", "Kopecký")}

Povinný: {pov['nom']}, nar. {rnd_date(r)}, r.č. {rnd_birth_id(r)},
   bytem {rnd_address(r)[0]},
   telefon: {rnd_phone(r)}, e-mail: {rnd_email("Vladimír", "Šimek", r)},
   číslo OP: {r.randint(100000000, 999999999)},
   číslo řidičského průkazu: EA {r.randint(100000, 999999)}

Plátce mzdy: {zam}, IČO: 15926837, sídlo: Revoluční 15, 110 00 Praha 1 - Staré Město,
   datová schránka: {rnd_data_box(r)}, e-mail: security@cybershield.cz

II. Předmět exekuce

Na základě pravomocného a vykonatelného rozsudku Okresního soudu v Brně ze dne 5. 11. 2025, sp. zn. 22 C 315/2025, jímž byla {pov['dat']} uložena povinnost zaplatit {opr['dat']} částku 185 000 Kč s příslušenstvím, nařizuje soudní exekutor provedení exekuce srážkami ze mzdy povinného {pov['gen']}.

III. Příkaz plátci mzdy

Plátce mzdy (zaměstnavatel) {zam} je povinen:
a) provádět ze mzdy povinného {pov['gen']} srážky v zákonem stanovené výši,
b) sražené částky zasílat na účet soudního exekutora č. {rnd_bank(r)}, IBAN: {rnd_iban(r)},
   variabilní symbol: 2051478026,
c) neprodleně oznámit exekutorovi, pokud povinný {pov['nom']} skončí pracovní poměr.

Plátce mzdy je povinen zaslat exekutorovi {ex['dat']} do 15 dnů vyúčtování čisté mzdy povinného za posledních 12 měsíců. Komunikace s exekutorem {ex['ins']} probíhá na e-mailu podatelna@exekutor-brno.cz a telefonně na +420 541 235 678.

IV. Pohledávka oprávněné

Celková dlužná částka: 185 000 Kč (jistina) + 18 500 Kč (úroky z prodlení) + 24 350 Kč (náklady oprávněné) + 31 200 Kč (náklady exekuce) = celkem 259 050 Kč.

Přeplatek bude vrácen {pov['dat']} na jeho účet č. {rnd_bank(r)}.

V. Poučení

Proti tomuto exekučnímu příkazu není přípustný opravný prostředek (§ 47 odst. 3 exekučního řádu). Povinný {pov['nom']} může podat návrh na zastavení exekuce, pokud jsou pro to důvody (§ 55 exekučního řádu).

Oprávněná {opr['nom']} a povinný {pov['nom']} mají právo nahlížet do exekučního spisu v kanceláři exekutora {ex['gen']} na adrese Palackého 28, 612 00 Brno - Královo Pole, v úředních hodinách.

VI. Doručení

Tento příkaz se doručuje:
1. {opr['dat']} — oprávněné
2. {pov['dat']} — povinnému
3. {zam} — plátci mzdy

V Brně dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

{ex['nom']}
Soudní exekutor
Exekutorský úřad Brno-město
e-mail: podatelna@exekutor-brno.cz
tel.: +420 541 235 678
"""


def gen_02_notarsky_zapis(r: random.Random) -> str:
    """Notářský zápis — kupní smlouva na nemovitost s vícero adresami."""
    not_name = inflect_cz("Blanka", "Zemanová", True)
    prod = inflect_cz("Lukáš", "Havlíček", False)
    kup = inflect_cz("Anežka", "Kratochvílová", True)
    kup2 = inflect_cz("Dominik", "Kratochvíl", False)
    addr_nem = "Kolínská 42/7, 130 00 Praha 3 - Vinohrady"
    addr_prod = rnd_address(r)[0]
    addr_kup = rnd_address(r)[0]
    return f"""NOTÁŘSKÝ ZÁPIS
NZ 245/2026, N 312/2026

Sepsaný dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026 v notářské kanceláři JUDr. {not_name['nom']}, notářky se sídlem Kolínská 3, 130 00 Praha 3 - Vinohrady, IČO: 09182736, e-mail: notarka@stastna.cz, datová schránka: {rnd_data_box(r)}.

PŘEDE MNOU, notářkou {not_name['ins']}, se dostavili:

1. Prodávající: {prod['nom']}
   Narozen: {rnd_date(r)}
   Rodné číslo: {rnd_birth_id(r)}
   Trvalý pobyt: {addr_prod}
   Číslo občanského průkazu: {r.randint(100000000, 999999999)}
   Telefon: {rnd_phone(r)}
   E-mail: {rnd_email("Lukáš", "Havlíček", r)}
   Bankovní účet: {rnd_bank(r)}
   IBAN: {rnd_iban(r)}
   
   jehož totožnost jsem ověřila z občanského průkazu,

2. Kupující — manželé:
   a) {kup['nom']}
      Narozena: {rnd_date(r)}
      Rodné číslo: {rnd_birth_id(r, True)}
      Trvalý pobyt: {addr_kup}
      Číslo občanského průkazu: {r.randint(100000000, 999999999)}
      Telefon: {rnd_phone(r)}
      E-mail: {rnd_email("Anežka", "Kratochvílová", r)}

   b) {kup2['nom']}
      Narozen: {rnd_date(r)}
      Rodné číslo: {rnd_birth_id(r)}
      Trvalý pobyt: {addr_kup}
      Číslo OP: {r.randint(100000000, 999999999)}
      Telefon: {rnd_phone(r)}
      E-mail: {rnd_email("Dominik", "Kratochvíl", r)}

   jejichž totožnost jsem ověřila z občanských průkazů,

a uzavírají tuto

KUPNÍ SMLOUVU

I. Předmět převodu

Prodávající {prod['nom']} je výlučným vlastníkem bytové jednotky č. 42/7 v budově na adrese {addr_nem}, zapsané na LV 1234 v katastrálním území Vinohrady, obec Praha, okres Hlavní město Praha. Součástí převodu je spoluvlastnický podíl na společných částech domu ve výši 68/1000 a garážové stání č. 12.

II. Kupní cena a platební podmínky

Smluvní strany sjednaly kupní cenu ve výši 6 850 000 Kč (slovy: šest milionů osm set padesát tisíc korun českých).

Úhrada kupní ceny:
- Záloha 685 000 Kč — uhrazena na účet prodávajícího {prod['gen']} č. {rnd_bank(r)} do 7 dnů,
- Doplatek 6 165 000 Kč — složen do notářské úschovy u notářky {not_name['gen']} na účet č. {rnd_bank(r)}, IBAN: {rnd_iban(r)}.

Notářka {not_name['nom']} vyplatí doplatek prodávajícímu {prod['dat']} do 5 pracovních dnů po zápisu vlastnického práva kupujících {kup['gen']} a {kup2['gen']} do katastru nemovitostí.

III. Prohlášení smluvních stran

Prodávající {prod['nom']} prohlašuje, že bytová jednotka není zatížena zástavním právem, věcným břemenem ani jinými právy třetích osob. {prod['poss']} nemovitost nebyla předmětem restitučního řízení.

Kupující {kup['nom']} a {kup2['nom']} prohlašují, že nabývají nemovitost do společného jmění manželů.

IV. Intabulační doložka

Smluvní strany souhlasí s tím, aby na základě této smlouvy katastrální úřad zapsal:
- výmaz vlastnického práva {prod['gen']},
- vklad vlastnického práva ve prospěch {kup['gen']} a {kup2['gen']}.

V. Daňové povinnosti

Kupující hradí daň z nabytí nemovité věci. Prodávající {prod['nom']} příjmy z prodeje uvede v daňovém přiznání (IČO: neuvádí, DIČ: CZ{rnd_birth_id(r).replace('/', '')[:10]}).

VI. Odpovědnost za vady a předání

Prodávající {prod['nom']} předá klíče kupujícím {kup['dat']} a {kup2['dat']} nejpozději do 30 dnů od zápisu vlastnického práva. Předání bude potvrzeno předávacím protokolem s fotografickou dokumentací.

Kontakt na správce domu: Správa bytů Vinohrady s.r.o., IČO: {r.randint(10000000, 99999999)}, e-mail: sprava@svvinohrady.cz, tel.: {rnd_phone(r)}.

VII. Závěrečná ustanovení

Tento notářský zápis byl sepsán v jednom vyhotovení a schválen. Listiny ověřené notářkou {not_name['ins']} se ukládají v notářském archivu.

Účastníci prohlašují, že jim byl zápis přečten, souhlasí s jeho obsahem a na důkaz toho připojují své podpisy.

.............................     .............................     .............................
{prod['nom']}                  {kup['nom']}                  {kup2['nom']}
  (prodávající)                   (kupující)                    (kupující)

Ověřila: JUDr. {not_name['nom']}, notářka
Notářská kancelář, Kolínská 3, 130 00 Praha 3 - Vinohrady
Tel.: +420 222 888 333, e-mail: notarka@stastna.cz
"""


def gen_03_nemocnice_souhlas(r: random.Random) -> str:
    """Informovaný souhlas ve FN Ostrava — zdravotní údaje, RFID badge, ošetřující lékaři."""
    pac = inflect_cz("Růžena", "Horváthová", True)
    lek1 = inflect_cz("Sebastian", "Polák", False)
    lek2 = inflect_cz("Natálie", "Nguyenová", True)
    zk = inflect_cz("Vojtěch", "Kopecký", False)
    return f"""INFORMOVANÝ SOUHLAS PACIENTA S HOSPITALIZACÍ A OPERAČNÍM VÝKONEM

Fakultní nemocnice Ostrava, 17. listopadu 1790/5, 702 00 Ostrava - Moravská Ostrava
IČO: 00843989, datová schránka: {rnd_data_box(r)}
Oddělení: Kardiochirurgická klinika, 4. patro

I. Identifikace pacienta

Jméno a příjmení: {pac['nom']}
Datum narození: {rnd_date(r, 1945, 1975)}
Rodné číslo: {rnd_birth_id(r, True)}
Pojišťovna: VZP ČR (111)
Číslo pojištěnce: {r.randint(1000000000, 9999999999)}
Trvalý pobyt: {rnd_address(r)[0]}
Kontaktní adresa: {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Růžena", "Horváthová", r)}
RFID identifikátor pacienta: {rnd_rfid(r)}

Kontaktní osoba (manžel): {zk['nom']}, tel.: {rnd_phone(r)}, e-mail: {rnd_email("Vojtěch", "Kopecký", r)}

II. Ošetřující tým

Operatér: doc. MUDr. {lek1['nom']}, Ph.D., FESC
   Telefon: {rnd_phone(r)}
   E-mail: {rnd_email("Sebastian", "Polák", r, "fno.cz")}
   RFID badge: {rnd_rfid(r)}

Anesteziolog: MUDr. {lek2['nom']}
   Telefon: {rnd_phone(r)}
   E-mail: {rnd_email("Natálie", "Nguyenová", r, "fno.cz")}
   RFID badge: {rnd_rfid(r)}

III. Diagnóza a navrhovaný výkon

Pacientce {pac['dat']} byla diagnostikována těžká aortální stenóza (dg. I35.0) s projevy srdečního selhání (NYHA III). Na základě echokardiografického vyšetření a koronarografie je indikován chirurgický zákrok — náhrada aortální chlopně biologickou protézou (kód výkonu: 5-351.01).

Doktor {lek1['nom']} vysvětlil pacientce {pac['dat']} podstatu zákroku, alternativy (TAVI, konzervativní léčba) a možné komplikace: krvácení, infekce, arytmie, tromboembolická příhoda, v extrémním případě úmrtí.

IV. Farmakoterapie

Pacientka {pac['nom']} užívá: Warfarin 5 mg 1-0-0, Bisoprolol 2,5 mg 1-0-0, Furosemid 40 mg 1-0-0, Ramipril 5 mg 0-0-1. Alergie: Penicilin, Jód (kontrastní látka). Krevní skupina: A Rh+.

V. Prohlášení pacienta

Já, {pac['nom']}, prohlašuji, že jsem byla doktorem {lek1['ins']} srozumitelně informována o:
- diagnóze a jejím vývoji,
- navrhovaném operačním výkonu a jeho průběhu,
- možných rizicích a komplikacích,
- alternativních postupech léčby,
- předpokládané délce hospitalizace (7–14 dnů).

Na mé otázky bylo {lek1['ins']} a doktorkou {lek2['ins']} odpovězeno.

Pacientka {pac['nom']} souhlasí s předáním zdravotnické dokumentace {pac['gen']} pojišťovně VZP ČR pro účely úhrady péče a případným konzultacím s dalšími specialisty FN Ostrava.

VI. Kontaktní osoba pro případ nouze

V případě komplikací kontaktujte manžela {zk['gen']}, tel.: {rnd_phone(r)}. Manžel {zk['nom']} je oprávněn přijímat informace o zdravotním stavu {pac['gen']}.

VII. Souhlas s nakládáním s osobními a zdravotními údaji

Pacientka {pac['nom']} souhlasí se zpracováním osobních a zdravotních údajů v nemocničním informačním systému FN Ostrava v rozsahu nezbytném pro poskytování zdravotní péče. RFID identifikátor {pac['gen']} bude používán po dobu hospitalizace pro identifikaci při podávání léků a při transportu na operační sál.

V Ostravě dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................          .............................
{pac['nom']}                        doc. MUDr. {lek1['nom']}, Ph.D.
  (pacientka)                           (operatér)
"""


def gen_04_kyberneticka_bezpecnost(r: random.Random) -> str:
    """Smlouva o penetračním testování — SSH klíče, IP, MAC, uživatelské účty."""
    ob = inflect_cz("Theodor", "Brož", False)
    zhotov = inflect_cz("Patrik", "Müller", False)
    return f"""SMLOUVA O PROVEDENÍ PENETRAČNÍHO TESTU A BEZPEČNOSTNÍHO AUDITU

uzavřená dle § 2586 a násl. zákona č. 89/2012 Sb., občanský zákoník

I. Smluvní strany

Objednatel:
CyberShield Technologies s.r.o.
Sídlo: Revoluční 15, 110 00 Praha 1 - Staré Město
IČO: 15926837, DIČ: CZ15926837
Datová schránka: {rnd_data_box(r)}
Jednající: {ob['nom']}, CTO
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Theodor", "Brož", r, "cybershield.cz")}
LinkedIn: {rnd_linkedin(r, "Theodor", "Brož")}

Zhotovitel:
Ing. {zhotov['nom']}, OSCP, CEH
IČO: {r.randint(10000000, 99999999)}
Sídlo: {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Patrik", "Müller", r, "pentester.cz")}
Bankovní účet: {rnd_bank(r)}
IBAN: {rnd_iban(r)}
LinkedIn: {rnd_linkedin(r, "Patrik", "Müller")}
Facebook: {rnd_facebook(r, "Patrik", "Müller")}

II. Předmět smlouvy

Zhotovitel {zhotov['nom']} provede pro objednatele komplexní penetrační test vnější a vnitřní infrastruktury, včetně:
a) Testování webových aplikací (OWASP Top 10)
b) Testování síťové infrastruktury
c) Testování Wi-Fi sítí
d) Social engineering (phishing simulace)

III. Rozsah testování — technické údaje

Cílové IP adresy (scope):
- Produkční: {rnd_ip(r)}, {rnd_ip(r)}, {rnd_ip(r)}
- Testovací: {rnd_ip(r)}, {rnd_ip(r)}
- IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334

Doménové názvy:
- cybershield.cz, app.cybershield.cz, vpn.cybershield.cz, mail.cybershield.cz

MAC adresy síťových prvků:
- Firewall: {rnd_mac(r)}
- Core switch: {rnd_mac(r)}
- AP kancelář: {rnd_mac(r)}

Testovací účty poskytnuté objednatelem:
- Admin: username: test_admin, heslo: T3stAdm!n2026
- Uživatel: username: test_user, heslo: Us3r@Pass99
- API klíč pro REST API: sk-test-{r.randint(10000000, 99999999)}-{r.randint(10000000, 99999999)}

SSH klíč zhotovitele pro vzdálený přístup:
{rnd_ssh_key_fragment(r)}

IV. Časový harmonogram

Zahájení: {r.randint(1, 15)}. {r.randint(3, 6)}. 2026
Ukončení testů: {r.randint(16, 28)}. {r.randint(3, 6)}. 2026
Předání zprávy: do 10 pracovních dnů od ukončení testů

Testy budou prováděny v časovém okně 22:00–06:00 CET (mimo provozní špičku). Zhotovitel {zhotov['nom']} zajistí, že testování nenaruší provoz produkčních systémů.

V. Odměna

Celková odměna: 280 000 Kč bez DPH (339 800 Kč vč. DPH).
Platba na účet zhotovitele {zhotov['gen']} č. {rnd_bank(r)}, VS: 2026001.

VI. Mlčenlivost a ochrana údajů

Zhotovitel {zhotov['nom']} se zavazuje:
a) Nepředávat zjištěné informace třetím osobám,
b) Po ukončení zakázky bezpečně smazat veškeré testovací přístupy a záznamy,
c) Zprávu o testování předat výhradně {ob['dat']} nebo jím pověřené osobě,
d) Neuchovávat SSH klíče, hesla ani API klíče po skončení zakázky.

Komunikace mezi {ob['ins']} a {zhotov['ins']} bude probíhat šifrovaným kanálem (PGP/Signal).

V Praze dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................          .............................
{ob['nom']}                          Ing. {zhotov['nom']}
CyberShield Technologies s.r.o.       Zhotovitel
"""


def gen_05_skolni_matrika(r: random.Random) -> str:
    """Zápis do školní matriky — nezletilý žák, zákonní zástupci, zdravotní údaje."""
    zak = inflect_cz("Kryštof", "Jandák", False)
    mat = inflect_cz("Eliška", "Jandáková", True)
    ot = inflect_cz("Zbyněk", "Jandák", False)
    ucitel = inflect_cz("Daniela", "Šimková", True)
    return f"""ZÁPIS DO ŠKOLNÍ MATRIKY — PŘIHLÁŠKA K ZÁKLADNÍMU VZDĚLÁVÁNÍ

Střední průmyslová škola stavební, Pražská 55, 301 00 Plzeň
IČO: 48379212, datová schránka: {rnd_data_box(r)}
e-mail: sekretariat@spss-plzen.cz, tel.: +420 377 321 111

I. Údaje o žákovi

Jméno a příjmení: {zak['nom']}
Datum narození: {rnd_date(r, 2009, 2012)}
Rodné číslo: {rnd_birth_id(r)}
Místo narození: Plzeň
Státní občanství: české
Zdravotní pojišťovna: ČPZP (205)
Číslo pojištěnce: {r.randint(1000000000, 9999999999)}
Trvalý pobyt: {rnd_address(r)[0]}
Kontaktní telefon žáka: {rnd_phone(r)}
E-mail žáka: {rnd_email("Kryštof", "Jandák", r, "student.spss-plzen.cz")}

Zdravotní omezení: astma bronchiale, alergie na roztoče
Užívané léky: Ventolin inhaler dle potřeby

II. Zákonní zástupci

Matka:
   Jméno a příjmení: {mat['nom']}
   Datum narození: {rnd_date(r, 1975, 1990)}
   Rodné číslo: {rnd_birth_id(r, True)}
   Trvalý pobyt: {rnd_address(r)[0]}
   Telefon: {rnd_phone(r)}
   E-mail: {rnd_email("Eliška", "Jandáková", r)}
   Zaměstnavatel: MedVet Klinika s.r.o., IČO: 27304501

Otec:
   Jméno a příjmení: {ot['nom']}
   Datum narození: {rnd_date(r, 1975, 1990)}
   Rodné číslo: {rnd_birth_id(r)}
   Trvalý pobyt: {rnd_address(r)[0]}
   Telefon: {rnd_phone(r)}
   E-mail: {rnd_email("Zbyněk", "Jandák", r)}
   Zaměstnavatel: Škoda Auto a.s., IČO: 00177041

III. Údaje pro školní informační systém (Bakaláři)

Přihlašovací údaje zákonného zástupce:
   Username: {mat['nom'].split()[0][0].lower()}.{strip_diacritics(mat['nom'].split()[1]).lower()}
   Počáteční heslo: Skola2026!{r.randint(10, 99)}

Žákovský RFID čip: {rnd_rfid(r)} (pro docházku a stravování)

IV. Souhlas se zpracováním osobních údajů

Zákonní zástupci {mat['nom']} a {ot['nom']} souhlasí se zpracováním osobních údajů žáka {zak['gen']} a svých vlastních údajů v rozsahu nezbytném pro:
a) vedení školní matriky (zákon č. 561/2004 Sb.),
b) komunikaci prostřednictvím školního informačního systému Bakaláři,
c) evidence docházky prostřednictvím RFID čipu,
d) evidence stravování ve školní jídelně,
e) případného kontaktování zákonných zástupců v akutních zdravotních situacích.

Matka {mat['nom']} a otec {ot['nom']} berou na vědomí, že údaje budou zpracovávány po dobu studia žáka {zak['gen']} a následně archivovány dle spisového a skartačního řádu školy.

V. Třídní učitelka

{ucitel['nom']}, kabinet 205, tel.: {rnd_phone(r)}, e-mail: {rnd_email("Daniela", "Šimková", r, "spss-plzen.cz")}
Instagram školy: @spss_plzen_official
Facebook: https://www.facebook.com/spssplzen

VI. Podpisy

V Plzni dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................     .............................     .............................
{mat['nom']}                   {ot['nom']}                    {ucitel['nom']}
  (matka / zákonný zástupce)      (otec / zákonný zástupce)       (třídní učitelka)
"""


def gen_06_pojistna_udalost(r: random.Random) -> str:
    """Hlášení pojistné události — dopravní nehoda, SPZ, VIN, řidičák, svědci."""
    poj = inflect_cz("Maxmilián", "Bártl", False)
    vin2 = inflect_cz("Iveta", "Dostálová", True)
    sved = inflect_cz("Giovanni", "Rossi", False)
    return f"""HLÁŠENÍ POJISTNÉ UDÁLOSTI — DOPRAVNÍ NEHODA

Česká spořitelna pojišťovna a.s.
Olbrachtova 1929/62, 140 00 Praha 4
IČO: 45244782

Číslo pojistné smlouvy: 9876543210
Číslo pojistné události: PU-2026-{r.randint(10000, 99999)}

I. Pojistník (pojištěný)

Jméno a příjmení: {poj['nom']}
Datum narození: {rnd_date(r)}
Rodné číslo: {rnd_birth_id(r)}
Trvalý pobyt: {rnd_address(r)[0]}
Korespondenční adresa: {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Maxmilián", "Bártl", r)}
Číslo OP: {r.randint(100000000, 999999999)}
Číslo řidičského průkazu: EA {r.randint(100000, 999999)}
Bankovní účet pro výplatu pojistného plnění: {rnd_bank(r)}

II. Pojištěné vozidlo

Značka a model: Škoda Octavia Combi 2.0 TDI
SPZ: {rnd_spz(r)}
VIN: {rnd_vin(r)}
Barva: tmavě modrá metalíza
Rok výroby: 2022

III. Popis nehody

Dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026 v {r.randint(6, 22)}:{r.choice(['00', '15', '30', '45'])} hodin došlo na křižovatce ulic Sokolovská a Táborská v Karlových Varech ({rnd_ip(r)} — GPS: 50.2297N, 12.8714E) ke střetu vozidla pojistníka {poj['gen']} s vozidlem protistrany.

Řidič pojištěného vozidla: {poj['nom']}
Řidič protistrany: {vin2['nom']}, nar. {rnd_date(r)}, r.č. {rnd_birth_id(r, True)},
   bytem {rnd_address(r)[0]}, tel.: {rnd_phone(r)},
   e-mail: {rnd_email("Iveta", "Dostálová", r)},
   SPZ protistrany: {rnd_spz(r)}, VIN: {rnd_vin(r)},
   řidičský průkaz: EA {r.randint(100000, 999999)},
   pojišťovna protistrany: Allianz pojišťovna a.s., č. smlouvy: {r.randint(1000000000, 9999999999)}

IV. Svědek nehody

{sved['nom']}, nar. {rnd_date(r)}, tel.: {rnd_phone(r)}, e-mail: {rnd_email("Giovanni", "Rossi", r)}
Adresa: {rnd_address(r)[0]}

Svědek {sved['nom']} potvrdil, že vozidlo {vin2['gen']} vjelo do křižovatky na červenou. S {sved['ins']} se lze spojit telefonicky.

V. Rozsah poškození

Vozidlo {poj['gen']} (SPZ {rnd_spz(r)}): poškozený přední nárazník, levý blatník, levý světlomet. Předběžný odhad škody: 78 000 Kč.
Vozidlo protistrany {vin2['gen']}: poškozený pravý bok, zrcátko. Odhad: 45 000 Kč.

VI. Zranění

Pojistník {poj['nom']}: lehké poranění krční páteře (whiplash), ošetřen v Karlovarské krajské nemocnici.
{vin2['nom']}: bez zranění.

VII. Policejní protokol

Nehoda šetřena PČR, Dopravní inspektorát Karlovy Vary, č.j. KRPK-{r.randint(10000, 99999)}/ČJ-2026-{r.randint(100, 999)}.

VIII. Přílohy

1. Kopie řidičského průkazu {poj['gen']}
2. Kopie OP {poj['gen']}
3. Fotodokumentace (12 fotografií)
4. Lékařská zpráva — {poj['nom']}
5. Policejní protokol

Pojistník {poj['nom']} žádá o výplatu pojistného plnění na účet č. {rnd_bank(r)}.

V Karlových Varech dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................
{poj['nom']}
(pojistník)
"""


def gen_07_darovaci_smlouva(r: random.Random) -> str:
    """Darovací smlouva — vysoká částka, více svědků, přezdívky v textu."""
    darce = inflect_cz("Hans", "Müller", False)
    obdar = inflect_cz("Kristýna", "Petrova", True)
    sved1 = inflect_cz("Aleksandr", "Petrov", False)
    sved2 = inflect_cz("Mai Linh", "Nguyenová", True)
    return f"""DAROVACÍ SMLOUVA

uzavřená dle § 2055 a násl. zákona č. 89/2012 Sb., občanský zákoník

I. Smluvní strany

Dárce:
{darce['nom']}
Datum narození: {rnd_date(r, 1950, 1970)}
Rodné číslo: {rnd_birth_id(r)}
Státní občanství: české (naturalizován)
Trvalý pobyt: {rnd_address(r)[0]}
Kontaktní adresa: {rnd_address(r)[0]}
Číslo pasu: CZ{r.randint(1000000, 9999999)}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Hans", "Müller", r)}
Bankovní účet: {rnd_bank(r)}, IBAN: {rnd_iban(r)}
Datová schránka: {rnd_data_box(r)}

(dále jen „Dárce" nebo „pan {darce['nom'].split()[0]}")

Obdarovaná:
{obdar['nom']}
Datum narození: {rnd_date(r, 1990, 2002)}
Rodné číslo: {rnd_birth_id(r, True)}
Trvalý pobyt: {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Kristýna", "Petrova", r)}
Instagram: {rnd_instagram(r, "Kristýna")}
Bankovní účet: {rnd_bank(r)}
IBAN: {rnd_iban(r)}

(dále jen „Obdarovaná" nebo „Kristýna")

II. Předmět daru

Dárce {darce['nom']} daruje obdarované {obdar['dat']} finanční prostředky ve výši 2 500 000 Kč (slovy: dva miliony pět set tisíc korun českých) za účelem financování studia MBA na Univerzitě Karlově.

III. Podmínky darování

1. Částka bude převedena z účtu dárce {darce['gen']} (IBAN: {rnd_iban(r)}) na účet obdarované {obdar['gen']} do 30 dnů od podpisu.
2. Pan {darce['nom'].split()[0]} si vyhrazuje právo odvolat dar, pokud obdarovaná {obdar['nom']} neukončí první ročník studia MBA.
3. Obdarovaná Kristýna se zavazuje předložit dárci {darce['dat']} potvrzení o zápisu do studia.

IV. Prohlášení smluvních stran

Dárce {darce['nom']} prohlašuje, že dar poskytuje dobrovolně a bez nátlaku. Finanční prostředky pocházejí z legálních zdrojů (úspory, příjmy z podnikání — IČO: {r.randint(10000000, 99999999)}).

Obdarovaná {obdar['nom']} dar s vděčností přijímá a zavazuje se jej využít výhradně pro studijní účely.

V. Svědci

1. {sved1['nom']} (otec obdarované)
   Nar.: {rnd_date(r, 1960, 1980)}, r.č.: {rnd_birth_id(r)}
   Bytem: {rnd_address(r)[0]}
   Tel.: {rnd_phone(r)}

2. {sved2['nom']}
   Nar.: {rnd_date(r, 1985, 1995)}, r.č.: {rnd_birth_id(r, True)}
   Bytem: {rnd_address(r)[0]}
   Tel.: {rnd_phone(r)}
   E-mail: {rnd_email("Mai Linh", "Nguyenová", r)}

Svědkyně {sved2['nom']} potvrzuje, že byla přítomna podpisu smlouvy a obě strany jednaly svobodně. Se svědkyní {sved2['ins']} lze komunikovat na uvedeném e-mailu.

VI. Daňové důsledky

Dar je od daně z příjmů osvobozen dle § 10 odst. 3 písm. c) zákona o daních z příjmů, neboť obdarovaná {obdar['nom']} je dcerou svědka {sved1['gen']}, který je zetěm dárce {darce['gen']}.

VII. Závěrečná ustanovení

Smlouva nabývá platnosti dnem podpisu. Vztah mezi dárcem {darce['ins']} a obdarovanou {obdar['ins']} se řídí občanským zákoníkem.

V Praze dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................     .............................
{darce['nom']}                  {obdar['nom']}
  (dárce)                         (obdarovaná)

Svědci:
.............................     .............................
{sved1['nom']}                  {sved2['nom']}
"""


def gen_08_pracovni_smlouva_cizinec(r: random.Random) -> str:
    """Pracovní smlouva s cizincem — číslo víza, přechodný pobyt, zahraniční jména."""
    zam = inflect_cz("Nguyen Duc", "Nguyen", False)
    vedouci = inflect_cz("Radek", "Kratochvíl", False)
    hr = inflect_cz("Žaneta", "Poláková", True)
    return f"""PRACOVNÍ SMLOUVA

uzavřená dle zákona č. 262/2006 Sb., zákoník práce

I. Smluvní strany

Zaměstnavatel:
CyberShield Technologies s.r.o.
Sídlo: Revoluční 15, 110 00 Praha 1 - Staré Město
IČO: 15926837, DIČ: CZ15926837

Jednající: {vedouci['nom']}, CEO
Kontakt HR: {hr['nom']}, HR managerka
   Tel.: {rnd_phone(r)}, e-mail: {rnd_email("Žaneta", "Poláková", r, "cybershield.cz")}
   LinkedIn: {rnd_linkedin(r, "Žaneta", "Poláková")}

(dále jen „Zaměstnavatel")

Zaměstnanec:
{zam['nom']}
Datum narození: {rnd_date(r, 1988, 2000)}
Rodné číslo: {rnd_birth_id(r)}
Státní občanství: vietnamské
Číslo pasu: N{r.randint(10000000, 99999999)}
Číslo povolení k pobytu (zaměstnanecká karta): ZK-{r.randint(100000, 999999)}/CZ
Trvalý pobyt (Vietnam): 45 Tran Phu Street, Hanoi
Přechodný pobyt (ČR): {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Nguyen Duc", "Nguyen", r)}
Bankovní účet (ČR): {rnd_bank(r)}
IBAN: {rnd_iban(r)}
Zdravotní pojišťovna: VZP ČR (111)
Číslo pojištěnce: {r.randint(1000000000, 9999999999)}
LinkedIn: {rnd_linkedin(r, "Nguyen Duc", "Nguyen")}

(dále jen „Zaměstnanec")

II. Druh práce

Zaměstnanec {zam['nom']} bude vykonávat práci na pozici: Senior Software Developer.
Místo výkonu práce: Revoluční 15, 110 00 Praha 1 - Staré Město (s možností home-office).

III. Den nástupu a doba trvání

Nástup: 1. {r.randint(3, 9)}. 2026
Doba: neurčitá se zkušební dobou 3 měsíce

IV. Mzdové podmínky

Základní mzda: 85 000 Kč hrubého měsíčně
Osobní ohodnocení: až 15 000 Kč
Bonusy: roční výkonnostní bonus až 100 000 Kč
Stravenkový paušál: 2 000 Kč/měsíc
Sick days: 5 dní

Mzda bude zasílána na účet zaměstnance {zam['gen']} č. {rnd_bank(r)} do 15. dne následujícího měsíce.

V. Přístupové a identifikační údaje

Po nástupu bude zaměstnanci {zam['dat']} přidělen:
- Firemní e-mail: nguyen.duc@cybershield.cz
- Username: nguyend
- Počáteční heslo: Cy8er!{r.randint(1000, 9999)}
- RFID badge: {rnd_rfid(r)}
- SSH klíč pro přístup k serverům: {rnd_ssh_key_fragment(r)}
- VPN certifikát bude odeslán na e-mail zaměstnance {zam['gen']}

Vedoucí {vedouci['nom']} přidělí zaměstnanci {zam['dat']} mentor/buddy z týmu.

VI. Pracovní povinnosti a ochrana údajů

Zaměstnanec {zam['nom']} se zavazuje:
a) dodržovat vnitřní předpisy zaměstnavatele,
b) zachovávat mlčenlivost o obchodních informacích,
c) nešířit přístupové údaje (hesla, SSH klíče, API klíče),
d) hlásit bezpečnostní incidenty HR manažerce {hr['dat']} nebo vedoucímu {vedouci['dat']}.

VII. Souhlas se zpracováním osobních údajů

Zaměstnanec {zam['nom']} souhlasí se zpracováním osobních údajů v rozsahu: jméno, datum narození, rodné číslo, číslo pasu, číslo zaměstnanecké karty, adresa přechodného i trvalého bydliště, telefon, e-mail, bankovní údaje, RFID badge, fotografie pro ID kartu.

Údaje budou zpracovávány po dobu trvání pracovního poměru a poté archivovány dle zákona.

VIII. Závěrečná ustanovení

Smlouva je vyhotovena ve dvou exemplářích v českém jazyce. Zaměstnanec {zam['nom']} potvrzuje, že rozumí českému textu smlouvy.

V Praze dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................          .............................
{vedouci['nom']}                     {zam['nom']}
CyberShield Technologies s.r.o.       (zaměstnanec)

Za HR:
.............................
{hr['nom']}
HR managerka
"""


def gen_09_medicinska_studie(r: random.Random) -> str:
    """Informovaný souhlas s účastí v klinické studii — detailní zdravotní data, API klíč pro datový portál."""
    pac = inflect_cz("Beáta", "Kopecká", True)
    lek = inflect_cz("Vojtěch", "Zeman", False)
    koordin = inflect_cz("Francesca", "Rossiová", True)
    return f"""INFORMOVANÝ SOUHLAS S ÚČASTÍ V KLINICKÉ STUDII

Název studie: CARDIO-CZ-2026 — Randomizovaná dvojitě zaslepená studie účinnosti přípravku XR-450 u pacientů s fibrilací síní
Identifikátor studie: EudraCT 2026-000{r.randint(100, 999)}-{r.randint(10, 99)}
Hlavní zkoušející: prof. MUDr. {lek['nom']}, CSc.
Centrum: Fakultní nemocnice Ostrava, 17. listopadu 1790/5, 702 00 Ostrava - Moravská Ostrava
Etická komise: schválení č. EK-{r.randint(100, 999)}/2026

I. Identifikace účastnice studie

Jméno a příjmení: {pac['nom']}
Datum narození: {rnd_date(r, 1955, 1975)}
Rodné číslo: {rnd_birth_id(r, True)}
Trvalý pobyt: {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Beáta", "Kopecká", r)}
Zdravotní pojišťovna: OZP (207)
Číslo pojištěnce: {r.randint(1000000000, 9999999999)}

II. Zdravotní anamnéza účastnice

Diagnózy: Fibrilace síní (I48.0), Arteriální hypertenze (I10), Diabetes mellitus 2. typu (E11.9), Hypothyreóza (E03.9)
Farmakoterapie:
  - Eliquis 5 mg 1-0-1
  - Metformin 1000 mg 1-0-1
  - Euthyrox 75 μg 1-0-0
  - Bisoprolol 5 mg 1-0-0
Alergie: Sulfonamidy, latex
Krevní skupina: 0 Rh−
BMI: 28,3

Pacientce {pac['dat']} bylo vysvětleno, že dosavadní léčba fibrilace síní není dostatečně účinná a studie nabízí alternativní přístup.

III. Průběh studie

Účastnice {pac['nom']} bude randomizována do jedné ze dvou skupin:
- Skupina A: přípravek XR-450 (200 mg 2× denně)
- Skupina B: placebo

Doba trvání: 12 měsíců. Kontrolní návštěvy: měsíčně v centru FN Ostrava.

Koordinátorka studie: {koordin['nom']}
   Tel.: {rnd_phone(r)}
   E-mail: {rnd_email("Francesca", "Rossiová", r, "fno.cz")}

Pro zadávání dat do elektronického CRF bude {pac['dat']} přidělen:
   Portál: https://edc.cardio-cz-2026.eu
   ID účastnice: PAT-{r.randint(1000, 9999)}
   API klíč pro datový export: sk-study-{r.randint(10000000, 99999999)}

IV. Rizika a komplikace

Prof. MUDr. {lek['nom']}, CSc. informoval pacientku {pac['gen']} o možných nežádoucích účincích: bolest hlavy, nauzea, krvácení, kožní vyrážka. V případě závažných komplikací kontaktujte doktora {lek['gen']} na tel. {rnd_phone(r)} nebo koordinátorku {koordin['gen']} na tel. {rnd_phone(r)}.

V. Ochrana osobních a zdravotních údajů

Data účastnice {pac['gen']} budou pseudonymizována (přiděleno ID: PAT-{r.randint(1000, 9999)}) a uložena v zabezpečeném systému s šifrováním AES-256. Propojení ID s identitou {pac['gen']} bude uloženo odděleně v trezoru zkoušejícího {lek['gen']}.

VI. Souhlas

Já, {pac['nom']}, prohlašuji, že jsem byla informována prof. MUDr. {lek['ins']} o podstatě, cílech, rizicích a alternativách studie. Svou účast mohu kdykoliv ukončit bez udání důvodu.

V Ostravě dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................          .............................
{pac['nom']}                        prof. MUDr. {lek['nom']}, CSc.
  (účastnice studie)                    (hlavní zkoušející)

.............................
{koordin['nom']}
  (koordinátorka studie)
"""


def gen_10_smlouva_knihovna(r: random.Random) -> str:
    """Přihláška čtenáře do Městské knihovny v Praze — sociální sítě, čtenářský průkaz RFID."""
    cten = inflect_cz("Olga", "Müllerová", True)
    biblio = inflect_cz("Ingrid", "Brožová", True)
    return f"""PŘIHLÁŠKA ČTENÁŘE A SOUHLAS SE ZPRACOVÁNÍM OSOBNÍCH ÚDAJŮ

Městská knihovna v Praze
Mariánské náměstí 1, 115 72 Praha 1
IČO: 00064467
E-mail: info@mlp.cz, tel.: +420 222 113 555
www.mlp.cz

I. Údaje o čtenáři

Jméno a příjmení: {cten['nom']}
Datum narození: {rnd_date(r, 1960, 2000)}
Rodné číslo: {rnd_birth_id(r, True)}
Trvalý pobyt: {rnd_address(r)[0]}
Korespondenční adresa: {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Olga", "Müllerová", r)}
Facebook: {rnd_facebook(r, "Olga", "Müllerová")}
Instagram: {rnd_instagram(r, "Olga")}
Skype: olga.mullerova.{r.randint(10, 99)}

II. Čtenářský průkaz

Číslo průkazu: MKP-{r.randint(100000, 999999)}
RFID čip: {rnd_rfid(r)}
Platnost: od {r.randint(1, 28)}. {r.randint(1, 12)}. 2026 do {r.randint(1, 28)}. {r.randint(1, 12)}. 2027
Registrační poplatek: 200 Kč

III. Souhlas se zpracováním osobních údajů

Čtenářka {cten['nom']} souhlasí se zpracováním výše uvedených údajů za účelem:
a) evidence čtenářů a vedení výpůjčního systému,
b) zasílání upomínek a notifikací na e-mail {cten['gen']},
c) statistických účelů (anonymizovaných).

Údaje budou zpracovávány po dobu platnosti čtenářského průkazu čtenářky {cten['gen']} a 3 roky po jeho zániku.

IV. Knihovní řád — vybrané povinnosti

Čtenářka {cten['nom']} bere na vědomí:
- Maximální doba výpůjčky je 30 dnů s možností 2 prodloužení.
- Za poškození nebo ztrátu knihy odpovídá čtenářka {cten['nom']} v plné výši.
- RFID čip je nepřenosný. Čtenářka {cten['nom']} nesmí průkaz poskytnout třetí osobě.

V. Kontakt na knihovnici

Registrace: {biblio['nom']}, tel.: {rnd_phone(r)}, e-mail: {rnd_email("Ingrid", "Brožová", r, "mlp.cz")}

Jakékoliv změny osobních údajů je čtenářka {cten['nom']} povinna oznámit knihovnici {biblio['dat']} do 15 dnů.

V Praze dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................          .............................
{cten['nom']}                        {biblio['nom']}
  (čtenářka)                           (knihovnice)
"""


def gen_11_veterinarni_smlouva(r: random.Random) -> str:
    """Smlouva o veterinární péči — čip zvířete, majitel, adresa s čtvrtí."""
    majitel = inflect_cz("Žaneta", "Havlíčková", True)
    veter = inflect_cz("Sebastian", "Šimek", False)
    return f"""SMLOUVA O VETERINÁRNÍ PÉČI

MedVet Klinika s.r.o.
Masarykovo náměstí 7, 586 01 Jihlava
IČO: 27304501, e-mail: info@medvet-jihlava.cz, tel.: +420 567 123 456

I. Smluvní strany

Veterinární lékař:
MVDr. {veter['nom']}
IČO: {r.randint(10000000, 99999999)}
Sídlo: Masarykovo náměstí 7, 586 01 Jihlava
Tel.: {rnd_phone(r)}, e-mail: {rnd_email("Sebastian", "Šimek", r, "medvet-jihlava.cz")}

Majitelka zvířete:
{majitel['nom']}
Nar.: {rnd_date(r)}
Rodné číslo: {rnd_birth_id(r, True)}
Trvalý pobyt: {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Žaneta", "Havlíčková", r)}

II. Identifikace zvířete

Druh: pes
Plemeno: Zlatý retriever
Jméno: Buddy
Pohlaví: pes (kastrovaný)
Datum narození: 15. 3. 2020
Číslo mikročipu: 203 {r.randint(100, 999)} {r.randint(100000000, 999999999)}
Barva: zlatá
Váha: 32 kg

III. Předmět smlouvy

MVDr. {veter['nom']} se zavazuje poskytovat veterinární péči zvířeti majitelky {majitel['gen']} v rozsahu:
a) preventivní prohlídky (2× ročně),
b) vakcinace dle očkovacího plánu,
c) akutní ošetření,
d) diagnostika (RTG, UZ, laboratorní rozbory).

IV. Zdravotní záznam

Vakcinace: vzteklina (platná do 5/2027), parvoviróza, hepatitida, leptospiróza
Alergie: kuřecí protein
Chronická onemocnění: artróza levého kyčelního kloubu
Léky: Rimadyl 50 mg 1-0-1 dle potřeby

MVDr. {veter['nom']} informoval majitelku {majitel['gen']}, že zdravotní záznamy zvířete budou uchovávány v elektronickém systému kliniky.

V. Odměna

Preventivní prohlídka: 800 Kč
Akutní ošetření: dle ceníku
Platba na účet: {rnd_bank(r)}, VS: číslo mikročipu

VI. Souhlas se zpracováním údajů

Majitelka {majitel['nom']} souhlasí se zpracováním svých osobních údajů a údajů o zvířeti. Údaje budou zpracovávány MVDr. {veter['ins']} po dobu trvání smlouvy a 5 let po jejím ukončení.

V Jihlavě dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................          .............................
{majitel['nom']}                     MVDr. {veter['nom']}
"""


def gen_12_dedictvi(r: random.Random) -> str:
    """Usnesení o dědictví — pozůstalý, dědicové, podíly, adresy."""
    zustavitel = inflect_cz("Vladimír", "Kopecký", False)
    dedic1 = inflect_cz("Kateřina", "Kopecká", True)
    dedic2 = inflect_cz("Patrik", "Kopecký", False)
    notar = inflect_cz("Daniela", "Brožová", True)
    return f"""USNESENÍ O DĚDICTVÍ

Okresní soud v Pardubicích
Sp. zn.: 28 D 456/2026

Soudní komisařka JUDr. {notar['nom']}, notářka se sídlem Tyršova 18, 530 02 Pardubice, pověřená vedením pozůstalostního řízení, vydává toto

USNESENÍ

I. Zůstavitel

{zustavitel['nom']}, nar. {rnd_date(r, 1940, 1960)}, zemřelý dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2025,
rodné číslo: {rnd_birth_id(r)},
poslední trvalý pobyt: {rnd_address(r)[0]},
stav: vdovec

II. Dědicové

1. {dedic1['nom']} (dcera zůstavitele)
   Nar.: {rnd_date(r, 1970, 1985)}, r.č.: {rnd_birth_id(r, True)}
   Bytem: {rnd_address(r)[0]}
   Tel.: {rnd_phone(r)}, e-mail: {rnd_email("Kateřina", "Kopecká", r)}
   Bankovní účet: {rnd_bank(r)}

2. {dedic2['nom']} (syn zůstavitele)
   Nar.: {rnd_date(r, 1975, 1990)}, r.č.: {rnd_birth_id(r)}
   Bytem: {rnd_address(r)[0]}
   Tel.: {rnd_phone(r)}, e-mail: {rnd_email("Patrik", "Kopecký", r)}
   Bankovní účet: {rnd_bank(r)}
   IBAN: {rnd_iban(r)}
   LinkedIn: {rnd_linkedin(r, "Patrik", "Kopecký")}

III. Pozůstalostní majetek

A) Nemovitosti:
   - Rodinný dům, Tyršova 44/2, 530 02 Pardubice, LV 567, k.ú. Pardubice
     Hodnota dle znaleckého posudku: 4 200 000 Kč
   - Garáž č.p. 12, tamtéž
     Hodnota: 350 000 Kč

B) Bankovní účty zůstavitele {zustavitel['gen']}:
   - Č. účtu: {rnd_bank(r)}, zůstatek ke dni úmrtí: 234 567 Kč
   - Č. účtu: {rnd_bank(r)}, zůstatek: 89 123 Kč
   - IBAN: {rnd_iban(r)}, zůstatek: 15 600 EUR

C) Motorové vozidlo:
   - Volkswagen Passat 2.0 TDI, SPZ: {rnd_spz(r)}, VIN: {rnd_vin(r)}
     Rok výroby: 2019, hodnota: 420 000 Kč

D) Osobní majetek:
   - Zbrojní průkaz č. ZP-{r.randint(100000, 999999)}, zbraň CZ 75 B, č. {r.randint(10000, 99999)}

IV. Dluhy zůstavitele

- Hypoteční úvěr u České spořitelny a.s. (IČO: 45244782): zůstatek 1 850 000 Kč
- Nedoplatek na dani z nemovitosti: 3 200 Kč

V. Rozdělení dědictví

Dědicové {dedic1['nom']} a {dedic2['nom']} uzavřeli dědickou dohodu:
- {dedic1['dat']}: rodinný dům, garáž, osobní majetek (celkem cca 4 553 200 Kč)
- {dedic2['dat']}: bankovní účty, vozidlo, eurový účet (celkem cca 759 290 Kč + 15 600 EUR)
- Hypoteční úvěr přebírá dědička {dedic1['nom']}.

VI. Odměna soudní komisařky

Odměna JUDr. {notar['gen']}: 18 500 Kč + DPH. Platba na účet: {rnd_bank(r)}.

Toto usnesení je pravomocné.

V Pardubicích dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

JUDr. {notar['nom']}
Soudní komisařka
Notářka se sídlem Tyršova 18, 530 02 Pardubice
"""


def gen_13_rozhodci_nalez(r: random.Random) -> str:
    """Rozhodčí nález — obchodní spor, více stran, zahraniční účastník."""
    rozhodce = inflect_cz("Theodor", "Polák", False)
    zalobce = inflect_cz("Eliška", "Zemanová", True)
    zalob_firma = "TechBridge Innovations s.r.o."
    zalovany = inflect_cz("Hans", "Horváth", False)
    zalov_firma = "Horváth & Partners GmbH"
    return f"""ROZHODČÍ NÁLEZ

Rozhodčí řízení sp. zn. Rsp {r.randint(100, 999)}/2026

Rozhodce:
JUDr. {rozhodce['nom']}, Ph.D., zapsaný v seznamu rozhodců vedeném Ministerstvem spravedlnosti
Sídlo: {rnd_address(r)[0]}
IČO: {r.randint(10000000, 99999999)}
Tel.: {rnd_phone(r)}, e-mail: {rnd_email("Theodor", "Polák", r)}

I. Účastníci řízení

Žalobkyně:
{zalobce['nom']}, jednatelka společnosti {zalob_firma}
IČO: {r.randint(10000000, 99999999)}, DIČ: CZ{r.randint(10000000, 99999999)}
Sídlo: {rnd_address(r)[0]}
Nar.: {rnd_date(r, 1975, 1990)}
R.č.: {rnd_birth_id(r, True)}
Tel.: {rnd_phone(r)}
E-mail: {rnd_email("Eliška", "Zemanová", r)}
Právní zastoupení: Mgr. Dominik Jandák, advokát, ev. č. ČAK {r.randint(10000, 99999)}

(dále jen „Žalobkyně")

Žalovaný:
{zalovany['nom']}, jednatel společnosti {zalov_firma}
Sídlo: Bahnhofstraße 12, 1010 Wien, Rakousko
IČO (Firmenbuchnummer): FN {r.randint(100000, 999999)} z
Korespondenční adresa v ČR: {rnd_address(r)[0]}
Nar.: {rnd_date(r, 1965, 1985)}
Číslo pasu: AT{r.randint(1000000, 9999999)}
Tel.: {rnd_phone(r)}
E-mail: {rnd_email("Hans", "Horváth", r)}

(dále jen „Žalovaný")

II. Skutkový stav

Žalobkyně {zalobce['nom']} prostřednictvím společnosti {zalob_firma} uzavřela dne 15. 3. 2025 se žalovaným {zalovany['ins']} smlouvu o vývoji softwarového řešení za cenu 1 450 000 Kč. Žalovaný {zalovany['nom']} zaplatil pouze zálohu 450 000 Kč a zbývající částku 1 000 000 Kč nehradil přes opakované výzvy žalobkyně {zalobce['gen']}.

Žalovaný {zalovany['nom']} namítal, že dílo nebylo řádně předáno. Rozhodce po provedení důkazů (svědecké výpovědi, e-mailová korespondence, předávací protokol podepsaný {zalovany['ins']}) konstatuje, že dílo bylo řádně dokončeno a předáno dne 10. 9. 2025.

III. Právní posouzení

Rozhodce {rozhodce['nom']} konstatuje, že žalovaný {zalovany['nom']} porušil povinnost zaplatit sjednanou cenu díla dle § 2610 občanského zákoníku.

IV. Výrok

1. Žalovaný {zalovany['nom']} je povinen zaplatit žalobkyni {zalobce['dat']} částku 1 000 000 Kč s úrokem z prodlení ve výši 8,25 % p.a. od 1. 10. 2025 do zaplacení.

2. Žalovaný {zalovany['nom']} je povinen zaplatit žalobkyni {zalobce['dat']} náhradu nákladů řízení ve výši 125 000 Kč.

3. Platba na účet žalobkyně {zalobce['gen']}: {rnd_bank(r)}, IBAN: {rnd_iban(r)}, VS: {r.randint(100000, 999999)}.

V. Poučení

Proti tomuto rozhodčímu nálezu není odvolání přípustné. Rozhodčí nález je vykonatelný uplynutím lhůty k dobrovolnému plnění.

V Praze dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................
JUDr. {rozhodce['nom']}, Ph.D.
Rozhodce
"""


def gen_14_najemni_smlouva(r: random.Random) -> str:
    """Nájemní smlouva na byt — složitá adresa s čtvrtí, kauce, spolubydlící."""
    pronaj = inflect_cz("Aleksandr", "Petrov", False)
    najemce = inflect_cz("Anežka", "Šimková", True)
    spolub = inflect_cz("Dominik", "Bártl", False)
    return f"""NÁJEMNÍ SMLOUVA

uzavřená dle § 2201 a násl. zákona č. 89/2012 Sb., občanský zákoník

I. Smluvní strany

Pronajímatel:
{pronaj['nom']}
Nar.: {rnd_date(r)}
Rodné číslo: {rnd_birth_id(r)}
Trvalý pobyt: {rnd_address(r)[0]}
Tel.: {rnd_phone(r)}
E-mail: {rnd_email("Aleksandr", "Petrov", r)}
Bankovní účet: {rnd_bank(r)}
IBAN: {rnd_iban(r)}
IČO (pronájem jako OSVČ): {r.randint(10000000, 99999999)}
DIČ: CZ{r.randint(10000000, 99999999)}

(dále jen „Pronajímatel")

Nájemkyně:
{najemce['nom']}
Nar.: {rnd_date(r)}
Rodné číslo: {rnd_birth_id(r, True)}
Trvalý pobyt: {rnd_address(r)[0]}
Přechodný pobyt: Čelakovského sady 88/3, 120 00 Praha 2 - Nové Město
Tel.: {rnd_phone(r)}
E-mail: {rnd_email("Anežka", "Šimková", r)}

(dále jen „Nájemkyně")

Spolubydlící:
{spolub['nom']}
Nar.: {rnd_date(r)}
R.č.: {rnd_birth_id(r)}
Tel.: {rnd_phone(r)}

II. Předmět nájmu

Pronajímatel {pronaj['nom']} přenechává nájemkyni {najemce['dat']} do užívání byt č. 3 o dispozici 2+kk, nacházející se ve 2. NP domu na adrese Kolínská 42/7, 130 00 Praha 3 - Vinohrady, zapsaný na LV 1234, k.ú. Vinohrady.

Výměra bytu: 58 m². Příslušenství: sklep č. 3, jedno parkovací místo ve dvoře.

III. Nájemné a úhrady

Nájemné: 22 000 Kč / měsíc
Záloha na služby: 4 500 Kč / měsíc
Splatnost: do 15. dne předcházejícího měsíce
Platba na účet pronajímatele {pronaj['gen']}: {rnd_bank(r)}, VS: 42703

Kauce: 44 000 Kč (2× nájemné), uhrazena na účet {pronaj['gen']} č. {rnd_bank(r)}, IBAN: {rnd_iban(r)}.

IV. Doba nájmu

Nájem se sjednává na dobu určitou: od 1. 4. 2026 do 31. 3. 2028.

V. Práva a povinnosti

Nájemkyně {najemce['nom']} se zavazuje:
a) užívat byt řádně a v souladu s jeho účelem,
b) umožnit pronajímateli {pronaj['dat']} vstup do bytu za účelem nezbytných oprav po předchozím oznámení,
c) nahlásit pronajímateli {pronaj['dat']} každou změnu v osobě spolubydlícího.

Pronajímatel {pronaj['nom']} se zavazuje udržovat byt ve stavu způsobilém k bydlení.

Spolubydlící {spolub['nom']} bere na vědomí domovní řád a pravidla užívání společných prostor. Pronajímatel {pronaj['nom']} souhlasí s pobytem spolubydlícího {spolub['gen']} v bytě.

VI. Předávací protokol

Při předání bytu nájemkyni {najemce['dat']} bude sepsán předávací protokol s fotografiemi, stavy energií a podpisy obou stran. Klíče: 3 sady (nájemkyně {najemce['nom']}, spolubydlící {spolub['nom']}, pronajímatel {pronaj['nom']}).

VII. Ochrana osobních údajů

Smluvní strany souhlasí se zpracováním osobních údajů v rozsahu uvedeném v této smlouvě pro účely plnění smlouvy a zákonných povinností.

V Praze dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................          .............................          .............................
{pronaj['nom']}                      {najemce['nom']}                     {spolub['nom']}
  (pronajímatel)                        (nájemkyně)                          (spolubydlící)
"""


def gen_15_insolvence(r: random.Random) -> str:
    """Insolvenční návrh — dlužník, věřitelé, seznam pohledávek, registrační značky."""
    dluznik = inflect_cz("Maxmilián", "Kratochvíl", False)
    veritel1 = inflect_cz("Natálie", "Dostálová", True)
    veritel2 = inflect_cz("Ingrid", "Zemanová", True)
    spravce = inflect_cz("Lukáš", "Brož", False)
    return f"""INSOLVENČNÍ NÁVRH SPOJENÝ S NÁVRHEM NA POVOLENÍ ODDLUŽENÍ

Krajský soud v Brně
Husova 15, 601 95 Brno

I. Dlužník

{dluznik['nom']}
Nar.: {rnd_date(r, 1975, 1990)}
Rodné číslo: {rnd_birth_id(r)}
Trvalý pobyt: {rnd_address(r)[0]}
Korespondenční adresa: {rnd_address(r)[0]}
Telefon: {rnd_phone(r)}
E-mail: {rnd_email("Maxmilián", "Kratochvíl", r)}
Číslo OP: {r.randint(100000000, 999999999)}
Stav: svobodný, bezdětný
Zaměstnavatel: MedVet Klinika s.r.o., IČO: 27304501
Čistý měsíční příjem: 28 500 Kč

(dále jen „Dlužník")

II. Odůvodnění návrhu

Dlužník {dluznik['nom']} prohlašuje, že se nachází v úpadku ve smyslu § 3 odst. 1 zákona č. 182/2006 Sb. (insolvenční zákon), neboť má více věřitelů, peněžité závazky po lhůtě splatnosti delší 30 dnů a není schopen tyto závazky plnit.

Celková výše dluhů dlužníka {dluznik['gen']}: 1 245 000 Kč.

III. Seznam závazků

1. Česká spořitelna a.s. (IČO: 45244782)
   - Spotřebitelský úvěr č. SU-{r.randint(100000, 999999)}
   - Dlužná částka: 380 000 Kč + příslušenství
   - Jistina po splatnosti od: 15. 6. 2025

2. {veritel1['nom']} (soukromá půjčka)
   Nar.: {rnd_date(r)}, r.č.: {rnd_birth_id(r, True)}
   Bytem: {rnd_address(r)[0]}
   Tel.: {rnd_phone(r)}, e-mail: {rnd_email("Natálie", "Dostálová", r)}
   - Dlužná částka: 250 000 Kč
   - Smlouva ze dne 3. 1. 2024

3. {veritel2['nom']} (soukromá půjčka)
   Nar.: {rnd_date(r)}, r.č.: {rnd_birth_id(r, True)}
   Bytem: {rnd_address(r)[0]}
   Tel.: {rnd_phone(r)}
   - Dlužná částka: 180 000 Kč

4. Home Credit a.s. (IČO: 26978636)
   - Revolving úvěr
   - Dlužná částka: 95 000 Kč

5. Exekutorský úřad Brno-město ({spravce['nom']})
   - Náklady exekuce sp. zn. 205 EX 789/2025
   - Dlužná částka: 45 000 Kč

6. Daňový nedoplatek — FÚ pro Jihomoravský kraj
   - Nedoplatek na DPFO za rok 2024: 12 000 Kč

7. Nedoplatek nájemného: 283 000 Kč
   Pronajímatel: Aleksandr Petrov, e-mail: {rnd_email("Aleksandr", "Petrov", r)}

IV. Seznam majetku dlužníka {dluznik['gen']}

A) Bankovní účty:
   - Č. účtu: {rnd_bank(r)}, zůstatek: 3 450 Kč
   - IBAN: {rnd_iban(r)}, zůstatek: 890 Kč

B) Motorové vozidlo:
   - Škoda Fabia 1.2 TSI, SPZ: {rnd_spz(r)}, VIN: {rnd_vin(r)}
   - Rok výroby: 2015, odhad: 110 000 Kč

C) Osobní věci: běžné vybavení domácnosti, hodnota cca 25 000 Kč

V. Navrhovaný způsob oddlužení

Dlužník {dluznik['nom']} navrhuje oddlužení plněním splátkového kalendáře se zpeněžením majetkové podstaty (§ 398 odst. 1 InsZ).

Předpokládaná měsíční splátka: 9 500 Kč (po odečtení nezabavitelné částky).
Předpokládaná doba oddlužení: 5 let.
Míra uspokojení věřitelů: cca 45,8 %.

VI. Navrhovaný insolvenční správce

JUDr. {spravce['nom']}, insolvenční správce
Sídlo: {rnd_address(r)[0]}
IČO: {r.randint(10000000, 99999999)}
Datová schránka: {rnd_data_box(r)}
Tel.: {rnd_phone(r)}, e-mail: {rnd_email("Lukáš", "Brož", r)}

VII. Přílohy

1. Kopie OP dlužníka {dluznik['gen']}
2. Potvrzení o příjmu
3. Seznam závazků s doklady
4. Výpisy z bankovních účtů
5. Technický průkaz vozidla (SPZ: {rnd_spz(r)}, VIN: {rnd_vin(r)})

VIII. Prohlášení

Dlužník {dluznik['nom']} prohlašuje, že veškeré údaje uvedené v tomto návrhu jsou pravdivé a úplné.

V Brně dne {r.randint(1, 28)}. {r.randint(1, 12)}. 2026

.............................
{dluznik['nom']}
(dlužník / navrhovatel)
"""


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

GENERATORS = [
    gen_01_exekuce,
    gen_02_notarsky_zapis,
    gen_03_nemocnice_souhlas,
    gen_04_kyberneticka_bezpecnost,
    gen_05_skolni_matrika,
    gen_06_pojistna_udalost,
    gen_07_darovaci_smlouva,
    gen_08_pracovni_smlouva_cizinec,
    gen_09_medicinska_studie,
    gen_10_smlouva_knihovna,
    gen_11_veterinarni_smlouva,
    gen_12_dedictvi,
    gen_13_rozhodci_nalez,
    gen_14_najemni_smlouva,
    gen_15_insolvence,
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i, gen_fn in enumerate(GENERATORS, start=1):
        r = random.Random(42 + i * 7)
        text = gen_fn(r)
        stem = f"smlouva_final_{i:02d}"
        docx_path = OUT_DIR / f"{stem}.docx"

        doc = Document()
        style = doc.styles["Normal"]
        style.font.size = 110000  # ~8.5pt for denser text
        for line in text.strip().splitlines():
            doc.add_paragraph(line)
        doc.save(docx_path)
        print(f"  [{i:2d}/15] {docx_path.name}")

    print(f"\nHotovo — 15 smluv vygenerováno do {OUT_DIR}")


if __name__ == "__main__":
    main()
