"""
License Generator - ADMIN TOOL
Tento skript slouží pro generování licenčních souborů pro zákazníky
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import base64


# MASTER SECRET KEY - ZMĚŇ TOTO NA VLASTNÍ DLOUHÝ NÁHODNÝ STRING!
# Tento klíč nesmí nikdy uniknout. Drž ho v bezpečí.
MASTER_SECRET = "SKRYI_2024_MASTER_KEY_CHANGE_THIS_TO_YOUR_OWN_RANDOM_STRING_XYZ789"


def generate_license_key():
    """Vygeneruje náhodný licenční klíč ve formátu XXXX-XXXX-XXXX-XXXX"""
    parts = []
    for _ in range(4):
        part = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(4))
        parts.append(part)
    return '-'.join(parts)


def sign_license_data(data_string):
    """
    Podepíše licenční data pomocí HMAC

    Args:
        data_string: String který má být podepsán

    Returns:
        str: Hexadecimální podpis
    """
    combined = f"{data_string}|{MASTER_SECRET}"
    signature = hashlib.sha256(combined.encode('utf-8')).hexdigest()
    return signature


def create_license(
    customer_name,
    customer_email,
    hw_id,
    license_type="standard",
    duration_days=365,
    notes=""
):
    """
    Vytvoří licenční soubor pro zákazníka

    Args:
        customer_name: Jméno zákazníka
        customer_email: Email zákazníka
        hw_id: Hardware ID zákazníka (16 hex znaků)
        license_type: Typ licence ("trial", "standard", "professional", "enterprise")
        duration_days: Platnost licence ve dnech
        notes: Poznámky

    Returns:
        dict: Licenční data
    """
    license_key = generate_license_key()
    issue_date = datetime.now()
    expiry_date = issue_date + timedelta(days=duration_days)

    # Vytvoř licenční data
    license_data = {
        "license_key": license_key,
        "customer": {
            "name": customer_name,
            "email": customer_email
        },
        "hw_id": hw_id.replace('-', '').upper(),
        "type": license_type,
        "issued_at": issue_date.isoformat(),
        "expires_at": expiry_date.isoformat(),
        "notes": notes,
        "version": "1.0"
    }

    # Vytvoř string pro podpis
    sign_string = f"{license_key}|{hw_id}|{expiry_date.isoformat()}|{license_type}"
    signature = sign_license_data(sign_string)

    license_data["signature"] = signature

    return license_data


def save_license_file(license_data, output_path="license.lic"):
    """
    Uloží licenční soubor

    Args:
        license_data: Licenční data (dict)
        output_path: Cesta k výstupnímu souboru
    """
    # Převeď na JSON
    json_str = json.dumps(license_data, indent=2)

    # Base64 encode (lehká obfuskace)
    encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    # Ulož do souboru
    with open(output_path, 'w') as f:
        f.write(encoded)

    print(f"✅ Licence uložena do: {output_path}")


def print_license_info(license_data):
    """Zobrazí informace o licenci"""
    print("\n" + "=" * 70)
    print("VYGENEROVANÁ LICENCE")
    print("=" * 70)
    print(f"Licenční klíč:     {license_data['license_key']}")
    print(f"Zákazník:          {license_data['customer']['name']}")
    print(f"Email:             {license_data['customer']['email']}")
    print(f"Hardware ID:       {license_data['hw_id']}")
    print(f"Typ:               {license_data['type']}")
    print(f"Vystaveno:         {license_data['issued_at']}")
    print(f"Platnost do:       {license_data['expires_at']}")
    if license_data.get('notes'):
        print(f"Poznámky:          {license_data['notes']}")
    print("=" * 70)


def interactive_generator():
    """Interaktivní režim pro generování licencí"""
    print("\n" + "=" * 70)
    print("SKRYI LICENSE GENERATOR")
    print("=" * 70)
    print()

    # Získej vstupní data
    customer_name = input("Jméno zákazníka: ").strip()
    customer_email = input("Email zákazníka: ").strip()
    hw_id = input("Hardware ID (16 hex znaků, např. 8A3F-2BC1-E9D4-5678): ").strip()

    print("\nTypy licencí:")
    print("  1) trial       - Zkušební (30 dní)")
    print("  2) standard    - Standardní (1 rok)")
    print("  3) professional - Profesionální (1 rok)")
    print("  4) enterprise  - Enterprise (1 rok)")
    print("  5) custom      - Vlastní nastavení")

    choice = input("\nVyberte typ [1-5]: ").strip()

    license_types = {
        '1': ('trial', 30),
        '2': ('standard', 365),
        '3': ('professional', 365),
        '4': ('enterprise', 365),
    }

    if choice in license_types:
        license_type, duration = license_types[choice]
    elif choice == '5':
        license_type = input("Typ licence (custom): ").strip()
        duration = int(input("Platnost (dny): ").strip())
    else:
        license_type, duration = 'standard', 365

    notes = input("Poznámky (volitelné): ").strip()

    # Vygeneruj licenci
    print("\nGeneruji licenci...")
    license_data = create_license(
        customer_name=customer_name,
        customer_email=customer_email,
        hw_id=hw_id,
        license_type=license_type,
        duration_days=duration,
        notes=notes
    )

    # Zobraz info
    print_license_info(license_data)

    # Ulož do souboru
    safe_name = customer_name.replace(' ', '_').lower()
    filename = f"license_{safe_name}_{license_data['license_key'][:8]}.lic"
    save_license_file(license_data, filename)

    print(f"\n✅ Hotovo! Pošlete soubor '{filename}' zákazníkovi.")
    print("   Zákazník ho umístí do složky s aplikací.")


if __name__ == "__main__":
    # Spusť interaktivní generátor
    try:
        interactive_generator()
    except KeyboardInterrupt:
        print("\n\n❌ Zrušeno")
    except Exception as e:
        print(f"\n❌ Chyba: {e}")
