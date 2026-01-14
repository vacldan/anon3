#!/bin/bash
echo "=== Testing all contracts 13-24 ==="
echo ""

for i in 13 14 15 16 17 18 19 20 21 22 23 24; do
    echo "Processing smlouva$i..."
    python3 "anon7.2 - s padama.py" "smlouva${i}.docx" 2>&1 | grep "Nalezeno osob:"
done

echo ""
echo "=== Summary ==="
echo "smlouva13: $(grep -c "PERSON_" smlouva13_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva14: $(grep -c "PERSON_" smlouva14_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva15: $(grep -c "PERSON_" smlouva15_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva16: $(grep -c "PERSON_" smlouva16_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva17: $(grep -c "PERSON_" smlouva17_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva18: $(grep -c "PERSON_" smlouva18_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva19: $(grep -c "PERSON_" smlouva19_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva20: $(grep -c "PERSON_" smlouva20_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva21: $(grep -c "PERSON_" smlouva21_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva22: $(grep -c "PERSON_" smlouva22_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva23: $(grep -c "PERSON_" smlouva23_map.txt 2>/dev/null || echo '?') osob"
echo "smlouva24: $(grep -c "PERSON_" smlouva24_map.txt 2>/dev/null || echo '?') osob"
