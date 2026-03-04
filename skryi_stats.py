# skryi_stats.py - Lightweight statistics logging for SKRYI
import json
import os
from datetime import datetime
from pathlib import Path


def _get_stats_path() -> Path:
    """Vrátí cestu ke stats souboru vedle skriptu."""
    # Hledej stats.json ve složce aplikace
    script_dir = Path(__file__).parent
    return script_dir / "skryi_stats.json"


def _load_stats() -> dict:
    """Načte existující statistiky nebo vrátí prázdné."""
    path = _get_stats_path()
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "total_anonymized": 0,
        "total_deanonymized": 0,
        "total_pdf_converted": 0,
        "total_pdf_ocr": 0,
        "total_persons_found": 0,
        "monthly": {},
    }


def _save_stats(stats: dict):
    """Uloží statistiky do souboru."""
    path = _get_stats_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except OSError:
        pass  # Tiché selhání - statistiky nejsou kritické


def _month_key() -> str:
    return datetime.now().strftime("%Y-%m")


def log_anonymization(persons_found: int = 0, entities_total: int = 0):
    """Zaloguje úspěšnou anonymizaci."""
    stats = _load_stats()
    month = _month_key()

    stats["total_anonymized"] = stats.get("total_anonymized", 0) + 1
    stats["total_persons_found"] = stats.get("total_persons_found", 0) + persons_found

    if month not in stats.get("monthly", {}):
        stats.setdefault("monthly", {})[month] = {}
    m = stats["monthly"][month]
    m["anonymized"] = m.get("anonymized", 0) + 1
    m["persons_found"] = m.get("persons_found", 0) + persons_found

    _save_stats(stats)


def log_deanonymization():
    """Zaloguje úspěšnou deanonymizaci."""
    stats = _load_stats()
    month = _month_key()

    stats["total_deanonymized"] = stats.get("total_deanonymized", 0) + 1

    if month not in stats.get("monthly", {}):
        stats.setdefault("monthly", {})[month] = {}
    m = stats["monthly"][month]
    m["deanonymized"] = m.get("deanonymized", 0) + 1

    _save_stats(stats)


def log_pdf_conversion(ocr: bool = False):
    """Zaloguje úspěšnou PDF konverzi."""
    stats = _load_stats()
    month = _month_key()

    stats["total_pdf_converted"] = stats.get("total_pdf_converted", 0) + 1
    if ocr:
        stats["total_pdf_ocr"] = stats.get("total_pdf_ocr", 0) + 1

    if month not in stats.get("monthly", {}):
        stats.setdefault("monthly", {})[month] = {}
    m = stats["monthly"][month]
    m["pdf_converted"] = m.get("pdf_converted", 0) + 1
    if ocr:
        m["pdf_ocr"] = m.get("pdf_ocr", 0) + 1

    _save_stats(stats)


def get_stats() -> dict:
    """Vrátí aktuální statistiky."""
    return _load_stats()
