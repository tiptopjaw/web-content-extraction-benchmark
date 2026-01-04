# Development Guide - rs-trafilatura

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Rust | 1.85+ | Compiler (MSRV: Minimum Supported Rust Version) |
| Cargo | Latest | Build tool and package manager |
| Git | Any | Version control |

### Installation

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version  # Should be 1.85 or higher
cargo --version
```

## Setup

### Clone and Build

```bash
# Clone the repository
git clone https://github.com/Murrough-Foley/rs-trafilatura.git
cd rs-trafilatura

# Build in debug mode
cargo build

# Build in release mode (optimized)
cargo build --release

# Run tests
cargo test

# Run benchmarks
cargo bench
```

### Running Examples

```bash
# Basic extraction demo
cargo run --example basic

# Run extraction benchmark
cargo run --release --example benchmark_extract
```

## Project Structure

```
rs-trafilatura/
├── src/
│   ├── lib.rs           # Public API
│   ├── extract.rs       # Main extraction logic
│   ├── extractor/       # Extraction pipeline
│   ├── metadata/        # Metadata extraction
│   └── selector/        # CSS selectors
├── examples/            # Usage examples
├── tests/               # Test suite
│   ├── benchmark_suite/ # 983 HTML test files
│   └── *.rs             # Test modules
├── benches/             # Criterion benchmarks
├── scripts/             # Utility scripts
└── Cargo.toml           # Package manifest
```

## Development Workflow

### 1. Code Style

The project uses strict linting:

```bash
# Check code without building
cargo check

# Run clippy for linting suggestions
cargo clippy

# Format code
cargo fmt
```

**Lint Configuration** (from Cargo.toml):
- `unsafe_code = "forbid"` - No unsafe code allowed
- `unwrap_used = "deny"` - Production code must handle errors
- `expect_used = "deny"` - No expect() in production

### 2. Testing

```bash
# Run all tests
cargo test

# Run specific test
cargo test extraction_test

# Run tests with output
cargo test -- --nocapture

# Run accuracy benchmark
cargo test accuracy_test
```

### 3. Benchmarking

```bash
# Run criterion benchmarks
cargo bench

# Run benchmark_extract binary
cargo run --release --bin benchmark_extract
```

### 4. Adding Dependencies

Edit `Cargo.toml`:

```toml
[dependencies]
new_dependency = "version"

[dev-dependencies]
new_dev_dependency = "version"
```

Then run:
```bash
cargo update
cargo build
```

## Key Development Concepts

### Extraction Pipeline

1. **HTML Input** → Parse with `dom_query`
2. **Text Node Collection** → Find all text-bearing nodes
3. **Handler Processing** → Process via `handlers.rs`
4. **Boilerplate Pruning** → Remove non-content via `pruning.rs`
5. **Scoring** → Calculate content scores via `scoring.rs`
6. **Metadata Extraction** → Extract via `metadata/`
7. **Output** → Return `ExtractResult`

### Selector System

The `selector/` module contains CSS selectors for:

| Type | Purpose | Files |
|------|---------|-------|
| Content | Identify main content | `content.rs` |
| Discard | Identify boilerplate | `discard.rs` |
| Metadata | Extract meta info | `meta.rs` |
| Precision | Optimize accuracy | `precision.rs` |

### Feature Flags

```toml
[features]
default = ["readability"]  # Enable Readability fallback
readability = ["dep:dom_smoothie"]  # Optional dependency
```

To build without Readability fallback:
```bash
cargo build --no-default-features
```

## Debugging

### Logging

The library doesn't use external logging. Add print statements for debugging:

```rust
println!("Debug: {:?}", some_value);
```

### Common Issues

1. **F-Score below 0.90**: Run accuracy tests to identify gaps
2. **Clippy warnings**: Address before committing
3. **Test failures**: Check `tests/benchmark_suite/` for ground truth files

## Building Documentation

```bash
# Generate Rustdoc
cargo doc --no-deps

# View docs locally
cargo doc --open --no-deps
```

## Release Process

### Pre-release Checklist

- [ ] All tests pass (`cargo test`)
- [ ] F-Score ≥ 0.90 (`cargo test accuracy_test`)
- [ ] No clippy warnings (`cargo clippy`)
- [ ] Code formatted (`cargo fmt --check`)
- [ ] Documentation updated

### Release Steps

```bash
# Update version in Cargo.toml
# Commit changes
git add -A
git commit -m "Release v0.1.X"
git tag v0.1.X

# Build release
cargo build --release

# Publish to crates.io
cargo publish
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all checks pass
5. Submit PR

## Performance Tuning

### Profiling

```bash
# Profile with perf (Linux)
perf record --call-graph dwarf cargo test
perf report
```

### Memory Analysis

```bash
# Check memory usage
valgrind --tool=massif cargo run --example basic
```

## Additional Resources

- **Architecture**: See `docs/architecture.md`
- **API Reference**: See `docs/html-cleaning-api-design.md`
- **Research**: See `docs/research-*.md`
- **Issues**: See `docs/issues/`
