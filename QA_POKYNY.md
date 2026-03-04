# QA Pokyny – Hodnocení kvality anonymizace

## 1. Přehled

Každá anonymizovaná smlouva se hodnotí skórem **0–10 bodů** (start 10.0). Body se strhávají podle závažnosti nalezených problémů. Výsledek určuje, zda je anonymizace přijatelná (GO) nebo vyžaduje opravu (NO-GO).

### Verdikt

| Skóre | Verdikt | Význam |
|-------|---------|--------|
| ≥ 9.0 a 0 kritických | **GO** ✓ | Anonymizace je v pořádku |
| < 9.0 nebo ≥ 1 kritická | **NO-GO** ✗ | Vyžaduje opravu |

---

## 2. Hodnoticí matice

### 2.1 KRITICKÉ chyby (−3.0 za každou) — musí být 0

Jakákoli citlivá data v plaintextu = okamžitý NO-GO bez ohledu na celkové skóre.

| # | Chyba | Popis | Příklad |
|---|-------|-------|---------|
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

### 2.2 ZÁVAŽNÉ chyby (−1.0 za každou)

| # | Chyba | Popis | Příklad |
|---|-------|-------|---------|
| Z1 | `wrong_entity_type` | Entita přiřazena do špatné kategorie | Telefon `+420 777 123 456` tagován jako `[[AMOUNT_*]]` |
| Z2 | `phone_as_AMOUNT` | Telefonní číslo klasifikováno jako AMOUNT | Kontext jasně říká telefon, ale tag je AMOUNT |
| Z3 | `idcard_as_PHONE` | Číslo OP/pasu klasifikováno jako PHONE | `AB 456789` tagováno jako `[[PHONE_*]]` |
| Z4 | `IBAN_as_CARD` | IBAN klasifikován jako CARD nebo naopak | IBAN formát ale tag `[[CARD_*]]` |
| Z5 | `merged_persons` | Dvě různé osoby sloučeny pod jeden tag | Novák i Svoboda oba jako `[[PERSON_1]]` |
| Z6 | `split_person` | Jedna osoba rozštěpena do více tagů (ne pádové varianty) | `Jan Novák` jako `[[PERSON_1]]`, `Jana Nováka` jako `[[PERSON_2]]` |
| Z7 | `incomplete_redaction` | Karta tagovaná, ale CVV/expirace zůstaly v textu | `[[CARD_1]], CVV: 123, exp: 05/28` |
| Z8 | `map_inconsistency` | Sekce v textu existuje, ale v mapě chybí | Text má IBAN tagy, mapa nemá IBAN sekci |
| Z9 | `BANK_wrong_context` | Bankovní účet taguje číslo jednací nebo jiný identifikátor | Číslo spisu `42 C 18/2023` jako `[[BANK_*]]` |
| Z10 | `address_tail` | Adresa v textu zachytila „ocásek" (telefon, email, kontext) | `[[ADDRESS_1]]` = `Křenová 14, 602 00 Brno Kontakt` |

### 2.3 DROBNÉ chyby (−0.3 až −0.5 za každou)

| # | Chyba | Srážka | Popis | Příklad |
|---|-------|--------|-------|---------|
| D1 | `canonical_not_nominative` | −0.5 | Kanonická forma v mapě není v 1. pádě (nominativ) | Mapa: `Nováka` místo `Novák` |
| D2 | `canonical_diacritics` | −0.5 | Chybná diakritika v kanonické formě | `-ova` místo `-ová`; `Štik` místo `Štika` |
| D3 | `canonical_gender_mismatch` | −0.5 | Gender mismatch (mužské křestní + ženské příjmení nebo naopak) | `Petra Nový` (místo `Petr Nový`) |
| D4 | `blacklist_as_person` | −0.5 | Slovo z blacklistu detekováno jako osoba | `Prosím David` nebo `Firma Horáková` jako osoba |
| D5 | `firstname_not_in_library` | −0.5 | Křestní jméno osoby není v `cz_names.v1.json` (pravděpodobně role/nesmysl) | `Manager Horák` detekován jako osoba |
| D6 | `phantom_person` | −0.5 | Osoba v mapě, jejíž tag se v dokumentu nevyskytuje | `[[PERSON_23]]: Eva Nová` v mapě, ale nikde v textu |
| D7 | `address_prefix_in_map` | −0.3 | Adresa v mapě obsahuje prefix typu „Sídlo:", „Bydliště:" | Mapa: `Sídlo: Křenová 14, Brno` místo `Křenová 14, Brno` |
| D8 | `dob_plaintext` | −0.3 | Datum narození ponecháno v plaintextu, přestože jiné datumy jsou tgovány | `nar. 15.3.1992` v textu |
| D9 | `typographic_artifact` | −0.3 | Typografické artefakty kolem tagů | `]]Email:`, `.:`, `[[PERSON_1]]]]` |
| D10 | `variant_typo` | −0.3 | Překlep v příjmení ve variantě v mapě | `Dvořáek` místo `Dvořák` v mapě |
| D11 | `tech_token_as_phone` | −0.3 | Technický token (IRIS_, VOICE_, HASH_BIO_) tagován jako PHONE | `IRIS_7749382` jako `[[PHONE_*]]` |

### 2.4 BONUSY (+0.2 až +0.3, max. celkem +0.5)

| # | Bonus | Body | Podmínka |
|---|-------|------|----------|
| B1 | END-SCAN | +0.3 | Důsledný druhý průchod po náhradách (karty/Luhn, IBAN, hesla, e-maily nalepené na `]]`) |
| B2 | Precedence | +0.2 | Implementovaná priorita detekce (CARD > IBAN > BIRTH_ID > ... > PERSON) eliminuje mis-matchy |
| B3 | Strict PERSON validation | +0.2 | Validace křestního jména proti knihovně + pádová kanonizace v 1. pádě |

---

## 3. Algoritmus výpočtu skóre

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

Aby jedna kategorie nepřevážila celé hodnocení:

| Kategorie | Max. celková srážka |
|-----------|---------------------|
| Kanonické formy (D1, D2, D3) | −3.0 |
| Blacklist + names.json (D4, D5) | −2.0 |
| Úniky jmen (K7) | −3.0 (každý je kritický) |
| Phantom osoby (D6) | −2.0 |
| Nepokrytá reálná jména | −3.0 |

---

## 4. Příklad výpočtu

### Smlouva se 2 drobnými chybami a 1 bonusem:

```
Start:                           10.0
D2: canonical_diacritics ×1      −0.5
D6: phantom_person ×2            −1.0
B3: strict PERSON validation     +0.2
─────────────────────────────────────
Skóre:                            8.7/10 → NO-GO (< 9.0)
```

### Smlouva bez chyb + 2 bonusy:

```
Start:                           10.0
B1: END-SCAN                     +0.3
B3: strict PERSON validation     +0.2
─────────────────────────────────────
Skóre:                           10.0/10 → GO ✓ (cap +0.5 → 10.0)
```

### Smlouva s 1 kritickou chybou:

```
Start:                           10.0
K7: plain_PERSON_leak ×1         −3.0
─────────────────────────────────────
Skóre:                            7.0/10 → NO-GO ✗ (kritická chyba!)
```

---

## 5. Priorita detekce entit (precedence)

Při překryvu typů (např. číslo může být PHONE i AMOUNT) platí tato priorita (shora = nejvyšší):

1. **CARD** (platební karta, Luhn validace)
2. **IBAN**
3. **BIRTH_ID** (rodné číslo)
4. **ID_CARD** (číslo OP/pasu)
5. **INSURANCE_ID**
6. **EMAIL**
7. **USERNAME / ACCOUNT**
8. **PASSWORD**
9. **API_KEY / SECRET**
10. **IP / HOST**
11. **PHONE**
12. **BANK** (číslo účtu)
13. **ADDRESS**
14. **AMOUNT**
15. **DATE**
16. **PERSON**
17. **ORG / PLACE / PRODUCT / TERM**

---

## 6. Heuristiky a regexy (referenční)

| Entita | Regex / heuristika |
|--------|-------------------|
| CARD | `\b(?:\d[ -]?){13,19}\b` + Luhn validace |
| IBAN (CZ) | `\b[A-Z]{2}\d{2}(?:\s?\d{4}){5}\b` |
| BANK (CZ účet) | `\b\d{2,6}[- ]?\d{0,10}(?:/\d{4})\b` + kontext |
| PHONE (CZ/EU) | `\b(?:\+?420[\s-]?)?(?:\d{3}[\s-]?){2}\d{3}\b` |
| EMAIL | `(?<!\w)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?!\w)` |
| PASSWORD | `(?i)\b(password\|heslo)\s*:\s*\S+` |
| USERNAME | `(?i)\b(Login\|Username\|Uživatel)\b.*?:\s*([A-Za-z0-9._\-@]+)` |
| ID_CARD | `AB 123456`, `OP: 123456789` (nesmí spadnout do PHONE) |
| BIRTH_ID | `\b\d{2}[01]\d[0-3]\d/?\d{3,4}\b` + kontext (RČ, rodné číslo, nar.) |

---

## 7. Specifická pravidla pro PERSON

### 7.1 Kanonická forma

- Musí být vždy v **1. pádě (nominativ)**.
- Ženská příjmení: `-ová` (s dlouhým ó), ne `-ova`.
- Ženská příjmení na `-á`: `Pokorná`, `Malá`, ne `Pokorna`, `Mala`.
- Mužská příjmení na `-a` (Sýkora, Zíka): zachovat `-a` v nominativu.
- Mužská příjmení s vložným `-e-` (Havel, Pavel): zachovat v nominativu.
- Mužská příjmení konsonantní: `Beran`, ne `Berana`.
- Mužská příjmení na `-ek`: `Kolísek`, ne `Kolísk`.

### 7.2 Pádové varianty

Všechny pády téhož jména se sloučí pod **jeden tag**:
- `Julie Matoušková` (nom.) → `[[PERSON_X]]`
- `Julii Matouškové` (dat.) → `[[PERSON_X]]`
- `Julií Matouškovou` (instr.) → `[[PERSON_X]]`

### 7.3 Validace křestního jména

Křestní jméno MUSÍ existovat v `cz_names.v1.json`. Pokud ne → neanonymizovat jako osobu.

### 7.4 Blacklist (ne-osoby)

Do mapy osob NESMÍ patřit:
- Zdvořilostní obraty: `Prosím` + jméno
- Firemní reference: `Firma` + příjmení
- Role/pozice: Manager, Developer, Architect, Director, Chief, Officer, Senior, Account, Services, Risk

---

## 8. Specifická pravidla pro ADDRESS

- V textu: tag nahrazuje **pouze** adresu, ne okolní text (telefon, email, kontext).
- V mapě: **čistá adresa** bez prefixů (`Sídlo:`, `Bydliště:`, `Adresa:`).

---

## 9. QA guardrails (pro CI / automatizaci)

Kontrolní body pro automatické QA:

1. **End-scan**: Po všech náhradách druhý průchod na karty (Luhn), IBAN, hesla, API/secret, telefony, e-maily nalepené na `]]`.
2. **1:1 mapa ↔ text**: Každý tag v textu má záznam v mapě; žádná prázdná hodnota; v TEST MODE žádné `***REDACTED***`.
3. **PERSON validace**: Křestní jméno v knihovně nebo silný kontext; 1. pád; pádové varianty sloučeny.
4. **BANK/IBAN integrita**: Žádné „ocásky" číslic; IBAN vždy `[[IBAN_*]]`, účet vždy `[[BANK_*]]`.
5. **PHONE ≠ AMOUNT**: PHONE běží před AMOUNT v precedenci; whitelist technických prefixů (IRIS_, VOICE_...).
6. **Adresy v mapě**: Bez prefixů typu „Sídlo:", „Bydliště:".

---

## 10. Požadovaný formát reportu

Pro každou smlouvu:

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

## 11. Workflow (postup)

1. Anonymizovat smlouvy: `python anon72.py test_data/smlouvaXX.docx`
2. Spustit deep validaci: `python deep_validate.py`
3. Projít souhrnnou tabulku – pokud skóre < 9.0 → opravit
4. **Priorita oprav:**
   - Kritické (K1–K10) → vždy opravit jako první
   - Závažné (Z1–Z10) → opravit v dalším kole
   - Drobné (D1–D11) → opravit po vyřešení kritických a závažných
5. Po opravě → znovu anonymizovat + validovat (iterovat dokud průměr ≥ 9.0)

---

## 12. Poznámky

- Toto je **testovací konfigurace** – mapy obsahují plné citlivé hodnoty. V produkci se CARD/PASSWORD/API_KEY/SECRET logují jako REDACTED/last4.
- `deep_validate.py` implementuje subset těchto kontrol (zaměřený na PERSON). Pro plný audit všech entit použijte `_gdpr_audit.py` nebo manuální revizi dle tohoto dokumentu.
- Skóre z `deep_validate.py` a z tohoto QA dokumentu se mohou mírně lišit (jiné váhy). Tento dokument je **nadřazený** a slouží jako finální reference.
