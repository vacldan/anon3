#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

# Load anon7.2
with open('anon7.2 - s padama.py', 'r', encoding='utf-8') as f:
    exec(f.read(), globals())

# Run test
CZECH_FIRST_NAMES = load_names_library('cz_names.v1.json')
anon = Anonymizer(verbose=True)
anon.anonymize_docx('smlouva32.docx', '/tmp/test_orig.docx', '/tmp/test_orig_map.json', '/tmp/test_orig_map.txt')
print("✅ DONE")
