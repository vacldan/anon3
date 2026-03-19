"""
Jednoduché UI pro generování licencí SKRYI
Zadej HW ID, vyber délku, vygeneruj .lic soubor
"""

import sys
from pathlib import Path

# Přidej kořen projektu do path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from licensing.license_generator import create_license, save_license_file
from tkinter import Tk, ttk, StringVar, IntVar, messagebox, filedialog, Spinbox


# Presety licencí: (popisek, typ, dny)
PRESETS = [
    ("Free trial 10 dní", "trial", 10),
    ("Free trial 1 měsíc", "trial", 30),
    ("Standard 1 rok", "standard", 365),
    ("Vlastní délka", "custom", 0),
]


def main():
    root = Tk()
    root.title("SKRYI License Generator")
    root.geometry("480x380")
    root.resizable(True, True)

    # Styl
    style = ttk.Style()
    style.configure("TLabel", padding=4)
    style.configure("TButton", padding=6)

    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)

    # HW ID
    ttk.Label(main_frame, text="Hardware ID (16 znaků):").pack(anchor="w")
    hw_var = StringVar()
    hw_entry = ttk.Entry(main_frame, textvariable=hw_var, width=40, font=("Consolas", 11))
    hw_entry.pack(fill="x", pady=(0, 12))
    # hw_entry prázdný – uživatel vloží HW ID

    # Typ licence
    ttk.Label(main_frame, text="Typ licence:").pack(anchor="w", pady=(8, 0))
    preset_var = IntVar(value=0)
    for i, (label, _, _) in enumerate(PRESETS):
        rb = ttk.Radiobutton(main_frame, text=label, variable=preset_var, value=i)
        rb.pack(anchor="w")

    # Vlastní délka (skryto když není custom)
    custom_frame = ttk.Frame(main_frame)
    custom_frame.pack(anchor="w", pady=(4, 12))
    ttk.Label(custom_frame, text="Počet dní:").pack(side="left")
    days_var = StringVar(value="30")
    days_spin = Spinbox(custom_frame, from_=1, to=3650, textvariable=days_var, width=8)
    days_spin.pack(side="left", padx=(8, 0))

    # Zákazník (volitelné, pro free trial stačí prázdné)
    ttk.Label(main_frame, text="Zákazník (volitelné):").pack(anchor="w", pady=(8, 0))
    customer_frame = ttk.Frame(main_frame)
    customer_frame.pack(fill="x", pady=(0, 4))
    name_var = StringVar(value="Free Trial")
    email_var = StringVar(value="trial@skryi.cz")
    ttk.Entry(customer_frame, textvariable=name_var, width=25).pack(side="left", padx=(0, 8))
    ttk.Entry(customer_frame, textvariable=email_var, width=25).pack(side="left")

    def get_duration():
        idx = preset_var.get()
        _, typ, days = PRESETS[idx]
        if typ == "custom":
            try:
                v = days_var.get()
                return int(v) if v else 30
            except (ValueError, TypeError):
                return 30
        return days

    def get_license_type():
        idx = preset_var.get()
        return PRESETS[idx][1]

    def do_generate():
        hw_raw = hw_var.get().strip()
        hw = hw_raw.replace("-", "").replace(" ", "").upper()

        if not hw:
            messagebox.showerror("Chyba", "Zadejte Hardware ID.")
            return
        if len(hw) != 16:
            messagebox.showerror("Chyba", f"HW ID musí mít 16 znaků (má {len(hw)}).\nZadáno: {hw}")
            return
        if not all(c in "0123456789ABCDEF" for c in hw):
            messagebox.showerror("Chyba", "HW ID může obsahovat jen hex znaky (0-9, A-F).")
            return

        duration = get_duration()
        if duration < 1:
            messagebox.showerror("Chyba", "Délka musí být alespoň 1 den.")
            return

        license_type = get_license_type()
        if license_type == "custom":
            license_type = "standard"

        try:
            license_data = create_license(
                customer_name=name_var.get().strip() or "Free Trial",
                customer_email=email_var.get().strip() or "trial@skryi.cz",
                hw_id=hw,
                license_type=license_type,
                duration_days=duration,
                notes="",
            )
        except Exception as e:
            messagebox.showerror("Chyba", str(e))
            return

        # Uložit jako
        default_name = f"license_{license_data['license_key'][:8]}.lic"
        path = filedialog.asksaveasfilename(
            defaultextension=".lic",
            filetypes=[("Licenční soubor", "*.lic"), ("Všechny soubory", "*.*")],
            initialfile=default_name,
        )
        if path:
            save_license_file(license_data, path)
            messagebox.showinfo(
                "Hotovo",
                f"Licence uložena:\n{path}\n\n"
                f"Platnost do: {license_data['expires_at'][:10]}\n"
                f"Typ: {license_data['type']}",
            )

    ttk.Button(main_frame, text="Vygenerovat a uložit licenci", command=do_generate).pack(
        pady=(16, 0)
    )

    root.mainloop()


if __name__ == "__main__":
    main()
