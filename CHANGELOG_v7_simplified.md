# Změny v Claude_code_6_v7_simplified.py

## Datum: 20.11.2024

## Cíl: Zjednodušení anonymizace - pouze PII data

### ✅ Odstraněno 14 non-PII patterns (105 řádků kódu)

Podle GDPR a definitivního seznamu PII byly odstraněny patterns, které **nejsou** osobní identifikátory:

1. **AMOUNT_RE** - Částky (Kč, EUR, USD)
2. **VARIABLE_SYMBOL_RE** - Variabilní symboly
3. **CONST_SYMBOL_RE** - Konstantní symboly
4. **SPEC_SYMBOL_RE** - Specifické symboly
5. **LICENSE_ID_RE** - Čísla lékařů
6. **CASE_ID_RE** - Spisová čísla
7. **COURT_FILE_RE** - Soudní spisy
8. **POLICY_ID_RE** - Čísla pojistných smluv
9. **CONTRACT_ID_RE** - Čísla smluv
10. **BENEFIT_CARD_RE** - Benefitní karty (MultiSport, Sodexo)
11. **DIPLOMA_ID_RE** - Čísla diplomů
12. **EMPLOYEE_ID_RE** - Zaměstnanecká čísla
13. **SECURITY_CLEARANCE_RE** - NBÚ prověrky
14. **LAB_ID_RE** - Laboratorní ID

### ✅ Přidáno 3 chybějící PII patterns

Podle GDPR a definitivního seznamu byly přidány chybějící identifikátory:

1. **VIN_RE** - VIN vozidla (Vehicle Identification Number)
   - Formát: 17 znaků (A-HJ-NPR-Z0-9)
   - Příklad: TMBCF61Z0L7654321

2. **MAC_RE** - MAC adresa (Media Access Control)
   - Formáty: 00:1B:44:11:3A:B7, 00-1B-44-11-3A-B7, 001B.4411.3AB7
   - Příklad: 00:1B:44:11:3A:B7

3. **IMEI_RE** - IMEI mobilu (International Mobile Equipment Identity)
   - Formát: 15 číslic
   - Příklad: 123456789012345

### 📊 Statistiky

- **Před**: 43 patterns, 1577 řádků
- **Po**: 32 patterns, 1472 řádků
- **Rozdíl**: -11 patterns, -105 řádků (-6.7%)

### ✅ Zachováno 29 PII patterns

#### Přímé identifikátory osob:
- PERSON (jméno, příjmení) + inference
- BIRTH_ID_RE - Rodné číslo
- BIRTH_DATE_RE - Datum narození
- ADDRESS_RE - Adresa
- PHONE_RE - Telefon
- EMAIL_RE - Email

#### Finanční identifikátory:
- BANK_RE - Bankovní účet
- IBAN_RE - IBAN
- CARD_RE - Platební karta
- INSURANCE_ID_RE - Číslo pojištěnce

#### Úřední identifikátory:
- ID_CARD_RE - Občanský průkaz
- PASSPORT_RE - Pas
- DRIVER_LICENSE_RE - Řidičský průkaz
- ICO_RE - IČO
- DIC_RE - DIČ

#### Vozidla:
- LICENSE_PLATE_RE - SPZ
- **VIN_RE** - VIN (NOVÝ)

#### Digitální identifikátory:
- IP_RE - IP adresa
- **MAC_RE** - MAC adresa (NOVÝ)
- **IMEI_RE** - IMEI (NOVÝ)
- RFID_RE - RFID karta

#### Přihlašovací údaje:
- PASSWORD_RE - Hesla
- API_KEY_RE - API klíče
- SECRET_RE - Secret keys
- SSH_KEY_RE - SSH klíče
- CREDENTIALS_RE - Přihlašovací údaje
- USERNAME_RE - Usernames
- ACCOUNT_ID_RE - Account ID
- HOSTNAME_RE - Hostname

#### Biometrické:
- GENETIC_ID_RE - Genetické identifikátory (rs...)

#### Pomocné:
- DATE_RE, DOB_RE, DATE_WORDS_RE - Datum (všeobecné)

### 🎯 Výsledek

✅ Kód je nyní **GDPR-compliant** a anonymizuje pouze **skutečné PII data**
✅ Odstraněny non-PII patterns (částky, symboly, spisová čísla, atd.)
✅ Přidány chybějící PII patterns (VIN, MAC, IMEI)
✅ Testováno na smlouvě 13 - funguje správně (35 osob, 153 entit)

### 📝 Poznámky

- Všechny změny jsou v souladu s definitivním seznamem PII
- Kód je kratší a přehlednější
- Zachovány všechny důležité PII identifikátory
