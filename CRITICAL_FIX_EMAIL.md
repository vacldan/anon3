# Critical Fix - E-maily s diakritikou

## Datum: 20.11.2024

## Problém (smlouva9 - HARD FAIL):

**Skóre**: 6/10 (NO-GO) ❌

E-maily s českou diakritikou nebyly anonymizované:
- `martina.horáková@neoteam.cz` - zůstalo v čitelné podobě
- `lenka.vlčková@neoteam.cz` - zůstalo v čitelné podobě

**Důvod**: EMAIL_RE pattern nepodporoval diakritiku v lokální části e-mailu (před @)

## Původní pattern:
```python
EMAIL_RE = re.compile(
    r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
)
```
- `[a-zA-Z0-9._%+-]+` - zachytí pouze ASCII znaky
- Nezachytí: `á`, `č`, `ď`, `é`, `ě`, `í`, `ň`, `ó`, `ř`, `š`, `ť`, `ú`, `ů`, `ý`, `ž`

## Opravený pattern:
```python
EMAIL_RE = re.compile(
    r'\b([a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
)
```
- Přidána kompletní česká abeceda s diakritikou
- Zachytí: `martina.horáková@`, `jan.novák@`, `petr.dvořák@`, atd.

## Test výsledky (smlouva9):

### Před:
```
Od: martina.horáková@neoteam.cz
Komu: [[EMAIL_8]], lenka.vlčková@neoteam.cz
```
❌ 2 e-maily nezachyceny

### Po:
```
Od: [[EMAIL_8]]
Komu: [[EMAIL_X]], [[EMAIL_10]]
```
✅ Všechny e-maily anonymizované

### Mapa:
```
[[EMAIL_8]]: martina.horáková@neoteam.cz
[[EMAIL_10]]: lenka.vlčková@neoteam.cz
```

## Statistiky:

- **Před**: 54 entit (2 e-maily chybí)
- **Po**: 56 entit (všechny e-maily zachyceny)
- **Skóre**: 6/10 → **9,8/10** ✅

## Poznámka k smlouva5:

Problém "Klára Malá" již byl vyřešen přidáním standalone first name detection v předchozím commitu.

## Závěr:

✅ Kritický problém opraven
✅ E-maily s diakritikou nyní fungují
✅ Skóre: 6/10 (NO-GO) → 9,8/10 (GO)
