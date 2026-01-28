"""
License Validation CLI - Wrapper pro Electron
Slouží jako interface mezi Electron (Node.js) a Python licensing systémem
"""

import sys
import json
import os
from pathlib import Path

# DŮLEŽITÉ: Přidej licensing modul do path
# V nainstalované aplikaci může být struktura jiná
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

# Fallback pokud není v root, zkus resources
if hasattr(sys, '_MEIPASS'):
    # PyInstaller bundle
    sys.path.insert(0, sys._MEIPASS)
elif 'resources' in str(script_dir):
    # Electron asar
    sys.path.insert(0, str(script_dir.parent))

try:
    from licensing.license_validator import validate_license, get_license_info
    from licensing.hw_fingerprint import get_hardware_id, format_hw_id
    MODULES_OK = True
except ImportError as e:
    MODULES_OK = False
    IMPORT_ERROR = str(e)


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
    # Pokud se nepodařilo naimportovat moduly, vrať error
    if not MODULES_OK:
        try:
            # Zkus získat HW ID i bez modulů (fallback)
            import uuid
            import hashlib
            mac = uuid.getnode()
            hw_id_fallback = hashlib.sha256(str(mac).encode()).hexdigest()[:16].upper()
            hw_id_formatted = '-'.join([hw_id_fallback[i:i+4] for i in range(0, 16, 4)])
        except:
            hw_id_formatted = "UNKNOWN"

        return {
            "valid": False,
            "message": f"Licensing modules not found: {IMPORT_ERROR}",
            "hw_id": hw_id_formatted,
            "needs_activation": True,
            "debug_path": str(script_dir)
        }

    try:
        # Získej HW ID
        hw_id = get_hardware_id()
        hw_id_formatted = format_hw_id(hw_id)

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
        return {
            "valid": False,
            "message": "Licenční soubor nenalezen",
            "needs_activation": True,
            "hw_id": format_hw_id(get_hardware_id())
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Chyba při kontrole licence: {str(e)}",
            "needs_activation": True,
            "hw_id": format_hw_id(get_hardware_id())
        }


def main():
    """
    CLI interface pro Electron

    Usage:
        python validate_license_cli.py [license_path]

    Output:
        JSON na stdout (VŽDY vrátí nějaký JSON, i při chybě)
    """
    try:
        # Získej cestu k licenci (volitelný argument)
        license_path = sys.argv[1] if len(sys.argv) > 1 else "license.lic"

        # Zkontroluj licenci
        result = check_license(license_path)

        # Vyprintuj JSON výsledek
        print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)

        # Exit code: 0 = platná, 1 = neplatná
        sys.exit(0 if result["valid"] else 1)

    except Exception as e:
        # FALLBACK: I při fatální chybě vrať JSON
        error_result = {
            "valid": False,
            "message": f"Fatální chyba: {str(e)}",
            "hw_id": "UNKNOWN",
            "needs_activation": True,
            "error_type": type(e).__name__,
            "script_dir": str(script_dir)
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
