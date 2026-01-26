"""
JavaScript Obfuscation Script
Chrání main.js před úpravami license checku
"""

import subprocess
import sys
from pathlib import Path
import shutil

ROOT = Path(__file__).parent
DIST = ROOT / "dist_obfuscated"

def check_npm_package(package):
    """Zkontroluj jestli je npm package nainstalovaný"""
    try:
        result = subprocess.run(
            ["npm", "list", package, "--depth=0"],
            capture_output=True,
            text=True,
            cwd=ROOT
        )
        return result.returncode == 0
    except:
        return False

def install_obfuscator():
    """Nainstaluj javascript-obfuscator"""
    print("📦 Instaluji javascript-obfuscator...")
    try:
        subprocess.run(
            ["npm", "install", "--save-dev", "javascript-obfuscator"],
            check=True,
            cwd=ROOT
        )
        print("✅ javascript-obfuscator nainstalován")
        return True
    except:
        print("❌ Nepodařilo se nainstalovat javascript-obfuscator")
        return False

def obfuscate_js(input_file, output_file):
    """Obfuskuj JavaScript soubor"""
    print(f"\n🔒 Obfuskuji: {input_file.name}")

    cmd = [
        "npx",
        "javascript-obfuscator",
        str(input_file),
        "--output", str(output_file),
        "--compact", "true",
        "--control-flow-flattening", "true",
        "--control-flow-flattening-threshold", "0.75",
        "--dead-code-injection", "true",
        "--dead-code-injection-threshold", "0.4",
        "--debug-protection", "false",
        "--disable-console-output", "false",
        "--identifier-names-generator", "hexadecimal",
        "--log", "false",
        "--rename-globals", "false",
        "--self-defending", "true",
        "--string-array", "true",
        "--string-array-encoding", "['base64']",
        "--string-array-threshold", "0.75",
        "--transform-object-keys", "true",
        "--unicode-escape-sequence", "false"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if result.returncode == 0:
            print(f"✅ Obfuskace úspěšná: {output_file.name}")
            return True
        else:
            print(f"❌ Chyba při obfuskaci: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return False

def main():
    print("=" * 60)
    print("JavaScript Obfuscation - SKRYI Document Suite")
    print("=" * 60)

    # Zkontroluj jestli je javascript-obfuscator nainstalován
    if not check_npm_package("javascript-obfuscator"):
        print("\n⚠️  javascript-obfuscator není nainstalován")
        response = input("Nainstalovat? (ano/ne): ").strip().lower()
        if response not in ["ano", "a", "yes", "y"]:
            print("Zrušeno.")
            sys.exit(0)
        if not install_obfuscator():
            sys.exit(1)

    # Vytvoř dist složku pokud neexistuje
    DIST.mkdir(exist_ok=True)

    # Obfuskuj main.js
    main_js = ROOT / "main.js"
    main_js_obf = DIST / "main.js"

    if not main_js.exists():
        print(f"\n❌ Chyba: {main_js} neexistuje")
        sys.exit(1)

    success = obfuscate_js(main_js, main_js_obf)

    # Zkopíruj index.html (neobfuskujeme, HTML je těžko čitelný i bez toho)
    print(f"\n📄 Kopíruji index.html...")
    shutil.copy2(ROOT / "index.html", DIST / "index.html")

    if success:
        print(f"\n{'=' * 60}")
        print("✅ JavaScript obfuskace dokončena!")
        print("=" * 60)
        print(f"\nObfuskované soubory v: {DIST}")
        print("\nDůležité:")
        print("- main.js je nyní obfuskovaný a self-defending")
        print("- Pokud někdo zkusí upravit kód, aplikace přestane fungovat")
        print("- License check je chráněn proti odstranění")
    else:
        print("\n❌ Obfuskace selhala")
        sys.exit(1)

if __name__ == "__main__":
    main()
