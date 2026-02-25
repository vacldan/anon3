# SKRYI Document Suite - Technical Documentation

> **Version:** 3.0.0
> **Last Updated:** 2026-02-25
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
| `anon72.py` | ~5990 | Core anonymization engine. `Anonymizer` class with regex-based NER, Czech morphological inference, GDPR entity detection. |
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
  │     ├── _apply_known_people(text)        # Replace known person variants
  │     └── _replace_remaining_people(text)  # Detect new persons via NER patterns
  │
  ├── 3. Post-processing:
  │     ├── _fix_canonical_names_not_in_document()  # Remove phantom inferences
  │     ├── _fix_gender_mismatches()                # Fix cross-gender pairs
  │     └── _deduplicate_persons()                  # Merge duplicate persons
  │           └── Returns tag_remap dict → applied to all paragraphs/tables
  │
  ├── 4. Save anonymized document
  └── 5. _create_maps() → JSON map, TXT map, PDF report
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
| ADDRESS | ADRESA | Czech address prefixes + street/city patterns |
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

2. **Morphological inference** - Czech names are declined through 7 grammatical cases:
   - `Jana` could be nominative (female name) OR genitive of `Jan` (male)
   - `Nováka` is genitive of `Novák`
   - `Novákové` is genitive of `Nováková`

3. **Key inference functions:**
   - `_male_genitive_to_nominative(obs)` - Converts observed form to male nominative
   - `infer_first_name_nominative(obs)` - Infers nominative for first names
   - `infer_surname_nominative(obs)` - Infers nominative for surnames
   - `variants_for_first(first)` / `variants_for_surname(surname)` - Generate all declension variants

4. **Deduplication** (`_deduplicate_persons`):
   - Phase 1: Exact match (same first+last, different tag)
   - Phase 2: Surname-only match (one has first name, other doesn't)
   - Phase 3: Cross-gender match (Novák ↔ Nováková if same-person context)
   - Returns `tag_remap` dict for document-wide tag replacement

5. **Name library** (`cz_names.v1.json`):
   - `firstnames.M` - Male first names with diacritics
   - `firstnames.F` - Female first names with diacritics
   - `firstnames_no_diac` - Names without diacritics (e.g., "Jan" without háček)
   - Used to disambiguate gender of observed name forms

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

### Platform

8. **Windows-only in production** - WMIC/PowerShell calls for HW fingerprint, registry for autostart, NSIS installer. Development works cross-platform.

9. **Antivirus false positives** - Nuitka-compiled .exe files are sometimes flagged by antivirus software. The license validator has a Python fallback if the .exe fails silently.

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
    │     ├── _deduplicate_persons() → tag_remap
    │     ├── Apply tag_remap to all text
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
