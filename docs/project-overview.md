# Project Overview - rs-trafilatura

## Executive Summary

**rs-trafilatura** is a high-performance Rust library for web content extraction. It ports the proven trafilatura algorithm (originally Python, then Go) to Rust, providing clean, readable content from web pages.

### What It Does

- Extracts main content from HTML pages
- Removes boilerplate (navigation, ads, footer, sidebar)
- Preserves meaningful text and structure
- Extracts rich metadata (title, author, date, etc.)
- Handles character encoding automatically

### Key Achievement

**F-Score of 0.899** on benchmark suite (983 pages), matching Python and Go implementations.

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Type** | Rust Library |
| **Language** | Rust 2021 Edition |
| **MSRV** | 1.85 |
| **Repository** | monolith |
| **License** | MIT OR Apache-2.0 |
| **Repository** | https://github.com/Murrough-Foley/rs-trafilatura |

## Technology Stack

| Category | Technology |
|----------|------------|
| Core Language | Rust |
| DOM Parsing | dom_query 0.24 |
| Readability Fallback | dom_smoothie 0.14 (optional) |
| HTML Cleaning | html-cleaning (git) |
| Pattern Matching | regex 1.11 |
| Date Handling | chrono 0.4 |
| Encoding | encoding_rs 0.8 |
| Serialization | serde + serde_json |
| URL Handling | url 2.5 |

## Architecture Type

**Library/Module-based** with modular sub-crates:
- `extractor/` - Content extraction pipeline
- `metadata/` - Metadata extraction
- `selector/` - CSS content/boilerplate selectors

## Repository Structure

```
rs-trafilatura/
├── src/
│   ├── lib.rs              # Public API
│   ├── extract.rs          # Main orchestration (99KB)
│   ├── extractor/          # Extraction pipeline
│   ├── metadata/           # Metadata extraction
│   └── selector/           # CSS selectors
├── tests/
│   ├── benchmark_suite/    # 983 test HTML files
│   └── *.rs                # Test modules
├── examples/               # Usage examples
├── benches/                # Criterion benchmarks
└── docs/                   # Documentation
```

## Performance Metrics

| Metric | rs-trafilatura (Rust) | Python | Go |
|--------|----------------------|--------|-----|
| **Precision** | 0.897 | **0.907** | 0.898 |
| **Recall** | **0.938** | 0.921 | 0.924 |
| **F1-Score** | **0.899** | 0.897 | 0.896 |

## Usage Example

```rust
use rs_trafilatura::extract;

let html = r#"<html>..."#;
let result = extract(html)?;

println!("Title: {:?}", result.metadata.title);
println!("Content: {}", result.content_text);
```

## Feature Flags

| Feature | Default | Description |
|---------|---------|-------------|
| `readability` | Yes | Mozilla Readability fallback |

## Getting Started

1. **For Users**: See `README.md` and `examples/`
2. **For Developers**: See `docs/development-guide.md`
3. **For Contributors**: See `docs/project_context.md`

## Documentation Index

- [Architecture](./architecture.md) - System architecture
- [Development Guide](./development-guide.md) - Setup and workflow
- [Source Tree](./source-tree-analysis.md) - File structure
- [Research - Block Classification](./research-block-classification.md)
- [Research - Browser Automation](./research-browser-automation-rust.md)
- [PRD](./prd.md) - Product requirements

## Benchmarking

Run the accuracy benchmark:
```bash
cargo run --release --example benchmark_extract
```

## Quality Standards

- F-Score ≥ 0.90 required before release
- No unsafe code allowed
- No `unwrap()` or `expect()` in production
- All clippy warnings addressed (pedantic level)

## Links

- **Repository**: https://github.com/Murrough-Foley/rs-trafilatura
- **Original Python**: https://github.com/adbar/trafilatura
- **Go Port**: https://github.com/markusmobius/go-trafilatura
