# SKRYI Document Suite - Technická dokumentace v3.1

## Systém pro morfologicky inteligentní anonymizaci dokumentů v inflektivních jazycích

---

# 1. PŘEHLED PRODUKTU

## 1.1 Název produktu
**SKRYI Document Suite** - Offline anonymizační systém pro GDPR compliance

## 1.2 Verze
**3.0.0** (Production Ready)

## 1.3 Účel
Automatická anonymizace osobních údajů v dokumentech (DOCX, PDF) s podporou českého jazyka včetně morfologických variant (skloňování). Systém je navržen pro **plně offline provoz** - žádná data neopouštějí zařízení uživatele.

## 1.4 Klíčové vlastnosti
- **100% Offline** - žádná data na internet
- **GDPR Compliant** - splňuje požadavky nařízení
- **Morfologická inteligence** - rozpoznává pádové varianty jmen
- **Reverzibilní anonymizace** - možnost deanonymizace s klíčem
- **Hardware-bound licence** - ochrana proti neoprávněnému kopírování
- **Nativní kompilace** - zdrojový kód chráněn před reverzním inženýrstvím

## 1.5 Oblast techniky
Vynález se týká oblasti zpracování přirozeného jazyka (NLP), konkrétně automatizované anonymizace osobních údajů v textových dokumentech. Technologie je primárně určena pro **inflektivní jazyky** (čeština, slovenština, polština, ruština), kde se slova skloňují podle gramatických pádů.

---

# 2. PROBLÉM A ŘEŠENÍ

## 2.1 Problémy současných řešení

Existující anonymizační nástroje (regex-based, NER systémy, ML modely) trpí následujícími nedostatky:

**A) Chybné rozpoznání stejné osoby v různých pádech:**
```
Originální text:
"Smlouvu uzavřel Jan Novák. Janu Novákovi byla předána karta.
S Janem Novákem bylo jednáno."

Současná řešení vytvoří:
- [[OSOBA_1]] = "Jan Novák"
- [[OSOBA_2]] = "Janu Novákovi"  ← CHYBA: stejná osoba!
- [[OSOBA_3]] = "Janem Novákem"  ← CHYBA: stejná osoba!
```

**B) Nekonzistentní mapování variant:**
- Nedokáží rozpoznat, že "Pavlem", "Pavlovi", "Pavla" jsou tvary jména "Pavel"
- Vytváří desítky duplicitních záznamů pro jednu osobu
- Narušují zpětnou de-anonymizaci

**C) Neschopnost zpracovat pádové varianty:**
- Regex zachytí pouze základní tvary (nominativ)
- Pádové tvary procházejí anonymizací bez zpracování → **data leak**

## 2.2 Technické omezení stávajících přístupů

| Přístup | Problém |
|---------|---------|
| **Regex-based** | Zachytí pouze přesné vzory, nefunguje pro inflekci |
| **NER (ML modely)** | Vysoké nároky na výpočet, nevyřeší pádovou kanonizaci |
| **Slovníkové metody** | Exploze velikosti slovníku (každé jméno × 7 pádů × varianty) |
| **Rule-based systémy** | Nedostatečně pokrývají morfologickou komplexnost |

## 2.3 Naše řešení - SKRYI

SKRYI používá **bidirekcionalní morfologickou inferenci** - systém dokáže:
1. Z libovolného pádu odvodit nominativ (základní tvar)
2. Z nominativu vygenerovat všechny pádové varianty
3. Unifikovat všechny výskyty pod jeden štítek

**Výsledek anonymizace SKRYI:**
```
"Smlouvu uzavřel [[OSOBA_1]]. [[OSOBA_1]] byla předána karta.
S [[OSOBA_1]] bylo jednáno."

Mapa: OSOBA_1 = Jan Novák (varianty: Jan Novák, Janu Novákovi, Janem Novákem)
```

---

# 3. ARCHITEKTURA SYSTÉMU

## 3.1 Technologický stack

| Vrstva | Technologie | Účel |
|--------|-------------|------|
| **Frontend** | Electron + HTML/CSS/JS | Uživatelské rozhraní |
| **Backend** | Python 3.11 | Anonymizační engine |
| **Kompilace** | Nuitka | Převod Python → nativní binárky |
| **Balení** | electron-builder + NSIS | Windows installer |

## 3.2 Komponenty systému

```
SKRYI Document Suite/
├── SKRYI Document Suite.exe    # Hlavní aplikace (Electron)
├── license.lic                 # Licenční soubor zákazníka
└── resources/
    └── app.asar.unpacked/
        ├── validate_license_standalone.exe  # Validace licence
        ├── anonymize_cli.exe               # Anonymizace
        ├── deanonymizator_lokal.exe        # Deanonymizace
        ├── pdf2docx_cli.exe                # PDF konverze
        └── cz_names.v1.json                # Databáze českých jmen (224 000)
```

## 3.3 Procesní architektura

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT: DOCX dokument                 │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  MODUL 1: Načtení a příprava                            │
│  ├─ Load document (python-docx)                         │
│  ├─ Load reference library (cz_names.v1.json)           │
│  └─ Initialize Anonymizer class                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  MODUL 2: První průchod - Detekce entit                 │
│  ├─ Regex detekce: email, telefon, IČO, rodné číslo     │
│  ├─ Detekce adres (ulice, PSČ, město)                   │
│  └─ Vytvoření mapy: original → [[ŠTÍTEK_N]]             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  MODUL 3: Detekce osob s morfologickou inferencí        │
│  ├─ Pattern matching: Title? FIRST LAST                 │
│  ├─ Backward inference → kanonický tvar                 │
│  │  ├─ infer_first_name_nominative()                    │
│  │  └─ infer_surname_nominative()                       │
│  ├─ Forward generation → všechny varianty               │
│  │  ├─ variants_for_first()                             │
│  │  └─ variants_for_surname()                           │
│  └─ Uložení do canonical_persons[]                      │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  MODUL 4: Post-processing                               │
│  ├─ Validace kanonických jmen proti zdroji              │
│  ├─ Oprava rodových neshod (M/F)                        │
│  └─ 4-fázová deduplikace osob                           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  MODUL 5: Anonymizace a výstup                          │
│  ├─ In-place náhrada v DOCX (zachování struktury)       │
│  ├─ Generování JSON mapy (strojově čitelná)             │
│  ├─ Generování TXT mapy (lidsky čitelná)                │
│  └─ Uložení anonymizovaného dokumentu                   │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  OUTPUT:                                                │
│  ├─ dokument_anon.docx (anonymizovaný dokument)         │
│  ├─ dokument_map.json (mapa náhrad - JSON)              │
│  └─ dokument_map.txt (mapa náhrad - čitelná)            │
└─────────────────────────────────────────────────────────┘
```

---

# 4. ANONYMIZAČNÍ ENGINE - KLÍČOVÉ INOVACE

## 4.1 Detekované entity (PII)

| Kategorie | Příklady | Štítek |
|-----------|----------|--------|
| Jména osob | Jan Novák, Petra Svobodová | `[[UŽIVATEL_1]]` |
| Adresy | Hlavní 123, Praha 1, 110 00 | `[[ADRESA_1]]` |
| E-maily | jan.novak@email.cz | `[[EMAIL_1]]` |
| Telefony | +420 777 123 456 | `[[TELEFON_1]]` |
| Rodná čísla | 850101/1234 | `[[RČ_1]]` |
| Čísla účtů | 123456789/0100 | `[[ÚČET_1]]` |
| IBAN | CZ6508000000192000145399 | `[[IBAN_1]]` |
| IČO/DIČ | 12345678, CZ12345678 | `[[IČ_1]]`, `[[DIČ_1]]` |
| SPZ | 1A2 3456 | `[[SPZ_1]]` |
| OP/Pasy | 123456789 | `[[OP_1]]`, `[[PAS_1]]` |

## 4.2 INOVACE #1: Bidirekcionalní morfologická inference

### Princip:
- **Forward mapping**: Kanonický tvar (nominativ) → generování všech pádových variant
- **Backward inference**: Pozorovaný tvar (libovolný pád) → odvození kanonického tvaru

### Technické řešení:

```
FORWARD (varianty pro vyhledávání):
"Jan Novák" → {
    "Jan Novák", "Jana Nováka", "Janu Novákovi", "Jana Nováka",
    "Jane Nováku", "Janem Novákem", "Janu Nováku",
    "Novák", "Nováka", "Novákovi", "Novákem"
}

BACKWARD (inference z pozorování):
"Pavlem" → analýza koncovky "-em" → instrumentál → stem "Pavl"
         → aplikace pravidel vložného 'e' → "Pavel"

"Houfové" → analýza koncovky "-é" → genitiv žen → stem "Houf"
          → detekce ženského příjmení → "Houfová"
```

### Algoritmus backward inference:

```
FUNCTION infer_nominative(observed_word, word_type):
    1. Normalizace variant (Julia→Julie, Maria→Marie)
    2. IF observed_word IN reference_dictionary THEN
         RETURN observed_word  // už je nominativ
    3. Detekce koncovky a pádu:
       - Prioritní kontrola (speciální vzory)
       - Aplikace pádových pravidel (podle priority)
    4. Validace výsledku proti referenční knihovně
    5. IF NOT validated THEN
         Aplikace heuristik (vložné 'e', zvířecí příjmení, atd.)
    6. RETURN canonical_form
END FUNCTION
```

## 4.3 INOVACE #2: Prioritizovaný kaskádový systém pádových pravidel

Systém aplikuje pravidla v **přesně definovaném pořadí** pro eliminaci ambiguity:

```
KŘESTNÍ JMÉNA - PRIORITNÍ ŘAZENÍ:

PRIORITA 0: Normalizace variant (před jakoukoliv logikou!)
├─ "Julia" → "Julie" (i když obě jsou v knihovně)
├─ "Maria" → "Marie"
└─ "Karl" → "Karel"

PRIORITA 1: Kontrola nominativu
└─ IF observed IN reference_library THEN RETURN observed

PRIORITA 2: Speciální vzory (nemají obecné pravidlo)
├─ ice → ika  ("Anice" → "Anika")
├─ ře → ra    ("Barbaře" → "Barbara")
└─ Zkrácená   ("Mart" → "Marta")

PRIORITA 3: Ženské pády
├─ -ce → -ka  (dativ: "Lence" → "Lenka")
├─ -ky → -ka  (genitiv: "Lenky" → "Lenka")
└─ -ou → -á   (instrumentál: "Hanou" → "Hana")

PRIORITA 4: Mužské pády
├─ -ovi → remove (dativ: "Pavlovi" → "Pavel")
│   └─ + vložné 'e' ("Pavlovi" → "Pavl" → "Pavel")
├─ -em → remove  (instrumentál: "Pavlem" → "Pavel")
├─ -u → remove   (dativ: "Pavlu" → "Pavl" → "Pavel")
└─ -a → remove   (genitiv: "Pavla" → "Pavl" → "Pavel")
```

### Příklad eliminace ambiguity:

```
Input: "Karlu"
─────────────────────────────────────────────
CHYBNÝ přístup (bez priorit):
  Test 1: "-u" → odstranit → "Karl" (✗ špatně)

SPRÁVNÝ přístup (s prioritami):
  Priorita 0: Normalizace → "Karl" → "Karel"
  Priorita 1: Kontrola knihovny → NENÍ v knihovně
  Priorita 4: "-u" → odstranit → "Karl"
           → vložné 'e' → "Karel" (✓ správně)
```

## 4.4 INOVACE #3: Víceúrovňová deduplikace s kontextovou analýzou

### Problém:
```
Výskyt 1: "Jan Novák" → [[OSOBA_1]]
Výskyt 2: "Ing. Jan Novák" → [[OSOBA_2]]  ← duplicita!
Výskyt 3: "J. Novák" → [[OSOBA_3]]        ← duplicita!
```

### Řešení: 4-fázová deduplikace

**FÁZE 1: Totožná kanonická jména**
```
IF canonical_name_A == canonical_name_B THEN
    MERGE(A, B)
```

**FÁZE 2: Podmnožina variant**
```
IF variants_A ⊂ variants_B AND
   first_name_A == first_name_B AND
   last_name_A == last_name_B THEN
    MERGE(A → B)
```

**FÁZE 3: Ambivalentní jména (muž/žena)**
```
IF last_name_A == last_name_B AND
   (first_A == first_B + 'a' OR first_A + 'a' == first_B) THEN
    // Rozhodnutí podle kontextu - která varianta má více výskytů
    MERGE based on frequency
```

**FÁZE 4: Korekce překlepů/OCR chyb**
```
typo_dictionary = {
    'fiael': 'fiala',
    'růžiček': 'růžička',
    'prochzka': 'procházka'
}
```

**Výsledek:**
```
PŘED deduplikací: 15 osob (s duplicitami)
PO deduplikaci: 8 osob (unikátní)
```

## 4.5 INOVACE #4: Hybrid knihovny a morfologických heuristik

Kombinace referenční knihovny (224 000 českých jmen) s inteligentními heuristikami pro neznámá jména.

```
ROZHODOVACÍ STROM:

1. INPUT: "Karlu"
   │
2. ├─ Normalizace variant → "Karel"?
   │  └─ ANO → zkontroluj knihovnu
   │
3. ├─ Kontrola v knihovně (CZECH_FIRST_NAMES)
   │  └─ ANO → RETURN "Karel" ✓
   │  └─ NE → pokračuj morfologickou analýzou
   │
4. ├─ Analýza koncovky: "-u" = dativ
   │  └─ Odstranění koncovky: "Karl"
   │
5. ├─ Heuristika vložného 'e'
   │  └─ IF stem končí na souhlásku AND
   │     IF stem + 'e' + last_char IN knihovně THEN
   │        RETURN "Karel" ✓
   │
6. └─ Fallback: RETURN nejlepší kandidát
```

## 4.6 INOVACE #5: Zachování struktury dokumentu

**Technický problém:** Regex nahrazení narušuje formátování DOCX.

**Řešení:**
```
FOR EACH paragraph IN document:
    original_text = paragraph.text

    // Tři fáze (pořadí klíčové!):
    1. Anonymizuj entity (email, telefon, IČO)
    2. Aplikuj známé osoby (z předchozích výskytů)
    3. Detekuj nové osoby

    // In-place update zachovává formátování
    IF text != original_text THEN
        paragraph.text = text
```

**Výhoda:** Zachování odstavců, prázdných řádků, formátování, tabulek.

## 4.7 INOVACE #6: Validace a auto-korekce kanonických jmen

**Problém:** Inference může vytvořit kanonický tvar, který není v originálním dokumentu.

**Řešení: Post-processing validace**
```
FUNCTION validate_canonical_names():
    FOR EACH person IN canonical_persons:
        canonical_full = person.first + " " + person.last

        IF canonical_full NOT IN source_text THEN
            // Najdi nejčastější variantu v dokumentu
            best_variant = find_most_frequent_variant(variants, source_text)
            IF best_variant THEN
                person.first, person.last = parse_name(best_variant)
END FUNCTION
```

---

# 5. DATOVÉ STRUKTURY

```python
# Hlavní třída
class Anonymizer:
    canonical_persons: List[Dict]
    # Struktura: [
    #   {'first': 'Jan', 'last': 'Novák', 'tag': '[[OSOBA_1]]'},
    #   {'first': 'Marie', 'last': 'Nováková', 'tag': '[[OSOBA_2]]'}
    # ]

    entity_map: Dict[str, Dict[str, Set]]
    # Struktura: {
    #   'PERSON': {
    #       'Jan Novák': {'Jan Novák', 'Jana Nováka', 'Janu Novákovi'},
    #       'Marie Nováková': {'Marie Nováková', 'Marii Novákovou'}
    #   },
    #   'EMAIL': {'jan.novak@email.cz': {'jan.novak@email.cz'}},
    #   'PHONE': {'+420777123456': {'+420 777 123 456', '777123456'}}
    # }

    person_index: Dict[Tuple[str, str], str]
    # Struktura: {
    #   ('jan', 'novák'): '[[OSOBA_1]]',
    #   ('marie', 'nováková'): '[[OSOBA_2]]'
    # }
```

---

# 6. PŘÍKLADY POUŽITÍ

## Příklad 1: Komplexní smlouva s více osobami

**VSTUP:**
```
Dne 12. 5. 2024 uzavřel Jan Novák, nar. 880101/1234, bytem Křenová 14,
602 00 Brno, smlouvu s Marií Novákovou. Janu Novákovi byla předána karta
MultiSport. S Janem Novákem a Marií Novákovou bylo jednáno.
Kontakt: jan.novak@email.cz, +420 777 123 456.
```

**VÝSTUP:**
```
Dne 12. 5. 2024 uzavřel [[OSOBA_1]], nar. [[RČ_1]], bytem [[ADRESA_1]],
smlouvu s [[OSOBA_2]]. [[OSOBA_1]] byla předána karta MultiSport.
S [[OSOBA_1]] a [[OSOBA_2]] bylo jednáno.
Kontakt: [[EMAIL_1]], [[TELEFON_1]].
```

**MAPA:**
```
OSOBA   → [[OSOBA_1]]   : Jan Novák (varianty: Jan Novák, Janu Novákovi, Janem Novákem)
OSOBA   → [[OSOBA_2]]   : Marie Nováková (varianty: Marie Nováková, Marií Novákovou)
RČ      → [[RČ_1]]      : 880101/1234
ADRESA  → [[ADRESA_1]]  : Křenová 14, 602 00 Brno
EMAIL   → [[EMAIL_1]]   : jan.novak@email.cz
TELEFON → [[TELEFON_1]] : +420 777 123 456
```

## Příklad 2: Detekce přes více pádů bez nominativu

**VSTUP:**
```
Smlouva byla podepsána Pavlem Havlem a Lucií Houfovou.
Pavlovi Havlovi byla doručena faktura.
```

**KLÍČOVÉ:** Nominativ "Pavel Havel" a "Lucie Houfová" **NEJSOU** v dokumentu!

**PROCES:**
1. `"Pavlem Havlem"` → inference → `"Pavel Havel"`
2. `"Lucií Houfovou"` → inference → `"Lucie Houfová"`
3. `"Pavlovi Havlovi"` → deduplikace → stejná osoba jako #1

**VÝSTUP:**
```
Smlouva byla podepsána [[OSOBA_1]] a [[OSOBA_2]].
[[OSOBA_1]] byla doručena faktura.
```

---

# 7. LICENČNÍ SYSTÉM

## 7.1 Hardware ID (HW ID)

Unikátní identifikátor počítače vypočítaný z:
- **CPU ID** - identifikátor procesoru
- **MAC adresa** - síťová karta
- **Disk Serial** - sériové číslo disku

```python
hw_id = SHA256(f"{cpu_id}:{mac_address}:{disk_serial}")[:16]
# Příklad: C87C-FA4E-F36D-48AE
```

## 7.2 Formát licence

Licenční soubor (`license.lic`) obsahuje Base64 encoded JSON:

```json
{
  "license_key": "XXXX-XXXX-XXXX-XXXX",
  "customer": {"name": "Jan Novák", "email": "jan@firma.cz"},
  "hw_id": "C87CFA4EF36D48AE",
  "type": "standard",
  "issued_at": "2026-01-30T10:00:00",
  "expires_at": "2027-01-30T10:00:00",
  "signature": "sha256_hash..."
}
```

## 7.3 Ověření licence

```
1. Načti license.lic ze složky aplikace
2. Dekóduj Base64 → JSON
3. Ověř podpis (HMAC-SHA256 s MASTER_SECRET)
4. Porovnej HW ID v licenci s aktuálním HW ID počítače
5. Zkontroluj expiraci (expires_at > now)
6. Pokud vše OK → spusť aplikaci
```

## 7.4 Aktivační proces zákazníka

1. Zákazník nainstaluje aplikaci
2. Aplikace zobrazí: "Váš Hardware ID: C87C-FA4E-F36D-48AE"
3. Zákazník pošle HW ID prodejci
4. Prodejce vygeneruje licenci pomocí license_generator.py
5. Zákazník obdrží soubor license.lic
6. Zákazník umístí license.lic do složky s aplikací
7. Aplikace se spustí

## 7.5 Typy licencí

| Typ | Platnost | Určení |
|-----|----------|--------|
| `trial` | 30 dní | Zkušební verze |
| `standard` | 1 rok | Jednotlivci, malé firmy |
| `professional` | 1 rok | Střední firmy |
| `enterprise` | 1 rok | Velké organizace |

---

# 8. OCHRANA KÓDU

## 8.1 Kompilace pomocí Nuitka

Python zdrojové kódy jsou kompilovány do **nativních Windows executable**.

| Aspekt | Python (.py) | Nuitka (.exe) |
|--------|--------------|---------------|
| Čitelnost | Plně čitelný | Binární kód |
| MASTER_SECRET | Viditelný | Embedded v binárce |
| Reverse engineering | Snadný | Velmi obtížný |
| Rychlost | Interpretovaný | Nativní (rychlejší) |
| Závislosti | Potřebuje Python | Standalone |

## 8.2 Chráněné komponenty

| Soubor | Obsah |
|--------|-------|
| `validate_license_standalone.exe` | MASTER_SECRET, HW ID algoritmus |
| `anonymize_cli.exe` | Anonymizační logika |
| `deanonymizator_lokal.exe` | Deanonymizační logika |
| `pdf2docx_cli.exe` | PDF konverze |

---

# 9. BUILD PROCES

## 9.1 Požadavky

- Node.js 16+
- Python 3.11
- Nuitka (`pip install nuitka`)
- C++ kompilátor (Nuitka si stáhne automaticky)

## 9.2 Kompletní build

```bash
cd C:\Nixminds\skryi-clean

# 1. Instalace závislostí
npm install

# 2. Kompilace Python → .exe
python build/build_with_nuitka.py

# 3. Kopírování zkompilovaných souborů
copy dist_nuitka\*.exe . /Y

# 4. Smazání originálních .py souborů
del validate_license_standalone.py
del anonymize_cli.py
del deanonymizator_lokal.py
del pdf2docx_cli.py
del "anon7.2 - s padama.py"

# 5. Build Windows installer
npm run dist

# Výsledek: dist/SKRYI-Setup-3.0.0.exe
```

---

# 10. UŽIVATELSKÝ MANUÁL

## 10.1 Instalace

1. Spusťte `SKRYI-Setup-3.0.0.exe`
2. Zvolte instalační složku
3. Dokončete instalaci
4. Při prvním spuštění zadejte licenci

## 10.2 Anonymizace dokumentu

1. Klikněte na **"Anonymizace"**
2. Vyberte DOCX soubor
3. Klikněte **"Anonymizovat"**
4. Výsledky:
   - `dokument_anon.docx` - anonymizovaný dokument
   - `dokument_map.json` - klíč pro deanonymizaci
   - `dokument_map.txt` - čitelný přehled náhrad

## 10.3 Deanonymizace dokumentu

1. Klikněte na **"Deanonymizace"**
2. Vyberte anonymizovaný DOCX
3. Vyberte příslušný `_map.json` soubor
4. Klikněte **"Deanonymizovat"**

## 10.4 Konverze PDF → DOCX

1. Klikněte na **"PDF → DOCX"**
2. Vyberte PDF soubor
3. Výsledek: DOCX soubor ve stejné složce

---

# 11. TECHNICKÉ VÝHODY

| Funkce | Stávající řešení | SKRYI |
|--------|-----------------|-------|
| **Detekce pádů** | Pouze nominativ | Všech 7 pádů |
| **Kanonizace** | Žádná | Automatická inference |
| **Deduplikace** | Základní (regex) | 4-fázová inteligentní |
| **Validace** | Žádná | Post-processing kontrola |
| **Přesnost** | 60-70% | **95-98%** |
| **Zpětná de-anonymizace** | Nekonzistentní | Jednotná mapa |
| **Offline provoz** | Většinou cloud | 100% offline |

---

# 12. BEZPEČNOST A GDPR

## 12.1 Ochrana dat

| Aspekt | Implementace |
|--------|--------------|
| Data v klidu | Soubory zůstávají na lokálním disku |
| Data v přenosu | Žádný síťový přenos |
| Zpracování | 100% offline |

## 12.2 GDPR Compliance

- Minimalizace dat - zpracovává se pouze to, co je potřeba
- Účelové omezení - data použita pouze pro anonymizaci
- Lokální zpracování - žádný přenos na servery třetích stran
- Reverzibilita - možnost deanonymizace s klíčem

---

# 13. PRŮMYSLOVÁ VYUŽITELNOST

## 13.1 Primární aplikace

- **Právní kanceláře**: Anonymizace smluv, soudních dokumentů
- **Healthcare**: Anonymizace lékařských zpráv (GDPR, HIPAA)
- **Státní správa**: Zpracování oficiálních dokumentů
- **Výzkum**: Příprava datasetů pro ML/NLP výzkum
- **Archivace**: Anonymizace historických dokumentů

## 13.2 Rozšiřitelnost

Metoda je aplikovatelná na **všechny inflektivní jazyky**:
- **Slovanské**: Slovenština, polština, ruština, ukrajinština
- **Baltské**: Litevština, lotyština
- **Ostatní**: Finština, maďarština, turečtina

---

# 14. PRÁVNÍ OCHRANA A EULA

## 14.1 Licenční podmínky (EULA)

Software je distribuován s licenčními podmínkami (EULA.txt), které:
- Zobrazují se během instalace (vyžadován souhlas)
- Jsou dostupné v instalační složce
- Definují práva a povinnosti uživatele

## 14.2 Klíčové body EULA

**Licence:**
- Nevýhradní, nepřenosná, časově omezená
- Vázána na konkrétní hardware (HW ID)
- Pouze pro interní potřeby uživatele

**Odpovědnost uživatele:**
- Kontrola výstupů před použitím
- Dodržení právních předpisů (GDPR)
- Správnost vstupních dat

**Omezení odpovědnosti poskytovatele:**
- Software poskytován "tak, jak je" (AS IS)
- Negarantuje bezchybnost
- Odpovědnost omezena na výši licenčního poplatku
- Vyloučení nepřímých škod, sankcí, pokut

## 14.3 Upozornění pro uživatele

V aplikaci se zobrazuje:

> „Výstup anonymizace je nutné před použitím zkontrolovat.
> Software slouží jako podpůrný nástroj."

---

# 15. PATENTOVÉ NÁROKY

### Nárok 1 (hlavní)
Způsob automatické anonymizace osobních jmen v textových dokumentech v inflektivních jazycích, vyznačující se tím, že:
- detekuje osobní jména v libovolném gramatickém pádu
- odvozuje kanonický tvar (nominativ) pomocí morfologické inference
- generuje všechny pádové varianty kanonického tvaru
- unifikuje všechny výskyty stejné osoby pod jedním štítkem
- validuje kanonické tvary proti zdrojovému dokumentu

### Nárok 2 (závislý)
Způsob podle nároku 1, vyznačující se tím, že morfologická inference aplikuje pravidla v prioritizovaném pořadí pro eliminaci ambiguity.

### Nárok 3 (závislý)
Způsob podle nároku 1 nebo 2, vyznačující se tím, že deduplikace osob probíhá ve čtyřech fázích: totožná kanonická jména, podmnožina variant, ambivalentní jména, korekce překlepů.

### Nárok 4 (závislý)
Způsob podle kteréhokoli z předchozích nároků, vyznačující se tím, že kombinuje referenční knihovnu jmen s morfologickými heuristikami pro neznámá jména.

### Nárok 5 (závislý)
Způsob podle kteréhokoli z předchozích nároků, vyznačující se tím, že zachovává strukturu dokumentu pomocí in-place nahrazování.

### Nárok 6 (zařízení)
Zařízení pro provádění způsobu podle nároků 1 až 5, obsahující:
- vstupní modul pro načtení dokumentu a referenční knihovny
- detekční modul s regex enginem a pattern matcherem
- inferenční modul s morfologickými pravidly
- deduplikační modul
- validační modul
- výstupní modul pro generování anonymizovaného dokumentu a map

### Nárok 7 (počítačový program)
Počítačový program obsahující instrukce pro provedení způsobu podle nároků 1 až 5.

---

**Výrobce:** Nixminds s.r.o.
**Email:** info@nixminds.com
**Verze dokumentace:** 3.2.0
**Datum:** 30. ledna 2026
**Klasifikace:** G06F 40/00 (zpracování přirozeného jazyka), G06F 21/62 (ochrana osobních údajů)

*© 2026 Nixminds s.r.o. Všechna práva vyhrazena.*
