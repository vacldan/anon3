"""
License Validation CLI - Wrapper pro Electron
Slouží jako interface mezi Electron (Node.js) a Python licensing systémem
"""

import sys
import json
from pathlib import Path
import os

# Získej absolutní cestu k root složce projektu
# Pokud je skript v podsložce (např. python/), jdi o level výš
SCRIPT_DIR = Path(__file__).parent.absolute()

# Zkontroluj jestli je skript v podsložce - pokud ano, jdi do parent
if SCRIPT_DIR.name == "python" or not (SCRIPT_DIR / "licensing").exists():
    # Zkus parent directory (root projektu)
    ROOT_DIR = SCRIPT_DIR.parent
    print(f"[DEBUG] Script in subdirectory, using parent: {ROOT_DIR}", file=sys.stderr)
else:
    ROOT_DIR = SCRIPT_DIR
    print(f"[DEBUG] Script in root directory: {ROOT_DIR}", file=sys.stderr)

# DEBUG: Vypiš info o prostředí PŘED importem
print(f"[DEBUG] Python executable: {sys.executable}", file=sys.stderr)
print(f"[DEBUG] __file__: {__file__}", file=sys.stderr)
print(f"[DEBUG] SCRIPT_DIR: {SCRIPT_DIR}", file=sys.stderr)
print(f"[DEBUG] ROOT_DIR: {ROOT_DIR}", file=sys.stderr)
print(f"[DEBUG] Current working dir: {os.getcwd()}", file=sys.stderr)
print(f"[DEBUG] licensing folder exists: {(ROOT_DIR / 'licensing').exists()}", file=sys.stderr)
print(f"[DEBUG] Licencing folder exists: {(ROOT_DIR / 'Licencing').exists()}", file=sys.stderr)

# Přidej root složku do path pro import modulů
sys.path.insert(0, str(ROOT_DIR))

# Změň working directory na root projektu
os.chdir(ROOT_DIR)

print(f"[DEBUG] sys.path: {sys.path[:3]}", file=sys.stderr)

try:
    print(f"[DEBUG] Trying to import from licensing (lowercase)...", file=sys.stderr)
    from licensing.license_validator import validate_license, get_license_info
    from licensing.hw_fingerprint import get_hardware_id, format_hw_id
    print(f"[DEBUG] Import from licensing successful!", file=sys.stderr)
except ImportError as e:
    print(f"[DEBUG] Import from licensing failed: {e}", file=sys.stderr)
    # Fallback pokud jsou moduly ve složce Licencing (capital L)
    try:
        print(f"[DEBUG] Trying to import from Licencing...", file=sys.stderr)
        from Licencing.license_validator import validate_license, get_license_info
        from Licencing.hw_fingerprint import get_hardware_id, format_hw_id
        print(f"[DEBUG] Import from Licencing successful!", file=sys.stderr)
    except ImportError as e2:
        print(f"[DEBUG] Import from Licencing also failed: {e2}", file=sys.stderr)
        print(json.dumps({
            "valid": False,
            "message": f"Licensing moduly nenalezeny: {e}",
            "needs_activation": True,
            "hw_id": "N/A"
        }), flush=True)
        sys.exit(1)


def check_license(license_path="license.lic"):
    """
    Zkontroluje licenci a vrátí JSON výsledek

    Returns JSON:
    {
        "valid": true/false,
        "message": "...",
        "license_info": {
            "customer_name": "...",
            "license_key": "...",
            "type": "standard",
            "expires_at": "2025-01-26",
            "days_remaining": 364
        },
        "hw_id": "8A3F-2BC1-E9D4-5678"
    }
    """
    try:
        # Získej HW ID
        try:
            hw_id = get_hardware_id()
            hw_id_formatted = format_hw_id(hw_id)
        except Exception as hw_error:
            hw_id = "UNKNOWN"
            hw_id_formatted = "UNKNOWN"
            print(f"[DEBUG] HW ID error: {hw_error}", file=sys.stderr)

        # Validuj licenci
        is_valid, message, license_data = validate_license(license_path, verbose=False)

        result = {
            "valid": is_valid,
            "message": message,
            "hw_id": hw_id_formatted,
            "needs_activation": not is_valid
        }

        # Pokud je licence platná, přidej detaily
        if is_valid and license_data:
            result["license_info"] = {
                "customer_name": license_data.get('customer', {}).get('name', 'N/A'),
                "customer_email": license_data.get('customer', {}).get('email', 'N/A'),
                "license_key": license_data.get('license_key', 'N/A'),
                "type": license_data.get('type', 'standard'),
                "issued_at": license_data.get('issued_at', 'N/A'),
                "expires_at": license_data.get('expires_at', 'N/A'),
            }

            # Spočítej zbývající dny
            try:
                from datetime import datetime
                expires_at = datetime.fromisoformat(license_data['expires_at'])
                days_remaining = (expires_at - datetime.now()).days
                result["license_info"]["days_remaining"] = max(0, days_remaining)
            except:
                result["license_info"]["days_remaining"] = 0

        return result

    except FileNotFoundError:
        try:
            hw_id_fallback = format_hw_id(get_hardware_id())
        except:
            hw_id_fallback = "UNKNOWN"
        return {
            "valid": False,
            "message": "Licenční soubor nenalezen",
            "needs_activation": True,
            "hw_id": hw_id_fallback
        }
    except Exception as e:
        try:
            hw_id_fallback = format_hw_id(get_hardware_id())
        except:
            hw_id_fallback = "UNKNOWN"
        return {
            "valid": False,
            "message": f"Chyba při kontrole licence: {str(e)}",
            "needs_activation": True,
            "hw_id": hw_id_fallback
        }


def main():
    """
    CLI interface pro Electron

    Usage:
        python validate_license_cli.py [license_path]

    Output:
        JSON na stdout
    """
    # Získej cestu k licenci (volitelný argument)
    # Pokud není zadána cesta, hledej v root projektu
    if len(sys.argv) > 1:
        provided_path = sys.argv[1]
        # DEBUG
        print(f"[DEBUG] Provided path: {provided_path}", file=sys.stderr)
        print(f"[DEBUG] Path exists: {Path(provided_path).exists()}", file=sys.stderr)

        # Pokud poskytnutá cesta existuje, použij ji
        if Path(provided_path).exists():
            license_path = provided_path
        else:
            # Jinak zkus v ROOT_DIR
            license_path = str(ROOT_DIR / "license.lic")
            print(f"[DEBUG] Falling back to: {license_path}", file=sys.stderr)
    else:
        # Defaultně hledej license.lic v root projektu
        license_path = str(ROOT_DIR / "license.lic")
        print(f"[DEBUG] Using default path: {license_path}", file=sys.stderr)

    print(f"[DEBUG] Final license path: {license_path}", file=sys.stderr)
    print(f"[DEBUG] License file exists: {Path(license_path).exists()}", file=sys.stderr)
    print(f"[DEBUG] SCRIPT_DIR: {SCRIPT_DIR}", file=sys.stderr)
    print(f"[DEBUG] ROOT_DIR: {ROOT_DIR}", file=sys.stderr)

    # Zkontroluj licenci
    result = check_license(license_path)

    # Vyprintuj JSON výsledek
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)

    # Exit code: 0 = platná, 1 = neplatná
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
