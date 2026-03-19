#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate SKRYI FINAL consolidated report from 4 source documents."""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fpdf import FPDF
from datetime import datetime

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")


class FinalReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DV", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
        self.add_font("DV", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DV", "", 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, "SKRYI Document Suite  |  Final Report & Strategic Plan  |  CONFIDENTIAL", align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("DV", "", 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"(c) 2026 Nixminds s.r.o.  --  Strana {self.page_no()}", align="C")

    # ---- layout helpers ----
    def title_page(self):
        self.add_page()
        self.ln(40)
        self.set_font("DV", "B", 30)
        self.set_text_color(20, 50, 110)
        self.cell(0, 15, "SKRYI Document Suite", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font("DV", "B", 15)
        self.set_text_color(60, 60, 60)
        self.cell(0, 10, "Final Report & Strategic Plan", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_font("DV", "", 11)
        self.set_text_color(90, 90, 90)
        self.cell(0, 8, "Offline GDPR Anonymization Platform for Inflective Languages", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(25)
        self._hline(50)
        self.ln(10)
        self.set_font("DV", "", 10)
        self.set_text_color(60, 60, 60)
        for line in [
            f"Datum: {datetime.now().strftime('%d. %m. %Y')}",
            "Verze dokumentu: Final v3.1 (2026-03-18)",
            "Klasifikace: CONFIDENTIAL",
            "",
            "Pripravil: Nixminds s.r.o.",
            "Segment: RegTech / LegalTech / Cybersecurity",
        ]:
            self.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

    def _hline(self, inset=10):
        self.set_draw_color(20, 50, 110)
        self.set_line_width(0.5)
        self.line(inset, self.get_y(), self.w - inset, self.get_y())

    def h1(self, text):
        self.ln(3)
        self.set_font("DV", "B", 16)
        self.set_text_color(20, 50, 110)
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        self._hline(self.l_margin)
        self.ln(4)

    def h2(self, text):
        self.ln(2)
        self.set_font("DV", "B", 13)
        self.set_text_color(40, 70, 130)
        self.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def h3(self, text):
        self.ln(1)
        self.set_font("DV", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def p(self, text):
        self.set_font("DV", "", 10)
        self.set_text_color(35, 35, 35)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def b(self, text):
        self.set_font("DV", "", 10)
        self.set_text_color(35, 35, 35)
        self.cell(6, 6, chr(8226))
        self.multi_cell(0, 6, text)
        self.ln(1)

    def tbl(self, headers, rows, widths=None):
        if widths is None:
            w = (self.w - self.l_margin - self.r_margin) / len(headers)
            widths = [w] * len(headers)
        self.set_font("DV", "B", 9)
        self.set_fill_color(20, 50, 110)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(widths[i], 8, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("DV", "", 9)
        self.set_text_color(35, 35, 35)
        alt = False
        for row in rows:
            if self.get_y() > self.h - 30:
                self.add_page()
            self.set_fill_color(238, 242, 250) if alt else self.set_fill_color(255, 255, 255)
            for i, c in enumerate(row):
                self.cell(widths[i], 8, str(c), border=1, fill=True)
            self.ln()
            alt = not alt
        self.ln(3)

    def kv_table(self, pairs, w1=65, w2=115):
        """Key-value two-column table."""
        self.set_font("DV", "B", 9)
        self.set_fill_color(20, 50, 110)
        self.set_text_color(255, 255, 255)
        self.cell(w1, 8, "Metrika", border=1, fill=True, align="C")
        self.cell(w2, 8, "Hodnota", border=1, fill=True, align="C")
        self.ln()
        self.set_text_color(35, 35, 35)
        alt = False
        for k, v in pairs:
            self.set_fill_color(238, 242, 250) if alt else self.set_fill_color(255, 255, 255)
            self.set_font("DV", "B", 9)
            self.cell(w1, 8, k, border=1, fill=True)
            self.set_font("DV", "", 9)
            self.cell(w2, 8, v, border=1, fill=True)
            self.ln()
            alt = not alt
        self.ln(3)


def build():
    pdf = FinalReportPDF()

    # =====================================================================
    #  TITLE PAGE
    # =====================================================================
    pdf.title_page()

    # =====================================================================
    #  TABLE OF CONTENTS
    # =====================================================================
    pdf.add_page()
    pdf.h1("Obsah")
    toc = [
        "1.  Executive Summary",
        "2.  Trh a legislativni katalyzatory 2026",
        "3.  Produkt a technologicke jadro",
        "4.  Technicke konkurencni vyhody (Unfair Advantage)",
        "5.  Validace kvality a produkcni pripravenost",
        "6.  Cilove trhy a segmentace",
        "7.  Konkurencni analyza",
        "8.  Cenova strategie a licencni model",
        "9.  Revenue model a financni projekce",
        "10. Go-to-Market strategie",
        "11. SWOT analyza",
        "12. Rizika a mitigace",
        "13. Tim a organizace",
        "14. Produkcni roadmapa",
        "15. Akcni plan (30 dni)",
        "16. Zaver a klicova doporuceni",
    ]
    for t in toc:
        pdf.p(t)

    # =====================================================================
    #  1. EXECUTIVE SUMMARY
    # =====================================================================
    pdf.add_page()
    pdf.h1("1. Executive Summary")
    pdf.p(
        "SKRYI Document Suite resi kriticky problem uniku osobnich udaju (PII) "
        "v dokumentech zpusobeny neschopnosti beznych nastroju sklonovat v cestine. "
        "Zatimco globalni konkurence selhava u padovych forem jmen, SKRYI diky "
        "bidirekcionalni morfologicke inferenci dosahuje 97-99% presnosti anonymizace."
    )
    pdf.p(
        "Na trhu neexistuje srovnatelny produkt, ktery by kombinoval: (1) morfologickou "
        "inteligenci pro sklonnovani jmen ve vsech 7 padech, (2) plne offline provoz, "
        "(3) 34 kategorii PII, (4) reverzibilni anonymizaci s klicem, a (5) automaticky OCR vstup."
    )
    pdf.p(
        "Produkt je ve stavu Production Ready (v3.1.0). Byl overen na korpusu 241 "
        "syntetickych smluv pokryvajicich 6 sektoru. Manualni audit potvrdil nulovy "
        "pocet skutecnych uniku osobnich udaju. Verze 3.1 prinesla opravy klasifikace "
        "(INSURANCE_ID vs PHONE, vokativni deduplikace, kontextova filtrace SPZ)."
    )
    pdf.p(
        "V roce 2026, pod tlakem nove legislativy (AI Act, EHDS, smernice o transparentnosti "
        "odmenovani), se SKRYI stava nezbytnym nastrojem pro bezpecne nakladani s daty."
    )

    pdf.h2("Klicova cisla")
    pdf.kv_table([
        ("Kategorie PII", "34 typu (jmena, adresy, RC, IBAN, SPZ, VIN, SSH klice...)"),
        ("Knihovna jmen", "~7 000 unikatnich ceskych/mezinarodn. krestnich jmen (+ stovky tisic padovych tvaru)"),
        ("Presnost anonymizace", "97-99 % (overeno na 241 smlouvach)"),
        ("Doba zpracovani", "< 2 s / dokument (typicka smlouva 3-5 stran)"),
        ("Offline rezim", "100 % -- zadna data neopousteji zarizeni"),
        ("OCR podpora", "PDF, PNG, JPG, TIFF, BMP, WEBP"),
        ("Platforma", "Windows 10/11 (desktop)"),
        ("Technologie", "Electron + Python (Nuitka compiled)"),
        ("Globalni trh GDPR", "$3.34 mld (2025) -> $13.71 mld (2030), CAGR 25.6 %"),
    ])

    # =====================================================================
    #  2. MARKET & LEGISLATIVE CATALYSTS
    # =====================================================================
    pdf.add_page()
    pdf.h1("2. Trh a legislativni katalyzatory 2026")

    pdf.h2("2.1 Globalni trh")
    pdf.p(
        "Globalni trh GDPR sluzeb dosahne dle odhadu $13.71 mld do roku 2030 "
        "(z $3.34 mld v 2025, rocni rust ~25.6 %). Evrope jako rodisti GDPR patri "
        "dominantni podil. Segment BFSI (banky, pojistovny) tvori cca 35 % poptavky."
    )

    pdf.h2("2.2 Regulatorni katalyzatory v 2026")
    pdf.p(
        "Rok 2026 je pro SKRYI klicovy diky soubehu nekolika regulatornich pozadavku:"
    )
    pdf.b(
        "EHDS (Evropsky prostor pro zdravotni data): Povinnost sdileni dat pro vyzkum "
        "vyzaduje certifikovanou anonymizaci. SKRYI umoznuje nemocnicim procesovat data lokalne."
    )
    pdf.b(
        "EU AI Act (plna ucinnost od 2.8.2026): Firmy trenujici vlastni modely musi "
        "garantovat ochranu soukromi. SKRYI slouzi jako 'enabler' pro legalni pripravu datasetu."
    )
    pdf.b(
        "Smernice o transparentnosti odmenovani (cerven 2026): Nutnost anonymizovat "
        "mzdove listy pro reporting Gender Pay Gap."
    )
    pdf.b(
        "Novela zakona o zdravotnich sluzbach: Povinne klinicke audity (EKA) vyzaduji "
        "bezpecne zpristupneni dokumentace externim auditorum."
    )
    pdf.b(
        "NIS2: Zprisnene pozadavky na kybernetickou bezpecnost pro kritickou infrastrukturu "
        "vcetne zdravotnictvi, energetiky a financniho sektoru."
    )

    pdf.h2("2.3 Inflektivni jazyky = specialni problem")
    pdf.p(
        "Existujici anonymizacni nastroje (Presidio, AWS Comprehend, Google DLP) jsou navrhovany "
        "pro anglictinu. V cestine a slovenstine se jmena sklonjuji -- 'Jan Novak' ma 14+ tvaru "
        "(Jana Novaka, Janu Novakovi, Janem Novakem...). Stavajici reseni tyto tvary "
        "nerozpoznavaji, coz vede k data leakum."
    )
    pdf.p(
        "Problem se netyka jen cestiny: polstina, slovenstina, chorvatstina, slovinstina, "
        "madarstina -- stovky milionu uzivatelu v EU bez adekvat. nastroje."
    )

    pdf.h2("2.4 Offline pozadavek")
    pdf.p(
        "Advokatni kancelare, soudy, nemocnice a ministerstva nesmeji posilat citlive "
        "dokumenty do cloudu. SKRYI je jediny produkt na trhu, ktery to resil s plnou "
        "morfologickou podporou -- tzv. 'true zero trust'."
    )

    # =====================================================================
    #  3. PRODUCT
    # =====================================================================
    pdf.add_page()
    pdf.h1("3. Produkt a technologicke jadro")

    pdf.h2("3.1 Funkce produktu")
    pdf.tbl(
        ["Funkce", "Popis"],
        [
            ["Anonymizace DOCX", "Automat. detekce a nahrazeni 34 kategorii PII tagy [[OSOBA_1]] atd."],
            ["Deanonymizace", "Zpetna rekonstrukce puvodniho dokumentu pomoci klice (_map.json)"],
            ["OCR konverze", "PDF / obrazky (PNG, JPG, TIFF, BMP, WEBP) -> DOCX pres Tesseract"],
            ["Hromadne zpracovani", "Automaticky watcher -- slozkovy rezim pro davkove zpracovani"],
            ["PDF certifikat", "Automaticky audit trail: SHA-256 otisk, statistiky, GDPR dolozka"],
            ["Morfol. inteligence", "7 padu x 2 cisla x privlastnovaci tvary pro ceska jmena"],
            ["Standalone krestni jm.", "Post-pass zachyti i samostatne stojici krestni jmena (Barbora, Jakubovi)"],
            ["Sektorovy blacklist", "500+ chranenych slov v 6 oborech + 267 instituci (data-driven)"],
            ["Kontextova klasifikace PHONE", "VS: a cisla pojistence nejsou chybne tagovana jako telefon (v3.1)"],
            ["Vokativni deduplikace", "Zenske vokativy (Petro, Martino) slouceny s nominativem (v3.1)"],
            ["Kontextova filtrace SPZ", "Cisla protokolu (NB2004) nejsou chybne tagovana jako SPZ (v3.1)"],
            ["Viceslovna cizi jmena", "Bezpecne zpracovani jmen typu 'Mai Linh Nguyenova'"],
            ["Hardwarova licence", "HW-ID binding, AppData persistence, offline validace"],
        ],
        [48, 132],
    )

    pdf.h2("3.2 Technologicky stack")
    pdf.tbl(
        ["Vrstva", "Technologie", "Proc"],
        [
            ["GUI", "Electron + HTML/CSS/JS", "Moderni UI, rychly vyvoj, Win installer"],
            ["Backend", "Python 3.11", "NLP ekosystem, python-docx, fpdf2"],
            ["Kompilace", "Nuitka", "Ochrana kodu, nativni rychlost, bez Py runtime"],
            ["Baleni", "electron-builder + NSIS", "Profesionalni installer (~100 MB)"],
            ["OCR", "Tesseract + Poppler", "Open-source, lokalni, cestina"],
            ["Licence", "HMAC + HW fingerprint", "Offline validace, anti-piracy"],
        ],
        [30, 55, 95],
    )

    pdf.h2("3.3 Bezpecnostni architektura")
    pdf.b("Zdrojovy kod chranen Nuitka kompilaci (binarne .pyd/.exe) -- bez plaintext Pythonu")
    pdf.b("Licence vazana na HW ID (CPU + MAC + S/N disku) -- znemoznuje nelegalni sireni")
    pdf.b("Zadna sitova komunikace -- plne air-gapped prostredi")
    pdf.b("EULA explicitne stanovuje nutnost finalni lidske kontroly vystupu")

    # =====================================================================
    #  4. COMPETITIVE ADVANTAGES
    # =====================================================================
    pdf.add_page()
    pdf.h1("4. Technicke konkurencni vyhody (Unfair Advantage)")

    pdf.p(
        "SKRYI ma nekolik patentovatelnych inovaci, ktere ho odlisuji od vsech existujicich reseni:"
    )

    advantages = [
        ("1. Bidirekcionalni morfologicka inference",
         "Z libovolneho padu odvodi nominativ a naopak. Zadny konkurent toto neumi pro cestinu. "
         "Napr. 's Janem Novakem' -> SKRYI odvodi 'Jan Novak' a nahradi vsech 14+ tvaru."),
        ("2. Prioritizovany kaskadovy system padovych pravidel",
         "Eliminuje ambiguitu ('Karlu' -> 'Karel', ne 'Karl') pomoci presne definovaneho poradi pravidel."),
        ("3. 4-fazova deduplikace osob",
         "Slucuje duplicitni osoby: totozna jmena -> podmnoziny variant -> muz/zena -> preklepy/OCR chyby."),
        ("4. Standalone first-name post-pass",
         "Zachyti krestni jmena ve vsech padech, i kdyz se vyskytuji bez prijmeni "
         "('Barbora uhradi Jakubovi...' -> '[[OSOBA_1]] uhradi [[OSOBA_2]]...')."),
        ("5. Orphan surname absorption",
         "Bezpecne zpracuje viceslovna cizi jmena ('Mai Linh Nguyenova') vcetne prijmeni."),
        ("6. Inteligentni absorpce mestskych ctvrti",
         "Resi ceske adresy s ctvrtemi za pomlckou ('Praha 3 - Vinohrady')."),
        ("7. Data-driven institucionalni blacklist",
         "267 instituci (banky, univerzity, nemocnice) + 500+ roli -> minimalni false positives."),
        ("7a. Kontextova klasifikace PHONE (v3.1)",
         "Variabilni symboly (VS:) a cisla pojistence nejsou chybne tagovana jako telefon diky "
         "analyze 40 znaku kontextu pred cislem. _remove_phone_idcard_overlap rozsirena o INSURANCE_ID."),
        ("7b. Vokativni deduplikace (v3.1)",
         "Zenske vokativy (Petro, Martino, Jano) jsou rozpoznany jako tvary zenskych jmen a slouceny "
         "s nominativem. Gender-fix rozsiren o detekci -o koncovek jako fem. vokativu."),
        ("7c. Kontextova filtrace SPZ (v3.1)",
         "Cisla protokolu a lekarskych zaznamu (NB2004) nejsou chybne tagovana jako SPZ diky "
         "kontextove kontrole (protokol, nemocnice, pacient, vysetreni)."),
        ("8. 100% offline architektura",
         "Zadna data neopousteji zarizeni. Klicovy pozadavek pro advokaty, soudy, nemocnice."),
        ("9. 34 kategorii PII",
         "Nejsirsi pokryti na trhu: od jmen a RC pres IBAN, SSH klice, RFID, az po socialni site."),
    ]
    for title, desc in advantages:
        pdf.h3(title)
        pdf.p(desc)

    # =====================================================================
    #  5. QUALITY VALIDATION
    # =====================================================================
    pdf.add_page()
    pdf.h1("5. Validace kvality a produkcni pripravenost")

    pdf.h2("5.1 Stav produktu")
    pdf.tbl(
        ["Oblast", "Stav", "Detail"],
        [
            ["Anonymizacni engine", "Production Ready", "v3.1.0, ~8 250 radku, 34 PII kategorii"],
            ["GUI (Electron)", "Production Ready", "Single-file HTML, 4 taby, dark theme"],
            ["OCR konverze", "Production Ready", "PDF + 5 obrazkovych formatu"],
            ["Deanonymizace", "Production Ready", "Plne reverzibilni"],
            ["Hromadne zpracovani", "Production Ready", "3 watchery (anon/deanon/PDF)"],
            ["Licencni system", "Production Ready", "HW-bound, AppData persistence"],
            ["PDF certifikat", "Production Ready", "SHA-256, GDPR dolozka"],
            ["Windows installer", "Production Ready", "NSIS, ~100 MB"],
            ["Dokumentace", "Kompletni", "Technicka + verejna + EULA"],
        ],
        [48, 38, 84],
    )

    pdf.h2("5.2 Vysledky validace")
    pdf.tbl(
        ["Test", "Rozsah", "Vysledek"],
        [
            ["Standardni validator", "241 smluv", "100 % PASS"],
            ["Striktni validator (V2)", "241 smluv", "100 % PASS"],
            ["Brute-force cross-check", "241 smluv", "0 realnych leaku"],
            ["Manualni audit", "241 smluv (1 po 1)", "0 realnych leaku, v3.1 opravy klasifikace"],
            ["Stress-test (cizi jmena)", "15 specialnich smluv", "100 % PASS"],
            ["Regresni test po oprave", "241 smluv (re-anonymizace)", "239 OK, 2 OSError (ukladani)"],
        ],
        [48, 45, 77],
    )

    pdf.h2("5.3 Testovaci korpus")
    pdf.p(
        "Testovaci korpus obsahuje 241 syntetickych smluv: pracovni, kupni, najemni, "
        "trestni spisy, lekarske zpravy, rodinnepravni, financni, exekucni prikazy, "
        "darovaci a dalsi. Smlouvy obsahuji ceska i zahranicni jmena (vietnamska, "
        "nemecka, polska, anglicka), SSH klice, RFID identifikatory, LinkedIn profily, "
        "datove schranky a dalsi PII."
    )

    pdf.h2("5.4 Produkcni gate (doporuceni)")
    pdf.p("Pred kazdym komerenim releasem zavest povinny gate:")
    pdf.b("V2: 100% PASS (10/10) na definovanem regression setu")
    pdf.b("0 PII leak, 0 map inconsistency, 0 orphan/phantom")
    pdf.b("Freeze pravidel + podpis release reportu (QA + Product Owner)")
    pdf.b("Validacni evidence pack pro enterprise zakazniky")

    # =====================================================================
    #  6. TARGET MARKETS
    # =====================================================================
    pdf.add_page()
    pdf.h1("6. Cilove trhy a segmentace")

    pdf.h2("6.1 TAM / SAM / SOM")
    pdf.tbl(
        ["Segment", "TAM", "SAM", "SOM (rok 1-2)"],
        [
            ["CR -- advokatni kancelare", "~3 500", "~1 000 (50+ zam.)", "50-100"],
            ["CR -- notari", "~450", "~450", "20-40"],
            ["CR -- nemocnice", "~190", "~190", "10-20"],
            ["CR -- ministerstva + urady", "~6 000", "~500 (kraj.+)", "20-30"],
            ["CR -- HR / person. ag.", "~800", "~400", "20-30"],
            ["CR -- BFSI (banky, poj.)", "~200", "~200", "10-20"],
            ["SK -- ekvivalentni", "~60 % CR", "~500", "15-25"],
            ["PL, HR, SI -- budouci", "10x CR", "--", "--"],
        ],
        [52, 38, 46, 34],
    )
    pdf.p("Konzervativni odhad SOM v prvnich 2 letech: 100-250 placenych licenci v CR/SK.")

    pdf.h2("6.2 Primarni segmenty (beachhead)")

    pdf.h3("Advokatni kancelare a notari")
    pdf.p(
        "Denne pracuji s citlivymi smlouvami, rozsudky, zavetmi. Regulator (CAK) tlaci na "
        "GDPR compliance. Vysoka ochota platit. Typicky 1-5 licenci na kancelar. "
        "Hodinovy naklad firmy: ~1 200 Kc -> rocni uspora az 216 000 Kc pri 100 dok/mesic."
    )

    pdf.h3("Nemocnice a zdravotnicka zarizeni")
    pdf.p(
        "Lekarske zpravy, propousteci zpravy, znalecke posudky. GDPR + zakon o zdravotnich "
        "sluzbach + EHDS. Casto interni IT -> jednodussi nasazeni. Typicky 5-20 licenci. "
        "Hodinovy naklad: ~448 Kc -> rocni uspora ~80 640 Kc."
    )

    pdf.h3("Verejna sprava")
    pdf.p(
        "Povinnost anonymizovat rozhodnuti, spisy, datove schranky. Verejne zakazky. "
        "Delsi sales cycle, ale vyssi LTV. Enterprise licence. "
        "Aktualne v CR je vypsana soutez na novy system anonymizace soudnich rozsudku -- "
        "stavajici nastroje podle iROZHLAS.cz nesplnuji zakladni funkce a jsou pomale."
    )

    pdf.h3("BFSI (banky, pojistovny)")
    pdf.p(
        "Segment tvori cca 35 % poptavky po GDPR resenich. Prisna compliance oddeleni. "
        "Smlouvy, interni audity, reporting. Enterprise licence."
    )

    pdf.h3("Konzultanti a DPO-as-a-Service")
    pdf.p(
        "Firmy nabizejici outsourcing ochrany osobnich udaju pouziji SKRYI jako klicovy "
        "nastroj pro sve klienty. Multiplikacni efekt -- 1 DPO = vice koncovych uzivatelu."
    )

    pdf.h2("6.3 Sekundarni a terciarni trhy")
    pdf.b("Rok 2-3: Slovensko (~60 % objemu CR, minimalni engine upravy)")
    pdf.b("Rok 3-5: Polsko (4x vetsi trh), Chorvatsko, Slovinsko")
    pdf.b("Moznost: HR 'Blind Recruitment' -- anonymizace CV dle AI Actu (kampan Q3 2026)")

    # =====================================================================
    #  7. COMPETITIVE ANALYSIS
    # =====================================================================
    pdf.add_page()
    pdf.h1("7. Konkurencni analyza")

    pdf.tbl(
        ["Reseni", "Offline", "CZ morfol.", "PII typy", "Cena/rok", "Nevyhoda"],
        [
            ["SKRYI", "ANO", "ANO (7 padu)", "34", "viz kap. 8", "Pouze Windows"],
            ["Cleardox (cloud)", "NE", "Nizka (1.pad)", "~20", "42 000+ Kc", "Cloud, riziko"],
            ["Zavernime.cz", "NE (web)", "Stredni", "~15", "36 000+ Kc", "Cloud prohlizec"],
            ["MS Presidio", "NE", "NE", "~15", "Zdarma (OSS)", "Bez CZ, cloud"],
            ["AWS Comprehend", "NE", "NE", "~12", "Pay-per-use", "Cloud, anglicky"],
            ["Google DLP", "NE", "NE", "~50", "Pay-per-use", "Cloud, anglicky"],
            ["anonym.legal", "Castecne", "NE", "~10", "N/A", "Presidio API na serv."],
            ["Manualni prace", "ANO", "ANO (lidsky)", "neom.", "Mzdove nakl.", "Pomale, chybove"],
        ],
        [28, 16, 24, 18, 30, 54],
    )

    pdf.h2("7.1 Cenove srovnani s manualni praci")
    pdf.p(
        "Prumerna advokatni kancelar anonymizuje ~50-100 dokumentu/mesic. "
        "Manualni anonymizace trva 10-30 min na dokument."
    )
    pdf.tbl(
        ["Metrika", "Manualni prace", "SKRYI"],
        [
            ["Cas na dokument", "20 min (prumer)", "< 5 s (automaticky)"],
            ["Mesicni cas (100 dok.)", "33 hodin", "< 10 minut"],
            ["Rocni mzdovy naklad", "~150-216 000 Kc", "Licence SKRYI"],
            ["Chybovost", "5-15 % (lidsky faktor)", "< 1-3 %"],
            ["Audit trail", "Zadny", "PDF certifikat (SHA-256)"],
        ],
        [48, 56, 56],
    )

    pdf.h2("7.2 ROI podle sektoru")
    pdf.tbl(
        ["Odvetvi", "Hodinovy naklad firmy", "Rocni uspora (100 dok/m)", "Navratnost licence"],
        [
            ["Advokacie", "1 200 Kc", "216 000 Kc", "~1.5 mesice"],
            ["Zdravotnictvi", "448 Kc", "80 640 Kc", "~4 mesice"],
            ["Verejna sprava", "423 Kc", "76 140 Kc", "~4.5 mesice"],
            ["BFSI", "900 Kc", "~162 000 Kc", "~2 mesice"],
        ],
        [38, 42, 50, 40],
    )

    # =====================================================================
    #  8. PRICING STRATEGY
    # =====================================================================
    pdf.add_page()
    pdf.h1("8. Cenova strategie a licencni model")

    pdf.h2("8.1 Licencni model")
    pdf.p(
        "Hardware-bound licence s rocni obnovou. Licence je vazana na konkretni "
        "pocitac (HW ID). Prenos na jiny pocitac je mozny kontaktovanim podpory."
    )

    pdf.h2("8.2 Doporucene ceny (bez DPH)")
    pdf.tbl(
        ["Typ licence", "Cena / rok", "Cilovy segment", "Obsah"],
        [
            ["SKRYI Solo (1 licence)", "9 900 Kc", "Samostatni advokati, konzultanti",
             "1 instalace na PC, plna funkcionalita, OCR, aktualizace, email podpora"],
            ["SKRYI Office 2-5", "29 900 Kc", "Male kancelare (2-5 lidi)",
             "Max. 5 instalaci v jedne organizaci, plna funkcionalita, OCR, watcher, aktualizace"],
            ["SKRYI Office 6-20", "69 900 Kc", "Stredni tymy (6-20 lidi)",
             "Max. 20 instalaci, plna funkcionalita, OCR, watcher, prioritni podpora (SLA reakce), aktualizace"],
            ["SKRYI Enterprise 20+", "Od 119 900 Kc + 4 900 Kc/lic. nad 20", "Velke firmy, nemocnice, urady",
             "Licence pro organizaci, SLA, onboarding, moznost on-prem nasazeni a integrace na miru"],
        ],
        [40, 40, 45, 65],
    )

    pdf.h2("8.3 Zduvodneni ceny (Value-Based Pricing)")
    pdf.p(
        "Cena kotvena proti nakladum rucni anonymizace + riziku GDPR incidentu. "
        "Licence Standard (24 900 Kc/rok) je ~12-16 % rocniho mzdoveho nakladu na "
        "manualni anonymizaci. ROI je dosazeno jiz pri zpracovani 10-15 dokumentu za mesic. "
        "Prumerna AK zpracuje 50-100 dokumentu mesicne -> ROI < 2 mesice."
    )
    pdf.p(
        "Enterprise cena je konkurenceschopna vuci internimu vyvoji "
        "(~500 000-1 000 000 Kc za vlastni reseni + udrzba)."
    )

    pdf.h2("8.4 Slevy a incentives")
    pdf.b("Early adopter sleva: 30 % pro prvnich 50 zakazniku")
    pdf.b("Rocni platba predem: 10 % sleva")
    pdf.b("Multi-licence: 20 % od 3. licence vyse")
    pdf.b("Referral program: 15 % z prvni rocni platby doporuceneho zakaznika")
    pdf.b("Akademicka licence: 50 % sleva pro univerzity a vyzkumne ustavy")

    pdf.h2("8.5 Strategie land-and-expand")
    pdf.p(
        "U enterprise zakazniku preferovat pilotni nasazeni (1-3 licence) s naslednym "
        "rollout na celou organizaci. Klicove: jasne SLA a support tiers "
        "(response/resolve casy) ve smlouvach."
    )

    # =====================================================================
    #  9. REVENUE MODEL
    # =====================================================================
    pdf.add_page()
    pdf.h1("9. Revenue model a financni projekce")

    pdf.h2("9.1 Revenue streams")
    pdf.b("Rocni licence (primarni): 80-85 % trzeb")
    pdf.b("Onboarding a skoleni (enterprise): 10 % trzeb")
    pdf.b("Customizace a integrace: 5-10 % trzeb")
    pdf.b("On-prem setup fee (enterprise): jednorazove")

    pdf.h2("9.2 Scenare ARR")
    pdf.tbl(
        ["Scenar", "Zakaznici Y1", "ARR Y1 (Kc)", "ARR Y1 (EUR)", "Poznamka"],
        [
            ["Konzervativni", "25", "~2 000 000", "~80 000", "Prevazne Standard"],
            ["Realisticky", "60", "~5 500 000", "~220 000", "Mix Standard + Profess."],
            ["Ambiciozni", "120", "~12 000 000", "~480 000", "Vcetne Enterprise"],
        ],
        [30, 30, 32, 30, 48],
    )

    pdf.h2("9.3 Projekce -- realisticky scenar (5 let)")
    pdf.tbl(
        ["Rok", "Standard", "Profess.", "Enterprise", "Celkem", "ARR (Kc)", "ARR (EUR)"],
        [
            ["Rok 1", "35", "18", "5", "58", "2 659 000", "~106 000"],
            ["Rok 2", "80", "35", "10", "125", "5 517 000", "~221 000"],
            ["Rok 3 (+SK)", "140", "55", "18", "213", "9 522 000", "~381 000"],
            ["Rok 4 (+PL R&D)", "220", "80", "28", "328", "14 960 000", "~598 000"],
            ["Rok 5 (+PL)", "350", "120", "40", "510", "23 438 000", "~938 000"],
        ],
        [24, 22, 22, 24, 20, 30, 28],
    )

    pdf.h2("9.4 Naklady (rok 1)")
    pdf.tbl(
        ["Polozka", "Mesicne (Kc)", "Rocne (Kc)"],
        [
            ["Vyvojar/zakladatel (1 FTE)", "0 (sweat equity)", "0"],
            ["Cloud (web, email, CI/CD)", "2 000", "24 000"],
            ["Marketing (online, PPC, PR)", "15 000", "180 000"],
            ["Pravni sluzby (EULA, audit)", "--", "60 000"],
            ["Ucetnictvi", "3 000", "36 000"],
            ["Konference a networking", "--", "40 000"],
            ["Celkem", "~20 000", "~340 000"],
        ],
        [68, 45, 45],
    )

    pdf.h2("9.5 Break-even")
    pdf.p(
        "Pri rocnich nakladech ~340 000 Kc a prumerne cene licence ~30 000 Kc je "
        "break-even dosazen pri 12 prodanych licencich za rok -- tj. 1 licence mesicne."
    )

    pdf.h2("9.6 Klicove KPI")
    pdf.b("MRR / ARR (Monthly/Annual Recurring Revenue)")
    pdf.b("ARPU (Average Revenue Per User)")
    pdf.b("CAC vs. LTV (Customer Acquisition Cost vs. Lifetime Value)")
    pdf.b("Churn rate (mira odchodu zakazniku)")
    pdf.b("Conversion rate: Trial -> Paid")
    pdf.b("Net Revenue Retention (enterprise)")
    pdf.b("Pass rate na produkcnim regression setu (kvalita = KPI)")

    # =====================================================================
    #  10. GO-TO-MARKET
    # =====================================================================
    pdf.add_page()
    pdf.h1("10. Go-to-Market strategie")

    pdf.h2("Faze 1: Product hardening + piloty (mesice 1-3)")
    pdf.b("Overit 241/241 PASS na V2 regression setu")
    pdf.b("Vytvorit demo dataset + audit evidence balicek pro enterprise")
    pdf.b("Oslovit 10-15 advokat. kancelari s nabidkou bezpl. trial (30 dni)")
    pdf.b("Osobni demo + onboarding zdarma pro prvnich 5 zakazniku")
    pdf.b("Sbirat testimonials a case studies")
    pdf.b("Publikovat whitepaper: 'Proc LLM selhavaji v ceske anonymizaci'")

    pdf.h2("Faze 2: Komercni launch + organicky rust (mesice 3-12)")
    pdf.b("Landing page + SEO ('anonymizace smluv', 'GDPR anonymizator')")
    pdf.b("LinkedIn inbound marketing -- clanky o GDPR compliance")
    pdf.b("Partnerstvi s CAK (Ceska advokatni komora) -- doporuceny nastroj")
    pdf.b("Webinare a live demo pro cilove segmenty")
    pdf.b("Referral program aktivni")
    pdf.b("Ucast na konf. ISSS Hradec Kralove (sitovani s verejnou spravou)")
    pdf.b("Kampan 'Blind Recruitment' -- anonymizace CV dle AI Actu pro HR")
    pdf.b("Vyuzit 'dark social': doporuceni v uzavrenych DPO komunitach (Slack/Discord)")

    pdf.h2("Faze 3: Skalovani (rok 2+)")
    pdf.b("Account manager pro enterprise segment")
    pdf.b("Slovenska lokalizace + slovenska knihovna jmen")
    pdf.b("Partnerstvi s IT distributory (Alza Business, AutoCont)")
    pdf.b("Vstup na verejne zakazky (NIPEZ, E-ZAK)")
    pdf.b("Konference: IT pravo, eHealth, GDPR summity")
    pdf.b("Priprava polske expanze pres granty TA CR TREND")

    pdf.h2("Distribucni kanaly")
    pdf.tbl(
        ["Kanal", "Priorita", "Naklady", "Ocekavany podil"],
        [
            ["Primy prodej (web + demo)", "Vysoka", "Nizke", "45 %"],
            ["Referral program", "Vysoka", "Variabilni (15 %)", "20 %"],
            ["DPO / compliance konzultanti", "Vysoka", "Nizke (partnerska marze)", "15 %"],
            ["IT distributori", "Stredni", "Marze 20-30 %", "10 %"],
            ["Verejne zakazky", "Stredni", "Admin overhead", "7 %"],
            ["Konference / events", "Nizka", "40 000 Kc/rok", "3 %"],
        ],
        [50, 23, 45, 40],
    )

    # =====================================================================
    #  11. SWOT
    # =====================================================================
    pdf.add_page()
    pdf.h1("11. SWOT analyza")

    pdf.h2("Silne stranky (Strengths)")
    pdf.b("Unikatni morfologicka inteligence pro inflektivni jazyky -- zadny konkurent")
    pdf.b("100% offline -- splnuje nejprisnejsi bezpecnostni pozadavky ('true zero trust')")
    pdf.b("34 kategorii PII -- nejsirsi pokryti na trhu")
    pdf.b("Produkt je hotovy a validovany (241 smluv, 0 realnych leaku)")
    pdf.b("Nizke provozni naklady (desktop app, zadna infrastruktura)")
    pdf.b("Patentovatelne inovace (12 klicovych technologickych inovaci, vcetne v3.1)")
    pdf.b("Reverzibilni anonymizace s audit trail -- unikatni pro compliance")

    pdf.h2("Slabe stranky (Weaknesses)")
    pdf.b("Pouze Windows -- chybi macOS/Linux verze")
    pdf.b("Jednoclenny tym (zakladatel = vyvojar = prodejce)")
    pdf.b("Zadny brand awareness -- novy produkt na trhu")
    pdf.b("Rule-based approach -- potencialni omezeni pro exoticke jazyky")
    pdf.b("Zavislost na python-docx -- omezena podpora starsich .doc formatu")

    pdf.h2("Prilezitosti (Opportunities)")
    pdf.b("GDPR enforcement se zprisnuje -- rostouci poptavka po compliance nastrojich")
    pdf.b("EHDS + AI Act + NIS2 = tri nove regulacni katalyzatory v 2026")
    pdf.b("Expanze na slovensky a polsky trh (10x vetsi TAM)")
    pdf.b("Partnerstvi s pravnimi a zdravotnickymi asociacemi")
    pdf.b("SaaS/API verze pro enterprise zakazniky (budouci pivot)")
    pdf.b("Integrace s DMS systemy (SharePoint, Google Workspace)")
    pdf.b("'Blind Recruitment' kampan -- anonymizace CV jako novy use case")
    pdf.b("Cesky stat aktivne hleda novy system pro anonymizaci soudnich rozsudku")

    pdf.h2("Hrozby (Threats)")
    pdf.b("Velci hraci (Microsoft, Google) mohou pridat CZ podporu do cloudovych nastroju")
    pdf.b("Open-source alternativy (Presidio + CZ community model)")
    pdf.b("Regulatorni zmeny -- zmirneni GDPR by snizilo poptavku")
    pdf.b("Ekonomicka recese -- organizace skrtaji IT rozpocty")
    pdf.b("LLM de-anonymizace: moderni modely umi identifikovat osoby podle stylu psani")
    pdf.b("Piracstvi -- nutnost robustni licence ochrany (HW binding implementovano)")

    # =====================================================================
    #  12. RISKS & MITIGATION
    # =====================================================================
    pdf.add_page()
    pdf.h1("12. Rizika a mitigace")

    pdf.tbl(
        ["Riziko", "Dopad", "Pravdepodobnost", "Mitigace"],
        [
            ["Edge-case quality regrese", "Vysoky", "Stredni",
             "Release gate 100% V2, povinne regression behy"],
            ["False positives/negatives", "Stredni", "Stredni",
             "Sektorove policy packy + governance blacklistu"],
            ["Prehnane obchodni claimy", "Vysoky", "Nizka",
             "Marketing: 'asistencni nastroj', ne 'pravni system'"],
            ["Enterprise security audit", "Stredni", "Vysoka",
             "Security compliance pack + auditni artefakty"],
            ["LLM stylometricka de-anon.", "Stredni", "Budouci",
             "Budouci verze: stylometricke maskovani"],
            ["Konkurencni vstup BigTech", "Vysoky", "Nizka",
             "Patentova ochrana, first-mover advantage"],
        ],
        [40, 20, 28, 82],
    )

    pdf.h2("Enterprise pripravenost (doporuceni)")
    pdf.b("Pripravit 'Data Processing & Security Whitepaper' (1-2 strany)")
    pdf.b("Zavest release note sablonu 'Known limitations + mitigations'")
    pdf.b("Standardizovany 'Validation Evidence Pack' pro audit/IT security")
    pdf.b("Marketing formulovat jako 'asistencni nastroj', nikoli 'pravni rozhodovaci system'")

    # =====================================================================
    #  13. TEAM
    # =====================================================================
    pdf.h1("13. Tim a organizace")

    pdf.h2("13.1 Soucasny tym")
    pdf.p(
        "Nixminds s.r.o. je technologicka spolecnost zamerena na NLP a GDPR compliance nastroje. "
        "SKRYI Document Suite byl vyvinut jako hlavni produkt spolecnosti."
    )

    pdf.h2("13.2 Plan rozsireni tymu")
    pdf.tbl(
        ["Role", "Kdy", "Duvod"],
        [
            ["Sales / Account Manager", "Mesic 6-9", "Primy prodej a enterprise vztahy"],
            ["Customer Support", "Mesic 9-12", "Podpora zakazniku, onboarding"],
            ["Backend Developer", "Rok 2", "Polska/slovenska lokalizace engine"],
            ["Marketing Specialist", "Rok 2", "Content marketing, SEO, PPC"],
            ["DPO / Legal Advisor", "Rok 2-3", "Compliance poradenstvi pro zakazniky"],
        ],
        [48, 28, 94],
    )

    # =====================================================================
    #  14. ROADMAP
    # =====================================================================
    pdf.add_page()
    pdf.h1("14. Produkcni roadmapa")

    roadmap = [
        ("Q1 2026 (aktualni)", [
            "Produkt v3.1.0 dokoncen a validovan",
            "Testovaci korpus 241 smluv, 0 leaku",
            "v3.1: Opravy INSURANCE_ID/PHONE, vokativni deduplikace, kontextova filtrace SPZ",
            "Business plan pripraven",
        ]),
        ("Q2 2026", [
            "Landing page + trial verze online",
            "Pilotni zakaznici (5-10)",
            "Whitepaper 'Proc LLM selhavaji v ceske anonymizaci'",
            "Ucast na ISSS Hradec Kralove",
            "Sbirani testimonials",
        ]),
        ("Q3 2026", [
            "Prvni placene licence",
            "Referral program",
            "CAK partnerstvi",
            "Kampan 'Blind Recruitment' pro HR",
        ]),
        ("Q4 2026", [
            "40-60 licenci celkem",
            "Slovenska lokalizace zahajena",
            "Enterprise onboarding workflow",
            "Security compliance pack hotovy",
        ]),
        ("2027 H1", [
            "SK verze v produkci",
            "130+ licenci",
            "Ucast na konferencich (IT pravo, eHealth)",
        ]),
        ("2027 H2", [
            "Polska verze -- R&D",
            "API/SaaS prototyp",
            "200+ licenci",
            "Grant TA CR TREND pro PL expanzi",
        ]),
        ("2028", [
            "PL verze v produkci",
            "macOS verze",
            "350+ licenci",
            "Break-even / Serie A",
        ]),
    ]
    for period, milestones in roadmap:
        pdf.h3(period)
        for m in milestones:
            pdf.b(m)

    # =====================================================================
    #  15. 30-DAY ACTION PLAN
    # =====================================================================
    pdf.add_page()
    pdf.h1("15. Akcni plan (30 dni)")

    pdf.p("Konkretni kroky pro prvni mesic po schvaleni business planu:")

    actions = [
        ("1. Zalozit 'Production Gate Board'",
         "Owner: Product + QA. Definovat regression set a PASS kriteria."),
        ("2. Overit 100% V2 PASS",
         "Potvrdit 241/241 na regression setu. Freeze pravidel pro release branch."),
        ("3. Pripravit komercni balicek",
         "Cenik, SLA, onboarding nabidka, security one-pager, demo dataset."),
        ("4. Landing page + trial distribuce",
         "Jednoduchy web s moznosti stazeni 30-denni trial verze."),
        ("5. Oslovit 10 pilotnich zakazniku",
         "Advokatni kancelare, notari, 1 nemocnice. Osobni demo + onboarding zdarma."),
        ("6. Zahajit content marketing",
         "LinkedIn clanky o GDPR, newsletter, whitepaper draft."),
        ("7. Pravni pripravenost",
         "Finalizace EULA, licencni podminky, GDPR compliance documentation."),
        ("8. Nastavit KPI dashboard",
         "MRR, pipeline, Trial->Paid conversion, churn. Tydenni review."),
    ]
    for title, desc in actions:
        pdf.h3(title)
        pdf.p(desc)

    # =====================================================================
    #  16. CONCLUSION
    # =====================================================================
    pdf.add_page()
    pdf.h1("16. Zaver a klicova doporuceni")

    pdf.p(
        "SKRYI Document Suite je technologicky vyspely, plne validovany produkt resici "
        "realny a rostouci problem na trhu. Kombinace morfologicke inteligence, offline "
        "provozu a sirokeho pokryti PII kategorii vytvari silnou konkurencni vyhodu "
        "bez primeho konkurenta."
    )

    pdf.h2("Top 7 doporuceni")

    pdf.h3("1. Spustit trial verzi co nejdrive")
    pdf.p("Produkt je hotovy. Kazdy mesic bez prodeje je ztracena prilezitost.")

    pdf.h3("2. Zamerit se na advokatni kancelare jako beachhead segment")
    pdf.p(
        "Nejvyssi ochota platit, nejsilnejsi regulatorni tlak, dobre definovany use case. "
        "ROI < 2 mesice."
    )

    pdf.h3("3. Investovat do partnerstvi s CAK")
    pdf.p("Doporuceni od Ceske advokatni komory = okamzita duveryhodnost u tisicu kancelari.")

    pdf.h3("4. Chranit IP")
    pdf.p(
        "Zvazit patentovou prihlasku na klicove morfologicke inovace "
        "(bidirekcionalni inference, kaskadovy system pravidel)."
    )

    pdf.h3("5. Planovat slovenskou a polskou lokalizaci")
    pdf.p("Polsky trh je 4x vetsi a ma identicky problem. Hlavni growth lever.")

    pdf.h3("6. Vyuzit legislativni katalyzatory 2026")
    pdf.p(
        "AI Act, EHDS, smernice o transparentnosti odmenovani -- tri nove regulace "
        "v jednom roce vytvareji bezprecedentni poptavku po anonymizaci."
    )

    pdf.h3("7. Pripravit enterprise compliance pack")
    pdf.p(
        "Security whitepaper, validation evidence pack, standardizovane SLA. "
        "Nutne pro enterprise sales cycle."
    )

    pdf.ln(12)
    pdf._hline(40)
    pdf.ln(8)
    pdf.set_font("DV", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "Nixminds s.r.o.  |  info@nixminds.com", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Dokument vygenerovan: {datetime.now().strftime('%d. %m. %Y %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "CONFIDENTIAL -- Pouze pro interni pouziti", align="C")

    out = os.path.join(os.path.dirname(__file__), "SKRYI_Final_Report.pdf")
    pdf.output(out)
    print(f"[OK] Final report saved to: {out}")
    print(f"     Pages: {pdf.page_no()}")
    return out


if __name__ == "__main__":
    build()
