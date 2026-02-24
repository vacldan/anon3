# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a Python-based offline GDPR/PII document anonymizer ("Anonymizátor") for Czech-language `.docx` legal documents. It detects and replaces personally identifiable information with labeled tags like `[[PERSON_1]]`, `[[ADDRESS_1]]`, etc.

### Tech stack

- **Python 3** (single-script application, no framework)
- **python-docx** — the only external dependency (for reading/writing `.docx` files)
- **No database, no external APIs, no Docker** — fully offline

### Running the application

Single file:
```
python3 "anon7.2 - s padama.py" smlouva0.docx
```

Batch mode (all `.docx` in a directory):
```
python3 "anon7.2 - s padama.py" --batch .
```

Outputs per file: `<basename>_anon.docx`, `<basename>_map.json`, `<basename>_map.txt`.

### Important notes

- The main script filename contains spaces: `anon7.2 - s padama.py`. Always quote it when running from the shell.
- The script requires `cz_names.v1.json` to be in the same directory (or working directory) — it is already in the repo root.
- Batch mode can be slow (~5s per document due to heavy regex processing). For quick verification, run on a single file like `smlouva0.docx`.
- There are no automated tests (pytest, unittest) in the repo despite the README mentioning them. No lint configuration exists either.
- `Claude_code_6.py` is an older version of the anonymizer — the current version is `anon7.2 - s padama.py`.
