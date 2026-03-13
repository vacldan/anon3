# SKRYI Document Suite - Technical Documentation

> **Version:** 3.3.0
> **Last Updated:** 2026-03-13
> **Audience:** Senior developers, DevOps engineers, maintainers

---

## 1. Architecture Overview

SKRYI Document Suite is a **desktop application** for GDPR-compliant anonymization of Czech/Slovak legal documents. It uses a **hybrid architecture**: Electron (Node.js) for the GUI shell and Python for all document processing logic.

```
┌──────────────────────────────────────────────────────┐
│                    Electron Shell                     │
│                                                       │
│  ┌─────────────┐       ┌───────────────────────────┐ │
│  │  index.html  │◄─IPC─►│       main.js             │ │
│  │  (Renderer)  │       │    (Main Process)          │ │
│  │              │       │                            │ │
│  │  - UI/CSS    │       │  - Window management       │ │
│  │  - User I/O  │       │  - License validation      │ │
│  │  - Stats     │       │  - Python discovery        │ │
│  │              │       │  - IPC handler dispatch     │ │
│  └─────────────┘       │  - Watcher management      │ │
│                         │  - Stats persistence       │ │
│                         └──────────┬────────────────┘ │
│                                    │ spawn (child_process)
│                                    ▼                   │
│  ┌──────────────────────────────────────────────────┐ │
│  │          Python Backend (compiled .exe)           │ │
│  │                                                    │ │
│  │  anonymize_cli.exe  ──imports──► anon72.pyd       │ │
│  │  deanonymizator_lokal.exe                         │ │
│  │  pdf2docx_cli.exe                                 │ │
│  │  validate_license_standalone.exe                  │ │
│  │  skryi_watcher.exe / deanon_watcher.exe           │ │
│  │  pdf2docx_watcher.exe                             │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Python compiled to .exe via Nuitka** - No Python runtime required on end-user machines. Code protection via native compilation.
2. **anon72.py compiled as .pyd module** - The 6000-line anonymization engine is compiled as an importable native module, shared by multiple executables.
3. **Single HTML file with inline CSS/JS** - The entire UI is in `index.html` (~1400 lines). No bundler, no framework.
4. **nodeIntegration: true** - The renderer process has direct access to Node.js APIs (including `ipcRenderer`). No preload script is used.

---

## 2. File Map

### Core Application Files

| File | Lines | Purpose |
|------|-------|---------|
| `main.js` | ~1360 | Electron main process. Python discovery, license check, IPC handlers, watcher management, stats. |
| `index.html` | ~1430 | Single-file UI: HTML structure, full CSS (Chrome/Silver dark theme), inline JavaScript. |
| `anon72.py` | ~8250 | Core anonymization engine. `Anonymizer` class with regex-based NER, Czech morphological inference, GDPR entity detection, 6 post-passes (standalone first names, orphan surnames, maiden names, titled names, company person names, birth ID as variable symbol), district absorption, comprehensive masculine -a surname handling. |
| `anonymize_cli.py` | ~147 | CLI wrapper that imports `anon72`, parses args, runs anonymization, outputs JSON result for Electron. |
| `deanonymizator_lokal.py` | ~300 | Reverse-anonymization: reads `_map.json`, replaces tags back to original values. |
| `pdf2docx_cli.py` | ~250 | PDF/image to DOCX converter. Uses `pdf2docx` for native PDFs, falls back to Tesseract OCR for scanned documents. |
| `validate_license_standalone.py` | ~200 | License validator. HW fingerprint (CPU+MAC+disk hash), HMAC-SHA256 signature verification. |
| `package.json` | ~100 | npm/electron-builder config. Build targets, file inclusion/exclusion rules, NSIS installer config. |

### Watcher Services (Background Processes)

| File | Watches Folder | Action |
|------|---------------|--------|
| `skryi_watcher.py` | `Documents/SKRYI/01_ANONYMIZACE/IN` | Auto-anonymize new .docx files |
| `deanon_watcher.py` | `Documents/SKRYI/02_DEANONYMIZACE/IN` | Auto-deanonymize (requires map) |
| `pdf2docx_watcher.py` | `Documents/SKRYI/03_KONVERZE_PDF/IN` | Auto-convert PDF/images to DOCX |

All watchers use the `watchdog` library (event-based, not polling). Output goes to corresponding `OUT` folder. Errors go to `SKRYI/ERROR`. Logs go to `SKRYI/LOGS`.

### Build System

| File | Purpose |
|------|---------|
| `build/build_with_nuitka.py` | Compiles all Python scripts to native .exe/.pyd via Nuitka |
| `build/build_with_trial_pyarmor.py` | Alternative build using PyArmor (obfuscation, not compilation) |
| `build/test_before_compile.py` | Pre-build tests |

### Data Files

| File | Purpose |
|------|---------|
| `cz_names.v1.json` | Czech name database. Structure: `{firstnames: {M: [...], F: [...], U: [...]}, firstnames_no_diac: {...}, surnames: {...}}` |
| `institutions_blacklist.json` | Curated list (~250–300) of institutions/companies/universities/hospitals (CZ/SK + selected neighbors) that must never be classified as PERSON. Loaded once at startup and merged into `critical_blacklist`/`role_words` in `anon72.py` and `non_person_tokens` in `run_anonymize_tests.py`. |
| `fonts/DejaVuSans.ttf` | Font for PDF report generation (fpdf2 requires explicit TTF for Czech characters) |
| `fonts/DejaVuSans-Bold.ttf` | Bold variant |
| `EULA.txt` | End-user license agreement (shown during NSIS install) |
| `assets/logo.png` | Application logo (96x96, displayed in sidebar) |

---

## 3. Electron Main Process (`main.js`)

### Startup Sequence

```
app.whenReady()
  ├── discoverPythonOnce()      // Find py/python/python3 interpreter
  │     └── Probes: PYTHON_BIN env → py -3 → python → python3
  ├── checkLicense()            // Validate license.lic
  │     ├── resolveScript("validate_license_standalone.py")
  │     ├── findLicenseFile()   // Search: exe dir → AppData → unpacked → __dirname
  │     └── spawn validator → parse JSON → copy to AppData if valid
  └── createWindow()            // BrowserWindow with nodeIntegration
        └── win.loadFile("index.html")
```

### Python Discovery (`discoverPythonOnce`)

The app first finds a working Python interpreter. Priority order:
1. `PYTHON_BIN` environment variable (user override)
2. `py -3 --version` (Windows py launcher)
3. `python --version`
4. `python3 --version`

Result stored in global `PY = { cmd, isPyLauncher }`.

### Script Resolution (`resolveScript`)

When main.js needs to run a Python tool, it calls `resolveScript(baseName)`:

```
resolveScript("anonymize_cli.py")
  ├── Search for .exe (Nuitka compiled):
  │     1. app.asar.unpacked/anonymize_cli.exe
  │     2. __dirname/anonymize_cli.exe
  ├── Fallback to .py:
  │     1. app.asar.unpacked/anonymize_cli.py
  │     2. app.asar.unpacked/python/anonymize_cli.py
  │     3. __dirname/anonymize_cli.py
  │     4. __dirname/python/anonymize_cli.py
  └── Returns { path, isExe: boolean }
```

If `isExe`, the file is spawned directly. Otherwise, it's run via the discovered Python interpreter.

### IPC Channels

All communication between renderer (index.html) and main process uses Electron IPC:

| Channel | Direction | Purpose |
|---------|-----------|---------|
| `get-app-version` | Renderer → Main | Returns `package.json` version |
| `select-file` | Renderer → Main | Open file dialog for .docx |
| `anonymize-document` | Renderer → Main | Run anonymization pipeline |
| `show-folder` | Renderer → Main | Open file in OS file manager |
| `select-anon-file` | Renderer → Main | Open dialog for anonymized .docx |
| `select-map-file` | Renderer → Main | Open dialog for .json map |
| `deanonymize-document` | Renderer → Main | Run deanonymization |
| `select-pdf-file` | Renderer → Main | Open dialog for PDF/images |
| `convert-pdf-to-docx` | Renderer → Main | Run PDF → DOCX conversion |
| `get-folder-status` | Renderer → Main | Folder structure state + watcher status |
| `open-folder` | Renderer → Main | Open specific SKRYI subfolder |
| `open-skryi-folder` | Renderer → Main | Open base SKRYI folder |
| `start-watcher` | Renderer → Main | Start watcher (anon/deanon/pdf) |
| `stop-watcher` | Renderer → Main | Stop watcher process |
| `enable-autostart` | Renderer → Main | Add Windows registry Run key |
| `disable-autostart` | Renderer → Main | Remove Windows registry Run key |
| `get-license-info` | Renderer → Main | Fetch current license details |
| `get-stats` | Renderer → Main | Read usage statistics |
| `progress-update` | Main → Renderer | Real-time progress messages (throttled to 4/sec) |

### Anonymization Flow (IPC `anonymize-document`)

```
Renderer: ipcRenderer.invoke('anonymize-document', filePath)
  │
  ▼ main.js
  1. Compute expected output paths:
     - {base}_anon.docx, {base}_map.json, {base}_map.txt, {base}_report.pdf
  2. resolveScript("anonymize_cli_turbo.py") → fallback to "anonymize_cli.py"
  3. Build CLI args: --input, --output, --map, --map_txt, --report
  4. Spawn process (exe directly or via Python interpreter)
  5. Stream stdout → sendProgress() (throttled, max 4 msg/sec)
  6. On close: parseJsonFromOutput(stdout) → extract paths from JSON
  7. Fallback file discovery if JSON parsing fails
  8. Return { success, outputFile, mapJson, mapTxt, reportPdf }
```

### Stats System

Usage statistics are persisted to `skryi_stats.json` (in AppData for production, `__dirname` for development):

```json
{
  "total_anonymized": 42,
  "total_deanonymized": 15,
  "total_pdf_converted": 8,
  "total_pdf_ocr": 3,
  "total_persons_found": 156,
  "monthly": {
    "2026-02": { "anonymized": 5, "persons_found": 23 }
  }
}
```

---

## 4. Anonymization Engine (`anon72.py`)

### Class: `Anonymizer`

The core of the system. A single instance processes one document.

```python
class Anonymizer:
    def __init__(self, verbose=False):
        self.entity_map = defaultdict(dict)     # {type: {canonical: {variants}}}
        self.canonical_persons = []              # [{first, last, tag, gender}]
        self.person_canonical_names = {}         # {tag: "First Last"}
        self.source_text = ""                    # Full document text for validation
```

### Processing Pipeline

The document is processed paragraph-by-paragraph in strict order:

```
anonymize_docx(input, output, map_json, map_txt, pdf_report)
  │
  ├── 1. Load document (python-docx)
  ├── 2. Store full source text for validation
  │
  ├── FOR EACH paragraph + table cell:
  │     ├── anonymize_entities(text)         # Regex-based entity detection
  │     │     └── Includes address post-passes:
  │     │           ├── Full-address regex patterns (multiple word orders)
  │     │           ├── Proximity merge: group nearby PSČ/street/city components
  │     │           ├── City+PSČ merge into existing ADDRESS tags
  │     │           ├── Standalone city detection (80+ Czech cities)
  │     │           ├── Country absorption (Česká/Slovenská republika)
  │     │           ├── District absorption ("[[ADDRESS_2]] - Vinohrady")
  │     │           └── ADDRESS deduplication (subset merge)
  │     ├── _apply_known_people(text)        # Replace known person variants
  │     └── _replace_remaining_people(text)  # Detect new persons via NER patterns
  │
  ├── 3. Post-processing:
  │     ├── _fix_canonical_names_not_in_document()  # Remove phantom inferences
  │     ├── _fix_gender_mismatches()                # Fix cross-gender pairs
  │     └── _deduplicate_persons()                  # Merge duplicate persons
  │           └── Returns tag_remap dict → applied to all paragraphs/tables
  │
  ├── 4. Post-pass pipeline (6 passes, on full document):
  │     ├── _postpass_standalone_firstnames(doc)      # Catch standalone first names
  │     ├── _postpass_orphan_surname_after_tag(doc)   # Absorb surname fragments after tags
  │     ├── _postpass_maiden_names(doc)               # (rozená Nováková), roz. Dvořáková
  │     ├── _postpass_titled_standalone_names(doc)     # JUDr. Novák, Ing. Dvořák
  │     ├── _postpass_company_person_names(doc)        # Horák & Partners s.r.o.
  │     └── _postpass_birth_id_as_var_symbol(doc)      # Var. symbol 6005301111 → BIRTH_ID
  │
  ├── 5. Save anonymized document
  └── 6. _create_maps() → JSON map, TXT map, PDF report
```

### Entity Detection (`anonymize_entities`)

All entity detection is **regex-based** (no ML models). The method processes text through ~40 regex substitutions in a specific order. Each match calls `_get_or_create_label(type, original)` which:
1. Normalizes the matched text
2. Checks if an equivalent entity already exists
3. Assigns a sequential tag like `[[OSOBA_1]]`, `[[ADRESA_1]]`, etc.

**Detected entity types (34 categories):**

| Category | Tag Prefix | Example Pattern |
|----------|-----------|-----------------|
| PERSON | OSOBA | Regex + Czech morphological rules |
| ADDRESS | ADRESA | Multi-level: regex patterns + proximity merge + city whitelist (80+) |
| RC (Birth Number) | RC | `\d{6}/\d{3,4}` |
| DATE | DATUM | `5. 7. 2026` format |
| BIRTH_DATE | DATUM_NAR | Date after "narozen/á" |
| BANK_ACCOUNT | UCET | Bank account number patterns |
| IBAN | IBAN | `CZ\d{2}\s?\d{4}...` |
| CARD | KARTA | 16-digit card numbers (Luhn check) |
| ICO | ICO | 8-digit with context ("IČO", "IČ") |
| DIC | DIC | `CZ\d{8,10}` |
| PHONE | TEL | Czech phone patterns (+420, 9-digit) |
| EMAIL | EMAIL | Standard email regex |
| PASSPORT | PAS | Passport number patterns |
| ID_CARD | OP | Czech ID card patterns |
| DRIVER_LICENSE | RP | Driver license patterns |
| LICENSE_PLATE | SPZ | Czech plate patterns (`\d[A-Z]\d \d{4}`) |
| VIN | VIN | 17-character VIN |
| IP | IP | IPv4 addresses |
| INSURANCE_ID | POJISTENEC | Health insurance numbers |
| USERNAME | USERNAME | Login/username patterns |
| PASSWORD | HESLO | Password patterns |
| API_KEY | API_KEY | API key/token patterns |
| SECRET | SECRET | Secret/private key patterns |
| SSH_KEY | SSH_KEY | SSH key patterns |
| HOST | HOST | Hostname patterns |
| RFID | RFID | RFID/badge numbers |
| LINKEDIN | LINKEDIN | LinkedIn profile URLs |
| FACEBOOK | FACEBOOK | Facebook profile URLs |
| INSTAGRAM | INSTAGRAM | Instagram handles |
| SKYPE | SKYPE | Skype IDs |

### Czech Person Name Detection

This is the most complex part of the engine. It handles:

1. **Pattern-based detection** (`_replace_remaining_people`):
   - Full name: `Ing. Jan Novák` (title + first + last)
   - Role + name: `nájemce Jan Novák` (legal role prefix)
   - Standalone surname after known context
   - Standalone first name after known context
   - Robust ordering and overlap resolution between 4-word, 3-word and 2-word patterns to avoid corrupting tags when names are separated by large whitespace.

2. **Morphological inference** - Czech names are declined through 7 grammatical cases:
   - `Jana` could be nominative (female name) OR genitive of `Jan` (male)
   - `Nováka` is genitive of `Novák`
   - `Novákové` is genitive of `Nováková`

3. **Key inference functions:**
   - `_male_genitive_to_nominative(obs)` - Converts observed form to male nominative
   - `infer_first_name_nominative(obs)` - Infers nominative for first names
   - `infer_surname_nominative(obs)` - Infers nominative for surnames (supports 7 cases, vocative for -a stems, double-suffix detection, 30+ masculine -a stem families)
   - `variants_for_first(first)` / `variants_for_surname(surname)` - Generate all declension variants (7 cases + possessive adjectives + plural forms)

4. **Deduplication** (`_deduplicate_persons`):
   - Phase 1: Exact match (same first+last, different tag)
   - Phase 2: Surname-only match (one has first name, other doesn't)
   - Phase 3: Cross-gender match (Novák ↔ Nováková if same-person context)
   - Returns `tag_remap` dict for document-wide tag replacement

5. **Standalone first-name post-pass** (`_postpass_standalone_firstnames`):
   - Runs AFTER dedup/remap, BEFORE document save
   - For each detected person, extracts their first name and generates Czech case variants via `variants_for_first()`
   - Scans the entire document for these variants **outside** existing `[[...]]` tags
   - Safety measures:
     - Short names (< 4 chars: Jan, Eva, Ivo) only replaced in safe contexts (after `Pan/Paní`, academic titles like `Ing./Mgr./MUDr.`, or in signature blocks like `S pozdravem, ...`)
     - Longer names (4+ chars: Jakub, Barbora, Petra) replaced broadly
     - Blacklist of common Czech words that collide with name forms (`nová`, `město`, `stav`, `server`, `svědci`, etc.)
     - Never replaces inside existing `[[...]]` tags
   - Typical impact: catches standalone first names across 236 test contracts

6. **Orphan surname absorption after person tags** (`_postpass_orphan_surname_after_tag`):
   - Handles cases where a **multi-word first name** (e.g. `Mai Linh Nguyenová`) is partially anonymized and the surname fragment remains right after a `[[PERSON_N]]` tag.
   - Pattern: `[[PERSON_N]] Surname` → `[[PERSON_N]]`, applied only when:
     - Surname matches any known surname variant of an already-detected person, **or**
     - Surname matches a robust Czech surname suffix heuristic (`-ová`, `-ové`, `-ovou`, `-ský`, `-ská`, etc.).
   - Also handles quoted nicknames between tag and surname: `[[PERSON_N]] „Luky" Kříž` → `[[PERSON_N]]`
   - Runs on the fully anonymized document (paragraphs + tables) after person deduplication and tag remap.

7. **Maiden name post-pass** (`_postpass_maiden_names`):
   - Catches maiden name patterns that survive initial person detection:
     - `(rozená Nováková)`, `(roz. Dvořáková)`, `, rozená Krajíčková`
   - Regex: `(?:\(|,\s*)(rozen[áéou]|roz\.)\s+([A-Z][a-z]+)(\))?`
   - Maps the maiden surname to the correct PERSON tag or creates a new one.

8. **Titled standalone names post-pass** (`_postpass_titled_standalone_names`):
   - Anonymizes standalone names with professional titles that were missed by main detection:
     - `JUDr. Novák`, `MUDr. Dvořáková`, `Ing. Procházka`
   - Supported titles: JUDr, MUDr, Mgr, Ing, Bc, PhDr, RNDr, doc, prof, Ph.D
   - Only replaces if the surname matches a known person from the entity map.

9. **Company person names post-pass** (`_postpass_company_person_names`):
   - Anonymizes surnames within company names that constitute GDPR-relevant PII:
     - `Horák & Partners s.r.o.` → `[[PERSON_N]] & Partners s.r.o.`
     - `advokátní kancelář Říha & Partners` → `advokátní kancelář [[PERSON_N]] & Partners`
   - Matches known surnames from the entity map against company name patterns.
   - Company suffixes: `& Partners`, `s.r.o.`, `a.s.`, `Consulting`, `Advisory`, `Legal`, `Law`, `Group`, etc.

10. **Birth ID as variable symbol post-pass** (`_postpass_birth_id_as_var_symbol`):
    - Detects birth IDs used as variable symbols in digit-only form (without the slash):
      - `variabilní symbol: 6005301111` where `600530/1111` is a known BIRTH_ID
    - Compares digit-only forms against known birth IDs and replaces with the corresponding `[[BIRTH_ID_N]]` tag.

11. **Address proximity merge** (`_address_proximity_merge` inside `anonymize_entities`):
   - Detects independent address components regardless of word order:
     - **PSČ**: `\d{3}\s?\d{2}` (with optional "PSČ" prefix)
     - **Street + number**: `(prefix)? Word(+Word)*(+RomanNumeral)? Number(/Number)?`
     - **City**: whitelist of **80+ Czech cities** (Praha, Brno, Ostrava, Plzeň, Olomouc, Liberec, Hradec Králové, České Budějovice, Karlovy Vary, Zlín, Pardubice, Jihlava, Děčín, Přerov, Chrudim, Tábor, Svitavy, Kroměříž, Znojmo, Třebíč, Prostějov, Kutná Hora, Havlíčkův Brod, Kolín, Benešov, Písek, Louny, Strakonice, Kladno, Mladá Boleslav, and many more)
     - **Country**: `Česká republika`, `Slovenská republika`
   - Groups components within MAX_DIST=80 characters, breaking on non-ADDRESS tags (barriers)
   - Requires at least one "strong" component (PSČ, street+number, or existing ADDRESS tag)
   - Normalizes PSČ (removes "PSČ" prefix, formats `14028` → `140 28`) and deduplicates parts

8. **Address district/country absorption** (inside `anonymize_entities`):
   - Post-pass absorbs `", Česká republika"` after `[[ADDRESS_N]]` tags
   - Post-pass absorbs `"- DistrictName"` after `[[ADDRESS_N]]` tags
   - Must run AFTER standalone city detection so the tag exists first

9. **ADDRESS deduplication** (`_deduplicate_addresses`, runs before document save):
   - Sorts all ADDRESS entries by canonical value length
   - If a shorter entry is a substring of a longer one → merges them (keeps the longer one)
   - Remaps all tags in the document (paragraphs + tables)
   - Eliminates redundant entries like standalone `"Svitavy"` when `"Svitavy, Česká republika, náměstí Míru 32/1, 568 02"` already exists
   - Combined with substring matching in `_get_or_create_label`, prevents most duplicates at creation time

14. **Masculine -a surname inference** (`infer_surname_nominative` enhancements):
    - Czech masculine surnames ending in `-a` (Fiala, Svoboda, Skála, Malina, Neruda, etc.) decline like feminine nouns but require masculine nominative recovery.
    - The function maintains coordinated stem sets across all case handlers:
      - `masculine_a_stems` (instrumental `-ou` → `-a`): 45+ stems including `fial`, `svobod`, `skál`, `malin`, `nerud`, `procházk`, etc.
      - `surname_stems_needing_a` (dative `-ovi`, genitive plural `-ů`, final control): synchronized with `masculine_a_stems`
      - `known_a_surnames` (accusative `-u` → `-a`): covers the same stems
      - `protected_a_surnames` (genitive `-y` → `-a`): includes full forms like `fiala`, `janota`, `neruda`, etc.
    - **Vocative handler**: New rule converts vocative `-o` → nominative `-a` (e.g., `Fialo` → `Fiala`, `Svobodo` → `Svoboda`) using both the stem set and `common_surnames_a` / `animal_plant_surnames` lookups.
    - **Double-suffix detection**: Priority 0 rule in the `-ou` handler detects doubled `-ová` suffixes (e.g., `Bartůňkováovou` → correctly strips to `Bartůňková`).
    - Without these coordinated sets, masculine -a surnames create **duplicate PERSON entities** (e.g., "Dalibor Fiala" + "Dalibor Fialý" + "Dalibor Fialo") because the nominative inference returns incorrect forms that don't match the existing person index key.

15. **Non-person blacklists** (sector-specific):
   - `critical_blacklist` in person detection: prevents roles/institutions from being tagged as PERSON
   - `role_blacklist_words` in map cleanup: removes false PERSON entries post-hoc
   - Institution/brand coverage is **data-driven**:
     - Terms are maintained in `institutions_blacklist.json` (banks, insurers, universities, hospitals, large retailers, gov. bodies) and loaded once at module import.
     - `anon72.py` merges this set into `critical_blacklist`/`role_words`; `run_anonymize_tests.py` merges it into `non_person_tokens`, so both engine and validators share the same view of “non-person” tokens.
   - Sector coverage spans 6 target domains:
     - **Legal**: advokát, advokátní, notář, soud, soudce, soudkyně
     - **Healthcare**: nemocnice, klinika, ordinace, ambulance, oddělení, pracoviště
     - **Public administration**: ministerstvo, magistrát, obec, město, úřad
     - **HR**: recruiter, recruitment, talent, personální, personalista, peopleops
     - **Education**: gymnázium, univerzita, fakulta, škola, školství
     - **Financial**: banka, spořitelna, pojišťovna, bankovní, finanční

16. **Name library** (`cz_names.v1.json`):
    - `firstnames.M` - Male first names with diacritics
    - `firstnames.F` - Female first names with diacritics
    - `firstnames_no_diac` - Names without diacritics (e.g., "Jan" without háček)
    - Used to disambiguate gender of observed name forms

17. **International diacritics support**:
    - All person-related regex character classes were extended to include Central-European and selected Western diacritics (e.g. `Ä, Ö, Ü, Ą, Ę, Ł, Ń, Ś, Ź, Ż, Ő, Ű, Ñ` and their lowercase variants).
    - This prevents leaks for foreign surnames like `"Müllerová"` or mixed-origin full names while keeping the false-positive rate low thanks to the existing blacklist logic.

### Output Files

For input `smlouva.docx`, the anonymizer produces:

| File | Content |
|------|---------|
| `smlouva_anon.docx` | Anonymized document with `[[OSOBA_1]]`, `[[ADRESA_1]]` tags |
| `smlouva_map.json` | Machine-readable map: `{entity_type: {canonical_value: [variants]}}` |
| `smlouva_map.txt` | Human-readable replacement table |
| `smlouva_report.pdf` | PDF certificate with statistics, entity counts, SHA-256 hash |

---

## 5. PDF/Image Conversion (`pdf2docx_cli.py`)

### Detection Strategy

```
Input file
  │
  ├── Image file (.png/.jpg/.tiff/...)
  │     └── Direct OCR via Tesseract → DOCX
  │
  └── PDF file
        ├── Try pdf2docx (native text extraction)
        │     └── Check text length > threshold
        ├── If low text → scanned PDF detected
        │     ├── Poppler pdftoppm → convert pages to images
        │     └── Tesseract OCR each page → combine to DOCX
        └── Return DOCX
```

### External Dependencies (must be installed on build machine)

- **Tesseract OCR** - For scanned document recognition. Auto-detected on common Windows paths.
- **Poppler** (`pdftoppm`) - For rendering PDF pages to images before OCR.
- **pdf2docx** Python package - For native PDF text extraction.

---

## 6. License System

### Flow

```
App start → checkLicense()
  ├── Find license.lic (exe dir → AppData → unpacked)
  ├── Run validate_license_standalone.exe license.lic
  │     ├── Read license.lic (base64 JSON)
  │     ├── Compute HW fingerprint: SHA256(CPU_ID:MAC:DISK_SERIAL)[:16]
  │     ├── Verify HMAC-SHA256 signature with MASTER_SECRET
  │     ├── Check expiry date
  │     └── Return JSON: {valid, message, hw_id, ...}
  ├── If valid → copy to AppData (survives reinstall)
  └── If invalid → show dialog with HW ID for activation
```

### HW Fingerprint

Hardware ID is a deterministic 16-char hex string derived from:
- CPU ProcessorId (via WMIC or PowerShell Get-CimInstance)
- MAC address (via `uuid.getnode()`)
- Primary disk serial number

Format: `XXXX-XXXX-XXXX-XXXX`

### License File Format

Base64-encoded JSON containing: customer name, HW ID, expiry date, features, HMAC signature.

---

## 7. Build Pipeline

### Prerequisites

```bash
# Node.js + npm (for Electron)
npm install

# Python 3.11+ with required packages
pip install nuitka python-docx fpdf2 fontTools pdf2docx watchdog pytesseract Pillow

# Nuitka will auto-download MinGW C++ compiler on first run
```

### Step 1: Compile Python → Native Executables

```bash
python build/build_with_nuitka.py
```

This runs in 4 phases:

**Phase 1: Compile scripts to standalone .exe (Nuitka `--onefile`)**

Each script becomes a single .exe file with all dependencies bundled:

| Script | Extra Flags | Notes |
|--------|------------|-------|
| `validate_license_standalone.py` | - | Contains MASTER_SECRET |
| `anonymize_cli.py` | `--include-package=fpdf --include-package=fontTools` | **Capital T in fontTools is critical!** |
| `deanonymizator_lokal.py` | - | |
| `pdf2docx_cli.py` | - | |
| `skryi_watcher.py` | - | |
| `deanon_watcher.py` | - | |
| `pdf2docx_watcher.py` | - | |

**Phase 2: Compile anon72.py as .pyd module**

```bash
nuitka --module anon72.py
```

Produces `anon72.cp311-win_amd64.pyd` (platform-specific name) + copies as `anon72.pyd` (for Nuitka onefile compatibility).

**Phase 3: Copy data files** - `cz_names.v1.json`, `fonts/`

**Phase 4: Auto-copy to project root** - All .exe, .pyd files copied to project root for `electron-builder` packaging.

### Step 2: Package Electron App

```bash
npm run dist
```

Uses `electron-builder` with NSIS target (Windows installer).

**Critical `package.json` build configuration:**

```json
{
  "files": [
    "main.js", "index.html", "package.json", "EULA.txt",
    "assets/**/*", "fonts/**/*",
    "*.exe", "*.pyd", "cz_names.v1.json",
    "!**/*.py",           // EXCLUDES all Python source files
    "!**/dist/**",        // EXCLUDES build output
    "!**/node_modules/**" // EXCLUDES node_modules
  ],
  "asarUnpack": [
    "**/*.exe", "**/*.pyd",     // Executables must be outside asar
    "cz_names.v1.json",         // Data file accessed by .exe
    "fonts/**/*", "assets/**/*" // Resources
  ]
}
```

**Why `asarUnpack`?** Electron packs files into an `app.asar` archive. Compiled .exe files cannot run from inside an asar, so they must be extracted to `app.asar.unpacked/`.

### Step 3: Output

```
dist/
  └── SKRYI-Setup-3.0.0.exe    # NSIS installer (~80-150 MB)
```

Installed to: `C:\Program Files\SKRYI Document Suite\`

```
resources/
  ├── app.asar                  # Packed: main.js, index.html, package.json
  └── app.asar.unpacked/        # Unpacked:
        ├── anonymize_cli.exe
        ├── deanonymizator_lokal.exe
        ├── pdf2docx_cli.exe
        ├── validate_license_standalone.exe
        ├── skryi_watcher.exe
        ├── deanon_watcher.exe
        ├── pdf2docx_watcher.exe
        ├── anon72.pyd
        ├── anon72.cp311-win_amd64.pyd
        ├── cz_names.v1.json
        ├── fonts/
        │     ├── DejaVuSans.ttf
        │     └── DejaVuSans-Bold.ttf
        └── assets/
              └── logo.png
```

---

## 8. Development vs Production

| Aspect | Development | Production |
|--------|------------|------------|
| Run command | `npm run dev` | Installed via NSIS |
| Python scripts | Run as `.py` via interpreter | Run as `.exe` (Nuitka compiled) |
| anon72 module | Imported as `.py` | Imported as `.pyd` |
| Script resolution | `__dirname/*.py` | `app.asar.unpacked/*.exe` |
| License check | Skipped if validator not found | Required |
| Stats file | `__dirname/skryi_stats.json` | `%AppData%/SKRYI Document Suite/skryi_stats.json` |
| License file | `__dirname/license.lic` | Searched in exe dir, AppData, unpacked |
| Debug mode | `NIX_DEBUG=1` → DevTools + verbose logs | Off |
| Python verbose | `NIX_VERBOSE=1` → `--verbose` flag | Off |

---

## 9. SKRYI Folder Structure (User's Documents)

Created automatically when the "Folder Mode" tab is activated:

```
Documents/
  └── SKRYI/
        ├── 01_ANONYMIZACE/
        │     ├── IN/     ← Drop .docx files here
        │     └── OUT/    ← Anonymized files appear here
        ├── 02_DEANONYMIZACE/
        │     ├── IN/     ← Drop _anon.docx + _map.json here
        │     └── OUT/    ← Deanonymized files appear here
        ├── 03_KONVERZE_PDF/
        │     ├── IN/     ← Drop PDF/images here
        │     └── OUT/    ← Converted .docx files appear here
        ├── ERROR/        ← Failed files moved here
        └── LOGS/         ← Daily log files (skryi_YYYYMMDD.log)
```

---

## 10. UI Structure (`index.html`)

Single-file SPA with 4 tabs:

### CSS Architecture

CSS custom properties (variables) define the Chrome/Silver dark theme:

```css
:root {
  --bg0: #181B24;       /* Deepest background */
  --panel0: #23262F;    /* Card/panel background */
  --accent: #6AAFE8;    /* Primary accent (blue) */
  --ok: #4CD89D;        /* Success green */
  --warn: #F0B040;      /* Warning amber */
  --bad: #F06060;        /* Error red */
}
```

### Tab Layout

| Tab | Content |
|-----|---------|
| **Anonymizace** | File picker → Run anonymization → Show results + open output/map |
| **Deanonymizace** | Pick anon file + map file → Run deanonymization → Show output |
| **PDF → DOCX** | Pick PDF/image → Run conversion (native or OCR) → Show output |
| **Složky** | Folder mode: view SKRYI folder structure, start/stop watchers, autostart toggle |

### Sidebar

- Application logo (96x96)
- Tab navigation buttons
- Statistics display (total anonymized/deanonymized/converted)
- License info (licensee name, expiry, HW ID)
- Version display

---

## 11. Known Limitations and Gotchas

### Build

1. **`fontTools` capitalization** - Nuitka `--include-package=fontTools` requires exact Python import name (capital T). The pip package name is lowercase `fonttools` but the import is `fontTools`. Using wrong case silently fails the entire anonymize_cli.exe compilation.

2. **`!**/*.py` in package.json** - All Python source files are excluded from the Electron build. Only compiled .exe and .pyd files ship. This means development mode needs Python installed, production does not.

3. **Nuitka onefile temp extraction** - When a `--onefile` exe runs, it extracts to a temp folder. The `anon72.pyd` module needs to be findable from the ORIGINAL exe location, not the temp folder. `anonymize_cli.py` handles this with `sys.argv[0]` path resolution.

### Anonymization

4. **Processing order matters** - Entities must be detected before persons. If phone detection runs after person detection, phone numbers embedded in addresses might be missed. The order in `anonymize_docx` is: `anonymize_entities()` → `_apply_known_people()` → `_replace_remaining_people()`.

5. **Czech morphology is approximated** - The system uses rule-based suffix stripping for Czech declension (7 cases × 2 numbers). This covers ~90% of cases but cannot handle irregular forms or context-dependent ambiguity (e.g., "Jana" = female name or male genitive).

6. **Name library gaps** - `cz_names.v1.json` must include both `firstnames` (with diacritics) and `firstnames_no_diac` (without) sections. Missing the no-diac section causes names like "Jan" (which lacks háček) to not be recognized, leading to incorrect gender inference.

7. **Dedup tag remap** - After person deduplication, old tags must be replaced throughout the entire document. The `tag_remap` dict is applied to all paragraphs and table cells after dedup runs.

8. **Standalone first-name post-pass ordering** - `_postpass_standalone_firstnames` must run AFTER dedup (so tag_remap is applied first) and BEFORE document save. Short names (< 4 chars) are only replaced in safe contexts to avoid false positives with common Czech words.

9. **Orphan surname post-pass ordering** - `_postpass_orphan_surname_after_tag` must run after all person detection and tag remapping. It only operates on patterns of the form `[[PERSON_N]] Surname` and uses both known surname variants and suffix heuristics; this is what fixes cases like `"Mai Linh Nguyenová"` where only the first-name chunk was originally tagged.

10. **District absorption ordering** - The `district_after_addr_re` post-pass must run at the END of `anonymize_entities`, after all city detection patterns (`city_pattern`, `city_in_place`). If placed earlier, the address tag for "Praha 3" doesn't exist yet and the district name "Vinohrady" won't be absorbed.

11. **Address proximity merge barriers** - The proximity merge must break groups when non-ADDRESS tags (`[[ICO_X]]`, `[[PERSON_X]]`) appear between address components. Without barriers, unrelated entities can be incorrectly merged into a single ADDRESS tag.

12. **ADDRESS deduplication ordering** - `_deduplicate_addresses()` must run AFTER all post-processing (person dedup, standalone firstnames, orphan surnames) but BEFORE document save and map creation. This ensures all ADDRESS tags are finalized before the merge pass.

13. **Non-person false positives** - Common Czech words like `Stav`, `Banka`, `Zpracovatel`, `Nové`, `Poplatek`, `Specifikace`, `Běžný` can be mistakenly detected as person names when they appear in "FirstName LastName" position. The `critical_blacklist` and `role_blacklist_words` sets prevent this but must be kept up-to-date for each target sector (legal, healthcare, HR, education, finance, public admin). Multi-word city names (Kutná Hora, Havlíčkův Brod, Přemysla Otakara, etc.) are also blacklisted to prevent detection as person names.

**13a. Masculine -a surname stem synchronization** - The `infer_surname_nominative` function has **6 separate stem sets** that must be kept in sync (`masculine_a_stems`, `surname_stems_needing_a` in 3 locations, `known_a_surnames`, `protected_a_surnames`, `_vocative_a_stems`). Adding a new masculine -a surname (e.g., "Fiala") requires adding its stem to ALL of these sets. Failure to do so causes the person to be split into multiple entities with incorrect nominative forms.

### Platform

14. **Windows-only in production** - WMIC/PowerShell calls for HW fingerprint, registry for autostart, NSIS installer. Development works cross-platform.

15. **Antivirus false positives** - Nuitka-compiled .exe files are sometimes flagged by antivirus software. The license validator has a Python fallback if the .exe fails silently.

### Testing and validation (v3.3.0)

To validate the correctness of the engine after all changes (6 post-passes, masculine -a surname inference, expanded blacklists, extended diacritics, batch error handling), a comprehensive audit pipeline was used:

- **Full batch regression**: Batch anonymization of **236 synthetic contracts** (150 GDPR-specific tests, 30 loan variants, 15 high-complexity stress tests, legacy documents). **0 errors, 0 warnings**.
- **Deep automated verification**: Script checking all 236 anonymized DOCX + JSON maps for NAME-LEAK (known names outside tags), ORPHAN-DOC/MAP (tag-map mismatches), MAP-DUP (duplicate persons). Result: **236/236 CLEAN**.
- **Address variant stress-test**: 30 loan contract variants with varied address formats/word orders. **Zero address leaks, zero false person detections, zero duplicate ADDRESS entries**.
- **Masculine -a surname regression**: Contracts with "Dalibor Fiala", "Arnošt Malina" etc. verified across all 7 cases + vocative. Previously created 3 PERSON entities for one person; after fix, all forms correctly unified.
- **Production readiness**: 0 DeprecationWarnings, debug output gated behind `--verbose`, batch mode handles OSError/PermissionError with timestamped fallback files.
- **Audit scripts** (in `test_data/`):
  - `_full_addr_audit.py` – dumps all ADDRESS entries from all maps, categorizes OK vs SUSPECT for manual review.
  - `_full_person_audit.py` – dumps all PERSON entries from all maps, categorizes OK vs SUSPECT (pattern: typical Czech name 2+ words, no digits, no s.r.o./a.s.).
- **Address prefix stripping**: Values like "adrese Růžová 847/23" or "bytem Dlouhá 15" are normalized in the map to "Růžová 847/23" and "Dlouhá 15" by stripping prefixes "adrese", "bytem" etc. in `_get_or_create_label` for ADDRESS type.

---

## 12. Data Flow Diagrams

### Anonymization Data Flow

```
User selects smlouva.docx
         │
         ▼
    index.html
    ipcRenderer.invoke('anonymize-document', path)
         │
         ▼
    main.js
    resolveScript('anonymize_cli.py') → anonymize_cli.exe
    spawn(anonymize_cli.exe, [--input, --output, --map, --map_txt, --report])
         │
         ▼
    anonymize_cli.exe
    ├── load cz_names.v1.json → CZECH_FIRST_NAMES set
    ├── import anon72 (from anon72.pyd)
    ├── Anonymizer().anonymize_docx(...)
    │     ├── Load DOCX (python-docx)
    │     ├── For each paragraph:
    │     │     ├── anonymize_entities(text)     → [[ADRESA_1]], [[TEL_1]], [[RC_1]], ...
    │     │     ├── _apply_known_people(text)    → Replace known person variants
    │     │     └── _replace_remaining_people()  → [[OSOBA_1]], [[OSOBA_2]], ...
    │     ├── _fix_canonical_names_not_in_document()
    │     ├── _fix_gender_mismatches()
    │     ├── _normalize_canonicals_to_nominative()
    │     ├── _deduplicate_persons() → tag_remap
    │     ├── Apply tag_remap to all text
    │     ├── _postpass_standalone_firstnames()       → "Barbora", "Jakubovi"
    │     ├── _postpass_orphan_surname_after_tag()    → "[[PERSON_N]] Nguyenová"
    │     ├── _postpass_maiden_names()                → "(rozená Nováková)"
    │     ├── _postpass_titled_standalone_names()     → "JUDr. Novák"
    │     ├── _postpass_company_person_names()        → "Horák & Partners s.r.o."
    │     ├── _postpass_birth_id_as_var_symbol()      → "var.symbol 6005301111"
    │     ├── _deduplicate_addresses()
    │     ├── _deduplicate_phones()
    │     ├── _remove_phone_idcard_overlap()
    │     ├── Save _anon.docx
    │     └── _create_maps() → _map.json, _map.txt, _report.pdf
    └── Print JSON result to stdout
         │
         ▼
    main.js
    parseJsonFromOutput(stdout) → {success, output, map_json, map_txt, report_pdf}
    logStat("anonymize", {persons: N})
         │
         ▼
    index.html
    Display results, enable "Open file" / "Open map" buttons
```

### Deanonymization Data Flow

```
User selects smlouva_anon.docx + smlouva_map.json
         │
         ▼
    main.js → spawn deanonymizator_lokal.exe
    [--input anon.docx, --map map.json, --output _deanon.docx]
         │
         ▼
    deanonymizator_lokal.exe
    ├── Load map.json → {[[OSOBA_1]]: "Jan Novák", [[ADRESA_1]]: "Hlavní 5, Praha", ...}
    ├── Load _anon.docx
    ├── For each paragraph: replace all [[TAG_N]] → original values
    │     └── Uses infer_first_name_nominative() for correct case restoration
    └── Save _deanon.docx
```

---

## 13. Quick Reference: Common Tasks

### Add a new entity type

1. Add regex pattern in `anon72.py` (before the `Anonymizer` class, ~line 1400)
2. Add `replace_xxx` function inside `anonymize_entities()` method
3. Add the type to `_ENTITY_CATEGORY_MAP` (line ~5634)
4. Test with a sample document

### Add a new IPC handler

1. Add `ipcMain.handle("channel-name", async (evt, ...args) => {...})` in `main.js`
2. Call from renderer: `await ipcRenderer.invoke("channel-name", ...args)` in `index.html`

### Debug anonymization issues

```bash
# Run in development mode with verbose logging
NIX_DEBUG=1 NIX_VERBOSE=1 npm run dev
```

Or run the CLI directly:
```bash
python anonymize_cli.py --input test.docx --output test_anon.docx --map test_map.json --map_txt test_map.txt --verbose
```

### Build a new installer

```bash
# 1. Compile Python to .exe
python build/build_with_nuitka.py

# 2. Verify all .exe files exist in project root
ls -la *.exe *.pyd

# 3. Package Electron app
npm run dist

# 4. Installer at dist/SKRYI-Setup-3.0.0.exe
```
