# QA Pokyny – Testování, validace a hodnocení anonymizace

> **Toto je jediný autoritativní dokument** pro agenty, kteří testují, kontrolují a hodnotí kvalitu anonymizace. Nahrazuje a slučuje dřívější `PRAVIDLA_TESTOVANI_A_VALIDACE.md` i `audit.txt`.

---

## 0. ZLATÉ PRAVIDLO

**Po jakékoli změně v `anon72.py`:**

1. Znovu anonymizovat testovací smlouvy (uživatel vždy určí, které smlouvy testovat)
2. Spustit `python deep_validate.py`
3. Projít **VŠECHNY** hlášené chyby a opravit **systematicky** – ne jen jednotlivé příklady

**Nikdy neopravuj jen konkrétní případ, který uživatel nahlásil.** Vždy spusť validaci a podívej se, kolik smluv má stejný problém. Oprava musí být obecná.

**Které smlouvy testovat:** Vždy čekej na instrukce od uživatele. Netestuj automaticky žádný pevný rozsah smluv.

---

## 1. Hodnoticí matice – skóre 0–10

Každá anonymizovaná smlouva se hodnotí skórem **0–10 bodů** (start 10.0). Body se strhávají podle závažnosti nalezených problémů.

### Verdikt

| Skóre | Verdikt | Význam |
|-------|---------|--------|
| ≥ 9.0 a 0 kritických | **GO** ✓ | Anonymizace je v pořádku |
| < 9.0 nebo ≥ 1 kritická | **NO-GO** ✗ | Vyžaduje opravu |

---

### 1.1 KRITICKÉ chyby (−3.0 za každou) — musí být 0

Jakákoli citlivá data v plaintextu = okamžitý NO-GO bez ohledu na celkové skóre.

| # | Kód | Popis | Příklad |
|---|-----|-------|---------|
| K1 | `plain_EMAIL` | E-mail v anonymizovaném textu bez tagu | `jan.novak@email.cz` zůstal v textu |
| K2 | `plain_BIRTH_ID` | Rodné číslo v plaintextu | `850315/6847` mimo `[[BIRTH_ID_*]]` |
| K3 | `plain_IBAN` | IBAN v plaintextu | `CZ65 0800 0000 0012 3456 7899` v textu |
| K4 | `plain_CARD` | Číslo platební karty (Luhn-valid 13–19 číslic) | `4532 0123 4567 8901` v textu |
| K5 | `plain_PASSWORD` | Heslo v prostém textu | `Heslo: MojeTajneHeslo123` v textu |
| K6 | `plain_API_SECRET` | API klíč / secret / SSH klíč v textu | `api_key: sk-abc123...` v textu |
| K7 | `plain_PERSON_leak` | Jméno osoby z mapy zůstalo v anonymizovaném dokumentu | `Martin Novák` v textu, přestože je v mapě jako `[[PERSON_1]]` |
| K8 | `tag_missing_in_map` | Tag v dokumentu nemá odpovídající záznam v mapě | `[[PERSON_15]]` v textu, ale v mapě chybí |
| K9 | `map_value_empty` | Hodnota v mapě je prázdná nebo chybí | `[[EMAIL_3]]: (prázdné)` |
| K10 | `map_value_redacted` | V TEST režimu mapa obsahuje `***REDACTED***` místo plné hodnoty | (v produkci OK, v testu zakázáno) |

### 1.2 ZÁVAŽNÉ chyby (−1.0 za každou)

| # | Kód | Popis | Příklad |
|---|-----|-------|---------|
| Z1 | `wrong_entity_type` | Entita přiřazena do špatné kategorie | Telefon `+420 777 123 456` tagován jako `[[AMOUNT_*]]` |
| Z2 | `phone_as_AMOUNT` | Telefonní číslo klasifikováno jako AMOUNT | Kontext jasně říká telefon, ale tag je AMOUNT |
| Z3 | `idcard_as_PHONE` | Číslo OP/pasu klasifikováno jako PHONE | `AB 456789` tagováno jako `[[PHONE_*]]` |
| Z4 | `IBAN_as_CARD` | IBAN klasifikován jako CARD nebo naopak | IBAN formát ale tag `[[CARD_*]]` |
| Z5 | `merged_persons` | Dvě různé osoby sloučeny pod jeden tag | Novák i Svoboda oba jako `[[PERSON_1]]` |
| Z6 | `split_person` | Jedna osoba rozštěpena do více tagů (ne pádové varianty) | `Jan Novák` = `[[PERSON_1]]`, `Jana Nováka` = `[[PERSON_2]]` |
| Z7 | `incomplete_redaction` | Karta tagovaná, ale CVV/expirace zůstaly v textu | `[[CARD_1]], CVV: 123, exp: 05/28` |
| Z8 | `map_inconsistency` | Sekce v textu existuje, ale v mapě chybí | Text má IBAN tagy, mapa nemá IBAN sekci |
| Z9 | `BANK_wrong_context` | Bankovní účet taguje číslo jednací nebo jiný identifikátor | Číslo spisu `42 C 18/2023` jako `[[BANK_*]]` |
| Z10 | `address_tail` | Adresa v textu zachytila „ocásek" (telefon, email, kontext) | `[[ADDRESS_1]]` = `Křenová 14, Brno Kontakt` |

### 1.3 DROBNÉ chyby (−0.3 až −0.5 za každou)

| # | Kód | Srážka | Popis | Příklad |
|---|-----|--------|-------|---------|
| D1 | `canonical_not_nominative` | −0.5 | Kanonická forma v mapě není v 1. pádě | Mapa: `Nováka` místo `Novák` |
| D2 | `canonical_diacritics` | −0.5 | Chybná diakritika v kanonické formě | `-ova` místo `-ová`; `Štik` místo `Štika` |
| D3 | `canonical_gender_mismatch` | −0.5 | Gender mismatch křestní ↔ příjmení | `Petra Nový` (místo `Petr Nový`) |
| D4 | `blacklist_as_person` | −0.5 | Blacklist slovo detekováno jako osoba | `Prosím David` nebo `Firma Horáková` |
| D5 | `firstname_not_in_library` | −0.5 | Křestní jméno není v `cz_names.v1.json` | `Manager Horák` detekován jako osoba |
| D6 | `phantom_person` | −0.5 | Osoba v mapě, jejíž tag není v dokumentu | `[[PERSON_23]]: Eva Nová` – tag nikde v textu |
| D7 | `address_prefix_in_map` | −0.3 | Adresa v mapě s prefixem | `Sídlo: Křenová 14, Brno` místo čisté adresy |
| D8 | `dob_plaintext` | −0.3 | Datum narození v plaintextu (ostatní datumy tgovány) | `nar. 15.3.1992` zůstalo v textu |
| D9 | `typographic_artifact` | −0.3 | Typografické artefakty kolem tagů | `]]Email:`, `.:`, `[[PERSON_1]]]]` |
| D10 | `variant_typo` | −0.3 | Překlep v příjmení ve variantě | `Dvořáek` místo `Dvořák` |
| D11 | `tech_token_as_phone` | −0.3 | Technický token tagován jako PHONE | `IRIS_7749382` jako `[[PHONE_*]]` |

### 1.4 BONUSY (+0.2 až +0.3, max. celkem +0.5)

| # | Bonus | Body | Podmínka |
|---|-------|------|----------|
| B1 | END-SCAN | +0.3 | Důsledný druhý průchod po náhradách (Luhn, IBAN, hesla, e-maily na `]]`) |
| B2 | Precedence | +0.2 | Implementovaná priorita detekce eliminuje mis-matchy |
| B3 | Strict PERSON | +0.2 | Validace křestního jména proti knihovně + pádová kanonizace |

---

## 2. Algoritmus výpočtu skóre

```
score = 10.0
score -= 3.0 × počet(KRITICKÉ)
score -= 1.0 × počet(ZÁVAŽNÉ)
score -= Σ(srážka za každou DROBNOU)     # −0.3 nebo −0.5 dle tabulky
score += min(0.5, Σ bonusů)              # max +0.5
score = max(0, round(score, 1))

VERDIKT:
  GO   = (score ≥ 9.0) AND (počet(KRITICKÉ) == 0)
  NO-GO = cokoliv jiného
```

### Stropy srážek (caps)

| Kategorie | Max. celková srážka |
|-----------|---------------------|
| Kanonické formy (D1, D2, D3) | −3.0 |
| Blacklist + names.json (D4, D5) | −2.0 |
| Úniky jmen (K7) | −3.0 (každý je kritický) |
| Phantom osoby (D6) | −2.0 |
| Nepokrytá reálná jména | −3.0 |

### Příklady výpočtu

```
# Příklad 1: dvě drobné + bonus
Start:                           10.0
D2: canonical_diacritics ×1      −0.5
D6: phantom_person ×2            −1.0
B3: strict PERSON validation     +0.2
Skóre:                            8.7/10 → NO-GO ✗

# Příklad 2: čistá smlouva + bonusy
Start:                           10.0
B1: END-SCAN                     +0.3
B3: strict PERSON validation     +0.2
Skóre:                           10.0/10 → GO ✓

# Příklad 3: kritická chyba
Start:                           10.0
K7: plain_PERSON_leak ×1         −3.0
Skóre:                            7.0/10 → NO-GO ✗ (kritická!)
```

---

## 3. Pravidla pro PERSON (detailně)

### 3.1 Kanonická forma – musí být v 1. pádě (nominativ)

| Pravidlo | Správně | Špatně |
|----------|---------|--------|
| Ženská příjmení na **-ová** (dlouhé ó) | Matoušková, Havránková, Peroutková | Matouškova, Havránkova |
| Ženská příjmení na **-á** | Pokorná, Malá, Tichá | Pokorna, Mala |
| Mužská příjmení na **-a** (Sýkora, Zíka, Štika) | Pavel Zíka, Martin Štika | Pavel Zík, Martin Štik |
| Mužská příjmení s vložným **-e-** (Havel) | Petr Havel | Petr Havl |
| Mužská příjmení konsonantní | Beran, Rendl, Konrád, Frydrych | Berana, Konráda |
| Mužská příjmení na **-ek** | Kolísek, Chrástek, Hájek | Kolísk, Chrástk |
| Mužská příjmení na **-ka** | Švestka, Paseka | Švestek |

### 3.2 Pádové varianty → jeden tag

Všechny pády téhož jména se sloučí pod jeden tag:

```
Julie Matoušková  (nom.)   → [[PERSON_X]]
Julii Matouškové  (dat.)   → [[PERSON_X]]
Julií Matouškovou (instr.) → [[PERSON_X]]
```

### 3.3 Validace křestního jména

**Hlavní obranná linie proti false positives:** křestní jméno (pozorovaná forma NEBO inferovaný nominativ) MUSÍ existovat v `cz_names.v1.json` nebo v rozšířeném seznamu. Pokud ne → **neanonymizovat jako osobu**.

Toto řeší obecně: názvy rolí (Manager, Developer, Career...), zdvořilostní obraty (Prosím), firemní reference (Firma), jakékoli ne-jméno.

### 3.4 Blacklist – ne-osoby

Do mapy osob NESMÍ patřit:

- **Zdvořilostní obraty:** „Prosím David" → Prosím NENÍ jméno
- **Firemní reference:** „Firma Horáková s.r.o." → Firma NENÍ jméno
- **Role/pozice:** Manager, Services, Risk, Account, Senior, Developer, Architect, Director, Chief, Officer

### 3.5 Úplnost anonymizace

- **Žádný tvar jména** z mapy (canonical ani varianty) nesmí zůstat v anonymizovaném dokumentu.
- Každý výskyt musí být nahrazen tagem `[[PERSON_X]]`.
- Osoby v mapě, jejichž tag se v dokumentu nevyskytuje = **phantom osoby** (chyba D6).

---

## 4. Pravidla pro ADDRESS

- V textu: tag nahrazuje **pouze** adresu, ne okolní text (telefon, email, kontext).
- V mapě: **čistá adresa** bez prefixů (`Sídlo:`, `Bydliště:`, `Adresa:`).

---

## 5. Priorita detekce entit (precedence)

Při překryvu typů platí tato priorita (shora = nejvyšší):

| # | Entita | Poznámka |
|---|--------|----------|
| 1 | **CARD** | Luhn validace, 13–19 číslic |
| 2 | **IBAN** | CZ/EU formát |
| 3 | **BIRTH_ID** | Rodné číslo + kontext |
| 4 | **ID_CARD** | Číslo OP/pasu |
| 5 | **INSURANCE_ID** | Pojistné číslo |
| 6 | **EMAIL** | Včetně „nalepených" na `]]` |
| 7 | **USERNAME / ACCOUNT** | Login, GitHub, Jira... |
| 8 | **PASSWORD** | Heslo v kontextu |
| 9 | **API_KEY / SECRET** | API klíče, SSH |
| 10 | **IP / HOST** | IP adresy, hostname |
| 11 | **PHONE** | CZ/EU formáty (běží PŘED AMOUNT) |
| 12 | **BANK** | Číslo účtu CZ |
| 13 | **ADDRESS** | Ulice, PSČ, město |
| 14 | **AMOUNT** | Částky + měny (po PHONE!) |
| 15 | **DATE** | Datumy |
| 16 | **PERSON** | Jména + pádové varianty |
| 17 | **ORG / PLACE / PRODUCT / TERM** | Ostatní |

---

## 6. Referenční regexy

| Entita | Regex / heuristika |
|--------|-------------------|
| CARD | `\b(?:\d[ -]?){13,19}\b` + Luhn |
| IBAN (CZ) | `\b[A-Z]{2}\d{2}(?:\s?\d{4}){5}\b` |
| BANK (CZ účet) | `\b\d{2,6}[- ]?\d{0,10}(?:/\d{4})\b` + kontext |
| PHONE (CZ/EU) | `\b(?:\+?420[\s-]?)?(?:\d{3}[\s-]?){2}\d{3}\b` |
| EMAIL | `(?<!\w)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?!\w)` |
| PASSWORD | `(?i)\b(password\|heslo)\s*:\s*\S+` |
| USERNAME | `(?i)\b(Login\|Username\|Uživatel)\b.*?:\s*([A-Za-z0-9._\-@]+)` |
| ID_CARD | `AB 123456`, `OP: 123456789` (nesmí spadnout do PHONE) |
| BIRTH_ID | `\b\d{2}[01]\d[0-3]\d/?\d{3,4}\b` + kontext (RČ, rodné číslo, nar.) |

---

## 7. Metodika testování

### 7.1 Spuštění anonymizace

Smlouvy k testování **určuje uživatel**. Příklady:

```bash
# Jedna smlouva
python anon72.py test_data/smlouva10.docx

# Hromadně (Linux/Mac)
for n in $(seq 10 33); do python anon72.py "test_data/smlouva$n.docx"; done

# Hromadně (PowerShell)
foreach ($n in 10..33) { if ($n -ne 30) { python anon72.py "test_data\smlouva$n.docx" } }
```

### 7.2 Spuštění deep validace

```bash
# Všechny smlouvy v test_data/
python deep_validate.py

# Jedna smlouva
python deep_validate.py test_data/smlouva10.docx
```

Skript automaticky najde nejnovější `_anon_*.docx` a `_map_*.txt` podle časového razítka.

### 7.3 Interpretace výstupu deep_validate.py

| Sekce | Co kontroluje | Při chybě → opravit |
|-------|---------------|----------------------|
| **1. Kanonické formy** | Správný nominativ a diakritika | `infer_surname_nominative` v anon72.py |
| **1b. Blacklist v osobách** | Prosím, Firma, role nesmí být osoby | `critical_blacklist` / `role_words` v anon72.py |
| **1c. Křestní jméno v names.json** | Křestní jméno existuje v knihovně | Blacklist (role/nesmysl) nebo rozšířit knihovnu |
| **2. Úniky jmen** | Žádné jméno nezůstalo v dokumentu | `variants_for_surname` / `variants_for_first` |
| **3. Phantom osoby** | Všechny osoby mají tag v dokumentu | AUTO-OPRAVA v anon72.py |
| **4. Varianty vs. zdroj** | Tvary v mapě odpovídají zdroji | Kontrola mapování |
| **5. Nepokrytá jména** | Potenciální jména ve zdroji chybí v mapě | Zkontrolovat detekci |

### 7.4 Souhrnná tabulka

Na konci hromadného běhu `deep_validate.py` vypíše:

```
Smlouva      Skóre      Kanon    Blklst   Names    Úniky    Phantom  Status
smlouva10    10/10      0        0        0        0        0        ✓
smlouva11    8.5/10     1        0        0        0        3        ✗
```

---

## 8. Testovací vzory pro ověření pravidel

Pro ověření všech pravidel by testovací dokument měl obsahovat:

### Ženská příjmení -ová
- Julie Matoušková, Julii Matouškové, Julií Matouškovou
- Elodie Havránková, Elodii Havránkové, Elodií Havránkovou

### Mužská příjmení -a
- Pavel Zíka, Pavla Zíky, Pavlovi Zíkovi
- Martin Štika, Martina Štiky, Martinovi Štikovi

### Mužská příjmení s vložným -e-
- Petr Havel, Petra Havla, Petrem Havlem, Petrovi Havlovi

### Mužská příjmení konsonantní
- Emil Konrád, Emila Konráda, Emilovi Konrádovi
- Přemysl Rendl, Přemysla Rendla, Přemyslovi Rendlovi

### Mužská příjmení -ek
- Alex Kolísek, Alexe Kolíska, Alexovi Kolískovi

### Ne-osoby (nesmí se anonymizovat)
- „Prosím Davide, dodejte podklady" → Prosím NENÍ jméno
- „Firma Horáková s.r.o." → Firma NENÍ jméno
- „Account Manager", „Senior Developer" → role, NE osoby

---

## 9. QA guardrails (pro CI / automatizaci)

1. **End-scan**: Po všech náhradách druhý průchod na karty (Luhn), IBAN, hesla, API/secret, telefony, e-maily nalepené na `]]`.
2. **1:1 mapa ↔ text**: Každý tag v textu má záznam v mapě; žádná prázdná hodnota; v TEST MODE žádné `***REDACTED***`.
3. **PERSON validace**: Křestní jméno v knihovně nebo silný kontext; 1. pád; pádové varianty sloučeny.
4. **BANK/IBAN integrita**: Žádné „ocásky" číslic; IBAN vždy `[[IBAN_*]]`, účet vždy `[[BANK_*]]`.
5. **PHONE ≠ AMOUNT**: PHONE běží před AMOUNT v precedenci; whitelist technických prefixů (IRIS_, VOICE_...).
6. **Adresy v mapě**: Bez prefixů typu „Sídlo:", „Bydliště:".

---

## 10. Formát reportu

### Jednotlivá smlouva

```
Verdikt:     X.Y/10 → GO / NO-GO + 1 věta „proč"

Tabulka odpočtů:
  Kritické (n × −3.0)   → −X.X
  Závažné  (n × −1.0)   → −X.X
  Drobné   (součet)      → −X.X
  Bonusy                 → +X.X
  ─────────────────────────────
  Konečné skóre:          X.Y/10

Kritické nálezy:  (očíslovaně, s doslovnou citací z anonymu)
Další chyby:      (ZÁVAŽNÉ/DROBNÉ stručně, s příklady)
Co je OK:         (stručný výčet bezproblémových oblastí)
Doporučené fixy:  (minimální a cílené)
```

### Souhrnná tabulka (batch)

```
Smlouva      Skóre   Krit  Závaž  Drobné  Bonus  Status
──────────────────────────────────────────────────────────
smlouva10    10/10    0     0      0       +0.5   GO ✓
smlouva11     8.5/10  0     1      1       +0.0   NO-GO ✗
smlouva12     7.0/10  1     0      0       +0.0   NO-GO ✗
──────────────────────────────────────────────────────────
Průměr:       8.5/10
```

---

## 11. Postup po změně kódu (workflow)

1. **Anonymizovat** testovací smlouvy (dle pokynů uživatele)
2. **Spustit** `python deep_validate.py`
3. **Projít** souhrnnou tabulku – pokud skóre < 9 → detail
4. **Priorita oprav:**
   - Kritické (K1–K10) → vždy jako první
   - Závažné (Z1–Z10) → v dalším kole
   - Drobné (D1–D11) → po vyřešení kritických a závažných
5. **Po opravě** → znovu od bodu 1 (iterovat dokud průměr ≥ 9.0 a 0 kritických)

---

## 12. Soubory a nástroje

| Soubor | Účel |
|--------|------|
| `anon72.py` | Hlavní anonymizátor |
| `deep_validate.py` | Validační skript (kontroly 1–5 + souhrnná tabulka) |
| `_validate_gdpr_tests.py` | Batch validace GDPR testových smluv |
| `_gdpr_audit.py` | GDPR audit helper (kontrola úniků z JSON mapy) |
| `cz_names.v1.json` | Knihovna českých křestních jmen (MVČR) |
| `test_data/smlouva10.docx` – `smlouva33.docx` | Testovací smlouvy |
| `test_data/smlouvaXX_anon_*.docx` | Anonymizované výstupy |
| `test_data/smlouvaXX_map_*.txt` | Mapy osob (textové) |
| `test_data/smlouvaXX_map_*.json` | Mapy osob (JSON) |

---

## 13. Poznámky

- Toto je **testovací konfigurace** – mapy obsahují plné citlivé hodnoty. V produkci se CARD/PASSWORD/API_KEY/SECRET logují jako REDACTED/last4.
- `deep_validate.py` implementuje subset těchto kontrol (zaměřený na PERSON). Pro plný audit všech entit (EMAIL, PHONE, BANK, IBAN, CARD atd.) použijte manuální revizi dle tohoto dokumentu.
- Tento dokument je **nadřazený** všem ostatním QA dokumentům a slouží jako finální reference.
