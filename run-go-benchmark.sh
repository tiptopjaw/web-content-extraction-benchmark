#!/bin/bash
# Run go-trafilatura on ALL benchmark files
set -e

HTML_DIR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/data/html_files"
OUTPUT_DIR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/benchmark-results/go"
GO_EXTRACTOR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/go-trafilatura/go-trafilatura-cli"

mkdir -p "$OUTPUT_DIR"

echo "Starting go-trafilatura benchmark on ALL files..."
echo "Start time: $(date)"

START=$(date +%s.%N)

for f in "$HTML_DIR"/*.html; do
    BASENAME=$(basename "$f" .html)
    "$GO_EXTRACTOR" -f txt "$f" > "$OUTPUT_DIR/${BASENAME}.txt" 2>/dev/null || true
done

END=$(date +%s.%N)
ELAPSED=$(echo "$END - $START" | bc)

echo "End time: $(date)"
echo "Total time: ${ELAPSED}s"
echo "$ELAPSED" > "$OUTPUT_DIR/total_time.txt"

NUM_FILES=$(ls "$HTML_DIR"/*.html | wc -l)
echo "Files processed: $NUM_FILES"
echo "$NUM_FILES" > "$OUTPUT_DIR/num_files.txt"
