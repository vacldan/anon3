from __future__ import annotations

from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "test_data"


def write_txt_and_docx(stem: str, text: str) -> None:
    txt_path = OUT_DIR / f"{stem}.txt"
    docx_path = OUT_DIR / f"{stem}.docx"

    txt_path.write_text(text, encoding="utf-8")

    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(docx_path)


def main() -> None:
    variants: dict[int, str] = {}

    # 41) Nemocnice – smlouva s externím IT dodavatelem (NIS/GDPR)
    variants[41] = """SMLOUVA O PODPOŘE NEMOCNIČNÍHO INFORMAČNÍHO SYSTÉMU A ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ

uzavřená dle § 1746 odst. 2 zákona č. 89/2012 Sb., občanský zákoník, a dle Nařízení (EU) 2016/679 (GDPR)

I. SMLUVNÍ STRANY

1. Zadavatel (Nemocnice):
   Název: Fakultní nemocnice Sever
   Sídlo: U Nemocnice 1, 120 00 Praha 2
   IČO: 00012345
   DIČ: CZ00012345
   Statutární zástupce: MUDr. Jan Vlk, ředitel
   Telefon: +420 224 111 222
   E‑mail: reditelstvi@fnsever.cz
   Datová schránka: abcd123

   (dále jen „Nemocnice“)

2. Dodavatel IT služeb:
   Obchodní firma: MEDISOFT Solutions s.r.o.
   Sídlo: Technologická 5, 160 00 Praha 6
   IČO: 05223311
   DIČ: CZ05223311
   Zapsaná v OR u Městského soudu v Praze, oddíl C, vložka 257890
   Kontaktní osoba: Ing. Radek Zahradník
   Datum narození: 12. 04. 1985
   Rodné číslo: 850412/1234
   Telefon: +420 606 888 999
   E‑mail: radek.zahradnik@medisoft.cz
   IP adresa služebního notebooku: 10.22.33.44

   (dále jen „Dodavatel“)

Společně též jen „Smluvní strany“.

II. PŘEDMĚT SMLOUVY

1. Dodavatel se zavazuje poskytovat Nemocnici podporu nemocničního informačního systému MEDISOFT, zahrnující zejména:
   a) správu databáze pacientů,
   b) správu uživatelských účtů zdravotnického personálu,
   c) aktualizace aplikace a bezpečnostních záplat,
   d) asistenci při testování anonymizace zdravotnických záznamů exportovaných z NIS.
2. Nemocnice se zavazuje platit Dodavateli odměnu dle článku VII této smlouvy.

III. KATEGORIE ZPRACOVÁVANÝCH ÚDAJŮ

1. V rámci provozu NIS MEDISOFT jsou zpracovávány osobní údaje:
   a) pacientů (jméno, příjmení, datum narození, rodné číslo, číslo pojištěnce, diagnózy),
   b) zdravotnického personálu (jméno, příjmení, titul, osobní číslo, číslo služebního telefonu),
   c) kontaktních osob pacientů a osob blízkých.
2. Pro testovací účely se ve smlouvě výslovně uvádí následující fiktivní osoby:
   a) Pacient: Bc. Barbora Koutná, nar. 15. 05. 1991, rodné číslo 910515/4567,
      adresa: Lipová 8, 602 00 Brno, telefon: +420 731 222 333, e‑mail: barbora.koutna@example.com.
   b) Ošetřující lékař: MUDr. Ondřej Jelínek, nar. 03. 03. 1980, rodné číslo 800303/7890,
      služební e‑mail: ondrej.jelinek@fnsever.cz, telefon: +420 224 555 666.
   c) Kontaktní osoba: Marek Koutný, nar. 20. 08. 1989, rodné číslo 890820/3210,
      telefon: +420 603 987 111, e‑mail: marek.koutny@example.org.

IV. PŘÍSTUPY A TECHNICKÉ ÚDAJE

1. Dodavatel používá pro vzdálený přístup tyto přístupové údaje:
   Uživatelské jméno: radek.zahradnik
   Heslo: M3diSoft!2026
   VPN server: vpn.fnsever.cz
2. Přístupy jsou logovány včetně IP adres (např. 10.22.33.44, 192.168.20.101), uživatelského jména a času přihlášení.
3. Nemocnice bere na vědomí, že se v logách budou objevovat pádové tvary jmen, např. „s Barborou Koutnou“, „Barboře Koutné“, „Ondřeji Jelínkovi“, „s Ondřejem Jelínkem“.

V. ZÁRUKY A BEZPEČNOST

1. Dodavatel prohlašuje, že všichni jeho zaměstnanci, kteří budou mít přístup do NIS, podepsali dohody o mlčenlivosti.
2. Dodavatel zpracovává osobní údaje výlučně na základě pokynů Nemocnice.

VII. ODMĚNA

1. Měsíční paušál za podporu NIS činí 45 000 Kč bez DPH.
2. Odměna bude hrazena na účet Dodavatele č. 227799881/5500, IBAN: CZ24 5500 0000 0022 7799 8810.

VIII. ZÁVĚR

V Praze dne 5. 3. 2026
"""

    # 42) Sociální služby – terénní pečovatelská služba
    variants[42] = """SMLOUVA O POSKYTOVÁNÍ TERÉNNÍ PEČOVATELSKÉ SLUŽBY

uzavřená dle zákona č. 108/2006 Sb., o sociálních službách

I. SMLUVNÍ STRANY

1. Poskytovatel sociálních služeb:
   Název: Centrum sociálních služeb Javor
   Sídlo: Javorová 5, 779 00 Olomouc
   IČO: 25998877
   Telefon: +420 585 111 444
   E‑mail: info@cssjavor.cz
   Kontaktní osoba: Mgr. Iveta Konečná, vedoucí terénních služeb

   (dále jen „Poskytovatel“)

2. Uživatel služby:
   Jméno a příjmení: František Kubíček
   Datum narození: 21. 09. 1942
   Rodné číslo: 420921/1234
   Trvalý pobyt: Na Stráni 12, 779 00 Olomouc
   Telefon: +420 604 222 333
   Číslo průkazu ZTP: 123456789

   (dále jen „Uživatel“)

II. ROZSAH POSKYTOVANÉ SLUŽBY

1. Poskytovatel zajistí uživateli pomoc při zvládání běžných úkonů péče o vlastní osobu, pomoc při osobní hygieně, zajištění nákupů a doprovody k lékaři.
2. Uživatel souhlasí, aby pracovníci Poskytovatele navštěvovali jeho bytovou jednotku Na Stráni 12, 779 00 Olomouc.

III. OSOBNÍ ÚDAJE UŽIVATELE A OSOB BLÍZKÝCH

1. Uživatel bere na vědomí, že Poskytovatel povede evidenční list uživatele služby, ve kterém budou uvedeny:
   a) osobní údaje Františka Kubíčka,
   b) údaje o kontaktní osobě: dcera Jana Brázdová, nar. 17. 02. 1972, rodné číslo 720217/3456,
      adresa: Jabloňová 11, 779 00 Olomouc, telefon: +420 603 777 888, e‑mail: jana.brazdova@example.com,
   c) údaje o ošetřujícím lékaři: MUDr. Pavel Richter, nar. 05. 11. 1969, rodné číslo 691105/5678,
      ordinace: Poliklinika Sever, Masarykova 3, 779 00 Olomouc, telefon: +420 585 222 555.

2. V textu dokumentace se mohou objevit pádové tvary: „Františka Kubíčka“, „s Františkem Kubíčkem“, „Jany Brázdové“, „s Janou Brázdovou“, „Pavla Richtera“, „s Pavlem Richterem“.

IV. PŘEDÁVÁNÍ INFORMACÍ A PŘÍSTUPOVÉ ÚDAJE

1. Poskytovatel používá interní informační systém, do něhož budou vkládány záznamy o návštěvách u Františka Kubíčka.
2. Do systému se přihlašují sociální pracovníci pomocí přístupových údajů (příklad pro test):
   Uživatelské jméno: ikonecna
   Heslo: Javor!2026
   Přihlášení probíhá z IP adres 192.168.50.101 a 10.0.1.22.

V. ÚHRADA

1. Uživatel hradí úhradu za terénní pečovatelskou službu bezhotovostně na účet Poskytovatele č. 1122334455/0800.

VI. ZÁVĚR

V Olomouci dne 10. 4. 2026
"""

    # 43) Psychologická poradna – smlouva o poskytování služeb a mlčenlivosti
    variants[43] = """SMLOUVA O POSKYTOVÁNÍ PSYCHOLOGICKÝCH SLUŽEB A OCHRANĚ OSOBNÍCH ÚDAJŮ

I. SMLUVNÍ STRANY

1. Poskytovatel:
   Název: Psychologické centrum Harmonia, s.r.o.
   Sídlo: Náměstí 5. května 3, 301 00 Plzeň
   IČO: 06112233
   Telefon: +420 377 111 222
   E‑mail: info@harmonia-ps.cz
   Kontaktní psycholog: PhDr. Klára Jandová

2. Klient:
   Jméno a příjmení: Bc. Tereza Hálková
   Datum narození: 19. 11. 1995
   Rodné číslo: 951119/6789
   Trvalý pobyt: Luční 7, 326 00 Plzeň
   Telefon: +420 728 333 444
   E‑mail: tereza.halkova@example.com

II. PŘEDMĚT SMLOUVY

1. Poskytovatel se zavazuje poskytovat Klientce individuální psychologické poradenství a krátkodobou terapii.
2. Klientka bere na vědomí, že v rámci sezení budou zaznamenávány stručné zápisy obsahující citlivé údaje o jejím duševním zdraví a rodinné situaci.

III. ÚDAJE O DALŠÍCH OSOBÁCH

1. Klientka výslovně uvádí osoby, které se v jejím příběhu typicky vyskytují:
   a) partner: Jakub Němec, nar. 07. 07. 1994, rodné číslo 940707/1234,
      telefon: +420 606 555 666, e‑mail: jakub.nemec@example.com;
   b) matka: Alena Hálková, nar. 02. 02. 1968, rodné číslo 680202/4321,
      adresa: Luční 7, 326 00 Plzeň;
   c) sestra: Mgr. Nikola Hálková, nar. 12. 03. 1992, rodné číslo 920312/3456,
      e‑mail: nikola.halkova@example.org.

2. V záznamech se budou objevovat pádové varianty jmen: „s Jakubem Němcem“, „Jakuba Němce“, „Aleně Hálkové“, „s Alenou Hálkovou“, „Nikole Hálkové“, „s Nikolou Hálkovou“.

IV. ZPŮSOB VEDENÍ DOKUMENTACE

1. Zápisy z konzultací budou vedeny v elektronickém systému, do kterého se Poskytovatel přihlašuje pomocí:
   Uživatelské jméno: kjandova
   Heslo: H@rmonia2026
2. Přístupy jsou logovány včetně IP adresy 192.168.0.77 a identifikátoru zařízení.

V. ODMĚNA

1. Cena jednoho sezení (50 minut) činí 1 200 Kč, platba probíhá převodem na účet Poskytovatele 556688990/0100, variabilní symbol 9511196789.

VI. ZÁVĚR

V Plzni dne 12. 5. 2026
"""

    # 44) Advokát – trestní řízení (obhajoba)
    variants[44] = """SMLOUVA O POSKYTOVÁNÍ PRÁVNÍ POMOCI V TRESTNÍ VĚCI

I. SMLUVNÍ STRANY

1. Advokát:
   Jméno a příjmení: JUDr. Miroslav Černý
   IČO: 71588933
   Sídlo: Soudní 8, 110 00 Praha 1
   Ev. č. ČAK: 22334
   Telefon: +420 602 999 000
   E‑mail: miroslav.cerny@obhajci.cz

2. Obviněný (Klient):
   Jméno a příjmení: Bc. Patrik Král
   Datum narození: 04. 04. 1990
   Rodné číslo: 900404/2222
   Trvalý pobyt: Na Výsluní 21, 190 00 Praha 9
   Telefon: +420 777 444 333
   E‑mail: patrik.kral@example.com

II. PŘEDMĚT SMLOUVY

1. Advokát se zavazuje poskytovat Klientovi právní pomoc v trestním řízení vedeném pod sp. zn. 1 T 45/2026 u Obvodního soudu pro Prahu 9.
2. Klient bere na vědomí, že v rámci spisu budou obsaženy osobní údaje jeho, svědků i poškozených.

III. IDENTIFIKACE POŠKOZENÉHO A SVĚDKŮ

1. Poškozená: Jana Košťálová, nar. 08. 08. 1988, rodné číslo 880808/3456,
   adresa: Dlouhá 9, 110 00 Praha 1, telefon: +420 605 111 222, e‑mail: jana.kostalova@example.org.
2. Svědek: Tomáš Doležal, nar. 01. 01. 1985, rodné číslo 850101/6789,
   adresa: Na Skalce 4, 252 10 Mníšek pod Brdy, telefon: +420 604 555 777.
3. V podáních k soudu se mohou objevit pádové tvary: „Patrika Krále“, „s Patrikem Králem“, „Jany Košťálové“, „s Janou Košťálovou“, „Tomáše Doležala“, „s Tomášem Doležalem“.

IV. ODMĚNA

1. Advokát účtuje odměnu dle advokátního tarifu, minimálně však 35 000 Kč za celé řízení.
2. Záloha ve výši 20 000 Kč bude uhrazena na účet Advokáta 889977665/0300 do 5 dnů od podpisu smlouvy.

V. ZÁVĚR

V Praze dne 20. 5. 2026
"""

    # 45) Škola – smlouva s dodavatelem školního informačního systému
    variants[45] = """SMLOUVA O POSKYTOVÁNÍ A SPRÁVĚ ŠKOLNÍHO INFORMAČNÍHO SYSTÉMU

I. SMLUVNÍ STRANY

1. Škola:
   Název: Základní škola Slunečná
   Sídlo: Slunečná 3, 400 04 Ústí nad Labem
   IČO: 70888811
   Ředitel: Mgr. Radim Štěrba
   Telefon: +420 475 123 456
   E‑mail: reditel@zsslunecna.cz

2. Dodavatel IS:
   Obchodní firma: EDU-SOFT s.r.o.
   Sídlo: Digitální 9, 150 00 Praha 5
   IČO: 07554466
   Kontaktní osoba: Ing. Michaela Kubová
   Telefon: +420 607 555 444
   E‑mail: michaela.kubova@edu-soft.cz

II. ÚDAJE ZPRACOVÁVANÉ V IS

1. IS zpracovává osobní údaje žáků a jejich zákonných zástupců, zejména:
   a) jméno, příjmení, datum narození a rodné číslo žáků,
   b) adresy bydliště,
   c) kontaktní e‑maily a telefonní čísla rodičů.
2. Pro test anonymizace jsou v této smlouvě uvedeni:
   a) žák: Filip Novotný, nar. 05. 09. 2013, rodné číslo 130905/0015,
      adresa: K Žernosekám 11, 400 04 Ústí nad Labem;
   b) matka: Mgr. Andrea Novotná, nar. 30. 01. 1984, rodné číslo 840130/4567,
      e‑mail: andrea.novotna@example.com, telefon: +420 603 444 222;
   c) otec: Ing. Vojtěch Novotný, nar. 11. 12. 1982, rodné číslo 821211/7890,
      e‑mail: vojtech.novotny@example.org.

III. PŘÍSTUPOVÉ ÚDAJE

1. Dodavatel spravuje účty administrátorů:
   Uživatelské jméno: rsterba
   Heslo: Slun3cna!2026
2. Rodiče se přihlašují do rodičovského portálu; příklad:
   Uživatelské jméno: anovotna
   Heslo: Fil1p2026

IV. ZÁVĚR

V Ústí nad Labem dne 30. 5. 2026
"""

    # 46) Mateřská škola – docházka dítěte a zpracování údajů
    variants[46] = """SMLOUVA O DOCHÁZCE DÍTĚTE DO MATEŘSKÉ ŠKOLY A ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ

I. SMLUVNÍ STRANY

1. Mateřská škola:
   Název: Mateřská škola U Stromu
   Sídlo: U Stromu 2, 500 03 Hradec Králové
   IČO: 70992233
   Ředitelka: Mgr. Daniela Fořtová
   Telefon: +420 495 222 333
   E‑mail: reditelka@msustromu.cz

2. Zákonný zástupce:
   Jméno a příjmení: Ing. Petr Havel
   Datum narození: 18. 07. 1987
   Rodné číslo: 870718/4444
   Adresa: K Labi 9, 500 03 Hradec Králové
   Telefon: +420 604 111 222
   E‑mail: petr.havel@example.com

II. DÍTĚ

1. Dítě:
   Jméno a příjmení: Klára Havelová
   Datum narození: 09. 03. 2021
   Rodné číslo: 210309/0006
   Adresa: K Labi 9, 500 03 Hradec Králové

III. ÚDAJE A KONTAKTY

1. Zákonný zástupce souhlasí se zpracováním osobních údajů Kláry Havelové a svých údajů pro účely vedení docházky a komunikace školy s rodiči.
2. V textu směrnic se mohou objevovat tvary: „Kláry Havelové“, „s Klárou Havelovou“, „Petra Havla“, „s Petrem Havlem“.

IV. ZÁVĚR

V Hradci Králové dne 7. 6. 2026
"""

    # 47) Pracovnělékařské služby – smlouva se zaměstnavatelem
    variants[47] = """SMLOUVA O ZAJIŠTĚNÍ PRACOVNĚLÉKAŘSKÝCH SLUŽEB

I. SMLUVNÍ STRANY

1. Poskytovatel pracovnělékařských služeb:
   Název: MEDIPRAC s.r.o.
   Sídlo: Zdravotní 10, 602 00 Brno
   IČO: 26223344
   Telefon: +420 543 111 888
   E‑mail: info@mediprac.cz
   Kontaktní lékař: MUDr. Alena Krátká

2. Zaměstnavatel:
   Název: STROJÍRNY Morava a.s.
   Sídlo: Průmyslová 77, 627 00 Brno
   IČO: 25566789
   IČZ: 1234567
   Kontaktní osoba: Ing. Roman Jílek, vedoucí HR
   Telefon: +420 602 333 999
   E‑mail: roman.jilek@strojirny-morava.cz

II. ÚDAJE ZAMĚSTNANCŮ

1. Poskytovatel bude zpracovávat osobní údaje zaměstnanců v rozsahu nezbytném pro pracovnělékařské prohlídky.
2. Pro test anonymizace smlouva obsahuje následující příklady:
   a) zaměstnanec: Martin Řehoř, nar. 14. 02. 1986, rodné číslo 860214/3210,
      pozice: svářeč, telefon: +420 604 555 333;
   b) zaměstnanec: Jana Dvořáčková, nar. 29. 09. 1990, rodné číslo 900929/7890,
      pozice: účetní, e‑mail: jana.dvorackova@example.com.
3. V dokumentaci se objeví tvary: „Martina Řehoře“, „s Martinem Řehořem“, „Jany Dvořáčkové“, „s Janou Dvořáčkovou“.

III. ZÁVĚR

V Brně dne 15. 6. 2026
"""

    # 48) Rodinná mediace – dohoda o zpracování údajů
    variants[48] = """DOHODA O PROVEDENÍ RODINNÉ MEDIACE A ZPRACOVÁNÍ OSOBNÍCH ÚDAJů

I. STRANY MEDIACE

1. Mediátor:
   Jméno a příjmení: Mgr. Šárka Pokorná
   Adresa: Mediátorská 4, 602 00 Brno
   Telefon: +420 739 111 222
   E‑mail: sarka.pokorna@mediace-brno.cz

2. Účastníci mediace:
   a) Tomáš Konečný, nar. 10. 10. 1984, rodné číslo 841010/5678,
      adresa: Olšová 6, 602 00 Brno, telefon: +420 604 222 444;
   b) Mgr. Lenka Konečná, nar. 05. 05. 1985, rodné číslo 850505/7890,
      adresa: Olšová 6, 602 00 Brno, e‑mail: lenka.konecna@example.com.

3. Předmětem mediace je úprava péče o nezletilé děti: Eliška Konečná, nar. 02. 03. 2015, a Vojtěch Konečný, nar. 18. 09. 2017.

II. ZPRACOVÁVANÉ ÚDAJE

1. V rámci mediace budou zaznamenávány osobní údaje účastníků i dětí.
2. V zápisech se mohou vyskytnout tvary: „Tomáše Konečného“, „s Tomášem Konečným“, „Lenky Konečné“, „s Lenkou Konečnou“, „Elišky Konečné“, „s Eliškou Konečnou“.

III. ZÁVĚR

V Brně dne 22. 6. 2026
"""

    # 49) Bezpečnostní agentura – monitorování obchodního centra
    variants[49] = """SMLOUVA O ZAJIŠTĚNÍ OSTRAHY A MONITOROVÁNÍ OBCHODNÍHO CENTRA

I. SMLUVNÍ STRANY

1. Objednatel:
   Název: OC Galerie Jih a.s.
   Sídlo: Obchodní 1, 700 30 Ostrava
   IČO: 27766554
   Zastoupená: Ing. Romanem Krupou, předsedou představenstva
   Telefon: +420 595 123 000
   E‑mail: info@ocgaleriejih.cz

2. Dodavatel bezpečnostních služeb:
   Název: SECURITAS Moravia s.r.o.
   Sídlo: Bezpečnostní 8, 709 00 Ostrava
   IČO: 26221155
   Kontaktní osoba: Bc. Jakub Šíma
   Telefon: +420 736 555 444
   E‑mail: jakub.sima@securitas-moravia.cz

II. MONITOROVÁNÍ A OSOBNÍ ÚDAJE

1. Dodavatel zajišťuje nepřetržité kamerové monitorování společných prostor OC Galerie Jih.
2. Kamerové záznamy mohou obsahovat obrazové záznamy osob, registrační značky vozidel (např. 5AZ 4567, 7B8 2345) a další identifikátory.
3. V rámci testu anonymizace se uvádí kontaktní osoby:
   a) technik správy budovy: Ing. Martin Blažek, nar. 29. 01. 1980, telefon: +420 603 111 777;
   b) vedoucí směny bezpečnostní služby: Petr Valenta, nar. 16. 06. 1983, e‑mail: petr.valenta@example.com.

III. PŘÍSTUPOVÉ ÚDAJE KE KAMEROVÉMU SYSTÉMU

1. Administrátorský přístup:
   Uživatelské jméno: j.sima
   Heslo: S3curitas!2026
   IP adresa serveru: 172.16.0.10

IV. ZÁVĚR

V Ostravě dne 5. 7. 2026
"""

    # 50) Sociálně-právní ochrana dětí – spolupráce s neziskovou organizací
    variants[50] = """SMLOUVA O SPOLUPRÁCI PŘI POSKYTOVÁNÍ SOCIÁLNĚ-PRÁVNÍ OCHRANY DĚTÍ

I. SMLUVNÍ STRANY

1. Orgán sociálně-právní ochrany dětí:
   Název: Magistrát města Brna, OSPOD
   Sídlo: Dominikánské náměstí 1, 601 67 Brno
   Kontaktní osoba: Mgr. Petra Jelínková
   Telefon: +420 542 174 111
   E‑mail: petra.jelinkova@brno.cz

2. Nezisková organizace:
   Název: Spolek Dobrá rodina
   Sídlo: Rodinná 6, 612 00 Brno
   IČO: 26588741
   Statutární zástupce: Bc. Marek Hruška
   Telefon: +420 737 222 333
   E‑mail: marek.hruska@dobrarodina.cz

II. IDENTIFIKACE DÍTĚTE A RODINY

1. Předmětem spolupráce je podpora rodiny nezletilé Anny Králové, nar. 14. 04. 2016, rodné číslo 160414/0007.
2. Rodiče:
   a) otec: Jan Král, nar. 02. 02. 1984, rodné číslo 840202/1234,
      telefon: +420 602 888 111;
   b) matka: Mgr. Simona Králová, nar. 19. 09. 1985, rodné číslo 850919/5678,
      e‑mail: simona.kralova@example.com.
3. V záznamech se objeví tvary: „Anny Králové“, „s Annou Královou“, „Jana Krále“, „s Janem Králem“, „Simony Králové“, „se Simonou Královou“.

III. ZÁVĚR

V Brně dne 10. 7. 2026
"""

    for idx, text in variants.items():
        stem = f"smlouva_gdpr_test_{idx}"
        write_txt_and_docx(stem, text)


if __name__ == "__main__":
    main()

