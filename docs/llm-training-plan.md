# LLM Training Plan: Web Content Extraction Model

## Project Context

This plan lives within the **Web Content Extraction Benchmark** project. The benchmark evaluates how well algorithms extract main article content from raw HTML pages, stripping away navigation, ads, footers, and other boilerplate.

### Repository

- **Repo root**: `/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/`
- **GitHub**: https://github.com/Murrough-Foley/web-content-extraction-benchmark

### Key Paths

| Path | Description |
|---|---|
| `benchmark/html/` | 720 raw HTML files (236 MB total) |
| `benchmark/html-sanitized/` | 720 sanitized HTML files (82 MB, scripts/styles/SVG removed) |
| `benchmark/ground-truth/` | 712 annotated GT JSON files (v2.0 schema, human-verified) |
| `benchmark-package/` | Published benchmark with evaluate.py and results |
| `benchmark-package/output/` | Extractor output JSON files |
| `benchmark-package/evaluate.py` | Evaluation script (shingle-based F1/P/R) |
| `annotation_tool/` | GT annotation tool (server.py on port 8777) |
| `docs/` | Documentation and plans |
| `scripts/` | Utility scripts |

### GT Format (v2.0 schema)

```json
{
  "schema_version": "2.0",
  "url": "https://example.com/article",
  "file_id": "0001",
  "ground_truth": {
    "title": "Article Title",
    "author": "Author Name",
    "publish_date": "2025-01-15",
    "main_content": "Plain text content, no markdown. Paragraphs separated by double newlines.",
    "with": ["Sentences that MUST be in extraction"],
    "without": ["Boilerplate that must NOT be in extraction"]
  }
}
```

Rules: Plain text only in main_content. No markdown formatting (`#`, `**`, `*`). Headings as plain text on their own lines. Paragraphs separated by `\n\n`.

### Current Benchmark Results (712 curated pages)

| Extractor | F1 | Precision | Recall | Speed |
|---|---|---|---|---|
| rs-trafilatura | 0.868 | 0.875 | 0.900 | 20.2 ms |
| dom-smoothie | 0.783 | 0.756 | 0.879 | 6.0 ms |
| trafilatura | 0.766 | 0.747 | 0.862 | 21.2 ms |

### Key References

- Unsloth docs: https://unsloth.ai/docs
- Unsloth Qwen3.5 notebooks: https://unsloth.ai/docs/get-started/unsloth-notebooks
- Unsloth dataset guide: https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/datasets-guide
- ChatNoir benchmark: https://github.com/chatnoir-eu/web-content-extraction-benchmark
- ReaderLM-v2 (competitor): https://huggingface.co/jinaai/ReaderLM-v2
- Qwen3.5-4B: https://huggingface.co/Qwen/Qwen3.5-4B
- Qwen3.5-27B: https://huggingface.co/Qwen/Qwen3.5-27B

---

## Goal

Fine-tune an LLM that reliably extracts the main content from web pages, outperforming existing shared models (ReaderLM-v2, traditional extractors). Publish the model on Hugging Face as an open contribution to the web extraction community.

## Target Performance

| Extractor | F1 Score | Notes |
|---|---|---|
| rs-trafilatura (current best traditional) | 0.868 | Must beat this |
| ReaderLM-v2 (Jina AI, 1.5B params) | TBD on our benchmark | Stretch goal |
| **Our model** | **>0.90** | Target |

## Base Model Selection

Train all four Qwen3.5 small models and compare. All share 256K context, dense architecture, and Apache 2.0 license. The training data and pipeline are identical — only the base model changes.

| Model | Params | VRAM (4-bit QLoRA) | Colab Tier | Unsloth Notebook | Inference Speed |
|---|---|---|---|---|---|
| **Qwen3.5-0.8B** | 0.9B | ~3 GB | Free (T4) | Yes | Fastest |
| **Qwen3.5-2B** | 2B | ~4 GB | Free (T4) | Yes | Fast |
| **Qwen3.5-4B** | 5B | ~6 GB | Free (T4) | Yes | Medium |
| **Qwen3.5-9B** | 10B | ~8 GB | Free (T4, tight) | Not yet listed | Slower |

All run locally on AMD Radeon 24GB for inference.

Key comparison: ReaderLM-v2 (Jina AI) is 1.5B params — the Qwen3.5-2B is the closest size match. If our 2B beats ReaderLM-v2, that's a strong story for publication. The 0.8B would be remarkable if competitive — smallest extraction model available.

Publish the best performer (or all of them as a model family if multiple sizes are useful).

## Training Method

- **Supervised Fine-Tuning (SFT)** using Unsloth on Google Colab
- **4-bit QLoRA** to fit in free-tier T4 VRAM (15GB)
- **ChatML format** for training data

## Dataset Summary

### Target: 1,000 high-quality, page-type-balanced examples (primary dataset)

| Source | Pages | Quality | Era |
|---|---|---|---|
| Our benchmark (curated GT) | 712 | Human-verified, high quality | 2025-2026 |
| Cherry-picked from benchmark-package | ~288 | AI-generated GT, upgraded to v2.0 | 2025-2026 |
| **Primary total** | **~1,000** | **High quality, balanced** | **2025-2026** |
| ChatNoir combined (8 datasets) | ~2,500 | Varies (hand/CSS-annotated) | 2007-2019 |
| Synthetic augmentation | ~1,000-2,000 | HTML mutations of primary GT | 2025-2026 |
| **Grand total** | **~4,500-5,500** | Mixed | Mixed |

### Page Type Balance Target

There are 1,157 unused pages in `benchmark-package/` (have HTML + AI-generated GT but not in our curated set). These are the source for filling page type gaps.

| Type | Current (712) | Target (1,000) | Need | Source |
|---|---|---|---|---|
| article | 417 (58.6%) | 450 (45%) | +33 | benchmark-package pool |
| forum | 78 (11.0%) | 120 (12%) | +42 | benchmark-package pool |
| service | 76 (10.7%) | 110 (11%) | +34 | benchmark-package pool |
| product | 52 (7.3%) | 100 (10%) | +48 | benchmark-package pool |
| documentation | 37 (5.2%) | 80 (8%) | +43 | benchmark-package pool |
| collection | 28 (3.9%) | 70 (7%) | +42 | benchmark-package pool |
| listing | 24 (3.4%) | 70 (7%) | +46 | benchmark-package pool |

Steps to fill gaps:
1. Classify the 1,157 unused pages by page type (LLM pass over URLs/HTML)
2. Cherry-pick ~288 pages to fill the gaps above
3. Review and upgrade their GT to v2.0 quality standard
4. Add to `benchmark/ground-truth/` and `benchmark/html/`

### ChatNoir Sub-datasets (Apache 2.0)

Source: https://github.com/chatnoir-eu/web-content-extraction-benchmark

| Dataset | Approx Size | Description |
|---|---|---|
| CleanEval | ~800 | Classic extraction benchmark (2007) |
| CleanPortalEval | ~100 | Portal/homepage variant |
| CETD | ~150 | ArsTechnica, BBC, NYTimes, Yahoo, Wiki |
| Dragnet | ~300 | News articles with corrected GT |
| Google Trends 2017 | ~500 | Trending articles |
| L3S-GN1 | ~600 | Google News, CSS-annotated |
| Readability | ~50 | Mozilla Readability.js test cases |
| Scrapinghub | 184 | Original ScrapingHub benchmark |

### Synthetic Augmentation Strategy

Take our existing HTML+GT pairs and create variations by:
- Renaming CSS classes and IDs
- Injecting ad divs, cookie banners, newsletter popups
- Changing wrapper tags (article -> div, etc.)
- Shuffling sidebar/nav positions

The ground truth answer stays the same. This teaches the model not to rely on specific class names or page layouts.

---

## Phases

### Phase 1: Data Preparation

#### 1a. Sanitize HTML files ✅ DONE

Strip token-wasting content from all 720 HTML files. Script: `scripts/sanitize_html.py`

| Tag/Pattern | % of Total HTML | Action |
|---|---|---|
| `<script>` | 35.7% (83.5 MB) | Remove |
| `<style>` | 15.4% (36.1 MB) | Remove |
| `<svg>` | 6.6% (15.5 MB) | Remove |
| `<!-- comments -->` | 0.7% (1.5 MB) | Remove |
| `<noscript>` | Minor | Remove |
| `<iframe>` | Minor | Remove |
| `data-*` attributes | Minor | Remove |
| `on*` event handlers | Minor | Remove |

**Actual result: 65.2% reduction** (236 MB → 82 MB). Handles unclosed/malformed tags.

Output: `benchmark/html-sanitized/` directory with cleaned HTML files (720 files, zero remnants).

#### 1b. Complete remaining ground truth annotations ✅ DONE

- 712 GT files annotated and verified against HTML source
- **All files 0001-0719 fully verified**: completeness, boilerplate, accuracy, formatting, snippets

**Files removed (no usable content):**

| ID | Issue |
|---|---|
| 0539 | Audacity Discourse — JS-rendered shell, no server-side content |
| 0542 | Anubis bot protection page, not a forum |
| 0571 | Discourse Meta — JS-rendered, empty body |
| 0572 | Lemmy — content behind auth wall |
| 0623 | Apple search results page, not a product page |
| 0630 | Empty HTML shell (90 bytes) |
| 0657 | Shopify collection — fully JS-rendered, no content |

**Thin GT files fixed:**

| ID | Issue | Resolution |
|---|---|---|
| 0577 | Student Room — single long HTML line | Reviewed |
| 0580 | Allbirds Wool Runner — thin product description | Reviewed |
| 0582 | Bombas Quarter Socks — was truncated | Fixed: expanded with product features |
| 0585 | Ruggable Beatrice Rug — thin, JS-rendered | Reviewed |
| 0698 | Stripe Payments — was fabricated UI text | Fixed: replaced with actual page content |
| 0705 | Intercom — empty, JS-rendered | Confirmed: empty main_content correct |
| 0706 | Fiverr Writing — was fabricated content | Fixed: set to empty (JS-rendered) |
| 0714 | SmartCat GenAI — was truncated (3 lines) | Fixed: expanded to full page content |
| 0717 | DoodloDesigns Packaging — thin | Reviewed |

#### 1c. Expand dataset to 1,000 with page type balancing

There are 1,157 unused pages in `benchmark-package/` that have HTML (`benchmark-package/html/*.html.gz`) and AI-generated GT (`benchmark-package/ground-truth.json`) but are not in our curated working set. We need ~288 of them to reach 1,000 balanced examples.

Steps:
1. Write a script to classify all 1,157 unused pages by page type (use URL patterns + HTML structure)
2. Select ~288 pages to fill the gaps: +48 product, +46 listing, +43 documentation, +42 forum, +42 collection, +34 service, +33 article
3. Copy selected HTML files to `benchmark/html/`
4. Convert their GT from `benchmark-package/ground-truth.json` format (`articleBody`) to our v2.0 schema
5. Review and upgrade GT quality in annotation tool — the package GT is AI-generated (older, lower quality than our curated set)
6. Sanitize the new HTML files (run sanitize script on additions)

Priority: Focus on the most underrepresented types first (product, listing, documentation).

#### 1d. Integrate ChatNoir datasets

- Download and extract the ChatNoir combined dataset (Git LFS required)
- Convert from their JSONL format to our training format
- Quality check: spot-check samples from each sub-dataset
- Note: These are older web pages (2007-2019) - use as supplementary training data

#### 1e. Generate synthetic augmentations

- Write a script to mutate HTML while preserving GT content
- Target ~1,000-2,000 synthetic variations from our 1,000 curated pairs
- Focus augmentation on underrepresented page types (product, listing, documentation) for extra balance
- Validate that GT content still appears in mutated HTML

### Phase 2: Training Data Conversion

Convert all data sources into Unsloth-compatible ChatML format:

```json
{"messages": [
  {"role": "system", "content": "Extract the main content from this HTML page. Return JSON with title, author, date, and content fields."},
  {"role": "user", "content": "<sanitized HTML>"},
  {"role": "assistant", "content": "{\"title\": \"...\", \"author\": \"...\", \"publish_date\": \"...\", \"main_content\": \"...\"}"}
]}
```

Dataset splits:
- **Training**: All 1,000 curated pages + ChatNoir + synthetic augmentation (~4,500-5,500 samples)
- **Validation**: ~5-10% held out from training set for monitoring loss (~250-500 samples)
- **Evaluation**: Completely separate benchmark (see Phase 3) — never seen during training

### Phase 3: Build Evaluation Benchmark (500 pages)

The trained model cannot be evaluated on any data it was trained on. Build a completely independent benchmark with fresh pages from new domains.

**Target composition** (mirrors training distribution):

| Type | % | Count |
|---|---|---|
| article | 45% | 225 |
| forum | 12% | 60 |
| service | 11% | 55 |
| product | 10% | 50 |
| documentation | 8% | 40 |
| collection | 7% | 35 |
| listing | 7% | 35 |
| **Total** | **100%** | **500** |

**Requirements:**
- Zero domain overlap with the 1,507 domains in benchmark-package
- Same v2.0 GT schema, same human verification quality
- Sanitized HTML (same script as training data)

**Process:**
1. Source new URLs for each page type (use existing `scripts/download_*_html.py` as templates)
2. Download HTML with Playwright (`scripts/download_with_playwright.py`) to capture JS-rendered content
3. LLM-draft GT (DeepSeek/Claude) for each page
4. Human verify all 500 GT files in annotation tool
5. Sanitize HTML
6. Store in `eval-benchmark/` directory (separate from training data)

**Timing:** Can run in parallel with Phase 2 (training data conversion) and Phase 4 (fine-tuning). Must be complete before Phase 5 (evaluation).

### Phase 4: Fine-Tuning

Train all four Qwen3.5 small models using identical data and hyperparameters:

- Platform: Google Colab (free tier T4 — all models fit)
- Framework: Unsloth + HuggingFace TRL
- Method: 4-bit QLoRA SFT
- Start with Unsloth's Qwen3.5 notebook as template
- Hyperparameters: Start with Unsloth defaults, tune learning rate and epochs
- Monitor validation loss to avoid overfitting
- Save checkpoints for each model

Training order (smallest first — fastest iteration, catches data issues early):
1. `unsloth/Qwen3.5-0.8B` — quickest to train, sanity check the pipeline
2. `unsloth/Qwen3.5-2B` — direct ReaderLM-v2 size competitor
3. `unsloth/Qwen3.5-4B` — expected sweet spot
4. `unsloth/Qwen3.5-9B` — quality ceiling test

### Phase 5: Evaluation

Run all four fine-tuned models against the **eval benchmark** (500 fresh pages) and compare:

| Metric | 0.8B | 2B | 4B | 9B | rs-trafilatura | ReaderLM-v2 |
|---|---|---|---|---|---|---|
| F1 Score | ? | ? | ? | ? | 0.868 | TBD |
| Precision | ? | ? | ? | ? | 0.875 | TBD |
| Recall | ? | ? | ? | ? | 0.900 | TBD |
| With% | ? | ? | ? | ? | 74.8% | TBD |
| Without% | ? | ? | ? | ? | 8.3% | TBD |
| Speed (ms/page) | ? | ? | ? | ? | 20.2 | TBD |

Additional evaluation:
- Break down F1 by page type (article, forum, product, docs, service) to check for weaknesses
- Run traditional extractors (rs-trafilatura, trafilatura, dom-smoothie) on the same eval benchmark for direct comparison
- Run ReaderLM-v2 on the eval benchmark
- Test on ScrapingHub benchmark for cross-benchmark validation
- Measure inference speed on local AMD GPU

### Phase 6: Publication

- Upload best model(s) to Hugging Face with model card
- If multiple sizes are competitive, publish as a model family (e.g., WebExtract-0.8B, -2B, -4B, -9B)
- Write up the training process, methodology, and comparative results
- Add the model(s) as extractors in our benchmark results table
- Share on relevant communities (r/LocalLLaMA, HuggingFace, etc.)

---

## Key Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Smaller models too weak for extraction | Poor quality | Training all four sizes — compare and publish best |
| Old ChatNoir data hurts modern performance | Lower scores on our benchmark | Weight modern data higher, validate on modern-only set |
| Long HTML exceeds context window | Truncated input | Sanitization reduces 99% of files to <256K tokens |
| Overfitting on small dataset | Poor generalization | Augmentation + ChatNoir data + validation monitoring |
| Free Colab disconnects during training | Lost training progress | Save checkpoints, use Colab Pro if needed |

## Hardware

**Training**: Google Colab (T4 16GB free tier, A100 80GB if stepping up to larger model)
**Local inference**: AMD Radeon 24GB + AMD Ryzen iGPU 31GB (shared RAM)

## Estimated Costs

| Scenario | Cost |
|---|---|
| All 4 small models (0.8B, 2B, 4B, 9B) on Colab free tier | $0 |
| Colab Pro (if free tier disconnects or quotas hit) | ~$12/month |
