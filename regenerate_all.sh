#!/bin/bash
for i in 13 14 15 16 17 18 19 20 21 22 23 24; do
    echo "=== Regenerating smlouva$i ==="
    python3 "anon7.2 - s padama.py" "smlouva$i.docx" 2>&1 | grep "Nalezeno osob:"
done
