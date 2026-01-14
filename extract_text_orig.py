# -*- coding: utf-8 -*-
"""
Extrahuje text z originálního dokumentu
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
    text = extract_text("smlouva33.docx")

    # Ukáž řádky 33-40 (kde je problém)
    lines = text.split('\n')
    print("Radky 33-40 v originalu:")
    for i in range(32, min(40, len(lines))):
        print(f"{i+1}: {lines[i][:200]}")
