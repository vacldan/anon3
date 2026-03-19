#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate SKRYI One-Pager PDF – structured layout with clear form and spacing."""

import os
from reportlab.lib import colors

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
FONT_DIR = os.path.join(ROOT_DIR, "fonts")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo5.png")

FONT_REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

# Palette
BG = colors.HexColor("#0A0F1C")
PANEL = colors.HexColor("#121A2B")
PANEL_2 = colors.HexColor("#162039")
ACCENT = colors.HexColor("#5A6BFF")
ACCENT_LIGHT = colors.HexColor("#9FB2FF")
TEXT = colors.HexColor("#F1F5FF")
TEXT_MUTED = colors.HexColor("#A5AFBF")
LINE = colors.HexColor("#23304B")

# Grid
M = 32          # margin
G = 16          # gap between elements
SECT = 28       # gap between major sections
CONTENT_W = 0   # set in build()


def draw_para(c, x, y_top, w, text, style):
    p = Paragraph(text, style)
    _, h = p.wrap(w, 1200)
    p.drawOn(c, x, y_top - h)
    return h


def section_header(c, x, y, label):
    """Draw section label with accent bar. Returns y after label."""
    c.setFillColor(ACCENT)
    c.rect(x, y - 8, 4, 10, fill=1, stroke=0)
    c.setFillColor(ACCENT_LIGHT)
    c.rect(x, y - 8, 4, 2, fill=1, stroke=0)
    c.setFillColor(TEXT)
    c.setFont("DV-B", 10)
    c.drawString(x + 10, y - 7, label)
    return y - 20


def build():
    pdfmetrics.registerFont(TTFont("DV", FONT_REG))
    pdfmetrics.registerFont(TTFont("DV-B", FONT_BOLD))

    w, h = A4
    global CONTENT_W
    CONTENT_W = w - M * 2

    c = canvas.Canvas(os.path.join(os.path.dirname(__file__), "SKRYI_OnePager.pdf"), pagesize=A4)
    c.setFillColor(BG)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    body = ParagraphStyle("body", fontName="DV", fontSize=9, leading=12, textColor=TEXT)
    body_muted = ParagraphStyle("body_muted", fontName="DV", fontSize=8.5, leading=11, textColor=TEXT_MUTED)
    headline = ParagraphStyle("headline", fontName="DV-B", fontSize=22, leading=26, textColor=TEXT)
    sub = ParagraphStyle("sub", fontName="DV", fontSize=9.5, leading=13, textColor=TEXT_MUTED)

    y = h - M

    # ─── HEADER ─────────────────────────────────────────────────────────
    c.setFillColor(TEXT_MUTED)
    c.setFont("DV", 8)
    c.drawRightString(w - M, y - 6, "GDPR compliant · 100% offline · SHA-256")
    y -= 24

    # ─── HERO (vlevo: oko + SKRYI, vpravo: text) ───────────────────────────
    left_w = 240   # prostor pro oko + nápis SKRYI
    right_w = CONTENT_W - left_w - G
    hero_y = y

    # Levá strana: velký nápis SKRYI + oko
    skryi_font_size = 52
    c.setFillColor(TEXT)
    c.setFont("DV-B", skryi_font_size)
    c.drawString(M, hero_y - skryi_font_size, "SKRYI")

    img_h = 0
    if os.path.exists(LOGO_PATH):
        img_w, img_h = left_w, 110
        if HAS_PIL:
            try:
                with Image.open(LOGO_PATH) as im:
                    rw, rh = im.size
                    ratio = min(left_w / rw, 110 / rh)
                    img_w = int(rw * ratio)
                    img_h = int(rh * ratio)
            except Exception:
                pass
        img_y = hero_y - skryi_font_size - 12 - img_h
        c.drawImage(LOGO_PATH, M, img_y, width=img_w, height=img_h, mask="auto")

    left_block_h = skryi_font_size + 12 + img_h

    # Pravá strana: nadpis + podtitul
    text_x = M + left_w + G
    head_h = draw_para(c, text_x, hero_y, right_w, "Offline GDPR anonymizace dokumentů, která konečně rozumí češtině.", headline)
    sub_h = draw_para(c, text_x, hero_y - head_h - 8, right_w,
        "SKRYI Document Suite. Desktopová aplikace garantující 100% ochranu dat bez opuštění vašeho zařízení.", sub)

    y = hero_y - max(head_h + sub_h + 12, left_block_h) - SECT

    # ─── PROBLÉM ────────────────────────────────────────────────────────
    y = section_header(c, M, y, "PROBLÉM")
    c.setFillColor(TEXT)
    c.setFont("DV-B", 9.5)
    c.drawString(M, y - 10, "Anglická umělá inteligence na českou morfologii nestačí.")
    y -= 18
    bullets = [
        "Většina softwarů je navržena pro angličtinu. V češtině má pouhé jméno \"Jan Novák\" více než 14 různých tvarů.",
        "Běžná AI tyto tvary nerozpozná a propustí je → fatální úniky PII.",
        "Manuální začerňování je pomalé, drahé a náchylné k chybám.",
    ]
    for b in bullets:
        y -= draw_para(c, M, y, CONTENT_W, "• " + b, body_muted) + 6
    y -= SECT

    # ─── ŘEŠENÍ (2 cards) ────────────────────────────────────────────────
    y = section_header(c, M, y, "ŘEŠENÍ")
    card_w = (CONTENT_W - G) / 2
    card_h = 52
    pad = 12

    # Card 1
    c.setFillColor(PANEL)
    c.setStrokeColor(LINE)
    c.rect(M, y - card_h, card_w, card_h, fill=1, stroke=1)
    c.setFillColor(ACCENT)
    c.rect(M + pad, y - 18, 14, 14, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("DV-B", 8)
    c.drawCentredString(M + pad + 7, y - 11, "MI")
    c.setFillColor(TEXT)
    c.setFont("DV-B", 9.5)
    c.drawString(M + pad + 18, y - 12, "Unikátní morfologická inteligence")
    draw_para(c, M + pad + 18, y - 18, card_w - pad - 26,
        "Bidirekcionální morfologická inference. Z jakéhokoliv pádu systém odvodí základní tvar a bezchybně jej skryje.", body_muted)

    # Card 2
    c.setFillColor(PANEL)
    c.setStrokeColor(LINE)
    c.rect(M + card_w + G, y - card_h, card_w, card_h, fill=1, stroke=1)
    c.setFillColor(ACCENT)
    c.rect(M + card_w + G + pad, y - 18, 14, 14, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("DV-B", 8)
    c.drawCentredString(M + card_w + G + pad + 7, y - 11, "ZT")
    c.setFillColor(TEXT)
    c.setFont("DV-B", 9.5)
    c.drawString(M + card_w + G + pad + 18, y - 12, "100 % Offline (Zero Trust)")
    draw_para(c, M + card_w + G + pad + 18, y - 18, card_w - pad - 26,
        "Žádná data do cloudu. Aplikace běží plně a bezpečně na vašem zařízení.", body_muted)

    y -= card_h + SECT

    # ─── KLÍČOVÉ ÚDAJE (2×2 grid) ───────────────────────────────────────
    y = section_header(c, M, y, "KLÍČOVÉ ÚDAJE")
    stat_w = (CONTENT_W - G) / 2
    stat_h = 38
    row1 = y
    row2 = y - stat_h - 10

    def stat_box(x, yb, val, lbl):
        c.setFillColor(PANEL_2)
        c.setStrokeColor(LINE)
        c.rect(x, yb - stat_h, stat_w, stat_h, fill=1, stroke=1)
        c.setFillColor(ACCENT_LIGHT)
        c.setFont("DV-B", 11)
        c.drawString(x + 12, yb - 16, val)
        c.setFillColor(TEXT_MUTED)
        c.setFont("DV", 8)
        c.drawString(x + 12, yb - 28, lbl)

    stat_box(M, row1, "98–99 % přesnost", "Validováno na 231 reálných smlouvách")
    stat_box(M + stat_w + G, row1, "< 5 s / dokument", "Typická smlouva")
    stat_box(M, row2, "34 kategorií údajů", "Jména, adresy, rodná čísla, e-maily, IBAN, SPZ…")
    stat_box(M + stat_w + G, row2, "100 % offline", "Zero Trust, data neopouští zařízení")

    y = row2 - stat_h - SECT

    # ─── TABULKA (SKRYI vs. Manuálně) – celá šířka stránky ─────────────────
    y = section_header(c, M, y, "SKRYI vs. MANUÁLNĚ")
    total_w = CONTENT_W
    col_w = [
        int(total_w * 0.32),   # Metrika
        int(total_w * 0.42),   # SKRYI (více místa pro „PDF certifikát SHA-256“)
        total_w - int(total_w * 0.32) - int(total_w * 0.42),  # Manuálně
    ]
    row_h = 16

    # Header
    c.setStrokeColor(LINE)
    c.setFillColor(PANEL_2)
    c.rect(M, y - row_h, col_w[0], row_h, fill=1, stroke=1)
    c.setFillColor(ACCENT)
    c.rect(M + col_w[0], y - row_h, col_w[1], row_h, fill=1, stroke=1)
    c.setFillColor(PANEL_2)
    c.rect(M + col_w[0] + col_w[1], y - row_h, col_w[2], row_h, fill=1, stroke=1)
    c.setFillColor(TEXT)
    c.setFont("DV-B", 9)
    c.drawString(M + 6, y - 11, "Metrika")
    c.setFillColor(colors.white)
    c.drawString(M + col_w[0] + 6, y - 11, "SKRYI")
    c.setFillColor(TEXT_MUTED)
    c.drawString(M + col_w[0] + col_w[1] + 6, y - 11, "Manuálně")
    y -= row_h

    rows = [
        ("Čas na 1 dokument", "< 5 s", "~20 min"),
        ("Měsíční čas (100 dok.)", "< 10 min", "~33 h"),
        ("Chybovost", "< 1–3 %", "5–15 %"),
        ("Auditní stopa", "PDF certifikát SHA-256", "žádná"),
    ]
    for r in rows:
        c.setFillColor(PANEL)
        c.rect(M, y - row_h, total_w, row_h, fill=1, stroke=1)
        c.setFillColor(TEXT)
        c.setFont("DV", 9)
        c.drawString(M + 6, y - 11, r[0])
        c.setFillColor(ACCENT_LIGHT)
        c.setFont("DV-B", 9)
        c.drawString(M + col_w[0] + 6, y - 11, r[1])
        c.setFillColor(TEXT_MUTED)
        c.setFont("DV", 9)
        c.drawString(M + col_w[0] + col_w[1] + 6, y - 11, r[2])
        y -= row_h

    y -= SECT

    # ─── CTA ────────────────────────────────────────────────────────────
    cta_h = 32
    cta_y = max(M, y - cta_h - 8)
    c.setFillColor(ACCENT)
    c.rect(M, cta_y, CONTENT_W, cta_h, fill=1, stroke=0)
    c.setFillColor(ACCENT_LIGHT)
    c.rect(M, cta_y + cta_h - 3, CONTENT_W, 3, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("DV-B", 11)
    c.drawCentredString(w / 2, cta_y + 20, "Zabezpečte svá data a získejte zpět svůj čas.")
    c.setFont("DV", 9)
    c.drawCentredString(w / 2, cta_y + 8, "Kontaktujte nás pro Demo")

    c.save()
    print(f"[OK] One-pager: {os.path.join(os.path.dirname(__file__), 'SKRYI_OnePager.pdf')}")


if __name__ == "__main__":
    build()
