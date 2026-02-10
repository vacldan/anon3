# pdf2docx_cli.py - PDF to DOCX converter with OCR fallback for scanned documents
import sys
import os
import re
import subprocess
from pathlib import Path

# Set UTF-8 encoding - safe cross-platform approach
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

# --- Kontrola závislostí ---

_has_pdf2docx = False
try:
    from pdf2docx import Converter
    _has_pdf2docx = True
except ImportError:
    pass

_has_ocr = False
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance, ImageFilter
    from docx import Document
    from docx.shared import Pt
    _has_ocr = True
except ImportError:
    pass

if not _has_pdf2docx and not _has_ocr:
    print("ERROR: Zadna knihovna pro konverzi PDF neni nainstalována!", flush=True)
    print("Pro textove PDF:    pip install pdf2docx", flush=True)
    print("Pro skenovane PDF:  pip install pytesseract pdf2image Pillow python-docx", flush=True)
    print("                    apt install tesseract-ocr tesseract-ocr-ces poppler-utils", flush=True)
    sys.exit(1)


# --- Detekce typu PDF ---

def is_scanned_pdf(pdf_path: Path) -> bool:
    """
    Zjistí, zda je PDF skenované (obrázkové) nebo textové.

    Textové PDF → pdftotext vytáhne text, není potřeba OCR.
    Skenované PDF → pdftotext nevytáhne skoro nic, potřeba OCR.
    """
    try:
        result = subprocess.run(
            ['pdftotext', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        text = result.stdout.strip()
        # Méně než 50 znaků na celý dokument = pravděpodobně sken
        return len(text) < 50
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # pdftotext není dostupný nebo timeout → zkus OCR pro jistotu
        return True


# --- Konverze textového PDF (pdf2docx) ---

def convert_text_pdf(pdf_path: Path, docx_path: Path) -> bool:
    """Převede textové PDF do DOCX přes knihovnu pdf2docx."""
    if not _has_pdf2docx:
        return False

    try:
        print("  Metoda: pdf2docx (textove PDF)", flush=True)
        cv = Converter(str(pdf_path))
        cv.convert(str(docx_path), start=0, end=None)
        cv.close()

        if docx_path.exists() and docx_path.stat().st_size > 0:
            return True
        return False

    except Exception as e:
        print(f"  pdf2docx selhalo: {e}", flush=True)
        return False


# --- Konverze skenovaného PDF (OCR) ---

def preprocess_image(image):
    """Předzpracuje obrázek pro lepší OCR kvalitu.

    Minimální zásah - jen převod na šedou a jemné zvýšení kontrastu.
    Upscale ani binarizace se nedělá (amplifikuje šum / ničí diacritiku).
    """
    # Převeď na šedou
    img = image.convert('L')

    # Jemné zvýšení kontrastu
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    return img


def cleanup_ocr_text(text: str) -> str:
    """Vyčistí běžné OCR artefakty."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Odstraň řádky s jen symboly (artefakty skenování)
        if stripped and re.match(r'^[|_\-=~*#@!]+$', stripped):
            continue
        cleaned.append(line)

    text = '\n'.join(cleaned)

    # Oprav dvojité mezery
    text = re.sub(r'  +', ' ', text)

    # Oprav rozlomená slova na konci řádku (čes-\nký → český)
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

    # Sloučí osamocené číslo bodu (např. "2.2\n\nJakou nemovitou...")
    # s následujícím neprázdným řádkem
    # Vzor: řádek obsahuje jen číslo typu "2.2" nebo "2.3'" nebo "24" → připoj k dalšímu textu
    text = re.sub(
        r'^(\d{1,3}[\.\)]{0,1}\d{0,2}[\'\'"]?)\s*\n+(?=\S)',
        r'\1 ',
        text,
        flags=re.MULTILINE
    )

    return text


def convert_scanned_pdf(pdf_path: Path, docx_path: Path,
                        lang: str = "ces", dpi: int = 300) -> bool:
    """Převede skenované PDF do DOCX přes Tesseract OCR."""
    if not _has_ocr:
        print("  OCR neni dostupne! Nainstalujte:", flush=True)
        print("    pip install pytesseract pdf2image Pillow python-docx", flush=True)
        print("    apt install tesseract-ocr tesseract-ocr-ces poppler-utils", flush=True)
        return False

    try:
        print(f"  Metoda: Tesseract OCR (skenovane PDF)", flush=True)
        print(f"  Jazyk: {lang}, Rozliseni: {dpi} DPI", flush=True)

        # 1. PDF → obrázky
        print("  Prevadim stranky na obrazky...", flush=True)
        images = convert_from_path(str(pdf_path), dpi=dpi)
        print(f"  Nalezeno {len(images)} stranek", flush=True)

        # 2. OCR každé stránky → text
        doc = Document()
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)

        total_chars = 0

        for i, image in enumerate(images, 1):
            pct = int(i / len(images) * 100)
            print(f"\r  OCR: {i}/{len(images)} stranek ({pct}%)", end='', flush=True)

            # Předzpracování obrázku pro lepší kvalitu OCR
            processed = preprocess_image(image)

            page_text = pytesseract.image_to_string(
                processed, lang=lang, config="--oem 1 --psm 3"
            )
            page_text = cleanup_ocr_text(page_text)
            total_chars += len(page_text)

            # 3. Text → DOCX odstavce
            for para_text in page_text.split('\n'):
                doc.add_paragraph(para_text.strip() if para_text.strip() else '')

            if i < len(images):
                doc.add_page_break()

        print(flush=True)

        doc.save(str(docx_path))
        print(f"  OCR hotovo, rozpoznano {total_chars:,} znaku", flush=True)

        return docx_path.exists() and docx_path.stat().st_size > 0

    except Exception as e:
        print(f"  OCR selhalo: {e}", flush=True)
        return False


# --- Hlavní konverzní funkce ---

def convert_pdf(pdf_path: Path, dpi: int = 300, lang: str = "ces") -> bool:
    """
    Převede PDF do DOCX - automaticky zvolí správnou metodu.

    Textové PDF  → pdf2docx (zachová formátování)
    Skenované PDF → Tesseract OCR (přečte text z obrázku)
    """
    docx_path = pdf_path.with_suffix('.docx')

    print(f"Zpracovavam PDF: {pdf_path.name}", flush=True)
    print(f"Vystupni DOCX: {docx_path.name}", flush=True)

    if not pdf_path.exists():
        print(f"ERROR: PDF soubor neexistuje: {pdf_path}", flush=True)
        return False

    if pdf_path.stat().st_size == 0:
        print(f"ERROR: PDF soubor je prazdny: {pdf_path}", flush=True)
        return False

    # Detekce: textové nebo skenované?
    scanned = is_scanned_pdf(pdf_path)

    if scanned:
        print("  Detekovano: SKENOVANE PDF (obrazek)", flush=True)
        success = convert_scanned_pdf(pdf_path, docx_path, lang=lang, dpi=dpi)
    else:
        print("  Detekovano: TEXTOVE PDF", flush=True)
        success = convert_text_pdf(pdf_path, docx_path)

        # Fallback: pokud pdf2docx selhalo a máme OCR, zkus OCR
        if not success and _has_ocr:
            print("  Zkousim fallback pres OCR...", flush=True)
            success = convert_scanned_pdf(pdf_path, docx_path, lang=lang, dpi=dpi)

    if success:
        print(f"[OK] Uspesne prevedeno: {docx_path.name}", flush=True)
        print(f"Velikost: {docx_path.stat().st_size} bytu", flush=True)
    else:
        print("ERROR: Konverze selhala", flush=True)

    return success


def main():
    print("PDF to DOCX Converter - Nixminds Document Suite", flush=True)
    print("=" * 50, flush=True)

    # Informace o dostupných metodách
    if _has_pdf2docx:
        print("  [+] pdf2docx: dostupne (textove PDF)", flush=True)
    else:
        print("  [-] pdf2docx: neni (pip install pdf2docx)", flush=True)

    if _has_ocr:
        print("  [+] Tesseract OCR: dostupne (skenovane PDF)", flush=True)
    else:
        print("  [-] Tesseract OCR: neni (pip install pytesseract pdf2image Pillow)", flush=True)

    # Parsuj argumenty - podpora --dpi a --lang
    args = sys.argv[1:]
    dpi = 300
    lang = "ces"
    pdf_files = []

    i = 0
    while i < len(args):
        if args[i] == '--dpi' and i + 1 < len(args):
            dpi = int(args[i + 1])
            i += 2
        elif args[i] == '--lang' and i + 1 < len(args):
            lang = args[i + 1]
            i += 2
        else:
            pdf_files.append(args[i])
            i += 1

    if not pdf_files:
        print("\nERROR: Nebyl zadan PDF soubor", flush=True)
        print("Pouziti: python pdf2docx_cli.py <cesta_k_pdf> [--dpi 400] [--lang ces+eng]", flush=True)
        sys.exit(1)

    success_count = 0
    total_count = 0

    for pdf_arg in pdf_files:
        total_count += 1
        pdf_path = Path(pdf_arg)

        print(f"\nZpracovavam ({total_count}): {pdf_path.name}", flush=True)

        if not pdf_path.exists():
            print(f"[!] Soubor neexistuje: {pdf_path}", flush=True)
            continue

        if pdf_path.suffix.lower() != ".pdf":
            print(f"[!] Soubor neni PDF: {pdf_path}", flush=True)
            continue

        if convert_pdf(pdf_path, dpi=dpi, lang=lang):
            success_count += 1
        else:
            print(f"[X] Konverze selhala pro: {pdf_path.name}", flush=True)

    print("\n" + "=" * 50, flush=True)
    print(f"VYSLEDEK: {success_count}/{total_count} souboru uspesne prevedeno", flush=True)

    exit_code = 0
    if success_count == total_count and total_count > 0:
        print("[OK] Vsechny soubory byly uspesne prevedeny!", flush=True)
    else:
        print("[!] Nektere soubory nebyly prevedeny", flush=True)
        exit_code = 1

    if not os.environ.get('NO_PAUSE'):
        try:
            input("\nStiskni Enter pro ukonceni...")
        except (EOFError, KeyboardInterrupt):
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
