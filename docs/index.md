# Project Documentation Index - rs-trafilatura

## Project Overview

**Type:** Library (single part)
**Primary Language:** Rust 2021 Edition
**Architecture:** Library/Module-based

### Quick Reference

- **Tech Stack:** Rust, dom_query, dom_smoothie, chrono, regex, serde
- **MSRV:** 1.85
- **Source Files:** 36 Rust files
- **Repository:** https://github.com/Murrough-Foley/rs-trafilatura

## Generated Documentation

### Core Documentation

- [Project Overview](./project-overview.md) - Executive summary and quick reference
- [Architecture](./architecture.md) - System architecture, data structures, API design
- [Source Tree Analysis](./source-tree-analysis.md) - Directory structure and file organization
- [Development Guide](./development-guide.md) - Setup, workflow, and contribution guidelines

### Research & Analysis

- [Research - Block Classification](./rs-trafilatura/docs/research-block-classification.md)
- [Research - Browser Automation in Rust](./rs-trafilatura/docs/research-browser-automation-rust.md)

### Planning Documents

- [Product Requirements](./rs-trafilatura/docs/prd.md)
- [Epics Overview](./rs-trafilatura/docs/epics.md)
- [Epic - HTML Cleaning Crate](./rs-trafilatura/docs/epic-html-cleaning-crate.md)
- [Epic - Release Process](./rs-trafilatura/docs/epic-release.md)

### Design Documents

- [Architecture (Original)](./rs-trafilatura/docs/architecture.md) - Detailed architectural decisions
- [HTML Cleaning API Design](./rs-trafilatura/docs/html-cleaning-api-design.md)
- [Implementation Differences](./rs-trafilatura/docs/differences.md)
- [Project Context (AI Agents)](./rs-trafilatura/docs/project_context.md)

### Reference

- [Known Issues & Future Fixes](./rs-trafilatura/docs/FUTURE_FIXES.md)

## Getting Started

### For Users

1. Start with: [Project Overview](./project-overview.md)
2. See: `README.md` at project root
3. Explore: `examples/` directory

### For Developers

1. Read: [Development Guide](./development-guide.md)
2. Study: [Architecture](./architecture.md)
3. Understand: [Source Tree](./source-tree-analysis.md)

### For AI Assistants

1. Read: [Project Context](./rs-trafilatura/docs/project_context.md)
2. Reference: [Architecture](./architecture.md)
3. Check: [Known Issues](./rs-trafilatura/docs/FUTURE_FIXES.md)

## File Statistics

| Category | Count | Location |
|----------|-------|----------|
| Source Files | 36 | `src/` |
| Test Files | 30+ | `tests/` |
| Existing Docs | 15 | `rs-trafilatura/docs/` |
| New Docs | 4 | `docs/` |

## Benchmarking

**Performance Metrics:**
- F-Score: 0.899 (on 983 benchmark pages)
- Precision: 0.897
- Recall: 0.938

Run benchmarks:
```bash
cargo run --release --example benchmark_extract
```

## Next Steps

1. Review the documentation above
2. For brownfield PRD: Use this index as context
3. For new features: Reference relevant architecture docs

---

*Generated: 2026-01-02 by BMAD Document Project Workflow*
