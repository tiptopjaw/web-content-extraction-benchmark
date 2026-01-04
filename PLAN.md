# RS-Trafilatura Accuracy Improvement Plan

## Problem Summary
RS-trafilatura gets accuracy=0.0 on 22 files where go-trafilatura gets 1.0. The accuracy metric uses exact token matching, so even one extra token breaks the match.

## Root Cause Analysis
RS is extracting unwanted metadata as part of the article body:
- **Article Headlines (54.5%)** - 12 files include title in body
- **Author Bylines (9.1%)** - 2 files include "By Reuters", "Staff Reports"
- **Publication Metadata** - Timestamps, source attribution
- **Photo Credits (4.5%)** - Image attribution lines

## Implementation Phases

### Phase 1: Enhanced Boilerplate Class Detection (LOW RISK)
**File:** `rs-trafilatura/src/patterns.rs`

Add to `BOILERPLATE_CLASS` regex:
```
|photo[-_]?credit|img[-_]?credit|image[-_]?credit|\bcredit\b|source[-_]?attribution
```

These patterns match photo credit containers that go-trafilatura filters.

### Phase 2: Photo Credit Text Detection (LOW RISK)
**File:** `rs-trafilatura/src/html_processing.rs`

Add to `is_share_button_text()`:
```rust
// Photo credit patterns - "Name | Source | Getty Images" format
if trimmed.len() < 100 {
    let lower = trimmed.to_lowercase();
    let agencies = ["getty", "reuters", "bloomberg", "afp", "shutterstock",
                   "ap photo", "photo by", "image by", "credit:"];
    for agency in agencies {
        if lower.contains(agency) {
            return true;
        }
    }
}

// "Photo:" or "Credit:" prefix
if lower.starts_with("photo:") || lower.starts_with("credit:")
    || lower.starts_with("photo by") || lower.starts_with("image by") {
    return true;
}
```

### Phase 3: Byline and Publication Metadata Detection (MEDIUM RISK)
**File:** `rs-trafilatura/src/html_processing.rs`

Add to `is_share_button_text()`:
```rust
// News agency attribution - standalone or with location
let agencies = ["reuters", "pti", "afp", "associated press", "staff reports",
               "ians", "ani", "xinhua", "dpa", "panarmenia"];
for agency in agencies {
    if lower.starts_with(agency) && trimmed.len() < 80 {
        return true;
    }
}

// "By [Author]" byline pattern - only short text
if lower.starts_with("by ") && trimmed.len() < 60 {
    let after_by = &trimmed[3..];
    // Check for capitalized author name, not sentence continuation
    if after_by.chars().next().map_or(false, |c| c.is_uppercase())
        && !after_by.contains(". ") {
        return true;
    }
}

// Timestamp patterns - "Updated:" "Published:" prefixes
if (lower.starts_with("updated:") || lower.starts_with("published:")
    || lower.starts_with("last updated")) && trimmed.len() < 100 {
    return true;
}
```

### Phase 4: Headline Class-Based Filtering (MEDIUM RISK)
**File:** `rs-trafilatura/src/extract.rs`

Enhance heading filtering in `extract_filtered_text_inner()` around line 1497:
```rust
if is_heading {
    let heading_sel = Selection::from(node);
    let heading_text = etree::iter_text(&heading_sel, " ");
    let heading_text_trimmed = heading_text.trim();

    // Existing: Skip headings with boilerplate patterns
    if html_processing::is_share_button_text(heading_text_trimmed) {
        skip_depths.push(depth);
        continue;
    }

    // NEW: Check if heading has title/headline class markers
    if let Some(class) = dom::get_attribute(&heading_sel, "class") {
        let class_lower = class.to_ascii_lowercase();
        if class_lower.contains("entry-title")
            || class_lower.contains("post-title")
            || class_lower.contains("article-title")
            || class_lower.contains("pg-headline") {
            skip_depths.push(depth);
            continue;
        }
    }

    // NEW: Check itemprop="headline" attribute
    if let Some(itemprop) = dom::get_attribute(&heading_sel, "itemprop") {
        if itemprop.to_ascii_lowercase() == "headline" {
            skip_depths.push(depth);
            continue;
        }
    }
}
```

## Testing Strategy
1. Run benchmark after each phase
2. Track accuracy, F1, precision, recall changes
3. Monitor for regressions in other files
4. Focus on the 22 problem files

## Expected Outcome
- Phase 1-2: +2-3% accuracy (photo credits, class patterns)
- Phase 3: +3-5% accuracy (bylines, metadata)
- Phase 4: +5-10% accuracy (headline filtering)
- Target: Close gap from 0.044 to <0.02
