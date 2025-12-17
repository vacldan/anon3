#!/usr/bin/env python3
"""Test inference for Pavel Zíka variations."""

# Import inference functions from anon script
import sys
sys.path.insert(0, '/home/user/anon3')

# Read the anon script and extract functions
with open('anon7.2 - s padama.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Execute to get the functions
exec(code, globals())

# Test cases
test_cases = [
    ("Pavel", "Zíka"),
    ("Pavla", "Zíky"),
    ("Pavlovi", "Zíkovi"),
    ("Radim", "Šídlo"),
    ("Radima", "Šídla"),
    ("Radimovi", "Šídlovi"),
    ("Leoš", "Kubů"),
    ("Leoše", "Kubů"),
    ("Leošovi", "Kubů"),
]

print("Testing inference:\n")
for first_obs, last_obs in test_cases:
    # This mimics the logic in the anonymizer
    last_nom = infer_surname_nominative(last_obs)

    # Check if it's potentially male genitive
    first_lo = first_obs.lower()
    last_nom_lo = last_nom.lower()

    is_female_surname = last_nom_lo.endswith(('ová', 'á'))

    if is_female_surname:
        first_nom = infer_first_name_nominative(first_obs) if first_obs else first_obs
    else:
        # Male surname logic
        if first_lo.endswith('a') and len(first_lo) > 2:
            candidate_male = first_obs[:-1]
            candidate_male_lo = candidate_male.lower()

            male_genitiv_a = {
                'josef', 'emil', 'odon', 'štěpán', 'maxim', 'adam',
                'matěj', 'jakub', 'lukáš', 'jan', 'petr', 'pavel',
                'marek', 'oldřich', 'bedřich', 'stanislav', 'radoslav', 'václav',
                'leon', 'albert', 'erik', 'teodor', 'viktor', 'igor', 'artur',
                'oleksandr', 'sergej', 'oleg', 'mihail', 'denis', 'ivan',
                'lubomír', 'přemysl', 'tadeáš', 'rostislav', 'ctibor',
                'karel', 'michal', 'tomáš', 'aleš', 'miloš', 'leoš', 'radim'
            }

            male_genitive_forms = {
                'marka': 'marek',
                'karla': 'karel',
                'michala': 'michal',
                'vita': 'vito',
                'bruna': 'bruno',
                'lea': 'leo',
                'radima': 'radim',
                'leoše': 'leoš',
            }

            if first_lo in male_genitive_forms:
                first_nom = male_genitive_forms[first_lo].capitalize()
            elif candidate_male_lo in male_genitiv_a:
                if not candidate_male_lo.endswith(('a', 'e', 'ie', 'ia', 'y')):
                    first_nom = candidate_male
                else:
                    first_nom = infer_first_name_nominative(first_obs)
            else:
                first_nom = infer_first_name_nominative(first_obs)
        else:
            first_nom = infer_first_name_nominative(first_obs)

    print(f"{first_obs:15} {last_obs:15} → {first_nom:15} {last_nom:15}")
