#!/bin/bash
# Benchmark comparison: rs-trafilatura vs go-trafilatura
# Usage: ./benchmark-comparison.sh [num_files]

set -e

# Configuration
RS_EXTRACTOR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/rs-trafilatura/target/release/extract_stdin"
GO_EXTRACTOR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/go-trafilatura/go-trafilatura-cli"
HTML_DIR="/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/data/html_files"
NUM_FILES="${1:-100}"  # Default to 100 files

# Verify tools exist
if [[ ! -x "$RS_EXTRACTOR" ]]; then
    echo "Error: rs-trafilatura extractor not found at $RS_EXTRACTOR"
    exit 1
fi

if [[ ! -x "$GO_EXTRACTOR" ]]; then
    echo "Error: go-trafilatura extractor not found at $GO_EXTRACTOR"
    exit 1
fi

# Get list of HTML files
FILES=($(ls "$HTML_DIR"/*.html | head -n "$NUM_FILES"))
TOTAL_FILES=${#FILES[@]}

echo "========================================"
echo "Benchmark: rs-trafilatura vs go-trafilatura"
echo "========================================"
echo "Files to process: $TOTAL_FILES"
echo ""

# Calculate total size
TOTAL_SIZE=$(du -ch "${FILES[@]}" 2>/dev/null | tail -1 | cut -f1)
echo "Total data size: $TOTAL_SIZE"
echo ""

# Warm up (run once to load caches)
echo "Warming up..."
cat "${FILES[0]}" | "$RS_EXTRACTOR" > /dev/null 2>&1 || true
"$GO_EXTRACTOR" -f txt "${FILES[0]}" > /dev/null 2>&1 || true
echo ""

# Benchmark rs-trafilatura
echo "Running rs-trafilatura..."
RS_START=$(date +%s.%N)
for f in "${FILES[@]}"; do
    cat "$f" | "$RS_EXTRACTOR" > /dev/null 2>&1
done
RS_END=$(date +%s.%N)
RS_TIME=$(echo "$RS_END - $RS_START" | bc)

echo "  Time: ${RS_TIME}s"
echo ""

# Benchmark go-trafilatura
echo "Running go-trafilatura..."
GO_START=$(date +%s.%N)
for f in "${FILES[@]}"; do
    "$GO_EXTRACTOR" -f txt "$f" > /dev/null 2>&1
done
GO_END=$(date +%s.%N)
GO_TIME=$(echo "$GO_END - $GO_START" | bc)

echo "  Time: ${GO_TIME}s"
echo ""

# Calculate results
RS_PER_FILE=$(echo "scale=4; $RS_TIME / $TOTAL_FILES" | bc)
GO_PER_FILE=$(echo "scale=4; $GO_TIME / $TOTAL_FILES" | bc)
SPEEDUP=$(echo "scale=2; $GO_TIME / $RS_TIME" | bc)

echo "========================================"
echo "RESULTS"
echo "========================================"
echo ""
printf "%-20s %12s %12s\n" "Metric" "rs-trafilatura" "go-trafilatura"
printf "%-20s %12s %12s\n" "--------------------" "------------" "------------"
printf "%-20s %12.3fs %12.3fs\n" "Total time" "$RS_TIME" "$GO_TIME"
printf "%-20s %12.4fs %12.4fs\n" "Per file" "$RS_PER_FILE" "$GO_PER_FILE"
echo ""
echo "Speedup (Go/Rust): ${SPEEDUP}x"
echo ""

if (( $(echo "$SPEEDUP > 1" | bc -l) )); then
    echo "rs-trafilatura is ${SPEEDUP}x FASTER than go-trafilatura"
else
    SLOWDOWN=$(echo "scale=2; 1 / $SPEEDUP" | bc)
    echo "rs-trafilatura is ${SLOWDOWN}x SLOWER than go-trafilatura"
fi
