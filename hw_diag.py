"""Diagnostika HW ID - zjisti proc se lisi"""
import subprocess, hashlib, uuid, platform

print("=== DIAGNOSTIKA HW ID ===")
print()

# CPU via WMIC
try:
    r = subprocess.check_output("wmic cpu get ProcessorId", shell=True, stderr=subprocess.DEVNULL)
    cpu_wmic = r.decode().split('\n')[1].strip()
    print(f"CPU (WMIC):       [{cpu_wmic}]")
except Exception as e:
    cpu_wmic = None
    print(f"CPU (WMIC):       FAILED - {e}")

# CPU via PowerShell
try:
    r = subprocess.check_output(
        ['powershell', '-NoProfile', '-Command',
         'Get-CimInstance -ClassName Win32_Processor | Select-Object -ExpandProperty ProcessorId'],
        shell=False, stderr=subprocess.DEVNULL)
    cpu_ps = r.decode().strip()
    print(f"CPU (PowerShell): [{cpu_ps}]")
except Exception as e:
    cpu_ps = None
    print(f"CPU (PowerShell): FAILED - {e}")

print(f"CPU (platform):   [{platform.processor()}]")
print()

# Disk via WMIC
try:
    r = subprocess.check_output("wmic diskdrive get SerialNumber", shell=True, stderr=subprocess.DEVNULL)
    lines = [l.strip() for l in r.decode().split('\n') if l.strip() and l.strip() != 'SerialNumber']
    disk_wmic = lines[0] if lines else None
    print(f"DISK (WMIC):       [{disk_wmic}]")
except Exception as e:
    disk_wmic = None
    print(f"DISK (WMIC):       FAILED - {e}")

# Disk via PowerShell
try:
    r = subprocess.check_output(
        ['powershell', '-NoProfile', '-Command',
         '(Get-CimInstance -ClassName Win32_DiskDrive | Select-Object -First 1).SerialNumber'],
        shell=False, stderr=subprocess.DEVNULL)
    disk_ps = r.decode().strip()
    print(f"DISK (PowerShell): [{disk_ps}]")
except Exception as e:
    disk_ps = None
    print(f"DISK (PowerShell): FAILED - {e}")
print()

# MAC
mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)][::-1])
print(f"MAC: [{mac}]")
print()

# Compute HW IDs
def make_hw(cpu, disk):
    combined = f"{cpu}:{mac}:{disk}"
    h = hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
    return '-'.join([h[i:i+4] for i in range(0, 16, 4)])

print("=== VYPOCTENE HW ID ===")
if cpu_wmic and disk_wmic:
    print(f"HW ID (WMIC+WMIC):     {make_hw(cpu_wmic, disk_wmic)}")
if cpu_ps and disk_ps:
    print(f"HW ID (PS+PS):         {make_hw(cpu_ps, disk_ps)}")
if cpu_wmic and disk_ps:
    print(f"HW ID (WMIC+PS disk):  {make_hw(cpu_wmic, disk_ps)}")
if cpu_ps and disk_wmic:
    print(f"HW ID (PS cpu+WMIC):   {make_hw(cpu_ps, disk_wmic)}")
print(f"HW ID (fallback):      {make_hw(platform.processor(), 'UNKNOWN')}")
print()
print(f"OCEKAVANY HW ID:       C87C-FA4E-F36D-48AE")
print(f"AKTUALNI HW ID:        {make_hw(cpu_wmic or cpu_ps or platform.processor(), disk_wmic or disk_ps or 'UNKNOWN')}")
