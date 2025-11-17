# 🔍 AUDIT SMLOUVA 13 - VÝSLEDEK

**Datum auditu:** 2025-11-17
**Auditor:** Claude (Senior GDPR/PII Auditor)
**Testovací soubor:** smlouva13.docx
**Anonymizovaný výstup:** smlouva13_anon.docx
**Mapa:** smlouva13_map.json / smlouva13_map.txt
**Testovací kód:** Claude_code_6_complete.py (commit 403ed02)

---

## ⚠️ VERDIKT: **-197.6/10 → NO-GO**

**Důvod:** Systém není v souladu s TEST MODE konfigurací podle audit.txt. Mapa obsahuje 63 položek s ***REDACTED*** hodnotami, což je v TEST režimu **ZAKÁZÁNO**. Navíc všechna rodná čísla (18×) byla chybně klasifikována jako BANK účty místo BIRTH_ID.

---

## 📊 TABULKA ODPOČTŮ

| Kategorie | Počet | Bodová penalizace | Celkem |
|-----------|-------|-------------------|--------|
| **HARD FAILS** | 63 | -3.0 každý | **-189.0** |
| **MAJOR chyby** | 18 | -1.0 každý | **-18.0** |
| **MINOR chyby** | 2 | -0.3 každý | **-0.6** |
| **Bonusy** | 0 | +0.0 | **+0.0** |
| | | **CELKEM:** | **-197.6/10** |

**Výpočet:**
```
Skóre = 10.0 - 189.0 - 18.0 - 0.6 + 0.0 = -197.6
```

**Požadavek pro GO:**
- Skóre ≥ 9.3 ✗ (dosaženo: -197.6)
- 0 HARD FAILS ✗ (dosaženo: 63)

---

## 🚨 KRITICKÉ NÁLEZY (HARD FAILS)

### HF-1: map_value_contains_redacted (63 položek, -189.0 bodů)

**Popis:** V TEST MODE je ZAKÁZÁNO ukládat ***REDACTED*** hodnoty do mapy. Mapa musí obsahovat PLNÉ originální hodnoty pro auditní účely.

**Zjištěno v:** `smlouva13_map.json`

**Příklady z mapy:**

```json
{
  "type": "BANK",
  "label": "[[BANK_1]]",
  "original": "***REDACTED_1***",  // ← ZAKÁZÁNO V TEST MODE!
  "occurrences": 1
}
```

**Detailní rozpis:**
1. **BANK:** 51 položek s `***REDACTED_X***`
   - Příklady: BANK_1 až BANK_51 (všechny)

2. **CARD:** 5 položek s `***REDACTED_X***`
   - CARD_1 až CARD_5 (všechny)

3. **IBAN:** 4 položky s `***REDACTED_X***`
   - IBAN_1 až IBAN_4 (všechny)

4. **PASSWORD:** 3 položky s `***REDACTED_X***`
   - PASSWORD_1 až PASSWORD_3 (všechny)

**Podle audit.txt (řádek 62):**
> `map_value_contains_redacted` – TEST MODE: mapa nesmí obsahovat ***REDACTED***

**Podle audit.txt (řádek 69):**
> Poznámka: Toto je testovací konfigurace – mapy obsahují celé citlivé hodnoty (PCI/GDPR NEBEZPEČNÉ). Do produkce přepni LOG_VALUES pro CARD/PASSWORD/API_KEY/SECRET na REDACTED/last4...

**Důsledek:** 63 HARD FAILs × (-3.0) = **-189.0 bodů**

---

## ⚠️ DALŠÍ CHYBY (MAJOR/MINOR)

### MAJOR-1: Rodná čísla chybně klasifikována jako BANK (18 položek, -18.0 bodů)

**Popis:** Všechna rodná čísla v dokumentu byla detekována a tagována jako bankovní účty ([[BANK_X]]) místo správné kategorie [[BIRTH_ID_X]].

**Příklady z anonymizovaného dokumentu:**

**Řádek 18:**
```
Rodné číslo: [[BANK_1]]
```
✗ Mělo být: `Rodné číslo: [[BIRTH_ID_1]]`

**Řádek 31:**
```
Rodné číslo: [[BANK_3]]
```
✗ Mělo být: `Rodné číslo: [[BIRTH_ID_2]]`

**Řádek 58:**
```
Rodné číslo: [[BANK_5]]
```
✗ Mělo být: `Rodné číslo: [[BIRTH_ID_3]]`

**Celkový výskyt:** 18 rodných čísel chybně tagovaných jako BANK

**Podle audit.txt (řádek 159):**
> Špatné přiřazení typu/kontextu (např. BANK v čísle jednacím; PHONE uvnitř IRIS_/VOICE_; IBAN jako CARD)

**Důsledek:** 18 MAJOR chyb × (-1.0) = **-18.0 bodů**

---

### MINOR-1: Nesrovnalost mezi mapou a textem (2 položky, -0.6 bodů)

**Popis:** Dva tagy jsou v mapě, ale nejsou použity v anonymizovaném textu.

**Chybějící tagy:**
- PHONE_10 (v mapě, ne v textu)
- PHONE_11 (v mapě, ne v textu)

**Podle audit.txt (řádek 162):**
> Nekonzistence mapy (sekce v textu existuje, ale v mapě chybí; slité dvě různé osoby do jedné kanoniky)

**Důsledek:** 2 MINOR chyby × (-0.3) = **-0.6 bodů**

---

## ✅ CO JE OK

Navzdory kritickým problémům systém správně zpracoval:

1. **PERSON detekce:** 35 osob úspěšně identifikováno a tagováno
   - Všechna jména jsou z české knihovny (7092 jmen načteno)
   - Pádové varianty správně sloučeny

2. **EMAIL anonymizace:** 21 emailových adres správně tagováno
   - Žádný plain email v textu
   - Všechny emaily v mapě obsahují plné hodnoty (správně v TEST MODE)

3. **PHONE anonymizace:** 18 telefonních čísel správně tagováno
   - Žádné plain telefony v textu
   - Detekce českých formátů (+420 i bez předvolby)

4. **ADDRESS anonymizace:** 9 adres správně tagováno
   - Adresy v mapě jsou čisté (bez prefixů "Sídlo:")
   - Správný formát s PSČ

5. **ICO/DIČ:** Správně identifikováno a tagováno
   - ICO: 8 položek
   - DIČ: 3 položky

6. **ID_CARD:** 4 občanské průkazy správně tagováno

7. **AMOUNT:** 65 částek správně tagováno
   - Správné rozlišení od telefonních čísel

8. **IP/HOST:** Technické údaje správně tagováno
   - IP adresy: 3
   - Hostname: 1

9. **USERNAME:** 3 uživatelská jména správně tagováno

10. **Žádné plain citlivé údaje v textu:**
    - Žádné plain IBAN ✓
    - Žádné plain karty ✓
    - Žádné plain emaily ✓
    - CVV a expirace karet správně anonymizovány ✓

---

## 🔧 POŽADOVANÉ FIXY

### FIX-1: Přepnout z PRODUCTION na TEST MODE (KRITICKÝ)

**Problém:** Kód běží v produkčním režimu a redaktuje citlivé hodnoty v mapě.

**Řešení:** V kódu `Claude_code_6_complete.py` změnit konfiguraci logu hodnot:

```python
# CURRENT (PRODUCTION MODE):
LOG_VALUES = {
    'BANK': 'REDACTED',
    'IBAN': 'REDACTED',
    'CARD': 'REDACTED',
    'PASSWORD': 'REDACTED',
    # ...
}

# ZMĚNIT NA (TEST MODE):
LOG_VALUES = {
    'BANK': 'full',
    'IBAN': 'full',
    'CARD': 'full',
    'PASSWORD': 'full',
    # ...
}
```

**Očekávaný dopad:** -189.0 → 0.0 (eliminuje všechny HARD FAILs)

---

### FIX-2: Opravit detekci rodných čísel (KRITICKÝ)

**Problém:** Regex pro BIRTH_ID není dostatečně prioritní nebo má špatný kontext.

**Řešení:**

1. **Zvýšit prioritu BIRTH_ID v CATEGORY_PRECEDENCE:**
   ```python
   CATEGORY_PRECEDENCE = [
       'CARD',
       'IBAN',
       'BIRTH_ID',      # ← Posunout výše, před BANK
       'ID_CARD',
       # ...
       'BANK',          # ← Posunout níže
   ]
   ```

2. **Zlepšit regex a kontextovou detekci:**
   ```python
   BIRTH_ID_RE = re.compile(
       r'(?:RČ|rodné číslo|r\.č\.|nar\.|narozen[aáý]?)\s*:?\s*'
       r'(\d{6}/?\d{3,4})\b',
       re.IGNORECASE
   )
   ```

3. **Přidat silný kontextový filtr:**
   - Pokud je context "Rodné číslo:", VŽDY použít BIRTH_ID
   - Pokud je format `XXXXXX/XXXX`, preferovat BIRTH_ID

**Očekávaný dopad:** -18.0 → 0.0

---

### FIX-3: Vyčistit nepoužité tagy z mapy (MINOR)

**Problém:** PHONE_10 a PHONE_11 jsou v mapě, ale ne v textu.

**Řešení:** Přidat post-processing cleanup:
```python
# Po anonymizaci:
text_tags = set(re.findall(r'\[\[([A-Z_]+_\d+)\]\]', anon_text))
map_tags = set(map_dict.keys())
unused_tags = map_tags - text_tags
for tag in unused_tags:
    del map_dict[tag]
```

**Očekávaný dopad:** -0.6 → 0.0

---

## 📈 OČEKÁVANÉ SKÓRE PO FIXECH

Po implementaci všech fixů:

```
Skóre = 10.0 - 0.0 (HARD) - 0.0 (MAJOR) - 0.0 (MINOR) + 0.3 (BONUS) = 10.3
```

**Bonusy (+0.3):**
- Důsledná anonymizace emailů, telefonů, adres
- Správná precedence (po FIX-2)
- Validace PERSON proti knihovně

**Zaokrouhleno:** **10.0/10 → GO** ✓

---

## 📋 QA CHECKLIST (pro CI)

Po implementaci fixů ověřit:

- [ ] **TEST MODE aktivní:** Všechny hodnoty v mapě jsou plné (žádné ***REDACTED***)
- [ ] **BIRTH_ID detekce:** Všechna RČ tagována jako [[BIRTH_ID_X]], ne [[BANK_X]]
- [ ] **Žádné plain citlivé údaje:** CARD (Luhn), IBAN, EMAIL, PHONE, BANK
- [ ] **1:1 mapa ↔ text:** Každý tag v textu má položku v mapě
- [ ] **PERSON validace:** Všechna jména z knihovny nebo se silným kontextem
- [ ] **Precedence:** CARD, IBAN, BIRTH_ID před BANK a PHONE před AMOUNT

---

## 📊 JAK JSEM POČÍTALA HODNOCENÍ

### Systém bodování (podle audit.txt)

**Start skóre:** 10.0

**HARD FAILS (-3.0 každý):**
- Podle audit.txt řádky 131-155
- Musí být 0, jinak automaticky NO-GO
- Zjištěno: 63 položek s ***REDACTED*** v mapě
- Výpočet: 63 × (-3.0) = -189.0

**MAJOR chyby (-1.0 každý):**
- Podle audit.txt řádky 157-166
- Špatné přiřazení typu/kontextu
- Zjištěno: 18 rodných čísel tagovaných jako BANK
- Výpočet: 18 × (-1.0) = -18.0

**MINOR chyby (-0.3 až -0.5 každý):**
- Podle audit.txt řádky 168-174
- Nekonzistence mapy, typografické artefakty
- Zjištěno: 2 tagy v mapě bez použití v textu
- Výpočet: 2 × (-0.3) = -0.6

**Bonusy (+0.2 až +0.3, max +0.5):**
- Podle audit.txt řádky 176-183
- Důsledný END-SCAN, implementovaná precedence
- Zjištěno: Systém má některé dobré vlastnosti, ale kvůli HARD FAILs nelze udělit bonus
- Výpočet: 0.0 (bonusy se neudělují při NO-GO)

**Finální výpočet:**
```
score = 10.0
score -= 3.0 × 63  // HARD FAILS
score -= 1.0 × 18  // MAJOR
score -= 0.3 × 2   // MINOR
score += 0.0       // BONUS (žádný při NO-GO)
score = 10.0 - 189.0 - 18.0 - 0.6 + 0.0 = -197.6
```

**Zaokrouhlení:** -197.6 (na 1 desetinné místo)

**Verdikt:**
- GO práh: 9.3 a 0 HARD FAILS
- Dosaženo: -197.6 a 63 HARD FAILS
- **Výsledek: NO-GO**

---

## 🔍 METODIKA AUDITU

### 1. Načtení konfigurace (audit.txt)
- Přečetla jsem audit.txt a identifikovala TEST MODE požadavky
- Klíčové: LOG_VALUES = full, REQUIRE_ZERO_HARD_FAILS = true

### 2. Spuštění anonymizace
- Použila jsem: `python3 Claude_code_6_complete.py smlouva13.docx`
- Výstupy: smlouva13_anon.docx, smlouva13_map.json, smlouva13_map.txt

### 3. Analýza mapy (smlouva13_map.json)
- Kontrola všech 213 entit
- Identifikace ***REDACTED*** hodnot: 63 položek
- Ověření struktury a úplnosti

### 4. Analýza anonymizovaného textu
- Extrakce všech 246 tagů z dokumentu
- Porovnání s mapou (248 tagů)
- Hledání plain citlivých údajů pomocí regexů

### 5. Kontextová analýza
- Kontrola kontextu kolem tagů (např. "Rodné číslo: [[BANK_X]]")
- Identifikace chybných klasifikací
- Ověření logiky GDPR compliance

### 6. Výpočet skóre
- Deterministické hodnocení podle audit.txt tabulky
- Kategorizace všech nálezů (HARD/MAJOR/MINOR)
- Aplikace vzorce a zaokrouhlení

### 7. Generování reportu
- Strukturovaný výstup s příklady
- Doporučené fixy s očekávaným dopadem
- QA checklist pro CI

---

## 📝 POZNÁMKY

- Kód anonymizoval **213 entit celkem**
- Nalezeno **35 osob** v dokumentu
- Žádné plain citlivé údaje v textu (dobrá práce na regex frontu)
- Hlavní problém je **konfigurace** (PRODUCTION vs TEST MODE)
- Po fixech by mělo být skóre **~10.0/10 → GO**

---

**Konec auditu**
*Vygenerováno: 2025-11-17 20:05 UTC*
