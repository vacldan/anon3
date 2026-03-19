#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jednoduchá UI pro anonymizaci a validaci SKRYI.
Spusť: python validation_ui.py
"""

import os
import subprocess
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
except ImportError:
    print("Chyba: tkinter není k dispozici. Nainstaluj Python s podporou tkinter.")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
TEST_DATA = ROOT / "test_data"

# (tlačítko, popis, příkaz nebo skript)
ACTIONS = [
    (
        "Kompletní anonymizace všech smluv",
        "Anonymizuje všechny .docx v test_data (jména, adresy, RČ, telefony, emaily…). Výstup: *_anon.docx, *_map.json, *_map.txt",
        ["anonymize", "test_data"],  # speciální – spustí anon72 --batch
    ),
    (
        "Ověření osob a leaků (všechny smlouvy)",
        "Zkontroluje, že mapa obsahuje očekávané osoby a že v anonymizovaném textu nejsou vidět původní jména.",
        "test_data/verify_name_order_results.py",
    ),
    (
        "Full leak audit",
        "Kontrola úniků: originály z mapy v textu, PII regex mimo tagy, typy entit. Report do full_leak_audit_report.txt.",
        "test_data/full_leak_audit.py",
    ),
    (
        "Přehled detekovaných entit",
        "Vypíše, které typy entit (PERSON, PHONE, IBAN…) byly detekovány v každé smlouvě.",
        "test_data/analyze_entity_detection.py",
    ),
    (
        "Finální verifikace",
        "Kontrola NAME-LEAK (příjmení mimo tag), ORPHAN-DOC (tag bez mapy), MAP-DUP (duplicitní osoby).",
        "verify_final.py",
    ),
    (
        "Kontrola výsledků (osoby, telefony, SPZ)",
        "Pro každou smlouvu: osoby v mapě, gender mismatch, name leaky, pojištěnec jako telefon, falešné SPZ.",
        "test_data/check_results.py",
    ),
    (
        "Leak scanner",
        "Skenuje všechny _anon.docx na potenciální úniky (města u adres, PSČ, ulice+číslo).",
        "leak_scanner.py",
    ),
]


def run_action(action):
    """Spustí akci (skript nebo batch anonymizaci) a zobrazí výstup."""
    if isinstance(action, list) and action[0] == "anonymize":
        cmd = [sys.executable, str(ROOT / "anon72.py"), "--batch", str(TEST_DATA)]
        label = "Kompletní anonymizace (anon72 --batch test_data)"
    else:
        path = ROOT / action
        if not path.exists():
            output.insert(tk.END, f"CHYBA: Soubor neexistuje: {path}\n", "error")
            return
        cmd = [sys.executable, str(path)]
        label = action

    output.delete(1.0, tk.END)
    output.insert(tk.END, f"Spouštím: {label}\n", "info")
    output.insert(tk.END, "=" * 60 + "\n")
    output.update()

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        out = result.stdout or ""
        err = result.stderr or ""
        if out:
            output.insert(tk.END, out, "stdout")
        if err:
            output.insert(tk.END, err, "stderr")
        if result.returncode != 0:
            output.insert(tk.END, f"\n[Exit code: {result.returncode}]\n", "error")
    except Exception as e:
        output.insert(tk.END, f"CHYBA: {e}\n", "error")


def main():
    global output
    win = tk.Tk()
    win.title("SKRYI – Anonymizace a validace")
    win.minsize(520, 450)
    win.geometry("750x600")

    # Popis nahoře
    desc_frame = ttk.Frame(win, padding=(10, 10, 10, 5))
    desc_frame.pack(fill=tk.X)
    ttk.Label(
        desc_frame,
        text="Anonymizace a kontrola anonymizovaných smluv. Klikni na tlačítko pro spuštění.",
        font=("Segoe UI", 9),
        wraplength=700,
    ).pack(anchor=tk.W)

    # Horní panel – tlačítka
    frame_btns = ttk.Frame(win, padding=10)
    frame_btns.pack(fill=tk.X)

    ttk.Label(frame_btns, text="Akce:", font=("", 10, "bold")).pack(anchor=tk.W)

    for i, (label, desc, action) in enumerate(ACTIONS):
        f = ttk.Frame(frame_btns)
        f.pack(pady=3, anchor=tk.W)
        btn = ttk.Button(f, text=label, command=lambda a=action: run_action(a))
        btn.pack(side=tk.LEFT)
        ttk.Label(f, text=f" – {desc}", font=("Segoe UI", 8), foreground="#555").pack(side=tk.LEFT, padx=(8, 0))

    # Výstup
    ttk.Label(win, text="Výstup:", font=("", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(5, 0))
    output = scrolledtext.ScrolledText(
        win,
        wrap=tk.WORD,
        font=("Segoe UI", 10),
        height=25,
        bg="#1e1e1e",
        fg="#d4d4d4",
        insertbackground="#d4d4d4",
    )
    output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    output.tag_config("info", foreground="#569cd6")
    output.tag_config("stdout", foreground="#d4d4d4")
    output.tag_config("stderr", foreground="#ce9178")
    output.tag_config("error", foreground="#f48771")

    output.insert(tk.END, "Klikni na tlačítko pro spuštění akce.\n", "info")

    win.mainloop()


if __name__ == "__main__":
    main()
