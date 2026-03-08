#!/usr/bin/env python3
"""
Sanitize HTML files for the benchmark.

Strips token-wasting content while preserving semantic structure:
- <script> tags and content
- <style> tags and content
- <svg> tags and content
- <!-- HTML comments -->
- <noscript> tags and content
- <iframe> tags
- data-* attributes
- on* event handler attributes

Keeps: All semantic HTML tags, class/id attributes, href/src attributes.

Output goes to benchmark/html-sanitized/ (originals untouched).

Usage:
    python scripts/sanitize_html.py
    python scripts/sanitize_html.py --dry-run
"""
import argparse
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
HTML_DIR = BASE_DIR / "benchmark" / "html"
OUT_DIR = BASE_DIR / "benchmark" / "html-sanitized"

# Tags to remove entirely (tag + content)
STRIP_TAGS = re.compile(
    r'<(script|style|svg|noscript|iframe)\b[^>]*>.*?</\1>',
    re.DOTALL | re.IGNORECASE
)

# Self-closing variants (e.g. <script src="..." />, <iframe ... />)
STRIP_SELF_CLOSING = re.compile(
    r'<(script|style|svg|noscript|iframe)\b[^>]*/\s*>',
    re.IGNORECASE
)

# Tags with no content (e.g. <script src="..."></script>)
STRIP_EMPTY = re.compile(
    r'<(script|style|svg|noscript|iframe)\b[^>]*>\s*</\1>',
    re.IGNORECASE
)

# HTML comments
STRIP_COMMENTS = re.compile(r'<!--.*?-->', re.DOTALL)

# data-* attributes
STRIP_DATA_ATTRS = re.compile(r'\s+data-[\w.-]+\s*=\s*(?:"[^"]*"|\'[^\']*\'|\S+)', re.IGNORECASE)

# on* event handler attributes (onclick, onload, onerror, etc.)
STRIP_EVENT_ATTRS = re.compile(r'\s+on\w+\s*=\s*(?:"[^"]*"|\'[^\']*\'|\S+)', re.IGNORECASE)

# Collapse runs of blank lines to max 2
COLLAPSE_BLANKS = re.compile(r'\n{3,}')


STRIP_UNCLOSED_COMMENTS = re.compile(r'<!--(?!.*-->).*', re.DOTALL)


def _strip_unclosed_tags(html: str) -> str:
    """Remove unclosed script/style/svg/noscript/iframe tags.

    Finds opens without matching closes and removes from the open tag
    to the next closing tag of any element, or EOF.
    """
    tags = ['script', 'style', 'svg', 'noscript', 'iframe']
    for tag in tags:
        while True:
            open_match = re.search(rf'<{tag}\b[^>]*>', html, re.IGNORECASE)
            if not open_match:
                break
            # Check for close tag (allow whitespace/newlines before >)
            close_match = re.search(rf'</{tag}[\s]*>', html[open_match.start():], re.IGNORECASE)
            if close_match:
                # Remove the whole matched pair
                cut_start = open_match.start()
                cut_end = open_match.start() + close_match.end()
                html = html[:cut_start] + html[cut_end:]
                continue
            # Unclosed — remove from open tag to next closing tag of any kind, or EOF
            rest = html[open_match.end():]
            end_match = re.search(r'</\w+[\s]*>', rest, re.IGNORECASE)
            if end_match:
                cut_end = open_match.end() + end_match.start()
            else:
                cut_end = len(html)
            html = html[:open_match.start()] + html[cut_end:]
    return html


def sanitize(html: str) -> str:
    # Remove tags with content (order matters: empty first, then full)
    html = STRIP_EMPTY.sub('', html)
    html = STRIP_TAGS.sub('', html)
    html = STRIP_SELF_CLOSING.sub('', html)
    html = _strip_unclosed_tags(html)
    html = STRIP_COMMENTS.sub('', html)
    html = STRIP_UNCLOSED_COMMENTS.sub('', html)
    html = STRIP_DATA_ATTRS.sub('', html)
    html = STRIP_EVENT_ATTRS.sub('', html)
    html = COLLAPSE_BLANKS.sub('\n\n', html)
    return html


def main():
    parser = argparse.ArgumentParser(description="Sanitize HTML files for benchmark")
    parser.add_argument("--dry-run", action="store_true", help="Show stats without writing")
    args = parser.parse_args()

    html_files = sorted(HTML_DIR.glob("*.html"))
    if not html_files:
        print(f"No HTML files found in {HTML_DIR}")
        sys.exit(1)

    if not args.dry_run:
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_before = 0
    total_after = 0

    for i, f in enumerate(html_files):
        raw = f.read_text(encoding="utf-8", errors="replace")
        cleaned = sanitize(raw)

        before = len(raw)
        after = len(cleaned)
        total_before += before
        total_after += after
        reduction = (1 - after / before) * 100 if before else 0

        if not args.dry_run:
            (OUT_DIR / f.name).write_text(cleaned, encoding="utf-8")

        if (i + 1) % 100 == 0 or i == len(html_files) - 1:
            print(f"  [{i+1}/{len(html_files)}] processed")

    reduction_pct = (1 - total_after / total_before) * 100 if total_before else 0
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Results:")
    print(f"  Files:      {len(html_files)}")
    print(f"  Before:     {total_before // 1024 // 1024} MB")
    print(f"  After:      {total_after // 1024 // 1024} MB")
    print(f"  Reduction:  {reduction_pct:.1f}%")
    if not args.dry_run:
        print(f"  Output:     {OUT_DIR}")


if __name__ == "__main__":
    main()
