import sys, os, datetime
sys.path.insert(0, '.')
import anon72

nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(10, 20))
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

for n in nums:
    src = f'test_data/smlouva{n}.docx'
    if not os.path.exists(src):
        print(f'[SKIP] {src} not found')
        continue
    out_docx = f'test_data/smlouva{n}_anon_{ts}.docx'
    out_json = f'test_data/smlouva{n}_map_{ts}.json'
    out_txt  = f'test_data/smlouva{n}_map_{ts}.txt'
    print(f'[RUN] smlouva{n} ...', end=' ', flush=True)
    try:
        a = anon72.Anonymizer()
        a.anonymize_docx(src, out_docx, out_json, out_txt)
        print('OK')
    except Exception as e:
        print(f'ERROR: {e}')
