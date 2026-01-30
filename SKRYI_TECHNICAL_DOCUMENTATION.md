# SKRYI Document Suite - Technická dokumentace v3.0

## Kompletní řešení pro anonymizaci citlivých dokumentů

---

# 1. PŘEHLED PRODUKTU

## 1.1 Název produktu
**SKRYI Document Suite** - Offline anonymizační systém pro GDPR compliance

## 1.2 Verze
**3.0.0** (Production Ready)

## 1.3 Účel
Automatická anonymizace osobních údajů v dokumentech (DOCX, PDF) s podporou českého jazyka včetně morfologických variant (skloňování). Systém je navržen pro **plně offline provoz** - žádná data neopouštějí zařízení uživatele.

## 1.4 Klíčové vlastnosti
- ✅ **100% Offline** - žádná data na internet
- ✅ **GDPR Compliant** - splňuje požadavky nařízení
- ✅ **Morfologická inteligence** - rozpoznává pádové varianty jmen
- ✅ **Reverzibilní anonymizace** - možnost deanonymizace s klíčem
- ✅ **Hardware-bound licence** - ochrana proti neoprávněnému kopírování
- ✅ **Nativní kompilace** - zdrojový kód chráněn před reverzním inženýrstvím

---

# 2. ARCHITEKTURA SYSTÉMU

## 2.1 Technologický stack

| Vrstva | Technologie | Účel |
|--------|-------------|------|
| **Frontend** | Electron + HTML/CSS/JS | Uživatelské rozhraní |
| **Backend** | Python 3.11 | Anonymizační engine |
| **Kompilace** | Nuitka | Převod Python → nativní binárky |
| **Balení** | electron-builder + NSIS | Windows installer |

## 2.2 Komponenty systému

```
SKRYI Document Suite/
├── SKRYI Document Suite.exe    # Hlavní aplikace (Electron)
├── license.lic                 # Licenční soubor zákazníka
└── resources/
    └── app.asar.unpacked/
        ├── validate_license_standalone.exe  # Validace licence (5.9 MB)
        ├── anonymize_cli.exe               # Anonymizace (5.8 MB)
        ├── deanonymizator_lokal.exe        # Deanonymizace (9.8 MB)
        ├── pdf2docx_cli.exe                # PDF konverze (70 MB)
        └── cz_names.v1.json                # Databáze českých jmen (232 KB)
```

## 2.3 Datový tok

```
                    ┌─────────────────────┐
                    │   Uživatel          │
                    │   (DOCX/PDF)        │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Electron GUI      │
                    │   (main.js)         │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼─────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│  pdf2docx_cli.exe │ │ anonymize_cli   │ │ deanonymizator  │
│  (PDF → DOCX)     │ │    .exe         │ │   _lokal.exe    │
└───────────────────┘ └────────┬────────┘ └─────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Anonymizační       │
                    │  Engine             │
                    │  (anon7.2)          │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼─────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│ dokument_anon.docx│ │ map.json        │ │ map.txt         │
│ (anonymizovaný)   │ │ (strojový klíč) │ │ (čitelný klíč)  │
└───────────────────┘ └─────────────────┘ └─────────────────┘
```

---

# 3. ANONYMIZAČNÍ ENGINE

## 3.1 Detekované entity (PII)

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

## 3.2 Morfologická inference (klíčová inovace)

### Problém v češtině:
```
"Smlouvu podepsal Jan Novák. Janu Novákovi byla předána kopie.
S Janem Novákem bylo dohodnuto splácení."
```

Běžné systémy by vytvořily 3 různé entity. **SKRYI** rozpozná, že jde o **jednu osobu** ve 3 pádech.

### Řešení - Bidirectionální inference:

**Forward mapping** (generování variant):
```
"Jan Novák" → {
    nominativ: "Jan Novák",
    genitiv: "Jana Nováka",
    dativ: "Janu Novákovi",
    akuzativ: "Jana Nováka",
    vokativ: "Jane Nováku",
    lokál: "Janu Novákovi",
    instrumentál: "Janem Novákem"
}
```

**Backward inference** (zpětné odvození):
```
"Novákem" → koncovka "-em" → instrumentál → stem "Novák" → nominativ "Novák"
```

### Výsledek anonymizace:
```
"Smlouvu podepsal [[UŽIVATEL_1]]. [[UŽIVATEL_1]] byla předána kopie.
S [[UŽIVATEL_1]] bylo dohodnuto splácení."
```

**Mapa náhrad:**
```json
{
  "UŽIVATEL_1": {
    "original": "Jan Novák",
    "variants": ["Jana Nováka", "Janu Novákovi", "Janem Novákem"],
    "occurrences": 3
  }
}
```

---

# 4. LICENČNÍ SYSTÉM

## 4.1 Přehled

Systém používá **hardware-bound offline licence** - licence je vázána na konkrétní počítač zákazníka.

## 4.2 Hardware ID (HW ID)

HW ID je unikátní identifikátor počítače vypočítaný z:
- **CPU ID** - identifikátor procesoru
- **MAC adresa** - síťová karta
- **Disk Serial** - sériové číslo disku

```python
hw_id = SHA256(f"{cpu_id}:{mac_address}:{disk_serial}")[:16]
# Příklad: C87C-FA4E-F36D-48AE
```

## 4.3 Formát licence

Licenční soubor (`license.lic`) obsahuje Base64 encoded JSON:

```json
{
  "license_key": "XXXX-XXXX-XXXX-XXXX",
  "customer": {
    "name": "Jan Novák",
    "email": "jan@firma.cz"
  },
  "hw_id": "C87CFA4EF36D48AE",
  "type": "standard|professional|enterprise",
  "issued_at": "2026-01-30T10:00:00",
  "expires_at": "2027-01-30T10:00:00",
  "signature": "sha256_hash..."
}
```

## 4.4 Ověření licence

```
┌─────────────────────────────────────────────────────────────┐
│                    VALIDACE LICENCE                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Načti license.lic ze složky aplikace                     │
│ 2. Dekóduj Base64 → JSON                                    │
│ 3. Ověř podpis (HMAC-SHA256 s MASTER_SECRET)               │
│ 4. Porovnej HW ID v licenci s aktuálním HW ID počítače     │
│ 5. Zkontroluj expiraci (expires_at > now)                  │
│ 6. Pokud vše OK → spusť aplikaci                           │
│    Pokud NE → zobraz HW ID pro aktivaci                    │
└─────────────────────────────────────────────────────────────┘
```

## 4.5 Aktivační proces zákazníka

```
1. Zákazník nainstaluje aplikaci
2. Aplikace zobrazí: "Váš Hardware ID: C87C-FA4E-F36D-48AE"
3. Zákazník pošle HW ID prodejci
4. Prodejce vygeneruje licenci pomocí license_generator.py
5. Zákazník obdrží soubor license.lic
6. Zákazník umístí license.lic do složky s aplikací
7. Aplikace se spustí
```

## 4.6 Typy licencí

| Typ | Platnost | Určení |
|-----|----------|--------|
| `trial` | 30 dní | Zkušební verze |
| `standard` | 1 rok | Jednotlivci, malé firmy |
| `professional` | 1 rok | Střední firmy |
| `enterprise` | 1 rok | Velké organizace |

---

# 5. OCHRANA KÓDU

## 5.1 Kompilace pomocí Nuitka

Python zdrojové kódy jsou kompilovány do **nativních Windows executable** pomocí Nuitka kompilátoru.

### Proces kompilace:

```bash
# Instalace
pip install nuitka

# Kompilace do standalone .exe
python -m nuitka --onefile --standalone validate_license_standalone.py
```

### Výhody:

| Aspekt | Python (.py) | Nuitka (.exe) |
|--------|--------------|---------------|
| Čitelnost | ✅ Plně čitelný | ❌ Binární kód |
| MASTER_SECRET | ⚠️ Viditelný | ✅ Embedded v binárce |
| Reverse engineering | Snadný | Velmi obtížný |
| Rychlost | Interpretovaný | Nativní (rychlejší) |
| Závislosti | Potřebuje Python | Standalone |

## 5.2 Chráněné komponenty

| Soubor | Velikost | Obsah |
|--------|----------|-------|
| `validate_license_standalone.exe` | 5.9 MB | MASTER_SECRET, HW ID algoritmus |
| `anonymize_cli.exe` | 5.8 MB | Anonymizační logika |
| `deanonymizator_lokal.exe` | 9.8 MB | Deanonymizační logika |
| `pdf2docx_cli.exe` | 70 MB | PDF konverze |

## 5.3 MASTER_SECRET

Kritický tajný klíč pro podepisování licencí. Je "zapečetěn" v binárním kódu `validate_license_standalone.exe`.

```
BEZPEČNOST:
- ❌ Nikdy v plain-text souborech
- ❌ Nikdy v gitu
- ✅ Pouze v kompilované binárce
- ✅ Pouze prodejce zná MASTER_SECRET pro generování licencí
```

---

# 6. BUILD PROCES

## 6.1 Požadavky

- Node.js 16+
- Python 3.11
- Nuitka (`pip install nuitka`)
- C++ kompilátor (Nuitka si stáhne automaticky)

## 6.2 Kompletní build

```bash
cd C:\Nixminds\skryi-clean

# 1. Instalace závislostí
npm install

# 2. Kompilace Python → .exe (trvá 10-20 minut)
python build/build_with_nuitka.py

# 3. Kopírování zkompilovaných souborů
copy dist_nuitka\*.exe . /Y

# 4. Smazání originálních .py souborů (DŮLEŽITÉ!)
del validate_license_standalone.py
del anonymize_cli.py
del deanonymizator_lokal.py
del pdf2docx_cli.py
del "anon7.2 - s padama.py"

# 5. Build Windows installer
npm run dist

# Výsledek: dist/SKRYI-Setup-3.0.0.exe
```

## 6.3 Struktura projektu

```
skryi-clean/
├── main.js                 # Electron hlavní proces
├── index.html              # UI
├── package.json            # Konfigurace
├── logo.png                # Logo aplikace
├── build/
│   ├── icon.ico            # Ikona aplikace
│   ├── build_with_nuitka.py # Nuitka build script
│   └── build_with_trial_pyarmor.py # (alternativa - PyArmor)
├── licensing/
│   └── license_generator.py # ADMIN: Generátor licencí
└── dist/
    └── SKRYI-Setup-3.0.0.exe # Výsledný installer
```

---

# 7. ADMINISTRACE LICENCÍ

## 7.1 Generování licence pro zákazníka

```bash
cd licensing
python license_generator.py
```

```
======================================================================
SKRYI LICENSE GENERATOR
======================================================================

Jméno zákazníka: Jan Novák
Email zákazníka: jan@firma.cz
Hardware ID: C87C-FA4E-F36D-48AE

Typy licencí:
  1) trial       - Zkušební (30 dní)
  2) standard    - Standardní (1 rok)
  3) professional - Profesionální (1 rok)
  4) enterprise  - Enterprise (1 rok)

Vyberte typ [1-5]: 2

✅ Licence uložena do: license_jan_novak_XXXX-XXX.lic
```

## 7.2 Distribuce licence

1. Vygenerovaný `.lic` soubor pošlete zákazníkovi
2. Zákazník umístí soubor do `C:\Program Files\SKRYI Document Suite\`
3. Přejmenuje na `license.lic` (pokud je potřeba)
4. Restartuje aplikaci

---

# 8. UŽIVATELSKÝ MANUÁL

## 8.1 Instalace

1. Spusťte `SKRYI-Setup-3.0.0.exe`
2. Zvolte instalační složku
3. Dokončete instalaci
4. Při prvním spuštění zadejte licenci (viz sekce 4.5)

## 8.2 Anonymizace dokumentu

1. Klikněte na **"Anonymizace"**
2. Vyberte DOCX soubor
3. Klikněte **"Anonymizovat"**
4. Výsledky:
   - `dokument_anon.docx` - anonymizovaný dokument
   - `dokument_map.json` - klíč pro deanonymizaci
   - `dokument_map.txt` - čitelný přehled náhrad

## 8.3 Deanonymizace dokumentu

1. Klikněte na **"Deanonymizace"**
2. Vyberte anonymizovaný DOCX
3. Vyberte příslušný `_map.json` soubor
4. Klikněte **"Deanonymizovat"**
5. Výsledek: `dokument_deanon.docx`

## 8.4 Konverze PDF → DOCX

1. Klikněte na **"PDF → DOCX"**
2. Vyberte PDF soubor
3. Výsledek: DOCX soubor ve stejné složce

---

# 9. BEZPEČNOSTNÍ ASPEKTY

## 9.1 Ochrana dat

| Aspekt | Implementace |
|--------|--------------|
| Data v klidu | Soubory zůstávají na lokálním disku |
| Data v přenosu | Žádný síťový přenos |
| Zpracování | 100% offline |
| Logy | Minimální, žádné PII |

## 9.2 Ochrana software

| Hrozba | Ochrana |
|--------|---------|
| Kopírování licence | Hardware-bound (HW ID) |
| Čtení zdrojového kódu | Nuitka kompilace |
| Padělání licence | HMAC-SHA256 podpis |
| Reverse engineering | Nativní binární kód |

## 9.3 GDPR Compliance

- ✅ Minimalizace dat - zpracovává se pouze to, co je potřeba
- ✅ Účelové omezení - data použita pouze pro anonymizaci
- ✅ Lokální zpracování - žádný přenos na servery třetích stran
- ✅ Reverzibilita - možnost deanonymizace s klíčem

---

# 10. PODPORA A KONTAKT

**Výrobce:** Nixminds s.r.o.
**Email:** info@nixminds.com
**Verze dokumentace:** 3.0.0
**Datum:** 30. ledna 2026

---

*© 2026 Nixminds s.r.o. Všechna práva vyhrazena.*
