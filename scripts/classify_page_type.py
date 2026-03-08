"""
URL-based page type classifier for web content extraction.

Classifies URLs into page types using fast heuristic pattern matching.
Based on url_labeler.py from the ml-scoring project, adapted for
content extraction benchmark page types.

Page types:
  article       - Blog posts, news, editorials, guides
  forum         - Discussion threads, Q&A, community posts
  product       - Individual product pages
  category      - Product listings, collections, browse pages
  documentation - Technical docs, API references, man pages, wikis
  service       - SaaS feature pages, service descriptions
"""
from urllib.parse import urlparse


PAGE_TYPES = [
    'article',
    'forum',
    'product',
    'category',
    'documentation',
    'service',
]


# === Forum detection ===

FORUM_PATH_PATTERNS = [
    '/forum', '/forums/', '/thread/', '/threads/',
    '/topic/', '/topics/', '/discussion/', '/discussions/',
    '/community/', '/t/',  # Discourse-style
    '/questions/', '/question/',
    '/comments/',
]

FORUM_DOMAIN_PATTERNS = [
    'forum.', 'forums.', 'community.', 'discuss.',
    'discussion.', 'users.',  # users.rust-lang.org
    'reddit.com', 'stackoverflow.com', 'stackexchange.com',
    'gamefaqs.', 'discourse.',
    'news.ycombinator.com',
    'quora.com',
    'lemmy.',
    'tapatalk.com',
    'bbs.',  # bbs.archlinux.org
    'webhostingtalk.com',
    'netmums.com',
    'mumsnet.com',
    'nairaland.com',
    'lobste.rs',
]

FORUM_PATH_EXTRA = [
    '/viewtopic.php',  # phpBB
    '/showthread.php',  # vBulletin
    '/item?id=',  # Hacker News
    '/talk/',  # Mumsnet-style
]


# === Product detection ===

PRODUCT_PATH_PATTERNS = [
    '/products/', '/product/',
    '/dp/',       # Amazon
    '/ip/',       # Walmart
    '/shop/',     # Common store path
]

PRODUCT_DOMAIN_PATTERNS = [
    'shop.', 'store.',
]


# === Category / collection detection ===

CATEGORY_PATH_PATTERNS = [
    '/collections/', '/collection/',
    '/categories/', '/category/',
    '/browse/',
    '/cat/',  # IKEA-style
    '/subcategory/',
]


# === Documentation detection ===

DOCS_PATH_PATTERNS = [
    '/docs/', '/doc/',
    '/documentation/',
    '/reference/',
    '/api/',
    '/guide/', '/guides/',
    '/tutorial/', '/tutorials/',
    '/manual/',
    '/handbook/',
    '/wiki/',
    '/man-pages/', '/man/',
    '/library/',  # Python stdlib docs
    '/concepts/',
    '/userguide/',
    '/quickstart',
    '/getting-started',
    '/book/',
]

DOCS_DOMAIN_PATTERNS = [
    'docs.', 'doc.',
    'wiki.',
    'devdocs.',
    'man7.org',
    'readthedocs.io',
    'readthedocs.org',
    'developer.hashicorp.com',
    'developer.mozilla.org',
]


# === Service page detection ===

SERVICE_PATH_PATTERNS = [
    '/services/', '/service/',
    '/solutions/', '/solution/',
    '/offerings/',
    '/what-we-do',
]


# === Article / blog detection ===

ARTICLE_PATH_PATTERNS = [
    '/blog/', '/blog',
    '/news/', '/news',
    '/article/', '/articles/',
    '/post/', '/posts/',
    '/insight/', '/insights/',
    '/resource/', '/resources/',
    '/learn/',
    '/stories/',
    '/magazine/',
    '/journal/',
    '/press/',
    '/editorial/',
    '/opinion/',
    '/review/',
    '/column/',
]

BLOG_SLUG_PATTERNS = [
    '-ways-to-', '-tips-', '-reasons-', '-steps-to-',
    '-things-to-', '-best-', '-top-', '-essential-',
    'beginners-guide', 'complete-guide', 'ultimate-guide',
    'how-to-', 'what-is-', 'why-', 'when-to-',
    '-vs-', '-versus-', '-comparison',
    '-checklist', '-trends-', '-strategies-',
    '-challenges-', '-benefits-', '-advantages-',
]


def classify_url(url: str) -> str:
    """
    Classify a URL into a page type using heuristic pattern matching.

    Args:
        url: Full URL or path to classify

    Returns:
        One of: 'article', 'forum', 'product', 'category',
                'documentation', 'service', or 'article' (default)
    """
    if not url:
        return 'article'

    parsed = urlparse(url)
    url_lower = url.lower()
    path_lower = parsed.path.lower()
    domain_lower = (parsed.netloc or '').lower()

    # 1. Forum detection (check first - forums have distinctive patterns)
    if any(p in domain_lower for p in FORUM_DOMAIN_PATTERNS):
        return 'forum'
    if any(p in path_lower for p in FORUM_PATH_PATTERNS):
        return 'forum'
    if any(p in url_lower for p in FORUM_PATH_EXTRA):
        return 'forum'

    # 2. Documentation detection (before article - /docs/guide/ is docs, not article)
    if any(p in domain_lower for p in DOCS_DOMAIN_PATTERNS):
        return 'documentation'
    if any(p in path_lower for p in DOCS_PATH_PATTERNS):
        return 'documentation'

    # 3. Product detection (before category - /products/slug is product)
    if any(p in path_lower for p in PRODUCT_PATH_PATTERNS):
        return 'product'

    # 4. Category / collection detection
    if any(p in path_lower for p in CATEGORY_PATH_PATTERNS):
        return 'category'

    # 5. Service page detection
    if any(p in path_lower for p in SERVICE_PATH_PATTERNS):
        return 'service'

    # 6. Article / blog detection
    if any(p in path_lower for p in ARTICLE_PATH_PATTERNS):
        return 'article'
    if any(p in url_lower for p in BLOG_SLUG_PATTERNS):
        return 'article'

    # 7. Default to article (most common page type on the web)
    return 'article'


def classify_url_detailed(url: str) -> dict:
    """
    Classify a URL and return detailed match info for debugging.

    Returns:
        Dict with 'url', 'page_type', 'matched_pattern', 'matched_source'
    """
    if not url:
        return {'url': url, 'page_type': 'article', 'matched_pattern': None, 'matched_source': 'default'}

    parsed = urlparse(url)
    url_lower = url.lower()
    path_lower = parsed.path.lower()
    domain_lower = (parsed.netloc or '').lower()

    checks = [
        ('forum', 'domain', FORUM_DOMAIN_PATTERNS, domain_lower),
        ('forum', 'path', FORUM_PATH_PATTERNS, path_lower),
        ('forum', 'url', FORUM_PATH_EXTRA, url_lower),
        ('documentation', 'domain', DOCS_DOMAIN_PATTERNS, domain_lower),
        ('documentation', 'path', DOCS_PATH_PATTERNS, path_lower),
        ('product', 'path', PRODUCT_PATH_PATTERNS, path_lower),
        ('category', 'path', CATEGORY_PATH_PATTERNS, path_lower),
        ('service', 'path', SERVICE_PATH_PATTERNS, path_lower),
        ('article', 'path', ARTICLE_PATH_PATTERNS, path_lower),
        ('article', 'slug', BLOG_SLUG_PATTERNS, url_lower),
    ]

    for page_type, source, patterns, target in checks:
        for p in patterns:
            if p in target:
                return {
                    'url': url,
                    'page_type': page_type,
                    'matched_pattern': p,
                    'matched_source': source,
                }

    return {'url': url, 'page_type': 'article', 'matched_pattern': None, 'matched_source': 'default'}


if __name__ == '__main__':
    import json
    from pathlib import Path
    from collections import defaultdict

    gt_dir = Path(__file__).parent.parent / 'benchmark' / 'ground-truth'

    def get_actual_type(fid):
        n = int(fid)
        if n <= 500: return 'article'
        if n <= 579: return 'forum'
        if n <= 631: return 'product'
        if n <= 660: return 'category'
        if n <= 689: return 'documentation'
        if n <= 719: return 'service'
        return 'unknown'

    # Classify all URLs and compare
    correct = 0
    total = 0
    by_type = defaultdict(lambda: {'correct': 0, 'total': 0, 'misses': []})

    for f in sorted(gt_dir.glob('*.json')):
        gt = json.load(open(f))
        url = gt.get('url', '')
        actual = get_actual_type(f.stem)
        result = classify_url_detailed(url)
        predicted = result['page_type']

        total += 1
        info = by_type[actual]
        info['total'] += 1

        if predicted == actual:
            correct += 1
            info['correct'] += 1
        else:
            info['misses'].append({
                'id': f.stem,
                'url': url[:100],
                'predicted': predicted,
                'pattern': result['matched_pattern'],
                'source': result['matched_source'],
            })

    print(f'\n=== URL Page Type Classification Results ===\n')
    print(f'Overall: {correct}/{total} correct ({correct/total:.1%})\n')

    print(f'{"Type":<15s} {"Correct":>7s} {"Total":>5s} {"Acc":>6s}')
    print('-' * 35)
    for pt in ['article', 'forum', 'product', 'category', 'documentation', 'service']:
        info = by_type[pt]
        acc = info['correct'] / info['total'] if info['total'] else 0
        print(f'{pt:<15s} {info["correct"]:>7d} {info["total"]:>5d} {acc:>5.1%}')

    # Show misclassified
    for pt in ['article', 'forum', 'product', 'category', 'documentation', 'service']:
        misses = by_type[pt]['misses']
        if misses:
            print(f'\n--- {pt}: {len(misses)} misclassified ---')
            for m in misses[:10]:
                print(f'  {m["id"]}: predicted={m["predicted"]:15s} pattern={m["pattern"]!s:20s} {m["url"][:80]}')
            if len(misses) > 10:
                print(f'  ... and {len(misses)-10} more')
