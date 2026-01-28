"""
Standalone License Validator - ALL-IN-ONE
Vše v jednom souboru - žádné externí závislosti na licensing/
"""

import sys
import json
import hashlib
import base64
import platform
import uuid
import subprocess
from datetime import datetime
from pathlib import Path


# ==================== MASTER SECRET ====================
MASTER_SECRET = "NixMinds_Secure_2026_!_8k9Pq2LzWvRt5XyN_Anonymizer_Secret_Key_99"


# ==================== HARDWARE FINGERPRINTING ====================

def get_cpu_id():
    """Získá identifikátor procesoru"""
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                "wmic cpu get ProcessorId",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip().split('\n')
            if len(result) > 1:
                return result[1].strip()
    except:
        pass
    return platform.processor() or "UNKNOWN_CPU"


def get_mac_address():
    """Získá MAC adresu"""
    try:
        mac = uuid.getnode()
        mac_str = ':'.join(['{:02x}'.format((mac >> i) & 0xff)
                           for i in range(0, 8*6, 8)][::-1])
        return mac_str
    except:
        return "UNKNOWN_MAC"


def get_disk_serial():
    """Získá sériové číslo systémového disku"""
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                "vol C:",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip()

            for line in result.split('\n'):
                if 'Serial Number is' in line or 'Sériové číslo svazku je' in line:
                    serial = line.split('is')[-1].strip()
                    return serial.replace('-', '')
    except:
        pass
    return "UNKNOWN_DISK"


def get_motherboard_serial():
    """Získá sériové číslo základní desky"""
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                "wmic baseboard get SerialNumber",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip().split('\n')

            if len(result) > 1:
                return result[1].strip()
    except:
        pass
    return "UNKNOWN_MB"


def get_hardware_id():
    """Vygeneruje unikátní HW fingerprint (16 hex znaků)"""
    cpu = get_cpu_id()
    mac = get_mac_address()
    disk = get_disk_serial()
    mb = get_motherboard_serial()

    combined = f"{cpu}|{mac}|{disk}|{mb}"
    hw_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16].upper()
    return hw_hash


def format_hw_id(hw_id):
    """Formátuje HW ID do čitelného tvaru: 8A3F-2BC1-E9D4-5678"""
    return '-'.join([hw_id[i:i+4] for i in range(0, len(hw_id), 4)])


# ==================== LICENSE VALIDATION ====================

def verify_signature(license_data):
    """Ověří podpis licence"""
    try:
        license_key = license_data['license_key']
        hw_id = license_data['hw_id']
        expires_at = license_data['expires_at']
        license_type = license_data['type']
        stored_signature = license_data['signature']

        sign_string = f"{license_key}|{hw_id}|{expires_at}|{license_type}"
        combined = f"{sign_string}|{MASTER_SECRET}"
        expected_signature = hashlib.sha256(combined.encode('utf-8')).hexdigest()

        return stored_signature == expected_signature
    except Exception as e:
        return False


def load_license_file(license_path):
    """Načte a dekóduje licenční soubor"""
    try:
        with open(license_path, 'r') as f:
            encoded = f.read().strip()

        decoded = base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
        license_data = json.loads(decoded)
        return license_data
    except FileNotFoundError:
        return None
    except Exception as e:
        return None


def validate_license(license_path="license.lic"):
    """
    Ověří platnost licence
    Returns: (is_valid: bool, message: str, license_data: dict|None)
    """
    # 1. Načti licenční soubor
    license_data = load_license_file(license_path)
    if not license_data:
        return False, "Licenční soubor nenalezen nebo je poškozený", None

    # 2. Ověř podpis
    if not verify_signature(license_data):
        return False, "Neplatný licenční soubor (podpis nesouhlasí)", None

    # 3. Ověř HW ID
    current_hw_id = get_hardware_id()
    expected_hw_id = license_data.get('hw_id', '').replace('-', '').upper()

    if current_hw_id != expected_hw_id:
        return False, "Licence je vázána na jiné zařízení", None

    # 4. Ověř expiraci
    try:
        expires_at = datetime.fromisoformat(license_data['expires_at'])
        now = datetime.now()

        if now > expires_at:
            days_expired = (now - expires_at).days
            return False, f"Licence vypršela před {days_expired} dny", None
    except Exception as e:
        return False, f"Chyba při kontrole expirace: {e}", None

    # Vše OK!
    customer_name = license_data.get('customer', {}).get('name', 'Neznámý')
    license_type = license_data.get('type', 'standard')
    success_msg = f"Licence platná ({license_type}) - {customer_name}"

    return True, success_msg, license_data


# ==================== CLI INTERFACE ====================

def check_license(license_path="license.lic"):
    """
    Zkontroluje licenci a vrátí JSON výsledek
    """
    try:
        # Získej HW ID
        hw_id = get_hardware_id()
        hw_id_formatted = format_hw_id(hw_id)

        # Validuj licenci
        is_valid, message, license_data = validate_license(license_path)

        result = {
            "valid": is_valid,
            "message": message,
            "hw_id": hw_id_formatted,
            "needs_activation": not is_valid,
            "standalone": True  # Indikátor že běží standalone verze
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
                expires_at = datetime.fromisoformat(license_data['expires_at'])
                days_remaining = (expires_at - datetime.now()).days
                result["license_info"]["days_remaining"] = max(0, days_remaining)
            except:
                result["license_info"]["days_remaining"] = 0

        return result

    except FileNotFoundError:
        hw_id = get_hardware_id()
        return {
            "valid": False,
            "message": "Licenční soubor nenalezen",
            "needs_activation": True,
            "hw_id": format_hw_id(hw_id),
            "standalone": True
        }
    except Exception as e:
        hw_id = get_hardware_id()
        return {
            "valid": False,
            "message": f"Chyba: {str(e)}",
            "needs_activation": True,
            "hw_id": format_hw_id(hw_id),
            "error_type": type(e).__name__,
            "standalone": True
        }


def main():
    """CLI interface pro Electron"""
    try:
        license_path = sys.argv[1] if len(sys.argv) > 1 else "license.lic"
        result = check_license(license_path)
        print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
        sys.exit(0 if result["valid"] else 1)
    except Exception as e:
        error_result = {
            "valid": False,
            "message": f"Fatální chyba: {str(e)}",
            "hw_id": "UNKNOWN",
            "needs_activation": True,
            "error_type": type(e).__name__,
            "standalone": True
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
