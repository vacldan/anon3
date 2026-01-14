#!/usr/bin/env python3
"""Regenerate all contracts 13-24 with surname inference fix"""
import subprocess
import sys

for num in range(13, 25):
    contract = f"smlouva{num}.docx"
    print(f"\n{'='*80}")
    print(f"Regenerating {contract}...")
    print('='*80)

    result = subprocess.run(
        ['python3', 'anon7.2 - s padama.py', contract],
        capture_output=False,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Error regenerating {contract}")
        sys.exit(1)

print("\n" + "="*80)
print("✅ All contracts regenerated successfully!")
print("="*80)
