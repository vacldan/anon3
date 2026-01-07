#!/bin/bash
# Test batch processing speed

echo "Testing batch anonymization speed..."
time_start=$(date +%s)

for file in smlouva*.docx; do
    base=$(basename "$file" .docx)
    python3 anonymize_cli_turbo.py \
        --input "$file" \
        --output "${base}_anon.docx" \
        --map "${base}_map.json" \
        --map_txt "${base}_map.txt" > /dev/null 2>&1
    echo -n "."
done

time_end=$(date +%s)
elapsed=$((time_end - time_start))
echo ""
echo "Total time: ${elapsed} seconds"
