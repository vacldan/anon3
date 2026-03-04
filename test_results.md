# Výsledky testů anonymizace SKRYI

## Shrnutí

| Metrika | Hodnota |
|---------|---------|
| Celkem smluv | 33 |
| Prošlo (score>=9) | 1 |
| Selhalo | 32 |
| Průměr score | 6.4/10 |
| S PII leakem | 15 |
| Nekonzistentní mapa | 29 |

## Přehled po smlouvách

| Soubor | Score | Status | Problémy |
|--------|-------|--------|----------|
| smlouva 30.docx | 8/10 | FAIL | mapa |
| smlouva0.docx | 4/10 | FAIL | PII:2, mapa |
| smlouva10.docx | 4/10 | FAIL | PII:2, mapa |
| smlouva11.docx | 7/10 | FAIL | PII:1 |
| smlouva12.docx | 4/10 | FAIL | PII:2, mapa |
| smlouva13.docx | 8/10 | FAIL | regex:1 |
| smlouva14.docx | 0/10 | FAIL | PII:6, regex:1, mapa |
| smlouva15.docx | 0/10 | FAIL | PII:6, regex:1, mapa |
| smlouva16.docx | 2/10 | FAIL | PII:2, regex:1, mapa |
| smlouva17.docx | 5/10 | FAIL | PII:3 |
| smlouva18.docx | 8/10 | FAIL | mapa |
| smlouva19.docx | 8/10 | FAIL | mapa |
| smlouva2.docx | 4/10 | FAIL | PII:2, mapa |
| smlouva20.docx | 8/10 | FAIL | mapa |
| smlouva21.docx | 8/10 | FAIL | mapa |
| smlouva22.docx | 8/10 | FAIL | mapa |
| smlouva23.docx | 8/10 | FAIL | mapa |
| smlouva24.docx | 8/10 | FAIL | mapa |
| smlouva25.docx | 8/10 | FAIL | mapa |
| smlouva26.docx | 8/10 | FAIL | mapa |
| smlouva27.docx | 8/10 | FAIL | mapa |
| smlouva28.docx | 8/10 | FAIL | mapa |
| smlouva29.docx | 8/10 | FAIL | mapa |
| smlouva3.docx | 10/10 | OK | — |
| smlouva31.docx | 6/10 | FAIL | regex:1, mapa |
| smlouva32.docx | 8/10 | FAIL | mapa |
| smlouva33.docx | 6/10 | FAIL | regex:1, mapa |
| smlouva4.docx | 5/10 | FAIL | PII:1, mapa |
| smlouva5.docx | 8/10 | FAIL | mapa |
| smlouva6.docx | 8/10 | FAIL | mapa |
| smlouva7.docx | 5/10 | FAIL | PII:1, mapa |
| smlouva8.docx | 8/10 | FAIL | mapa |
| smlouva9.docx | 5/10 | FAIL | PII:1, mapa |

---

## Detaily chyb po smlouvách

### smlouva 30.docx — 8/10

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[PERSON_45]]', '[[BIRTH_ID_43]]', '[[BIRTH_ID_45]]', '[[BIRTH_ID_46]]', '[[BIRTH_ID_47]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_3]]: kanonické příjmení 'Machael' se nevyskytuje v originálu, ale varianta 'Ctislav Machala' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_17]]: kanonické příjmení 'Fialová' se nevyskytuje v originálu, ale varianta 'Fialové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva0.docx — 4/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Innovation Labs`
- `Nová`

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_1]]: kanonické příjmení 'Nováek' se nevyskytuje v originálu, ale varianta 'Martinem Novákem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_7]]: kanonické příjmení 'Dvořáek' se nevyskytuje v originálu, ale varianta 'Petrem Dvořákem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-PARTIAL-NAME] [[PERSON_10]] = 'Nová' vypadá jako neúplné jméno (pouze jedno slovo).
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_15]]: kanonické příjmení 'Poláčková' se nevyskytuje v originálu, ale varianta 'Jitkou Poláčkovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva10.docx — 4/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Praha`
- `Nové`

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[EMAIL_14]]', '[[PHONE_17]]', '[[EMAIL_13]]', '[[PERSON_55]]', '[[BIRTH_ID_13]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_9]]: kanonické příjmení 'Štik' se nevyskytuje v originálu, ale varianta 'Martin Štika' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [E-WRONG-TYPE] [[PERSON_16]] = 'Poboček Praha' vypadá jako město / pobočka, ne osoba.
- [D-PARTIAL-NAME] [[PERSON_18]] = 'Malá' vypadá jako neúplné jméno (pouze jedno slovo).
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_24]]: kanonické příjmení 'Havl' se nevyskytuje v originálu, ale varianta 'Petrem Havlem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [C-ROLE-AS-PERSON] [[PERSON_28]] = 'Support Program' obsahuje ne-osobu / roli ('Support Program').
- [C-ROLE-AS-PERSON] [[PERSON_28]] = 'Support Program' – první slovo 'Support' je role/pozice, ne křestní jméno.
- [C-ROLE-AS-PERSON] [[PERSON_29]] = 'Career Support' obsahuje ne-osobu / roli ('Career Support').
- [C-ROLE-AS-PERSON] [[PERSON_29]] = 'Career Support' – první slovo 'Career' je role/pozice, ne křestní jméno.
- [C-ROLE-AS-PERSON] [[PERSON_40]] = 'Sokol Invest' obsahuje 'Invest', pravděpodobně firma/role, ne osoba.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_41]]: kanonické příjmení 'Nový' se nevyskytuje v originálu, ale varianta 'Nové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [blacklist_as_person] [[PERSON_43]] = 'Prosím David' obsahuje zdvořilostní obrat / prefix ('Prosím'), který nemá být součástí osoby.
- [C-ROLE-AS-PERSON] [[PERSON_45]] = 'Customer Success' obsahuje ne-osobu / roli ('Customer Success').
- [C-ROLE-AS-PERSON] [[PERSON_45]] = 'Customer Success' – první slovo 'Customer' je role/pozice, ne křestní jméno.

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_6]] = 'na adrese Komenského 58, Brno' obsahuje prefix 'na adrese', který podle QA pravidel do adresy nepatří.

---

### smlouva11.docx — 7/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Papin Food`

---

### smlouva12.docx — 4/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Praha`
- `Nové`

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[EMAIL_14]]', '[[PHONE_17]]', '[[EMAIL_13]]', '[[PERSON_55]]', '[[BIRTH_ID_13]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_9]]: kanonické příjmení 'Štik' se nevyskytuje v originálu, ale varianta 'Martin Štika' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [E-WRONG-TYPE] [[PERSON_16]] = 'Poboček Praha' vypadá jako město / pobočka, ne osoba.
- [D-PARTIAL-NAME] [[PERSON_18]] = 'Malá' vypadá jako neúplné jméno (pouze jedno slovo).
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_24]]: kanonické příjmení 'Havl' se nevyskytuje v originálu, ale varianta 'Petrem Havlem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [C-ROLE-AS-PERSON] [[PERSON_28]] = 'Support Program' obsahuje ne-osobu / roli ('Support Program').
- [C-ROLE-AS-PERSON] [[PERSON_28]] = 'Support Program' – první slovo 'Support' je role/pozice, ne křestní jméno.
- [C-ROLE-AS-PERSON] [[PERSON_29]] = 'Career Support' obsahuje ne-osobu / roli ('Career Support').
- [C-ROLE-AS-PERSON] [[PERSON_29]] = 'Career Support' – první slovo 'Career' je role/pozice, ne křestní jméno.
- [C-ROLE-AS-PERSON] [[PERSON_40]] = 'Sokol Invest' obsahuje 'Invest', pravděpodobně firma/role, ne osoba.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_41]]: kanonické příjmení 'Nový' se nevyskytuje v originálu, ale varianta 'Nové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [blacklist_as_person] [[PERSON_43]] = 'Prosím David' obsahuje zdvořilostní obrat / prefix ('Prosím'), který nemá být součástí osoby.
- [C-ROLE-AS-PERSON] [[PERSON_45]] = 'Customer Success' obsahuje ne-osobu / roli ('Customer Success').
- [C-ROLE-AS-PERSON] [[PERSON_45]] = 'Customer Success' – první slovo 'Customer' je role/pozice, ne křestní jméno.

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_6]] = 'na adrese Komenského 58, Brno' obsahuje prefix 'na adrese', který podle QA pravidel do adresy nepatří.

---

### smlouva13.docx — 8/10

**PII nalezené regexem:**
- `123456/2024` (Rodné číslo (RC))

---

### smlouva14.docx — 0/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `hcp_admin`
- `Manager`
- `Risk Manager`
- `Services`
- `Brno`
- `Architect`

**PII nalezené regexem:**
- `125 000 000` (Telefon 9 číslic)

**Mapa – konzistence JSON/TXT:**
- Duplicitní entita '456789012...' má různé tagy

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_19]]: kanonické příjmení 'Františka' se nevyskytuje v originálu, ale varianta 'Na Františku' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [C-ROLE-AS-PERSON] [[PERSON_21]] = 'Risk Manager' – první slovo 'Risk' je role/pozice, ne křestní jméno.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_26]]: kanonické příjmení 'Bulovec' se nevyskytuje v originálu, ale varianta 'Na Bulovce' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva15.docx — 0/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `hcp_admin`
- `Manager`
- `Risk Manager`
- `Services`
- `Brno`
- `Architect`

**PII nalezené regexem:**
- `125 000 000` (Telefon 9 číslic)

**Mapa – konzistence JSON/TXT:**
- Duplicitní entita '456789012...' má různé tagy

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_19]]: kanonické příjmení 'Františka' se nevyskytuje v originálu, ale varianta 'Na Františku' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [C-ROLE-AS-PERSON] [[PERSON_21]] = 'Risk Manager' – první slovo 'Risk' je role/pozice, ne křestní jméno.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_26]]: kanonické příjmení 'Bulovec' se nevyskytuje v originálu, ale varianta 'Na Bulovce' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva16.docx — 2/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Praha`
- `Manager`

**PII nalezené regexem:**
- `150 000 000` (Telefon 9 číslic)

**Mapa – chyby osob (PERSON):**
- [C-ROLE-AS-PERSON] [[PERSON_23]] = 'Account Manager' – první slovo 'Account' je role/pozice, ne křestní jméno.

---

### smlouva17.docx — 5/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `8508121234`
- `123456`
- `Brno`

---

### smlouva18.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_6]]: kanonické příjmení 'Kratochvílová' se nevyskytuje v originálu, ale varianta 'Lenkou Kratochvílovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_7]]: kanonické příjmení 'Novotná' se nevyskytuje v originálu, ale varianta 'Šárkou Novotnou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_8]]: kanonické příjmení 'Strmisková' se nevyskytuje v originálu, ale varianta 'Alžbětou Strmiskovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_12]]: kanonické příjmení 'Štefánek' se nevyskytuje v originálu, ale varianta 'Tomášem Štefánkem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_14]]: kanonické příjmení 'Vráný' se nevyskytuje v originálu, ale varianta 'Tobiášem Vránou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_15]]: kanonické příjmení 'Prášek' se nevyskytuje v originálu, ale varianta 'Markem Práškem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva19.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_3]]: kanonické příjmení 'Novotná' se nevyskytuje v originálu, ale varianta 'Lucie Novotné' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_4]]: kanonické příjmení 'Hrbáčová' se nevyskytuje v originálu, ale varianta 'Gabrielou Hrbáčovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_5]]: kanonické příjmení 'Pavlík' se nevyskytuje v originálu, ale varianta 'Pavlíkem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_6]]: kanonické příjmení 'Šimůnek' se nevyskytuje v originálu, ale varianta 'Filipem Šimůnkem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_7]]: kanonické příjmení 'Zbořilová' se nevyskytuje v originálu, ale varianta 'Hany Zbořilové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_8]]: kanonické příjmení 'Melichová' se nevyskytuje v originálu, ale varianta 'Kláry Melichové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_9]]: kanonické příjmení 'Růžičková' se nevyskytuje v originálu, ale varianta 'Michaelou Růžičkovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_10]]: kanonické příjmení 'Konečná' se nevyskytuje v originálu, ale varianta 'Zorou Konečnou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_28]]: kanonické příjmení 'Plíšková' se nevyskytuje v originálu, ale varianta 'Pavlínou Plíškovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva2.docx — 4/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Převzetí Bytu`
- `Stav`

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[BANK_1]]', '[[BIRTH_ID_1]]', '[[DATE_8]]', '[[DATE_7]]', '[[ADDRESS_2]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_3]]: kanonické příjmení 'Přepisová' se nevyskytuje v originálu, ale varianta 'Elektřina Přepis' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_5]]: kanonické příjmení 'Byta' se nevyskytuje v originálu, ale varianta 'Převzetí Bytu' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_6]]: kanonické příjmení 'Výš' se nevyskytuje v originálu, ale varianta 'Porušení Výše' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_7]]: kanonické příjmení 'Byta' se nevyskytuje v originálu, ale varianta 'Nepředání Bytu' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva20.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_8]]: kanonické příjmení 'Šemberová' se nevyskytuje v originálu, ale varianta 'Davida Šembery' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_37]]: kanonické příjmení 'Vaňk' se nevyskytuje v originálu, ale varianta 'Miroslavem Vaňkem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_47]]: kanonické příjmení 'Kratochvíl' se nevyskytuje v originálu, ale varianta 'Adrianem Kratochvílem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_1]] = 'se sídlem V Kapslovně 881/11, Praha 3' obsahuje prefix 'se sídlem', který podle QA pravidel do adresy nepatří.

---

### smlouva21.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_33]]: kanonické příjmení 'Šemberá' se nevyskytuje v originálu, ale varianta 'Davidem Šemberou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_34]]: kanonické příjmení 'Šemberá' se nevyskytuje v originálu, ale varianta 'Davida Šembery' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_41]]: kanonické příjmení 'Havl' se nevyskytuje v originálu, ale varianta 'Viktor Havel' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_42]]: kanonické příjmení 'Hofmanová' se nevyskytuje v originálu, ale varianta 'Radku Hofmanovi' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_51]]: kanonické příjmení 'Vaňek' se nevyskytuje v originálu, ale varianta 'Miroslav Vaněk' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_59]]: kanonické příjmení 'Dvořáek' se nevyskytuje v originálu, ale varianta 'Martin Dvořák' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva22.docx — 8/10

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[PERSON_117]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_64]]: kanonické příjmení 'Šemberá' se nevyskytuje v originálu, ale varianta 'Davidem Šemberou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_65]]: kanonické příjmení 'Šemberá' se nevyskytuje v originálu, ale varianta 'Davida Šembery' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_72]]: kanonické příjmení 'Havl' se nevyskytuje v originálu, ale varianta 'Viktor Havel' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_73]]: kanonické příjmení 'Hofmanová' se nevyskytuje v originálu, ale varianta 'Radku Hofmanovi' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_82]]: kanonické příjmení 'Vaňek' se nevyskytuje v originálu, ale varianta 'Miroslav Vaněk' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_90]]: kanonické příjmení 'Dvořáek' se nevyskytuje v originálu, ale varianta 'Martin Dvořák' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_99]]: kanonické příjmení 'Vojt' se nevyskytuje v originálu, ale varianta 'Kryštof Vojta' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_108]]: kanonické příjmení 'Lukášová' se nevyskytuje v originálu, ale varianta 'Samuelu Lukášovi' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_112]]: kanonické příjmení 'Šteinerová' se nevyskytuje v originálu, ale varianta 'Danielu Šteinerovi' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_115]]: kanonické příjmení 'Vlná' se nevyskytuje v originálu, ale varianta 'Otakar Vlna' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_120]]: kanonické příjmení 'Popelká' se nevyskytuje v originálu, ale varianta 'Ivanem Popelkou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva23.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_57]]: kanonické příjmení 'Holubc' se nevyskytuje v originálu, ale varianta 'Otta Holubce' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_59]]: kanonické příjmení 'Pazder' se nevyskytuje v originálu, ale varianta 'Radim Pazdera' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_60]]: kanonické příjmení 'Šimůnk' se nevyskytuje v originálu, ale varianta 'Lubomír Šimůnek' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_64]]: kanonické příjmení 'Blažeková' se nevyskytuje v originálu, ale varianta 'Čeňka Blažka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_71]]: kanonické příjmení 'Vachoušk' se nevyskytuje v originálu, ale varianta 'Adam Vachoušek' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_72]]: kanonické příjmení 'Říp' se nevyskytuje v originálu, ale varianta 'Tomáš Řípa' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_73]]: kanonické příjmení 'Šebk' se nevyskytuje v originálu, ale varianta 'Vladimír Šebek' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_82]]: kanonické příjmení 'Malin' se nevyskytuje v originálu, ale varianta 'Jindřich Malina' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_85]]: kanonické příjmení 'Bláh' se nevyskytuje v originálu, ale varianta 'Josef Bláha' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_87]]: kanonické příjmení 'Čapk' se nevyskytuje v originálu, ale varianta 'Bogdan Čapek' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_89]]: kanonické příjmení 'Jančíková' se nevyskytuje v originálu, ale varianta 'Radka Jančíka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_92]]: kanonické příjmení 'Šenek' se nevyskytuje v originálu, ale varianta 'Dalimil Šenk' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_93]]: kanonické příjmení 'Zástěr' se nevyskytuje v originálu, ale varianta 'Marek Zástěra' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_101]]: kanonické příjmení 'Ženíšk' se nevyskytuje v originálu, ale varianta 'Marek Ženíšek' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_105]]: kanonické příjmení 'Slavíčk' se nevyskytuje v originálu, ale varianta 'Boris Slavíček' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_107]]: kanonické příjmení 'Křivánk' se nevyskytuje v originálu, ale varianta 'Lukáš Křivánek' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_108]]: kanonické příjmení 'Černot' se nevyskytuje v originálu, ale varianta 'Patrik Černota' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva24.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_24]]: kanonické příjmení 'Šustrová' se nevyskytuje v originálu, ale varianta 'Alice Šustrů' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_54]]: kanonické příjmení 'Zík' se nevyskytuje v originálu, ale varianta 'Pavel Zíka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_62]]: kanonické příjmení 'Kuba' se nevyskytuje v originálu, ale varianta 'Leoš Kubů' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_63]]: kanonické příjmení 'Havránk' se nevyskytuje v originálu, ale varianta 'Aleš Havránek' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_66]]: kanonické příjmení 'Brázd' se nevyskytuje v originálu, ale varianta 'Lukáš Brázda' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_68]]: kanonické příjmení 'Krejz' se nevyskytuje v originálu, ale varianta 'Štěpán Krejza' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_70]]: kanonické příjmení 'Hrabět' se nevyskytuje v originálu, ale varianta 'Rostislava Hraběte' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_71]]: kanonické příjmení 'Rendlo' se nevyskytuje v originálu, ale varianta 'Přemysla Rendla' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_75]]: kanonické příjmení 'Lojd' se nevyskytuje v originálu, ale varianta 'Stanislav Lojda' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_76]]: kanonické příjmení 'Švestk' se nevyskytuje v originálu, ale varianta 'Ctibor Švestka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_82]]: kanonické příjmení 'Hrdin' se nevyskytuje v originálu, ale varianta 'Bruna Hrdiny' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_83]]: kanonické příjmení 'Jiroušk' se nevyskytuje v originálu, ale varianta 'Marca Jirouška' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_85]]: kanonické příjmení 'Kucht' se nevyskytuje v originálu, ale varianta 'Kuchta' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_86]]: kanonické příjmení 'Kuchtová' se nevyskytuje v originálu, ale varianta 'Maxe Kuchty' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_88]]: kanonické příjmení 'Kolísk' se nevyskytuje v originálu, ale varianta 'Alexovi Kolískovi' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_89]]: kanonické příjmení 'Kolíseková' se nevyskytuje v originálu, ale varianta 'Alexe Kolíska' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_90]]: kanonické příjmení 'Vavr' se nevyskytuje v originálu, ale varianta 'Nicolas Vavra' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_91]]: kanonické příjmení 'Vavrová' se nevyskytuje v originálu, ale varianta 'Nicolase Vavry' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_98]]: kanonické příjmení 'Jirs' se nevyskytuje v originálu, ale varianta 'Albert Jirsa' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_100]]: kanonické příjmení 'Chrástk' se nevyskytuje v originálu, ale varianta 'Mihail Chrástek' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_101]]: kanonické příjmení 'Havličk' se nevyskytuje v originálu, ale varianta 'Sergej Havlička' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_103]]: kanonické příjmení 'Rychter' se nevyskytuje v originálu, ale varianta 'Oleg Rychtera' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva25.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_2]]: kanonické příjmení 'Pešková' se nevyskytuje v originálu, ale varianta 'Lenkou Peškovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_3]]: kanonické příjmení 'Bureš' se nevyskytuje v originálu, ale varianta 'Michala Bureše' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_11]]: kanonické příjmení 'Jur' se nevyskytuje v originálu, ale varianta 'Pavla Jury' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_12]]: kanonické příjmení 'Holubcová' se nevyskytuje v originálu, ale varianta 'Martiny Holubcové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_13]]: kanonické příjmení 'Šimůnek' se nevyskytuje v originálu, ale varianta 'Romana Šimůnka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_16]]: kanonické příjmení 'Horská' se nevyskytuje v originálu, ale varianta 'Radku Horskou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva26.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_3]]: kanonické příjmení 'Kyselová' se nevyskytuje v originálu, ale varianta 'Martiny Kyselové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_11]]: kanonické příjmení 'Vrba' se nevyskytuje v originálu, ale varianta 'Adama Vrby' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_13]]: kanonické příjmení 'Pecek' se nevyskytuje v originálu, ale varianta 'Lukáš Pecka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_20]]: kanonické příjmení 'Chýl' se nevyskytuje v originálu, ale varianta 'Radovan Chýle' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva27.docx — 8/10

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[BIRTH_ID_43]]', '[[BIRTH_ID_45]]', '[[BIRTH_ID_46]]', '[[BIRTH_ID_47]]', '[[BIRTH_ID_48]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_4]]: kanonické příjmení 'Dvořák' se nevyskytuje v originálu, ale varianta 'Dvořákovi' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_8]]: kanonické příjmení 'Procházka' se nevyskytuje v originálu, ale varianta 'Martina Procházku' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_12]]: kanonické příjmení 'Pokorná' se nevyskytuje v originálu, ale varianta 'Elišky Pokorné' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_13]]: kanonické příjmení 'Pokorný' se nevyskytuje v originálu, ale varianta 'Adama Pokorného' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_14]]: kanonické příjmení 'Pokorný' se nevyskytuje v originálu, ale varianta 'Pavlu Pokornému' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_15]]: kanonické příjmení 'Pokorná' se nevyskytuje v originálu, ale varianta 'Lucie Pokorné' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_18]]: kanonické příjmení 'Novotná' se nevyskytuje v originálu, ale varianta 'Hanou Novotnou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_22]]: kanonické příjmení 'Holubová' se nevyskytuje v originálu, ale varianta 'Dany Holubové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_33]]: kanonické příjmení 'Horák' se nevyskytuje v originálu, ale varianta 'Jana Horáka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_5]] = 'trvale bytem Krátká 5, Liberec 460 01' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.

---

### smlouva28.docx — 8/10

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[BIRTH_ID_63]]', '[[ADDRESS_18]]', '[[BIRTH_ID_57]]', '[[BIRTH_ID_62]]', '[[BIRTH_ID_64]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_20]]: kanonické příjmení 'Kubík' se nevyskytuje v originálu, ale varianta 'Matěje Kubíka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_21]]: kanonické příjmení 'Kubík' se nevyskytuje v originálu, ale varianta 'Miroslavem Kubíkem' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_24]]: kanonické příjmení 'Sedlák' se nevyskytuje v originálu, ale varianta 'Bohumila Sedláka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_31]]: kanonické příjmení 'Pokorná' se nevyskytuje v originálu, ale varianta 'Dany Pokorné' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_36]]: kanonické příjmení 'Součková' se nevyskytuje v originálu, ale varianta 'Kláru Součkovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_59]]: kanonické příjmení 'Málek' se nevyskytuje v originálu, ale varianta 'Ondřeje Málka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva29.docx — 8/10

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[BIRTH_ID_63]]', '[[PERSON_66]]', '[[BIRTH_ID_57]]', '[[BIRTH_ID_62]]', '[[BIRTH_ID_64]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_18]]: kanonické příjmení 'Tesařová' se nevyskytuje v originálu, ale varianta 'Emílie Tesařové' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_5]] = 'bytemRevoluční 67/9, Děčín 405 02' obsahuje prefix 'bytem', který podle QA pravidel do adresy nepatří.

---

### smlouva31.docx — 6/10

**PII nalezené regexem:**
- `347 000 000` (Telefon 9 číslic)

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[BIRTH_ID_35]]', '[[BIRTH_ID_34]]', '[[BIRTH_ID_36]]', '[[BIRTH_ID_37]]', '[[BIRTH_ID_31]]']

---

### smlouva32.docx — 8/10

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[BIRTH_ID_43]]', '[[BIRTH_ID_41]]', '[[BIRTH_ID_38]]', '[[BIRTH_ID_39]]', '[[BIRTH_ID_37]]']

---

### smlouva33.docx — 6/10

**PII nalezené regexem:**
- `124 000 000` (Telefon 9 číslic)

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[BIRTH_ID_40]]', '[[BIRTH_ID_41]]', '[[BIRTH_ID_39]]']

---

### smlouva4.docx — 5/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Klára Malá`

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_1]] = 'trvale bytem Na Hrázi 21, 612 00 Brno' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_2]] = 'trvale bytem K Lesu 14, 370 01 České Budějovice' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_3]] = 'trvale bytem U Studánky 58, 500 03 Hradec Králové' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_4]] = 'trvale bytem Horní cesta 17, 674 01 Třebíč' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_5]] = 'trvale bytem Pod Skalkou 3, 101 00 Praha' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_6]] = 'trvale bytem Družstevní 66, 787 01 Šumperk' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.

---

### smlouva5.docx — 8/10

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_1]] = 'trvale bytem Na Výsluní 8, 779 00 Olomouc' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_2]] = 'trvale bytem V Koutech 123, 110 00 Praha' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_3]] = 'trvale bytem U Trati 66, 602 00 Brno' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_4]] = 'trvale bytem Slunečná 45, 370 01 České Budějovice' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_5]] = 'trvale bytem Družstevní 17, 736 01 Havířov' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_6]] = 'trvale bytem Lipová 9, 460 01 Liberec' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_7]] = 'trvale bytem Komenského 5, 400 01 Ústí nad Labem' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_8]] = 'trvale bytem Na Lani 77, 290 01 Poděbrady' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_9]] = 'trvale bytem Horská 3, 500 03 Hradec Králové' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.
- [D-PREFIX] [[ADDRESS_10]] = 'trvale bytem Lesní 10, 787 01 Šumperk' obsahuje prefix 'trvale bytem', který podle QA pravidel do adresy nepatří.

---

### smlouva6.docx — 8/10

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_5]] = 'na adrese: Tylova 58, 779 00 Olomouc' obsahuje prefix 'na adrese', který podle QA pravidel do adresy nepatří.

---

### smlouva7.docx — 5/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Bc.`

**Mapa – chyby osob (PERSON):**
- [D-PARTIAL-NAME] [[PERSON_18]] = 'Nová' vypadá jako neúplné jméno (pouze jedno slovo).

**Mapa – chyby adres (ADDRESS):**
- [D-PREFIX] [[ADDRESS_17]] = 'na adrese: Palackého 10, 500 02 Hradec Králové' obsahuje prefix 'na adrese', který podle QA pravidel do adresy nepatří.

---

### smlouva8.docx — 8/10

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_1]]: kanonické příjmení 'Černý' se nevyskytuje v originálu, ale varianta 'Tomášem Černým' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_4]]: kanonické příjmení 'Popesca' se nevyskytuje v originálu, ale varianta 'Alexandru Popescu' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-PARTIAL-NAME] [[PERSON_11]] = 'Hrubá' vypadá jako neúplné jméno (pouze jedno slovo).
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_16]]: kanonické příjmení 'Vrabcová' se nevyskytuje v originálu, ale varianta 'Klárou Vrabcovou' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_20]]: kanonické příjmení 'Havelek' se nevyskytuje v originálu, ale varianta 'Petr Havelka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

### smlouva9.docx — 5/10

**PII leak (hodnoty z mapy nalezené v anonymu):**
- `Banka`

**Mapa – konzistence JSON/TXT:**
- V TXT jsou labely, které chybí v JSON: ['[[PERSON_24]]', '[[PERSON_4]]']

**Mapa – chyby osob (PERSON):**
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_4]]: kanonické příjmení 'Vypracovalová' se nevyskytuje v originálu, ale varianta 'Compliance Vypracoval' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.
- [D-CANONICAL-NOT-IN-SOURCE] [[PERSON_5]]: kanonické příjmení 'Banek' se nevyskytuje v originálu, ale varianta 'Banka' ano – pravděpodobně špatný nominativ nebo překlep v kanonické formě.

---

## Selhané soubory

smlouva 30.docx, smlouva0.docx, smlouva10.docx, smlouva11.docx, smlouva12.docx, smlouva13.docx, smlouva14.docx, smlouva15.docx, smlouva16.docx, smlouva17.docx, smlouva18.docx, smlouva19.docx, smlouva2.docx, smlouva20.docx, smlouva21.docx, smlouva22.docx, smlouva23.docx, smlouva24.docx, smlouva25.docx, smlouva26.docx, smlouva27.docx, smlouva28.docx, smlouva29.docx, smlouva31.docx, smlouva32.docx, smlouva33.docx, smlouva4.docx, smlouva5.docx, smlouva6.docx, smlouva7.docx, smlouva8.docx, smlouva9.docx

---
*Detailní data v `test_results.json`*