"""
Build script pro obfuskaci Python kódu pomocí PyArmor

Tento skript:
1. Obfuskuje licensing modul
2. Obfuskuje core CLI skripty (anonymize, deanonymize, pdf2docx)
3. Vytvoří dist/ složku s obfuskovanými soubory
"""

import os
import shutil
from pathlib import Path
import subprocess
import sys

# Root projektu
ROOT = Path(__file__).parent

# Soubory k obfuskaci
FILES_TO_OBFUSCATE = [
    "validate_license_cli.py",
    "anonymize_cli.py",
    "deanonymizator_lokal.py",
    "pdf2docx_cli.py",
]

# Moduly k obfuskaci (složky)
MODULES_TO_OBFUSCATE = [
    "licensing",
]

# Výstupní složka
DIST_DIR = ROOT / "dist_obfuscated"


def run_pyarmor(cmd):
    """Spusť PyArmor příkaz"""
    print(f"\n▶ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Chyba: {result.stderr}")
        sys.exit(1)
    print(f"✅ Hotovo")
    return result.stdout


def main():
    print("=" * 60)
    print("PyArmor Build Script - SKRYI Document Suite")
    print("=" * 60)

    # Vyčisti dist složku
    if DIST_DIR.exists():
        print(f"\n🗑️  Mažu starou dist složku: {DIST_DIR}")
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(exist_ok=True)
    print(f"\n📁 Vytvořena dist složka: {DIST_DIR}")

    # Obfuskuj jednotlivé soubory
    print(f"\n{'=' * 60}")
    print("1. Obfuskace jednotlivých souborů")
    print("=" * 60)

    for file in FILES_TO_OBFUSCATE:
        file_path = ROOT / file
        if not file_path.exists():
            print(f"⚠️  Soubor nenalezen, přeskakuji: {file}")
            continue

        print(f"\n🔒 Obfuskuji: {file}")

        # PyArmor 9 příkaz pro obfuskaci
        cmd = [
            "pyarmor",
            "gen",
            "--output", str(DIST_DIR),
            "--recursive",
            str(file_path)
        ]

        run_pyarmor(cmd)

    # Obfuskuj moduly (složky)
    print(f"\n{'=' * 60}")
    print("2. Obfuskace modulů")
    print("=" * 60)

    for module in MODULES_TO_OBFUSCATE:
        module_path = ROOT / module
        if not module_path.exists():
            print(f"⚠️  Modul nenalezen, přeskakuji: {module}")
            continue

        print(f"\n🔒 Obfuskuji modul: {module}")

        # Vytvoř cílovou složku v dist
        dist_module = DIST_DIR / module
        dist_module.mkdir(exist_ok=True, parents=True)

        # Obfuskuj všechny .py soubory v modulu
        cmd = [
            "pyarmor",
            "gen",
            "--output", str(dist_module),
            "--recursive",
            str(module_path)
        ]

        run_pyarmor(cmd)

    # Kopíruj ostatní potřebné soubory
    print(f"\n{'=' * 60}")
    print("3. Kopírování ostatních souborů")
    print("=" * 60)

    files_to_copy = [
        "main.js",
        "index.html",
        "package.json",
        "package-lock.json",
        "get_hw_id.py",  # Tento NENÍ obfuskovaný - zákazník ho potřebuje spustit
    ]

    for file in files_to_copy:
        src = ROOT / file
        if src.exists():
            dst = DIST_DIR / file
            shutil.copy2(src, dst)
            print(f"📄 Zkopírován: {file}")

    # Kopíruj složky
    folders_to_copy = [
        "node_modules",  # Pokud existuje
        "venv",  # Pokud existuje
    ]

    for folder in folders_to_copy:
        src = ROOT / folder
        if src.exists():
            dst = DIST_DIR / folder
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print(f"📁 Zkopírována složka: {folder}")

    print(f"\n{'=' * 60}")
    print("✅ BUILD DOKONČEN!")
    print("=" * 60)
    print(f"\nObfuskované soubory jsou v: {DIST_DIR}")
    print("\nDalší kroky:")
    print("1. Otestuj aplikaci ve složce dist_obfuscated/")
    print("2. Pokud vše funguje, nahraď produkční soubory obfuskovanými verzemi")
    print("3. Pro distribuci zákazníkovi zabal obsah dist_obfuscated/ složky")


if __name__ == "__main__":
    main()
