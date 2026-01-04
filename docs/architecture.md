# Architecture Documentation - rs-trafilatura

## Executive Summary

**rs-trafilatura** is a high-performance Rust library for web content extraction. It provides clean, readable content from web pages by removing boilerplate, navigation, ads, and page chrome while preserving meaningful text and metadata.

### Key Metrics

| Metric | Value |
|--------|-------|
| F-Score | 0.899 (on 983 benchmark pages) |
| Precision | 0.897 |
| Recall | 0.938 |
| Language | Rust 2021 Edition |
| MSRV | 1.85 |
| Code Size | ~36 Rust source files |

## Technology Stack

### Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `dom_query` | 0.24 | DOM manipulation with CSS selectors |
| `dom_smoothie` | 0.14 (optional) | Mozilla Readability fallback |
| `html-cleaning` | git | HTML sanitization utilities |
| `regex` | 1.11 | Pattern matching |
| `chrono` | 0.4 | Date parsing |
| `encoding_rs` | 0.8 | Character encoding detection |
| `serde` + `serde_json` | 1.0 | JSON-LD parsing |
| `url` | 2.5 | URL handling |
| `thiserror` | 2.0 | Error handling |

### Development Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `criterion` | 0.5 | Benchmarking |
| `flate2` | 1.0 | Compression for tests |

## Architecture Pattern

### Library Module Structure

The library follows a **modular architecture** with three primary modules:

```
rs-trafilatura
├── lib.rs (Public API)
├── extract.rs (Orchestration)
├── extractor/ (Extraction Pipeline)
├── metadata/ (Metadata Extraction)
└── selector/ (CSS Selectors)
```

### Module Responsibilities

#### 1. Extractor Module (`src/extractor/`)

Handles the core content extraction pipeline:

| File | Responsibility |
|------|----------------|
| `pipeline.rs` | Orchestrates the extraction process |
| `handlers.rs` | Processes text nodes |
| `pruning.rs` | Removes boilerplate content |
| `fallback.rs` | Mozilla Readability fallback |
| `state.rs` | Manages extraction state |
| `tags.rs` | Tag handling |
| `comments.rs` | Comment extraction |

**Pipeline Flow:**
```
HTML Input
    ↓
DOM Parsing (dom_query)
    ↓
Initial Text Node Collection
    ↓
Handler Processing
    ↓
Boilerplate Pruning
    ↓
Content Scoring
    ↓
Metadata Extraction
    ↓
Output Generation
```

#### 2. Metadata Module (`src/metadata/`)

Extracts metadata from multiple sources:

| File | Responsibility |
|------|----------------|
| `json_ld.rs` | JSON-LD structured data parsing |
| `meta_tags.rs` | HTML meta tags (Open Graph, Dublin Core) |
| `dom_extraction.rs` | DOM-based title/author/date extraction |

#### 3. Selector Module (`src/selector/`)

CSS selectors for content/discard classification:

| File | Responsibility |
|------|----------------|
| `content.rs` | Selectors for main content areas |
| `discard.rs` | Selectors for boilerplate (nav, footer, etc.) |
| `meta.rs` | Selectors for metadata extraction |
| `precision.rs` | Precision optimization selectors |
| `utils.rs` | Selector utilities |

## Data Architecture

### ExtractResult Structure

```rust
pub struct ExtractResult {
    pub content_text: String,           // Main content as plain text
    pub content_html: Option<String>,   // Main content as HTML
    pub comments_text: Option<String>,  // Comments as text
    pub comments_html: Option<String>,  // Comments as HTML
    pub metadata: Metadata,             // Extracted metadata
    pub images: Vec<String>,            // Image URLs
}

pub struct Metadata {
    pub title: Option<String>,
    pub author: Option<String>,
    pub date: Option<String>,
    pub description: Option<String>,
    pub sitename: Option<String>,
    pub url: Option<String>,
    pub hostname: Option<String>,
    pub image: Option<String>,
    pub language: Option<String>,
    pub categories: Vec<String>,
    pub tags: Vec<String>,
    pub license: Option<String>,
    pub page_type: Option<String>,
}
```

### Options Configuration

```rust
pub struct Options {
    pub include_comments: bool,
    pub include_tables: bool,
    pub include_images: bool,
    pub include_links: bool,
    pub favor_precision: bool,  // Stricter filtering
    pub favor_recall: bool,     // More inclusive
    pub url: Option<String>,
    pub author_blacklist: Option<Vec<String>>,
    // ... 20+ options
}
```

## API Design

### Public API (lib.rs)

```rust
// Basic extraction
pub fn extract(html: &str) -> Result<ExtractResult>

// With options
pub fn extract_with_options(html: &str, options: &Options) -> Result<ExtractResult>

// From bytes (with encoding detection)
pub fn extract_bytes(html: &[8]) -> Result<ExtractResult>
```

### Feature Flags

- `readability` (default): Enables Mozilla Readability fallback via `dom_smoothie`

## Performance Characteristics

### Benchmark Results

| Implementation | Precision | Recall | F1 Score |
|----------------|-----------|--------|----------|
| **rs-trafilatura (Rust)** | 0.897 | 0.938 | **0.899** |
| trafilatura (Python) | 0.907 | 0.921 | 0.897 |
| go-trafilatura (Go) | 0.898 | 0.924 | 0.896 |

### Optimization Strategies

1. **Compile-time regex**: Patterns compiled at build time
2. **LRU caching**: Link density calculations cached
3. **DOM query optimization**: Efficient CSS selector usage
4. **Single-pass processing**: Minimize DOM traversals

## Error Handling

The library uses `thiserror` for type-safe error handling:

```rust
#[error("Extraction error: {0}")]
pub struct ExtractionError(String);
```

No panics on malformed HTML - graceful error handling throughout.

## Configuration

### Cargo Feature Flags

```toml
[features]
default = ["readability"]  # Enable Readability fallback
readability = ["dep:dom_smoothie"]
```

### Rust Lint Configuration

- `unsafe_code = "forbid"` - No unsafe code allowed
- `unwrap_used = "deny"` - Prevents unwrap() in production
- `expect_used = "deny"` - Prevents expect() in production

## Quality Assurance

### Test Coverage

- **983 benchmark pages** for accuracy testing
- **30+ test files** covering extraction scenarios
- **F-Score validation** against Python/Go implementations
- **CI/CD** via GitHub Actions (`.github/workflows/ci.yml`)

### Release Requirements

- F-Score ≥ 0.90 before release
- All tests passing
- No clippy warnings (pedantic level)

## Future Enhancements

See `docs/FUTURE_FIXES.md` for known accuracy gaps and planned improvements:

- Markdown output option
- Link preservation feature flags
- `html-cleaning` crate extraction
