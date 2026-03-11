"""Generátor variant 16-30 s kompletně odlišnými adresami (jiná města, ulice, PSČ)."""
from pathlib import Path
from docx import Document

BASE = Path(__file__).resolve().parent / "smlouva-o-uveru_base.docx"
OUT_DIR = Path(__file__).resolve().parent

ORIG_ADDR1 = "Vyskočilova 1442/1b, Praha 4 - Michle, 140 28"
ORIG_ADDR2 = "nám. Kosmonautů 899/2, Mohelnice, 789 85 p. Mohelnice"

ADDR1_VARIANTS = [
    # 16: Brno - klasický formát
    "Šumavská 524/31, Brno - Žabovřesky, 616 00",
    # 17: Ostrava - PSČ napřed
    "PSČ 702 00, Ostrava, ul. Nádražní 3114/128",
    # 18: Plzeň - obrácený slovosled
    "301 00 Plzeň, Americká 2/42",
    # 19: Olomouc - bez PSČ
    "Olomouc, Horní náměstí 583",
    # 20: České Budějovice - plný formát s republikou
    "nám. Přemysla Otakara II. 1/1, České Budějovice, 370 01, Česká republika",
    # 21: Hradec Králové - PSČ slitě
    "50002, Hradec Králové, Velké náměstí 21",
    # 22: Liberec - obrácený
    "Liberec, 460 01, Moskevská 637/6a",
    # 23: Pardubice - ul. prefix
    "ul. Smilova 334, Pardubice, PSČ 530 02",
    # 24: Zlín - kompaktní
    "nábřeží 315/2, 760 01 Zlín",
    # 25: Karlovy Vary - republika napřed
    "Česká republika, Karlovy Vary, T. G. Masaryka 855/24, 360 01",
    # 26: Jihlava - město napřed
    "Jihlava, Masarykovo náměstí 97/1, PSČ 586 01",
    # 27: Opava - bez mezer v PSČ
    "Hrnčířská 171/14, 74601 Opava",
    # 28: Teplice - PSČ uprostřed
    "Krupská 1859/2, 415 01, Teplice",
    # 29: Chomutov - nám. prefix
    "náměstí 1. Máje 72/1, Chomutov, 430 01, Česká republika",
    # 30: Děčín - rozložený
    "Děčín, Česká republika, Masarykovo náměstí 1/1, PSČ 405 02",
]

ADDR2_VARIANTS = [
    # 16: Znojmo
    "Obroková 348/12, Znojmo, 669 02",
    # 17: Kroměříž
    "PSČ 767 01, Kroměříž, Velké náměstí 115",
    # 18: Třebíč - bez PSČ
    "Karlovo náměstí 104/55, Třebíč",
    # 19: Prostějov
    "nám. T. G. Masaryka 130/14, 796 01 Prostějov",
    # 20: Přerov - republika
    "Přerov, Česká republika, Bratrská 709/30, 750 02",
    # 21: Havlíčkův Brod
    "58001, Havlíčkův Brod, Havlíčkovo náměstí 57",
    # 22: Kutná Hora - obrácený
    "Kutná Hora, 284 01, Havlíčkovo náměstí 552/1",
    # 23: Kolín
    "ul. Karlovo náměstí 78, Kolín, PSČ 280 02",
    # 24: Benešov
    "Masarykovo náměstí 1, 256 01 Benešov",
    # 25: Písek - republika napřed
    "Česká republika, Písek, Velké náměstí 114, 397 01",
    # 26: Chrudim
    "Chrudim, Resselovo náměstí 77, PSČ 537 01",
    # 27: Louny - bez mezer
    "Mírové náměstí 35, 44001 Louny",
    # 28: Tábor - PSČ uprostřed
    "Žižkovo náměstí 2, 390 01, Tábor",
    # 29: Strakonice
    "náměstí Palackého 1, Strakonice, 386 01, Česká republika",
    # 30: Svitavy
    "Svitavy, Česká republika, náměstí Míru 32/1, PSČ 568 02",
]


def replace_in_paragraphs(doc: Document, old: str, new: str) -> int:
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
        variant_num = i + 16

        doc = Document(str(BASE))
        r1 = replace_in_paragraphs(doc, ORIG_ADDR1, addr1)
        r2 = replace_in_paragraphs(doc, ORIG_ADDR2, addr2)

        out_name = OUT_DIR / f"smlouva-uver-variant-{variant_num}.docx"
        doc.save(str(out_name))
        print(f"[OK] {out_name.name} (addr1 hits={r1}, addr2 hits={r2})")


if __name__ == "__main__":
    generate_variants()
