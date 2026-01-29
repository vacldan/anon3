# Nixminds Document Suite - Installer Setup

## PyArmor Trial License Workaround

**PROBLEM**: PyArmor trial verze má limity na velikost souborů. Soubor `anon7.2 - s padama.py` (100KB) je příliš velký.

**ŘEŠENÍ**: Použij nový build script který obfuskuje pouze kritické soubory:

```cmd
# Spusti build script pro trial verzi
python build/build_with_trial_pyarmor.py

# Zkopiruj obfuskovane soubory
copy dist_obfuscated\validate_license_standalone.py .
copy dist_obfuscated\anonymize_cli.py .
copy dist_obfuscated\deanonymizator.py .
copy dist_obfuscated\pdf2docx_cli.py .
xcopy dist_obfuscated\pyarmor_runtime_* pyarmor_runtime_*\ /E /I /Y

# Build installer
npm run dist
```

**CO JE CHRÁNĚNO**:
- `validate_license_standalone.py` - OBFUSKOVÁN (obsahuje MASTER_SECRET)
- `anonymize_cli.py` - OBFUSKOVÁN (pokud trial dovolí)
- `deanonymizator.py` - OBFUSKOVÁN (pokud trial dovolí)

**CO NENÍ CHRÁNĚNO** (trial limit):
- `anon7.2 - s padama.py` - zkopírován jako je (příliš velký)

Pro plnou ochranu: Kup PyArmor Pro licenci ($70-200)

---

## PROBLEM: Installer obsahuje zbytecne soubory

Puvodni konfigurace `"files": ["**/*"]` balila VSECHNO vcetne:
- Testovacich dokumentu (smlouva*.docx)
- Historie (historie*.txt)
- Debug souboru

## RESENI: Pouzij CISTOU konfiguraci

### Krok 1: Aktualizuj package.json

Nahrad sekci `"build"` v tvem package.json obsahem z:
`build/package-build-clean.json`

Tato konfigurace:
- Zahrnuje POUZE potrebne soubory (main.js, index.html, Python skripty)
- VYLUCUJE testovaci dokumenty (*.docx)
- VYLUCUJE historie a logy (*.txt, *.log)
- VYLUCUJE debug soubory

### Krok 2: Vytvor ikonu (volitelne)

1. Jdi na: https://convertico.com/
2. Nahraj obrazek oka (PNG)
3. Stahni jako icon.ico
4. Uloz do: `build/icon.ico`

**Pokud ikonu nechces:**
Odeber tyto radky z package.json:
```json
"icon": "build/icon.ico",
"installerIcon": "build/icon.ico",
"uninstallerIcon": "build/icon.ico"
```

### Krok 3: Build

```cmd
cd C:\Nixminds\nixminds-anonymizer

# Vymaz cache
rmdir /s /q dist
rmdir /s /q %LOCALAPPDATA%\electron-builder\Cache

# Build
npm run dist
```

---

## DULEZITE: PyArmor Obfuskace

Pred buildovanim MUSIS obfuskovat Python soubory:

```cmd
# 1. Nainstaluj PyArmor
pip install pyarmor

# 2. Obfuskuj hlavni soubory
pyarmor gen -O dist_obfuscated/ validate_license_standalone.py anonymize_cli.py deanonymizator.py pdf2docx_cli.py

# 3. Obfuskuj licensing modul
pyarmor gen -O dist_obfuscated/licensing/ licensing/__init__.py licensing/hw_fingerprint.py licensing/license_validator.py

# 4. Zkopiruj obfuskovane soubory zpet
copy dist_obfuscated\*.py .
xcopy dist_obfuscated\licensing\*.py licensing\ /Y

# 5. Build
npm run dist
```

---

## Struktura po instalaci (SPRAVNA)

```
C:\Program Files\Nixminds\Nixminds Document Suite\
├── Nixminds Document Suite.exe
├── license.lic                    <- Zakaznik sem prida licenci
└── resources\
    └── app.asar.unpacked\
        ├── validate_license_standalone.py  <- OBFUSKOVANY
        ├── anonymize_cli.py                <- OBFUSKOVANY
        ├── deanonymizator.py               <- OBFUSKOVANY
        ├── licensing\
        │   └── *.py                        <- OBFUSKOVANE
        ├── pyarmor_runtime_000000\         <- Runtime
        └── cz_names.v1.json
```

ZADNE testovaci dokumenty (smlouva*.docx)!
ZADNE historie (historie*.txt)!
