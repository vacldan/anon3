"""
Standalone License Validator - ALL-IN-ONE
Vše v jednom souboru - žádné externí závislosti na licensing/
Hledá license.lic ve více lokacích včetně složky s .exe
"""

import sys
import json
import hashlib
import base64
import platform
import uuid
import subprocess
import os
from datetime import datetime
from pathlib import Path


# ==================== MASTER SECRET ====================
MASTER_SECRET = "NixMinds_Secure_2026_!_8k9Pq2LzWvRt5XyN_Anonymizer_Secret_Key_99"


# ==================== HW FINGERPRINT ====================
def get_cpu_id():
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output("wmic cpu get ProcessorId", shell=True, stderr=subprocess.DEVNULL)
            return result.decode().split('\n')[1].strip()
        elif platform.system() == "Linux":
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'Serial' in line or 'model name' in line:
                        return line.split(':')[1].strip()
        return platform.processor()
    except:
        return platform.processor()


def get_mac_address():
    try:
        mac = uuid.getnode()
        return ':'.join(['{:02x}'.format((mac >> i) & 0xff) for i in range(0, 48, 8)][::-1])
    except:
        return "00:00:00:00:00:00"


def get_disk_serial():
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output("wmic diskdrive get SerialNumber", shell=True, stderr=subprocess.DEVNULL)
            lines = [l.strip() for l in result.decode().split('\n') if l.strip() and l.strip() != 'SerialNumber']
            return lines[0] if lines else "UNKNOWN"
        elif platform.system() == "Linux":
            result = subprocess.check_output("lsblk -o SERIAL | head -2 | tail -1", shell=True, stderr=subprocess.DEVNULL)
            return result.decode().strip() or "UNKNOWN"
        return "UNKNOWN"
    except:
        return "UNKNOWN"


def get_hardware_id():
    cpu = get_cpu_id()
    mac = get_mac_address()
    disk = get_disk_serial()
    combined = f"{cpu}:{mac}:{disk}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16].upper()


def format_hw_id(hw_id):
    return '-'.join([hw_id[i:i+4] for i in range(0, 16, 4)])


# ==================== LICENSE VALIDATION ====================
def verify_signature(license_data):
    data_to_sign = (
        f"{license_data['hw_id']}:"
        f"{license_data['customer']['name']}:"
        f"{license_data['customer']['email']}:"
        f"{license_data['license_key']}:"
        f"{license_data['type']}:"
        f"{license_data['issued_at']}:"
        f"{license_data['expires_at']}"
    )
    expected_signature = hashlib.sha256((data_to_sign + MASTER_SECRET).encode()).hexdigest()
    return license_data.get('signature') == expected_signature


def load_license_file(license_path):
    with open(license_path, 'r') as f:
        encoded_data = f.read().strip()
    decoded_data = base64.b64decode(encoded_data).decode('utf-8')
    return json.loads(decoded_data)


def validate_license(license_path):
    try:
        license_data = load_license_file(license_path)
    except FileNotFoundError:
        return False, "Licenční soubor nenalezen", None
    except Exception as e:
        return False, f"Chyba při načítání licence: {e}", None

    if not verify_signature(license_data):
        return False, "Neplatný podpis licence - možná padělané!", None

    current_hw_id = get_hardware_id()
    license_hw_id = license_data.get('hw_id', '').replace('-', '').upper()

    if current_hw_id != license_hw_id:
        return False, f"Licence je vázána na jiný počítač", None

    expires_at = datetime.fromisoformat(license_data['expires_at'])
    if datetime.now() > expires_at:
        return False, "Licence vypršela", None

    license_type = license_data.get('type', 'standard')
    customer_name = license_data.get('customer', {}).get('name', 'Unknown')

    return True, f"Licence platná ({license_type}) - {customer_name}", license_data


def get_license_info(license_data):
    if not license_data:
        return None

    expires_at = datetime.fromisoformat(license_data['expires_at'])
    days_remaining = (expires_at - datetime.now()).days

    return {
        "customer_name": license_data.get('customer', {}).get('name', 'Unknown'),
        "customer_email": license_data.get('customer', {}).get('email', 'Unknown'),
        "license_key": license_data.get('license_key', 'Unknown'),
        "type": license_data.get('type', 'standard'),
        "issued_at": license_data.get('issued_at'),
        "expires_at": license_data.get('expires_at'),
        "days_remaining": max(0, days_remaining)
    }


# ==================== LICENSE FILE SEARCH ====================
def find_license_file():
    """
    Hledá license.lic ve více lokacích:
    1. Aktuální pracovní adresář
    2. Složka kde je tento script
    3. Složka s .exe (pro Electron app - 2 úrovně nahoru od scriptu)
    4. Složka resources (1 úroveň nahoru)
    5. Cesta předaná jako argument
    """
    script_dir = Path(__file__).parent.absolute()

    # Seznam míst kde hledat
    search_locations = [
        # Argument z příkazové řádky
        Path(sys.argv[1]) if len(sys.argv) > 1 else None,

        # Aktuální pracovní adresář
        Path.cwd() / "license.lic",

        # Složka scriptu
        script_dir / "license.lic",

        # Electron app: resources\app.asar.unpacked -> resources -> app root (s .exe)
        script_dir.parent.parent / "license.lic",  # ../../license.lic

        # Jen o jednu úroveň nahoru
        script_dir.parent / "license.lic",  # ../license.lic

        # Tři úrovně nahoru (pro různé struktury)
        script_dir.parent.parent.parent / "license.lic",
    ]

    for location in search_locations:
        if location and location.exists():
            return str(location)

    return None


# ==================== MAIN ====================
def check_license():
    hw_id = get_hardware_id()
    hw_id_formatted = format_hw_id(hw_id)

    license_path = find_license_file()

    if not license_path:
        return {
            "valid": False,
            "message": "Licenční soubor nenalezen",
            "hw_id": hw_id_formatted,
            "needs_activation": True,
            "standalone": True,
            "searched_locations": [
                str(Path.cwd() / "license.lic"),
                str(Path(__file__).parent / "license.lic"),
                str(Path(__file__).parent.parent.parent / "license.lic"),
            ]
        }

    is_valid, message, license_data = validate_license(license_path)

    result = {
        "valid": is_valid,
        "message": message,
        "hw_id": hw_id_formatted,
        "needs_activation": not is_valid,
        "standalone": True,
        "license_path": license_path
    }

    if is_valid and license_data:
        result["license_info"] = get_license_info(license_data)

    return result


def main():
    try:
        result = check_license()
        print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
        sys.exit(0 if result["valid"] else 1)
    except Exception as e:
        error_result = {
            "valid": False,
            "message": f"Kritická chyba: {str(e)}",
            "hw_id": "UNKNOWN",
            "needs_activation": True,
            "standalone": True,
            "error": str(e)
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
