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

    # 31) Advokát – civilní spor
    variants[31] = """SMLOUVA O POSKYTOVÁNÍ PRÁVNÍCH SLUŽEB

uzavřená dle zákona č. 85/1996 Sb., o advokacii, a dle § 1746 odst. 2 zákona č. 89/2012 Sb., občanský zákoník

I. SMLUVNÍ STRANY

1. Advokát (Poskytovatel):
   Advokát: Mgr. Daniel Mlynář, ev. č. ČAK 12345
   Sídlo: Právnická 12, 110 00 Praha 1
   IČO: 05288977
   Datová schránka: a1b2c3d
   Telefon: +420 731 456 789
   E-mail: daniel.mlynar@advokati.cz
   Bankovní spojení (úschovy): 112882351/0300
   IBAN: CZ98 0300 0000 0011 2882 3510
   IP adresa kanceláře: 192.168.11.22
   MAC zařízení: 00:1F:44:AA:22:11

   (dále jen „Advokát“)

2. Klient (Objednatel):
   Jméno a příjmení: Ing. Markéta Benešová
   Datum narození: 23. 08. 1987
   Rodné číslo: 870823/4567
   Trvalý pobyt: Sadová 19, 370 01 České Budějovice
   Doručovací adresa: Sadová 19, byt 7, 370 01 České Budějovice
   Číslo občanského průkazu: 112233445
   Číslo pasu: PP4567891
   Telefon: +420 777 999 111
   E-mail: marketa.benesova@example.com
   Bankovní účet pro vrácení přeplatků: 662219881/5500

   (dále jen „Klient“)

Společně též jen „Smluvní strany“.

II. PŘEDMĚT SMLOUVY

1. Advokát se zavazuje poskytovat Klientovi právní služby ve věci zastupování v civilním sporu o zaplacení dlužné částky a souvisejících úkonů (předžalobní výzvy, návrh na vydání platebního rozkazu, vyjádření k odporu, jednání u soudu).
2. Spisová značka (předběžně): 12 C 123/2026; soud: Okresní soud v Českých Budějovicích.
3. Klient bere na vědomí, že pro řádné posouzení věci bude Advokát pracovat s dokumenty obsahujícími osobní údaje (smlouvy, e-maily, chaty, výpisy z účtů, faktury).

III. IDENTIFIKACE DALŠÍCH FYZICKÝCH OSOB

1. Klient uvádí, že ve věci vystupují zejména tyto osoby:
   a) Proti-strana: Petr Dohnal, nar. 10. 10. 1984, rodné číslo 841010/1234,
      adresa: Jabloňová 12, 400 01 Ústí nad Labem, tel. +420 605 123 456, e-mail: petr.dohnal@example.org.
   b) Svědek: Gabriela Štěpánová, nar. 01. 01. 1990, rodné číslo 900101/2222,
      adresa: U Parku 8, 779 00 Olomouc, tel. +420 603 987 654.
   c) Kontakt pro doručování: Tomáš Nguyen, nar. 05. 05. 1988, rodné číslo 880505/3333,
      e-mail: tomas.nguyen@example.net, tel. +420 605 444 555.

2. Klient výslovně souhlasí, aby osobní údaje uvedené v tomto článku byly použity v rozsahu nezbytném pro vedení sporu, včetně uvádění v podáních k soudu a při jednáních.

IV. POUŽÍVÁNÍ OSOBNÍCH ÚDAJŮ V PRŮBĚHU POSKYTOVÁNÍ SLUŽEB

1. Komunikace bude probíhat zejména e-mailem na adresách daniel.mlynar@advokati.cz a marketa.benesova@example.com, dále telefonicky na +420 731 456 789 a +420 777 999 111.
2. Advokát je oprávněn kontaktovat Proti-stranu (Petra Dohnala) a Svědka (Gabrielu Štěpánovou) pouze v rozsahu, v němž to dovolují právní předpisy a povaha zastoupení.
3. Smluvní strany si jsou vědomy, že v dokumentech se budou vyskytovat pádové tvary jmen, např. „Markétě Benešové“, „s Markétou Benešovou“, „Petra Dohnala“, „Petru Dohnalovi“, „s Petrem Dohnalem“, „Gabriely Štěpánové“, „Gabrielou Štěpánovou“.

V. PŘÍSTUPOVÉ ÚDAJE A PŘEDÁVÁNÍ PODKLADŮ

1. Klient poskytne Advokátovi přístup do klientského úložiště podkladů:
   Uživatelské jméno: mbenesova
   Heslo: M@rketa2026!
   URL: https://files.example.com/mbenesova
2. Advokát se zavazuje neposkytnout přístupové údaje třetím osobám a uchovávat podklady v zabezpečené podobě.
3. Pro účely testování anonymizace Klient předá i kopie e-mailů obsahujících osobní údaje, zejména marketa.benesova@example.com a petr.dohnal@example.org, a dále telefonní čísla +420 777 999 111 a +420 605 123 456.

VI. ODMĚNA A PLATEBNÍ PODMÍNKY

1. Odměna je sjednána jako hodinová ve výši 2 900 Kč bez DPH.
2. Záloha na odměnu činí 20 000 Kč a bude uhrazena na účet Advokáta č. 112882351/0300 do 5 dnů od podpisu.
3. Variabilní symbol: 8708234567 (rodné číslo Klienta bez lomítka).
4. Případné vrácení přeplatku proběhne na účet Klienta 662219881/5500.

VII. DOBA TRVÁNÍ SMLOUVY

1. Smlouva se uzavírá na dobu určitou do pravomocného skončení věci uvedené v čl. II.
2. Ukončením smlouvy není dotčeno vypořádání odměny a nákladů.

VIII. ZVLÁŠTNÍ USTANOVENÍ O OCHRANĚ OSOBNÍCH ÚDAJŮ

1. Advokát zpracovává osobní údaje v rozsahu nezbytném pro poskytování právních služeb a plnění povinností stanovených právními předpisy a stavovskými předpisy.
2. Klient bere na vědomí, že právní služby podléhají povinnosti mlčenlivosti.

IX. ZÁVĚREČNÁ USTANOVENÍ

V Praze dne 3. 6. 2026

……………………..............................
Mgr. Daniel Mlynář
Advokát

……………………..............................
Ing. Markéta Benešová
Klient
"""

    # 32) Nemocnice – informovaný souhlas + portál + kontakty
    variants[32] = """SMLOUVA O POSKYTNUTÍ ZDRAVOTNÍ PÉČE A INFORMOVANÝ SOUHLAS

uzavřená dle zákona č. 372/2011 Sb., o zdravotních službách, a souvisejících právních předpisů

I. SMLUVNÍ STRANY

1. Poskytovatel zdravotních služeb:
   Název: Krajská nemocnice Jih a.s.
   Sídlo: Nemocniční 1, 400 01 Ústí nad Labem
   IČO: 44550011
   Telefon: +420 477 111 222
   E-mail: podatelna@knjih.cz
   Kontaktní lékař: MUDr. Tomáš Hruška, nar. 28. 02. 1978, rodné číslo 780228/1234

   (dále jen „Nemocnice“)

2. Pacient:
   Jméno a příjmení: Bc. Sabina Nedvědová
   Datum narození: 30. 06. 1993
   Rodné číslo: 930630/7890
   Trvalý pobyt: Jabloňová 12, 400 01 Ústí nad Labem
   Číslo pojištěnce: 9306307890
   Telefon: +420 731 444 555
   E-mail: sabina.nedvedova@example.com
   Číslo OP: 556677889

   (dále jen „Pacient“)

II. PŘEDMĚT

1. Nemocnice poskytne Pacientovi plánované vyšetření, laboratorní testy a dle výsledků případnou hospitalizaci.
2. Pacient potvrzuje, že byl poučen o povaze výkonů, možných komplikacích, alternativách a o způsobu vedení zdravotnické dokumentace.

III. ZVLÁŠTNÍ KATEGORIE OSOBNÍCH ÚDAJŮ – ZDRAVOTNÍ ÚDAJE

1. Pacient bere na vědomí, že Nemocnice bude zpracovávat údaje o zdravotním stavu (zvláštní kategorie), zejména: diagnóza, výsledky laboratorních testů, anamnéza, medikace, alergie.
2. Pro účely testu se v textu uvádí příklady: diagnóza – hypertenze; alergie – penicilin; užívané léky – metoprolol.

IV. IDENTIFIKACE DALŠÍCH OSOB A KONTAKTŮ

1. Pacient určuje kontaktní osobu:
   Jméno a příjmení: Renata Slámová, nar. 08. 03. 1984, rodné číslo 840308/6789,
   tel. +420 606 777 222, e-mail: renata.slamova@example.com.
2. Pacient dále uvádí osobu blízkou:
   Miroslav Vaněk, nar. 11. 11. 1980, rodné číslo 801111/1234, tel. +420 603 222 111.

V. POUŽÍVÁNÍ ÚDAJŮ V TEXTU A KOMUNIKACE

1. Nemocnice bude komunikovat s Pacientem na e-mail sabina.nedvedova@example.com a telefonu +420 731 444 555.
2. Smluvní strany si jsou vědomy pádových tvarů: „Sabině Nedvědové“, „se Sabinou Nedvědovou“, „Renatě Slámové“, „s Renatou Slámovou“, „Miroslava Vaňka“, „Miroslavu Vaňkovi“.

VI. PACIENTSKÝ PORTÁL A PŘÍSTUPOVÉ ÚDAJE

1. Pacient získá přístup do pacientského portálu (výsledky, zprávy, objednání):
   Uživatelské jméno: snedvedova
   Heslo: N3mocnice!2026
2. Přístupy mohou být logovány včetně IP adres, např. 10.0.0.58 a 192.168.11.22, a identifikátoru zařízení (IMEI 356778119992110).

VII. ÚHRADA A FAKTURACE

1. Nadstandardní služby mohou být hrazeny kartou: 4111 1111 1111 2222, platnost 08/28, CVC: 123.
2. Případná fakturace: účet Nemocnice 987654321/0300; variabilní symbol 9306307890.

VIII. DOBA UCHOVÁNÍ A GDPR

1. Pacient bere na vědomí, že zdravotnická dokumentace je uchovávána po dobu stanovenou právními předpisy.
2. Nemocnice je oprávněna zpřístupnit údaje pouze oprávněným osobám a v případech stanovených zákonem.

IX. ZÁVĚR

V Ústí nad Labem dne 4. 6. 2026

……………………..............................
Bc. Sabina Nedvědová
Pacient

……………………..............................
MUDr. Tomáš Hruška
za Krajská nemocnice Jih a.s.
"""

    # 33) Škola – souhlas rodiče se zpracováním údajů žáka + poradna
    variants[33] = """SMLOUVA O POSKYTOVÁNÍ ŠKOLNÍCH PORADENSKÝCH SLUŽEB A SOUHLAS SE ZPRACOVÁNÍM OSOBNÍCH ÚDAJŮ

I. SMLUVNÍ STRANY

1. Škola:
   Název: Gymnázium Na Hradbách
   Sídlo: Na Hradbách 15, 702 00 Ostrava
   IČO: 12398745
   Telefon: +420 596 111 222
   E-mail: sekretariat@gymhradby.cz
   Kontaktní osoba: Mgr. Štěpán Hrubeš, ředitel školy

   (dále jen „Škola“)

2. Zákonný zástupce (Objednatel):
   Jméno a příjmení: Mgr. Veronika Lacinová
   Datum narození: 12. 02. 1994
   Rodné číslo: 940212/7890
   Adresa: U Lesa 9, 530 02 Pardubice
   Telefon: +420 605 123 456
   E-mail: veronika.lacinova@example.com
   Číslo OP: 987654321

   (dále jen „Zákonný zástupce“)

II. DÍTĚ / ŽÁK

1. Žák:
   Jméno a příjmení: Nikol Šťastná
   Datum narození: 02. 02. 2010
   Rodné číslo: 100202/0005
   Trvalý pobyt: Na Návsi 6, 789 01 Zábřeh
   Třída: 1.A
   Číslo žáka v systému: 1A-2010-023

III. PŘEDMĚT

1. Škola se zavazuje poskytovat školní poradenské služby (výchovné poradenství, konzultace, doporučení opatření) pro žáka Nikol Šťastnou.
2. Zákonný zástupce souhlasí se zpracováním osobních údajů žáka a svých údajů v rozsahu nezbytném pro poskytování poradenství.

IV. ZVLÁŠTNÍ ÚDAJE A KONTEXT

1. Zákonný zástupce bere na vědomí, že v rámci poradenství mohou být zpracovávány i citlivé informace (např. doporučení PPP, projevy úzkosti, logopedická péče).
2. Pro účely testu se v textu vyskytují tvary: „Nikol Šťastné“, „s Nikol Šťastnou“, „Veronice Lacinové“, „s Veronikou Lacinovou“, „Veroniky Lacinové“.

V. PŘÍSTUP DO ŠKOLNÍHO SYSTÉMU

1. Škola poskytne Zákonnému zástupci přístup do systému (e-žákovská knížka):
   Uživatelské jméno: vlacinova
   Heslo: Sk0la!2026
   IP přihlášení (typicky): 85.95.12.34
2. Zákonný zástupce je povinen udržovat přístupové údaje v tajnosti.

VI. KOMUNIKACE

1. Komunikace probíhá e-mailem na sekretariat@gymhradby.cz a veronika.lacinova@example.com, případně telefonicky na +420 596 111 222 a +420 605 123 456.

VII. DOBA TRVÁNÍ

1. Tato smlouva se uzavírá na dobu školní docházky žáka na této škole, nejdéle do 30. 6. 2028.

VIII. GDPR

1. Škola zpracovává údaje na základě právní povinnosti a oprávněného zájmu, případně souhlasu u vybraných údajů.

IX. ZÁVĚR

V Ostravě dne 6. 6. 2026

……………………..............................
Mgr. Veronika Lacinová
Zákonný zástupce

……………………..............................
Mgr. Štěpán Hrubeš
ředitel školy
"""

    # 34) Sociální služby – domov se zvláštním režimem + opatrovník
    variants[34] = """SMLOUVA O POSKYTOVÁNÍ SOCIÁLNÍ SLUŽBY

uzavřená dle zákona č. 108/2006 Sb., o sociálních službách

I. SMLUVNÍ STRANY

1. Poskytovatel:
   Název: Domov Harmonie, příspěvková organizace
   Sídlo: Lázeňská 89, 602 00 Brno
   IČO: 66770011
   Telefon: +420 541 222 333
   E-mail: info@domovharmonie.cz

   (dále jen „Poskytovatel“)

2. Uživatel služby:
   Jméno a příjmení: Václav Svoboda
   Datum narození: 30. 05. 1960
   Rodné číslo: 600530/1111
   Trvalý pobyt: Na Kopci 12, 100 00 Praha 10
   Telefon: +420 602 333 444

   (dále jen „Uživatel“)

3. Opatrovník / kontaktní osoba:
   Jméno a příjmení: Petra Svobodová
   Datum narození: 22. 11. 1990
   Rodné číslo: 901122/4567
   Adresa: Křenová 14, 602 00 Brno
   Telefon: +420 603 987 654
   E-mail: petra.svobodova@example.com

II. PŘEDMĚT

1. Poskytovatel se zavazuje poskytovat Uživatelovi pobytovou sociální službu včetně ubytování, stravy, pomoci při zvládání běžných úkonů, aktivizačních činností a doprovodu k lékaři.
2. Uživatel bere na vědomí, že v souvislosti s poskytováním služby budou zpracovávány jeho osobní údaje a údaje o zdravotním stavu (např. diagnóza: demence, diabetes; medikace).

III. DALŠÍ OSOBY

1. Uživatel uvádí další blízké osoby:
   a) Dcera: Lucie Malá, nar. 09. 09. 1993, rodné číslo 930909/7890, e-mail: lucie.mala@example.org, tel. +420 605 444 555.
   b) Kontaktní osoba pro krizové situace: Tomáš Svoboda, nar. 01. 02. 1988, rodné číslo 880201/3210, tel. +420 602 111 222.

IV. POUŽÍVÁNÍ ÚDAJŮ V TEXTU

1. Smluvní strany si jsou vědomy pádových tvarů: „Václavu Svobodovi“, „s Václavem Svobodou“, „Petře Svobodové“, „s Petrou Svobodovou“, „Lucii Malé“, „s Lucií Malou“.
2. Poskytovatel může informovat Petru Svobodovou o zdravotním stavu Václava Svobody v rozsahu nezbytném pro poskytování služby.

V. ÚHRADA

1. Úhrada za službu činí 14 900 Kč měsíčně a bude hrazena převodem na účet Poskytovatele 123456789/0100.
2. Variabilní symbol: 6005301111.
3. Případné doplatky budou hrazeny z účtu opatrovníka 987654321/0300.

VI. DOBA TRVÁNÍ

1. Smlouva se uzavírá na dobu neurčitou, počínaje dnem 1. 7. 2026.

VII. GDPR

1. Poskytovatel zpracovává údaje na základě právních povinností a pro poskytování sociální služby.

VIII. ZÁVĚR

V Brně dne 10. 6. 2026

……………………..............................
Václav Svoboda
Uživatel

……………………..............................
Petra Svobodová
Opatrovník
"""

    # 35) Soudy – plná moc + doručování + citlivé údaje v přílohách
    variants[35] = """PLNÁ MOC A DOHODA O ZASTUPOVÁNÍ V ŘÍZENÍ

I. ZMOCNITEL

Jméno a příjmení: Adam Král
Datum narození: 10. 01. 1975
Rodné číslo: 750110/5678
Adresa: Na Výšinách 25, 170 00 Praha 7
Telefon: +420 602 222 333
E-mail: adam.kral@example.com
Číslo OP: 445566778

II. ZMOCNĚNEC (ADVOKÁT)

Jméno a příjmení: JUDr. Pavel Král, ev. č. ČAK 54321
Sídlo: Právnická 12, 110 00 Praha 1
Telefon: +420 222 555 101
E-mail: pavel.kral@advokat.cz
Datová schránka: z9y8x7w

III. PŘEDMĚT

1. Zmocnitel tímto zmocňuje Zmocněnce k zastupování ve věci vedené u Obvodního soudu pro Prahu 3, sp. zn. 15 C 456/2026.
2. Zmocněnec je oprávněn přijímat doručování, podávat návrhy, opravné prostředky a činit veškeré úkony.

IV. IDENTIFIKACE DALŠÍCH OSOB

1. V řízení vystupuje protistrana: Jana Procházková, nar. 05. 05. 1992, RČ 920505/1234, adresa: Dlouhá 8, 602 00 Brno, e-mail: jana.prochazkova@example.com.
2. Svědek: Matěj Procházka, nar. 15. 09. 1991, RČ 910915/7890, tel. +420 608 999 000.

V. POUŽÍVÁNÍ ÚDAJŮ V TEXTU

1. V podáních se mohou objevovat tvary: „Adamu Královi“, „s Adamem Králem“, „Jany Procházkové“, „Janě Procházkové“, „s Janou Procházkovou“, „Matěje Procházky“.
2. Přílohy mohou obsahovat bankovní údaje (např. 1122334455/5500), e-maily, telefonní čísla a kopie dokladů.

VI. ODMĚNA

1. Odměna bude sjednána dle advokátního tarifu; záloha 10 000 Kč na účet 112882351/0300.
2. Variabilní symbol: 7501105678.

VII. GDPR

1. Zmocněnec zpracovává údaje v rámci poskytování právních služeb a plnění právních povinností.

VIII. ZÁVĚR

V Praze dne 12. 6. 2026

……………………..............................
Adam Král

……………………..............................
JUDr. Pavel Král
"""

    # 36) Nemocnice – zpracovatelská smlouva GDPR s IT dodavatelem (pacientské systémy)
    variants[36] = """SMLOUVA O ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ (GDPR) – NEMOCNIČNÍ INFORMAČNÍ SYSTÉM

uzavřená dle čl. 28 Nařízení (EU) 2016/679 (GDPR)

I. SMLUVNÍ STRANY

1. Správce:
   Název: Krajská nemocnice Jih a.s.
   Sídlo: Nemocniční 1, 400 01 Ústí nad Labem
   IČO: 44550011
   Kontaktní e-mail: dpo@knjih.cz
   Telefon: +420 477 111 222

   (dále jen „Správce“)

2. Zpracovatel:
   Název: HealthIT Services s.r.o.
   Sídlo: Serverová 22, 639 00 Brno
   IČO: 87654321
   Kontaktní osoba: Igor Vraný, nar. 03. 04. 1980, RČ 800403/5678, tel. +420 608 444 777, e-mail: igor.vrany@healthit.cz

   (dále jen „Zpracovatel“)

II. PŘEDMĚT

1. Správce pověřuje Zpracovatele správou a provozem nemocničního informačního systému (NIS), v němž jsou zpracovávány osobní údaje pacientů.
2. Typy údajů: jméno, příjmení, datum narození, rodné číslo, adresa, kontakt, údaje o hospitalizaci, diagnózy, výsledky vyšetření, medikace.

III. PŘÍKLADY DAT A KONTAKTŮ (PRO TEST)

1. V systému se mohou nacházet údaje pacientů, např. „Sabině Nedvědové“ (RČ 930630/7890), e-mail sabina.nedvedova@example.com, tel. +420 731 444 555, nebo „Renatě Slámové“ (RČ 840308/6789).
2. Údaje o přístupu:
   Admin účet: admin.nis
   Heslo: NIS!Adm1n2026
   IP přístupy: 185.22.33.44, 192.168.11.22
   MAC: 00:11:22:33:44:55

IV. BEZPEČNOST A AUDIT

1. Zpracovatel vede auditní logy přístupů (uživatel, IP, čas, akce).
2. Zpracovatel umožní Správci provést audit po předchozí dohodě.

V. DOBA TRVÁNÍ

1. Smlouva se uzavírá na dobu určitou od 1. 7. 2026 do 30. 6. 2029.

VI. ZÁVĚR

V Ústí nad Labem dne 20. 6. 2026

……………………..............................
za Správce

……………………..............................
Igor Vraný
za Zpracovatele
"""

    # 37) Úřad – žádost o nahlížení do spisu + doručování + kontakty
    variants[37] = """ŽÁDOST O NAHLÍŽENÍ DO SPISU A SOUVISEJÍCÍ SOUHLASY SE ZPRACOVÁNÍM ÚDAJŮ

I. ŽADATEL

Jméno a příjmení: Gabriela Štěpánová
Datum narození: 01. 01. 1990
Rodné číslo: 900101/2222
Adresa: U Parku 8, 779 00 Olomouc
Telefon: +420 603 987 654
E-mail: gabriela.stepanova@example.com
Číslo OP: 123456789

II. SPRÁVNÍ ORGÁN

Název: Městský úřad Nový Brod
Sídlo: Náměstí 1, 500 02 Hradec Králové
Telefon: +420 495 888 111
E-mail: podatelna@novybrod.cz

III. PŘEDMĚT

1. Žadatel žádá o nahlížení do spisu vedeného pod č. j. MU-NB/2026/12345.
2. Žadatel žádá o zaslání kopií dokumentů na e-mail gabriela.stepanova@example.com a v listinné podobě na adresu U Parku 8, 779 00 Olomouc.

IV. DALŠÍ OSOBY

1. Ve spise se nacházejí osobní údaje dalších osob, např. Tomáš Nguyen (tel. +420 605 444 555, e-mail tomas.nguyen@example.net) a Petra Svobodová (petra.svobodova@example.com).
2. V textu se mohou vyskytovat tvary: „Gabriele Štěpánové“, „s Gabrielou Štěpánovou“, „Tomáši Nguyenovi“, „s Tomášem Nguyenem“.

V. PŘÍSTUP DO PORTÁLU

1. Pro přístup do elektronické spisové služby:
   Uživatelské jméno: gstepanova
   Heslo: Spis!2026
   IP: 85.95.12.34

VI. ZÁVĚR

V Hradci Králové dne 25. 6. 2026

……………………..............................
Gabriela Štěpánová
"""

    # 38) Škola + dodavatel – smlouva o provozu IS (e-žk) + rodiče/žáci
    variants[38] = """SMLOUVA O PROVOZU ŠKOLNÍHO INFORMAČNÍHO SYSTÉMU A ZPRACOVÁNÍ OSOBNÍCH ÚDAJŮ

I. SMLUVNÍ STRANY

1. Škola (Správce):
   Název: Gymnázium Na Hradbách
   Sídlo: Na Hradbách 15, 702 00 Ostrava
   IČO: 12398745
   Telefon: +420 596 111 222
   E-mail: sekretariat@gymhradby.cz
   Zastoupená: Mgr. Štěpán Hrubeš

2. Dodavatel (Zpracovatel):
   Název: EduCloud Systems s.r.o.
   Sídlo: U Kampusu 9, 625 00 Brno
   IČO: 98732145
   Kontaktní osoba: Kamil Řezníček, RČ 860921/4444, tel. +420 725 666 999, e-mail: kamil.reznicek@educloud.cz

II. PŘEDMĚT

1. Zpracovatel se zavazuje provozovat systém pro evidenci žáků, rozvrh, klasifikaci a komunikaci s rodiči.
2. Typické údaje: jméno, příjmení, datum narození, adresa, zákonný zástupce, kontakty, poznámky k podpůrným opatřením.

III. PŘÍKLADY (PRO TEST)

1. Žák: Nikol Šťastná (RČ 100202/0005), zákonný zástupce: Veronika Lacinová (veronika.lacinova@example.com, +420 605 123 456).
2. V textu se mohou objevovat tvary: „Nikol Šťastné“, „s Nikol Šťastnou“, „Veronice Lacinové“, „s Veronikou Lacinovou“.

IV. PŘÍSTUPY

1. Admin školy:
   Uživatelské jméno: shrubes
   Heslo: Gymn4zium!2026
2. Servisní účet dodavatele:
   Uživatelské jméno: servis.educloud
   Heslo: EduCl0ud?2026
3. Logování přístupů: IP 85.95.12.34, 85.95.12.35, MAC 00:25:96:FF:EE:11.

V. DOBA TRVÁNÍ

1. Smlouva se uzavírá na dobu určitou od 1. 9. 2026 do 31. 8. 2030.

VI. ZÁVĚR

V Ostravě dne 30. 6. 2026

……………………..............................
Mgr. Štěpán Hrubeš

……………………..............................
Kamil Řezníček
"""

    # 39) Lékařství práce – pracovnělékařské služby pro firmu + zaměstnanci
    variants[39] = """SMLOUVA O POSKYTOVÁNÍ PRACOVNĚLÉKAŘSKÝCH SLUŽEB

I. SMLUVNÍ STRANY

1. Poskytovatel:
   Název: PrivatMed Clinic s.r.o.
   Sídlo: Poliklinická 3, 120 00 Praha 2
   IČO: 99887766
   Telefon: +420 224 333 444
   E-mail: recepce@privatmed.cz
   Lékař: MUDr. Tomáš Hruška, RČ 780228/1234

2. Zaměstnavatel (Objednatel):
   Název: DataSecure Solutions s.r.o.
   Sídlo: Technologická 15, 160 00 Praha 6
   IČO: 05288977
   Kontakt: Ing. Radek Holík, RČ 820718/4321, tel. +420 739 111 222, e-mail: radek.holik@datasecure.cz

II. PŘEDMĚT

1. Poskytovatel bude provádět vstupní, periodické a mimořádné prohlídky zaměstnanců Zaměstnavatele.
2. V rámci služeb budou zpracovávány zdravotní údaje (zvláštní kategorie), výsledky vyšetření a posudky o zdravotní způsobilosti.

III. SEZNAM OSOB (PŘÍKLADY PRO TEST)

1. Zaměstnanec: Veronika Lacinová, RČ 940212/7890, e-mail: veronika.lacinova@example.com, tel. +420 605 123 456.
2. Zaměstnanec: Erik Roubal, RČ 800909/3333, e-mail: erik.roubal@example.com, tel. +420 739 555 777.
3. V dokumentaci se mohou objevit tvary: „Veronice Lacinové“, „s Veronikou Lacinovou“, „Erika Roubala“, „s Erikem Roubalem“.

IV. KOMUNIKACE A DORUČOVÁNÍ POSUDKŮ

1. Posudky budou předávány osobně nebo zabezpečeně; výjimečně zaslány na e-mail radek.holik@datasecure.cz.
2. Faktury budou zasílány na info@datasecure.cz.

V. ÚHRADA

1. Cena prohlídky: 950 Kč / osoba; fakturace měsíčně.
2. Úhrada na účet 6655443322/5500; variabilní symbol 05288977.

VI. ZÁVĚR

V Praze dne 5. 7. 2026

……………………..............................
MUDr. Tomáš Hruška

……………………..............................
Ing. Radek Holík
"""

    # 40) Soudy/právo – mediace + citlivé údaje v přílohách, více kontextu
    variants[40] = """SMLOUVA O MEDIACI A MLČENLIVOSTI

uzavřená dle zákona č. 202/2012 Sb., o mediaci

I. SMLUVNÍ STRANY

1. Mediátor:
   Jméno a příjmení: Mgr. Robert Vlach
   Datum narození: 03. 04. 1980
   Rodné číslo: 800403/5678
   Adresa: Na Kopci 3, 625 00 Brno
   Telefon: +420 608 444 777
   E-mail: robert.vlach@cloudata.cz
   Bankovní účet: 4455667789/0300

2. Účastník A:
   Jméno a příjmení: Jana Procházková
   Datum narození: 05. 05. 1992
   Rodné číslo: 920505/1234
   Adresa: Dlouhá 8, 602 00 Brno
   Telefon: +420 777 555 444
   E-mail: jana.prochazkova@example.com
   Číslo OP: 987654321

3. Účastník B:
   Jméno a příjmení: Matěj Procházka
   Datum narození: 15. 09. 1991
   Rodné číslo: 910915/7890
   Adresa: Dlouhá 8, 602 00 Brno
   Telefon: +420 608 999 000
   E-mail: matej.prochazka@example.org

II. PŘEDMĚT

1. Účastníci A a B žádají mediaci ve sporu týkajícím se vypořádání společného bydlení a úhrady nákladů.
2. Mediátor provede nejméně tři sezení a vypracuje mediační dohodu.

III. DALŠÍ OSOBY A DOKUMENTY

1. Účastníci uvádějí svědka: Klára Procházková, nar. 20. 12. 1995, RČ 951220/4567, tel. +420 604 333 222.
2. V přílohách mohou být bankovní údaje (např. 1122334455/5500), e-maily, telefonní čísla, případně citlivé informace o zdravotním stavu (např. psychologická péče).

IV. POUŽÍVÁNÍ OSOBNÍCH ÚDAJŮ V TEXTU

1. Smluvní strany si jsou vědomy pádových tvarů: „Janě Procházkové“, „s Janou Procházkovou“, „Matěje Procházky“, „Matějovi Procházkovi“, „Kláry Procházkové“.
2. Komunikace bude probíhat e-mailem na robert.vlach@cloudata.cz, jana.prochazkova@example.com a matej.prochazka@example.org.

V. PŘÍSTUPOVÉ ÚDAJE

1. Účastníci předají dokumenty přes sdílenou složku:
   Uživatelské jméno: mediace.prochazka
   Heslo: M3diace!2026
   IP: 85.95.12.34

VI. ODMĚNA

1. Odměna Mediátora činí 1 800 Kč/h, hrazena převodem na účet 4455667789/0300.
2. Variabilní symbol: 9205051234.

VII. MLČENLIVOST A GDPR

1. Mediátor a účastníci se zavazují k mlčenlivosti o skutečnostech sdělených v mediaci.
2. Osobní údaje budou použity pouze pro účely mediace.

VIII. ZÁVĚR

V Brně dne 8. 7. 2026

……………………..............................
Mgr. Robert Vlach

……………………..............................
Jana Procházková

……………………..............................
Matěj Procházka
"""

    for idx, text in variants.items():
        stem = f"smlouva_gdpr_test_{idx:02d}"
        write_txt_and_docx(stem, text)
        print("Wrote", stem)


if __name__ == "__main__":
    main()

