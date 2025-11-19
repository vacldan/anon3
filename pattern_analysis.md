# ANALÝZA PATTERNS - Co ponechat vs co odstranit

## ✅ MUSÍ BÝT ANONYMIZOVÁNO (podle definitivního seznamu)

### 1. Přímé identifikátory osob
- ✅ **PERSON_RE** + _replace_remaining_people() - Jméno a příjmení
- ✅ **BIRTH_ID_RE** - Rodné číslo (930715/1245)
- ✅ **BIRTH_DATE_RE** - Datum narození (15.7.1993)
- ✅ **ADDRESS_RE** - Adresa
- ✅ **PHONE_RE** - Telefon (+420 724 123 456)
- ✅ **EMAIL_RE** - Email (jan.novak@email.cz)

### 2. Finanční identifikátory
- ✅ **BANK_RE** - Číslo bankovního účtu (2345678901/0800)
- ✅ **IBAN_RE** - IBAN (CZ23 0800 ...)
- ✅ **CARD_RE** - Číslo platební karty (4532 1234 5678 9012)
- ✅ **INSURANCE_ID_RE** - Číslo pojistky (9307151245)

### 3. Úřední identifikátory
- ✅ **ID_CARD_RE** - Občanský průkaz (234567890)
- ✅ **PASSPORT_RE** - Číslo pasu (12345678)
- ✅ **DRIVER_LICENSE_RE** - Řidičský průkaz (456789012)
- ✅ **ICO_RE** - IČO u OSVČ (12345678)
- ✅ **DIC_RE** - DIČ osobní (CZ930715/1245)

### 4. Dopravní identifikátory
- ✅ **LICENSE_PLATE_RE** - SPZ (3A4 5678)
- ❌ **VIN_RE** - VIN vozidla (CHYBÍ!)

### 5. Digitální identifikátory
- ✅ **IP_RE** - IP adresa (78.45.123.89)
- ❌ **MAC_RE** - MAC adresa (CHYBÍ!)
- ❌ **IMEI_RE** - IMEI mobilu (CHYBÍ!)
- ✅ **RFID_RE** - RFID (RF-2024-0156)

### 6. Přihlašovací údaje
- ✅ **PASSWORD_RE** - Heslo
- ✅ **USERNAME_RE** - Username (jan.novak)
- ✅ **API_KEY_RE** - API klíč (ghp_Kx7m...)
- ✅ **SECRET_RE** - Secret/Token
- ✅ **SSH_KEY_RE** - SSH klíče
- ✅ **CREDENTIALS_RE** - Obecné přihlašovací údaje

### 7. Biometrické identifikátory
- ✅ **GENETIC_ID_RE** - DNA/genetické ID (HASH_BIO_JP_0156)

---

## ❌ NEMĚLO BY BÝT ANONYMIZOVÁNO (odstranit!)

### Obecné údaje (NEJSOU PII)
- ❌ **AMOUNT_RE** - Částky (1 234 Kč) - NENÍ PII!
- ❌ **CONST_SYMBOL_RE** - Konstantní symbol - NENÍ PII!
- ❌ **SPEC_SYMBOL_RE** - Specifický symbol - NENÍ PII!
- ❌ **VARIABLE_SYMBOL_RE** - Variabilní symbol - NENÍ PII!

### Identifikátory institucí/dokumentů (NEJSOU PII osoby)
- ❌ **CASE_ID_RE** - Spisové číslo (FÚ-123456/2024) - NENÍ PII!
- ❌ **COURT_FILE_RE** - Soudní spis (23 C 45/2024) - NENÍ PII!
- ❌ **POLICY_ID_RE** - Číslo pojistné smlouvy - NENÍ PII!
- ❌ **CONTRACT_ID_RE** - Číslo smlouvy - NENÍ PII!
- ❌ **LICENSE_ID_RE** - Číslo lékaře (45678) - NENÍ PII pacienta!

### Možná diskutabilní (ale nejsou přímé identifikátory)
- ❓ **BENEFIT_CARD_RE** - MultiSport (možná ano/ne)
- ❓ **DIPLOMA_ID_RE** - Číslo diplomu (VŠE/2015/12345)
- ❓ **EMPLOYEE_ID_RE** - Zaměstnanecké číslo
- ❓ **SECURITY_CLEARANCE_RE** - NBÚ prověrka
- ❓ **LAB_ID_RE** - Laboratorní ID
- ❓ **BIRTH_PLACE_RE** - Místo narození
- ❓ **ACCOUNT_ID_RE** - Account ID
- ❓ **HOSTNAME_RE** - Hostname

### Duplicitní/redundantní patterns
- ⚠️ **DATE_RE** - duplicita s BIRTH_DATE_RE (možná ponechat pro obecné datumy?)
- ⚠️ **DOB_RE** - duplicita s BIRTH_DATE_RE
- ⚠️ **DATE_WORDS_RE** - duplicita s BIRTH_DATE_RE

---

## 📊 SUMMARY

**Ponechat (27 patterns):**
1. PERSON_RE
2. BIRTH_ID_RE
3. BIRTH_DATE_RE
4. ADDRESS_RE
5. PHONE_RE
6. EMAIL_RE
7. BANK_RE
8. IBAN_RE
9. CARD_RE
10. INSURANCE_ID_RE
11. ID_CARD_RE
12. PASSPORT_RE
13. DRIVER_LICENSE_RE
14. ICO_RE
15. DIC_RE
16. LICENSE_PLATE_RE
17. IP_RE
18. RFID_RE
19. PASSWORD_RE
20. USERNAME_RE
21. API_KEY_RE
22. SECRET_RE
23. SSH_KEY_RE
24. CREDENTIALS_RE
25. GENETIC_ID_RE
26. VIN_RE (přidat)
27. MAC_RE (přidat)
28. IMEI_RE (přidat)

**Odstranit (10+ patterns):**
1. AMOUNT_RE ❌
2. CONST_SYMBOL_RE ❌
3. SPEC_SYMBOL_RE ❌
4. VARIABLE_SYMBOL_RE ❌
5. CASE_ID_RE ❌
6. COURT_FILE_RE ❌
7. POLICY_ID_RE ❌
8. CONTRACT_ID_RE ❌
9. LICENSE_ID_RE ❌
10. BENEFIT_CARD_RE ❌
11. DIPLOMA_ID_RE ❌
12. EMPLOYEE_ID_RE ❌
13. SECURITY_CLEARANCE_RE ❌
14. LAB_ID_RE ❌
15. BIRTH_PLACE_RE ❌ (?)
16. ACCOUNT_ID_RE ❌
17. HOSTNAME_RE ❌

**Výsledek: 43 patterns → ~30 patterns** (redukce o ~30%)
