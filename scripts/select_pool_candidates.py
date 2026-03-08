#!/usr/bin/env python3
"""Classify unused benchmark-package files by page type and select candidates
to expand the curated benchmark toward 1,000 files.

Uses URL-based classification (matching rs-trafilatura's classify_url logic)
plus simple HTML heuristics for ambiguous cases.

Output: pool_candidates.json with classified files and selection recommendations.
"""

import json
import os
import gzip
import re
from collections import defaultdict
from urllib.parse import urlparse

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_GT = os.path.join(PROJ, "benchmark-package", "ground-truth.json")
PKG_HTML = os.path.join(PROJ, "benchmark-package", "html")
CUR_GT = os.path.join(PROJ, "benchmark", "ground-truth")
CUR_HTML = os.path.join(PROJ, "benchmark", "html")

# URL patterns for page type classification (mirrors rs-trafilatura logic)
FORUM_PATTERNS = [
    r'/forum', r'/thread', r'/topic', r'/discussion', r'/community/',
    r'/t/', r'/d/', r'viewtopic', r'showthread', r'/post/',
    r'discourse', r'reddit\.com/r/', r'news\.ycombinator',
    r'stackexchange', r'stackoverflow', r'askubuntu',
    r'superuser\.com', r'serverfault\.com',
]

PRODUCT_PATTERNS = [
    r'/product[s]?/', r'/item/', r'/dp/', r'/ip/',
    r'/buy/', r'\.html$.*product',
    r'shop\..*/.*-', r'/collections/.+/.+',
]

CATEGORY_PATTERNS = [
    r'/collections?/', r'/category/', r'/categories/',
    r'/shop/', r'/browse/', r'/department/',
    r'/collections$', r'/shop$',
]

DOC_PATTERNS = [
    r'/docs?/', r'/documentation/', r'/guide/',
    r'/reference/', r'/api/', r'/manual/',
    r'/wiki/', r'/tutorial/', r'/learn/',
    r'docs\.',  r'wiki\.',
    r'developer\.',  r'devdocs\.',
]

SERVICE_PATTERNS = [
    r'^https?://[^/]+/?$',  # Homepage
    r'/pricing', r'/features', r'/solutions',
    r'/services', r'/about', r'/enterprise',
    r'/platform',
]

LISTING_PATTERNS = [
    r'/search', r'/results', r'/listings',
    r'/index', r'/archive', r'/tag/',
    r'/page/', r'\?page=', r'\?q=',
]


def classify_url(url: str) -> str:
    """Classify a URL into a page type."""
    url_lower = url.lower()

    for pat in FORUM_PATTERNS:
        if re.search(pat, url_lower):
            return "forum"

    for pat in DOC_PATTERNS:
        if re.search(pat, url_lower):
            return "documentation"

    for pat in PRODUCT_PATTERNS:
        if re.search(pat, url_lower):
            return "product"

    for pat in CATEGORY_PATTERNS:
        if re.search(pat, url_lower):
            return "collection"

    for pat in LISTING_PATTERNS:
        if re.search(pat, url_lower):
            return "listing"

    for pat in SERVICE_PATTERNS:
        if re.search(pat, url_lower):
            return "service"

    return "article"


def get_html_hints(html_path: str) -> dict:
    """Extract quick signals from HTML to refine classification."""
    try:
        with gzip.open(html_path, 'rt', errors='replace') as f:
            html = f.read(100_000)  # First 100KB is enough for signals
    except Exception:
        return {}

    hints = {}
    html_lower = html.lower()

    # Check for og:type
    og_match = re.search(r'og:type["\s]+content="([^"]+)"', html_lower)
    if og_match:
        hints['og_type'] = og_match.group(1)

    # Check for JSON-LD @type
    ld_types = re.findall(r'"@type"\s*:\s*"(\w+)"', html)
    if ld_types:
        hints['ld_types'] = ld_types

    # Word count estimate (visible text proxy)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    hints['word_count'] = len(text.split())

    # Check for common forum platforms
    if 'discourse' in html_lower or 'data-discourse' in html_lower:
        hints['platform'] = 'discourse'
    elif 'vbulletin' in html_lower:
        hints['platform'] = 'vbulletin'
    elif 'phpbb' in html_lower:
        hints['platform'] = 'phpbb'

    return hints


def refine_type(url_type: str, hints: dict) -> str:
    """Refine URL classification with HTML hints."""
    og = hints.get('og_type', '')
    ld = hints.get('ld_types', [])

    if 'Product' in ld and url_type == 'article':
        return 'product'
    if og == 'product' and url_type == 'article':
        return 'product'
    if og == 'article' and url_type != 'forum':
        return 'article'
    if hints.get('platform') in ('discourse', 'vbulletin', 'phpbb'):
        return 'forum'

    return url_type


def main():
    # Load package GT
    with open(PKG_GT) as f:
        pkg_gt = json.load(f)

    # Get curated IDs (GT + HTML)
    curated_ids = set()
    for f in os.listdir(CUR_GT):
        if f.endswith('.json'):
            curated_ids.add(f.replace('.json', ''))
    for f in os.listdir(CUR_HTML):
        if f.endswith('.html'):
            curated_ids.add(f.replace('.html', ''))

    # Current page type distribution
    current_types = defaultdict(int)
    for f in os.listdir(CUR_GT):
        if not f.endswith('.json'):
            continue
        with open(os.path.join(CUR_GT, f)) as fh:
            d = json.load(fh)
        pt = d.get('_internal', {}).get('page_type', {}).get('primary', 'article')
        current_types[pt] += 1

    print("=== Current distribution ===")
    total_current = sum(current_types.values())
    for t in sorted(current_types, key=current_types.get, reverse=True):
        print(f"  {t:<15} {current_types[t]:>4} ({current_types[t]/total_current*100:.1f}%)")
    print(f"  {'TOTAL':<15} {total_current:>4}")

    # Target distribution
    targets = {
        'article': 450,
        'forum': 120,
        'service': 110,
        'product': 100,
        'documentation': 80,
        'collection': 70,
        'listing': 70,
    }
    target_total = sum(targets.values())

    print(f"\n=== Target: {target_total} ===")
    needed = {}
    for t in sorted(targets, key=targets.get, reverse=True):
        gap = max(0, targets[t] - current_types.get(t, 0))
        needed[t] = gap
        print(f"  {t:<15} have={current_types.get(t,0):>4}  target={targets[t]:>4}  need={gap:>4}")

    total_needed = sum(needed.values())
    print(f"  {'TOTAL NEEDED':<15} {total_needed:>4}")

    # Classify pool files
    print(f"\n=== Classifying {len(pkg_gt) - len(curated_ids)} pool files ===")

    pool = []  # (fid, url, page_type, body_len, hints)
    pool_types = defaultdict(list)

    for fid in sorted(pkg_gt.keys()):
        if fid in curated_ids:
            continue
        html_path = os.path.join(PKG_HTML, f"{fid}.html.gz")
        if not os.path.exists(html_path):
            continue

        entry = pkg_gt[fid]
        url = entry.get('url', '')
        body = entry.get('articleBody', '')
        body_len = len(body)

        # Skip very short GT
        if body_len < 50:
            continue

        # Classify
        url_type = classify_url(url)
        hints = get_html_hints(html_path)
        page_type = refine_type(url_type, hints)

        # Skip JS-rendered pages (very few visible words)
        if hints.get('word_count', 999) < 30:
            continue

        rec = {
            'file_id': fid,
            'url': url,
            'page_type': page_type,
            'body_len': body_len,
            'word_count': hints.get('word_count', 0),
            'og_type': hints.get('og_type', ''),
            'ld_types': hints.get('ld_types', []),
        }
        pool.append(rec)
        pool_types[page_type].append(rec)

    print(f"Classified {len(pool)} usable pool files:")
    for t in sorted(pool_types, key=lambda t: len(pool_types[t]), reverse=True):
        print(f"  {t:<15} {len(pool_types[t]):>4}")

    # Select candidates: prioritize by need, pick longest GT first (higher quality)
    selected = []
    selected_types = defaultdict(int)

    for page_type in sorted(needed, key=needed.get, reverse=True):
        n = needed[page_type]
        if n == 0:
            continue

        candidates = sorted(pool_types.get(page_type, []),
                          key=lambda r: r['body_len'], reverse=True)

        picked = candidates[:n]
        selected.extend(picked)
        selected_types[page_type] = len(picked)

        if len(picked) < n:
            print(f"  WARNING: {page_type} only has {len(picked)} candidates, need {n}")

    print(f"\n=== Selected {len(selected)} candidates ===")
    for t in sorted(selected_types, key=selected_types.get, reverse=True):
        have = current_types.get(t, 0)
        print(f"  {t:<15} +{selected_types[t]:>3} (was {have}, now {have + selected_types[t]})")

    final_total = total_current + len(selected)
    print(f"  {'NEW TOTAL':<15} {final_total:>4}")

    # Save results
    output = {
        'current_distribution': dict(current_types),
        'targets': targets,
        'needed': needed,
        'pool_distribution': {t: len(v) for t, v in pool_types.items()},
        'selected': selected,
        'selected_count': len(selected),
        'selected_by_type': dict(selected_types),
    }

    out_path = os.path.join(PROJ, "pool_candidates.json")
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to: {out_path}")


if __name__ == '__main__':
    main()
