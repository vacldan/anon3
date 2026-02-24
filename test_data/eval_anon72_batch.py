from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
TEST_DATA = ROOT / "test_data"
ANON72 = ROOT / "anon72.py"
NAMES_JSON = ROOT / "cz_names.v1.json"


LABEL_RE = re.compile(r"\[\[[A-Z0-9_]+\]\]")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm_token(s: str) -> str:
    return strip_accents(s).lower().strip()


def labels_in_docx(path: Path) -> set[str]:
    doc = Document(str(path))
    txt = "\n".join(p.text for p in doc.paragraphs)
    return set(LABEL_RE.findall(txt))


def labels_in_map_txt(path: Path) -> set[str]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    return set(LABEL_RE.findall(txt))


def parse_map_txt_person_canonicals(path: Path) -> dict[str, str]:
    """
    Parses lines like:
      [[PERSON_1]]: Jan Novák
    under OSOBY section. Returns label -> canonical full name.
    """
    txt = path.read_text(encoding="utf-8", errors="replace")
    lines = txt.splitlines()
    in_osoby = False
    canon: dict[str, str] = {}
    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.strip() == "OSOBY":
            in_osoby = True
            continue
        if in_osoby and re.fullmatch(r"[A-Z_]+", line.strip()) and line.strip() not in {"OSOBY"}:
            # next section reached
            in_osoby = False
        if not in_osoby:
            continue
        m = re.match(r"^\s*(\[\[PERSON_\d+\]\]):\s*(.+?)\s*$", line)
        if m:
            canon[m.group(1)] = m.group(2)
    return canon


def parse_expected_types_from_source(source_txt: str) -> set[str]:
    exp: set[str] = set()

    if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", source_txt, re.I):
        exp.add("EMAIL")
    if re.search(r"\+420\s?\d{3}\s?\d{3}\s?\d{3}", source_txt) or re.search(r"\b\d{9}\b", source_txt):
        exp.add("PHONE")
    if re.search(r"\b\d{6,10}/\d{4}\b", source_txt):
        exp.add("BANK")
    if re.search(r"\b\d{6}/\d{3,4}\b", source_txt):
        exp.add("BIRTH_ID")
    if re.search(r"\bCZ\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{0,2}\b", source_txt):
        exp.add("IBAN")
    if re.search(r"\b(?:\d{4}\s){3}\d{4}\b", source_txt) or re.search(r"\b\d{16}\b", source_txt):
        exp.add("CARD")
    if re.search(r"\b\d{1,2}\.\s?\d{1,2}\.\s?\d{4}\b", source_txt):
        exp.add("DATE")
    if re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", source_txt) or re.search(r"\b[0-9a-f]{0,4}:[0-9a-f:]{2,}\b", source_txt, re.I):
        exp.add("IP")
    if re.search(r"\b[0-9A-F]{2}(:[0-9A-F]{2}){5}\b", source_txt, re.I):
        exp.add("MAC")
    if re.search(r"\bIČO\b|\bICO\b", source_txt, re.I) and re.search(r"\b\d{8}\b", source_txt):
        exp.add("ICO")
    if re.search(r"\bHeslo:\s*\S+", source_txt):
        exp.add("PASSWORD")
    if re.search(r"\bIMEI\b", source_txt):
        exp.add("IMEI")
    if re.search(r"\bICCID\b", source_txt):
        exp.add("ICCID")
    if re.search(r"https?://", source_txt):
        exp.add("LINKEDIN")  # loosely; engine uses LINKEDIN for social links
    if re.search(r"\bVIN\b", source_txt):
        exp.add("VIN")
    if re.search(r"Registrační značka|SPZ", source_txt, re.I):
        exp.add("LICENSE_PLATE")
    if re.search(r"Adresa|bytem|Trvalý pobyt|Sídlo|Korespondenční", source_txt, re.I):
        exp.add("ADDRESS")
    exp.add("PERSON")
    return exp


def run_anon72(input_docx: Path) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run(
        [sys.executable, str(ANON72), str(input_docx), "--names-json", str(NAMES_JSON)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return p.returncode, p.stdout


def load_map_json(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    return data.get("entities", [])


def summarize_entities(entities: list[dict]) -> tuple[Counter, Counter]:
    type_counts = Counter()
    label_counts = Counter()
    for e in entities:
        t = e.get("type")
        lbl = e.get("label")
        if t:
            type_counts[t] += 1
        if lbl:
            label_counts[lbl] += 1
    return type_counts, label_counts


def detect_person_canonical_mismatches(entities: list[dict], person_canon: dict[str, str]) -> list[str]:
    """
    Flags labels where canonical first/last don't resemble any observed originals.
    """
    originals_by_label: dict[str, list[str]] = defaultdict(list)
    for e in entities:
        if e.get("type") == "PERSON" and e.get("label") and e.get("original"):
            originals_by_label[e["label"]].append(e["original"])

    issues: list[str] = []
    for label, canon_full in person_canon.items():
        originals = originals_by_label.get(label, [])
        if not originals:
            continue
        canon_tokens = [norm_token(t) for t in re.split(r"\s+", canon_full) if t.strip()]
        if not canon_tokens:
            continue
        canon_first = canon_tokens[0]
        canon_last = canon_tokens[-1]

        orig_firsts = set()
        orig_lasts = set()
        for o in originals:
            toks = [norm_token(t) for t in re.split(r"\s+", o) if t.strip()]
            if toks:
                orig_firsts.add(toks[0])
                orig_lasts.add(toks[-1])

        first_ok = any(canon_first.startswith(of[: max(2, len(of) - 1)]) or of.startswith(canon_first[: max(2, len(canon_first) - 1)]) for of in orig_firsts)
        last_ok = any(canon_last.startswith(ol[: max(3, len(ol) - 1)]) or ol.startswith(canon_last[: max(3, len(canon_last) - 1)]) for ol in orig_lasts)
        if not first_ok or not last_ok:
            issues.append(f"{label}: canonical='{canon_full}' originals={sorted(set(originals))[:4]}")
    return issues


def suspicious_license_plates(entities: list[dict]) -> list[str]:
    vals = []
    for e in entities:
        if e.get("type") == "LICENSE_PLATE" and e.get("original"):
            vals.append(str(e["original"]))
    susp = []
    # very loose CZ patterns; anything that doesn't look like typical plate becomes suspicious
    plate_ok = re.compile(r"^[0-9A-Z]{2,3}\s?[0-9A-Z]{2,4}$")
    for v in vals:
        v2 = v.strip().upper()
        if len(v2) < 5 or len(v2) > 9 or not plate_ok.match(v2):
            susp.append(v)
    return susp


@dataclass
class ContractResult:
    i: int
    name: str
    ok: bool
    score: int
    notes: list[str]
    missing_labels: list[str]
    missing_types: list[str]
    person_mismatch_count: int
    entity_type_counts: dict[str, int]


def score_contract(
    ok: bool,
    missing_labels: list[str],
    missing_types: list[str],
    person_mismatch: list[str],
    susp_plates: list[str],
) -> tuple[int, list[str]]:
    score = 10
    notes: list[str] = []

    if not ok:
        return 1, ["Neproběhlo korektně (chybí výstupy nebo návratový kód != 0)."]

    if missing_labels:
        penalty = min(5, len(missing_labels))
        score -= penalty
        notes.append(f"Tagy v `_anon.docx` chybí v mapě: {len(missing_labels)} (−{penalty}).")

    if missing_types:
        penalty = min(4, len(missing_types))
        score -= penalty
        notes.append(f"Chybí očekávané typy entit podle zdrojového textu: {', '.join(missing_types)} (−{penalty}).")

    if person_mismatch:
        penalty = min(3, len(person_mismatch))
        score -= penalty
        notes.append(f"Podezřelá kanonická jména osob (mismatch): {len(person_mismatch)} (−{penalty}).")

    if susp_plates:
        penalty = min(2, len(susp_plates))
        score -= penalty
        notes.append(f"Podezřelé detekce LICENSE_PLATE: {len(susp_plates)} (−{penalty}).")

    score = max(1, min(10, score))
    if score >= 9 and not notes:
        notes.append("Vypadá čistě (žádný z automatických kontrolních problémů).")
    return score, notes


def main() -> int:
    results: list[ContractResult] = []

    start = 1
    end = 10
    if len(sys.argv) == 3:
        try:
            start = int(sys.argv[1])
            end = int(sys.argv[2])
        except ValueError:
            print("Usage: python eval_anon72_batch.py [start end]")
            return 2
    elif len(sys.argv) != 1:
        print("Usage: python eval_anon72_batch.py [start end]")
        return 2

    if start > end:
        start, end = end, start

    for i in range(start, end + 1):
        stem = f"smlouva_gdpr_test_{i:02d}"
        src_txt = TEST_DATA / f"{stem}.txt"
        in_docx = TEST_DATA / f"{stem}.docx"
        out_docx = TEST_DATA / f"{stem}_anon.docx"
        out_json = TEST_DATA / f"{stem}_map.json"
        out_txt = TEST_DATA / f"{stem}_map.txt"
        out_pdf = TEST_DATA / f"{stem}_report.pdf"

        name = in_docx.name
        notes: list[str] = []

        if not in_docx.exists():
            results.append(
                ContractResult(i=i, name=name, ok=False, score=1, notes=["Chybí vstupní DOCX."], missing_labels=[], missing_types=[], person_mismatch_count=0, entity_type_counts={})
            )
            continue

        rc, out = run_anon72(in_docx)
        if rc != 0:
            notes.append(f"anon72.py skončil s návratovým kódem {rc}.")

        outputs_ok = all(p.exists() for p in [out_docx, out_json, out_txt, out_pdf])
        if not outputs_ok:
            missing = [p.name for p in [out_docx, out_json, out_txt, out_pdf] if not p.exists()]
            notes.append(f"Chybí výstupy: {', '.join(missing)}.")

        entities: list[dict] = []
        type_counts: dict[str, int] = {}
        missing_labels: list[str] = []
        missing_types: list[str] = []
        person_mismatch: list[str] = []
        susp_plates: list[str] = []

        if outputs_ok:
            entities = load_map_json(out_json)
            type_counter, _label_counter = summarize_entities(entities)
            type_counts = dict(type_counter)

            docx_labels = labels_in_docx(out_docx)
            map_labels = labels_in_map_txt(out_txt)
            missing_labels = sorted(docx_labels - map_labels)

            source_text = src_txt.read_text(encoding="utf-8", errors="replace") if src_txt.exists() else ""
            expected = parse_expected_types_from_source(source_text)
            present_types = set(type_counter.keys())
            missing_types = sorted(t for t in expected if t not in present_types)

            person_canon = parse_map_txt_person_canonicals(out_txt)
            person_mismatch = detect_person_canonical_mismatches(entities, person_canon)
            susp_plates = suspicious_license_plates(entities)

        ok = (rc == 0) and outputs_ok
        score, score_notes = score_contract(ok, missing_labels, missing_types, person_mismatch, susp_plates)
        notes.extend(score_notes)

        # attach a short digest of anon72 stdout if error
        if rc != 0:
            tail = "\n".join(out.splitlines()[-30:])
            notes.append("Výstup (posledních ~30 řádků):\n" + tail)

        results.append(
            ContractResult(
                i=i,
                name=name,
                ok=ok,
                score=score,
                notes=notes,
                missing_labels=missing_labels,
                missing_types=missing_types,
                person_mismatch_count=len(person_mismatch),
                entity_type_counts=type_counts,
            )
        )

    # Print human-friendly summary (for shell output capture)
    for r in results:
        print(f"\n=== {r.i:02d} {r.name} ===")
        print(f"OK: {r.ok}")
        print(f"Skóre: {r.score}/10")
        if r.entity_type_counts:
            top = ", ".join(f"{k}={v}" for k, v in sorted(r.entity_type_counts.items()))
            print(f"Entity typy: {top}")
        if r.missing_labels:
            print(f"Missing labels in map: {len(r.missing_labels)} (např. {', '.join(r.missing_labels[:8])})")
        if r.missing_types:
            print(f"Missing expected types: {', '.join(r.missing_types)}")
        if r.notes:
            for n in r.notes:
                print(f"- {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

