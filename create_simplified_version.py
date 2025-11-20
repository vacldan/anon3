#!/usr/bin/env python3
"""
Create simplified version by removing non-PII patterns completely.
"""
import re

# Patterns to completely remove
REMOVE_PATTERNS = [
    'AMOUNT_RE',
    'VARIABLE_SYMBOL_RE',
    'CONST_SYMBOL_RE',
    'SPEC_SYMBOL_RE',
    'LICENSE_ID_RE',
    'CASE_ID_RE',
    'COURT_FILE_RE',
    'POLICY_ID_RE',
    'CONTRACT_ID_RE',
    'BENEFIT_CARD_RE',
    'DIPLOMA_ID_RE',
    'EMPLOYEE_ID_RE',
    'SECURITY_CLEARANCE_RE',
    'LAB_ID_RE',
]

def remove_pattern_definition(lines):
    """Remove pattern definitions and their usage."""
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line starts a pattern definition to remove
        should_skip = False
        for pattern in REMOVE_PATTERNS:
            if re.match(rf'^{pattern}\s*=\s*re\.compile', line):
                print(f"Removing pattern definition: {pattern} at line {i+1}")
                # Skip this line and all following lines until we hit a non-indented line
                should_skip = True
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    # Stop if we hit blank line followed by non-comment/non-indented
                    if next_line.strip() == '':
                        i += 1
                        if i < len(lines) and not lines[i].startswith((' ', '\t', '#')):
                            break
                    elif not next_line.startswith((' ', '\t')) and next_line.strip() and not next_line.strip().startswith('#'):
                        break
                    i += 1
                break

        if should_skip:
            continue

        # Check if this line defines a function for a removed pattern
        should_skip_function = False
        for pattern in REMOVE_PATTERNS:
            func_name = pattern.lower().replace('_re', '')
            if re.match(rf'\s+def replace_{func_name}\(', line):
                print(f"Removing function: replace_{func_name} at line {i+1}")
                # Skip function definition and body
                should_skip_function = True
                i += 1
                # Skip until we hit a line at same or lesser indentation
                base_indent = len(line) - len(line.lstrip())
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.strip() == '':
                        i += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= base_indent and next_line.strip():
                        break
                    i += 1
                break

        if should_skip_function:
            continue

        # Check if this line calls a removed pattern
        should_skip_call = False
        for pattern in REMOVE_PATTERNS:
            if f'{pattern}.sub(' in line:
                print(f"Removing pattern call: {pattern} at line {i+1}")
                should_skip_call = True
                break

        if not should_skip_call:
            result.append(line)

        i += 1

    return result

def add_new_patterns(lines):
    """Add VIN, MAC, IMEI patterns after LICENSE_PLATE_RE."""
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)

        # After LICENSE_PLATE_RE closing paren, add new patterns
        if re.match(r'^\)\s*$', line) and i > 0:
            # Check if previous lines contain LICENSE_PLATE_RE
            prev_lines = ''.join(lines[max(0, i-15):i])
            if 'LICENSE_PLATE_RE = re.compile' in prev_lines:
                print(f"Adding VIN, MAC, IMEI patterns after LICENSE_PLATE_RE at line {i+1}")
                result.append('\n')
                result.append('# VIN (Vehicle Identification Number) - 17 znaků\n')
                result.append('# Formát: TMBCF61Z0L7654321, 1HGBH41JXMN109186\n')
                result.append('VIN_RE = re.compile(\n')
                result.append('    r\'(?:VIN|Vehicle\\s+ID|Identifikační\\s+číslo\\s+vozidla)\\s*[:\\-]?\\s*([A-HJ-NPR-Z0-9]{17})\\b|\'\n')
                result.append('    r\'\\b([A-HJ-NPR-Z0-9]{17})\\b(?=\\s*(?:VIN|vozidlo|auto|vehicle))\',\n')
                result.append('    re.IGNORECASE\n')
                result.append(')\n')
                result.append('\n')
                result.append('# MAC adresa (Media Access Control)\n')
                result.append('# Formát: 00:1B:44:11:3A:B7, 00-1B-44-11-3A-B7, 001B.4411.3AB7\n')
                result.append('MAC_RE = re.compile(\n')
                result.append('    r\'(?:MAC\\s+(?:address|adresa)?)\\s*[:\\-]?\\s*([0-9A-F]{2}[:\\-][0-9A-F]{2}[:\\-][0-9A-F]{2}[:\\-][0-9A-F]{2}[:\\-][0-9A-F]{2}[:\\-][0-9A-F]{2})|\'\n')
                result.append('    r\'\\b([0-9A-F]{2}[:\\-][0-9A-F]{2}[:\\-][0-9A-F]{2}[:\\-][0-9A-F]{2}[:\\-][0-9A-F]{2}[:\\-][0-9A-F]{2})\\b|\'\n')
                result.append('    r\'\\b([0-9A-F]{4}\\.[0-9A-F]{4}\\.[0-9A-F]{4})\\b\',\n')
                result.append('    re.IGNORECASE\n')
                result.append(')\n')
                result.append('\n')
                result.append('# IMEI (International Mobile Equipment Identity)\n')
                result.append('# Formát: 15 číslic (např. 123456789012345)\n')
                result.append('IMEI_RE = re.compile(\n')
                result.append('    r\'(?:IMEI|International\\s+Mobile\\s+Equipment\\s+Identity)\\s*[:\\-]?\\s*(\\d{15})\\b|\'\n')
                result.append('    r\'\\b(\\d{15})\\b(?=\\s*(?:IMEI|mobil|telefon|mobile))\',\n')
                result.append('    re.IGNORECASE\n')
                result.append(')\n')

        i += 1

    return result

def add_new_pattern_calls(lines):
    """Add calls to VIN, MAC, IMEI patterns."""
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)

        # After LICENSE_PLATE_RE.sub call, add new pattern calls
        if 'LICENSE_PLATE_RE.sub(replace_license_plate, text)' in line:
            print(f"Adding VIN, MAC, IMEI pattern calls after LICENSE_PLATE at line {i+1}")
            result.append('\n')
            result.append('        # 18.1. VIN (Vehicle Identification Number)\n')
            result.append('        def replace_vin(match):\n')
            result.append('            vin = match.group(1) if match.group(1) else match.group(2)\n')
            result.append('            if vin:\n')
            result.append('                return self._get_or_create_label(\'VIN\', vin)\n')
            result.append('            return match.group(0)\n')
            result.append('        text = VIN_RE.sub(replace_vin, text)\n')
            result.append('\n')
            result.append('        # 18.2. MAC ADRESA\n')
            result.append('        def replace_mac(match):\n')
            result.append('            mac = match.group(1) or match.group(2) or match.group(3)\n')
            result.append('            if mac:\n')
            result.append('                return self._get_or_create_label(\'MAC\', mac)\n')
            result.append('            return match.group(0)\n')
            result.append('        text = MAC_RE.sub(replace_mac, text)\n')
            result.append('\n')
            result.append('        # 18.3. IMEI (International Mobile Equipment Identity)\n')
            result.append('        def replace_imei(match):\n')
            result.append('            imei = match.group(1) if match.group(1) else match.group(2)\n')
            result.append('            if imei:\n')
            result.append('                return self._get_or_create_label(\'IMEI\', imei)\n')
            result.append('            return match.group(0)\n')
            result.append('        text = IMEI_RE.sub(replace_imei, text)\n')

        i += 1

    return result

def main():
    print("Reading Claude_code_6_complete.py...")
    with open('Claude_code_6_complete.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"Original: {len(lines)} lines\n")

    print("Step 1: Removing non-PII patterns...")
    lines = remove_pattern_definition(lines)
    print(f"After removal: {len(lines)} lines\n")

    print("Step 2: Adding new patterns (VIN, MAC, IMEI)...")
    lines = add_new_patterns(lines)
    print(f"After adding patterns: {len(lines)} lines\n")

    print("Step 3: Adding new pattern calls...")
    lines = add_new_pattern_calls(lines)
    print(f"Final: {len(lines)} lines\n")

    print("Writing Claude_code_6_v7_simplified.py...")
    with open('Claude_code_6_v7_simplified.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("\n✓ Done!")
    print(f"Removed {1577 - len(lines) + 40} lines")  # +40 for new patterns
    print(f"Created: Claude_code_6_v7_simplified.py")

if __name__ == '__main__':
    main()
