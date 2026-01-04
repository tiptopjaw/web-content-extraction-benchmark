# Source Tree Analysis - rs-trafilatura

## Project Overview

**rs-trafilatura** is a Rust library for high-performance web content extraction. It ports the proven trafilatura algorithm (originally Python, then Go) to Rust.

```
rs-trafilatura/
├── Cargo.toml                 # Package manifest & dependencies
├── README.md                  # User-facing documentation
├── src/
│   ├── lib.rs                 # PUBLIC API ENTRY POINT
│   ├── extract.rs             # Main extraction orchestration (99KB)
│   ├── html_processing.rs     # HTML processing utilities
│   ├── dom.rs                 # DOM utilities
│   ├── encoding.rs            # Character encoding detection
│   ├── error.rs               # Error types
│   ├── etree.rs               # Element tree utilities
│   ├── link_density.rs        # Link density calculations
│   ├── lru.rs                 # LRU cache implementation
│   ├── options.rs             # Configuration options
│   ├── patterns.rs            # Regex patterns
│   ├── result.rs              # Result structures
│   ├── scoring.rs             # F-Score calculations
│   ├── url_utils.rs           # URL utilities
│   │
│   ├── extractor/             # Content extraction pipeline
│   │   ├── mod.rs             # Module exports
│   │   ├── pipeline.rs        # Extraction orchestration
│   │   ├── handlers.rs        # Text node processing
│   │   ├── pruning.rs         # Boilerplate removal
│   │   ├── fallback.rs        # Readability fallback
│   │   ├── state.rs           # Extraction state
│   │   ├── tags.rs            # Tag handling
│   │   └── comments.rs        # Comment extraction
│   │
│   ├── metadata/              # Metadata extraction
│   │   ├── mod.rs             # Module exports
│   │   ├── json_ld.rs         # JSON-LD parsing
│   │   ├── meta_tags.rs       # HTML meta tags (OG, DC)
│   │   └── dom_extraction.rs  # DOM-based extraction
│   │
│   ├── selector/              # CSS selectors for content/boilerplate
│   │   ├── mod.rs             # Module exports
│   │   ├── content.rs         # Content selectors
│   │   ├── discard.rs         # Discard/navigation selectors
│   │   ├── meta.rs            # Metadata selectors
│   │   ├── precision.rs       # Precision optimization
│   │   ├── utils.rs           # Selector utilities
│   │   └── comments.rs        # Comment selectors
│   │
│   └── bin/                   # CLI tools
│       ├── benchmark_extract.rs  # Benchmark extraction
│       ├── extract_stdin.rs      # Extract from stdin
│       └── extract_urls.rs       # Extract from URLs
│
├── tests/                     # Comprehensive test suite
│   ├── benchmark_suite/       # 983 HTML test files
│   ├── accuracy_test.rs       # Accuracy benchmarking
│   └── extraction_test.rs     # Extraction tests
│
├── examples/                  # Usage examples
├── benches/                   # Criterion benchmarks
├── scripts/                   # Build/eval scripts
└── docs/                      # Development documentation
```

## Critical Directories

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `src/lib.rs` | Public API | `extract()`, `extract_with_options()`, `extract_bytes()` |
| `src/extract.rs` | Core extraction | Main orchestration logic (99KB) |
| `src/extractor/` | Extraction pipeline | `pipeline.rs`, `handlers.rs`, `pruning.rs` |
| `src/metadata/` | Metadata extraction | `json_ld.rs`, `meta_tags.rs` |
| `src/selector/` | CSS selectors | Content/discard/precision selectors |

## Entry Points

| Entry Point | Type | Purpose |
|-------------|------|---------|
| `lib.rs` | Library | Public API for Rust consumers |
| `bin/benchmark_extract.rs` | Binary | CLI benchmark tool |
| `bin/extract_stdin.rs` | Binary | stdin input processing |
| `bin/extract_urls.rs` | Binary | URL-based extraction |

## Module Dependencies

```
lib.rs
├── extract.rs (main orchestrator)
│   ├── extractor/pipeline.rs
│   │   ├── handlers.rs
│   │   ├── pruning.rs
│   │   └── state.rs
│   ├── selector/* (CSS selectors)
│   ├── metadata/* (metadata extraction)
│   ├── html_processing.rs
│   ├── scoring.rs
│   └── url_utils.rs
├── options.rs (configuration)
└── result.rs (output structures)
```

## File Statistics

| Metric | Count |
|--------|-------|
| Total Rust files | 36 |
| Core library files | 13 |
| Extractor module | 8 |
| Metadata module | 4 |
| Selector module | 7 |
| Binary files | 3 |
| Test files | 30+ |

## Test Suite

- **Benchmark Suite**: 983 HTML test files in `tests/benchmark_suite/`
- **Accuracy Tests**: F-Score calculation against Python/Go implementations
- **Unit Tests**: Integration tests for extraction logic
