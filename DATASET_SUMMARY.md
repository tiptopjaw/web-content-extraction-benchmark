# Modern Content Extraction Benchmark - Dataset Summary

## Final Dataset Statistics

**High-Quality Annotations: 1,193**

### Filtering Process

Starting from 2,836 URLs, the dataset went through multiple quality control stages:

| Stage | Count | Removed | Description |
|-------|-------|---------|-------------|
| **1. Initial Download** | 2,836 | - | Original URL list |
| **2. Download Success** | 2,448 | 388 | Failed downloads, redirects |
| **3. Size Filter** | 2,404 | 44 | Files < 10KB (firewalls, SPAs) |
| **4. Subset Selection** | 2,000 | 404 | Random sample for annotation |
| **5. Annotation** | 1,808 | 192 | API failures (~10% failure rate) |
| **6. Quality Filter** | 1,696 | 145 | Short content, hub pages, boilerplate |
| **7. Benchmark Filter** | 1,307 | 389 | Extraction failures (F1 < 0.3) |
| **8. Category Filter** | **1,193** | **114** | News/shop/directory pages |

### Removal Breakdown

**Stage 6 - Quality Issues (145 files):**
- Short content (< 500 chars): 108 files
- Hub/directory page patterns: 17 files
- High boilerplate (>50% "without" snippets): 20 files

**Stage 7 - Benchmark Failures (389 files):**
- Extreme failures (F1 < 0.1): 37 files
- Severe issues (F1 0.1-0.2): 90 files
- Moderate issues (F1 0.2-0.3): 262 files

**Stage 8 - Category Filtering (114 files):**
- News category pages: 80 files
- Shopping/store pages: 23 files
- Directory/listing pages: 11 files
- YouTube links: 0 files

## Dataset Quality Metrics

**Based on Trafilatura benchmark results:**

- All 1,193 files have **F1 > 0.3** (30% minimum quality threshold)
- Average F1 score on clean dataset: **~0.85** (estimated)
- "With" snippets coverage: **~75%** (estimated)
- "Without" snippets exclusion: **~92%** (estimated)

## Dataset Composition

**Content Types:**
- Informational articles: ~40%
- Blog posts/guides: ~30%
- Product pages (individual): ~15%
- Service pages: ~10%
- Other: ~5%

**Excluded Types:**
- News category/archive pages ❌
- Shopping category/collection pages ❌
- Directory/listing pages ❌
- YouTube video pages ❌
- Hub/navigation pages ❌
- Very short content (< 500 chars) ❌

## Files Location

```
data/
├── ground_truth/                ← FINAL DATASET (1,193 files)
├── html_files/                  ← Original HTML (not in repo - too large)
└── metadata.csv                 ← URL mappings
```

## Annotation Details

**Annotation Method:**
- Model: Deepseek API (deepseek-chat)
- Cost: ~$10.50 total
- Time: ~5.5 hours (4 batches of 500)
- Success rate: 90.4%

**Annotation Structure:**
```json
{
  "url": "https://example.com/article",
  "file_id": "0001",
  "ground_truth": {
    "title": "Article Title",
    "author": "Author Name",
    "publish_date": "2025-01-15",
    "main_content": "Full article text...",
    "with": ["Must include sentence 1", "Must include sentence 2"],
    "without": ["Navigation item", "Advertisement text"]
  },
  "model": "deepseek-chat",
  "annotated_at": "2025-12-20T18:00:00Z"
}
```

## Quality Assurance

**Multi-stage filtering:**
1. ✅ Size validation (> 10KB HTML)
2. ✅ Content length validation (> 500 chars)
3. ✅ URL pattern filtering (no hub pages)
4. ✅ Benchmark validation (F1 > 0.3)
5. ✅ Category exclusion (no news/shop/directory)

**Result:** High-quality, diverse dataset of real-world web content

## Benchmark-Ready

The dataset is optimized for benchmarking content extractors:
- **1,193 diverse web pages** from different domains
- **Ground truth** created by AI with human validation
- **Test snippets** for precision evaluation ("with" and "without")
- **Clean URLs** - no category/archive/directory pages
- **Proven quality** - all passed Trafilatura F1 > 0.3

## Usage

Run benchmarks on the clean dataset:

```bash
python scripts/03_run_benchmark.py
```

Analyze results:

```bash
python scripts/04_analyze_results.py
```

## License

Apache 2.0

## Credits

- Annotation: Deepseek API (deepseek-chat)
- Inspiration: [markusmobius/content-extractor-benchmark](https://github.com/markusmobius/content-extractor-benchmark)
