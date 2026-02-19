#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKRYI PDF to DOCX Folder Watcher Service
=========================================
Automaticky monitoruje slozku PDF_IN a prevadikonvertuje PDF na DOCX.

Pouziti:
1. Vloz PDF soubor do slozky PDF_IN
2. Pockej par sekund
3. Prevedeny DOCX najdes ve slozce PDF_OUT

Event-based monitoring (ne polling) - reaguje okamzite na nove soubory.
"""

import os
import sys
import time
import json
import shutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# =============================================================================
# KONFIGURACE
# =============================================================================

# Zakladni slozka (Dokumenty/SKRYI)
def get_skryi_base_folder():
    """Vrati zakladni SKRYI slozku v Dokumentech uzivatele."""
    documents = Path.home() / "Documents"
    if not documents.exists():
        documents = Path.home() / "Dokumenty"  # Czech Windows
    if not documents.exists():
        documents = Path.home()
    return documents / "SKRYI"

BASE_FOLDER = get_skryi_base_folder()
PDF_FOLDER = BASE_FOLDER / "03_KONVERZE_PDF"
IN_FOLDER = PDF_FOLDER / "IN"
OUT_FOLDER = PDF_FOLDER / "OUT"
ERROR_FOLDER = BASE_FOLDER / "ERROR"
LOGS_FOLDER = BASE_FOLDER / "LOGS"

# Podporovane formaty
SUPPORTED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp'}

# Delay pred zpracovanim (cekame az se soubor dokonci kopirovat)
PROCESS_DELAY_SECONDS = 2

# =============================================================================
# LOGGING
# =============================================================================

def setup_logging():
    """Nastavi logging do souboru a konzole."""
    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

    log_file = LOGS_FOLDER / f"pdf2docx_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('SKRYI_PDF')

# =============================================================================
# ZPRACOVANI DOKUMENTU
# =============================================================================

def get_app_install_path():
    """Najde instalacni slozku SKRYI Document Suite."""
    possible_paths = [
        # Standardni instalace x64
        Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'SKRYI Document Suite' / 'resources' / 'app.asar.unpacked',
        # Instalace x86
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / 'SKRYI Document Suite' / 'resources' / 'app.asar.unpacked',
        # LocalAppData (portable/user install)
        Path(os.environ.get('LOCALAPPDATA', '')) / 'SKRYI Document Suite' / 'resources' / 'app.asar.unpacked',
    ]

    for p in possible_paths:
        if p.exists():
            return p
    return None

def get_script_path(script_name):
    """Najde cestu ke skriptu (preferuje .exe pred .py)."""
    exe_name = script_name.replace('.py', '.exe')

    # Zkusime najit v ruznych lokacich
    possible_paths = []

    # 1. V instalacni slozce aplikace (PRIORITA pro nainstalovanou verzi)
    install_path = get_app_install_path()
    if install_path:
        possible_paths.append(install_path / exe_name)
        possible_paths.append(install_path / script_name)

    # 2. Vedle tohoto skriptu
    possible_paths.append(Path(__file__).parent / exe_name)
    possible_paths.append(Path(__file__).parent / script_name)

    # 3. Vedle sys.executable (pro zkompilovanou verzi)
    possible_paths.append(Path(sys.executable).parent / exe_name)
    possible_paths.append(Path(sys.executable).parent / script_name)

    for p in possible_paths:
        if p.exists():
            return p

    return None

def process_document(file_path, logger):
    """
    Zpracuje jeden dokument - PDF to DOCX konverze.

    Args:
        file_path: Cesta k PDF souboru
        logger: Logger instance

    Returns:
        bool: True pokud uspech, False pokud chyba
    """
    file_path = Path(file_path)
    logger.info(f"Zpracovavam: {file_path.name}")

    try:
        # Kontrola pripony
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.warning(f"Nepodporovany format: {file_path.suffix}")
            return False

        # PDF/obrazek -> DOCX konverze
        is_image = file_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp'}
        logger.info(f"Konvertuji {'obrazek' if is_image else 'PDF'} na DOCX...")
        pdf2docx_script = get_script_path('pdf2docx_cli.py')

        if not pdf2docx_script or not pdf2docx_script.exists():
            # Fallback: pouzij primo pdf2docx knihovnu
            logger.info("CLI nenalezeno, pouzivam primo pdf2docx knihovnu...")
            try:
                from pdf2docx import Converter

                docx_path = file_path.with_suffix('.docx')
                cv = Converter(str(file_path))
                cv.convert(str(docx_path), start=0, end=None)
                cv.close()

                if not docx_path.exists():
                    logger.error("DOCX soubor nebyl vytvoren")
                    return False

            except ImportError:
                logger.error("pdf2docx knihovna neni nainstalovana!")
                return False
            except Exception as e:
                logger.error(f"Chyba pri konverzi: {e}")
                return False
        else:
            logger.info(f"Pouzivam CLI: {pdf2docx_script}")

            # Nastav prostredi pro neinteraktivni rezim
            env = os.environ.copy()
            env['NO_PAUSE'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'

            if pdf2docx_script.suffix == '.exe':
                result = subprocess.run(
                    [str(pdf2docx_script), str(file_path)],
                    capture_output=True, text=True, timeout=300,
                    env=env
                )
            else:
                result = subprocess.run(
                    [sys.executable, str(pdf2docx_script), str(file_path)],
                    capture_output=True, text=True, timeout=300,
                    env=env
                )

            if result.returncode != 0:
                logger.error(f"Konverze selhala: {result.stderr}")
                logger.error(f"STDOUT: {result.stdout}")
                return False

        # Najdi vytvoreny DOCX
        docx_path = file_path.with_suffix('.docx')
        if not docx_path.exists():
            logger.error("DOCX soubor nebyl vytvoren po konverzi")
            return False

        # Presun vystup do OUT slozky
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = file_path.stem

        dest = OUT_FOLDER / f"{base_name}_{timestamp}.docx"
        shutil.move(str(docx_path), str(dest))
        logger.info(f"Vystup: {dest.name}")

        # Smaz original z IN
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Original smazan: {file_path.name}")

        logger.info(f"Uspesne zpracovano: {file_path.name} -> {dest.name}")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout pri zpracovani: {file_path.name}")
        return False
    except Exception as e:
        logger.error(f"Chyba pri zpracovani {file_path.name}: {e}")
        return False

def move_to_error(file_path, logger, error_msg=""):
    """Presune soubor do ERROR slozky."""
    try:
        file_path = Path(file_path)
        if file_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest = ERROR_FOLDER / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            shutil.move(str(file_path), str(dest))
            logger.warning(f"Presunuto do ERROR: {dest.name}")

            # Zapis error log
            error_log = ERROR_FOLDER / f"{file_path.stem}_{timestamp}_error.txt"
            with open(error_log, 'w', encoding='utf-8') as f:
                f.write(f"Soubor: {file_path.name}\n")
                f.write(f"Cas: {datetime.now().isoformat()}\n")
                f.write(f"Chyba: {error_msg}\n")
    except Exception as e:
        logger.error(f"Nelze presunout do ERROR: {e}")

# =============================================================================
# FILE SYSTEM WATCHER
# =============================================================================

class PDFHandler(FileSystemEventHandler):
    """Handler pro udalosti file systemu."""

    def __init__(self, logger):
        self.logger = logger
        self.processing = set()  # Soubory, ktere se prave zpracovavaji
        self.pending = {}  # Soubory cekajici na zpracovani {path: timestamp}

    def on_created(self, event):
        """Vola se kdyz je vytvoren novy soubor."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Kontrola pripony
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        # Ignoruj docasne soubory
        if file_path.name.startswith('~') or file_path.name.startswith('.'):
            return

        self.logger.info(f"Novy soubor detekovan: {file_path.name}")

        # Pridej do pending s casovym razitkem
        self.pending[str(file_path)] = time.time()

    def on_modified(self, event):
        """Vola se kdyz je soubor modifikovan (napr. stale se kopiruje)."""
        if event.is_directory:
            return

        file_path = str(event.src_path)
        if file_path in self.pending:
            # Aktualizuj timestamp - soubor se stale meni
            self.pending[file_path] = time.time()

    def process_pending(self):
        """Zpracuje soubory, ktere jsou pripraveny (uz se nekopiruj)."""
        now = time.time()
        to_process = []

        for file_path, timestamp in list(self.pending.items()):
            # Pockej PROCESS_DELAY_SECONDS od posledni modifikace
            if now - timestamp >= PROCESS_DELAY_SECONDS:
                if file_path not in self.processing:
                    to_process.append(file_path)

        for file_path in to_process:
            self.processing.add(file_path)
            del self.pending[file_path]

            # Zpracuj soubor
            success = process_document(file_path, self.logger)

            if not success:
                move_to_error(file_path, self.logger, "Zpracovani selhalo")

            self.processing.discard(file_path)

# =============================================================================
# HLAVNI SMYCKA
# =============================================================================

def create_folders():
    """Vytvori potrebne slozky."""
    for folder in [BASE_FOLDER, PDF_FOLDER, IN_FOLDER, OUT_FOLDER, ERROR_FOLDER, LOGS_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)

    # Vytvor info soubor v IN slozce
    info_file = IN_FOLDER / "POUZITI.txt"
    if not info_file.exists():
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("SKRYI Document Suite - 03_KONVERZE_PDF\n")
            f.write("=" * 50 + "\n\n")
            f.write("JAK POUZIVAT:\n")
            f.write("-" * 50 + "\n")
            f.write("1. Vloz PDF nebo obrazek do teto slozky\n")
            f.write("2. Pockej par sekund\n")
            f.write("3. Prevedeny DOCX najdes ve slozce OUT\n\n")
            f.write("PODPOROVANE FORMATY:\n")
            f.write("-" * 50 + "\n")
            f.write("- PDF (textove i skenovane)\n")
            f.write("- Obrazky: PNG, JPG, JPEG, TIFF, TIF, BMP, WEBP\n\n")
            f.write("POZNAMKY:\n")
            f.write("-" * 50 + "\n")
            f.write("- Konverze zachovava formatovani pokud mozno\n")
            f.write("- Slozite tabulky mohou vyzadovat rucni upravu\n\n")
            f.write("(c) 2026 Nixminds s.r.o.\n")

def write_status(status, message=""):
    """Zapise status do souboru (pro tray ikonu)."""
    status_file = BASE_FOLDER / ".pdf_status"
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                'status': status,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'in_folder': str(IN_FOLDER),
                'out_folder': str(OUT_FOLDER)
            }, f)
    except:
        pass

def main():
    """Hlavni funkce - spusti watcher."""
    print("=" * 60)
    print("SKRYI Document Suite - PDF to DOCX Folder Watcher")
    print("=" * 60)

    # Vytvor slozky
    create_folders()
    print(f"\nSlozky vytvoreny v: {BASE_FOLDER}")
    print(f"  03_KONVERZE_PDF/IN:  {IN_FOLDER}")
    print(f"  03_KONVERZE_PDF/OUT: {OUT_FOLDER}")
    print(f"  ERROR:               {ERROR_FOLDER}")
    print(f"  LOGS:                {LOGS_FOLDER}")

    # Nastav logging
    logger = setup_logging()
    logger.info("SKRYI PDF Watcher spusten")

    # Vytvor handler a observer
    handler = PDFHandler(logger)
    observer = Observer()
    observer.schedule(handler, str(IN_FOLDER), recursive=False)

    # Spust observer
    observer.start()
    write_status('running', 'Monitoruji slozku PDF_IN')

    print(f"\nMonitoruji slozku: {IN_FOLDER}")
    print("Vlozte PDF nebo obrazek do slozky IN pro konverzi na DOCX.")
    print("Podporovane: PDF, PNG, JPG, JPEG, TIFF, TIF, BMP, WEBP")
    print("Pro ukonceni stisknete Ctrl+C\n")

    try:
        while True:
            time.sleep(1)
            handler.process_pending()  # Zpracuj cekajici soubory
    except KeyboardInterrupt:
        print("\nUkoncuji...")
        write_status('stopped', 'Zastaveno uzivatelem')
    finally:
        observer.stop()
        observer.join()
        logger.info("SKRYI PDF Watcher ukoncen")

if __name__ == '__main__':
    main()
