"""
Deploy script - nahradí původní Python soubory obfuskovanými verzemi

VAROVÁNÍ: Tento skript přepíše vaše Python soubory!
Před spuštěním se ujisti že máš zálohu.
"""

import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).parent
DIST = ROOT / "dist_obfuscated"
BACKUP = ROOT / "backup_original"

# Soubory k nahrazení
FILES_TO_REPLACE = [
    "validate_license_cli.py",
    "anonymize_cli.py",
    "deanonymizator_lokal.py",
    "pdf2docx_cli.py",
]

# Moduly k nahrazení
MODULES_TO_REPLACE = [
    "licensing",
]

# Runtime složka
RUNTIME = "pyarmor_runtime_000000"


def main():
    print("=" * 60)
    print("PyArmor Deploy Script")
    print("=" * 60)
    print()
    print("⚠️  VAROVÁNÍ: Tento skript přepíše Python soubory!")
    print("Původní soubory budou zazálohovány do backup_original/")
    print()

    # Zkontroluj že dist existuje
    if not DIST.exists():
        print("❌ Chyba: Složka dist_obfuscated/ neexistuje!")
        print("   Nejdříve spusť: python build_obfuscated.py")
        sys.exit(1)

    # Potvrzení
    response = input("Pokračovat? (ano/ne): ").strip().lower()
    if response not in ["ano", "a", "yes", "y"]:
        print("Zrušeno.")
        sys.exit(0)

    # Vytvoř backup složku
    if not BACKUP.exists():
        BACKUP.mkdir()
        print(f"\n📁 Vytvořena backup složka: {BACKUP}")
    else:
        print(f"\n📁 Použita existující backup složka: {BACKUP}")

    # Backup souborů
    print(f"\n{'=' * 60}")
    print("1. Zálohování původních souborů")
    print("=" * 60)

    for file in FILES_TO_REPLACE:
        src = ROOT / file
        if src.exists():
            dst = BACKUP / file
            shutil.copy2(src, dst)
            print(f"💾 Zazálohován: {file}")

    # Backup modulů
    for module in MODULES_TO_REPLACE:
        src = ROOT / module
        if src.exists():
            dst = BACKUP / module
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print(f"💾 Zazálohován modul: {module}")

    # Nahrazení souborů
    print(f"\n{'=' * 60}")
    print("2. Nahrazování obfuskovanými soubory")
    print("=" * 60)

    for file in FILES_TO_REPLACE:
        src = DIST / file
        dst = ROOT / file
        if src.exists():
            shutil.copy2(src, dst)
            print(f"🔒 Nahrazen: {file}")
        else:
            print(f"⚠️  Soubor nenalezen v dist: {file}")

    # Nahrazení modulů
    for module in MODULES_TO_REPLACE:
        src = DIST / module
        dst = ROOT / module
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print(f"🔒 Nahrazen modul: {module}")
        else:
            print(f"⚠️  Modul nenalezen v dist: {module}")

    # Kopírování runtime
    print(f"\n{'=' * 60}")
    print("3. Instalace PyArmor runtime")
    print("=" * 60)

    src_runtime = DIST / RUNTIME
    dst_runtime = ROOT / RUNTIME

    if src_runtime.exists():
        if dst_runtime.exists():
            shutil.rmtree(dst_runtime)
        shutil.copytree(src_runtime, dst_runtime)
        print(f"✅ Runtime nainstalován: {RUNTIME}")
    else:
        print(f"❌ Runtime nenalezen: {src_runtime}")
        print("   Aplikace nebude fungovat bez runtime!")

    print(f"\n{'=' * 60}")
    print("✅ DEPLOY DOKONČEN!")
    print("=" * 60)
    print()
    print("✅ Všechny Python soubory jsou nyní obfuskovány")
    print(f"💾 Záloha původních souborů: {BACKUP}")
    print()
    print("Další kroky:")
    print("1. Restartuj aplikaci: electron . --enable-logging")
    print("2. Otestuj všechny funkce (anonymizace, deanonymizace, licence)")
    print("3. Pokud něco nefunguje, obnov zálohu:")
    print(f"   cp -r {BACKUP}/* .")


if __name__ == "__main__":
    main()
