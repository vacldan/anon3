#!/bin/bash
echo "=== Regenerating all contracts 13-24 with ALL fixes ===" > regen_results.txt
echo "" >> regen_results.txt

for i in {13..24}; do
    echo "Processing smlouva$i..."
    python3 "anon7.2 - s padama.py" "smlouva${i}.docx" 2>&1 | grep -E "Nalezeno osob:|Chyba" | tee -a regen_results.txt
    echo "" >> regen_results.txt
done

echo "=== DONE ===" | tee -a regen_results.txt
echo "" | tee -a regen_results.txt
echo "Final results:" | tee -a regen_results.txt
grep "Nalezeno osob:" regen_results.txt | nl | tee -a regen_results.txt
