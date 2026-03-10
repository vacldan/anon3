---
name: generate-10-gdpr-test-contracts
overview: Vytvořit 10 různých českých testovacích smluv s bohatými GDPR-citlivými údaji a uložit je jako DOCX pro testování anon72.py.
todos:
  - id: design-scenarios
    content: Navrhnout 10 různých smluvních scénářů a přiřadit jim typy PII k pokrytí.
    status: completed
  - id: write-contract-texts
    content: Napsat české texty 10 smluv s bohatými PII a variabilními pády jmen.
    status: completed
  - id: generate-docx-files
    content: Vytvořit z textů 10 DOCX souborů `smlouva_gdpr_test_01–10.docx` do složky test_data.
    status: completed
  - id: smoke-test-anon72
    content: Namátkově otestovat anon72.py na 1–2 nových smlouvách a zkontrolovat generované mapy a reporty.
    status: completed
isProject: false
---

### Cíl

Vytvořit **10 odlišných českých smluv** jako **DOCX vstupy** pro `anon72.py`, každou s bohatým mixem PII (jména ve tvarech, adresy, rodná čísla, účty, IP, karty, hesla…), strukturou podobnou současné testovací smlouvě, ale s různými osobami a scénáři.

### Postup

- **1. Návrh šablony a variant scénářů**
  - Vycházet z existující smlouvy (poskytovatel/objednatel + další osoby, GDPR pasáže).
  - Navrhnout 10 scénářů (např. IT služby, nájem bytu, pracovní smlouva, zpracovatelská smlouva, zdravotní služby…), aby se lišil kontext i formulace.
  - U každého scénáře si vypsat, jaké typy PII má obsahovat (osoby, adresy, RČ, účty, karty, IP/MAC, přístupové údaje, SPZ/VIN atd.).
- **2. Generování textů pro 10 smluv**
  - Pro každou smlouvu vytvořit unikátní sadu českých jmen (muž/žena, různé příjmení) a použít je v různých pádech v průběhu textu.
  - Vložit různé typy PII dle plánu (včetně kombinací typu: RČ + datum narození + adresa + kontakt + přístupové údaje).
  - Zachovat právně-smluvní strukturu (články I–IX, hlavičky, závěr), ale drobně měnit znění, aby smlouvy nebyly jen copy–paste.
- **3. Uložení textů a převod na DOCX**
  - Pro každou smlouvu navrhnout cílové názvy souborů jako např. `[test_data/smlouva_gdpr_test_01.docx]` až `[test_data/smlouva_gdpr_test_10.docx]`.
  - Při implementaci (mimo tento plán) pro každý text vygenerovat odpovídající DOCX se zachováním odstavců a čitelného formátování.
- **4. Rychlá manuální kontrola**
  - Ověřit, že každá DOCX smlouva se bez chyb otevře v MS Word / LibreOffice.
  - Namátkově pustit `anon72.py` na 1–2 nové smlouvy a zkontrolovat, že se vytvoří `_anon.docx`, `_map.json`, `_map.txt` a `_report.pdf`.
- **5. Dokumentace pro další použití**
  - Krátce popsat v existující dokumentaci nebo README, že v `test_data` je sada smluv `smlouva_gdpr_test_01–10.docx` určená pro regresní testování anonymizačního enginu.

