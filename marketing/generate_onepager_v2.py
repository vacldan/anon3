#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKRYI One-Pager Verze 2 – design z verze 1, obsah z v2.
Kontrolováno: vše na jednu stránku A4.
"""

import os
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
FONT_DIR = os.path.join(ROOT_DIR, "fonts")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo4.png")
TRIAL_URL = "https://nixminds.cz/SKRYI"

BG = colors.HexColor("#0A0F1C")
PANEL = colors.HexColor("#121A2B")
PANEL_2 = colors.HexColor("#162039")
ACCENT = colors.HexColor("#5A6BFF")
ACCENT_LIGHT = colors.HexColor("#9FB2FF")
TEXT = colors.HexColor("#F1F5FF")
TEXT_MUTED = colors.HexColor("#A5AFBF")
LINE = colors.HexColor("#23304B")

# Kompaktní rozestupy pro fit na A4 (842pt)
M = 28
G = 14
SECT = 22
CONTENT_W = 0


def draw_para(c, x, y_top, w, text, style):
    p = Paragraph(text, style)
    _, h = p.wrap(w, 1200)
    p.drawOn(c, x, y_top - h)
    return h


def section_header(c, x, y, label):
    c.setFillColor(ACCENT)
    c.rect(x, y - 8, 4, 10, fill=1, stroke=0)
    c.setFillColor(ACCENT_LIGHT)
    c.rect(x, y - 8, 4, 2, fill=1, stroke=0)
    c.setFillColor(TEXT)
    c.setFont("DV-B", 10)
    c.drawString(x + 10, y - 7, label)
    return y - 22


def build():
    pdfmetrics.registerFont(TTFont("DV", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DV-B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))

    w, h = A4
    global CONTENT_W
    CONTENT_W = w - M * 2

    out_path = os.path.join(os.path.dirname(__file__), "SKRYI_OnePager_v2.pdf")
    c = canvas.Canvas(out_path, pagesize=A4)
    c.setFillColor(BG)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    body_muted = ParagraphStyle("body_muted", fontName="DV", fontSize=8, leading=10, textColor=TEXT_MUTED)
    headline = ParagraphStyle("headline", fontName="DV-B", fontSize=20, leading=24, textColor=TEXT)
    sub = ParagraphStyle("sub", fontName="DV", fontSize=9, leading=12, textColor=TEXT_MUTED)

    y = h - M

    # HEADER
    c.setFillColor(TEXT_MUTED)
    c.setFont("DV", 8)
    c.drawRightString(w - M, y - 6, "GDPR compliant · 100% offline · SHA-256")
    y -= 22

    # HERO
    left_w = 200
    right_w = CONTENT_W - left_w - G
    hero_y = y

    c.setFillColor(TEXT)
    c.setFont("DV-B", 44)
    c.drawString(M, hero_y - 44, "SKRYI")
    skryi_w = c.stringWidth("SKRYI", "DV-B", 44)

    img_h = 0
    if os.path.exists(LOGO_PATH):
        img_w = skryi_w
        img_h = 120
        if HAS_PIL:
            try:
                with Image.open(LOGO_PATH) as im:
                    rw, rh = im.size
                    img_w = skryi_w
                    img_h = int(rh * skryi_w / rw)
            except Exception:
                img_w, img_h = skryi_w, 120
        img_y = hero_y - 44 - 12 - img_h
        c.drawImage(LOGO_PATH, M, img_y, width=img_w, height=img_h, mask="auto")

    left_block_h = 44 + 12 + img_h
    text_x = M + left_w + G
    head_h = draw_para(c, text_x, hero_y, right_w, "Anonymizace, která konečně mluví česky.", headline)
    sub_h = draw_para(c, text_x, hero_y - head_h - 8, right_w,
        "100% Offline. 0 % úniků dat. Validováno na 231 smlouvách.", sub)
    draw_para(c, text_x, hero_y - head_h - sub_h - 14, right_w,
        "První GDPR nástroj s morfologickou inteligencí pro advokacii, nemocnice a státní správu.", body_muted)

    y = hero_y - max(head_h + sub_h + 28, left_block_h) - SECT

    # PROBLÉM A ŘEŠENÍ
    y = section_header(c, M, y, "PROBLÉM A ŘEŠENÍ")
    box_h = 100
    box_y = y
    c.setFillColor(PANEL)
    c.setStrokeColor(LINE)
    c.rect(M, y - box_h, CONTENT_W, box_h, fill=1, stroke=1)
    pad = 12
    y -= 12

    c.setFillColor(TEXT)
    c.setFont("DV-B", 9)
    c.drawString(M + pad, y - 9, "PROČ GLOBÁLNÍ AI SELHÁVÁ:")
    y -= 12
    c.setFillColor(TEXT_MUTED)
    c.setFont("DV", 8)
    c.drawString(M + pad, y - 9, "\"Smlouvu uzavřel Jan Novák. S Janem Novákem bylo jednáno.\"")
    c.drawString(M + pad, y - 17, "(Běžný nástroj zachytí jen první tvar.)")
    y -= 30

    c.setFillColor(TEXT)
    c.setFont("DV-B", 9)
    c.drawString(M + pad, y - 9, "JAK TO ŘEŠÍ SKRYI (Bidirekcionální inference):")
    y -= 12
    c.setFillColor(ACCENT_LIGHT)
    c.setFont("DV", 8)
    c.drawString(M + pad, y - 9, "\"Smlouvu uzavřel [[OSOBA_1]]. S [[OSOBA_1]] bylo jednáno.\"")
    c.setFillColor(TEXT_MUTED)
    c.drawString(M + pad, y - 17, "(Všech 7 pádů pod jedním štítkem.)")
    y = box_y - box_h - SECT

    # TECHNOLOGICKÝ NÁSKOK V KAŽDÉM DOKUMENTU (dlaždice zachovány)
    y = section_header(c, M, y, "TECHNOLOGICKÝ NÁSKOK V KAŽDÉM DOKUMENTU")
    tile_w = (CONTENT_W - G) / 2
    tile_h = 48
    tiles = [
        ("100% OFFLINE", "True Zero-Trust. Dokumenty nikdy neopustí váš počítač.", "ZT"),
        ("< 5 SEKUND", "Rychlost zpracování jedné smlouvy. Úspora stovek hodin měsíčně.", "5s"),
        ("98–99 % PŘESNOST", "34 kategorií (RČ, IBAN, jména, adresy, SPZ). Validováno na 231 smlouvách.", "99"),
        ("AUTO-OCR & AUDIT", "DOCX, PDF, PNG, JPG. PDF certifikát SHA-256 pro auditory.", "OCR"),
    ]
    tile_pad = 10
    top_pad = 8
    badge_w = 26
    badge_h = 14
    badge_font = 8
    for i, (title, desc, icon) in enumerate(tiles):
        row, col = i // 2, i % 2
        tx = M + col * (tile_w + G)
        ty = y - row * (tile_h + G)
        c.setFillColor(PANEL_2)
        c.setStrokeColor(LINE)
        c.rect(tx, ty - tile_h, tile_w, tile_h, fill=1, stroke=1)
        row_baseline = ty - top_pad - 10
        c.setFillColor(ACCENT)
        c.rect(tx + tile_pad, ty - top_pad - badge_h, badge_w, badge_h, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("DV-B", badge_font)
        c.drawCentredString(tx + tile_pad + badge_w / 2, row_baseline, icon)
        c.setFillColor(TEXT)
        c.setFont("DV-B", 9)
        c.drawString(tx + tile_pad + badge_w + 8, row_baseline, title)
        draw_para(c, tx + tile_pad, ty - top_pad - 14, tile_w - tile_pad * 2, desc, body_muted)
    y -= 2 * (tile_h + G) + SECT

    # ROI
    y = section_header(c, M, y, "NÁVRATNOST INVESTICE")
    c.setFillColor(TEXT)
    c.setFont("DV-B", 9)
    c.drawString(M, y - 10, "Zpracování 100 dokumentů měsíčně:")
    y -= 16
    c.setFillColor(TEXT_MUTED)
    c.setFont("DV", 8)
    c.drawString(M, y - 9, "Manuálně: 33 hodin práce | Vysoké riziko chyby | Náklad ~15 000 Kč+")
    y -= 14
    c.setFillColor(ACCENT_LIGHT)
    c.setFont("DV-B", 9)
    c.drawString(M, y - 9, "SKRYI: 10 minut | Přesnost 99 % | Zlomek ceny. Návratnost licence do 2 měsíců.")
    y -= SECT

    # TABULKA SKRYI vs. MANUÁLNĚ
    y = section_header(c, M, y, "SKRYI vs. MANUÁLNĚ")
    total_w = CONTENT_W
    col_w = [int(total_w * 0.32), int(total_w * 0.42), total_w - int(total_w * 0.32) - int(total_w * 0.42)]
    row_h = 14

    c.setStrokeColor(LINE)
    c.setFillColor(PANEL_2)
    c.rect(M, y - row_h, col_w[0], row_h, fill=1, stroke=1)
    c.setFillColor(ACCENT)
    c.rect(M + col_w[0], y - row_h, col_w[1], row_h, fill=1, stroke=1)
    c.setFillColor(PANEL_2)
    c.rect(M + col_w[0] + col_w[1], y - row_h, col_w[2], row_h, fill=1, stroke=1)
    c.setFillColor(TEXT)
    c.setFont("DV-B", 8)
    c.drawString(M + 4, y - 9, "Metrika")
    c.setFillColor(colors.white)
    c.drawString(M + col_w[0] + 4, y - 9, "SKRYI")
    c.setFillColor(TEXT_MUTED)
    c.drawString(M + col_w[0] + col_w[1] + 4, y - 9, "Manuálně")
    y -= row_h

    for r in [("Čas na 1 dokument", "< 5 s", "~20 min"), ("Měsíční čas (100 dok.)", "< 10 min", "~33 h"),
              ("Chybovost", "< 1–3 %", "5–15 %"), ("Auditní stopa", "PDF certifikát SHA-256", "žádná")]:
        c.setFillColor(PANEL)
        c.rect(M, y - row_h, total_w, row_h, fill=1, stroke=1)
        c.setFillColor(TEXT)
        c.setFont("DV", 8)
        c.drawString(M + 4, y - 9, r[0])
        c.setFillColor(ACCENT_LIGHT)
        c.setFont("DV-B", 8)
        c.drawString(M + col_w[0] + 4, y - 9, r[1])
        c.setFillColor(TEXT_MUTED)
        c.setFont("DV", 8)
        c.drawString(M + col_w[0] + col_w[1] + 4, y - 9, r[2])
        y -= row_h

    y -= SECT

    # CTA (modrý banner – nechat)
    cta_h = 36
    cta_y = max(M + 30, y - cta_h - 12)
    c.setFillColor(ACCENT)
    c.rect(M, cta_y, CONTENT_W, cta_h, fill=1, stroke=0)
    c.setFillColor(ACCENT_LIGHT)
    c.rect(M, cta_y + cta_h - 2, CONTENT_W, 2, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("DV-B", 10)
    c.drawCentredString(w / 2, cta_y + 18, "Přestaňte riskovat úniky dat. Získejte 14denní trial (Zero Risk).")

    y = cta_y - 18
    c.setFillColor(TEXT_MUTED)
    c.setFont("DV", 8)
    c.drawCentredString(w / 2, y - 8, "Kontakt info@nixminds.cz")

    c.save()
    print(f"[OK] One-pager v2: {out_path}")


if __name__ == "__main__":
    build()
