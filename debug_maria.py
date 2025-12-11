#!/usr/bin/env python3
"""Debug script to trace where Maria/Julia come from"""

import sys
import re
from docx import Document

# Import module code
sys.path.insert(0, '.')
with open('anon7.2 - s padama.py', 'r', encoding='utf-8') as f:
    code = f.read()
    # Remove the main() call at the end
    code = code.replace('if __name__ == "__main__":\n    main()', '')
    exec(code, globals())

# Monkey-patch _ensure_person_tag to log calls
original_ensure_person_tag = CzechAnonymizer._ensure_person_tag
debug_log = []

def debug_ensure_person_tag(self, first_nom, last_nom):
    # Log the call
    if 'Maria' in first_nom or 'Julia' in first_nom or 'Alica' in first_nom:
        import traceback
        stack = traceback.extract_stack()
        caller_info = stack[-2]
        debug_log.append({
            'first': first_nom,
            'last': last_nom,
            'caller_file': caller_info.filename,
            'caller_line': caller_info.lineno,
            'caller_code': caller_info.line
        })
        print(f"DEBUG: _ensure_person_tag called with first_nom='{first_nom}', last_nom='{last_nom}'")
        print(f"  Called from line {caller_info.lineno}")

    # Call original
    return original_ensure_person_tag(self, first_nom, last_nom)

# Patch
CzechAnonymizer._ensure_person_tag = debug_ensure_person_tag

# Run
print("Running anonymization with debug logging...")
print("="*80)

anonymizer = CzechAnonymizer('cz_names.v1.json')
anonymizer.anonymize_document('smlouva24.docx', 'smlouva24_anon_debug.docx')

print("\n" + "="*80)
print(f"Found {len(debug_log)} calls with Maria/Julia/Alica:")
for entry in debug_log:
    print(f"  {entry['first']} {entry['last']} - line {entry['caller_line']}")

