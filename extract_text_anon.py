# -*- coding: utf-8 -*-
"""
Extrahuje text z anonymizovaného dokumentu
"""

import sys
from docx import Document

def extract_text(docx_path):
    """Extrahuje text z DOCX dokumentu"""
    doc = Document(docx_path)
    text_parts = []

    # Hlavní text
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    return '\n'.join(text_parts)

if __name__ == "__main__":
    text = extract_text("smlouva33_anon.docx")

    # Najdi řádky s PERSON_25
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if '[[PERSON_25]]' in line:
            print(f"Radek {i+1} s [[PERSON_25]]:")
            print(f"  {line}")
            print()

    # Ukáž první řádky kolem řádku 37 (kde je problém)
    print("\nRadky 35-40 (kde je problem s Oldřich Sedlák):")
    for i in range(34, min(40, len(lines))):
        print(f"{i+1}: {lines[i][:150]}")
