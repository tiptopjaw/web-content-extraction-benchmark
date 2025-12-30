# Methodology Comparison: ScrapingHub vs Our Approach

## ScrapingHub Article Extraction Benchmark

**Source**: https://github.com/scrapinghub/article-extraction-benchmark

### HTML Collection
- **Tool**: Splash headless browser
- **JavaScript**: Disabled during fetch
- **Storage**: Gzipped, UTF-8 encoded
- **Format**: Raw HTML with ALL tags intact (`<script>`, `<style>`, `<meta>`, etc.)
- **Example**: Full WSJ article with 100+ meta tags, stylesheets, scripts

### Ground Truth Format
```json
{
  "hash_id": {
    "articleBody": "The main article text content...",
    "url": "https://example.com/article"
  }
}
```

**Fields**:
- `articleBody`: Just the article text (no metadata)
- `url`: Source URL

**No additional fields for**:
- Title
- Author
- Publication date
- "Must include" test snippets
- "Must exclude" test snippets

### Annotation Process
- Not documented in repository
- Referenced in whitepaper (external)
- HTML used as-is (no preprocessing)

### Extractor Evaluation
- Extractors receive **raw HTML** (with all tags)
- Compare extracted text to `articleBody`
- Metrics: Precision, Recall, F1, Accuracy
- Bootstrap resampling for confidence intervals

---

## Our Current Approach (WRONG ❌)

### HTML Collection
- **Tool**: Python requests library
- **JavaScript**: Not executed (static download)
- **Storage**: UTF-8 encoded (not gzipped)
- **Format**: Raw HTML stored, BUT...

### Ground Truth Creation (THE PROBLEM)
```python
def clean_html_for_api(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # ❌ REMOVES script and style elements
    for tag in soup(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()

    # ❌ Sends CLEANED HTML to Deepseek
    return str(soup)
```

**What we sent to Deepseek**: Cleaned HTML without `<script>`, `<style>`, `<iframe>`, `<noscript>`

**What extractors will see**: Raw HTML WITH all those tags

**Result**: Ground truth created from different HTML than what extractors process ❌

### Ground Truth Format
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
    "without": ["Ad text", "Navigation item"]
  }
}
```

**Fields**: More comprehensive than ScrapingHub
- ✅ main_content (equivalent to articleBody)
- ✅ title, author, publish_date (extra metadata)
- ✅ "with" snippets (must include)
- ✅ "without" snippets (must exclude)

---

## Required Changes

### Fix 1: Filter Large Files (COMPLETED ✅)

**Created `scripts/filter_large_files.py`**:
- Filters out 117 files > 1MB (4.9% of dataset)
- New total: 2,287 files (was 2,404)
- Max size now 975KB (was 8.5MB)
- Allows sending full HTML without truncation

### Fix 2: Remove HTML Cleaning (COMPLETED ✅)

**Changed in `annotate_batch.py` and `annotate_remaining.py`**:

```python
# BEFORE (WRONG):
async def annotate_html(client, file_id, html_content, url, semaphore):
    cleaned_html = clean_html_for_api(html_content)  # ❌ DON'T CLEAN

# AFTER (CORRECT):
async def annotate_html(client, file_id, html_content, url, semaphore):
    # Send full raw HTML (no cleaning, no truncation)
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "..."},
            {"role": "user", "content": ANNOTATION_PROMPT + "\n\n" + html_content}
        ],
        ...
    )
```

### Fix 3: Update Prompt (COMPLETED ✅)

Added to prompt:

```
- The HTML contains <script>, <style>, and other tags - ignore these and focus on visible content
```

### Fix 4: Redo All Annotations

- Delete all 1,988 existing annotations
- Re-run batches 1-4 with filtered dataset and raw HTML
- Estimated cost: ~$1.92
- Estimated time: ~6 hours

---

## Key Differences We're Keeping (OK ✅)

1. **Extra metadata**: We extract title, author, date (ScrapingHub doesn't)
2. **Test snippets**: We have "with"/"without" snippets (ScrapingHub doesn't)
3. **Download method**: We use requests (they use Splash) - both work without JS

These differences are **acceptable enhancements** to the original benchmark.

The critical issue was the HTML cleaning - that must be fixed.

---

## Verification Checklist

Before re-annotating:

- [x] Filter dataset to remove files > 1MB
- [x] Remove `clean_html_for_api()` function calls
- [x] Remove truncation - send full raw HTML
- [x] Update prompt to mention HTML contains script/style tags
- [x] Update scripts to use filtered metadata files
- [ ] Test on 1 file to verify functionality
- [ ] Delete all existing annotations
- [ ] Re-run all batches with filtered dataset
- [ ] Verify extractors receive same HTML format as annotation

---

## Summary

**The Problem**:
We cleaned HTML before annotation but extractors see raw HTML = inconsistent

**The Solution**:
1. Filter out files > 1MB (117 files, 4.9% of dataset)
2. Send full raw HTML (no cleaning, no truncation) to Deepseek for annotation

**The Cost**:
~$1.92 and 6 hours to redo 2,287 annotations (filtered dataset)

**The Benefit**:
Methodology matches industry standard benchmark, results will be valid and publishable

**Dataset Impact**: 2,287 files (removed 117 large files to avoid truncation issues)
