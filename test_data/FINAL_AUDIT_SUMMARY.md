# Finální audit – shrnutí

**Datum:** 13. 3. 2026  
**Kód:** anon72 (poslední verze)

---

## 1. Full test (run_full_test.py)

- **Celkem smluv:** 231
- **Úspěšně zpracováno:** 229
- **Chyby:** 2 (OSError při ukládání – smlouva-uver-variant-19, smlouva-uver-variant-2)
- **Leaky / map issues:** 0

---

## 2. Manuální audit (manual_final_audit.py)

Kontrola smlouva po smlouvě, mapa po mapě:

- **Zkontrolováno:** 231 smluv
- **Leaky (PII v anonymizovaném dokumentu):** 0
- **Problémy v mapách:** 0

**Závěr:** Žádné úniky původních osobních údajů do anonymizovaných dokumentů.

---

## 3. Leak scanner (leak_scanner.py)

Heuristická kontrola potenciálních leaků:

- **Naskenováno:** 236 souborů
- **Nalezeno:** 3 potenciální alerty (pravděpodobně false positive):

| Soubor | Alert | Poznámka |
|--------|-------|----------|
| smlouva14_anon.docx | Street+num: "Na Františku, Praha 1" | "Praha 1" = městská část, ne adresa; pattern match |
| smlouva15_anon.docx | Stejný kontext | Stejný případ |
| smlouva7_anon.docx | Street+num u "Předmět: Půjčka 150 000 Kč" | "150 000" = částka úvěru, ne adresa |

**Závěr:** Tyto 3 alerty jsou false positive – manuální audit nepotvrdil skutečné leaky.

---

## 4. Targeted audit (_targeted_audit.py)

Kontrola false positives v ADDRESS a PERSON:

- **ADDRESS false positives:** 8 (většinou „starts with lowercase“ – např. „byt 5“, „sídlem Tyršova“ – platné adresy)
- **ADDRESS duplicity:** 0
- **PERSON false positives:** 0

---

## 5. Full address audit (_full_addr_audit.py)

- **Celkem ADDRESS záznamů:** 1152
- **OK (pattern match):** 707
- **SUSPECT (k ruční kontrole):** 445

Suspect záznamy jsou většinou adresy v nestandardním formátu (např. „adrese Růžová…“, „bytem Dlouhá…“), nikoliv nutně chyby. Od verze s prefix-strippingem se z hodnot v mapě odstraňují prefixy „adrese“, „bytem“ atd., takže v mapě jsou čisté adresy.

---

## 6. Full person audit (_full_person_audit.py)

- **Celkem PERSON záznamů:** ~2490 (všechny mapy)
- **OK (pattern match):** typické jméno (2+ slova, bez číslic, bez s.r.o./a.s.)
- **SUSPECT (k ruční kontrole):** číslice v hodnotě, firmy (s.r.o., a.s.), speciální znaky, délka > 60 znaků

Skript prochází sekci OSOBY ve všech `*_map.txt` a kategorizuje záznamy jako OK/SUSPECT pro manuální review.

---

## Shrnutí pro ruční kontrolu

1. **Leaky:** Žádné potvrzené – manuální audit 0 issues.
2. **Nestabilní výsledky:** 8 drobných ADDRESS formátů (lowercase), 445 suspect adres k případné ruční kontrole.
3. **Doporučení:** Pro finální validaci projít výstup `_full_addr_audit.py` (suspect entries), `_full_person_audit.py` (suspect persons) a případně `_targeted_audit.py` (8 lowercase adres).

---

## Spuštění auditů

```bash
# Full test (re-anonymizace + kontrola)
python test_data/run_full_test.py

# Manuální audit smlouva po smlouvě
python test_data/manual_final_audit.py

# Leak scanner
python leak_scanner.py

# Targeted audit (false positives)
python test_data/_targeted_audit.py

# Full address audit
python test_data/_full_addr_audit.py

# Full person audit
python test_data/_full_person_audit.py
```
