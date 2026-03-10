#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys
from docx import Document

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fname = sys.argv[1] if len(sys.argv) > 1 else "anon_output/smlouva8_anon.docx"
words = sys.argv[2:] if len(sys.argv) > 2 else ["Barbora", "Jakubovi", "Jakub", "Havlíček"]

doc = Document(fname)
text = "\n".join(p.text for p in doc.paragraphs)

for word in words:
    hits = []
    for m in re.finditer(re.escape(word), text):
        before = text[max(0, m.start() - 5) : m.start()]
        if "[[" not in before:
            ctx = text[max(0, m.start() - 40) : m.end() + 40].replace("\n", " ")
            hits.append(ctx)
    if hits:
        for ctx in hits:
            print(f"  LEAK: '{word}' -> ...{ctx}...")
    else:
        print(f"  OK: '{word}' not found in plain text")
