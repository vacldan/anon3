# PyArmor - Ochrana Python kódu

## Co bylo provedeno

Všechny kritické Python soubory byly obfuskovány pomocí PyArmor 9 pro ochranu před:
- Dekompilací
- Reverse-engineering
- Krádežím zdrojového kódu

### Obfuskované soubory

**Core CLI skripty:**
- `validate_license_cli.py` - validace licencí
- `anonymize_cli.py` - anonymizace dokumentů
- `deanonymizator_lokal.py` - deanonymizace
- `pdf2docx_cli.py` - PDF konverze

**Licensing modul:**
- `licensing/hw_fingerprint.py` - Hardware ID generování
- `licensing/license_validator.py` - Validace licencí
- `licensing/license_generator.py` - Generování licencí

**NEOBFUSKOVANÉ soubory:**
- `get_hw_id.py` - Zákazník musí tento skript spustit aby získal HW ID

## Instalace obfuskovaných souborů

### Automatický způsob

Spusť deploy skript:
```bash
python deploy_obfuscated.py
```

Tento skript:
1. Zazálohuje původní soubory do `backup_original/`
2. Nahradí je obfuskovanými verzemi z `dist_obfuscated/`
3. Zkopíruje `pyarmor_runtime_000000/` runtime

### Manuální způsob

1. **Zálohuj původní soubory:**
   ```bash
   mkdir backup_original
   cp *.py backup_original/
   cp -r licensing backup_original/
   ```

2. **Zkopíruj obfuskované soubory:**
   ```bash
   cp dist_obfuscated/*.py .
   cp -r dist_obfuscated/licensing .
   cp -r dist_obfuscated/pyarmor_runtime_000000 .
   ```

3. **Restartuj aplikaci**

## Testování

Po instalaci obfuskovaných souborů otestuj:

1. **Spuštění aplikace:**
   ```bash
   electron . --enable-logging
   ```

2. **Kontrola licence:**
   ```bash
   python validate_license_cli.py
   ```

3. **Test anonymizace:**
   - Vyber DOCX soubor
   - Spusť anonymizaci
   - Zkontroluj výstup

## PyArmor Runtime

Složka `pyarmor_runtime_000000/` obsahuje runtime nutný pro spuštění obfuskovaného kódu.

**DŮLEŽITÉ:**
- Tato složka MUSÍ být přítomna v root projektu
- NIKDY ji nemazat
- Při distribuci aplikace ji VŽDY zabalit

## Build nové verze

Když upravíš zdrojový kód a potřebuješ znovu obfuskovat:

```bash
python build_obfuscated.py
```

Tento skript:
- Obfuskuje všechny Python soubory
- Vytvoří novou `dist_obfuscated/` složku
- Připraví soubory k nasazení

## Výhody PyArmor

✅ **Ochrana proti dekompilaci** - Nelze získat původní Python kód
✅ **Obfuscated bytecode** - Kód je zašifrován
✅ **Runtime protection** - Spouští se pouze s runtime
✅ **Bez změny funkcionality** - Aplikace funguje stejně jako předtím

## Co zákazník vidí

Když zákazník otevře `.py` soubor v editoru, uvidí:
- Binární/nečitelný kód
- Šifrované stringy
- Nepochopitelnou strukturu

**Nemůže:**
- Modifikovat logiku
- Odstranit licensing check
- Zkopírovat algoritmy

## Distribuce zákazníkovi

Při distribuci aplikace balíš:
```
nixminds-anonymizer/
├── main.js
├── index.html
├── package.json
├── *.py (obfuskované)
├── licensing/ (obfuskovaná)
├── pyarmor_runtime_000000/ (MUSÍ být zahrnuta!)
├── get_hw_id.py (NEOBFUSKOVANÝ - zákazník ho spouští)
└── license.lic (generovaná licence pro zákazníka)
```

## Poznámky

- PyArmor runtime je malá (několik KB)
- Performance impact je minimální
- Obfuskace je kompatibilní s Python 3.11+
- Licence je na 1 rok (PyArmor verze 9 je free pro komerční použití)

## Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'pyarmor_runtime_000000'`
**Řešení:** Zkopíruj složku `pyarmor_runtime_000000/` do root projektu

**Problem:** Aplikace nefunguje po obfuskaci
**Řešení:** Obnov z `backup_original/` a znovu spusť `build_obfuscated.py`

**Problem:** Zákazník nemůže spustit `get_hw_id.py`
**Řešení:** Tento soubor NENÍ obfuskovaný - zkontroluj že jsi ho nekopíroval z dist_obfuscated/
