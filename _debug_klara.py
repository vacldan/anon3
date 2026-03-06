import sys
import importlib
sys.stdout.reconfigure(encoding='utf-8')

# Force fresh import
if 'anon72' in sys.modules:
    del sys.modules['anon72']
import anon72
importlib.reload(anon72)

a = anon72.Anonymizer()

text = 'Klára Malá, [[DATE_1]], [[ADDRESS_1]]'
print(f"Input: {text!r}")
print(f"Calling _replace_remaining_people...")
result = a._replace_remaining_people(text)
print(f"Output: {result!r}")
print(f"Persons: {len(a.canonical_persons)}")
