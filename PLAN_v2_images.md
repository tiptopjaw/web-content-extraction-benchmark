# Plan: Benchmark v2 - Images & Page Type Classification

**Status**: Draft - For Review
**Created**: 2026-01-02
**Author**: Claude + User

---

## API Strategy

| Phase | API | Notes |
|-------|-----|-------|
| Development & Testing | MiniMax (M2.1) | Rate-limited but available for testing |
| Production Annotation | DeepSeek | Faster, cost-effective for full dataset |

---

## 1. Overview

### 1.1 Current State
The benchmark currently evaluates text extraction only:
- Title, author, publish date
- Main content text
- "With" snippets (must include)
- "Without" snippets (must exclude/boilerplate)

### 1.2 Proposed Extensions
1. **Image extraction** - Hero image + in-content images (public benchmark)
2. ~~**Link extraction**~~ - Removed (anchor text already covered by text metrics)
3. **Page type classification** - Internal only, for filtering/curation before public release

### 1.3 Goals
- Create a more comprehensive benchmark for modern web extraction
- Enable analysis of extractor performance by content type
- Identify pages that should be excluded from benchmark
- Provide richer ground truth for the community

---

## 2. Updated Ground Truth Schema

### 2.1 Full Schema (v2)

```json
{
  "schema_version": "2.0",
  "url": "https://example.com/article/how-to-cook",
  "file_id": "0001",

  "_internal": {
    "page_type": {
      "primary": "article",
      "confidence": "high",
      "needs_review": false,
      "review_reason": null,
      "tags": ["blog", "how-to", "food"]
    }
  },

  "ground_truth": {
    "title": "How to Cook the Perfect Steak",
    "author": "Jane Smith",
    "publish_date": "2025-06-15",
    "main_content": "Full article text here...",
    "with": [
      "Season the steak generously with salt",
      "Let it rest for 5 minutes before cutting"
    ],
    "without": [
      "Subscribe to our newsletter",
      "Copyright 2025 Example.com"
    ],
    "images": {
      "total_in_content": 8,
      "annotated_count": 2,
      "items": [
        {
          "src": "https://example.com/images/steak-hero.jpg",
          "filename": "steak-hero.jpg",
          "alt": "A perfectly seared ribeye steak on a cutting board",
          "caption": "The finished product: a medium-rare ribeye",
          "is_hero": true
        },
        {
          "src": "https://example.com/images/seasoning.jpg",
          "filename": "seasoning.jpg",
          "alt": "Salt and pepper being applied to raw steak",
          "caption": null,
          "is_hero": false
        }
      ]
    }
  },

  "model": "deepseek-chat",
  "annotated_at": "2026-01-02T12:00:00Z"
}
```

**Note**: The `_internal` field is stripped before public release. It contains curation metadata only.

### 2.2 Field Definitions

#### _internal.page_type (Internal - stripped before public release)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `primary` | string | Yes | Main page category (see list below) |
| `confidence` | string | Yes | "high", "medium", or "low" |
| `needs_review` | boolean | Yes | True if LLM is uncertain and needs human review |
| `review_reason` | string | No | Explanation when needs_review is true |
| `tags` | array[string] | No | Additional descriptive tags |

#### ground_truth.images (Public benchmark)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_in_content` | number | Yes | Total content images found in page |
| `annotated_count` | number | Yes | Number annotated (max 10) |
| `items` | array | Yes | Array of image objects (max 10) |

#### Image Item
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `src` | string | Yes | Full image URL (prefer data-src for lazy-loaded) |
| `filename` | string | Yes | Just the filename (for matching) |
| `alt` | string | No | Alt text attribute (null if missing) |
| `caption` | string | No | Caption/figcaption text (null if none) |
| `is_hero` | boolean | Yes | True if this is the main/hero image |

---

## 3. Page Type Classification

### 3.1 Primary Types

| Type | Code | Description | Keep in Benchmark? |
|------|------|-------------|-------------------|
| Article/Blog | `article` | News, blog posts, editorials, how-to guides | Yes |
| Product Page | `product` | E-commerce single product page | Yes |
| Collection/Category | `collection` | E-commerce listing, category pages | No (remove) |
| Service/Landing | `service` | Service descriptions, landing pages | Maybe |
| Documentation | `documentation` | Help docs, API docs, technical docs | Yes |
| Recipe | `recipe` | Recipe pages with ingredients/instructions | Yes |
| Review | `review` | Product or service reviews | Yes |
| Forum/Q&A | `forum` | Discussion threads, Q&A pages | Maybe |
| Directory/Listing | `directory` | Business listings, link directories | No (remove) |
| Homepage | `homepage` | Site homepages | No (remove) |
| Other | `other` | Doesn't fit categories above | Review case-by-case |

### 3.2 Tags (Optional, for finer analysis)
Examples: `technology`, `food`, `health`, `finance`, `travel`, `sports`, `entertainment`, `business`, `science`, `lifestyle`

---

## 4. Evaluation Metrics

### 4.0 Metric Grouping (Important)

**Text extraction** and **image extraction** are tested SEPARATELY:

| Metric Group | Extractors Evaluated | Notes |
|--------------|---------------------|-------|
| Text Metrics | All packages | Trafilatura, Readability, Boilerpy3, BeautifulSoup, rs-trafilatura |
| Image Metrics | rs-trafilatura only | Other packages don't support structured image extraction |

**Value of image ground truth**:
- Measures rs-trafilatura's image extraction quality over time
- Provides regression testing for rs-trafilatura
- Creates a dataset others can use to benchmark their own implementations

### 4.1 Existing Metrics (unchanged)
- **Text F1 Score**: Precision/recall on main_content
- **Snippet Coverage**: % of "with" snippets found, % of "without" snippets excluded
- **Title Match**: Exact or fuzzy match
- **Metadata Extraction**: Author, date accuracy

### 4.2 New Image Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| Image Recall | `found_images / total_gt_images` | % of ground truth images extracted |
| Image Precision | `correct_images / extracted_images` | % of extracted images that are relevant |
| Image F1 | `2 * (P * R) / (P + R)` | Harmonic mean |
| Hero Image Found | `1 or 0` | Was the hero image extracted? |
| Alt Text Accuracy | `correct_alt / images_with_alt` | % of alt texts correctly extracted |
| Caption Accuracy | `correct_caption / images_with_caption` | % of captions correctly extracted |

**Image Matching Strategy:**
1. Normalize filenames (lowercase, strip query params)
2. Match by filename (not full URL - CDN URLs may differ)
3. For duplicates, match by position/order

### 4.3 Scoring Approach

**No aggregate score** - Report text and image metrics separately.

| Report | Content |
|--------|---------|
| Text Benchmark | All extractors compared on F1, precision, recall, snippet coverage |
| Image Benchmark | rs-trafilatura only - image recall, precision, alt/caption accuracy |

---

## 5. Implementation Plan

### 5.0 Pre-requisite Fixes

**Directory Path Bug** (scripts/03_run_benchmark.py:26):
```python
# Current (BROKEN):
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth_clean"  # Does not exist!

# Fix:
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"  # Actual directory (1,193 files)
```

- [ ] Fix directory path in `03_run_benchmark.py`
- [ ] Search for other references to `ground_truth_clean`

### 5.1 Phase 1: Schema & Infrastructure
- [ ] Update annotation JSON schema
- [ ] Create schema validation script
- [ ] Create image normalization utilities (for filename matching)

#### 5.1.1 Extractor Interface

**Existing extractors** (text-only, unchanged):
```python
def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
    return {
        'title': str,
        'author': str,
        'publish_date': str,
        'main_content': str
    }
```

**rs-trafilatura wrapper** (new, with image support):
```python
def extract(self, html: str, url: str) -> ExtractionResult:
    return {
        'title': str,
        'author': str,
        'publish_date': str,
        'main_content': str,
        'images': List[ImageData],  # rs-trafilatura native support
    }

# Type definitions
ImageData = {'src': str, 'filename': str, 'alt': Optional[str], 'caption': Optional[str], 'is_hero': bool}
```

### 5.2 Phase 2: Extractor Updates
- [ ] Add `rs_trafilatura_extractor.py` wrapper with image extraction
- [ ] Existing extractors unchanged (text benchmarks only)

### 5.3 Phase 3: Annotation Pipeline
- [ ] Update DeepSeek prompt for images + page_type (internal)
- [ ] Update `annotate_batch.py` script
- [ ] Test on 5-10 sample files
- [ ] Review annotation quality

### 5.4 Phase 4: Re-annotate Dataset (PHASED APPROACH)

**Batch 1: Test & Validate (100 files)**
- [ ] Annotate files 0001-0100
- [ ] Manual review of flagged files + random sample
- [ ] Identify prompt issues, adjust if needed
- [ ] Estimated: ~$0.80-1.00

**Batch 2: Middle Sample (100 files)**
- [ ] Annotate files 0550-0650
- [ ] Verify consistency with Batch 1
- [ ] Estimated: ~$0.80-1.00

**Batch 3: Remaining Files (993 files)**
- [ ] Annotate remaining files
- [ ] Final validation
- [ ] Estimated: ~$6-8

**Total Estimated Cost**: ~$8-10 (v2 schema is 2-3x larger than v1)
**Total Estimated Time**: ~8-12 hours API processing

### 5.5 Phase 5: Benchmark Updates
- [ ] Update `03_run_benchmark.py` with new metrics
- [ ] Update `04_analyze_results.py` for new reports
- [ ] Add page-type breakdown analysis
- [ ] Generate comparison reports

### 5.6 Phase 6: Documentation & Cleanup
- [ ] Update README.md
- [ ] Update USAGE.md
- [ ] Document new metrics in results
- [ ] Archive v1 annotations

---

## 6. Potential Issues & Mitigations

### 6.1 Extractor Limitations

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Only rs-trafilatura extracts images | No cross-package comparison | Image benchmark is rs-trafilatura only |
| Boilerpy3 is text-only | No image support | Exclude from image metrics |

### 6.2 Annotation Challenges

| Issue | Impact | Mitigation |
|-------|--------|------------|
| LLM may hallucinate image URLs | Invalid ground truth | Validate URLs exist in HTML |
| Determining "in-content" vs decorative | Inconsistent annotations | Clear prompt with examples |
| Caption vs alt confusion | Wrong field assignment | Explicit definitions in prompt (see 6.2.1) |
| Pages with 50+ images | Annotation bloat | Cap at 10 most relevant (see 6.2.2) |

#### 6.2.1 Caption vs Alt - Explicit Definitions

| Field | HTML Source | What It Is |
|-------|-------------|------------|
| `alt` | `<img alt="...">` attribute | Accessibility text describing the image |
| `caption` | `<figcaption>` or adjacent `<p>` | Editorial text (credit, context, explanation) |
| `filename` | `src`, `data-src`, `data-lazy-src`, `srcset` | The actual image file |

**Lazy-loaded images:** Look for the real URL in `data-src`, `data-lazy-src`, `data-original`, or similar data attributes. The `src` may contain a placeholder.

#### 6.2.2 Image Selection Priority (for 10-image cap)

When a page has more than 10 content images, select in this order:
1. **Hero/featured image** (1 slot)
2. **Images with captions** (up to 4 slots)
3. **Images with meaningful alt text** (up to 3 slots)
4. **Remaining by position** in content (fill remaining slots)

Record total count: `"total_content_images": 47, "annotated_count": 10`

### 6.3 Matching Challenges

| Issue | Impact | Mitigation |
|-------|--------|------------|
| CDN URL variations | False negatives | Match by filename only |
| Relative vs absolute URLs | Matching failures | Normalize all URLs |
| Anchor text with extra whitespace | False negatives | Normalize whitespace |
| Dynamic/JS-loaded images | Not in source HTML | Note in ground truth |

### 6.4 Page Type Challenges

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Ambiguous pages (article + product) | Classification confusion | Use tags for secondary types |
| LLM inconsistent classification | Unreliable filtering | Provide clear examples in prompt |
| New page types emerge | Incomplete taxonomy | Use "other" + review periodically |

#### 6.4.1 Page Type Review Process (Hybrid Approach)

**Step 1: LLM flags uncertain cases**
```json
"page_type": {
  "primary": "article",
  "confidence": "high|medium|low",
  "needs_review": false,
  "review_reason": null
}
```

When confidence is "low", set `needs_review: true` with explanation:
```json
"page_type": {
  "primary": "service",
  "confidence": "low",
  "needs_review": true,
  "review_reason": "Page has service description but also blog-style content sections"
}
```

**Step 2: Manual batch sampling**
Review 3 batches to catch systematic issues:
- Files 0001-0050 (first 50)
- Files 0550-0600 (middle 50)
- Files 1143-1193 (last 50)

Total: ~150 files (12.5% sample) for manual spot-check.

**Step 3: Iterate**
After first annotation batch, review flagged files + samples, refine prompt, continue.

---

## 7. DeepSeek Prompt Design (Draft)

```
You are annotating a web page for a content extraction benchmark. Analyze the HTML and provide structured annotations.

## Task
Extract the following from the page:

1. **Page Type**: Classify the page (article, product, collection, service, documentation, recipe, review, forum, directory, homepage, other)

2. **Metadata**: Title, author, publish date

3. **Main Content**: The primary text content (exclude navigation, ads, footers)

4. **Images**: List all images that are part of the main content (max 10):
   - Hero/featured image (if any)
   - In-content images (photos, diagrams, illustrations)
   - EXCLUDE: icons, logos, ads, decorative backgrounds, UI elements
   - For lazy-loaded images, use data-src or data-lazy-src for the real URL

5. **Snippets**:
   - 5 sentences that MUST be in any good extraction
   - 5 items that should NOT be extracted (boilerplate)

## Output Format
[JSON schema here]

## Examples
[2-3 annotated examples]
```

---

## 8. Open Questions

1. ~~**Image cap**: Should we limit to N images per page?~~ **DECIDED: Yes, cap at 10**
2. ~~**Link extraction**: Include links in benchmark?~~ **DECIDED: No - removed from scope**
3. ~~**Scoring weights**: Aggregate score?~~ **DECIDED: No aggregate - report text/images separately**
4. ~~**Schema migration**: How to handle existing v1 annotations?~~ **See 8.1**
5. ~~**Partial extractor support**: How to score extractors without image support?~~ **DECIDED: Test separately**
6. ~~**Snippet count**: Keep at 5 or reduce to 3?~~ **DECIDED: Keep 5 snippets**

### 8.1 Schema Versioning Strategy

**Problem**: Current v1 annotations have no `schema_version` field.

**Solution**:
```python
def get_schema_version(annotation: dict) -> str:
    # Explicit version field (v2+)
    if 'schema_version' in annotation:
        return annotation['schema_version']
    # v1 detection: has ground_truth but no images
    if 'ground_truth' in annotation and 'images' not in annotation.get('ground_truth', {}):
        return '1.0'
    return 'unknown'
```

**Migration**: v1 files will be overwritten during re-annotation. Backup first.

### 8.2 Snippet Count

**DECIDED**: Keep 5 snippets for both "with" and "without" - better signal for validation.

### 8.3 Confidence Criteria Definition

| Confidence | Criteria |
|------------|----------|
| `high` | Page clearly matches ONE type; multiple indicators present (URL pattern, content structure, metadata) |
| `medium` | Mostly matches one type but has 1-2 ambiguous elements (e.g., article with product CTA) |
| `low` | Could reasonably fit 2+ types equally well; set `needs_review: true` |

---

## 9. Success Criteria

- [ ] All 1,193 files re-annotated with v2 schema
- [ ] Schema validation passes on 100% of files
- [ ] rs-trafilatura wrapper supports image extraction
- [ ] Benchmark runs without errors
- [ ] Page type classification complete (internal use)
- [ ] Script to filter/export public dataset (strips _internal)
- [ ] Documentation updated

---

## 10. Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Schema & Infrastructure | 2-3 hours | None |
| Phase 2: Extractor Updates | 3-4 hours | Phase 1 |
| Phase 3: Annotation Pipeline | 2-3 hours | Phase 1 |
| Phase 4: Re-annotate Dataset | 6-8 hours (mostly waiting) | Phase 3 |
| Phase 5: Benchmark Updates | 2-3 hours | Phase 2, 4 |
| Phase 6: Documentation | 1-2 hours | Phase 5 |

**Total**: ~16-23 hours of work + API processing time

---

## Appendix A: Extractor Capabilities (VERIFIED 2026-01-02)

| Extractor | Text | Images | Benchmark Role |
|-----------|------|--------|----------------|
| Trafilatura (Python) | Yes | No | Text benchmark |
| Readability | Yes | No* | Text benchmark |
| Boilerpy3 | Yes | No | Text benchmark |
| BeautifulSoup | Yes | No | Text benchmark |
| **rs-trafilatura** | Yes | **Yes** | Full benchmark (text + images) |

*Readability preserves images in HTML output but requires custom parsing - we're not building post-processors.

### Why Other Packages Can't Extract Images

**Trafilatura (Python)**:
```python
result = bare_extraction(html, include_images=True)
result.image  # Returns ONLY og:image meta tag (1 URL)
result.images # Does NOT exist - no structured image data
```

**Readability**: Returns cleaned HTML, not structured data. Would need BeautifulSoup parsing.

**Boilerpy3**: Text-only by design.

### Benchmark Strategy

The image ground truth serves to:
1. **Evaluate rs-trafilatura** against known-good annotations
2. **Track regressions** as rs-trafilatura evolves
3. **Provide a public dataset** others can use to benchmark their own extractors

---

## Appendix B: Example Pages by Type

To be filled with 2-3 example file_ids for each page type after classification.
