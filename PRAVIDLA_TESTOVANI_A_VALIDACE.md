# Pravidla testování a validace anonymizace

## 0. ZLATÉ PRAVIDLO

**Po jakékoli změně v `anon72.py`:**
1. Znovu anonymizovat testovací smlouvy (uživatel vždy určí, které smlouvy testovat)
2. Spustit `python deep_validate.py`
3. Projít VŠECHNY hlášené chyby a opravit systematicky – ne jen jednotlivé příklady

**Nikdy neopravuj jen konkrétní případ, který uživatel nahlásil.** Vždy spusť validaci a podívej se, kolik smluv má stejný problém. Oprava musí být obecná.

**Které smlouvy testovat:** Vždy čekej na instrukce od uživatele. Netestuj automaticky žádný pevný rozsah smluv.

---

## 1. Princip: Základní tvar + varianty

**Základní pravidlo:** Když v dokumentu vidíme jméno v nominativu (základní tvar), použijeme ho jako kanonické jméno osoby. Všechny ostatní pády a tvary téhož jména mapujeme na stejný tag.

- `Julie Matoušková` (nominativ) → `[[PERSON_X]]`
- `Julii Matouškové` (dativ) → `[[PERSON_X]]`
- `Julií Matouškovou` (instrumentál) → `[[PERSON_X]]`

**Kanonická forma v mapě** musí být vždy v nominativu a se správnou diakritikou.

---

## 2. Kontrolní body validace

### 2.1 Kanonická forma (základní tvar v mapě)

| Pravidlo | Příklady správně | Příklady špatně |
|----------|------------------|-----------------|
| Ženská příjmení končí na **-ová** (s dlouhým ó) | Matoušková, Havránková, Peroutková | Matouškova, Havránkova |
| Ženská příjmení na **-á** | Pokorná, Malá, Tichá | Pokorna, Mala |
| Mužská příjmení na **-a** (Sýkora, Zíka, Štika) | Pavel Zíka, Martin Štika, Václav Holas | Pavel Zík, Martin Štik, Václav Holasa |
| Mužská příjmení s vložným **-e-** (Havel, Pavel) | Petr Havel | Petr Havl |
| Mužská příjmení konzonantní | Beran, Rendl, Konrád, Frydrych | Berana, Rendlo, Konráda |
| Mužská příjmení na **-ek** | Kolísek, Chrástek, Hájek | Kolísk, Chrástk |
| Mužská příjmení na **-ka** | Švestka, Paseka | Švestek (pokud je nominativ Švestka) |

### 2.2 Blacklist – ne-osoby v mapě

Do mapy osob nesmí patřit:
- **Zdvořilostní obraty:** Prosím (+ jméno) → „Prosím David" NENÍ osoba
- **Firemní reference:** Firma (+ příjmení) → „Firma Horáková" NENÍ osoba
- **Role/pozice:** Manager, Services, Risk, Account, Senior, Developer, Architect, Director, Chief, Officer

### 2.3 Křestní jméno musí být v names.json (OBECNÝ FILTR)

**Toto je hlavní obranná linie proti false positives.**

Křestní jméno (pozorovaná forma NEBO inferovaný nominativ) MUSÍ existovat v knihovně `cz_names.v1.json` nebo v rozšířeném seznamu běžných českých jmen. Pokud neexistuje → **neanonymizovat jako osobu**.

Toto řeší obecně:
- Názvy rolí (Manager, Developer, Career, Customer, Poboček...)
- Zdvořilostní obraty (Prosím)
- Firemní reference (Firma)
- Jakékoli jiné ne-jméno

Blacklist konkrétních slov je jen doplňková pojistka – hlavní filtr je **validace proti names.json**.

### 2.4 Úplnost anonymizace (žádné úniky)

- **Žádný tvar jména** z mapy (canonical ani varianty) nesmí zůstat v anonymizovaném dokumentu.
- Každý výskyt musí být nahrazen tagem `[[PERSON_X]]`.

### 2.5 Konzistence mapy s dokumentem

- Každá varianta v mapě musí odpovídat textu, který byl v původním dokumentu.
- Tag v mapě musí odpovídat tagu v anonymizovaném dokumentu.
- Osoby v mapě, jejichž tag se v anonymizovaném dokumentu nevyskytuje = **phantom osoby** (chyba).

### 2.6 Pravopis a diakritika

- Křestní jména: správná česká diakritika (Jan, Jana, Julie, ne Julie bez důvodu).
- Příjmení: -ová s dlouhým ó, ne -ova.

---

## 3. Metodika deep kontroly

**Důležité:** Po změně kódu v `anon72.py` je nutné znovu spustit anonymizaci, pak validaci. Validace porovnává výstupy anonymizace – pokud jsou staré, výsledky neodpovídají aktuálnímu kódu.

### Krok 1: Spuštění anonymizace

Smlouvy k testování určuje uživatel. Příklady spuštění:

Jedna smlouva:
```powershell
cd c:\Nixminds\skryi-clean
python anon72.py test_data\smlouva10.docx
```

Hromadně (příklad – rozsah dle pokynů uživatele):
```powershell
foreach ($n in 10..33) { if ($n -ne 30) { python anon72.py "test_data\smlouva$n.docx" } }
```

### Krok 2: Spuštění deep validace

**Všechny smlouvy v test_data/:**
```
python deep_validate.py
```
Bez argumentů projde všechny dostupné smlouvy v `test_data/` a na konci vypíše souhrnnou tabulku se skóre.

**Jedna smlouva:**
```
python deep_validate.py test_data/smlouva10.docx
```
(Skript automaticky najde nejnovější `_anon_*.docx` a `_map_*.txt` podle časového razítka.)

### Krok 3: Interpretace výstupu

Výstup `deep_validate.py` obsahuje pro každou smlouvu:

| Sekce | Číslo | Co kontroluje |
|-------|-------|---------------|
| **Kanonické formy** | 1 | Správný nominativ a diakritika příjmení |
| **Blacklist v osobách** | 1b | Záznamy obsahující Prosím, Firma, role (Manager, Developer...) |
| **Křestní jméno v names.json** | 1c | První slovo osoby existuje v knihovně jmen |
| **Úniky jmen** | 2 | Jména, která zůstala v anonymizovaném dokumentu |
| **Phantom osoby** | 3 | Osoby v mapě bez odpovídajícího tagu v dokumentu |
| **Varianty vs. zdroj** | 4 | Tvary v mapě, které se neobjevují ve zdrojovém dokumentu |
| **Nepokrytá jména** | 5 | Potenciální jména ve zdroji, která nejsou v mapě |

### Krok 4: Souhrnná tabulka

Na konci hromadného běhu se vypíše tabulka se sloupci:

```
Smlouva      Skóre      Kanon    Blklst   Names    Úniky    Phantom  Status
```

- **Skóre 9–10/10** = v pořádku (✓)
- **Skóre < 9** = vyžaduje opravu (✗)

---

## 4. Testovací dokument – očekávané vzory

Pro ověření všech pravidel by testovací dokument měl obsahovat:

### 4.1 Ženská příjmení -ová

- Julie Matoušková, Julii Matouškové, Julií Matouškovou
- Elodie Havránková, Elodii Havránkové, Elodií Havránkovou

### 4.2 Mužská příjmení -a

- Pavel Zíka, Pavla Zíky, Pavlovi Zíkovi
- Martin Štika, Martina Štiky, Martinovi Štikovi
- Ctibor Švestka, Ctibora Švestky, Ctiborovi Švestkovi

### 4.3 Mužská příjmení s vložným -e-

- Petr Havel, Petra Havla, Petrem Havlem, Petrovi Havlovi

### 4.4 Mužská příjmení konzonantní

- Emil Konrád, Emila Konráda, Emilovi Konrádovi
- Lubomír Frydrych, Lubomíra Frydrycha
- Přemysl Rendl, Přemysla Rendla, Přemyslovi Rendlovi

### 4.5 Mužská příjmení -ek

- Alex Kolísek, Alexe Kolíska, Alexovi Kolískovi
- Mihail Chrástek, Mihaila Chrástka, Mihailovi Chrástkovi

### 4.6 Příjmení na -ová (žena) – kontrola diakritiky

- Očekávaný canonical: vždy **-ová** (dlouhé ó), nikdy -ova.

### 4.7 Ne-osoby (nesmí se anonymizovat)

- „Prosím Davide, dodejte podklady" → Prosím NENÍ jméno
- „Firma Horáková s.r.o." → Firma NENÍ jméno
- „Account Manager", „Senior Developer", „Risk Manager" → role, NE osoby

---

## 5. Hodnocení (scoring)

| Kategorie | Max. srážka | Popis |
|-----------|-------------|-------|
| Kanonické formy | -3 | Správný nominativ a diakritika (0.5 za chybu) |
| Blacklist v osobách | -2 | Prosím, Firma, role nesmí být osoby (0.5 za chybu) |
| Křestní jméno v names.json | -2 | První slovo musí být v knihovně jmen (0.5 za chybu) |
| Úniky jmen | -3 | Žádné jméno nezůstalo v dokumentu (1 za únik) |
| Phantom osoby | -2 | Všechny osoby v mapě mají tag v dokumentu (0.5 za phantom) |
| **Celkem** | **10** | |

**Minimální akceptovatelné skóre:** 9/10 (s tolerancí pro edge cases).

---

## 6. Interpretace výstupu deep_validate.py

| Sekce | Význam | Co dělat |
|-------|--------|----------|
| **1. Chyby kanonických forem** | Základní tvar v mapě je špatně (např. -ova místo -ová, Štik místo Štika) | Opravit `infer_surname_nominative` v anon72.py |
| **1b. Blacklist v osobách** | Slova jako Prosím, Firma, Manager detekována jako součást osoby | Přidat do `critical_blacklist` / `role_words` v anon72.py |
| **1c. Křestní jméno mimo names.json** | První slovo osoby (křestní jméno) není v knihovně cz_names.v1.json | Buď přidat do blacklistu (pokud to je role/nesmysl), nebo do rozšířeného seznamu v deep_validate.py (pokud to je legitimní jméno chybějící v knihovně) |
| **2. Úniky jmen** | Tvar z mapy zůstal v anonymizovaném dokumentu | Kontrola `variants_for_surname` / `variants_for_first` – chybí varianta |
| **3. Phantom osoby** | Osoba v mapě, jejíž tag není v dokumentu | Kontrola AUTO-OPRAVA – měla by tyto odstranit |
| **4. Varianty v mapě bez textu ve zdroji** | Mapovaná varianta se ve zdroji nevyskytuje | Může být OK (generovaná varianta); nebo chyba v mapování |
| **5. Nepokrytá jména** | Potenciální jména ve zdroji, která nejsou v mapě | Možné přehlédnutí detekce – zkontrolovat, zda jde o jméno nebo název firmy/role |

---

## 7. Doporučený postup po změně kódu

1. **Anonymizovat** testovací smlouvy (dle pokynů uživatele)
2. **Spustit** `python deep_validate.py`
3. **Projít** souhrnnou tabulku – pokud něco má skóre < 9, podívat se na detail
4. **Priorita oprav:**
   - Sekce 1 (kanonické formy) → opravit `infer_surname_nominative`
   - Sekce 1b (blacklist) → přidat slova do `critical_blacklist` / `role_words`
   - Sekce 1c (names.json) → blacklist nebo rozšířit knihovnu
   - Sekce 2 (úniky) → opravit generování variant
   - Sekce 3 (phantomy) → opravit auto-opravu
5. **Po opravě** → znovu od bodu 1 (anonymizovat → validovat)
6. **Hotovo** až průměrné skóre ≥ 9.0 a žádná smlouva nemá kritickou chybu (sekce 1, 1b, 1c, 2)

---

## 8. Soubory a nástroje

| Soubor | Účel |
|--------|------|
| `anon72.py` | Hlavní anonymizátor |
| `deep_validate.py` | Validační skript (kontroly 1–5 + souhrnná tabulka) |
| `cz_names.v1.json` | Knihovna českých křestních jmen (MVČR) |
| `test_data/smlouva10.docx` – `smlouva33.docx` | Testovací smlouvy |
| `test_data/smlouvaXX_anon_*.docx` | Anonymizované výstupy |
| `test_data/smlouvaXX_map_*.txt` | Mapy osob (textové) |
| `test_data/smlouvaXX_map_*.json` | Mapy osob (JSON) |
