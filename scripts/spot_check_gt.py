#!/usr/bin/env python3
"""Spot-check all GT files for common issues that may have slipped through."""

import json
import os
import re
import gzip
from pathlib import Path

GT_DIR = Path("benchmark/ground-truth")
HTML_DIR = Path("benchmark/html")

# Thresholds
SHORT_CONTENT_CHARS = 1500
LOW_WITH_SNIPPETS = 2
HTML_TO_GT_RATIO = 15  # If HTML is 15x+ larger than GT, flag it

# Encoding artifact patterns
ENCODING_ARTIFACTS = re.compile(r'â€™|â€"|â€œ|â€\x9d|Ã©|Ã¨|Ã¼|Ã¶|Ã¤|Â |â€¢|â€"')
HTML_TAG_PATTERN = re.compile(r'<(?:div|span|p|a|img|br|ul|ol|li|h[1-6]|table|tr|td|th|strong|em|b|i|script|style|link|meta)\b[^>]*>', re.IGNORECASE)

results = {
    "short_content": [],
    "low_with_snippets": [],
    "empty_without": [],
    "high_html_ratio": [],
    "encoding_artifacts": [],
    "html_tags": [],
    "with_not_in_content": [],
    "without_in_content": [],
}

gt_files = sorted(GT_DIR.glob("*.json"))
print(f"Scanning {len(gt_files)} GT files...\n")

for gt_path in gt_files:
    file_id = gt_path.stem

    with open(gt_path) as f:
        data = json.load(f)

    gt = data.get("ground_truth", {})
    content = gt.get("main_content", "")
    with_snippets = gt.get("with", [])
    without_snippets = gt.get("without", [])

    content_len = len(content)

    # 1. Short content
    if content_len < SHORT_CONTENT_CHARS:
        results["short_content"].append((file_id, content_len))

    # 2. Low with-snippets
    if len(with_snippets) < LOW_WITH_SNIPPETS:
        results["low_with_snippets"].append((file_id, len(with_snippets)))

    # 3. Empty without
    if len(without_snippets) == 0:
        results["empty_without"].append(file_id)

    # 4. HTML to GT ratio
    html_path = HTML_DIR / f"{file_id}.html"
    html_gz_path = HTML_DIR / f"{file_id}.html.gz"
    html_size = 0
    if html_path.exists():
        html_size = html_path.stat().st_size
    elif html_gz_path.exists():
        html_size = html_gz_path.stat().st_size * 3  # rough estimate

    if html_size > 0 and content_len > 0:
        ratio = html_size / content_len
        if ratio > HTML_TO_GT_RATIO:
            results["high_html_ratio"].append((file_id, f"{ratio:.1f}x", content_len, html_size))

    # 5. Encoding artifacts
    artifacts = ENCODING_ARTIFACTS.findall(content)
    if artifacts:
        results["encoding_artifacts"].append((file_id, artifacts[:3]))

    # 6. HTML tags in content
    tags = HTML_TAG_PATTERN.findall(content)
    if tags:
        results["html_tags"].append((file_id, tags[:3]))

    # 7. With-snippets not in content
    bad_with = [s[:60] for s in with_snippets if s not in content]
    if bad_with:
        results["with_not_in_content"].append((file_id, bad_with))

    # 8. Without-snippets in content
    bad_without = [s[:60] for s in without_snippets if s in content]
    if bad_without:
        results["without_in_content"].append((file_id, bad_without))

# Print report
print("=" * 80)
print("SPOT CHECK REPORT")
print("=" * 80)

print(f"\n### Short content (<{SHORT_CONTENT_CHARS} chars): {len(results['short_content'])} files")
for fid, clen in sorted(results["short_content"], key=lambda x: x[1]):
    print(f"  [{fid}] {clen} chars")

print(f"\n### Low with-snippets (<{LOW_WITH_SNIPPETS}): {len(results['low_with_snippets'])} files")
for fid, count in results["low_with_snippets"]:
    print(f"  [{fid}] {count} snippets")

print(f"\n### Empty without array: {len(results['empty_without'])} files")
for fid in results["empty_without"]:
    print(f"  [{fid}]")

print(f"\n### High HTML/GT ratio (>{HTML_TO_GT_RATIO}x): {len(results['high_html_ratio'])} files")
for fid, ratio, gt_len, html_len in sorted(results["high_html_ratio"], key=lambda x: float(x[1].rstrip('x')), reverse=True)[:30]:
    print(f"  [{fid}] ratio={ratio}, GT={gt_len} chars, HTML={html_len} bytes")
if len(results["high_html_ratio"]) > 30:
    print(f"  ... and {len(results['high_html_ratio']) - 30} more")

print(f"\n### Encoding artifacts: {len(results['encoding_artifacts'])} files")
for fid, arts in results["encoding_artifacts"]:
    print(f"  [{fid}] {arts}")

print(f"\n### HTML tags in content: {len(results['html_tags'])} files")
for fid, tags in results["html_tags"]:
    print(f"  [{fid}] {tags}")

print(f"\n### With-snippets NOT in content: {len(results['with_not_in_content'])} files")
for fid, snips in results["with_not_in_content"]:
    print(f"  [{fid}] {snips}")

print(f"\n### Without-snippets IN content: {len(results['without_in_content'])} files")
for fid, snips in results["without_in_content"]:
    print(f"  [{fid}] {snips}")

print(f"\n{'=' * 80}")
total_issues = sum(len(v) for v in results.values())
print(f"Total flags: {total_issues}")
