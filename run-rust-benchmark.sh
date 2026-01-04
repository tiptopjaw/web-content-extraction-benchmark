#!/bin/bash
# Run rs-trafilatura on ALL benchmark files
set -e

HTML_DIR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/data/html_files"
OUTPUT_DIR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/benchmark-results/rust"
RS_EXTRACTOR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/rs-trafilatura/target/release/extract_stdin"

mkdir -p "$OUTPUT_DIR"

echo "Starting rs-trafilatura benchmark on ALL files..."
echo "Start time: $(date)"

START=$(date +%s.%N)

for f in "$HTML_DIR"/*.html; do
    BASENAME=$(basename "$f" .html)
    cat "$f" | "$RS_EXTRACTOR" > "$OUTPUT_DIR/${BASENAME}.txt" 2>/dev/null || true
done

END=$(date +%s.%N)
ELAPSED=$(echo "$END - $START" | bc)

echo "End time: $(date)"
echo "Total time: ${ELAPSED}s"
echo "$ELAPSED" > "$OUTPUT_DIR/total_time.txt"

NUM_FILES=$(ls "$HTML_DIR"/*.html | wc -l)
echo "Files processed: $NUM_FILES"
echo "$NUM_FILES" > "$OUTPUT_DIR/num_files.txt"
