# LLM Evaluation Benchmark Plan

## Purpose

Build a completely independent benchmark of 500 web pages to evaluate our fine-tuned extraction models. No page or domain in this benchmark may appear in the training data. This ensures published results are valid and not contaminated by training data leakage.

## Requirements

- **500 pages** from fresh domains
- **Zero overlap** with the 1,507 domains already in `benchmark-package/`
- **Same v2.0 GT schema** and quality standard as training data
- **Same page type distribution** as training set
- **Sanitized HTML** using the same `scripts/sanitize_html.py` pipeline
- All traditional extractors + ReaderLM-v2 must also be run against this benchmark for comparison

## Page Type Targets

| Type | % | Count | URL Source Strategy |
|---|---|---|---|
| article | 45% | 225 | Google News, RSS feeds, blog aggregators |
| forum | 12% | 60 | Reddit, Discourse instances, Stack Exchange sites, phpBB forums |
| service | 11% | 55 | SaaS company pages, agency sites, consulting firms |
| product | 10% | 50 | Shopify stores, Amazon, DTC brands, Etsy |
| documentation | 8% | 40 | ReadTheDocs, GitBook, MDN, language/framework docs |
| collection | 7% | 35 | Curated lists, roundups, "best of" articles, resource pages |
| listing | 7% | 35 | Directory pages, job boards, event listings, classifieds |
| **Total** | **100%** | **500** | |

## Existing Tools (reuse from training benchmark)

| Tool | Path | Purpose |
|---|---|---|
| Playwright fetcher | `scripts/fetch_new_pages_pw.py` | Download HTML with JS rendering, creates stub GT |
| URL classifier | `scripts/classify_page_type.py` | Classify URLs by page type heuristics |
| GT annotator | `scripts/annotate_stubs.py` | LLM-draft GT from HTML via BeautifulSoup |
| Sanitizer | `scripts/sanitize_html.py` | Strip scripts, styles, SVG, comments |
| GT quality scanner | `scripts/scan_gt_quality.py` | Check GT for common issues |
| GT validator | `scripts/validate_ground_truth.py` | Validate v2.0 schema compliance |
| Annotation tool | `annotation_tool/server.py` (port 8777) | Browser-based manual GT review |
| Evaluation script | `benchmark-package/evaluate.py` | Shingle-based F1/P/R scoring |

## Domain Exclusion

The file `benchmark-package/ground-truth.json` contains URLs for all 1,507 existing pages across 1,507 unique domains. A domain exclusion list must be generated and checked against during URL collection.

Script needed: `scripts/generate_domain_exclusion_list.py`
- Extract all domains from `benchmark-package/ground-truth.json`
- Extract all domains from `benchmark/ground-truth/*.json`
- Output: `eval-benchmark/excluded_domains.txt` (one domain per line, no www prefix)

---

## Phases

### Phase A: Setup

1. Create directory structure:
   ```
   eval-benchmark/
   ├── html/              # Raw HTML files
   ├── html-sanitized/    # Sanitized HTML files
   ├── ground-truth/      # v2.0 GT JSON files
   ├── output/            # Extractor results (for evaluation)
   ├── excluded_domains.txt
   └── evaluate.py        # Copy of benchmark-package/evaluate.py
   ```
2. Generate domain exclusion list from existing benchmark
3. Assign file ID range: 2001-2500 (avoids collision with existing 0001-1507)

### Phase B: URL Collection (per page type)

Collect URLs in batches by type. For each URL, verify the domain is not in the exclusion list before proceeding.

#### Articles (225 pages)

Sources:
- Google News (different topics/regions than training set)
- RSS feeds from news sites not in existing benchmark
- Blog aggregators, Medium publications, Substack newsletters
- Reference: Existing article URLs in `docs/` for patterns to avoid

Diversity targets:
- Mix of news, blogs, opinion, guides, tutorials
- International English-language sites (UK, AU, IN, not just US)
- Mix of large publishers and small independent sites

#### Forums (60 pages)

Sources:
- Reddit threads (different subreddits than training set)
- Discourse instances (new communities)
- Stack Exchange sites (less common ones: cooking, travel, music)
- phpBB/vBulletin forums
- Reference: `docs/forum-thread-urls.md` for patterns used in training

Diversity targets:
- Mix of threaded (Reddit, Discourse) and flat (phpBB) layouts
- Short threads (2-5 replies) and long threads (20+ replies)
- Technical and non-technical topics

#### Service Pages (55 pages)

Sources:
- SaaS company feature/product pages
- Agency/consulting firm service descriptions
- Professional services (legal, accounting, healthcare)
- Reference: `docs/service-page-urls.md` for patterns used in training

#### Product Pages (50 pages)

Sources:
- Shopify stores (different from training set)
- WooCommerce stores
- Direct-to-consumer brand sites
- Amazon product pages (if not JS-rendered walls)
- Reference: `docs/product-page-urls.md` for patterns used in training

#### Documentation (40 pages)

Sources:
- ReadTheDocs sites for different projects
- GitBook documentation
- Framework/language docs (new frameworks not in training)
- API documentation pages
- Reference: `docs/documentation-page-urls.md` for patterns used in training

#### Collection Pages (35 pages)

Sources:
- "Best of" roundup articles
- Curated resource lists
- Tool comparison pages
- Reference: `docs/category-page-urls.md` for patterns used in training

#### Listing Pages (35 pages)

Sources:
- Job board listings
- Event listing pages
- Business directories
- Classified ad pages

### Phase C: HTML Download

For each batch of URLs:

1. Run through domain exclusion check
2. Download with Playwright (`scripts/fetch_new_pages_pw.py` adapted for eval-benchmark paths)
   - Use headed mode for pages that may have bot protection
   - Wait for JS rendering (important for forums, products)
3. Verify downloaded HTML has actual content (not empty shells, bot walls, auth gates)
4. Discard pages that are:
   - Fully JS-rendered with no server-side content
   - Behind authentication walls
   - Bot protection pages (Cloudflare challenges, Anubis)
   - Under 1KB of HTML (empty shells)

Expected: Download ~600 pages to end up with 500 usable ones after filtering.

### Phase D: GT Annotation

Two-pass annotation process:

**Pass 1: LLM Draft**
- Run `scripts/annotate_stubs.py` (or equivalent) on all downloaded HTML
- Use DeepSeek/Claude to generate initial GT with title, author, date, main_content, with[], without[]
- Automated quality checks: `scripts/scan_gt_quality.py`

**Pass 2: Human Verification**
- Review all 500 GT files in annotation tool (`annotation_tool/server.py`)
- For each file, verify:
  - main_content matches what a human would extract (no hallucination, no omissions)
  - title is correct
  - with[] snippets actually appear verbatim in main_content
  - without[] snippets are real boilerplate from the HTML
  - No markdown formatting in main_content
  - Correct page type classification
- Flag and fix or discard any problematic pages
- This is the most time-consuming step (~1-2 minutes per page = ~8-16 hours total)

### Phase E: Sanitization and Validation

1. Run `scripts/sanitize_html.py` on all eval HTML → `eval-benchmark/html-sanitized/`
2. Run `scripts/validate_ground_truth.py` on all GT files
3. Final stats check:
   - Confirm 500 pages with valid GT
   - Confirm page type distribution matches targets
   - Confirm zero domain overlap with training data
   - Confirm sanitized HTML token counts are within model context window

### Phase F: Baseline Evaluation

Before using for LLM evaluation, establish baseline scores by running traditional extractors:

1. rs-trafilatura
2. trafilatura (Python)
3. dom-smoothie
4. boilerpy3
5. beautifulsoup
6. ReaderLM-v2

This gives us the comparison table that our fine-tuned models must beat.

---

## Output

The completed eval benchmark will be:
- `eval-benchmark/` directory with 500 pages
- Baseline extractor scores on the eval benchmark
- Ready for Phase 5 of the LLM training plan (`docs/llm-training-plan.md`)

## Estimated Effort

| Phase | Effort | Can Parallelize |
|---|---|---|
| A. Setup | 30 min | — |
| B. URL collection | 3-4 hours | Yes (by page type) |
| C. HTML download | 2-3 hours | Yes (batched) |
| D. GT annotation (LLM draft) | 1-2 hours | Automated |
| D. GT annotation (human verify) | 8-16 hours | Biggest bottleneck |
| E. Sanitization & validation | 30 min | Automated |
| F. Baseline evaluation | 1-2 hours | Automated |
| **Total** | **~16-26 hours** | |

The human verification step (Phase D, Pass 2) is the bottleneck. Everything else is scripted or automated.
