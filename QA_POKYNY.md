# QA POKYNY – Kontrola kvality anonymizovaných smluv a map

## Účel dokumentu

Tento dokument obsahuje kompletní pokyny pro AI, která bude provádět systematickou kontrolu kvality výstupů anonymizačního nástroje SKRYI. Kontrola se provádí nad trojicí souborů:

1. **Originální smlouva** (`smlouva.docx`) – zdrojový dokument
2. **Anonymizovaná smlouva** (`smlouva_anon.docx`) – výstup s nahrazenými údaji
3. **Mapa nahrazení** (`smlouva_map.json`) – strojově čitelná mapa všech náhrad

---

## 1. VSTUPNÍ SOUBORY A JEJICH FORMÁT

### 1.1 Anonymizovaná smlouva (`*_anon.docx`)

Obsahuje původní text s nahrazenými GDPR-citlivými údaji ve formátu:

```
[[TYP_ČÍSLO]]
```

Příklady: `[[PERSON_1]]`, `[[ADDRESS_1]]`, `[[PHONE_2]]`, `[[RC_1]]`, `[[DATE_3]]`

### 1.2 JSON mapa (`*_map.json`)

Struktura:

```json
{
  "version": "1.0",
  "generated_at": "2026-03-04T15:30:45.123456",
  "source_file": "smlouva.docx",
  "entities": [
    {
      "type": "PERSON",
      "label": "[[PERSON_1]]",
      "original": "Jan Novák",
      "occurrences": 1
    },
    {
      "type": "PERSON",
      "label": "[[PERSON_1]]",
      "original": "Jana Nováková",
      "occurrences": 3
    },
    {
      "type": "ADDRESS",
      "label": "[[ADDRESS_1]]",
      "original": "Nerudova 42, 118 00 Praha 1",
      "occurrences": 2
    }
  ]
}
```

**Důležité:**
- Jeden label (např. `[[PERSON_1]]`) může mít více záznamů – kanonický tvar (nominativ) + skloněné varianty
- Kanonický tvar MUSÍ být uveden jako **první** záznam pro daný label
- Kanonický tvar může mít `"occurrences": 0` pokud se v textu vyskytuje jen ve skloněných tvarech
- Citlivé údaje (karty, pasy) mohou být zobrazeny jako `***REDACTED_###***`

### 1.3 Kompletní seznam typů entit

| Anglický tag (v dokumentu/JSON) | Český tag (v TXT mapě) | Popis |
|---|---|---|
| `PERSON` | `OSOBA` | Jména osob |
| `ADDRESS` | `ADRESA` | Adresy |
| `RC` | `RC` | Rodná čísla |
| `DATE` | `DATUM` | Data (obecná) |
| `BIRTH_DATE` | `DATUM_NAR` | Data narození |
| `BANK_ACCOUNT` | `UCET` | Bankovní účty |
| `IBAN` | `IBAN` | IBAN |
| `CARD` | `KARTA` | Platební karty |
| `ICO` | `ICO` | IČO |
| `DIC` | `DIC` | DIČ |
| `PHONE` | `TEL` | Telefonní čísla |
| `EMAIL` | `EMAIL` | E-mailové adresy |
| `PASSPORT` | `PAS` | Cestovní pasy |
| `ID_CARD` | `OP` | Občanské průkazy |
| `DRIVER_LICENSE` | `RP` | Řidičské průkazy |
| `LICENSE_PLATE` | `SPZ` | SPZ |
| `VIN` | `VIN` | VIN kódy |
| `IP` | `IP` | IP adresy |
| `USERNAME` | `USERNAME` | Uživatelská jména |
| `PASSWORD` | `HESLO` | Hesla |
| `API_KEY` | `API_KEY` | API klíče |
| `SECRET` | `SECRET` | Secrets |
| `SSH_KEY` | `SSH_KEY` | SSH klíče |
| `HOST` | `HOST` | Hostnames |
| `INSURANCE_ID` | `POJISTENEC` | Čísla pojištěnce |
| `RFID` | `RFID` | RFID/Badge |
| `LINKEDIN` | `LINKEDIN` | LinkedIn |
| `FACEBOOK` | `FACEBOOK` | Facebook |
| `INSTAGRAM` | `INSTAGRAM` | Instagram |
| `SKYPE` | `SKYPE` | Skype |

---

## 2. KONTROLA A – MAPA VS. ORIGINÁL (žádné phantom entity)

### Cíl
Každá entita v mapě MUSÍ existovat v originální smlouvě. Mapa nesmí obsahovat nic, co v originále není.

### Postup

1. Načti JSON mapu a originální smlouvu.
2. Pro KAŽDÝ záznam v `entities`:
   - Ověř, že hodnota `"original"` se vyskytuje v textu originální smlouvy.
   - **Výjimka pro PERSON:** Kanonický tvar (nominativ) s `"occurrences": 0` nemusí být přímo v textu – je odvozený. V tom případě MUSÍ existovat alespoň jedna varianta (jiný záznam se stejným labelem) s `"occurrences" > 0`, která v textu JE.
3. Pokud je v mapě entita, která v originále NEEXISTUJE a není kanonickým tvarem s variantami – označ jako **PHANTOM ENTITU**.

### Chyby k hlášení

| Kód | Závažnost | Popis |
|---|---|---|
| `A-PHANTOM` | S1-KRITICKÁ | Entita v mapě neexistuje v originálním dokumentu |
| `A-PHANTOM-CANON` | S2-VYSOKÁ | Kanonický tvar osoby neexistuje v dokumentu a nemá žádné platné varianty |

---

## 3. KONTROLA B – ÚPLNOST ANONYMIZACE

### Cíl
V anonymizované smlouvě nesmí zůstat žádný neanonymizovaný GDPR-citlivý údaj.

### Postup

1. Načti text anonymizované smlouvy.
2. Vyhledej výskyty následujících vzorů (tyto údaje by NEMĚLY zůstat v anonymizovaném textu):

#### 3.1 Rodná čísla
- Vzor: `\b\d{6}[/]?\d{3,4}\b` (6 číslic, volitelné lomítko, 3-4 číslice)
- Příklady: `920415/1234`, `9204151234`

#### 3.2 Telefonní čísla
- Vzory: `\+?\d{3}[\s-]?\d{3}[\s-]?\d{3}`, `\+?\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}`
- Příklady: `+420 777 888 999`, `777888999`, `777 888 999`

#### 3.3 E-mailové adresy
- Vzor: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`

#### 3.4 IČO
- Vzor: `\b\d{8}\b` v kontextu slov "IČ", "IČO", "identifikační číslo"

#### 3.5 DIČ
- Vzor: `\bCZ\d{8,10}\b`

#### 3.6 IBAN
- Vzor: `\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{0,4}\b`

#### 3.7 Bankovní účty
- Vzor: `\b\d{1,6}-?\d{6,10}/\d{4}\b`

#### 3.8 Čísla OP / pasů / ŘP
- OP: `\b\d{9}\b` v kontextu "občanský průkaz", "OP č."
- Pas: `\b\d{7,8}\b` v kontextu "cestovní pas", "pas č."

#### 3.9 SPZ
- Vzor: `\b\d[A-Z]{1,2}\s?\d{4,5}\b`

#### 3.10 Adresy
- Hledej spojení: ulice + číslo popisné + PSČ + město
- Vzor PSČ: `\b\d{3}\s?\d{2}\b`

#### 3.11 Jména osob
- **KRITICKÉ:** Porovnej jména z mapy s anonymizovaným textem.
- Pro KAŽDOU osobu z mapy (kanonický tvar + všechny varianty) ověř, že se ŽÁDNÁ z forem nevyskytuje v anonymizovaném textu.
- Hledej i částečné výskyty – samotná příjmení, samotná křestní jména.

#### 3.12 Data narození
- Vzor v kontextu "narozen", "nar.", "datum narození": `\b\d{1,2}\.\s?\d{1,2}\.\s?\d{4}\b`

### Chyby k hlášení

| Kód | Závažnost | Popis |
|---|---|---|
| `B-LEAK-PERSON` | S1-KRITICKÁ | Jméno osoby zůstalo v anonymizovaném textu |
| `B-LEAK-RC` | S1-KRITICKÁ | Rodné číslo zůstalo neanonymizované |
| `B-LEAK-PHONE` | S2-VYSOKÁ | Telefon zůstal neanonymizovaný |
| `B-LEAK-EMAIL` | S2-VYSOKÁ | E-mail zůstal neanonymizovaný |
| `B-LEAK-ADDRESS` | S2-VYSOKÁ | Adresa zůstala neanonymizovaná |
| `B-LEAK-BANK` | S2-VYSOKÁ | Bankovní údaje zůstaly neanonymizované |
| `B-LEAK-ICO` | S3-STŘEDNÍ | IČO zůstalo neanonymizované |
| `B-LEAK-DIC` | S3-STŘEDNÍ | DIČ zůstalo neanonymizované |
| `B-LEAK-DATE` | S3-STŘEDNÍ | Datum narození zůstalo neanonymizované |
| `B-LEAK-DOC` | S3-STŘEDNÍ | Číslo dokladu zůstalo neanonymizované |
| `B-LEAK-OTHER` | S3-STŘEDNÍ | Jiný citlivý údaj zůstal neanonymizovaný |

---

## 4. KONTROLA C – SPRÁVNOST TAGOVÁNÍ OSOB

### Cíl
V mapě nesmí být zkomolená jména. Role, tituly a funkce nesmí být označeny jako PERSON.

### 4.1 Zkomolená jména

Ověř, že každá hodnota `"original"` u typu `PERSON`:
- Obsahuje platné české (nebo cizí) křestní jméno a příjmení
- Není nesmyslná kombinace písmen (např. "Fiael Novák" místo "Fiala Novák")
- Kanonický tvar je v 1. pádu (nominativ): "Jan Novák", ne "Jana Nováka"
- Křestní jméno a příjmení nejsou prohozená

**Jak poznat zkomolené jméno:**
- Jméno neexistuje jako české křestní jméno ani příjmení
- Jméno obsahuje podezřelé shluky souhlásek nebo samohlásek
- Jméno vypadá jako překlep z OCR (záměna podobných písmen: l↔1, O↔0, rn↔m)

### 4.2 Role a tituly tagované jako PERSON

**KRITICKÉ:** Následující kategorie slov se NESMÍ vyskytovat jako hodnota `"original"` u typu `PERSON`. Pokud se takové slovo objeví jako entita typu PERSON, je to chyba – mělo být ignorováno:

#### Právní role a funkce
- právník, advokát, obhájce, znalec, soudce, soudkyně, státní zástupce, prokurátor
- notář, mediátor, rozhodce, insolvenční správce, likvidátor
- právní zástupce, statutární zástupce, zmocněnec
- svědek, svědkyně, stěžovatel, žalobce, žalovaný

#### Rodinné vztahy
- manžel, manželka, partner, partnerka, druh, družka
- otec, matka, syn, dcera, bratr, sestra
- dědeček, babička, vnuk, vnučka, strýc, teta
- tchán, tchýně, švagr, švagrová, snoubenec, snoubenka
- ex-manžel, ex-manželka, vdovec, vdova

#### Profesní role a tituly
- ředitel, ředitelka, jednatel, jednatelka, manažer, vedoucí
- auditor, konzultant, specialista, koordinátor, analytik
- lékař, doktor, sestra, primář, přednosta, farmaceut
- učitel, pedagog, lektor, profesor, docent

#### Smluvní strany a pozice
- kupující, prodávající, pronajímatel, nájemce, podnájemce
- zaměstnanec, zaměstnavatel, zástupce, zmocněnec
- dlužník, věřitel, ručitel, spoludlužník
- obžalovaný, obviněný, podezřelý, odsouzený
- pacient, pacientka, klient, zákazník

#### Oslovení
- pan, paní, slečna

**Pravidlo:** Pokud je v `"original"` POUZE role/titul BEZ konkrétního jména (např. `"original": "jednatel"` nebo `"original": "právní zástupce"`), je to CHYBA. Pokud je role součástí celého jména (např. `"original": "jednatel Jan Novák"`), pak by mělo být tagováno pouze jméno "Jan Novák", ne celý řetězec včetně role.

### Chyby k hlášení

| Kód | Závažnost | Popis |
|---|---|---|
| `C-GARBLED` | S2-VYSOKÁ | Zkomolené/nesmyslné jméno v mapě |
| `C-ROLE-AS-PERSON` | S2-VYSOKÁ | Role/titul/funkce tagována jako PERSON |
| `C-WRONG-CASE` | S3-STŘEDNÍ | Kanonický tvar není v nominativu |
| `C-SWAPPED` | S3-STŘEDNÍ | Prohozené křestní jméno a příjmení |

---

## 5. KONTROLA D – SPRÁVNOST TAGOVÁNÍ ADRES

### Cíl
Adresy musí obsahovat POUZE adresní údaje, bez přebytečného textu.

### Postup

Pro každou entitu typu `ADDRESS` ověř:

1. **Žádné „ocasky" textu** – hodnota `"original"` nesmí obsahovat text, který není součástí adresy:
   - **Špatně:** `"Nerudova 42, 118 00 Praha 1, zastoupená"` (slovo "zastoupená" není součástí adresy)
   - **Správně:** `"Nerudova 42, 118 00 Praha 1"`

2. **Žádné prefixy** – hodnota nesmí začínat slovy jako "bytem", "sídlem", "na adrese", "trvale bytem":
   - **Špatně:** `"bytem Nerudova 42, 118 00 Praha 1"`
   - **Správně:** `"Nerudova 42, 118 00 Praha 1"`

3. **Kompletní adresa** – ideálně by měla obsahovat ulici + číslo + PSČ + město (pokud jsou v originále)

4. **Bez jmen osob** – adresa nesmí obsahovat jméno osoby jako součást

### Typické chyby adres

| Problém | Příklad špatně | Příklad správně |
|---|---|---|
| Trailing text | `"Hlavní 5, 110 00 Praha 1, jednající"` | `"Hlavní 5, 110 00 Praha 1"` |
| Prefix | `"se sídlem Václavská 12, 120 00 Praha 2"` | `"Václavská 12, 120 00 Praha 2"` |
| Osobní údaj v adrese | `"Jan Novák, Hlavní 5, Praha"` | `"Hlavní 5, Praha"` |
| Fragment textu | `"110 00 Praha 1, IČO"` | `"110 00 Praha 1"` |

### Chyby k hlášení

| Kód | Závažnost | Popis |
|---|---|---|
| `D-TRAILING` | S2-VYSOKÁ | Adresa obsahuje přebytečný text na konci |
| `D-PREFIX` | S3-STŘEDNÍ | Adresa obsahuje prefix (bytem, sídlem, apod.) |
| `D-PERSON-IN-ADDR` | S2-VYSOKÁ | Adresa obsahuje jméno osoby |
| `D-FRAGMENT` | S3-STŘEDNÍ | Adresa je neúplný fragment |

---

## 6. KONTROLA E – SPRÁVNOST TYPŮ ENTIT

### Cíl
Každá entita musí být pod správným typem tagu.

### Postup

Pro každou entitu v mapě ověř, že typ (`"type"`) odpovídá obsahu (`"original"`):

| Typ | Očekávaný obsah | Příklady |
|---|---|---|
| `PERSON` | Jméno osoby (křestní + příjmení) | Jan Novák, Marie Svobodová |
| `ADDRESS` | Poštovní adresa | Hlavní 42, 110 00 Praha |
| `RC` | Rodné číslo (6+3-4 číslic) | 920415/1234 |
| `DATE` | Datum | 15. března 2024, 1.1.2023 |
| `BIRTH_DATE` | Datum narození | 15.4.1992 |
| `PHONE` | Telefonní číslo | +420 777 888 999 |
| `EMAIL` | E-mailová adresa | jan@firma.cz |
| `ICO` | 8-místné číslo | 12345678 |
| `DIC` | CZ + 8-10 číslic | CZ12345678 |
| `BANK_ACCOUNT` | Číslo účtu/kód banky | 123456-7890123456/0100 |
| `IBAN` | Mezinárodní číslo účtu | CZ65 0800 0000 1920 0014 5399 |

### Typické chyby typů

| Problém | Popis |
|---|---|
| Role jako PERSON | `"type": "PERSON", "original": "jednatel"` – jednatel je role, ne osoba |
| Datum jako PERSON | `"type": "PERSON", "original": "1. ledna"` – zjevně datum |
| Adresa jako PERSON | `"type": "PERSON", "original": "Praha"` – je to místo, ne osoba |
| Telefonní číslo jako ICO | `"type": "ICO", "original": "+420..."` – to je telefon |

### Chyby k hlášení

| Kód | Závažnost | Popis |
|---|---|---|
| `E-WRONG-TYPE` | S2-VYSOKÁ | Entita přiřazena ke špatnému typu |
| `E-AMBIGUOUS` | S4-NÍZKÁ | Entita by mohla patřit pod jiný typ (sporné) |

---

## 7. KONTROLA F – KONZISTENCE DOKUMENT ↔ MAPA

### Cíl
Každý tag v anonymizovaném dokumentu musí mít odpovídající záznam v mapě a naopak.

### Postup

1. **Extrakce tagů z dokumentu:** Najdi všechny výskyty vzoru `\[\[[A-Z_]+_\d+\]\]` v anonymizovaném textu.
2. **Extrakce tagů z mapy:** Sesbírej všechny unikátní hodnoty `"label"` z JSON mapy.
3. **Porovnání:**
   - Tag v dokumentu, který NENÍ v mapě = **OSIŘELÝ TAG**
   - Tag v mapě, který NENÍ v dokumentu = **NEPOUŽITÝ TAG** (varování, ne nutně chyba)

### Chyby k hlášení

| Kód | Závažnost | Popis |
|---|---|---|
| `F-ORPHAN-TAG` | S1-KRITICKÁ | Tag v dokumentu nemá záznam v mapě |
| `F-UNUSED-TAG` | S4-NÍZKÁ | Tag v mapě se nevyskytuje v dokumentu |
| `F-DUP-NUMBERING` | S3-STŘEDNÍ | Duplicitní číslování tagů (dva různé PERSON_1) |

---

## 8. KONTROLA G – DEDUPLIKACE OSOB

### Cíl
Stejná osoba nesmí mít dva různé tagy. Různé osoby nesmí sdílet jeden tag.

### Postup

1. **Detekce duplicit:** Hledej osoby se stejným příjmením a podobným/stejným křestním jménem ale různými tagy:
   - `[[PERSON_1]]: Jan Novák` a `[[PERSON_3]]: Jana Nováková` → pokud jde o manželský pár, jsou to 2 různé osoby = OK
   - `[[PERSON_1]]: Jan Novák` a `[[PERSON_3]]: Jan Novák` → duplicita = CHYBA
   - `[[PERSON_1]]: Jan Novák` a `[[PERSON_3]]: Janu Nováka` → skloněný tvar téže osoby = CHYBA (měly mít stejný tag)

2. **Kontrola mužských/ženských forem:**
   - Novák/Nováková – typicky dvě různé osoby (muž/žena), ALE:
   - Pokud se jedná o tutéž osobu jen ve skloněném tvaru, musí mít stejný tag
   - Kontext smlouvy rozhoduje (je zmíněn manžel/manželka? dva různí lidé?)

### Chyby k hlášení

| Kód | Závažnost | Popis |
|---|---|---|
| `G-DUP-PERSON` | S2-VYSOKÁ | Stejná osoba má dva různé tagy |
| `G-MERGED-DIFFERENT` | S2-VYSOKÁ | Dvě různé osoby mají stejný tag |

---

## 9. KLASIFIKACE ZÁVAŽNOSTI

| Úroveň | Popis | Příklady |
|---|---|---|
| **S1 – KRITICKÁ** | Únik osobních údajů, nefunkční anonymizace | Jméno zůstalo v textu, phantom entita, osiřelý tag |
| **S2 – VYSOKÁ** | Chybné tagování, ztráta informace | Role jako PERSON, zkomolené jméno, trailing text v adrese |
| **S3 – STŘEDNÍ** | Nepřesnost, neoptimální výstup | Špatný nominativ, prefix v adrese, chybějící IČO |
| **S4 – NÍZKÁ** | Kosmetická chyba, varování | Nepoužitý tag v mapě, sporný typ entity |

---

## 10. FORMÁT VÝSTUPNÍHO REPORTU

Report musí mít následující strukturu:

```
# QA REPORT – [název souboru]

## Souhrn
- Celkový počet entit v mapě: X
- Počet nalezených chyb: Y
- Z toho: S1: X, S2: X, S3: X, S4: X
- Celkové hodnocení: PASS / FAIL (FAIL pokud existuje jakákoliv S1 nebo S2 chyba)

## Nalezené chyby

### S1 – KRITICKÉ
1. [A-PHANTOM] Entita [[ADDRESS_3]] s hodnotou "Neznámá 99, Praha" neexistuje v originálním dokumentu.
2. [B-LEAK-PERSON] Jméno "Jan Novák" zůstalo neanonymizované na straně 3, odstavec 2.

### S2 – VYSOKÉ
1. [C-ROLE-AS-PERSON] [[PERSON_5]] obsahuje hodnotu "jednatel" – jde o roli, ne o osobu.
2. [D-TRAILING] [[ADDRESS_1]] hodnota "Hlavní 5, 110 00 Praha 1, zastoupená" obsahuje přebytečný text "zastoupená".

### S3 – STŘEDNÍ
1. [C-WRONG-CASE] [[PERSON_2]] kanonický tvar "Jana Nováka" není v nominativu. Správně: "Jan Novák".

### S4 – NÍZKÉ
1. [F-UNUSED-TAG] [[PHONE_3]] je v mapě, ale nevyskytuje se v anonymizovaném dokumentu.

## Detail entit

### PERSON (X entit)
| Tag | Kanonický tvar | Varianty | Status |
|---|---|---|---|
| [[PERSON_1]] | Jan Novák | Jana Nováka, Janu Novákovi | OK |
| [[PERSON_2]] | Marie Svobodová | Marie Svobodové | OK |
| [[PERSON_5]] | jednatel | – | CHYBA: C-ROLE-AS-PERSON |

### ADDRESS (X entit)
| Tag | Hodnota | Status |
|---|---|---|
| [[ADDRESS_1]] | Hlavní 5, 110 00 Praha 1, zastoupená | CHYBA: D-TRAILING |
| [[ADDRESS_2]] | Pražská 12, 130 00 Praha 3 | OK |

### Ostatní entity
| Tag | Typ | Hodnota | Status |
|---|---|---|---|
| [[PHONE_1]] | PHONE | +420 777 888 999 | OK |
| [[RC_1]] | RC | 920415/1234 | OK |
| [[ICO_1]] | ICO | 12345678 | OK |
```

---

## 11. POSTUP PRÁCE – KROK ZA KROKEM

1. **Načti všechny tři soubory** (originál, anonymizovanou verzi, JSON mapu).
2. **Proveď kontrolu A** (mapa vs. originál) – ověř existenci entit.
3. **Proveď kontrolu B** (úplnost anonymizace) – hledej úniky v anonymizovaném textu.
4. **Proveď kontrolu C** (osoby) – zkontroluj jména, role, zkomolení.
5. **Proveď kontrolu D** (adresy) – zkontroluj přebytečný text.
6. **Proveď kontrolu E** (typy) – ověř správné přiřazení typů.
7. **Proveď kontrolu F** (konzistence) – porovnej tagy dokument ↔ mapa.
8. **Proveď kontrolu G** (deduplikace) – hledej duplicitní/sloučené osoby.
9. **Sestav report** ve formátu z kapitoly 10.
10. **Vyhodnoť** – PASS pokud žádná S1/S2 chyba, jinak FAIL.

---

## 12. DŮLEŽITÉ POZNÁMKY

### Co NENÍ chyba
- Kanonický tvar osoby s `"occurrences": 0` – pokud existují varianty s `occurrences > 0`
- Skloněné tvary příjmení (Nováka, Novákovi, Novákem) – to je správné chování systému
- Ženské tvary příjmení (Nováková od Novák) – pokud jde o jinou osobu, je to OK
- Slova jako "Praha", "Brno" jako součást adresy (ne jako samostatná PERSON entita)
- Obecná data (1.1.2024) – mohou, ale nemusí být anonymizována (záleží na kontextu)
- Citlivé hodnoty zobrazené jako `***REDACTED***` v mapě – to je záměr

### Co JE vždy chyba
- Jakékoliv celé jméno osoby (křestní + příjmení) zůstávající v anonymizovaném textu
- Rodné číslo v anonymizovaném textu
- Role/titul (jednatel, advokát, manželka, apod.) tagovaná jako PERSON
- Entita v mapě, která neexistuje v originálním dokumentu
- Text za adresou, který k adrese nepatří (trailing fragments)
- Zkomolené jméno, které nevypadá jako reálné české jméno
- Tag v anonymizovaném dokumentu bez záznamu v mapě
