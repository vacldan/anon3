# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a Python-based offline GDPR/PII document anonymizer ("SKRYI / Anonymizátor") for Czech-language `.docx` legal documents. It detects and replaces personally identifiable information with labeled tags like `[[PERSON_1]]`, `[[ADDRESS_1]]`, etc. The project also includes an Electron desktop wrapper (`main.js` + `index.html`), but the core functionality is the Python anonymizer.

### Tech stack

- **Python 3** — core anonymizer (`anon72.py`) + validation (`deep_validate.py`)
- **python-docx** — the only required external Python dependency
- **Electron** (optional) — desktop UI wrapper (`main.js`, `index.html`, `package.json`)
- **No database, no external APIs, no Docker** — fully offline

### Key files

| File | Purpose |
|------|---------|
| `anon72.py` | Main anonymizer (current version) |
| `deep_validate.py` | Deep validation script (checks canonicals, leaks, phantoms, scoring) |
| `_validate_gdpr_tests.py` | Batch GDPR test validation runner |
| `_gdpr_audit.py` | GDPR audit helper |
| `cz_names.v1.json` | Czech first names dictionary (MVČR) |
| `QA_POKYNY.md` | **Unified QA doc — testing, validation, scoring matrix (MUST follow)** |
| `test_data/` | Test contracts (smlouva10–33) + anon outputs + maps |

### Running the anonymizer

Single file:
```bash
python3 anon72.py test_data/smlouva10.docx
```

Batch (example for smlouva10–33):
```bash
for n in $(seq 10 33); do python3 anon72.py "test_data/smlouva$n.docx"; done
```

Outputs per file: `<basename>_anon.docx`, `<basename>_map.json`, `<basename>_map.txt`.

### Testing and validation workflow (MANDATORY)

**See `QA_POKYNY.md` for the full specification.** Key points:

1. **After ANY change to `anon72.py`:** re-anonymize test contracts, then run `python3 deep_validate.py`
2. **Never fix just the reported case** — always run validation and fix the general pattern
3. **Which contracts to test:** wait for user instructions (do not assume a fixed range)

#### Running validation

All contracts in `test_data/`:
```bash
python3 deep_validate.py
```

Single contract:
```bash
python3 deep_validate.py test_data/smlouva10.docx
```

#### Scoring

**Full scoring matrix: see `QA_POKYNY.md`** — the authoritative reference for all quality evaluation.

Three severity tiers:
- **KRITICKÉ (−3.0 each):** plain-text PII leaks, missing map entries — must be 0 for GO
- **ZÁVAŽNÉ (−1.0 each):** wrong entity type, merged/split persons, incomplete redaction
- **DROBNÉ (−0.3/−0.5 each):** canonical form errors, blacklist words as persons, phantoms, address prefixes

**GO = score ≥ 9.0 AND 0 critical errors.** Target: average ≥ 9.0 across all contracts.

`deep_validate.py` implements a subset (focused on PERSON). For full entity audit, review against `QA_POKYNY.md`.

### Important notes

- `anon72.py` is the current main anonymizer. Older versions (`anon7.2 - s padama.py`, `Claude_code_6.py`, files in `test_data/`) are historical.
- The script requires `cz_names.v1.json` in the same directory or working directory.
- Processing time: ~2–5s per document due to heavy regex processing.
- `fpdf2` is not installed (PDF reports are skipped with a warning — this is non-critical).
- The Electron app (`npm run dev`) requires a display and is Windows-focused; the Python scripts are the primary development target.
