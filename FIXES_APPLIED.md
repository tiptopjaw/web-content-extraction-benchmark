# Annotation Methodology Fixes Applied

## Problem Identified

**Critical Issue**: All 1,988 existing annotations were created from cleaned HTML (with `<script>`, `<style>`, `<iframe>`, and `<noscript>` tags removed), but extractors would process raw HTML. This violates the fundamental principle that ground truth and extraction must use identical input.

**Root Cause**: Both `annotate_batch.py` and `annotate_remaining.py` used a `clean_html_for_api()` function that removed tags via BeautifulSoup before sending to Deepseek API.

## Fixes Applied

### 1. Filtered Large Files

**Created**: `scripts/filter_large_files.py`

**What it does**:
- Filters out 117 files > 1MB from dataset (4.9% of total)
- Creates `metadata_subset_filtered.csv` (1,899 files, was 2,000)
- Creates `metadata_remaining_filtered.csv` (388 files, was 404)
- **New total: 2,287 files** (down from 2,404)

**Result**:
- Max file size now 975KB (was 8.5MB)
- Average size: 226KB
- No truncation needed - can send full HTML

### 2. Fixed `scripts/annotate_batch.py`

**Changes**:
- Removed `BeautifulSoup` import (no longer needed)
- **Removed all truncation** - sends full raw HTML
- Updated to use `metadata_subset_filtered.csv`
- Updated prompt to mention HTML contains `<script>` and `<style>` tags

**Before (WRONG)**:
```python
from bs4 import BeautifulSoup

def clean_html_for_api(html_content, max_chars=100000):
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for tag in soup(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()
    cleaned = str(soup)
    # Truncate if too long
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n\n[... HTML truncated ...]"
    return cleaned

# In annotate_html():
cleaned_html = clean_html_for_api(html_content)
```

**After (CORRECT)**:
```python
# No BeautifulSoup import, no truncation function

# In annotate_html():
# Send full raw HTML (no cleaning, no truncation)
# Matches ScrapingHub methodology exactly
response = await client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": ANNOTATION_PROMPT + "\n\n" + html_content}
    ],
    temperature=0.3,
    max_tokens=4000
)
```

### 3. Fixed `scripts/annotate_remaining.py`

**Changes**: Identical fixes as `annotate_batch.py` above.
- Updated to use `metadata_remaining_filtered.csv`
- No truncation - sends full raw HTML

### 4. Created `scripts/test_annotation.py`

**Purpose**: Test annotation on a single file to verify:
- Raw HTML is sent to API (no cleaning, no truncation)
- Script/style tags are preserved
- Annotation quality is good

**Usage**:
```bash
python scripts/test_annotation.py --api-key YOUR_KEY --file-id 1
```

**Output**:
- Verifies script/style tags present in original HTML
- Confirms tags still present in HTML sent to API
- Shows annotation results (title, author, date, content length)
- Saves test annotation to `data/test_annotation.json`

### 5. Created `scripts/reset_annotations.py`

**Purpose**: Backup and delete all existing annotations to prepare for re-annotation.

**What it does**:
- Backs up all annotation directories with timestamp:
  - `ground_truth/` (1,988 files)
  - `ground_truth_clean/` (1,193 files)
  - `ground_truth_merged/` (if exists)
  - `ground_truth_removed/` (if exists)
- Deletes all annotation directories
- Recreates empty `ground_truth/` directory
- Saves backup to `data/annotations_backup_YYYYMMDD_HHMMSS/`

**Usage**:
```bash
python scripts/reset_annotations.py
# Prompts for confirmation before proceeding
```

## Verification

### Methodology Now Matches ScrapingHub

| Aspect | ScrapingHub | Our Approach (Before) | Our Approach (After) |
|--------|-------------|----------------------|---------------------|
| HTML Collection | Splash headless browser | Python requests | Python requests ✅ |
| JavaScript | Disabled | Not executed | Not executed ✅ |
| HTML Storage | Raw with all tags | Raw with all tags | Raw with all tags ✅ |
| HTML for Annotation | **Raw with all tags** | **❌ Cleaned (removed tags)** | **✅ Raw with all tags (no truncation)** |
| HTML for Extraction | Raw with all tags | Raw with all tags | Raw with all tags ✅ |
| File Size Filtering | Not documented | None | Exclude files > 1MB ✅ |
| Ground Truth Format | `articleBody` + `url` | Enhanced with metadata | Enhanced with metadata ✅ |

**Key Fix**: Annotation now uses raw HTML, matching what extractors will receive.

### Checklist Status

- [x] Filter files > 1MB from dataset
- [x] Remove `clean_html_for_api()` function calls
- [x] Remove truncation - send full raw HTML
- [x] Update prompt to mention HTML contains script/style tags
- [x] Create test script for verification
- [x] Create reset script for cleanup
- [ ] **Test on 1 file to verify functionality**
- [ ] **Delete all existing annotations**
- [ ] **Re-run all batches**
- [ ] Verify extractors receive same HTML format as annotation

## Next Steps

### 1. Test Single File

```bash
python scripts/test_annotation.py --api-key YOUR_KEY --file-id 1
```

**Expected**:
- Verification passes (script/style tags preserved)
- Annotation completes successfully
- Output saved to `data/test_annotation.json`

### 2. Reset Annotations

```bash
python scripts/reset_annotations.py
```

**Result**:
- All 1,988 existing annotations backed up
- Directories cleared
- Ready for fresh annotation

### 3. Re-annotate Batches 1-4

**Note**: Now using filtered dataset (1,899 files instead of 2,000)

```bash
# Batch 1 (files 1-500, ~475 after filtering)
python scripts/annotate_batch.py --api-key YOUR_KEY --batch 1

# Batch 2 (files 501-1000, ~475 after filtering)
python scripts/annotate_batch.py --api-key YOUR_KEY --batch 2

# Batch 3 (files 1001-1500, ~475 after filtering)
python scripts/annotate_batch.py --api-key YOUR_KEY --batch 3

# Batch 4 (files 1501-2000, ~474 after filtering)
python scripts/annotate_batch.py --api-key YOUR_KEY --batch 4
```

**Cost Estimate**:
- 1,899 files × ~2,000 tokens/file = ~3.8M tokens
- Input: 3.8M tokens × $0.14/1M = $0.53
- Output: 3.8M tokens × $0.28/1M = $1.06
- **Total: ~$1.59 for all 4 batches**

**Time Estimate**: ~5.5 hours total

### 4. Optional: Annotate Remaining 388 Files

**Note**: Now using filtered dataset (388 files instead of 404)

```bash
python scripts/annotate_remaining.py --api-key YOUR_KEY
```

**Cost**: ~$0.33
**Time**: ~40 minutes

### 5. Quality Filter and Merge

```bash
python scripts/merge_new_annotations.py
```

**Expected Output**: ~1,150-1,500 high-quality annotations

## Cost Summary

| Task | Files | Tokens | Cost | Time |
|------|-------|--------|------|------|
| Batches 1-4 (redo) | 1,899 | ~3.8M | ~$1.59 | ~5.5 hours |
| Remaining 388 files | 388 | ~776K | ~$0.33 | ~40 min |
| **Total** | **2,287** | **~4.6M** | **~$1.92** | **~6 hours** |

**Dataset size**: 2,287 files (filtered out 117 files > 1MB)

## Files Modified

1. `scripts/annotate_batch.py` - Removed HTML cleaning and truncation, uses filtered metadata
2. `scripts/annotate_remaining.py` - Removed HTML cleaning and truncation, uses filtered metadata
3. `scripts/test_annotation.py` - Removed truncation, uses filtered metadata
4. `METHODOLOGY_COMPARISON.md` - Updated checklist
5. `FIXES_APPLIED.md` - This document

## Files Created

1. `scripts/filter_large_files.py` - Filter files > 1MB
2. `data/metadata_subset_filtered.csv` - Filtered subset (1,899 files)
3. `data/metadata_remaining_filtered.csv` - Filtered remaining (388 files)
4. `scripts/test_annotation.py` - Single file test
5. `scripts/reset_annotations.py` - Backup and cleanup

## Validation

Once re-annotation is complete:

1. Check annotation quality on random samples
2. Verify extractors receive same HTML format
3. Run benchmark on subset to ensure valid results
4. Document results and compare with original ScrapingHub benchmark

## References

- Original benchmark: https://github.com/scrapinghub/article-extraction-benchmark
- Methodology comparison: `METHODOLOGY_COMPARISON.md`
- Project README: `README.md`
