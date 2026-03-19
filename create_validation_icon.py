#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vytvoří ikonu validation_icon.ico pro SKRYI validaci."""
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Nainstaluj: pip install Pillow")
    exit(1)

def create_icon():
    sizes = [16, 32, 48, 256]
    images = []
    for size in sizes:
        img = Image.new("RGBA", (size, size), (30, 30, 46, 255))
        draw = ImageDraw.Draw(img)
        # Štít + fajfka (validace)
        margin = size // 6
        x1, y1 = margin, margin
        x2, y2 = size - margin, size - margin
        # Zaoblený obdélník (štít)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=size//8, outline=(86, 156, 214), width=max(1, size//16))
        # Fajfka (checkmark)
        cx, cy = size // 2, size // 2
        w = size // 4
        pts = [(cx - w, cy), (cx - w//3, cy + w//2), (cx + w, cy - w)]
        draw.line(pts, fill=(78, 201, 176), width=max(1, size//12))
        images.append(img)
    out = Path(__file__).parent / "validation_icon.ico"
    images[0].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[1:])
    print(f"Vytvoreno: {out}")

if __name__ == "__main__":
    create_icon()
