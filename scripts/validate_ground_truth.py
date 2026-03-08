#!/usr/bin/env python3
"""
Comprehensive ground truth validation script.

Validates all GT entries against their HTML source files to catch:
- articleBody text not found in HTML
- with-snippets missing from articleBody
- without-snippets leaking into articleBody
- HTML tags in articleBody
- Empty or suspiciously short/long fields
- Invalid dates
- Title mismatches
- Author issues
"""

import gzip
import html as html_module
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = ROOT / "release"
GT_PATH = RELEASE_DIR / "ground-truth.json"
HTML_DIR = RELEASE_DIR / "html"

# Thresholds
MIN_CONTENT_LENGTH = 200
MAX_CONTENT_LENGTH = 100_000
MIN_TITLE_LENGTH = 5


def normalize_text(text: str) -> str:
    """Normalize whitespace for comparison."""
    return re.sub(r'\s+', ' ', text).strip().lower()


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)


def html_to_text(html_content: str) -> str:
    """Get rough plaintext from HTML for content matching."""
    # Remove script/style blocks
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = strip_html_tags(text)
    # Decode HTML entities
    text = html_module.unescape(text)
    return text


def check_text_in_html(needle: str, html_text: str, threshold: float = 0.8) -> tuple:
    """
    Check if a text appears in the HTML plaintext.
    Uses word-level matching since whitespace/formatting differs.
    Returns (found_ratio, details).
    """
    needle_words = re.findall(r'\w+', needle.lower())
    html_words_lower = html_text.lower()

    if not needle_words:
        return 1.0, "empty text"

    # Check 8-word shingles from the needle
    shingle_size = min(8, len(needle_words))
    if shingle_size < 3:
        # For very short text, check word-by-word
        found = sum(1 for w in needle_words if w in html_words_lower)
        return found / len(needle_words), f"{found}/{len(needle_words)} words found"

    shingles = []
    for i in range(len(needle_words) - shingle_size + 1):
        shingle = ' '.join(needle_words[i:i + shingle_size])
        shingles.append(shingle)

    if not shingles:
        return 1.0, "no shingles"

    found = sum(1 for s in shingles if s in html_words_lower)
    return found / len(shingles), f"{found}/{len(shingles)} shingles found"


def validate_entry(file_id: str, entry: dict, html_text: str) -> list:
    """Validate a single GT entry. Returns list of (severity, issue) tuples."""
    issues = []
    article_body = entry.get('articleBody', '')
    title = entry.get('title', '')
    author = entry.get('author', '')
    publish_date = entry.get('publish_date', '')
    with_snippets = entry.get('with', [])
    without_snippets = entry.get('without', [])

    # === articleBody checks ===

    # Empty or very short
    if not article_body:
        issues.append(('CRITICAL', 'articleBody is empty'))
    elif len(article_body) < MIN_CONTENT_LENGTH:
        issues.append(('WARNING', f'articleBody very short: {len(article_body)} chars'))
    elif len(article_body) > MAX_CONTENT_LENGTH:
        issues.append(('WARNING', f'articleBody very long: {len(article_body)} chars'))

    # HTML tags in articleBody
    html_tag_matches = re.findall(r'<(?:div|span|p|a|img|br|h[1-6]|ul|ol|li|table|tr|td|th|strong|em|b|i|script|style|link|meta|header|footer|nav|section|article|aside|main|figure|figcaption|blockquote|pre|code|iframe|form|input|button|select|textarea|label)\b[^>]*>', article_body, re.IGNORECASE)
    if html_tag_matches:
        issues.append(('CRITICAL', f'HTML tags in articleBody: {html_tag_matches[:3]}'))

    # Check articleBody content exists in HTML
    if article_body and html_text:
        ratio, detail = check_text_in_html(article_body, html_text)
        if ratio < 0.5:
            issues.append(('CRITICAL', f'articleBody poorly matched in HTML: {ratio:.1%} ({detail})'))
        elif ratio < 0.8:
            issues.append(('WARNING', f'articleBody partially matched in HTML: {ratio:.1%} ({detail})'))

    # === Title checks ===
    if not title:
        issues.append(('INFO', 'title is empty'))
    elif len(title) < MIN_TITLE_LENGTH:
        issues.append(('WARNING', f'title very short: "{title}"'))
    elif html_text:
        title_lower = title.lower()
        if title_lower not in html_text.lower():
            # Try first 50 chars of title
            if title_lower[:50] not in html_text.lower():
                issues.append(('WARNING', f'title not found in HTML: "{title[:60]}..."'))

    # === Author checks ===
    if not author:
        issues.append(('INFO', 'author is empty'))

    # === Date checks ===
    if not publish_date:
        issues.append(('INFO', 'publish_date is empty'))
    elif publish_date:
        # Basic date format validation
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', publish_date):
            issues.append(('WARNING', f'publish_date format unexpected: "{publish_date}"'))

    # === With-snippet checks ===
    article_lower = article_body.lower() if article_body else ''
    for i, snippet in enumerate(with_snippets):
        if not snippet:
            issues.append(('WARNING', f'with[{i}] is empty'))
            continue
        snippet_lower = snippet.lower()
        # Must appear in articleBody
        if snippet_lower not in article_lower:
            # Try normalized comparison
            norm_snippet = normalize_text(snippet)
            norm_article = normalize_text(article_body)
            if norm_snippet not in norm_article:
                issues.append(('CRITICAL', f'with[{i}] NOT in articleBody: "{snippet[:80]}..."'))

    # === Without-snippet checks ===
    for i, snippet in enumerate(without_snippets):
        if not snippet:
            issues.append(('WARNING', f'without[{i}] is empty'))
            continue
        snippet_lower = snippet.lower()
        # Must NOT appear in articleBody
        if snippet_lower in article_lower:
            issues.append(('CRITICAL', f'without[{i}] FOUND in articleBody: "{snippet[:80]}..."'))
        # Should appear in the HTML (otherwise it's a useless check)
        if html_text and snippet_lower not in html_text.lower():
            norm_snippet = normalize_text(snippet)
            norm_html = normalize_text(html_text)
            if norm_snippet not in norm_html:
                issues.append(('INFO', f'without[{i}] not found in HTML either: "{snippet[:80]}..."'))

    return issues


def main():
    print("Loading ground truth...")
    with open(GT_PATH, 'r', encoding='utf-8') as f:
        gt = json.load(f)
    print(f"  {len(gt)} entries loaded")

    all_issues = {}
    severity_counts = {'CRITICAL': 0, 'WARNING': 0, 'INFO': 0}
    files_with_issues = {'CRITICAL': set(), 'WARNING': set(), 'INFO': set()}

    for file_id in sorted(gt.keys()):
        entry = gt[file_id]

        # Load HTML
        html_gz_path = HTML_DIR / f"{file_id}.html.gz"
        html_text = ""
        if html_gz_path.exists():
            with gzip.open(html_gz_path, 'rt', encoding='utf-8', errors='replace') as f:
                raw_html = f.read()
            html_text = html_to_text(raw_html)
        else:
            all_issues[file_id] = [('CRITICAL', f'HTML file not found: {html_gz_path}')]
            severity_counts['CRITICAL'] += 1
            files_with_issues['CRITICAL'].add(file_id)
            continue

        issues = validate_entry(file_id, entry, html_text)
        if issues:
            all_issues[file_id] = issues
            for severity, _ in issues:
                severity_counts[severity] += 1
                files_with_issues[severity].add(file_id)

    # === Report ===
    print("\n" + "=" * 80)
    print("VALIDATION REPORT")
    print("=" * 80)

    print(f"\nTotal entries:    {len(gt)}")
    print(f"Entries clean:    {len(gt) - len(all_issues)}")
    print(f"Entries flagged:  {len(all_issues)}")
    print()
    print(f"CRITICAL issues:  {severity_counts['CRITICAL']} (in {len(files_with_issues['CRITICAL'])} files)")
    print(f"WARNING issues:   {severity_counts['WARNING']} (in {len(files_with_issues['WARNING'])} files)")
    print(f"INFO issues:      {severity_counts['INFO']} (in {len(files_with_issues['INFO'])} files)")

    # Print CRITICAL issues
    if files_with_issues['CRITICAL']:
        print("\n" + "-" * 80)
        print("CRITICAL ISSUES")
        print("-" * 80)
        for file_id in sorted(files_with_issues['CRITICAL']):
            critical = [(s, msg) for s, msg in all_issues[file_id] if s == 'CRITICAL']
            for _, msg in critical:
                print(f"  [{file_id}] {msg}")

    # Print WARNING issues
    if files_with_issues['WARNING']:
        print("\n" + "-" * 80)
        print("WARNING ISSUES")
        print("-" * 80)
        for file_id in sorted(files_with_issues['WARNING']):
            warnings = [(s, msg) for s, msg in all_issues[file_id] if s == 'WARNING']
            for _, msg in warnings:
                print(f"  [{file_id}] {msg}")

    # Print INFO issues (summary only)
    if files_with_issues['INFO']:
        print("\n" + "-" * 80)
        print("INFO (summary)")
        print("-" * 80)
        info_types = {}
        for file_id in files_with_issues['INFO']:
            for s, msg in all_issues[file_id]:
                if s == 'INFO':
                    key = msg.split(':')[0] if ':' in msg else msg
                    info_types.setdefault(key, []).append(file_id)
        for info_type, fids in sorted(info_types.items()):
            print(f"  {info_type}: {len(fids)} files")
            if len(fids) <= 10:
                print(f"    Files: {', '.join(sorted(fids))}")

    # Save detailed results to JSON
    results_path = ROOT / "validation_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_issues, f, indent=2, ensure_ascii=False, sort_keys=True)
    print(f"\nDetailed results saved to: {results_path}")

    return 1 if severity_counts['CRITICAL'] > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
