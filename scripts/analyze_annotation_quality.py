"""
Analyze annotation quality to identify problematic pages
"""
import json
import re
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"

# Navigation/boilerplate keywords
NAV_KEYWORDS = [
    'menu', 'navigation', 'close', 'open', 'submenu', 'contact', 'store',
    'subscribe', 'sign up', 'login', 'search', 'footer', 'header',
    'cookie', 'privacy', 'terms', 'copyright', 'all rights reserved'
]

def analyze_annotation(file_path):
    """Analyze a single annotation for quality issues"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    gt = data.get('ground_truth', {})
    file_id = data.get('file_id', '')
    url = data.get('url', '')

    main_content = gt.get('main_content', '')
    content_length = len(main_content)

    # Count navigation keywords
    main_lower = main_content.lower()
    nav_count = sum(main_lower.count(kw) for kw in NAV_KEYWORDS)

    # Check for repeated phrases (menu items)
    words = main_content.split()
    if len(words) > 0:
        word_freq = Counter(words)
        most_common = word_freq.most_common(5)
        max_repetition = most_common[0][1] if most_common else 0
    else:
        max_repetition = 0

    # Identify issues
    issues = []

    if content_length < 500:
        issues.append(f"SHORT_CONTENT ({content_length} chars)")

    if nav_count > 10:
        issues.append(f"HIGH_NAV_WORDS ({nav_count} occurrences)")

    if max_repetition > 5:
        issues.append(f"REPEATED_WORDS ({most_common[0][0]}: {max_repetition}x)")

    # Check for common hub page URLs
    if any(pattern in url.lower() for pattern in ['/education', '/topics', '/categories', '/sitemap', '/about', '/contact']):
        if content_length < 2000:
            issues.append("HUB_PAGE_PATTERN")

    # Check without snippets - should not be mostly from with snippets
    with_snippets = gt.get('with', [])
    without_snippets = gt.get('without', [])

    if without_snippets:
        # Check if without snippets are appearing in main_content
        without_in_content = sum(1 for snippet in without_snippets if snippet.lower() in main_lower)
        if without_in_content > len(without_snippets) / 2:
            issues.append(f"BOILERPLATE_IN_CONTENT ({without_in_content}/{len(without_snippets)} 'without' snippets found)")

    return {
        'file_id': file_id,
        'url': url,
        'content_length': content_length,
        'nav_keyword_count': nav_count,
        'max_word_repetition': max_repetition,
        'issues': issues
    }

def main():
    """Analyze all annotations"""

    annotations = list(GROUND_TRUTH_DIR.glob("*.json"))

    print(f"\n{'='*80}")
    print(f"Annotation Quality Analysis")
    print(f"{'='*80}\n")
    print(f"Total annotations: {len(annotations)}\n")

    problematic = []

    for ann_file in sorted(annotations):
        result = analyze_annotation(ann_file)
        if result['issues']:
            problematic.append(result)

    # Summary
    print(f"Problematic annotations: {len(problematic)}/{len(annotations)}\n")

    # Group by issue type
    issue_counts = Counter()
    for p in problematic:
        for issue in p['issues']:
            issue_type = issue.split('(')[0].strip()
            issue_counts[issue_type] += 1

    print("Issues by type:")
    for issue_type, count in issue_counts.most_common():
        print(f"  {issue_type}: {count}")

    # Show problematic files
    print(f"\n{'='*80}")
    print("Problematic Files (first 50)")
    print(f"{'='*80}\n")

    for i, p in enumerate(problematic[:50]):
        print(f"File {p['file_id']} | {p['content_length']} chars | {p['nav_keyword_count']} nav words")
        print(f"  URL: {p['url']}")
        print(f"  Issues: {', '.join(p['issues'])}")
        print()

    if len(problematic) > 50:
        print(f"... and {len(problematic) - 50} more\n")

    # Save full report
    report_file = BASE_DIR / "data" / "quality_analysis.json"
    with open(report_file, 'w') as f:
        json.dump(problematic, f, indent=2)

    print(f"Full report saved to: {report_file}")

    # Recommendations
    print(f"\n{'='*80}")
    print("Recommendations")
    print(f"{'='*80}\n")

    short_content_count = sum(1 for p in problematic if any('SHORT_CONTENT' in i for i in p['issues']))
    hub_page_count = sum(1 for p in problematic if any('HUB_PAGE' in i for i in p['issues']))
    nav_heavy_count = sum(1 for p in problematic if any('HIGH_NAV' in i for i in p['issues']))

    print(f"- {short_content_count} files with very short content (< 500 chars)")
    print(f"- {hub_page_count} files identified as hub/navigation pages")
    print(f"- {nav_heavy_count} files with excessive navigation keywords")
    print()

    if len(problematic) > 100:
        print("⚠ Recommendation: Consider filtering out problematic files before running more batches")
        print("  You may want to review the quality_analysis.json file and decide which to exclude")
    else:
        print("✓ Quality looks acceptable. Problematic files are a minority.")
        print("  You can proceed with remaining batches or filter these out first.")

if __name__ == "__main__":
    main()
