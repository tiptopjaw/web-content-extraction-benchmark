#!/bin/bash
# Run LLM-based extractors sequentially overnight
# MinerU-HTML (CPU, ~4h) then ReaderLM-v2 (GPU via Ollama, ~2.7h)
set -e

cd "$(dirname "$0")"

echo "=== Starting LLM benchmark runs at $(date) ==="

echo ""
echo "=== [1/2] MinerU-HTML (CPU, ~4 hours) ==="
python3 scripts/03_run_benchmark.py --extractor mineru-html 2>&1 | tee mineru_benchmark.log
echo "=== MinerU-HTML completed at $(date) ==="

echo ""
echo "=== [2/2] ReaderLM-v2 (Ollama GPU, ~2.7 hours) ==="
python3 scripts/03_run_benchmark.py --extractor readerlm-v2 2>&1 | tee readerlm_benchmark.log
echo "=== ReaderLM-v2 completed at $(date) ==="

echo ""
echo "=== All LLM benchmarks completed at $(date) ==="
