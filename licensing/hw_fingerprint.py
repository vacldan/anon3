"""
Hardware Fingerprinting Module
Generuje unikátní ID založené na HW počítače
"""

import hashlib
import platform
import uuid
import subprocess
import sys


def get_cpu_id():
    """Získá identifikátor procesoru"""
    try:
        if platform.system() == "Windows":
            # Windows: WMIC command
            result = subprocess.check_output(
                "wmic cpu get ProcessorId",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip().split('\n')
            if len(result) > 1:
                return result[1].strip()
        else:
            # Linux/Mac: /proc/cpuinfo nebo system_profiler
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'Serial' in line or 'Processor' in line:
                        return line.split(':')[1].strip()
    except:
        pass

    # Fallback: použij platform info
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
            # Windows: vol command pro C:
            result = subprocess.check_output(
                "vol C:",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip()

            # Hledej serial number v output
            for line in result.split('\n'):
                if 'Serial Number is' in line or 'Sériové číslo svazku je' in line:
                    serial = line.split('is')[-1].strip()
                    return serial.replace('-', '')
        else:
            # Linux: blkid nebo lsblk
            result = subprocess.check_output(
                "lsblk -o UUID,MOUNTPOINT | grep '/$'",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip()

            if result:
                return result.split()[0]
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
        else:
            # Linux: dmidecode
            result = subprocess.check_output(
                "sudo dmidecode -s baseboard-serial-number",
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode().strip()

            return result
    except:
        pass

    return "UNKNOWN_MB"


def get_hardware_id(verbose=False):
    """
    Vygeneruje unikátní HW fingerprint

    Kombinuje:
    - CPU ID
    - MAC adresa
    - Disk serial
    - Motherboard serial (volitelné - může selhat bez admin práv)

    Returns:
        str: 16-znakový hexadecimální HW ID (např. "8A3F2BC1E9D45678")
    """
    cpu = get_cpu_id()
    mac = get_mac_address()
    disk = get_disk_serial()
    mb = get_motherboard_serial()

    # Kombinuj všechny informace
    combined = f"{cpu}|{mac}|{disk}|{mb}"

    if verbose:
        print(f"[DEBUG] HW Fingerprint components:")
        print(f"  CPU:         {cpu}")
        print(f"  MAC:         {mac}")
        print(f"  Disk Serial: {disk}")
        print(f"  MB Serial:   {mb}")
        print(f"  Combined:    {combined}")

    # Vytvoř SHA-256 hash a vezmi prvních 16 znaků
    hw_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16].upper()

    if verbose:
        print(f"  HW ID:       {hw_hash}")

    return hw_hash


def format_hw_id(hw_id):
    """
    Formátuje HW ID do čitelného tvaru

    Např: "8A3F2BC1E9D45678" -> "8A3F-2BC1-E9D4-5678"
    """
    return '-'.join([hw_id[i:i+4] for i in range(0, len(hw_id), 4)])


def verify_hw_id(expected_hw_id):
    """
    Ověří, zda aktuální HW ID odpovídá očekávanému

    Args:
        expected_hw_id: Očekávané HW ID (s nebo bez pomlček)

    Returns:
        bool: True pokud ID souhlasí
    """
    current_hw_id = get_hardware_id()
    expected_clean = expected_hw_id.replace('-', '').upper()

    return current_hw_id == expected_clean


if __name__ == "__main__":
    # Test script - zobraz HW ID
    print("=" * 60)
    print("SKRYI Hardware Fingerprint Tool")
    print("=" * 60)
    print()

    hw_id = get_hardware_id(verbose=True)
    formatted = format_hw_id(hw_id)

    print()
    print("=" * 60)
    print(f"HARDWARE ID: {formatted}")
    print("=" * 60)
    print()
    print("Tento ID použijte při generování licence.")
