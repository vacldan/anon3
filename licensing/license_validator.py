"""
License Validator
Ověřuje licenční soubor v aplikaci (offline)
"""

import json
import hashlib
import base64
from datetime import datetime
from pathlib import Path
from .hw_fingerprint import get_hardware_id


# MASTER SECRET KEY - PRODUCTION
MASTER_SECRET = "NixMinds_Secure_2026_!_8k9Pq2LzWvRt5XyN_Anonymizer_Secret_Key_99"


def verify_signature(license_data):
    """
    Ověří podpis licence

    Args:
        license_data: Dict s licenčními daty

    Returns:
        bool: True pokud podpis souhlasí
    """
    try:
        license_key = license_data['license_key']
        hw_id = license_data['hw_id']
        expires_at = license_data['expires_at']
        license_type = license_data['type']
        stored_signature = license_data['signature']

        # Vytvoř stejný string jako při generování
        sign_string = f"{license_key}|{hw_id}|{expires_at}|{license_type}"
        combined = f"{sign_string}|{MASTER_SECRET}"
        expected_signature = hashlib.sha256(combined.encode('utf-8')).hexdigest()

        return stored_signature == expected_signature

    except Exception as e:
        print(f"[LICENSE] Chyba při ověřování podpisu: {e}")
        return False


def load_license_file(license_path):
    """
    Načte a dekóduje licenční soubor

    Args:
        license_path: Cesta k .lic souboru

    Returns:
        dict|None: Licenční data nebo None při chybě
    """
    try:
        with open(license_path, 'r') as f:
            encoded = f.read().strip()

        # Base64 decode
        decoded = base64.b64decode(encoded.encode('utf-8')).decode('utf-8')

        # Parse JSON
        license_data = json.loads(decoded)

        return license_data

    except FileNotFoundError:
        print(f"[LICENSE] Licenční soubor nenalezen: {license_path}")
        return None
    except Exception as e:
        print(f"[LICENSE] Chyba při čtení licence: {e}")
        return None


def validate_license(license_path="license.lic", verbose=False):
    """
    Ověří platnost licence

    Kontroly:
    1. Soubor existuje a je čitelný
    2. Podpis je platný (nebyl soubor modifikován)
    3. HW ID souhlasí
    4. Licence není expirovaná

    Args:
        license_path: Cesta k licenčnímu souboru
        verbose: Zda vypisovat detaily (default False pro production)

    Returns:
        tuple: (is_valid: bool, message: str, license_data: dict|None)
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

        days_remaining = (expires_at - now).days

    except Exception as e:
        return False, f"Chyba při kontrole expirace: {e}", None

    # Vše OK!
    customer_name = license_data.get('customer', {}).get('name', 'Neznámý')
    license_type = license_data.get('type', 'standard')

    success_msg = f"Licence platná ({license_type}) - {customer_name}"

    return True, success_msg, license_data


def get_license_info(license_path="license.lic"):
    """
    Vrátí informace o licenci bez plné validace

    Returns:
        dict|None: Základní info o licenci
    """
    license_data = load_license_file(license_path)
    if not license_data:
        return None

    try:
        expires_at = datetime.fromisoformat(license_data['expires_at'])
        days_remaining = (expires_at - datetime.now()).days

        return {
            "customer_name": license_data.get('customer', {}).get('name', 'N/A'),
            "license_key": license_data.get('license_key', 'N/A'),
            "type": license_data.get('type', 'N/A'),
            "expires_at": expires_at.strftime('%Y-%m-%d'),
            "days_remaining": max(0, days_remaining),
            "is_expired": days_remaining < 0
        }
    except:
        return None


if __name__ == "__main__":
    # Test validace
    print("\n" + "=" * 70)
    print("SKRYI LICENSE VALIDATOR - TEST")
    print("=" * 70)
    print()

    is_valid, message, data = validate_license(verbose=True)

    print()
    print("=" * 70)
    if is_valid:
        print("✅ VÝSLEDEK: PLATNÁ LICENCE")
    else:
        print("❌ VÝSLEDEK: NEPLATNÁ LICENCE")
    print(f"   {message}")
    print("=" * 70)
