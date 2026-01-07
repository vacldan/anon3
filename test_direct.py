#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Direct test of anon7.2 without CLI wrapper"""

import sys
import importlib.util

# Import anon7.2 directly
spec = importlib.util.spec_from_file_location("anon72", "anon7.2 - s padama.py")
anon72 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anon72)

# Run
anon72.CZECH_FIRST_NAMES = anon72.load_names_library('cz_names.v1.json')
anon = anon72.Anonymizer(verbose=False)
anon.anonymize_docx('smlouva32.docx', '/tmp/direct_test.docx', '/tmp/direct_test_map.json', '/tmp/direct_test_map.txt')
print("✅ DONE")
