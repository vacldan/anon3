# SKRYI Licensing System

Offline hardware-bound licensing pro SKRYI Document Suite

## 📋 Přehled

Tento licensing systém zajišťuje:
- ✅ **Offline aktivaci** - zákazník nemusí být online
- ✅ **HW binding** - licence vázána na konkrétní počítač
- ✅ **Časové omezení** - automatická expirace
- ✅ **Kryptografické ověření** - nelze padělat
- ✅ **Jednoduché použití** - jeden soubor .lic

## 🔧 Pro ADMINA - Generování licencí

### 1. Získej Hardware ID od zákazníka

Zákazník spustí `get_hw_id.exe` a pošle ti HW ID (formát: `8A3F-2BC1-E9D4-5678`)

### 2. Vygeneruj licenci

```bash
python licensing/license_generator.py
```

Program tě provede interaktivním dialogem:
```
SKRYI LICENSE GENERATOR
======================================================================

Jméno zákazníka: Jan Novák
Email zákazníka: jan.novak@firma.cz
Hardware ID: 8A3F-2BC1-E9D4-5678

Typy licencí:
  1) trial       - Zkušební (30 dní)
  2) standard    - Standardní (1 rok)
  3) professional - Profesionální (1 rok)
  4) enterprise  - Enterprise (1 rok)
  5) custom      - Vlastní nastavení

Vyberte typ [1-5]: 2
Poznámky (volitelné): Objednávka #12345

Generuji licenci...

======================================================================
VYGENEROVANÁ LICENCE
======================================================================
Licenční klíč:     A7B3-9X2F-K4M8-P1Q5
Zákazník:          Jan Novák
Email:             jan.novak@firma.cz
Hardware ID:       8A3F2BC1E9D45678
Typ:               standard
Vystaveno:         2024-01-20T10:30:00
Platnost do:       2025-01-20T10:30:00
Poznámky:          Objednávka #12345
======================================================================

✅ Licence uložena do: license_jan_novak_A7B39X2F.lic

✅ Hotovo! Pošlete soubor 'license_jan_novak_A7B39X2F.lic' zákazníkovi.
   Zákazník ho umístí do složky s aplikací.
```

### 3. Pošli zákazníkovi `.lic` soubor

Zákazník tento soubor uloží do hlavní složky s aplikací (vedle .exe).

## 👤 Pro ZÁKAZNÍKA - Aktivace

### 1. Získej Hardware ID

1. Spusť `get_hw_id.exe` (součást instalace)
2. Zkopíruj zobrazený Hardware ID
3. Pošli ho prodejci

### 2. Přijmi licenční soubor

1. Prodejce ti pošle soubor `license_*.lic`
2. Ulož ho do hlavní složky s aplikací:
   ```
   SKRYI_Document_Suite/
   ├── SKRYI.exe
   ├── license.lic          ← TADY
   ├── get_hw_id.exe
   └── ...
   ```

### 3. Spusť aplikaci

Aplikace automaticky ověří licenci při startu.

## 🔒 Bezpečnost

### Master Secret Key

**KRITICKÉ:** Změň `MASTER_SECRET` v souborech:
- `licensing/license_generator.py` (řádek 14)
- `licensing/license_validator.py` (řádek 12)

Na STEJNOU VLASTNÍ NÁHODNOU HODNOTU!

```python
# PŘED distribucí ZMĚŇ TOTO:
MASTER_SECRET = "TVUJ_VLASTNI_DLOUHY_NAHODNY_STRING_ALESPON_64_ZNAKU_XYZ123ABC789"
```

### Doporučení:
1. Vygeneruj si náhodný 64+ znakový string
2. Změň ho v obou souborech
3. Nikdy ho nikomu neukazuj
4. Zálohuj ho na bezpečné místo

### Generování random stringu (Python):
```python
import secrets
secrets.token_urlsafe(48)  # Vygeneruje náhodný string
```

## 📁 Struktura souborů

```
licensing/
├── __init__.py              # Modul init
├── hw_fingerprint.py        # HW ID získávání
├── license_generator.py     # [ADMIN] Generátor licencí
├── license_validator.py     # Validátor (v aplikaci)
└── README.md               # Tento soubor

get_hw_id.py                # [ZÁKAZNÍK] Nástroj pro HW ID
```

## 🧪 Testování

### Test HW fingerprint:
```bash
python licensing/hw_fingerprint.py
```

### Test generování licence:
```bash
python licensing/license_generator.py
```

### Test validace:
```bash
# Nejdřív vygeneruj testovací licenci s TVÝM HW ID
python licensing/license_generator.py

# Pak ji validuj
python licensing/license_validator.py
```

## ⚠️ Známá omezení

1. **Změna HW** - Pokud zákazník vymění procesor/MB/disk, licence přestane fungovat
   - Řešení: Vygeneruj novou licenci s novým HW ID

2. **Bez Admin práv** - Některé HW info (MB serial) vyžadují admin práva
   - To je OK, systém funguje i bez toho (použije fallback)

3. **VM / Docker** - HW ID může být nestabilní ve virtuálních prostředích
   - Doporuč zákazníkům fyzický stroj

## 📝 Formát licenčního souboru

`.lic` soubor je Base64-encoded JSON:

```json
{
  "license_key": "A7B3-9X2F-K4M8-P1Q5",
  "customer": {
    "name": "Jan Novák",
    "email": "jan.novak@firma.cz"
  },
  "hw_id": "8A3F2BC1E9D45678",
  "type": "standard",
  "issued_at": "2024-01-20T10:30:00",
  "expires_at": "2025-01-20T10:30:00",
  "notes": "Objednávka #12345",
  "version": "1.0",
  "signature": "abc123def456..."
}
```

`signature` = HMAC-SHA256 kontrolní součet, který zajišťuje integritu.

## 🚀 Další kroky

Po implementaci základního systému můžeš přidat:
- [ ] Online validaci (volitelný server check)
- [ ] Floating licenses (více počítačů)
- [ ] Trial mechanismus (14 dní zdarma)
- [ ] Auto-renewal přes API
- [ ] Usage analytics

---

**Vytvořeno pro SKRYI Document Suite**
*Offline Hardware-Bound Licensing System v1.0*
