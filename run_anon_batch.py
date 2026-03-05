import sys, os, datetime
sys.path.insert(0, '.')
import anon72
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
for n in range(10, 35):
    src = f'test_data/smlouva{n}.docx'
    if not os.path.exists(src):
        print(f'[SKIP] {n}')
        continue
    try:
        a = anon72.Anonymizer()
        a.anonymize_docx(src, f'test_data/smlouva{n}_anon_{ts}.docx', f'test_data/smlouva{n}_map_{ts}.json', f'test_data/smlouva{n}_map_{ts}.txt')
        print(f'[OK] {n}')
    except Exception as e:
        print(f'[ERR] {n}: {e}')
