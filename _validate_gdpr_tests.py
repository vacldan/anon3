import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from deep_validate import run_validation, print_report

base = Path('test_data')
results = []

for n in range(1, 51):
    src = base / f'smlouva_gdpr_test_{n:02d}.docx'
    if not src.exists():
        continue
    r = run_validation(str(src))
    if 'error' not in r:
        results.append((n, r))
        s = r['score']
        ec = len(r['errors_canonical'])
        ev = len(r.get('errors_canonical_variants', []))
        ur = len(r.get('uncovered_real', []))
        lk = len(r['leaks'])
        ph = len(r['phantoms'])
        status = 'OK' if s >= 9 else 'FAIL'
        if s < 10:
            print(f"gdpr_test_{n:02d}: {s}/10 [{status}] canon={ec} var={ev} uncov={ur} leaks={lk} phantom={ph}")
            print_report(r)
    else:
        print(f"gdpr_test_{n:02d}: ERROR - {r.get('error','?')}")

print('\n' + '=' * 70)
print('SOUHRN GDPR TEST 01-50')
print('=' * 70)
print(f"{'Smlouva':<20} {'Skóre':<10} {'Kanon':<6} {'Var':<5} {'Nepokr':<6} {'Úniky':<6} {'Phantom':<7} {'Status'}")
print('-' * 70)
for n, r in results:
    ec = len(r['errors_canonical'])
    ev = len(r.get('errors_canonical_variants', []))
    ur = len(r.get('uncovered_real', []))
    lk = len(r['leaks'])
    ph = len(r['phantoms'])
    s = r['score']
    status = 'OK' if s >= 9 else 'FAIL'
    print(f"gdpr_test_{n:02d}      {s}/{r['max_score']:<6} {ec:<6} {ev:<5} {ur:<6} {lk:<6} {ph:<7} {status}")

avg = sum(r['score'] for _, r in results) / len(results) if results else 0
print('-' * 70)
print(f"Průměr: {avg:.1f}/10")
failed = [n for n, r in results if r['score'] < 9]
if failed:
    print(f"FAILED: {failed}")
    sys.exit(1)
else:
    print("VŠECHNY TESTY PROŠLY!")
