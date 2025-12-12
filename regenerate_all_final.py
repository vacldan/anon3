#!/usr/bin/env python3
import subprocess
import sys

contracts = list(range(13, 25))
results = []

print("=== Regenerating all contracts 13-24 with ALL fixes ===\n")

for num in contracts:
    filename = f"smlouva{num}.docx"
    print(f"Processing {filename}...", flush=True)

    result = subprocess.run(
        ["python3", "anon7.2 - s padama.py", filename],
        capture_output=True,
        text=True
    )

    # Extract person count
    for line in result.stdout.split('\n'):
        if "Nalezeno osob:" in line:
            count = line.split(':')[1].strip().split()[0]
            results.append((num, count))
            print(f"  ✅ smlouva{num}: {count} osob\n", flush=True)
            break

print("\n=== FINAL RESULTS ===")
print("Contract | Persons")
print("---------|--------")
for num, count in results:
    print(f"smlouva{num:2d} | {count:>7} osob")

print(f"\nTotal contracts processed: {len(results)}/12")
