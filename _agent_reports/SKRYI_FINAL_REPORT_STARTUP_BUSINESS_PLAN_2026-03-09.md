# SKRYI Final Report
## Startup dokumentace + business plán

**Datum:** 9. března 2026  
**Verze:** Final v1.0  
**Účel dokumentu:** Podklad pro startup dokumentaci, obchodní plán, licenční strategii a produkční readiness.

---

## 1) Vstupy a rámec

Tento dokument vychází z:

- `SKRYI_TECHNICAL_DOCUMENTATION (1).md`
- `TECHNICAL_DOCUMENTATION.md`
- pracovních chatů k tématům: kvalita anonymizace, minimální score, GDPR leaky, striktní validátor V2, chyby kanonických jmen (např. Kučer/Kučera, Machal/Machala), produkční připravenost a monetizace/licence.

Pracovní požadavek z chatů byl:

- cílit minimálně `9/10` na smlouvu,
- nulový leak citlivých údajů do anonymizovaných výstupů/map,
- zavést a používat striktní validaci V2,
- připravit produkt na komerční produkci.

---

## 2) Executive Summary

SKRYI je desktopový, plně offline nástroj pro GDPR anonymizaci dokumentů (primárně CZ/SK), postavený na Electron + Python architektuře s morfologicky orientovaným anonymizačním enginem. Hlavní diferenciátor je práce s pádovými tvary a deduplikací identit v inflektivních jazycích, včetně reverzibilní deanonymizace přes mapy.

Obchodně je SKRYI vhodný pro B2B segmenty s vysokým tlakem na compliance: advokacie, healthcare, veřejná správa, enterprise backoffice. Vhodný model je roční licence per workstation/per organizace s enterprise SLA a on-prem podporou.

Aktuální interní validace (09.03.2026) na 200 smlouvách:

- `191/200` PASS (práh >=9/10) v baseline,
- `191/200` PASS i ve striktním V2 režimu (pass pouze 10/10),
- `9` smluv je FAIL (série `smlouva_final_0x`), primárně kvůli detekovaným leakům/heuristickým false positives a jedné nekonzistenci mapy.

Závěr: produkt má silný technologický i komerční základ, ale před ostrou produkcí je potřeba uzavřít „hard gate“ na `200/200 PASS` ve V2 a formalizovat release governance.

---

## 3) Produkt a technologická hodnota

### 3.1 Co SKRYI řeší

- Odstranění PII z právních a provozních dokumentů.
- Zpracování dokumentů bez přenosu dat mimo zařízení (offline only).
- Pro CZ/SK problematiku řeší pádové varianty jmen, což bývá častý zdroj leaků.

### 3.2 Hlavní technologické výhody

- Morfologická inference jmen a příjmení (forward/backward přístup).
- Vícefázová deduplikace osob a tag remap přes celý dokument.
- Post-pass mechaniky (standalone jména, adresní čtvrti, role/blacklist filtry).
- Reversible anonymization (mapy + deanonymizační workflow).
- Generování auditních map a PDF reportu anonymizace.
- HW-bound licensing (HMAC podpis, HW fingerprint, AppData persistence).

### 3.3 Architektura

- GUI: Electron (`main.js`, IPC orchestrace).
- Engine: Python (`anon72.py`, CLI/watcher utility).
- Packaging: Nuitka kompilace + NSIS installer.
- License validation: samostatný validátor (`validate_license_standalone`).

---

## 4) Validace kvality a produkční readiness

### 4.1 Dřívější benchmark (report v repozitáři)

V `_agent_reports/test_results.md` je historický běh s výsledkem `185/185 PASS`, průměr `10.0/10`, bez leaků.

### 4.2 Aktuální re-run (09.03.2026)

Spuštěno:

- `python test_data/run_anonymize_tests.py`
- `python test_data/run_anonymize_tests_v2.py`

Výsledek (obě metody):

- Celkem: `200` smluv
- PASS: `191`
- FAIL: `9`
- Průměr: `9.8/10`
- S PII leakem: `9`
- Nekonzistentní mapa: `1`

FAIL soubory:

- `smlouva_final_01.docx`
- `smlouva_final_03.docx`
- `smlouva_final_04.docx`
- `smlouva_final_07.docx`
- `smlouva_final_08.docx`
- `smlouva_final_09.docx`
- `smlouva_final_11.docx`
- `smlouva_final_12.docx`
- `smlouva_final_13.docx`

### 4.3 Interpretace

- Jádro enginu je silné (191 smluv dává 10/10).
- Zbývající problém je zejména „edge-case governance“: kombinace heuristik, map quality pravidel a false positive/false negative hranic.
- Produkční claim „tip-top bez chybičky“ zatím není formálně splněn.

### 4.4 Hard production gate (doporučení)

Před komerčním nasazením zavést povinný gate:

- V2: `100% PASS (10/10)` na definovaném regression setu.
- `0` PII leak, `0` map inconsistency, `0` orphan/phantom.
- Freeze pravidel + podpis release reportu (QA + Product Owner).

---

## 5) GDPR, compliance a právní rámec

Podle dokumentace má SKRYI silné compliance základy:

- 100% lokální zpracování (bez cloudového přenosu dat).
- Žádné odesílání dokumentů/map třetím stranám.
- EULA jasně vymezuje roli uživatele jako správce osobních údajů.
- EULA zároveň explicitně stanovuje nutnost finální lidské kontroly výstupu.

Doporučení pro enterprise prodej:

- Přidat „Data Processing & Security Whitepaper“ (1–2 strany).
- Zavést release note šablonu „Known limitations + mitigations“.
- Mít standardizovaný „Validation Evidence Pack“ pro audit/IT security.

---

## 6) Trh a komerční potenciál

### 6.1 Cílové segmenty (beachhead)

1. Advokátní kanceláře a legal ops týmy.
2. Healthcare administrace a zdravotnické právní agendy.
3. Veřejná správa (smluvní agenda, spisy, žádosti).
4. BPO/shared services týmy pracující s citlivou dokumentací.

### 6.2 Value proposition (pro nákupčího)

- Nižší compliance riziko.
- Rychlejší anonymizace oproti ruční práci.
- Zajištění auditovatelnosti (mapa + report).
- Nasazení bez cloudového rizika.

### 6.3 Konkurenční výhoda

- Morfologická robustnost pro CZ/SK (častý slabý bod generických nástrojů).
- Offline by design.
- Enterprise-friendly licensing (HW-bound + audit stopa).

---

## 7) Licenční model a cenová strategie (návrh)

Poznámka: technická dokumentace definuje typy licencí (`trial`, `standard`, `professional`, `enterprise`), nikoli finální ceník. Níže je doporučená komerční struktura.

### 7.1 Doporučené licence

- `Trial` (30 dní): zdarma, omezený počet dokumentů, bez SLA.
- `Standard` (1 rok): malé týmy, 1 zařízení/licence.
- `Professional` (1 rok): rozšířené workflow (watcher, vyšší limity, priorita podpory).
- `Enterprise` (1 rok): multi-seat, centrální governance, SLA, onboarding.

### 7.2 Návrh cen (CZK, bez DPH)

- Trial: `0 Kč`
- Standard: `29 900 Kč / zařízení / rok`
- Professional: `79 900 Kč / zařízení / rok`
- Enterprise: od `390 000 Kč / rok` (balík + SLA)
- Volitelně: on-prem enterprise setup fee `120 000–450 000 Kč` dle rozsahu

### 7.3 Cenové zásady

- Cenu kotvit proti nákladům ruční anonymizace + riziku GDPR incidentu.
- U enterprise preferovat „land-and-expand“: pilot → rollout.
- Do smluv dát jasné SLA a support tiers (response/resolve časy).

---

## 8) Go-to-market plán (12 měsíců)

### Fáze 1 (M1–M3): Product hardening + reference piloty

- Uzavřít 9 fail případů na 200/200 PASS (V2).
- Vytvořit demo dataset + audit evidence balíček.
- Získat 3 pilotní zákazníky (legal/health/public).

### Fáze 2 (M4–M6): Komerční launch

- Zavést standardizovaný onboarding.
- Publikovat case studies (časová úspora, kvalita, audit trail).
- Budovat partnerský kanál (compliance konzultanti, legaltech partneři).

### Fáze 3 (M7–M12): Scale

- Enterprise pipeline + rámcové smlouvy.
- Rozšíření o sektorové slovníky/blacklisty.
- Připravit SK expansion a další inflektivní jazyky.

---

## 9) Finanční rámec (orientační scénáře)

### 9.1 Předpoklady

- Primární revenue: roční licence.
- Doplňkové revenue: onboarding, SLA, custom integrace.
- Cílem je vysoká gross margin software revenue.

### 9.2 Scénáře ARR (konec Year 1)

- Konzervativní: `25 zákazníků`, ARR ~ `3–5 mil. Kč`
- Realistický: `60 zákazníků`, ARR ~ `9–14 mil. Kč`
- Ambiciózní: `120 zákazníků`, ARR ~ `20–30 mil. Kč`

### 9.3 Klíčové KPI

- Pass rate na produkčním regression setu.
- Leak incidence na release (cílově 0).
- Conversion Trial → Paid.
- Net Revenue Retention (enterprise).
- Průměrná doba onboardingu.

---

## 10) Hlavní rizika a mitigace

### R1: Edge-case quality regressions

- Mitigace: release gate 100% V2 PASS, povinné regression běhy, diff review map.

### R2: False positives/false negatives v extrémních dokumentech

- Mitigace: sektorové policy packy + whitelist/blacklist governance.

### R3: Přehnané obchodní claimy vs. EULA realita

- Mitigace: marketing formulovat jako „asistenční nástroj“, ne „právní rozhodovací systém“.

### R4: Enterprise security due diligence

- Mitigace: připravený security compliance pack + auditní artefakty.

---

## 11) Doporučené rozhodnutí pro vedení

### Rozhodnutí A: Přímý production launch nyní

- Nedoporučeno, protože není splněn interní hard gate 200/200.

### Rozhodnutí B: 2–4 týdny hardening sprint + launch

- Doporučeno.
- Cíl sprintu: uzavřít 9 fail smluv, potvrdit 200/200 v baseline i V2, poté teprve komerční launch.

---

## 12) Akční plán (následujících 30 dní)

1. Založit „Production Gate Board“ (owner: Product + QA).
2. Opravit 9 fail případů (`smlouva_final_*`) jako samostatný quality sprint.
3. Zamrazit validační pravidla V2 pro release branch.
4. Připravit komerční balíček: ceník, SLA, onboarding nabídka, security one-pager.
5. Spustit 3 piloty s jasnou metrikou úspěchu (kvalita + čas + audit).

---

## 13) Final verdict

SKRYI má technologii i tržní potenciál na komerčně silný B2B produkt s důrazem na GDPR a offline bezpečnost. Pro bezpečný a důvěryhodný vstup do produkce je ale nutné uzavřít poslední quality gap (`9/200` fail) a formalizovat release governance.

Po splnění gate `200/200 PASS` je projekt připravený na standardní startup škálování (piloty → enterprise kontrakty → partner channel).

---

## Příloha A: Referenční artefakty v repozitáři

- `_agent_reports/test_results.json`
- `_agent_reports/test_results.md`
- `_agent_reports/test_results_v2.json`
- `_agent_reports/test_results_v2.md`
- `SKRYI_TECHNICAL_DOCUMENTATION (1).md`
- `TECHNICAL_DOCUMENTATION.md`
