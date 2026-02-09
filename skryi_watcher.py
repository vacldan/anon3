#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKRYI Folder Watcher Service
============================
Automaticky monitoruje složku IN a zpracovává dokumenty.

Event-based monitoring (ne polling) - reaguje okamžitě na nové soubory.
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

# Základní složka (Dokumenty/SKRYI)
def get_skryi_base_folder():
    """Vrátí základní SKRYI složku v Dokumentech uživatele."""
    documents = Path.home() / "Documents"
    if not documents.exists():
        documents = Path.home() / "Dokumenty"  # Czech Windows
    if not documents.exists():
        documents = Path.home()
    return documents / "SKRYI"

BASE_FOLDER = get_skryi_base_folder()
ANON_FOLDER = BASE_FOLDER / "01_ANONYMIZACE"
IN_FOLDER = ANON_FOLDER / "IN"
OUT_FOLDER = ANON_FOLDER / "OUT"
ERROR_FOLDER = BASE_FOLDER / "ERROR"
LOGS_FOLDER = BASE_FOLDER / "LOGS"

# Podporované formáty
SUPPORTED_EXTENSIONS = {'.docx', '.pdf'}

# Delay před zpracováním (čekáme až se soubor dokončí kopírovat)
PROCESS_DELAY_SECONDS = 2

# =============================================================================
# LOGGING
# =============================================================================

def setup_logging():
    """Nastaví logging do souboru a konzole."""
    LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

    log_file = LOGS_FOLDER / f"skryi_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('SKRYI')

# =============================================================================
# ZPRACOVÁNÍ DOKUMENTŮ
# =============================================================================

def get_app_install_path():
    """Najde instalační složku SKRYI Document Suite."""
    possible_paths = [
        # Standardní instalace x64
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
    """Najde cestu ke skriptu (preferuje .exe před .py)."""
    exe_name = script_name.replace('.py', '.exe')

    # Zkusíme najít v různých lokacích
    # DŮLEŽITÉ: Preferujeme lokální soubory před instalační složkou,
    # aby se používala nejnovější verze (stejně jako GUI v main.js)
    possible_paths = []

    # 1. Vedle tohoto skriptu (PRIORITA - lokální verze)
    possible_paths.append(Path(__file__).parent / exe_name)
    possible_paths.append(Path(__file__).parent / script_name)

    # 2. Vedle sys.executable (pro zkompilovanou verzi watcheru)
    possible_paths.append(Path(sys.executable).parent / exe_name)
    possible_paths.append(Path(sys.executable).parent / script_name)

    # 3. V instalační složce aplikace (fallback)
    install_path = get_app_install_path()
    if install_path:
        possible_paths.append(install_path / exe_name)
        possible_paths.append(install_path / script_name)

    for p in possible_paths:
        if p.exists():
            return p

    return None

def process_document(file_path, logger):
    """
    Zpracuje jeden dokument - anonymizace.

    Args:
        file_path: Cesta k souboru
        logger: Logger instance

    Returns:
        bool: True pokud úspěch, False pokud chyba
    """
    file_path = Path(file_path)
    logger.info(f"Zpracovávám: {file_path.name}")

    try:
        # Kontrola přípony
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.warning(f"Nepodporovaný formát: {file_path.suffix}")
            return False

        # PDF -> DOCX konverze pokud je potřeba
        working_file = file_path
        if file_path.suffix.lower() == '.pdf':
            logger.info("Konvertuji PDF na DOCX...")
            pdf2docx_script = get_script_path('pdf2docx_cli.py')

            if pdf2docx_script and pdf2docx_script.exists():
                if pdf2docx_script.suffix == '.exe':
                    result = subprocess.run(
                        [str(pdf2docx_script), str(file_path)],
                        capture_output=True, text=True, timeout=300
                    )
                else:
                    result = subprocess.run(
                        [sys.executable, str(pdf2docx_script), str(file_path)],
                        capture_output=True, text=True, timeout=300
                    )

                if result.returncode != 0:
                    logger.error(f"PDF konverze selhala: {result.stderr}")
                    return False

                # Najdi vytvořený DOCX
                docx_path = file_path.with_suffix('.docx')
                if docx_path.exists():
                    working_file = docx_path
                else:
                    logger.error("DOCX soubor nebyl vytvořen po PDF konverzi")
                    return False
            else:
                logger.error("pdf2docx_cli nenalezen")
                return False

        # Anonymizace
        logger.info("Anonymizuji dokument...")
        anonymize_script = get_script_path('anonymize_cli.py')

        if not anonymize_script or not anonymize_script.exists():
            install_path = get_app_install_path()
            logger.error(f"anonymize_cli nenalezen! Install path: {install_path}")
            return False

        logger.info(f"Pouzivam CLI: {anonymize_script}")

        # Připrav výstupní cesty - přímo do OUT složky (ne do IN!)
        base_name = working_file.stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        anon_file = OUT_FOLDER / f"{base_name}_{timestamp}_anon.docx"
        map_json = OUT_FOLDER / f"{base_name}_{timestamp}_map.json"
        map_txt = OUT_FOLDER / f"{base_name}_{timestamp}_map.txt"

        # Volání s korektními argumenty
        cli_args = [
            str(anonymize_script),
            "--input", str(working_file),
            "--output", str(anon_file),
            "--map", str(map_json),
            "--map_txt", str(map_txt)
        ]

        if anonymize_script.suffix == '.exe':
            result = subprocess.run(
                cli_args,
                capture_output=True, text=True, timeout=600
            )
        else:
            result = subprocess.run(
                [sys.executable] + cli_args,
                capture_output=True, text=True, timeout=600
            )

        if result.returncode != 0:
            logger.error(f"Anonymizace selhala: {result.stderr}")
            logger.error(f"STDOUT: {result.stdout}")
            return False

        # Zkontroluj výstupy (jsou přímo v OUT složce)
        files_created = []

        if anon_file.exists():
            files_created.append(anon_file.name)
            logger.info(f"Výstup: {anon_file.name}")

        if map_json.exists():
            files_created.append(map_json.name)

        if map_txt.exists():
            files_created.append(map_txt.name)

        # Smaž originál z IN (nebo přesuň do PROCESSED)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Originál smazán: {file_path.name}")

        # Smaž dočasný DOCX z PDF konverze
        if working_file != file_path and working_file.exists():
            working_file.unlink()

        logger.info(f"Úspěšně zpracováno: {file_path.name} -> {len(files_created)} souborů")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout při zpracování: {file_path.name}")
        return False
    except Exception as e:
        logger.error(f"Chyba při zpracování {file_path.name}: {e}")
        return False

def move_to_error(file_path, logger, error_msg=""):
    """Přesune soubor do ERROR složky."""
    try:
        file_path = Path(file_path)
        if file_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest = ERROR_FOLDER / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            shutil.move(str(file_path), str(dest))
            logger.warning(f"Přesunuto do ERROR: {dest.name}")

            # Zapiš error log
            error_log = ERROR_FOLDER / f"{file_path.stem}_{timestamp}_error.txt"
            with open(error_log, 'w', encoding='utf-8') as f:
                f.write(f"Soubor: {file_path.name}\n")
                f.write(f"Čas: {datetime.now().isoformat()}\n")
                f.write(f"Chyba: {error_msg}\n")
    except Exception as e:
        logger.error(f"Nelze přesunout do ERROR: {e}")

# =============================================================================
# FILE SYSTEM WATCHER
# =============================================================================

class SKRYIHandler(FileSystemEventHandler):
    """Handler pro události file systému."""

    def __init__(self, logger):
        self.logger = logger
        self.processing = set()  # Soubory, které se právě zpracovávají
        self.pending = {}  # Soubory čekající na zpracování {path: timestamp}

    def on_created(self, event):
        """Volá se když je vytvořen nový soubor."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Kontrola přípony
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        # Ignoruj dočasné soubory
        if file_path.name.startswith('~') or file_path.name.startswith('.'):
            return

        # Ignoruj výstupní soubory (prevence zpracování vlastního výstupu)
        if '_anon' in file_path.stem or '_map' in file_path.stem:
            return

        self.logger.info(f"Nový soubor detekován: {file_path.name}")

        # Přidej do pending s časovým razítkem
        self.pending[str(file_path)] = time.time()

    def on_modified(self, event):
        """Volá se když je soubor modifikován (např. stále se kopíruje)."""
        if event.is_directory:
            return

        file_path = str(event.src_path)
        if file_path in self.pending:
            # Aktualizuj timestamp - soubor se stále mění
            self.pending[file_path] = time.time()

    def process_pending(self):
        """Zpracuje soubory, které jsou připraveny (už se nekopírují)."""
        now = time.time()
        to_process = []

        for file_path, timestamp in list(self.pending.items()):
            # Počkej PROCESS_DELAY_SECONDS od poslední modifikace
            if now - timestamp >= PROCESS_DELAY_SECONDS:
                if file_path not in self.processing:
                    to_process.append(file_path)

        for file_path in to_process:
            self.processing.add(file_path)
            del self.pending[file_path]

            # Zpracuj soubor
            success = process_document(file_path, self.logger)

            if not success:
                move_to_error(file_path, self.logger, "Zpracování selhalo")

            self.processing.discard(file_path)

# =============================================================================
# HLAVNÍ SMYČKA
# =============================================================================

def create_folders():
    """Vytvori potrebne slozky."""
    for folder in [BASE_FOLDER, ANON_FOLDER, IN_FOLDER, OUT_FOLDER, ERROR_FOLDER, LOGS_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)

    # Vytvor info soubor v IN slozce
    info_file = IN_FOLDER / "POUZITI.txt"
    if not info_file.exists():
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("SKRYI Document Suite - 01_ANONYMIZACE\n")
            f.write("=" * 50 + "\n\n")
            f.write("JAK POUZIVAT:\n")
            f.write("-" * 50 + "\n")
            f.write("1. Vloz dokument (DOCX nebo PDF) do teto slozky\n")
            f.write("2. Pockej par sekund\n")
            f.write("3. Anonymizovany dokument + JSON mapu najdes ve slozce OUT\n\n")
            f.write("(c) 2026 Nixminds s.r.o.\n")

def write_status(status, message=""):
    """Zapíše status do souboru (pro tray ikonu)."""
    status_file = BASE_FOLDER / ".status"
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
    print("SKRYI Document Suite - Anonymization Folder Watcher")
    print("=" * 60)

    # Vytvor slozky
    create_folders()
    print(f"\nSlozky vytvoreny v: {BASE_FOLDER}")
    print(f"  01_ANONYMIZACE/IN:  {IN_FOLDER}")
    print(f"  01_ANONYMIZACE/OUT: {OUT_FOLDER}")
    print(f"  ERROR:              {ERROR_FOLDER}")
    print(f"  LOGS:               {LOGS_FOLDER}")

    # Nastav logging
    logger = setup_logging()
    logger.info("SKRYI Watcher spuštěn")

    # Vytvoř handler a observer
    handler = SKRYIHandler(logger)
    observer = Observer()
    observer.schedule(handler, str(IN_FOLDER), recursive=False)

    # Spusť observer
    observer.start()
    write_status('running', 'Monitoruji složku IN')

    print(f"\nMonitoruji složku: {IN_FOLDER}")
    print("Vložte dokument (DOCX/PDF) do složky IN pro anonymizaci.")
    print("Pro ukončení stiskněte Ctrl+C\n")

    try:
        while True:
            time.sleep(1)
            handler.process_pending()  # Zpracuj čekající soubory
    except KeyboardInterrupt:
        print("\nUkončuji...")
        write_status('stopped', 'Zastaveno uživatelem')
    finally:
        observer.stop()
        observer.join()
        logger.info("SKRYI Watcher ukončen")

if __name__ == '__main__':
    main()
