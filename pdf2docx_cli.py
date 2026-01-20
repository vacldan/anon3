# pdf2docx_cli.py - Enhanced for Electron integration
import sys
import os
from pathlib import Path

# Set UTF-8 encoding - safe cross-platform approach
if sys.platform == 'win32':
    # Only reconfigure on Windows if needed
    import io
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
else:
    # On Unix/Linux, ensure PYTHONIOENCODING is set via environment
    pass

try:
    from pdf2docx import Converter
except ImportError:
    print("ERROR: pdf2docx library není nainstalována!")
    print("Nainstalujte pomocí: pip install pdf2docx")
    sys.exit(1)

def convert_pdf(pdf_path: Path):
    """Convert PDF to DOCX"""
    try:
        docx_path = pdf_path.with_suffix('.docx')
        
        print(f"Zpracovavam PDF: {pdf_path.name}")
        print(f"Vystupni DOCX: {docx_path.name}")
        
        # Check if PDF exists
        if not pdf_path.exists():
            print(f"ERROR: PDF soubor neexistuje: {pdf_path}")
            return False
            
        # Check if PDF is readable
        if pdf_path.stat().st_size == 0:
            print(f"ERROR: PDF soubor je prázdný: {pdf_path}")
            return False
            
        print("Spoustim konverzi...")
        
        # Create converter
        cv = Converter(str(pdf_path))
        
        # Convert with progress feedback
        cv.convert(str(docx_path), start=0, end=None)
        cv.close()
        
        # Verify output
        if docx_path.exists() and docx_path.stat().st_size > 0:
            print(f"✅ Uspesne prevedeno: {docx_path.name}")
            print(f"Velikost vystupniho souboru: {docx_path.stat().st_size} bytů")
            return True
        else:
            print("ERROR: DOCX soubor nebyl vytvořen nebo je prázdný")
            return False
            
    except Exception as e:
        print(f"ERROR: Chyba při konverzi: {e}")
        return False

def main():
    print("PDF to DOCX Converter - Nixminds Document Suite")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("ERROR: Nebyl zadán PDF soubor")
        print("Použití: python pdf2docx_cli.py <cesta_k_pdf>")
        sys.exit(1)
    
    success_count = 0
    total_count = 0
    
    for pdf_arg in sys.argv[1:]:
        total_count += 1
        pdf_path = Path(pdf_arg)
        
        print(f"\nZpracovavam ({total_count}): {pdf_path.name}")
        
        if not pdf_path.exists():
            print(f"⚠️  Soubor neexistuje: {pdf_path}")
            continue
            
        if pdf_path.suffix.lower() != ".pdf":
            print(f"⚠️  Soubor není PDF: {pdf_path}")
            continue
            
        if convert_pdf(pdf_path):
            success_count += 1
        else:
            print(f"❌ Konverze selhala pro: {pdf_path.name}")
    
    print("\n" + "=" * 50)
    print(f"VÝSLEDEK: {success_count}/{total_count} souborů úspěšně převedeno")

    exit_code = 0
    if success_count == total_count and total_count > 0:
        print("✅ Všechny soubory byly úspěšně převedeny!")
        exit_code = 0
    else:
        print("⚠️  Některé soubory nebyly převedeny")
        exit_code = 1

    # Počkej na Enter před ukončením (pro drag & drop režim)
    # Pokud je nastavena proměnná NO_PAUSE (z Electronu), přeskoč čekání
    if not os.environ.get('NO_PAUSE'):
        try:
            input("\nStiskni Enter pro ukončení...")
        except (EOFError, KeyboardInterrupt):
            pass

    sys.exit(exit_code)

if __name__ == "__main__":
    main()