"""
SKRYI Hardware ID Tool
Tento nástroj zobrazí Hardware ID vašeho počítače

Hardware ID je potřeba pro aktivaci licence.
Pošlete ho prodejci při objednávce.
"""

import sys
from pathlib import Path

# Přidej licensing modul do path
sys.path.insert(0, str(Path(__file__).parent))

from licensing.hw_fingerprint import get_hardware_id, format_hw_id


def main():
    print()
    print("=" * 70)
    print("                    SKRYI - HARDWARE ID")
    print("=" * 70)
    print()
    print("Zjišťuji Hardware ID vašeho počítače...")
    print()

    try:
        # Získej HW ID
        hw_id = get_hardware_id()
        formatted = format_hw_id(hw_id)

        print("-" * 70)
        print()
        print(f"  VÁŠ HARDWARE ID:  {formatted}")
        print()
        print("-" * 70)
        print()
        print("DŮLEŽITÉ:")
        print("  → Tento Hardware ID je UNIKÁTNÍ pro váš počítač")
        print("  → Pošlete ho prodejci při objednávce licence")
        print("  → Licence bude vázána POUZE na tento počítač")
        print()
        print("POZNÁMKA:")
        print("  Pokud vyměníte procesor, základní desku nebo disk,")
        print("  bude potřeba nová aktivace.")
        print()
        print("=" * 70)

    except Exception as e:
        print()
        print("❌ CHYBA při zjišťování Hardware ID:")
        print(f"   {e}")
        print()
        print("Kontaktujte technickou podporu.")
        print("=" * 70)
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()

        # Počkej na Enter před zavřením (pro Windows .exe)
        input("\nStiskněte Enter pro ukončení...")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\n❌ Zrušeno uživatelem")
        sys.exit(1)
