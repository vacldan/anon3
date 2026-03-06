#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jednotný skript: spustí testy anonymizace → agenty analyzují výsledky → sestaví čitelný report.

Použití:
  python run_full_test.py                    # všechny smlouvy
  python run_full_test.py --min 25 --max 30  # jen smlouvy 25-30
  python run_full_test.py --no-agents        # jen testy, bez agentů
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "_agent_reports"


def main():
    ap = argparse.ArgumentParser(description="Testy anonymizace + analýza agentů")
    ap.add_argument("--min", type=int, default=None, help="Smlouvy od čísla")
    ap.add_argument("--max", type=int, default=None, help="Smlouvy do čísla")
    ap.add_argument("--no-agents", action="store_true", help="Jen testy, bez agentů")
    args = ap.parse_args()

    # 1) Spusť testy
    cmd_test = [sys.executable, "test_data/run_anonymize_tests.py"]
    if args.min is not None:
        cmd_test.extend(["--min", str(args.min)])
    if args.max is not None:
        cmd_test.extend(["--max", str(args.max)])

    print("=" * 60)
    print("KROK 1: Testy anonymizace")
    print("=" * 60)
    ret = subprocess.run(cmd_test, cwd=str(PROJECT_ROOT))
    if ret.returncode != 0:
        print("[VAROVÁNÍ] Některé testy selhaly, pokračuji...")

    if args.no_agents:
        print("\n[OK] Hotovo (bez agentů). Report: _agent_reports/test_results.json")
        return 0

    # 2) Spusť agenty s reportem
    report_path = REPORTS_DIR / "test_results.json"
    if not report_path.exists():
        print("\n[CHYBA] test_results.json neexistuje. Nejprve spusť testy.")
        return 1

    print("\n" + "=" * 60)
    print("KROK 2: Analýza agentů (Ollama)")
    print("=" * 60)
    cmd_agents = [
        sys.executable, "-m", "agents.multi_agents",
        "--report", "_agent_reports/test_results.json",
    ]
    ret = subprocess.run(cmd_agents, cwd=str(PROJECT_ROOT))
    if ret.returncode != 0:
        return ret.returncode

    # 3) Vygeneruj čitelný report
    last_run = REPORTS_DIR / "last_run.json"
    report_md = REPORTS_DIR / "report.md"
    if last_run.exists():
        try:
            import json
            with open(last_run, encoding="utf-8") as f:
                data = json.load(f)
            md = []
            md.append("# Report z testů anonymizace SKRYI\n")

            # Pokud existuje souhrn z test_results.json, přidej tabulku smluv
            test_results_path = REPORTS_DIR / "test_results.json"
            if test_results_path.exists():
                try:
                    with open(test_results_path, encoding="utf-8") as tf:
                        tr = json.load(tf)
                    summary = tr.get("summary", {})
                    prehled = tr.get("prehled", [])
                    total = summary.get("total", len(prehled))
                    passed = summary.get("passed", 0)
                    failed = summary.get("failed", 0)
                    avg_score = summary.get("avg_score", 0)

                    md.append(
                        f"**Souhrn testů:** celkem {total}, prošlo {passed}, selhalo {failed}, "
                        f"průměrné skóre {avg_score}\n"
                    )
                    md.append("\n---\n## 0. Přehled smluv (skóre 0–10)\n")
                    md.append(
                        "| Smlouva | Skóre | Status | Problémy | Poznámka |\n"
                        "|---|---|---|---|---|"
                    )
                    for item in prehled:
                        smlouva = item.get("soubor", "")
                        score = item.get("score", "")
                        status = item.get("status", "")
                        probl = item.get("problémy", "")
                        note = item.get("poznamka", "")
                        md.append(
                            f"| {smlouva} | {score} | {status} | {probl} | {note} |"
                        )
                except Exception:
                    # Pokud se nepodaří načíst test_results.json, pokračuj jen s agentím reportem
                    pass

            md.append(f"\n\n**Úkol (zadaný agentům):** {data.get('task', '')[:200]}...\n")
            md.append("\n---\n## 1. Plán\n")
            md.append(data.get("plan", ""))
            md.append("\n\n---\n## 2. Návrh změn (Builder)\n")
            md.append(data.get("builder_proposal", ""))
            md.append("\n\n---\n## 3. QA kontrola\n")
            md.append(data.get("qa_review", ""))
            with open(report_md, "w", encoding="utf-8") as f:
                f.write("\n".join(md))
            print(f"\n[OK] Čitelný report: {report_md}")
        except Exception:
            pass

    print("\n" + "=" * 60)
    print("HOTOVO")
    print("=" * 60)
    print(f"  - Testy:     _agent_reports/test_results.json")
    print(f"  - Agenti:    _agent_reports/last_run.json")
    print(f"  - Report:    _agent_reports/report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
