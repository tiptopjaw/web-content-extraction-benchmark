# Usage Guide

## Setup

1. **Install dependencies**:
```bash
cd modern-content-benchmark
pip install -r requirements.txt
```

2. **Verify structure**:
```bash
tree -L 2
```

## Step 1: Download HTML Files

Download all 2,836 web pages:

```bash
python scripts/01_download_pages.py
```

**Features**:
- Downloads 10 URLs concurrently
- Auto-resumes if interrupted
- Saves files as `0001.html`, `0002.html`, etc.
- Creates `metadata.csv` with URL mappings
- Shows progress and statistics

**Output**:
- `data/html_files/*.html` - Downloaded HTML files
- `data/metadata.csv` - Mapping of file IDs to URLs
- `data/download_progress.json` - Resume capability

## Step 2: Create Ground Truth Annotations

Use Deepseek API to generate annotations:

```bash
python scripts/02_create_annotations.py --api-key YOUR_DEEPSEEK_API_KEY
```

**Options**:
```bash
# Annotate specific range
python scripts/02_create_annotations.py --api-key KEY --start 1 --end 100

# Use different model
python scripts/02_create_annotations.py --api-key KEY --model deepseek-coder
```

**Features**:
- Sends HTML to Deepseek API
- Extracts title, author, date, main content
- Identifies "with" snippets (must extract)
- Identifies "without" snippets (must exclude)
- Saves as JSON files
- Concurrent API calls (5 at a time)
- Auto-skips already annotated files

**Output**:
- `data/ground_truth/0001.json` - Structured annotations
- Token usage statistics
- Success/failure report

**Cost Estimation**:
- Deepseek pricing: ~$0.14 per 1M input tokens, ~$0.28 per 1M output tokens
- Estimated: 2-5K tokens per page (input + output)
- Total for 2,836 pages: Approximately **$3-8 USD**

## Step 3: Run Benchmark

Test content extractors against ground truth annotations:

```bash
# Quick test on 10 files
python scripts/03_run_benchmark.py --limit 10

# Test specific extractor on subset
python scripts/03_run_benchmark.py --extractor trafilatura --limit 50

# Full benchmark on all annotations
python scripts/03_run_benchmark.py
```

**Available Extractors**:
- `trafilatura` - Advanced extraction optimized for recall
- `readability` - Mozilla's Readability algorithm (Python port)
- `boilerpy3-article` - Boilerpy3 with ArticleExtractor
- `boilerpy3-default` - Boilerpy3 with DefaultExtractor
- `beautifulsoup` - Custom BeautifulSoup-based extractor

**Options**:
```bash
--extractor NAME    # Test only specific extractor (default: all)
--limit N          # Test only first N files (for quick tests)
```

**Output**:
- `results/<extractor>_results.json` - Detailed results per extractor
- Metrics: Precision, Recall, F1 Score
- Snippet coverage: "With" and "Without" percentages
- Title match rate

## Step 4: Analyze Results

Generate comparison reports after running benchmarks:

```bash
python scripts/04_analyze_results.py
```

**Generates**:
- `results/comparison.csv` - Overall performance comparison table
- `results/best_worst_analysis.json` - Top/bottom performing files
- `results/length_analysis.json` - Performance by content length
- Console output with recommendations

**Example Output**:
```
Overall Performance Comparison
================================================================================
Extractor                   Precision  Recall  F1 Score  With Snippets  Without Snippets
Trafilatura                     0.759   0.864     0.793          0.730             0.055
Readability                     0.702   0.812     0.745          0.680             0.120
BeautifulSoup-Custom            0.650   0.701     0.673          0.590             0.180
```

**Understanding Metrics**:
- **Precision**: % of extracted text that is correct (higher = less noise)
- **Recall**: % of actual content that was extracted (higher = more complete)
- **F1 Score**: Balanced measure (harmonic mean of precision & recall)
- **With Snippets**: % of "must include" sentences found (higher = better)
- **Without Snippets**: % of "exclude" snippets found (lower = better)

## Incremental Approach

### Start Small
Test with first 100 pages:
```bash
# Download first 100
python scripts/01_download_pages.py  # Will download all, or modify to limit

# Annotate first 100
python scripts/02_create_annotations.py --api-key KEY --start 1 --end 100
```

### Scale Up
Once confident with results:
```bash
# Annotate next batch
python scripts/02_create_annotations.py --api-key KEY --start 101 --end 500

# Or annotate all remaining
python scripts/02_create_annotations.py --api-key KEY --start 101
```

## File Naming Convention

- **HTML files**: `0001.html`, `0002.html`, ..., `2836.html`
- **Annotations**: `0001.json`, `0002.json`, ..., `2836.json`
- **Metadata**: Single `metadata.csv` file

## Example Annotation Output

```json
{
  "url": "https://www.nytimes.com/2025/07/02/well/eat/nutrition-food-tips-2025.html",
  "file_id": "0001",
  "downloaded_at": "2025-12-20T17:45:00Z",
  "ground_truth": {
    "title": "Top Nutrition Trends for 2025",
    "author": "Jane Smith",
    "publish_date": "2025-07-02",
    "main_content": "Full article text here...",
    "with": [
      "Key nutrition trends include plant-based proteins",
      "Experts recommend reducing processed foods",
      "New research shows benefits of Mediterranean diet"
    ],
    "without": [
      "Subscribe to our newsletter",
      "Related Articles",
      "Advertisement"
    ]
  },
  "model": "deepseek-chat",
  "annotated_at": "2025-12-20T18:00:00Z"
}
```

## Troubleshooting

### Download Issues
- Check internet connection
- Verify URLs in `data/urls.txt`
- Adjust timeout in script if needed
- Check `data/download_progress.json` for resume point

### Annotation Issues
- Verify Deepseek API key is valid
- Check API quota/limits
- Review failed annotations in output
- Reduce concurrent requests if rate limited

### Resume After Interruption
Both scripts auto-resume:
- Downloads skip existing HTML files
- Annotations skip existing JSON files
- Safe to Ctrl+C and restart
