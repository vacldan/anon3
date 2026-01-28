# Deanonymization Improvements

## Summary

Replaced the simple deanonymizer with a production-ready version that includes Czech name normalization while removing excessive debug output.

## Changes

### 1. New Production Deanonymizer (`deanonymizator.py`)

**New File:** Production-ready version with Czech name normalization
**Replaces Usage Of:** Debug version `deanonymizator_lokal.py` in production

**Key Features:**
- ✅ **Czech Name Normalization** - Converts names from all grammatical cases to nominative (1st case)
  - Example: "Martina" (genitive) → "Martin" (nominative)
  - Example: "Novákovi" (dative) → "Novák" (nominative)
  - Example: "Ivanem" (instrumental) → "Ivan" (nominative)

- ✅ **TXT Map Support** - Uses base values from TXT maps for consistent person names

- ✅ **Clean Production Output** - Minimal console output by default
  - Essential messages only
  - Optional verbose mode with `--verbose` flag

- ✅ **File Locking Handling** - Saves to temp location if output file is locked

- ✅ **Flexible CLI** - Multiple argument formats supported:
  ```bash
  # Auto-detect from input file
  python deanonymizator.py smlouva_anon.docx

  # Positional arguments
  python deanonymizator.py input.docx map.json output.docx

  # Named arguments
  python deanonymizator.py --input input.docx --map map.json --output output.docx --verbose
  ```

### 2. Updated Electron Integration (`main.js`)

**Changed:** Line 428
```javascript
// Before:
const cli = resolvePy("deanonymizator_lokal.py");

// After:
const cli = resolvePy("deanonymizator.py");
```

**Effect:** Application now uses production version instead of debug version

### 3. Preserved Debug Version

**Kept:** `deanonymizator_lokal.py` - Full debug version available for troubleshooting

## Name Normalization Logic

The production version includes comprehensive Czech language support:

### First Names
- Genitive/Accusative: -a → remove (Ivana → Ivan)
- Genitive: -e → remove (Martine → Martin)
- Dative: -u → remove (Martinu → Martin)
- Instrumental: -em → remove (Ivanem → Ivan)
- Female genitive: -y → -a (Pavlíny → Pavlína)
- Female instrumental: -ou → -a (Pavlínou → Pavlína)

### Surnames
- Female genitive/dative: -é → -á (Pokorné → Pokorná)
- Instrumental: -ou → -á or -ý (Vránou → Vráná/Vráný)
- Male genitive: -a → remove (Nováka → Novák)
- Dative: -ovi → remove with smart -ek detection (Havlíčkovi → Havlíček)
- Instrumental: -em → remove with context (Novákem → Novák)

### Protected Names
- Built-in database of Czech names that should not be modified
- Loads from `cz_names.v1.json` if available
- Fallback to heuristic rules if library not found

## Technical Improvements

### Output Comparison

**Before (deanonymizator_lokal.py):**
```
===============================================================================
DEANONYMIZÁTOR - LOKÁLNÍ DEBUG VERZE
===============================================================================
Start: 2026-01-28 10:30:45

>>> Načítám knihovnu českých jmen...
✓ Knihovna jmen načtena: 5432 jmen

>>> INFORMACE O PROSTŘEDÍ:
Python verze: 3.9.13
Aktuální složka: /path/to/folder
...
[50+ lines of debug output]
```

**After (deanonymizer.py):**
```
DEANONYMIZATION COMPLETE
Output: /path/to/output.docx
```

With `--verbose` flag:
```
================================================================================
DEANONYMIZATION
================================================================================
Input:  /path/to/input.docx
Map:    /path/to/map.json
Output: /path/to/output.docx

Loading JSON: /path/to/map.json
Found 45 tags in mapping
Loading document: /path/to/input.docx
Paragraphs: 120, Tables: 3
Applying replacements...
Changed 38 paragraphs
Saving to: /path/to/output.docx
Saved successfully: 245,678 bytes
================================================================================
DEANONYMIZATION COMPLETE
================================================================================
Changed paragraphs: 38
Total tags in map: 45
Output file: /path/to/output.docx
================================================================================
```

## Benefits

1. **Better User Experience** - Clean output in Electron app UI
2. **Maintains Functionality** - All critical features preserved
3. **Better Debugging** - Verbose mode available when needed
4. **Correct Czech Grammar** - Names appear in proper nominative case
5. **Professional Output** - Production-ready code quality

## Files Changed

- `deanonymizator.py` - New production version with name normalization (630 lines)
- `main.js` - Updated to use production deanonymizator (line 428)
- `deanonymizator_lokal.py` - Preserved for debugging (no changes)
- `DEANONYMIZATION_IMPROVEMENTS.md` - Documentation (this file)

## Testing

The new version should be tested with:
1. Simple Czech documents with person names
2. Documents with names in various grammatical cases
3. Documents with tables
4. Large documents (100+ pages)
5. Files with locked output (Word open)

## Compatibility

- ✅ Same CLI interface as debug version
- ✅ Same input/output format
- ✅ Same JSON map structure
- ✅ Works with both JSON and TXT maps
- ✅ Cross-platform (Windows, Linux, macOS)

---

**Branch:** `claude/fix-deanonymization-local-TkTHs`
**Status:** Ready for testing and merge
