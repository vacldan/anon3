# Jak nahrát změny na GitHub

## Rychlý postup (PowerShell)

```powershell
cd c:\Nixminds\skryi-clean

# 1. Zkontroluj stav
git status

# 2. Přidej změny (všechny modifikované soubory)
git add anon72.py
git add SKRYI_TECHNICAL_DOCUMENTATION.md
git add "SKRYI_TECHNICAL_DOCUMENTATION (1).md"
git add TECHNICAL_DOCUMENTATION.md

# Nebo přidej vše najednou:
git add -u

# 3. Commit s popisem
git commit -m "v3.1: Opravy klasifikace - INSURANCE_ID vs PHONE, vokativní deduplikace, false PERSON/SPZ"

# 4. Push na GitHub
git push origin main
```

## Pokud používáte jinou větev (např. master)

```powershell
git push origin master
```

## Pokud je remote jinak pojmenovaný

```powershell
git remote -v
# Pokud je "origin" jiný, použijte jeho název místo origin
```

## Pokud je potřeba nejdřív stáhnout změny z GitHubu

```powershell
git pull origin main
# případně: git pull --rebase origin main
git push origin main
```

## Shrnutí změn v této verzi (v3.1)

- **anon72.py**: INSURANCE_ID vs PHONE misklasifikace, variabilní symbol (VS:), vokativní formy (-o), false PERSON (Hyundai Tucson, Brno Přechodný), false LICENSE_PLATE (NB2004)
- **Dokumentace**: 3 soubory aktualizovány na verzi 3.1.0
