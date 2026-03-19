# Audit anonymizace – shrnutí správně / špatně

## 1. SKUTEČNÉ LEAKY (9 smluv)

### BIRTH_PLACE (Brno, Praha)
- **Problém:** Anonymizátor nahrazuje jen výskyt v kontextu „Místo narození: X“.
- **Zůstává v textu:** Další výskyty stejného města – např. „DataCloud Brno“, „ÚMČ Brno-střed“, „VŠE Praha“, „Místo uzavření: Praha“.
- **Důvod:** Chybí post-pass, který by nahradil všechny výskyty hodnoty z mapy (podobně jako u ADDRESS).
- **Doporučení:** Přidat do `anon72.py` post-pass: pro každé `BIRTH_PLACE` z mapy nahradit všechny výskyty originálu tagem.

### USERNAME (hcp_admin)
- **Problém:** `USERNAME_RE` vyžaduje prefix (Login:, Username:, User:).
- **Zůstává v textu:** Výskyt v seznamu – např. „admin, root, administrator, hcp_admin“.
- **Doporučení:** Post-pass: pro každé USERNAME z mapy nahradit všechny výskyty originálu tagem.

### PERSON „Nové“
- **Problém:** False positive – „Nové“ z „Nové Město“ (místo) bylo označeno jako osoba.
- **Doporučení:** Rozšířit blacklist míst (nové město, staré město) nebo upravit NER, aby tato slova neoznačoval jako PERSON.

---

## 2. PII REGEX – FALSE POSITIVE (opraveno v auditu)

| Původní hit | Skutečnost | Oprava v `full_leak_audit.py` |
|-------------|------------|-------------------------------|
| 123456/2024 v „FÚ-123456/2024/Kon“ | Číslo jednací, ne RČ | `(?<!FÚ-)(?<!KS-)(?<!VS-)(?<!čj-)` |
| 125 000 000, 150 000 000 Kč | Částka v Kč, ne telefon | negative lookahead pro Kč/EUR/USD |

**Výsledek:** Po úpravě regexů v auditu: **0 smluv** s PII regex hitem (předtím 7). Všechny byly false positive.

---

## 3. POTENCIÁLNÍ MISKLASIFIKACE (5 případů)

Čísla označená jako PHONE, která začínají na 1 (neplatné CZ předvolby):

| Smlouva | Hodnota | Poznámka |
|---------|---------|----------|
| smlouva13 | 123789456 | Možná testovací číslo |
| smlouva27 | 111222333 | Možná testovací číslo |
| smlouva_gdpr_test_42 | 123456789 | Testovací data |
| smlouva_gdpr_test_57 | 191976141 | 191 = tísňová linka? |
| smlouva_gdpr_test_96 | 100615591 | Zkontrolovat kontext |

**Doporučení:** Projít tyto smlouvy a ověřit, zda jde o telefon, nebo o jiný typ údaje (číslo účtu, ID, testovací hodnota).

---

## 4. SPRÁVNĚ ANONYMIZOVÁNO

- **IBAN:** 224 výskytů – formát CZ + 20 číslic, správně detekováno.
- **BANK:** 488 výskytů – formát číslo/kód banky, vyloučeno FÚ-, KS-, VS-.
- **BIRTH_ID:** 1583 výskytů – vyloučeno číslo jednací (FÚ-, KS-, VS-).
- **PHONE:** 1174 výskytů – vyloučeny částky (Kč, EUR, USD).
- **Částky vs. telefon:** Anonymizátor správně neoznačuje částky jako telefony.

---

## 5. MIMO GDPR (technické entity)

Anonymizuje se i: IP, MAC, PASSWORD, USERNAME, API_KEY, SSH_KEY, sociální sítě (LINKEDIN, FACEBOOK), biometrie (BIO_HASH, VOICE_ID). To je nad rámec běžného GDPR, ale zvyšuje to bezpečnost.

---

## 5b. Technické smlouvy – nechat jen GDPR, nebo i hesla/klíče?

**Doporučení: nechat kód tak, jak je – anonymizovat i technické entity (passwords, API keys, SSH, IP, USERNAME v tech kontextu).**

| Přístup | Výhody | Nevýhody |
|--------|--------|----------|
| **Jen GDPR** (jména, RČ, telefony, účty, adresy…) | Čistě právní scope, méně „mimo“ entit | V technických smlouvách zůstanou v textu hesla, API klíče, přihlašovací jména → **bezpečnostní riziko** při sdílení |
| **GDPR + technické** (současný stav) | Jedna verze „safe to share“ – bez PII i bez credentials. U IT/hosting/API smluv je únik hesla nebo klíče reálný incident. | Širší scope; u čistě právních smluv to jen nic nezkazí |

**Proč to dává smysl nechat:**

1. **Technické smlouvy** – SLA, hosting, API, bezpečnostní dokumenty často obsahují příklady přihlášení (Login: x / Password: y), API klíče, IP adresy. Kdyby se anonymizovalo jen GDPR, tyto údaje by v anonymizovaném dokumentu zůstaly a sdílení (audit, partner, právník) by bylo rizikové.
2. **Jedna politika** – „anonymizovaná verze = bez osobních údajů a bez přístupových údajů“ je jednoduché pravidlo pro všechny typy smluv.
3. **GDPR není minimum pro bezpečnost** – únik API klíče nebo hesla není přímo „porušení GDPR“, ale je to bezpečnostní událost. Anonymizátor tím řeší i tohle.

**Kdy zvážit režim „jen GDPR“:**  
Např. pokud by klient chtěl anonymizovat pouze pro účely ochrany osobních údajů a technické detaily (IP, hostname) v dokumentu nevadí. Tehdy by šlo přidat volbu `--gdpr-only`, která by přeskočila bloky pro PASSWORD, API_KEY, SSH_KEY, volitelně IP/MAC/USERNAME. Výchozí by měl zůstat režim **GDPR + technické**.

---

## 6. DOPORUČENÉ ÚPRAVY V anon72.py

1. **BIRTH_PLACE post-pass:** Po detekci „Místo narození: Brno“ nahradit všechny výskyty „Brno“ v dokumentu tagem `[[BIRTH_PLACE_1]]` (s výjimkou již tagovaných kontextů).
2. **USERNAME post-pass:** Po detekci username s prefixem nahradit všechny výskyty daného username v dokumentu odpovídajícím tagem.
3. **PERSON „Nové“:** Přidat „nové město“, „staré město“ do blacklistu míst nebo do výjimek pro PERSON.

---

*Report vygenerován skriptem `test_data/full_leak_audit.py`*
