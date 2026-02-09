# -*- coding: utf-8 -*-
"""
OCR PDF to DOCX – Převod naskenovaných PDF do DOCX pomocí Tesseract OCR.

Naskenované PDF = pro počítač jen obrázek (pixely), žádný text.
Tento skript pomocí OCR přečte text z obrázku a uloží ho do DOCX,
který pak může zpracovat anonymizátor.

Postup:
    1. PDF stránky → obrázky (poppler/pdf2image)
    2. Obrázky → text (Tesseract OCR)
    3. Text → DOCX (python-docx)

Použití:
    python ocr_pdf_to_docx.py <soubor.pdf>
    python ocr_pdf_to_docx.py <soubor.pdf> --lang ces+eng
    python ocr_pdf_to_docx.py <soubor.pdf> -o vystup.docx
    python ocr_pdf_to_docx.py --batch <adresar>
    python ocr_pdf_to_docx.py --check <soubor.pdf>

Závislosti (pip):
    pip install pytesseract pdf2image Pillow python-docx

Systémové závislosti:
    apt install tesseract-ocr tesseract-ocr-ces poppler-utils
"""

import sys
import argparse
import re
from pathlib import Path

try:
    from pdf2image import convert_from_path
except ImportError:
    print("CHYBA: Chybi balicek pdf2image. Nainstalujte: pip install pdf2image")
    print("       A systemovy balicek: apt install poppler-utils")
    sys.exit(1)

try:
    import pytesseract
except ImportError:
    print("CHYBA: Chybi balicek pytesseract. Nainstalujte: pip install pytesseract")
    print("       A systemovy balicek: apt install tesseract-ocr tesseract-ocr-ces")
    sys.exit(1)

try:
    from docx import Document
    from docx.shared import Pt
except ImportError:
    print("CHYBA: Chybi balicek python-docx. Nainstalujte: pip install python-docx")
    sys.exit(1)

from PIL import Image


def ocr_page(image: Image.Image, lang: str = "ces+eng",
             config: str = "--oem 3 --psm 6") -> str:
    """Provede OCR na jedné stránce (obrázku) a vrátí rozpoznaný text."""
    return pytesseract.image_to_string(image, lang=lang, config=config)


def cleanup_ocr_text(text: str) -> str:
    """Vyčistí běžné OCR artefakty v textu."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Odstraň řádky obsahující jen symboly (artefakty skenování)
        if stripped and re.match(r'^[|_\-=~*#@!]+$', stripped):
            continue
        cleaned.append(line)

    text = '\n'.join(cleaned)
    # Oprav dvojité mezery
    text = re.sub(r'  +', ' ', text)
    # Oprav rozlomená slova na konci řádku (čes-\nký → český)
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

    return text


def is_scanned_pdf(pdf_path: str) -> bool:
    """
    Zjistí, zda je PDF skenované (obrázkové) nebo textové.

    Textové PDF → pdftotext vytáhne text přímo, OCR není potřeba.
    Skenované PDF → pdftotext nevytáhne skoro nic, potřeba OCR.
    """
    try:
        import subprocess
        result = subprocess.run(
            ['pdftotext', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        text = result.stdout.strip()
        images = convert_from_path(str(pdf_path), last_page=1)
        num_pages = max(len(images), 1)
        chars_per_page = len(text) / num_pages
        return chars_per_page < 100
    except Exception:
        return True


def pdf_to_docx(pdf_path: str, output_path: str = None,
                lang: str = "ces+eng", dpi: int = 300,
                verbose: bool = False) -> str:
    """
    Převede naskenované PDF do DOCX pomocí OCR.

    Args:
        pdf_path: Cesta k PDF souboru
        output_path: Cesta k výstupnímu DOCX (None = automaticky _ocr.docx)
        lang: Jazyky pro Tesseract (default: ces+eng)
        dpi: Rozlišení pro konverzi PDF→obrázek (default: 300)
        verbose: Podrobný výstup

    Returns:
        Cesta k vytvořenému DOCX souboru
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF soubor nenalezen: {pdf_path}")

    if output_path is None:
        output_path = pdf_path.parent / f"{pdf_path.stem}_ocr.docx"
    else:
        output_path = Path(output_path)

    print(f"\n  Zpracovavam: {pdf_path.name}")
    print(f"  Jazyk OCR: {lang}")
    print(f"  Rozliseni: {dpi} DPI")

    # 1. PDF stránky → obrázky
    print(f"  Prevadim PDF na obrazky...")
    try:
        images = convert_from_path(str(pdf_path), dpi=dpi)
    except Exception as e:
        raise RuntimeError(
            f"Nelze prevest PDF na obrazky: {e}\n"
            f"Ujistete se, ze je nainstalovany poppler-utils: "
            f"apt install poppler-utils"
        )

    print(f"  Nalezeno {len(images)} stranek")

    # 2. OCR každé stránky → text → DOCX
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    total_chars = 0

    for i, image in enumerate(images, 1):
        if verbose:
            print(f"  OCR stranka {i}/{len(images)}...")
        else:
            pct = int(i / len(images) * 100)
            print(f"\r  OCR: {i}/{len(images)} stranek ({pct}%)", end='', flush=True)

        page_text = ocr_page(image, lang=lang)
        page_text = cleanup_ocr_text(page_text)
        total_chars += len(page_text)

        # 3. Text → DOCX odstavce
        for para_text in page_text.split('\n'):
            doc.add_paragraph(para_text.strip() if para_text.strip() else '')

        if i < len(images):
            doc.add_page_break()

    print()

    doc.save(str(output_path))

    print(f"  Vysledek: {output_path.name}")
    print(f"  Celkem znaku: {total_chars:,}")
    print(f"  Celkem stranek: {len(images)}")

    return str(output_path)


def batch_pdf_to_docx(directory: str, lang: str = "ces+eng",
                      dpi: int = 300, verbose: bool = False) -> list:
    """Převede všechny PDF v adresáři na DOCX."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Adresar nenalezen: {directory}")

    pdf_files = sorted(dir_path.glob("*.pdf"))
    if not pdf_files:
        print(f"  Zadne PDF soubory v {directory}")
        return []

    print(f"\n  Nalezeno {len(pdf_files)} PDF souboru v {directory}")

    results = []
    for pdf_file in pdf_files:
        if pdf_file.name.startswith('~'):
            continue
        try:
            output = pdf_to_docx(str(pdf_file), lang=lang, dpi=dpi, verbose=verbose)
            results.append(output)
        except Exception as e:
            print(f"  CHYBA pri zpracovani {pdf_file.name}: {e}")

    return results


def main():
    ap = argparse.ArgumentParser(
        description="OCR PDF to DOCX - Prevod naskenovanych PDF do DOCX pomoci Tesseract OCR"
    )
    ap.add_argument("pdf_path", nargs='?',
                    help="Cesta k PDF souboru nebo adresari")
    ap.add_argument("--output", "-o",
                    help="Cesta k vystupnimu DOCX souboru")
    ap.add_argument("--lang", default="ces+eng",
                    help="Jazyky pro OCR (default: ces+eng)")
    ap.add_argument("--dpi", type=int, default=300,
                    help="Rozliseni pro konverzi (default: 300)")
    ap.add_argument("--batch", action="store_true",
                    help="Zpracovat vsechny PDF v adresari")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="Podrobny vystup")
    ap.add_argument("--check", action="store_true",
                    help="Pouze zkontrolovat, zda je PDF skenovane")

    args = ap.parse_args()

    if not args.pdf_path:
        print("CHYBA: Chybi cesta k PDF souboru.")
        print("Pouziti: python ocr_pdf_to_docx.py <soubor.pdf>")
        print("         python ocr_pdf_to_docx.py --batch <adresar>")
        return 2

    try:
        if args.check:
            is_scanned = is_scanned_pdf(args.pdf_path)
            print(f"  {args.pdf_path}: {'SKENOVANE' if is_scanned else 'TEXTOVE'} PDF")
            return 0

        if args.batch:
            results = batch_pdf_to_docx(
                args.pdf_path, lang=args.lang,
                dpi=args.dpi, verbose=args.verbose
            )
            print(f"\n  Zpracovano {len(results)} souboru")
            return 0

        output = pdf_to_docx(
            args.pdf_path, output_path=args.output,
            lang=args.lang, dpi=args.dpi, verbose=args.verbose
        )

        print(f"\n  Hotovo! Vystup: {output}")
        print(f"\n  Tip: Pro anonymizaci spustte:")
        print(f'  python "anon7.2 - s padama.py" "{output}"')

        return 0

    except Exception as e:
        print(f"\n  CHYBA: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
