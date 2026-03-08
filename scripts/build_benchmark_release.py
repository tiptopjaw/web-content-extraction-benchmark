#!/usr/bin/env python3
"""
Build the public benchmark release package.

Reads 500 curated ground truth files from benchmark/ground-truth/,
strips internal metadata, gzips HTML files, and assembles a self-contained
release/ directory with everything needed to run the benchmark.

Usage:
    python3 scripts/build_benchmark_release.py
"""

import gzip
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = ROOT / "benchmark"
GT_DIR = BENCHMARK_DIR / "ground-truth"
HTML_DIR = BENCHMARK_DIR / "html"
RELEASE_DIR = ROOT / "release"

# Fields to strip from individual GT files
STRIP_FIELDS = {"_internal", "model", "annotated_at", "schema_version", "file_id"}


def build_ground_truth() -> dict:
    """Read all GT files and transform into the flat release format."""
    gt_files = sorted(GT_DIR.glob("*.json"))
    if not gt_files:
        raise FileNotFoundError(f"No ground truth files found in {GT_DIR}")

    combined = {}
    for gt_path in gt_files:
        file_id = gt_path.stem  # e.g. "0001"
        with open(gt_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        gt = data.get("ground_truth", {})
        entry = {
            "articleBody": gt.get("main_content", ""),
            "url": data.get("url", ""),
            "title": gt.get("title", ""),
            "author": gt.get("author", ""),
            "publish_date": gt.get("publish_date", ""),
            "with": gt.get("with", []),
            "without": gt.get("without", []),
        }
        combined[file_id] = entry

    return combined


def gzip_html_files(dest_dir: Path) -> int:
    """Gzip all HTML files into dest_dir. Returns count."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    html_files = sorted(HTML_DIR.glob("*.html"))
    for html_path in html_files:
        gz_path = dest_dir / f"{html_path.name}.gz"
        with open(html_path, "rb") as f_in:
            with gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    return len(html_files)


def generate_readme(num_pages: int) -> str:
    """Generate README.md adapted for the curated 500-file dataset."""
    return f"""# Web Content Extraction Benchmark

**A curated benchmark for evaluating web content extraction and boilerplate removal algorithms.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.6+](https://img.shields.io/badge/Python-3.6+-green.svg)](https://www.python.org/)
[![Dataset: {num_pages} pages](https://img.shields.io/badge/Dataset-{num_pages}%20pages-orange.svg)](#dataset)

This benchmark provides **{num_pages} modern web pages** (collected in 2026) with human-verified ground truth annotations for evaluating article body extraction quality. It uses the same evaluation methodology as the widely-cited [ScrapingHub Article Extraction Benchmark](https://github.com/scrapinghub/article-extraction-benchmark), enabling direct comparison while providing a larger, curated test set from the modern web.

---

## Quick Start

```bash
# 1. Run your extractor on the HTML files and save output to output/
python your_extractor_script.py  # outputs to output/my-extractor.json

# 2. Evaluate
python evaluate.py
```

**Output:**
```
Extractor                F1             Precision      Recall         Accuracy
--------------------------------------------------------------------------------
my-extractor             0.725 +/- 0.009  0.698 +/- 0.011  0.754 +/- 0.008  0.142 +/- 0.025
```

---

## Dataset

### Overview

| Property | Value |
|----------|-------|
| **Total pages** | {num_pages} |
| **Collection date** | 2026 |
| **Ground truth method** | AI-generated with human verification |
| **HTML storage** | Gzip-compressed |

### Content Types

The dataset includes diverse content from across the web:

- **News articles** and journalism
- **Blog posts** and opinion pieces
- **Technical documentation** and tutorials
- **How-to guides** and educational content
- **Product reviews** and comparisons
- **Corporate pages** and about pages
- **Research summaries** and reports

---

## Evaluation Methodology

This benchmark uses the same evaluation approach as the [ScrapingHub Article Extraction Benchmark](https://github.com/scrapinghub/article-extraction-benchmark), enabling direct comparison of results.

### Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| **Precision** | What fraction of extracted text is actual article content? | TP / (TP + FP) |
| **Recall** | What fraction of the article was successfully extracted? | TP / (TP + FN) |
| **F1 Score** | Harmonic mean of precision and recall | 2 x (P x R) / (P + R) |
| **Accuracy** | Exact match after tokenization | extracted_tokens == ground_truth_tokens |

### Shingle-Based Matching

Unlike simple word overlap, this benchmark uses **4-gram shingle matching**:

1. Text is tokenized into words
2. Words are grouped into overlapping 4-word sequences (shingles)
3. Shingles are compared between extraction and ground truth
4. True positives, false positives, and false negatives are computed

### Snippet Validation

In addition to standard metrics, this benchmark provides **snippet-based validation**:

- **"With" snippets**: Sentences that MUST appear in a good extraction
- **"Without" snippets**: Boilerplate text that should NOT appear

Use `python evaluate.py --snippets` to include snippet coverage metrics.

---

## Running Your Extractor

### Step 1: Process HTML Files

Read each gzipped HTML file, run your extraction, and collect results:

```python
import gzip
import json
from pathlib import Path

results = {{}}

for html_path in Path('html').glob('*.html.gz'):
    file_id = html_path.stem.replace('.html', '')

    with gzip.open(html_path, 'rt', encoding='utf-8') as f:
        html = f.read()

    extracted_text = your_extractor(html)
    results[file_id] = {{'articleBody': extracted_text}}

with open('output/my-extractor.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False)
```

### Step 2: Output Format

Your output JSON must follow this structure:

```json
{{
  "0001": {{"articleBody": "Extracted text for page 0001..."}},
  "0002": {{"articleBody": "Extracted text for page 0002..."}}
}}
```

- Keys must match file IDs (e.g., `0001`, `0002`)
- Each entry must have an `articleBody` field containing the extracted text

### Step 3: Evaluate

```bash
python evaluate.py                    # Basic metrics
python evaluate.py --snippets         # Include snippet coverage
python evaluate.py --output results.json  # Save to JSON
```

---

## Data Format

### Ground Truth (ground-truth.json)

```json
{{
  "0001": {{
    "articleBody": "The main article text that extractors should capture...",
    "url": "https://example.com/article",
    "title": "Article Title",
    "author": "Author Name",
    "publish_date": "2025-01-15",
    "with": [
      "Sentence that MUST appear in extraction",
      "Another critical sentence from the article"
    ],
    "without": [
      "Subscribe to our newsletter",
      "Cookie policy text"
    ]
  }}
}}
```

### HTML Files (html/*.html.gz)

- Gzip-compressed HTML files, UTF-8 encoded
- Named by file ID (e.g., `0001.html.gz`)

### Prediction Output (output/*.json)

```json
{{
  "0001": {{"articleBody": "Your extracted text..."}},
  "0002": {{"articleBody": "Your extracted text..."}}
}}
```

---

## License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## Citation

If you use this benchmark in your research or development, please cite:

```bibtex
@misc{{web-content-extraction-benchmark-2026,
  title={{Web Content Extraction Benchmark}},
  author={{Foley, Murrough}},
  year={{2026}},
  url={{https://github.com/Murrough-Foley/web-content-extraction-benchmark}},
  note={{A curated benchmark dataset of {num_pages} modern web pages for evaluating content extraction algorithms}}
}}
```

---

## Acknowledgments

- **Evaluation methodology** based on [ScrapingHub Article Extraction Benchmark](https://github.com/scrapinghub/article-extraction-benchmark)
- **Ground truth generation** powered by frontier AI models with human quality review
"""


def main():
    print(f"Building benchmark release package...")
    print(f"  Source GT:   {GT_DIR}")
    print(f"  Source HTML: {HTML_DIR}")
    print(f"  Output:      {RELEASE_DIR}")
    print()

    # Clean previous release
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    RELEASE_DIR.mkdir(parents=True)

    # 1. Build combined ground truth
    print("Building ground-truth.json...")
    ground_truth = build_ground_truth()
    gt_path = RELEASE_DIR / "ground-truth.json"
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"  {len(ground_truth)} entries written")

    # 2. Gzip HTML files
    print("Gzipping HTML files...")
    html_count = gzip_html_files(RELEASE_DIR / "html")
    print(f"  {html_count} files compressed")

    # 3. Copy evaluate.py
    print("Copying evaluate.py...")
    shutil.copy2(ROOT / "evaluate.py", RELEASE_DIR / "evaluate.py")

    # 4. Copy LICENSE
    print("Copying LICENSE...")
    license_src = ROOT / "benchmark-package" / "LICENSE"
    shutil.copy2(license_src, RELEASE_DIR / "LICENSE")

    # 5. Generate README
    print("Generating README.md...")
    readme = generate_readme(len(ground_truth))
    (RELEASE_DIR / "README.md").write_text(readme, encoding="utf-8")

    # 6. Create output directory with .gitkeep
    print("Creating output/ directory...")
    output_dir = RELEASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / ".gitkeep").touch()

    # Summary
    print()
    print("Release package built successfully!")
    print(f"  {len(ground_truth)} ground truth entries")
    print(f"  {html_count} gzipped HTML files")
    print(f"  Output: {RELEASE_DIR}/")


if __name__ == "__main__":
    main()
