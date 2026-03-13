# Nixminds Document Suite - Clean Installer Build

Tento branch obsahuje pouze soubory potřebné pro vytvoření instalačního balíčku.

## Struktura souborů

```
├── main.js                        # Electron hlavní proces
├── index.html                     # UI aplikace
├── package.json                   # Konfigurace buildu
├── validate_license_standalone.py # Validace licence (obfuskovat!)
├── anonymize_cli.py               # CLI pro anonymizaci
├── deanonymizator_lokal.py        # Deanonymizace
├── pdf2docx_cli.py                # PDF konverze
├── anon72.py                       # Hlavní anonymizační engine (v7.2+, ~8250 řádků)
├── cz_names.v1.json               # Data pro české jména
├── build/
│   ├── build_with_trial_pyarmor.py  # Build script pro PyArmor trial
│   └── README-INSTALLER.md          # Detailní instrukce
└── licensing/
    └── license_generator.py       # ADMIN: Generátor licencí
```

## Rychlý build (4 kroky)

```cmd
# 1. Nainstaluj závislosti
npm install

# 2. Obfuskuj Python soubory (chrání MASTER_SECRET)
python build/build_with_trial_pyarmor.py

# 3. Zkopíruj obfuskované soubory
copy dist_obfuscated\validate_license_standalone.py . /Y
copy dist_obfuscated\anonymize_cli.py . /Y
copy dist_obfuscated\deanonymizator_lokal.py . /Y
copy dist_obfuscated\pdf2docx_cli.py . /Y
xcopy dist_obfuscated\pyarmor_runtime_000000 pyarmor_runtime_000000\ /E /I /Y

# 4. Vytvoř installer
npm run dist
```

Výsledný installer bude v `dist/` složce.

## Generování licencí (ADMIN)

```cmd
cd licensing
python license_generator.py
```

1. Zákazník nainstaluje aplikaci
2. Aplikace mu ukáže jeho Hardware ID
3. Zákazník ti pošle Hardware ID
4. Ty zadáš HW ID do generátoru a vygeneruješ `.lic` soubor
5. Pošleš zákazníkovi `.lic` soubor
6. Zákazník ho umístí do složky s aplikací a restartuje

## Hardware ID

Aplikace počítá unikátní Hardware ID z:
- CPU ID
- MAC adresa
- Sériové číslo disku

Licence je vázána na konkrétní počítač.

---

## Původní dokumentace anonymizátoru

Cíl: Tento nástroj automaticky anonymizuje osobní údaje dle GDPR v textových dokumentech (CZ/EN) a vytvoří anonymizovanou verzi dokumentu + mapu náhrad (JSON i TXT). Navržen pro zcela offline provoz.

### Klíčové vlastnosti

- Offline: žádná data neopouští zařízení
- Detekce PII: jména, adresy (víceúrovňová detekce s proximity merge), e-maily, telefony, bankovní účty, rodná čísla, IČ/DIČ, SPZ, SSH klíče, RFID, sociální sítě — 34 kategorií celkem
- Jednotné štítky: `[[PERSON_1]]`, `[[ADDRESS_1]]`, `[[BANK_ACCOUNT_1]]`
- Mapa náhrad: strojově čitelný map.json + lidsky čitelný map.txt
- Adresní engine: proximity merge komponent (PSČ, ulice, město, republika) bez ohledu na slovosled, deduplikace podmnožin, whitelist 80+ českých měst
- 6 specializovaných post-passů: izolovaná křestní jména, osiřelá příjmení, rodná jména, titulované osoby, firemní jména, RČ jako var. symboly
- Kompletní podpora mužských příjmení na -a (Fiala, Svoboda, Malina, Neruda) — 45+ kmenových sad koordinovaně pokrývajících všech 7 pádů + vokativ
- Testováno na **236 syntetických smlouvách** — 236/236 CLEAN, 0 leaků, 0 chyb, 0 warningů
