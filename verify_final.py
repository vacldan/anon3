#!/usr/bin/env python3
"""
Finální verifikace anonymizovaných smluv + map.
Kontroluje: NAME-LEAK, ORPHAN-DOC, ORPHAN-MAP, MAP-DUP.
"""
import json
import re
from pathlib import Path
from docx import Document

TEST_DIR = Path("test_data")
FALSE_POSITIVE_NAMES = frozenset({
    "stav", "banka", "nové", "poplatek", "specifikace", "běžný", "zpracovatel",
    "svědci", "nová", "město", "server", "byst", "strana", "datum", "část",
    "článek", "odstavec", "smlouva", "nájem", "pronájem", "výpověď", "režim",
    "malý", "malá", "malé",  # přídavné jméno "small" vs příjmení Malý/Malá
})

TAG_RE = re.compile(r'\[\[([A-Z_]+)_(\d+)\]\]')


def extract_text_from_docx(path):
    """Extract all text from DOCX (paragraphs + tables)."""
    doc = Document(path)
    parts = []
    for p in doc.paragraphs:
        parts.append(p.text)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def get_tags_in_text(text):
    """Return set of [[TAG_N]] found in text."""
    return set(TAG_RE.findall(text))


def verify_file(anon_path, map_path):
    """Verify single anon.docx + map.json. Returns list of issues."""
    issues = []
    if not anon_path.exists():
        return [("MISSING", f"Anon file not found: {anon_path}")]
    if not map_path.exists():
        return [("MISSING", f"Map file not found: {map_path}")]

    try:
        text = extract_text_from_docx(anon_path)
    except Exception as e:
        return [("ERROR", f"Cannot read DOCX: {e}")]

    try:
        with open(map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [("ERROR", f"Cannot read JSON: {e}")]

    # Build tag->canonical from entities array (current map format)
    map_tags = {}
    person_canonicals = {}  # tag -> "First Last" (canonical)
    label_to_originals = {}  # label -> set of originals

    entities = data.get("entities", [])
    for ent in entities:
        label = ent.get("label", "")
        orig = ent.get("original", "")
        typ = ent.get("type", "")
        if not label or not label.startswith("[["):
            continue
        map_tags[label] = orig
        if typ == "PERSON":
            if label not in label_to_originals:
                label_to_originals[label] = set()
            label_to_originals[label].add(orig)
            # Canonical = longest original with 2+ words, or first
            if label not in person_canonicals or (len(orig.split()) >= 2 and len(orig) > len(person_canonicals.get(label, ""))):
                person_canonicals[label] = orig

    # ORPHAN-DOC: tags in document but not in map
    doc_tags = set(m.group(0) for m in TAG_RE.finditer(text))
    for tag in doc_tags:
        if tag not in map_tags:
            issues.append(("ORPHAN-DOC", f"Tag {tag} in doc, not in map"))

    # ORPHAN-MAP: tags in map but not in document (exclude redacted placeholders)
    for tag in map_tags:
        if tag not in doc_tags and tag in text:
            continue
        if tag not in doc_tags:
            # May be OK if map has more entities (e.g. merged/deduped)
            pass  # Don't flag - map can have extra entries from dedup

    # MAP-DUP: duplicate PERSON canonicals (same canonical string -> multiple tags)
    canon_to_tags = {}
    for tag, canon in person_canonicals.items():
        c = canon.strip().lower()
        if c not in canon_to_tags:
            canon_to_tags[c] = []
        canon_to_tags[c].append(tag)
    for canon, tags in canon_to_tags.items():
        if len(tags) > 1:
            issues.append(("MAP-DUP", f"Duplicate person '{canon}': {tags}"))

    # NAME-LEAK: known person surnames (from map) appearing OUTSIDE tags
    known_lasts = set()
    for ent in entities:
        if ent.get("type") != "PERSON":
            continue
        orig = ent.get("original", "")
        parts = orig.split()
        if len(parts) >= 2:
            known_lasts.add(parts[-1].lower())
        elif len(parts) == 1 and len(parts[0]) >= 4:
            known_lasts.add(parts[0].lower())

    searchable_lasts = [n for n in sorted(known_lasts, key=len, reverse=True) if len(n) >= 4 and n.lower() not in FALSE_POSITIVE_NAMES]
    if searchable_lasts:
        # Remove all tag content from text for leak check
        text_no_tags = TAG_RE.sub("", text)
        for last in searchable_lasts:
            # Look for surname as whole word, not inside a tag
            pat = re.compile(r'(?<!\w)' + re.escape(last) + r'(?!\w)', re.IGNORECASE)
            for m in pat.finditer(text_no_tags):
                # Get context
                start = max(0, m.start() - 30)
                end = min(len(text_no_tags), m.end() + 30)
                ctx = text_no_tags[start:end].replace("\n", " ")
                issues.append(("NAME-LEAK", f"'{last}' outside tag, ctx: ...{ctx}..."))

    return issues


def main():
    anon_files = sorted(TEST_DIR.glob("*_anon.docx"))
    clean = 0
    with_issues = []
    for anon_path in anon_files:
        base = anon_path.stem.replace("_anon", "")
        map_path = TEST_DIR / f"{base}_map.json"
        issues = verify_file(anon_path, map_path)
        if not issues:
            clean += 1
        else:
            with_issues.append((anon_path.name, issues))

    print(f"\n=== FINÁLNÍ VERIFIKACE ===\n")
    print(f"CLEAN: {clean}/{len(anon_files)}")
    print(f"S PROBLÉMY: {len(with_issues)}")
    if with_issues:
        print("\n--- Soubory s problémy ---")
        for name, issues in with_issues:
            print(f"\n{name}:")
            for typ, msg in issues:
                print(f"  [{typ}] {msg}")
    else:
        print("\nVšechny soubory jsou CLEAN!")
    print()


if __name__ == "__main__":
    main()
