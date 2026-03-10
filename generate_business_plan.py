#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate SKRYI Business Plan & Startup Report as PDF."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fpdf import FPDF
from datetime import datetime

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")


class BusinessPlanPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, "SKRYI Document Suite — Business Plan & Startup Report  |  CONFIDENTIAL", align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 8, f"© 2026 Nixminds s.r.o.  —  Strana {self.page_no()}", align="C")

    def title_page(self):
        self.add_page()
        self.ln(50)
        self.set_font("DejaVu", "B", 28)
        self.set_text_color(30, 60, 120)
        self.cell(0, 14, "SKRYI Document Suite", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
        self.set_font("DejaVu", "", 14)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, "Business Plan & Startup Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font("DejaVu", "", 11)
        self.cell(0, 8, "Offline GDPR Anonymization Platform", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 8, "for Inflective Languages", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(30)
        self.set_draw_color(30, 60, 120)
        self.set_line_width(0.5)
        x = 50
        self.line(x, self.get_y(), self.w - x, self.get_y())
        self.ln(10)
        self.set_font("DejaVu", "", 10)
        self.set_text_color(60, 60, 60)
        lines = [
            f"Datum: {datetime.now().strftime('%d. %m. %Y')}",
            "Verze: 1.0",
            "Klasifikace: CONFIDENTIAL",
            "",
            "Připravil: Nixminds s.r.o.",
            "Kontakt: info@nixminds.com",
        ]
        for line in lines:
            self.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

    def section(self, title, level=1):
        self.ln(4)
        if level == 1:
            self.set_font("DejaVu", "B", 16)
            self.set_text_color(30, 60, 120)
            self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(30, 60, 120)
            self.set_line_width(0.4)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)
        elif level == 2:
            self.set_font("DejaVu", "B", 13)
            self.set_text_color(50, 80, 140)
            self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        else:
            self.set_font("DejaVu", "B", 11)
            self.set_text_color(60, 60, 60)
            self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

    def body(self, text):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(40, 40, 40)
        x = self.get_x()
        self.cell(6, 6, "•")
        self.multi_cell(0, 6, text)
        self.ln(1)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            w = (self.w - self.l_margin - self.r_margin) / len(headers)
            col_widths = [w] * len(headers)
        self.set_font("DejaVu", "B", 9)
        self.set_fill_color(30, 60, 120)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("DejaVu", "", 9)
        self.set_text_color(40, 40, 40)
        fill = False
        for row in rows:
            if self.get_y() > self.h - 30:
                self.add_page()
            if fill:
                self.set_fill_color(240, 244, 250)
            else:
                self.set_fill_color(255, 255, 255)
            max_h = 8
            for i, cell in enumerate(row):
                self.cell(col_widths[i], max_h, str(cell), border=1, fill=True)
            self.ln()
            fill = not fill
        self.ln(3)


def build():
    pdf = BusinessPlanPDF()

    # ==================== TITLE PAGE ====================
    pdf.title_page()

    # ==================== TABLE OF CONTENTS ====================
    pdf.add_page()
    pdf.section("Obsah")
    toc = [
        "1. Executive Summary",
        "2. Problém a tržní příležitost",
        "3. Produkt — SKRYI Document Suite",
        "4. Technologické konkurenční výhody",
        "5. Cílové trhy a segmenty",
        "6. Konkurenční analýza",
        "7. Cenová strategie a licenční model",
        "8. Revenue model a finanční projekce",
        "9. Go-to-Market strategie",
        "10. SWOT analýza",
        "11. Technická připravenost a validace",
        "12. Tým a organizace",
        "13. Roadmapa",
        "14. Závěr a doporučení",
    ]
    for item in toc:
        pdf.body(item)

    # ==================== 1. EXECUTIVE SUMMARY ====================
    pdf.add_page()
    pdf.section("1. Executive Summary")
    pdf.body(
        "SKRYI Document Suite je desktopová aplikace pro plně offline anonymizaci osobních údajů "
        "v dokumentech (DOCX, PDF, obrázky). Produkt cílí na organizace v České republice, "
        "na Slovensku a potenciálně dalších zemích s inflektivními jazyky (polština, chorvatština, "
        "slovinština), které potřebují splnit požadavky GDPR bez odesílání dat na cloud."
    )
    pdf.body(
        "Na trhu neexistuje srovnatelný produkt, který by kombinoval: (1) morfologickou inteligenci "
        "pro skloňování jmen ve všech 7 pádech, (2) plně offline provoz, (3) 34 kategorií PII, "
        "(4) reverzibilní anonymizaci s klíčem, a (5) automatický OCR vstup."
    )
    pdf.body(
        "Produkt je ve stavu Production Ready (v3.1.1). Byl ověřen na korpusu 200+ syntetických "
        "smluv pokrývajících 6 sektorů (právo, zdravotnictví, veřejná správa, HR, školství, finance). "
        "Manuální audit potvrdil nulový počet skutečných úniků osobních údajů."
    )

    pdf.section("Klíčová čísla", 2)
    pdf.table(
        ["Metrika", "Hodnota"],
        [
            ["Kategorie PII", "34 typů (jména, adresy, RČ, IBAN, SPZ, VIN, SSH klíče…)"],
            ["Knihovna jmen", "~7 000 unikátních českých/mezinárodních křestních jmen (+ stovky tisíc pádových tvarů)"],
            ["Přesnost anonymizace", "97–99 % (ověřeno na 200+ smlouvách)"],
            ["Doba zpracování", "< 2 s / dokument (typická smlouva 3–5 stran)"],
            ["Offline režim", "100 % — žádná data neopouštějí zařízení"],
            ["OCR podpora", "PDF, PNG, JPG, TIFF, BMP, WEBP"],
            ["Platforma", "Windows 10/11 (desktop)"],
            ["Technologie", "Electron + Python (Nuitka compiled)"],
        ],
        [60, 120],
    )

    # ==================== 2. PROBLEM ====================
    pdf.add_page()
    pdf.section("2. Problém a tržní příležitost")

    pdf.section("2.1 Regulatorní tlak", 2)
    pdf.body(
        "Od května 2018 platí v EU Obecné nařízení o ochraně osobních údajů (GDPR). "
        "Organizace jsou povinny chránit osobní údaje a za porušení jim hrozí pokuty až do výše "
        "20 mil. EUR nebo 4 % ročního obratu. Český ÚOOÚ aktivně ukládá pokuty — jen v roce 2025 "
        "bylo v ČR uděleno přes 30 pokut za porušení GDPR."
    )

    pdf.section("2.2 Inflektivní jazyky = speciální problém", 2)
    pdf.body(
        "Existující anonymizační nástroje (Presidio od Microsoftu, AWS Comprehend, Google DLP) "
        "jsou primárně navrženy pro angličtinu. V češtině a slovenštině se jména skloňují — "
        "\"Jan Novák\" má 14+ tvarů (Jana Nováka, Janu Novákovi, Janem Novákem…). "
        "Stávající řešení tyto tvary nerozpoznávají → data leak."
    )
    pdf.body(
        "Problém se netýká jen češtiny: polština, slovenština, chorvatština, slovinština, "
        "maďarština — to jsou stovky milionů uživatelů v EU, kteří nemají adekvátní nástroj."
    )

    pdf.section("2.3 Offline požadavek", 2)
    pdf.body(
        "Mnoho organizací (advokátní kanceláře, soudy, nemocnice, ministerstva) nemůže posílat "
        "citlivé dokumenty do cloudu. Potřebují nástroj, který funguje 100% offline. "
        "SKRYI je jediný produkt na trhu, který toto splňuje s plnou morfologickou podporou."
    )

    pdf.section("2.4 Velikost trhu (TAM/SAM/SOM)", 2)
    pdf.table(
        ["Segment", "TAM", "SAM", "SOM (rok 1–2)"],
        [
            ["ČR — advokátní kanceláře", "~3 500 kanceláří", "~1 000 (50+ zaměstnanců)", "50–100"],
            ["ČR — notáři", "~450 notářů", "~450", "20–40"],
            ["ČR — nemocnice a kliniky", "~190 nemocnic", "~190", "10–20"],
            ["ČR — ministerstva a úřady", "~6 000 úřadů", "~500 (krajské+)", "20–30"],
            ["ČR — HR / personální agentury", "~800 agentur", "~400", "20–30"],
            ["SK — ekvivalentní", "~60 % objemu ČR", "~500", "15–25"],
            ["PL, HR, SI — budoucí", "10× ČR", "—", "—"],
        ],
        [52, 42, 52, 34],
    )
    pdf.body(
        "Konzervativní odhad SOM v prvních 2 letech: 100–250 placených licencí v ČR/SK."
    )

    # ==================== 3. PRODUCT ====================
    pdf.add_page()
    pdf.section("3. Produkt — SKRYI Document Suite")

    pdf.section("3.1 Funkce produktu", 2)
    pdf.table(
        ["Funkce", "Popis"],
        [
            ["Anonymizace DOCX", "Automatická detekce a nahrazení 34 kategorií PII tagy [[OSOBA_1]] atd."],
            ["Deanonymizace", "Zpětná rekonstrukce původního dokumentu pomocí klíče (_map.json)"],
            ["OCR konverze", "PDF / obrázky (PNG, JPG, TIFF, BMP, WEBP) → DOCX přes Tesseract"],
            ["Hromadné zpracování", "Automatický watcher — složkový režim pro dávkové zpracování"],
            ["PDF certifikát", "Automatický audit trail: SHA-256 otisk, statistiky, GDPR doložka"],
            ["Morfologická inteligence", "7 pádů × 2 čísla × přivlastňovací tvary pro česká jména"],
            ["Standalone křestní jména", "Post-pass zachytí i samostatně stojící křestní jména (Barbora, Jakubovi)"],
            ["Sektorový blacklist", "500+ chráněných slov v 6 oborech + 267 institucí (data-driven)"],
            ["Víceslovná cizí jména", "Bezpečné zpracování jmen typu 'Mai Linh Nguyenová'"],
            ["Hardwarová licence", "HW-ID binding, AppData persistence, offline validace"],
        ],
        [52, 128],
    )

    pdf.section("3.2 Technologický stack", 2)
    pdf.table(
        ["Vrstva", "Technologie", "Proč"],
        [
            ["GUI", "Electron + HTML/CSS/JS", "Moderní UI, rychlý vývoj, Windows instalátor"],
            ["Backend", "Python 3.11", "Bohatý NLP ekosystém, python-docx, fpdf2"],
            ["Kompilace", "Nuitka", "Ochrana kódu, nativní rychlost, bez Python runtime"],
            ["Balení", "electron-builder + NSIS", "Profesionální Windows installer (~100 MB)"],
            ["OCR", "Tesseract + Poppler", "Open-source, lokální, čeština"],
        ],
        [35, 55, 90],
    )

    # ==================== 4. COMPETITIVE ADVANTAGES ====================
    pdf.add_page()
    pdf.section("4. Technologické konkurenční výhody")

    pdf.body(
        "SKRYI má několik patentovatelných inovací, které ho odlišují od všech existujících řešení:"
    )

    advantages = [
        ("Bidirekcionalní morfologická inference",
         "Z libovolného pádu odvodí nominativ a naopak. Žádný konkurent toto neumí pro češtinu."),
        ("Prioritizovaný kaskádový systém pádových pravidel",
         "Eliminuje ambiguitu (\"Karlu\" → \"Karel\", ne \"Karl\") pomocí přesně definovaného pořadí pravidel."),
        ("4-fázová deduplikace osob",
         "Slučuje duplicitní osoby: totožná jména → podmnožiny variant → muž/žena → překlepy/OCR chyby."),
        ("Standalone first-name post-pass",
         "Zachytí křestní jména ve všech pádech, i když se vyskytují bez příjmení (\"Barbora uhradí Jakubovi...\")."),
        ("Orphan surname absorption",
         "Bezpečně zpracuje víceslovná cizí jména (\"Mai Linh Nguyenová\") včetně příjmení."),
        ("Inteligentní absorpce městských čtvrtí",
         "Řeší české adresy s čtvrtěmi za pomlčkou (\"Praha 3 - Vinohrady\")."),
        ("Data-driven institucionální blacklist",
         "267 institucí (banky, univerzity, nemocnice) + 500+ rolí → minimální false positives."),
        ("100% offline architektura",
         "Žádná data neopouštějí zařízení. Klíčový požadavek pro advokáty, soudy, nemocnice."),
        ("34 kategorií PII",
         "Nejširší pokrytí na trhu: od jmen a RČ přes IBAN, SSH klíče, RFID, až po sociální sítě."),
    ]
    for title, desc in advantages:
        pdf.section(title, 3)
        pdf.body(desc)

    # ==================== 5. TARGET MARKETS ====================
    pdf.add_page()
    pdf.section("5. Cílové trhy a segmenty")

    pdf.section("5.1 Primární trh (rok 1–2): Česká republika", 2)
    segments = [
        ("Advokátní kanceláře a notáři",
         "Denně pracují s citlivými smlouvami, rozsudky, závětmi. Regulátor (ČAK) tlačí na GDPR compliance. "
         "Vysoká ochota platit za profesionální nástroje. Typicky 1–5 licencí na kancelář."),
        ("Nemocnice a zdravotnická zařízení",
         "Lékařské zprávy, propouštěcí zprávy, znalecké posudky. GDPR + zákon o zdravotních službách. "
         "Často interní IT oddělení → jednodušší nasazení. Typicky 5–20 licencí."),
        ("Veřejná správa (ministerstva, krajské úřady)",
         "Povinnost anonymizovat rozhodnutí, spisy, datové schránky. Veřejné zakázky. "
         "Delší sales cycle, ale vyšší LTV. Enterprise licence."),
        ("Finanční instituce",
         "Banky, pojišťovny, leasingové společnosti. Smlouvy, interní audity, reporting. "
         "Přísná compliance oddělení. Typicky enterprise licence."),
    ]
    for title, desc in segments:
        pdf.section(title, 3)
        pdf.body(desc)

    pdf.section("5.2 Sekundární trh (rok 2–3): Slovensko", 2)
    pdf.body(
        "Slovenština je nejbližší jazyk k češtině. Engine vyžaduje minimální úpravy (rozšíření knihovny jmen, "
        "drobné morfologické adaptace). Trh je ~60 % velikosti českého."
    )

    pdf.section("5.3 Terciární trh (rok 3–5): Polsko, Chorvatsko, Slovinsko", 2)
    pdf.body(
        "Všechny jsou inflektivní jazyky se stejným problémem. Polsko je 4× větší trh než ČR. "
        "Vyžaduje novou knihovnu jmen a morfologická pravidla, ale architektura je připravena."
    )

    # ==================== 6. COMPETITIVE ANALYSIS ====================
    pdf.add_page()
    pdf.section("6. Konkurenční analýza")

    pdf.table(
        ["Řešení", "Offline", "CZ morfologie", "PII typy", "Cena/rok", "Nevýhoda"],
        [
            ["SKRYI", "✓", "✓ (7 pádů)", "34", "viz kap. 7", "Pouze Windows"],
            ["MS Presidio", "✗ (cloud)", "✗", "~15", "Zdarma (OSS)", "Bez CZ podpory, cloud"],
            ["AWS Comprehend", "✗ (cloud)", "✗", "~12", "Pay-per-use", "Cloud, anglicky"],
            ["Google DLP", "✗ (cloud)", "✗", "~50", "Pay-per-use", "Cloud, anglicky"],
            ["Manuální práce", "✓", "✓ (lidsky)", "∞", "Mzdové nákl.", "Pomalé, chybové, drahé"],
            ["Regex skripty", "✓", "✗", "5–10", "Interní vývoj", "Bez morfologie, udržba"],
        ],
        [32, 18, 28, 20, 32, 50],
    )

    pdf.body(
        "SKRYI je jediný produkt, který kombinuje offline provoz, českou morfologii a široké pokrytí PII. "
        "Nejbližší alternativou je manuální práce, která stojí desítky hodin měsíčně u větších organizací."
    )

    pdf.section("6.1 Cenové srovnání s manuální prací", 2)
    pdf.body(
        "Průměrná advokátní kancelář anonymizuje ~50 dokumentů/měsíc. Manuální anonymizace trvá "
        "20–40 minut na dokument (identifikace + nahrazení + kontrola)."
    )
    pdf.table(
        ["Metrika", "Manuální práce", "SKRYI"],
        [
            ["Čas na dokument", "30 min (průměr)", "< 5 s (automaticky)"],
            ["Měsíční čas (50 dok.)", "25 hodin", "< 5 minut"],
            ["Roční mzdový náklad", "~150 000 Kč (asistent)", "Licence SKRYI"],
            ["Chybovost", "5–15 % (lidský faktor)", "< 1–3 %"],
            ["Audit trail", "Žádný", "PDF certifikát (SHA-256)"],
        ],
        [52, 59, 59],
    )

    # ==================== 7. PRICING ====================
    pdf.add_page()
    pdf.section("7. Cenová strategie a licenční model")

    pdf.section("7.1 Licenční model", 2)
    pdf.body(
        "Hardware-bound licence s roční obnovou. Licence je vázaná na konkrétní počítač (HW ID). "
        "Přenos na jiný počítač je možný kontaktováním podpory."
    )

    pdf.section("7.2 Doporučené ceny", 2)
    pdf.table(
        ["Typ licence", "Cena / rok (bez DPH)", "Cílový segment", "Obsah"],
        [
            ["Trial", "Zdarma (30 dní)", "Všichni", "Plná funkcionalita, 30 dokumentů limit"],
            ["Standard", "14 900 Kč", "OSVČ, malé kanceláře (1–3 osoby)", "1 PC, email podpora, aktualizace"],
            ["Professional", "34 900 Kč", "Střední firmy (4–20 osob)", "Až 5 PC, prioritní podpora, OCR, watcher"],
            ["Enterprise", "Na míru (od 89 000 Kč)", "Korporace, úřady, nemocnice", "Neomezeno PC, SLA, onboarding, customizace"],
        ],
        [30, 40, 50, 60],
    )

    pdf.section("7.3 Zdůvodnění ceny", 2)
    pdf.body(
        "Licence Standard (14 900 Kč/rok) je ~10 % ročního mzdového nákladu na manuální anonymizaci. "
        "ROI je dosaženo již při zpracování 10–15 dokumentů za měsíc. "
        "Průměrná advokátní kancelář zpracuje 30–80 dokumentů měsíčně → ROI < 1 měsíc."
    )
    pdf.body(
        "Enterprise cena je nastavena tak, aby byla konkurenceschopná vůči internímu vývoji "
        "(~500 000–1 000 000 Kč za vlastní řešení + údržba) a zároveň odrážela hodnotu offline "
        "nasazení a compliance certifikátů."
    )

    pdf.section("7.4 Slevy a incentives", 2)
    pdf.bullet("Early adopter sleva: 30 % pro prvních 50 zákazníků")
    pdf.bullet("Roční platba předem: 10 % sleva")
    pdf.bullet("Multi-licence: 20 % od 3. licence výše")
    pdf.bullet("Referral program: 15 % z první roční platby doporučeného zákazníka")
    pdf.bullet("Akademická licence: 50 % sleva pro univerzity a výzkumné ústavy")

    # ==================== 8. REVENUE MODEL ====================
    pdf.add_page()
    pdf.section("8. Revenue model a finanční projekce")

    pdf.section("8.1 Revenue streams", 2)
    pdf.bullet("Roční licence (primární): 80–85 % tržeb")
    pdf.bullet("Onboarding a školení (enterprise): 10 % tržeb")
    pdf.bullet("Customizace a integrace: 5–10 % tržeb")

    pdf.section("8.2 Projekce — konzervativní scénář", 2)
    pdf.table(
        ["Rok", "Standard", "Professional", "Enterprise", "Celkem licencí", "ARR (Kč)", "ARR (EUR)"],
        [
            ["Rok 1", "40", "15", "3", "58", "1 063 500", "~42 500"],
            ["Rok 2", "90", "35", "8", "133", "2 834 000", "~113 400"],
            ["Rok 3", "160", "60", "15", "235", "5 329 000", "~213 200"],
            ["Rok 4 (+SK)", "250", "90", "25", "365", "8 546 000", "~341 800"],
            ["Rok 5 (+PL)", "400", "140", "40", "580", "14 140 000", "~565 600"],
        ],
        [22, 22, 22, 30, 28, 28, 28],
    )
    pdf.body(
        "Pozn.: ARR = Annual Recurring Revenue. Výpočet: Standard × 14 900 + Professional × 34 900 "
        "+ Enterprise × 89 000. Nezahrnuje onboarding, customizace a referral příjmy."
    )

    pdf.section("8.3 Náklady (rok 1)", 2)
    pdf.table(
        ["Položka", "Měsíčně (Kč)", "Ročně (Kč)"],
        [
            ["Vývojář/zakladatel (1 FTE)", "0 (sweat equity)", "0"],
            ["Cloud (web, email, CI/CD)", "2 000", "24 000"],
            ["Marketing (online, PPC, PR)", "15 000", "180 000"],
            ["Právní služby (EULA, GDPR audit)", "—", "60 000"],
            ["Účetnictví", "3 000", "36 000"],
            ["Konference a networking", "—", "40 000"],
            ["Celkem", "~20 000", "~340 000"],
        ],
        [70, 45, 45],
    )

    pdf.section("8.4 Break-even", 2)
    pdf.body(
        "Při ročních nákladech ~340 000 Kč a průměrné ceně licence ~18 000 Kč je break-even "
        "dosažen při 19 prodaných licencích za rok — tj. méně než 2 licence měsíčně."
    )

    # ==================== 9. GO-TO-MARKET ====================
    pdf.add_page()
    pdf.section("9. Go-to-Market strategie")

    pdf.section("9.1 Fáze 1: Pilotní zákazníci (měsíce 1–3)", 2)
    pdf.bullet("Oslovit 10–15 advokátních kanceláří s nabídkou bezplatného trial (30 dní)")
    pdf.bullet("Osobní demo + onboarding zdarma pro prvních 5 zákazníků")
    pdf.bullet("Sbírat testimonials a case studies")
    pdf.bullet("Feedback loop → rychlé iterace produktu")

    pdf.section("9.2 Fáze 2: Organický růst (měsíce 3–12)", 2)
    pdf.bullet("Landing page + SEO (klíčová slova: \"anonymizace smluv\", \"GDPR anonymizátor\")")
    pdf.bullet("LinkedIn inbound marketing → články o GDPR compliance")
    pdf.bullet("Partnerství s ČAK (Česká advokátní komora) — doporučený nástroj")
    pdf.bullet("Webináře a live demo pro cílové segmenty")
    pdf.bullet("Referral program aktivní")

    pdf.section("9.3 Fáze 3: Škálování (rok 2+)", 2)
    pdf.bullet("Account manager pro enterprise segment")
    pdf.bullet("Slovenská lokalizace + slovenská knihovna jmen")
    pdf.bullet("Partnerství s IT distributory (Alza Business, AutoCont)")
    pdf.bullet("Vstup na veřejné zakázky (NIPEZ, E-ZAK)")
    pdf.bullet("Konference: IT právo, eHealth, GDPR summity")

    pdf.section("9.4 Distribuční kanály", 2)
    pdf.table(
        ["Kanál", "Priorita", "Náklady", "Očekávaný podíl"],
        [
            ["Přímý prodej (web + demo)", "Vysoká", "Nízké", "50 %"],
            ["Referral program", "Vysoká", "Variabilní (15 %)", "20 %"],
            ["IT distributoři", "Střední", "Marže 20–30 %", "15 %"],
            ["Veřejné zakázky", "Střední", "Admin overhead", "10 %"],
            ["Konference / events", "Nízká", "40 000 Kč/rok", "5 %"],
        ],
        [50, 25, 45, 40],
    )

    # ==================== 10. SWOT ====================
    pdf.add_page()
    pdf.section("10. SWOT analýza")

    pdf.section("Silné stránky (Strengths)", 2)
    pdf.bullet("Unikátní morfologická inteligence pro inflektivní jazyky — žádný konkurent")
    pdf.bullet("100% offline — splňuje nejpřísnější bezpečnostní požadavky")
    pdf.bullet("34 kategorií PII — nejširší pokrytí na trhu")
    pdf.bullet("Produkt je hotový a validovaný (200+ smluv, 0 reálných leaků)")
    pdf.bullet("Nízké provozní náklady (desktop app, žádná infrastruktura)")
    pdf.bullet("Patentovatelné inovace (7 klíčových technologických inovací)")

    pdf.section("Slabé stránky (Weaknesses)", 2)
    pdf.bullet("Pouze Windows — chybí macOS/Linux verze")
    pdf.bullet("Jednočlenný tým (zakladatel = vývojář = prodejce)")
    pdf.bullet("Žádný brand awareness — nový produkt na trhu")
    pdf.bullet("Rule-based approach — potenciální omezení pro exotické jazyky")
    pdf.bullet("Závislost na python-docx — omezená podpora starších .doc formátů")

    pdf.section("Příležitosti (Opportunities)", 2)
    pdf.bullet("GDPR enforcement se zpřísňuje — rostoucí poptávka po compliance nástrojích")
    pdf.bullet("Expanze na slovenský a polský trh (10× větší TAM)")
    pdf.bullet("AI Act (2026) — další regulace zvyšující poptávku po anonymizaci dat")
    pdf.bullet("Partnerství s právními a zdravotnickými asociacemi")
    pdf.bullet("SaaS/API verze pro enterprise zákazníky (budoucí pivot)")
    pdf.bullet("Integrace s DMS systémy (SharePoint, Google Workspace)")

    pdf.section("Hrozby (Threats)", 2)
    pdf.bullet("Velcí hráči (Microsoft, Google) mohou přidat CZ podporu do existujících cloudových nástrojů")
    pdf.bullet("Open-source alternativy (Presidio + CZ community model)")
    pdf.bullet("Regulatorní změny — zmírnění GDPR by snížilo poptávku")
    pdf.bullet("Ekonomická recese — organizace škrtají IT rozpočty")
    pdf.bullet("Piráctví — nutnost robustní licence ochrany (HW binding implementováno)")

    # ==================== 11. TECHNICAL READINESS ====================
    pdf.add_page()
    pdf.section("11. Technická připravenost a validace")

    pdf.section("11.1 Stav produktu", 2)
    pdf.table(
        ["Oblast", "Stav", "Detail"],
        [
            ["Anonymizační engine", "✓ Production Ready", "v3.1.1, 6 500+ řádků, 34 PII kategorií"],
            ["GUI (Electron)", "✓ Production Ready", "Single-file HTML, 4 taby, dark theme"],
            ["OCR konverze", "✓ Production Ready", "PDF + 5 obrázkových formátů"],
            ["Deanonymizace", "✓ Production Ready", "Plně reverzibilní"],
            ["Hromadné zpracování", "✓ Production Ready", "3 watchery (anon/deanon/PDF)"],
            ["Licence systém", "✓ Production Ready", "HW-bound, AppData persistence"],
            ["PDF certifikát", "✓ Production Ready", "SHA-256, GDPR doložka"],
            ["Windows installer", "✓ Production Ready", "NSIS, ~100 MB"],
            ["Dokumentace", "✓ Kompletní", "Technická + veřejná + EULA"],
        ],
        [48, 40, 82],
    )

    pdf.section("11.2 Validace kvality", 2)
    pdf.table(
        ["Test", "Rozsah", "Výsledek"],
        [
            ["Standardní validátor", "200+ smluv", "100 % PASS"],
            ["Přísný validátor (v2)", "200+ smluv", "100 % PASS"],
            ["Brute-force cross-check", "200+ smluv", "0 reálných leaků"],
            ["Manuální audit", "201 smluv (1 po 1)", "0 reálných leaků, 7 false positives"],
            ["Stress-test (cizí jména)", "15 speciálních smluv", "100 % PASS"],
            ["Regresní test po opravě", "201 smluv (re-anonymizace)", "Beze změn"],
        ],
        [52, 42, 76],
    )

    pdf.section("11.3 Testovací korpus", 2)
    pdf.body(
        "Testovací korpus obsahuje 200+ syntetických smluv pokrývajících: pracovní smlouvy, "
        "kupní smlouvy, nájemní smlouvy, trestní spisy, lékařské zprávy, rodinněprávní dokumenty, "
        "finanční smlouvy, exekuční příkazy, darovací smlouvy a další. "
        "Smlouvy obsahují české i zahraniční jména (vietnamská, německá, polská, anglická), "
        "SSH klíče, RFID identifikátory, LinkedIn profily, datové schránky a další PII."
    )

    # ==================== 12. TEAM ====================
    pdf.add_page()
    pdf.section("12. Tým a organizace")

    pdf.section("12.1 Současný tým", 2)
    pdf.body(
        "Nixminds s.r.o. je technologická společnost zaměřená na NLP a GDPR compliance nástroje. "
        "SKRYI Document Suite byl vyvinut jako hlavní produkt společnosti."
    )

    pdf.section("12.2 Plán rozšíření týmu", 2)
    pdf.table(
        ["Role", "Kdy", "Důvod"],
        [
            ["Sales / Account Manager", "Měsíc 6–9", "Přímý prodej a enterprise vztahy"],
            ["Customer Support", "Měsíc 9–12", "Podpora zákazníků, onboarding"],
            ["Backend Developer", "Rok 2", "Polská/slovenská lokalizace engine"],
            ["Marketing Specialist", "Rok 2", "Content marketing, SEO, PPC"],
        ],
        [50, 30, 100],
    )

    # ==================== 13. ROADMAP ====================
    pdf.section("13. Produktová roadmapa")

    roadmap = [
        ("Q1 2026", [
            "Produkt v3.1.1 dokončen",
            "Testovací korpus 200+ smluv",
            "Business plan připraven",
        ]),
        ("Q2 2026", [
            "Landing page + trial verze online",
            "Pilotní zákazníci (5-10)",
            "Sbírání testimonials",
        ]),
        ("Q3 2026", [
            "První placené licence",
            "Referral program",
            "ČAK partnerství",
        ]),
        ("Q4 2026", [
            "40-60 licencí celkem",
            "Slovenská lokalizace zahájena",
            "Enterprise onboarding",
        ]),
        ("2027 H1", [
            "SK verze v produkci",
            "130+ licencí",
            "Účast na konferencích",
        ]),
        ("2027 H2", [
            "Polská verze - R&D",
            "API/SaaS prototyp",
            "200+ licencí",
        ]),
        ("2028", [
            "PL verze v produkci",
            "macOS verze",
            "350+ licencí",
            "Série A / break-even",
        ]),
    ]
    for period, milestones in roadmap:
        pdf.section(period, 3)
        for m in milestones:
            pdf.bullet(m)

    # ==================== 14. CONCLUSION ====================
    pdf.add_page()
    pdf.section("14. Závěr a doporučení")

    pdf.body(
        "SKRYI Document Suite je technologicky vyspělý, plně validovaný produkt řešící reálný "
        "a rostoucí problém na trhu. Kombinace morfologické inteligence, offline provozu a širokého "
        "pokrytí PII kategorií vytváří silnou konkurenční výhodu bez přímého konkurenta."
    )

    pdf.section("Klíčová doporučení", 2)
    pdf.bullet(
        "Spustit trial verzi co nejdříve — produkt je hotový, trh čeká. Každý měsíc bez prodeje je "
        "ztracená příležitost."
    )
    pdf.bullet(
        "Zaměřit se na advokátní kanceláře jako první segment — nejvyšší ochota platit, "
        "nejsilnější regulatorní tlak, dobře definovaný use case."
    )
    pdf.bullet(
        "Investovat do partnerství s ČAK (Česká advokátní komora) — doporučení od ČAK = "
        "okamžitá důvěryhodnost u tisíců kanceláří."
    )
    pdf.bullet(
        "Chránit IP — zvážit patentovou přihlášku na klíčové morfologické inovace "
        "(bidirekcionalní inference, kaskádový systém pravidel)."
    )
    pdf.bullet(
        "Plánovat slovenskou a polskou lokalizaci jako hlavní growth lever — "
        "polský trh je 4× větší a má identický problém."
    )

    pdf.ln(10)
    pdf.set_draw_color(30, 60, 120)
    pdf.set_line_width(0.5)
    pdf.line(50, pdf.get_y(), pdf.w - 50, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "Nixminds s.r.o. | info@nixminds.com", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Dokument vygenerován: {datetime.now().strftime('%d. %m. %Y %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "CONFIDENTIAL — Pouze pro interní použití", align="C")

    # Save
    out = os.path.join(os.path.dirname(__file__), "SKRYI_Business_Plan.pdf")
    pdf.output(out)
    print(f"[OK] Business plan saved to: {out}")
    print(f"     Pages: {pdf.page_no()}")
    return out


if __name__ == "__main__":
    build()
