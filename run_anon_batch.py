import sys, os, datetime
sys.path.insert(0, '.')
import anon72
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# All contracts: smlouva0-9, smlouva10-33, "smlouva 30"
contracts = []
for n in range(0, 35):
    contracts.append((f'test_data/smlouva{n}.docx', f'smlouva{n}'))
# Also handle "smlouva 30.docx" (with space)
contracts.append(('test_data/smlouva 30.docx', 'smlouva 30'))

for src, name in contracts:
    if not os.path.exists(src):
        print(f'[SKIP] {name}')
        continue
    try:
        a = anon72.Anonymizer()
        a.anonymize_docx(src, f'test_data/{name}_anon_{ts}.docx', f'test_data/{name}_map_{ts}.json', f'test_data/{name}_map_{ts}.txt')
        print(f'[OK] {name}')
    except Exception as e:
        print(f'[ERR] {name}: {e}')
