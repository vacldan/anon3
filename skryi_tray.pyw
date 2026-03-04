#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKRYI Tray Icon
===============
Systémová ikona pro SKRYI folder watcher.
Běží na pozadí, zobrazuje status a umožňuje rychlý přístup ke složkám.

Použití .pyw přípony = spustí se bez konzolového okna na Windows.
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path

# Pokus o import pystray (pro systémovou ikonu)
try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("pystray není nainstalován. Spusťte: pip install pystray pillow")

# Pokus o import PIL pro ikonu
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Pillow není nainstalován. Spusťte: pip install pillow")

# =============================================================================
# KONFIGURACE
# =============================================================================

def get_skryi_base_folder():
    """Vrátí základní SKRYI složku v Dokumentech uživatele."""
    documents = Path.home() / "Documents"
    if not documents.exists():
        documents = Path.home() / "Dokumenty"
    if not documents.exists():
        documents = Path.home()
    return documents / "SKRYI"

BASE_FOLDER = get_skryi_base_folder()
IN_FOLDER = BASE_FOLDER / "IN"
OUT_FOLDER = BASE_FOLDER / "OUT"
STATUS_FILE = BASE_FOLDER / ".status"

# =============================================================================
# IKONA
# =============================================================================

def create_icon_image(color='green'):
    """Vytvoří jednoduchou ikonu jako PIL Image."""
    if not PIL_AVAILABLE:
        return None

    # Barvy podle stavu
    colors = {
        'green': '#4CAF50',   # Běží
        'yellow': '#FFC107',  # Zpracovává
        'red': '#F44336',     # Chyba
        'gray': '#9E9E9E'     # Zastaveno
    }

    bg_color = colors.get(color, colors['gray'])

    # Vytvoř 64x64 ikonu
    size = 64
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Kruh jako pozadí
    draw.ellipse([4, 4, size-4, size-4], fill=bg_color)

    # Písmeno S uprostřed
    try:
        from PIL import ImageFont
        # Pokus o načtení fontu
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()

        # Získej velikost textu
        bbox = draw.textbbox((0, 0), "S", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size - text_width) // 2
        y = (size - text_height) // 2 - 4

        draw.text((x, y), "S", fill='white', font=font)
    except:
        # Fallback - jednoduchý text
        draw.text((22, 16), "S", fill='white')

    return image

# =============================================================================
# WATCHER PROCES
# =============================================================================

class WatcherManager:
    """Správce watcher procesu."""

    def __init__(self):
        self.process = None
        self.running = False

    def start(self):
        """Spustí watcher proces."""
        if self.running:
            return

        # Najdi skryi_watcher.py nebo .exe
        watcher_script = Path(__file__).parent / "skryi_watcher.py"
        watcher_exe = Path(__file__).parent / "skryi_watcher.exe"

        if watcher_exe.exists():
            self.process = subprocess.Popen(
                [str(watcher_exe)],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        elif watcher_script.exists():
            self.process = subprocess.Popen(
                [sys.executable, str(watcher_script)],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        else:
            print("Watcher skript nenalezen!")
            return

        self.running = True

    def stop(self):
        """Zastaví watcher proces."""
        if self.process:
            self.process.terminate()
            self.process = None
        self.running = False

    def is_running(self):
        """Zkontroluje zda watcher běží."""
        if self.process:
            poll = self.process.poll()
            if poll is not None:
                self.running = False
                self.process = None
        return self.running

# =============================================================================
# STATUS MONITORING
# =============================================================================

def get_status():
    """Načte aktuální status ze souboru."""
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {'status': 'unknown', 'message': 'Status neznámý'}

# =============================================================================
# MENU AKCE
# =============================================================================

def open_in_folder():
    """Otevře IN složku v průzkumníku."""
    IN_FOLDER.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'win32':
        os.startfile(str(IN_FOLDER))
    else:
        subprocess.run(['xdg-open', str(IN_FOLDER)])

def open_out_folder():
    """Otevře OUT složku v průzkumníku."""
    OUT_FOLDER.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'win32':
        os.startfile(str(OUT_FOLDER))
    else:
        subprocess.run(['xdg-open', str(OUT_FOLDER)])

def open_base_folder():
    """Otevře hlavní SKRYI složku."""
    BASE_FOLDER.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'win32':
        os.startfile(str(BASE_FOLDER))
    else:
        subprocess.run(['xdg-open', str(BASE_FOLDER)])

# =============================================================================
# HLAVNÍ TRAY APLIKACE
# =============================================================================

class SKRYITray:
    """Hlavní třída pro systémovou ikonu."""

    def __init__(self):
        self.watcher = WatcherManager()
        self.icon = None
        self.running = True

    def create_menu(self):
        """Vytvoří menu pro systémovou ikonu."""
        status = get_status()
        status_text = f"Status: {status.get('message', 'Neznámý')}"

        return pystray.Menu(
            item(status_text, lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            item('Otevřít IN složku', lambda: open_in_folder()),
            item('Otevřít OUT složku', lambda: open_out_folder()),
            item('Otevřít SKRYI složku', lambda: open_base_folder()),
            pystray.Menu.SEPARATOR,
            item(
                'Spustit watcher',
                lambda: self.start_watcher(),
                visible=lambda item: not self.watcher.is_running()
            ),
            item(
                'Zastavit watcher',
                lambda: self.stop_watcher(),
                visible=lambda item: self.watcher.is_running()
            ),
            pystray.Menu.SEPARATOR,
            item('Ukončit SKRYI', lambda: self.quit())
        )

    def start_watcher(self):
        """Spustí watcher."""
        self.watcher.start()
        self.update_icon()

    def stop_watcher(self):
        """Zastaví watcher."""
        self.watcher.stop()
        self.update_icon()

    def update_icon(self):
        """Aktualizuje ikonu podle stavu."""
        if self.icon:
            if self.watcher.is_running():
                self.icon.icon = create_icon_image('green')
                self.icon.title = "SKRYI - Běží"
            else:
                self.icon.icon = create_icon_image('gray')
                self.icon.title = "SKRYI - Zastaveno"

    def quit(self):
        """Ukončí aplikaci."""
        self.running = False
        self.watcher.stop()
        if self.icon:
            self.icon.stop()

    def status_monitor(self):
        """Monitoruje status a aktualizuje ikonu."""
        while self.running:
            time.sleep(5)
            if self.icon:
                # Aktualizuj menu
                self.icon.menu = self.create_menu()

                # Aktualizuj ikonu podle stavu
                status = get_status()
                if status.get('status') == 'processing':
                    self.icon.icon = create_icon_image('yellow')
                elif status.get('status') == 'error':
                    self.icon.icon = create_icon_image('red')
                elif self.watcher.is_running():
                    self.icon.icon = create_icon_image('green')
                else:
                    self.icon.icon = create_icon_image('gray')

    def run(self):
        """Spustí tray aplikaci."""
        if not PYSTRAY_AVAILABLE or not PIL_AVAILABLE:
            print("Chybí potřebné knihovny (pystray, pillow)")
            print("Spusťte: pip install pystray pillow")
            return

        # Vytvoř ikonu
        icon_image = create_icon_image('gray')

        self.icon = pystray.Icon(
            'SKRYI',
            icon_image,
            'SKRYI Document Suite',
            menu=self.create_menu()
        )

        # Spusť status monitor ve vedlejším vlákně
        monitor_thread = threading.Thread(target=self.status_monitor, daemon=True)
        monitor_thread.start()

        # Automaticky spusť watcher
        self.start_watcher()

        # Spusť ikonu (blokující volání)
        self.icon.run()

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Hlavní vstupní bod."""
    # Vytvoř složky pokud neexistují
    for folder in [BASE_FOLDER, IN_FOLDER, OUT_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)

    # Spusť tray aplikaci
    app = SKRYITray()
    app.run()

if __name__ == '__main__':
    main()
