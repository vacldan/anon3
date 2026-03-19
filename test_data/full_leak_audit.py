#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kompletní audit anonymizovaných smluv: LEAK kontrola + PII regex + entity typy.

Pro každý pár (anon docx + map json):
1. Načte text z anonymizovaného DOCX
2. Načte entity z map JSON (typ, original)
3. Zkontroluje, zda se nějaký "original" z mapy objevuje v anonymizovaném textu (LEAK)
4. Zkontroluje anonymizovaný text regexem na PII vzory - pokud match je MIMO tag [[...]], je to potenciální leak

Sběr napříč všemi smlouvami:
- Všechny unikátní typy entit
- Rozdělení: STANDARD GDPR vs MIMO GDPR

Výstup: Přehledný report
"""

from __future__ import annotations

import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import re
import sys
from pathlib import Path
from collections import defaultdict

# PII regex vzory – ZALADĚNO podle anonymizátoru (anon72.py):
# - RC: vyloučeno FÚ-, KS-, VS-, čj- (číslo jednací)
# - Telefon: vyloučeno pokud následuje Kč/EUR/USD (částky)
# - Číslo účtu: vyloučeno FÚ-, KS-, VS-
PII_PATTERNS = [
    (r"(?<!FÚ-)(?<!KS-)(?<!VS-)(?<!čj-)(?<!\d)\d{6}/\d{3,4}(?!\d)", "RC"),
    (r"(?<!FÚ-)(?<!KS-)(?<!VS-)(?<!čj-)\d{9,16}/\d{4}", "Číslo účtu"),
    (r"CZ\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}", "IBAN"),
    (r"\+420\s?\d{3}\s?\d{3}\s?\d{3}", "Telefon +420"),
    (r"(?<!\d)\d{3}\s?\d{3}\s?\d{3}(?!\s*(?:Kč|EUR|USD|CZK)\b)(?!\d)", "Telefon 9 číslic"),
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "E-mail"),
    (r"(?<![A-Za-z0-9])\d[A-Z]{1,2}\d\s?\d{4}(?![A-Za-z0-9])", "SPZ"),
    (r"(?<![A-Za-z0-9])[A-HJ-NPR-Z0-9]{17}(?![A-Za-z0-9])", "VIN"),
]

# STANDARD GDPR entity (jména, adresy, RČ, telefony, emaily, účty, doklady, SPZ, VIN, data)
STANDARD_GDPR = {
    "PERSON", "ADDRESS", "BIRTH_ID", "PHONE", "EMAIL", "BANK", "IBAN", "BIC",
    "ID_CARD", "PASSPORT", "DRIVER_LICENSE", "ICO", "DIC", "DATE",
    "LICENSE_PLATE", "VIN", "CARD", "INSURANCE_ID", "BENEFIT_CARD", "ACCOUNT_ID",
    "EMP_ID", "GENETIC_ID", "RFID",
}

# MIMO GDPR (technické, sociální sítě, API, ...)
# Vše co není v STANDARD_GDPR je MIMO
MIMO_GDPR = {
    "USERNAME", "PASSWORD", "API_KEY", "SSH_KEY", "IP", "MAC", "IMEI",
    "HOST", "LINKEDIN", "FACEBOOK", "INSTAGRAM", "SKYPE", "VOICE_ID",
    "BIO_HASH", "PHOTO_ID", "SECRET",
}

TEST_DIR = Path(__file__).resolve().parent


def get_all_text_from_docx(docx_path: Path) -> str:
    """Extrahuje veškerý text z DOCX (odstavce + tabulky)."""
    try:
        from docx import Document
        doc = Document(str(docx_path))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        parts.append(p.text)
        return " ".join(parts)
    except Exception as e:
        return f"[CHYBA čtení DOCX: {e}]"


def find_tag_spans(text: str) -> list[tuple[int, int]]:
    """Vrátí seznam (start, end) pro každý [[...]] tag v textu."""
    spans = []
    for m in re.finditer(r"\[\[[^\]]+\]\]", text):
        spans.append((m.start(), m.end()))
    return spans


def is_inside_tag(pos: int, spans: list[tuple[int, int]]) -> bool:
    """True pokud pozice pos je uvnitř nějakého tagu."""
    for s, e in spans:
        if s <= pos < e:
            return True
    return False


def check_original_leaks(anon_text: str, entities: list[dict]) -> list[dict]:
    """Zkontroluje, zda se nějaký original z mapy objevuje v anonymizovaném textu."""
    leaks = []
    for ent in entities:
        orig = str(ent.get("original", "")).strip()
        etype = ent.get("type", "")
        label = ent.get("label", "")
        if len(orig) < 2:
            continue
        escaped = re.escape(orig)
        for m in re.finditer(escaped, anon_text, re.IGNORECASE):
            s, e = m.span()
            ctx = anon_text[max(0, s - 30):min(len(anon_text), e + 30)].replace("\n", " ")
            leaks.append({
                "original": orig,
                "type": etype,
                "label": label,
                "context": ctx,
            })
    return leaks


def check_pii_regex_outside_tags(anon_text: str) -> list[dict]:
    """PII regex - pouze hity MIMO tag [[...]]. Vzory vylučují false positive (částky, čj)."""
    spans = find_tag_spans(anon_text)
    hits = []
    for pat, label in PII_PATTERNS:
        for m in re.finditer(pat, anon_text):
            if is_inside_tag(m.start(), spans):
                continue
            ctx = anon_text[max(0, m.start() - 15):min(len(anon_text), m.end() + 15)].replace("\n", " ")
            hits.append({
                "match": m.group(),
                "type": label,
                "context": ctx,
            })
    return hits


def check_misclassifications(entities: list[dict], base: str) -> list[dict]:
    """Kontrola potenciálních špatných klasifikací."""
    issues = []
    by_type = defaultdict(list)
    for e in entities:
        by_type[e.get("type", "")].append(e.get("original", ""))

    # PHONE: začíná 1 a 9 číslic = pravděpodobně částka (CZ tel. nezačíná 1)
    for orig in by_type.get("PHONE", []):
        clean = re.sub(r"[\s\-+]", "", str(orig))
        if len(clean) == 9 and clean.isdigit() and clean.startswith("1"):
            issues.append({"file": base, "type": "PHONE_AS_AMOUNT", "original": orig})

    # BANK vs BIRTH_ID: stejná hodnota v obou = konflikt
    bank_vals = {str(x).replace(" ", "") for x in by_type.get("BANK", [])}
    for orig in by_type.get("BIRTH_ID", []):
        clean = str(orig).replace(" ", "")
        if clean in bank_vals:
            issues.append({"file": base, "type": "BIRTH_ID_AS_BANK", "original": orig})

    return issues


def load_map_entities(map_path: Path) -> list[dict]:
    """Načte entity z map JSON."""
    try:
        with open(map_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("entities", [])
    except Exception as e:
        return []


def find_all_pairs() -> list[tuple[Path, Path]]:
    """Najde všechny páry (anon docx, map json)."""
    pairs = []
    for anon in sorted(TEST_DIR.glob("*_anon.docx")):
        base = anon.stem.replace("_anon", "")
        map_path = TEST_DIR / f"{base}_map.json"
        if map_path.exists():
            pairs.append((anon, map_path))
    return pairs


def run_audit():
    """Spustí kompletní audit."""
    pairs = find_all_pairs()
    print(f"Nalezeno {len(pairs)} párů (anon docx + map json)")
    print("=" * 70)

    # Sběr
    contracts_with_original_leak = []
    contracts_with_regex_leak = []
    entity_type_counts = defaultdict(int)
    leak_examples = []  # max 20
    regex_leak_examples = []
    misclass_examples = []

    for anon_path, map_path in pairs:
        base = anon_path.stem.replace("_anon", "")
        anon_text = get_all_text_from_docx(anon_path)
        if anon_text.startswith("[CHYBA"):
            continue

        entities = load_map_entities(map_path)
        for ent in entities:
            t = ent.get("type", "")
            if t:
                entity_type_counts[t] += 1

        # 1) Original leak
        orig_leaks = check_original_leaks(anon_text, entities)
        if orig_leaks:
            contracts_with_original_leak.append(base)
            for leak in orig_leaks:
                if len(leak_examples) < 20:
                    leak_examples.append({
                        "file": base,
                        **leak,
                    })

        # 2) PII regex mimo tag (zlepšené vzory – méně false positive)
        regex_hits = check_pii_regex_outside_tags(anon_text)
        if regex_hits:
            contracts_with_regex_leak.append(base)
            for hit in regex_hits:
                if len(regex_leak_examples) < 20:
                    regex_leak_examples.append({
                        "file": base,
                        **hit,
                    })

        # 3) Misclassifikace
        mis = check_misclassifications(entities, base)
        misclass_examples.extend(mis[:3])  # max 3 per contract

    # Rozdělení typů
    standard_types = {t: entity_type_counts[t] for t in entity_type_counts if t in STANDARD_GDPR}
    mimo_types = {t: entity_type_counts[t] for t in entity_type_counts if t in MIMO_GDPR}
    other_types = {t: entity_type_counts[t] for t in entity_type_counts
                  if t not in STANDARD_GDPR and t not in MIMO_GDPR}

    # Report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("KOMPLETNÍ AUDIT ANONYMIZOVANÝCH SMLUV – LEAK REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Celkem zpracovaných párů: {len(pairs)}")
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("1. SMLOUVY S LEAKEM (originál z mapy v anonymizovaném textu)")
    report_lines.append("-" * 80)
    report_lines.append(f"Počet smluv s leakem: {len(contracts_with_original_leak)}")
    if contracts_with_original_leak:
        report_lines.append("Smlouvy:")
        for c in sorted(contracts_with_original_leak)[:50]:
            report_lines.append(f"  - {c}")
        if len(contracts_with_original_leak) > 50:
            report_lines.append(f"  ... a dalších {len(contracts_with_original_leak) - 50}")

    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("2. SMLOUVY S PII REGEX HIT MIMO TAG (RC, telefon, email, IBAN, SPZ, VIN)")
    report_lines.append("-" * 80)
    report_lines.append(f"Počet smluv s PII regex hit mimo tag: {len(contracts_with_regex_leak)}")
    if contracts_with_regex_leak:
        report_lines.append("Smlouvy:")
        for c in sorted(contracts_with_regex_leak)[:50]:
            report_lines.append(f"  - {c}")
        if len(contracts_with_regex_leak) > 50:
            report_lines.append(f"  ... a dalších {len(contracts_with_regex_leak) - 50}")

    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("3. TYPY ENTIT (četnost)")
    report_lines.append("-" * 80)
    report_lines.append("STANDARD GDPR (jména, adresy, RČ, telefony, emaily, účty, doklady, SPZ, VIN, data):")
    for t in sorted(standard_types.keys()):
        report_lines.append(f"  {t}: {standard_types[t]}")
    report_lines.append("")
    report_lines.append("MIMO GDPR (USERNAME, SSH_KEY, API_KEY, LINKEDIN, VOICE_ID, ...):")
    for t in sorted(mimo_types.keys()):
        report_lines.append(f"  {t}: {mimo_types[t]}")
    report_lines.append("")
    report_lines.append("Ostatní typy (v mapách):")
    for t in sorted(other_types.keys()):
        report_lines.append(f"  {t}: {other_types[t]}")

    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("4. KONKRÉTNÍ PŘÍKLADY LEAKŮ (originál v textu) – max 20")
    report_lines.append("-" * 80)
    for i, ex in enumerate(leak_examples[:20], 1):
        report_lines.append(f"  [{i}] {ex['file']}")
        report_lines.append(f"      Typ: {ex['type']}, Original: '{ex['original'][:60]}'")
        report_lines.append(f"      Kontext: ...{ex['context'][:80]}...")
        report_lines.append("")

    report_lines.append("-" * 80)
    report_lines.append("5. KONKRÉTNÍ PŘÍKLADY PII REGEX (mimo tag) – max 20")
    report_lines.append("-" * 80)
    for i, ex in enumerate(regex_leak_examples[:20], 1):
        report_lines.append(f"  [{i}] {ex['file']}")
        report_lines.append(f"      Typ: {ex['type']}, Match: '{ex['match']}'")
        report_lines.append(f"      Kontext: ...{ex['context'][:80]}...")
        report_lines.append("")

    report_lines.append("-" * 80)
    report_lines.append("6. POTENCIÁLNÍ MISKLASIFIKACE (PHONE jako částka, BIRTH_ID vs BANK)")
    report_lines.append("-" * 80)
    report_lines.append(f"Počet: {len(misclass_examples)}")
    for i, ex in enumerate(misclass_examples[:15], 1):
        report_lines.append(f"  [{i}] {ex.get('file', '?')}: {ex['type']} '{ex.get('original', '')}'")

    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("7. SHRNUTÍ AUDITU – CO JE SPRÁVNĚ / ŠPATNĚ")
    report_lines.append("-" * 80)
    report_lines.append("SKUTEČNÉ LEAKY (originál z mapy v textu):")
    report_lines.append("  - BIRTH_PLACE (Brno, Praha): anonymizuje se jen 'Místo narození: X',")
    report_lines.append("    ostatní výskyty (DataCloud Brno, ÚMČ Brno-střed) zůstávají = LEAK")
    report_lines.append("  - USERNAME (hcp_admin): anonymizuje se jen s prefixem Login/Username,")
    report_lines.append("    výskyt v seznamu 'admin, root, hcp_admin' zůstává = LEAK")
    report_lines.append("  - PERSON 'Nové': false positive z 'Nové Město' (místo)")
    report_lines.append("")
    report_lines.append("PII REGEX FALSE POSITIVE (opraveno v tomto skriptu):")
    report_lines.append("  - Částky (125 000 000 Kč) jako 'telefon' – vyloučeno (?!Kč|EUR|USD)")
    report_lines.append("  - Číslo jednací (FÚ-123456/2024) jako 'RC' – vyloučeno (?<!FÚ-)")
    report_lines.append("")
    report_lines.append("PII REGEX – SKUTEČNÉ LEAKY:")
    report_lines.append("  - Pokud po opravě stále zůstávají hity = skutečný PII mimo tag")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("KONEC REPORTU")
    report_lines.append("=" * 80)

    report_text = "\n".join(report_lines)
    print(report_text)

    # Uložit do souboru
    out_path = TEST_DIR / "full_leak_audit_report.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n[INFO] Report uložen: {out_path}")

    return {
        "total_pairs": len(pairs),
        "contracts_with_original_leak": len(contracts_with_original_leak),
        "contracts_with_regex_leak": len(contracts_with_regex_leak),
        "entity_types": dict(entity_type_counts),
        "standard_gdpr": dict(standard_types),
        "mimo_gdpr": dict(mimo_types),
        "other_types": dict(other_types),
    }


if __name__ == "__main__":
    run_audit()
