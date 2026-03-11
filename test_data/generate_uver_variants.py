from pathlib import Path

from docx import Document


BASE = Path(__file__).resolve().parent / "smlouva-o-uveru_base.docx"
OUT_DIR = Path(__file__).resolve().parent


ORIG_ADDR1 = "Vyskočilova 1442/1b, Praha 4 - Michle, 140 28"
ORIG_ADDR2 = "nám. Kosmonautů 899/2, Mohelnice, 789 85 p. Mohelnice"


ADDR1_VARIANTS = [
    "Vyskočilova 1442/1b, Praha 4 - Michle, 140 28",
    "PSČ 140 28, Vyskočilova 1442/1b, Praha 4 - Michle, Česká republika",
    "140 28 Praha 4 - Michle, Vyskočilova 1442/1b",
    "Praha 4 - Michle, Vyskočilova 1442/1b, 140 28",
    "Vyskočilova 1442/1b, 140 28 Praha 4 - Michle",
    "140 28, Praha 4, Michle, Vyskočilova 1442/1b",
    "Česká republika, 140 28 Praha 4 - Michle, Vyskočilova 1442/1b",
    "Vyskočilova 1442/1b, 14028 Praha 4 - Michle",
    "Praha 4, Michle, Vyskočilova 1442/1b, PSČ 140 28",
    "PSČ 140 28, Vyskočilova 1442/1b, Praha 4 - Michle",
    "Vyskočilova 1442/1b, Praha 4, Michle, PSČ 140 28",
    "14028, Praha 4 - Michle, Vyskočilova 1442/1b",
    "Vyskočilova 1442/1b, Praha 4 - Michle",
    "Vyskočilova 1442/1b, 140 28, Praha 4 - Michle",
    "Praha 4 - Michle, PSČ 140 28, Vyskočilova 1442/1b",
    "Vyskočilova 1442/1b, Praha 4, 140 28 Michle",
]

ADDR2_VARIANTS = [
    "nám. Kosmonautů 899/2, Mohelnice, 789 85 p. Mohelnice",
    "789 85 Mohelnice, nám. Kosmonautů 899/2",
    "Mohelnice, nám. Kosmonautů 899/2, 789 85",
    "nám. Kosmonautů 899/2, 789 85 Mohelnice",
    "Česká republika, 789 85 Mohelnice, nám. Kosmonautů 899/2",
    "PSČ 789 85, nám. Kosmonautů 899/2, Mohelnice",
    "nám. Kosmonautů 899/2, PSČ 789 85, Mohelnice",
    "Mohelnice 789 85, nám. Kosmonautů 899/2",
    "nám. Kosmonautů 899/2, 78985 Mohelnice",
    "Mohelnice, PSČ 789 85, nám. Kosmonautů 899/2",
    "78985, Mohelnice, nám. Kosmonautů 899/2",
    "Mohelnice, nám. Kosmonautů 899/2",
    "nám. Kosmonautů 899/2, Mohelnice",
    "Mohelnice, 789 85 p. Mohelnice, nám. Kosmonautů 899/2",
    "nám. Kosmonautů 899/2, 789 85, Mohelnice",
]


def replace_in_paragraphs(doc: Document, old: str, new: str) -> int:
    """Naivní textové nahrazení v odstavcích (pro testovací účely stačí)."""
    count = 0
    for p in doc.paragraphs:
        if old in p.text:
            p.text = p.text.replace(old, new)
            count += 1
    return count


def generate_variants() -> None:
    if not BASE.exists():
        raise SystemExit(f"Base DOCX not found: {BASE}")

    for i in range(15):
        addr1 = ADDR1_VARIANTS[i]
        addr2 = ADDR2_VARIANTS[i]

        doc = Document(str(BASE))
        r1 = replace_in_paragraphs(doc, ORIG_ADDR1, addr1)
        r2 = replace_in_paragraphs(doc, ORIG_ADDR2, addr2)

        out_name = OUT_DIR / f"smlouva-uver-variant-{i+1}.docx"
        doc.save(str(out_name))
        print(f"[OK] vytvořeno {out_name.name} (addr1 hits={r1}, addr2 hits={r2})")


if __name__ == "__main__":
    generate_variants()

