"""
Save list of all filtered URLs to a file for review
"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"

# Original files
ORIGINAL_SUBSET = DATA_DIR / "metadata_subset_2000.csv"
ORIGINAL_REMAINING = DATA_DIR / "metadata_remaining_404.csv"

# Final quality-filtered files
FINAL_SUBSET = DATA_DIR / "metadata_subset_quality.csv"
FINAL_REMAINING = DATA_DIR / "metadata_remaining_quality.csv"

# Output file
OUTPUT_FILE = DATA_DIR / "filtered_urls_removed.csv"

# Problematic URL patterns
PROBLEMATIC_PATTERNS = [
    '/education', '/topics', '/categories', '/sitemap',
    '/about-us', '/contact-us', '/menu', '/services',
    '/products', '/solutions',
]

# Category patterns
CATEGORY_PATTERNS = {
    'News Category': [
        '/news/', '/category/', '/tag/', '/topics/',
        '/latest-news/', '/press/', '/media/', '/blog-category/'
    ],
    'Shopping/Store': [
        '/shop', '/store', '/collections/', '/deals',
        '/buy', '/products/', '/catalog/', '/sale', '/outlet'
    ],
    'YouTube': [
        'youtube.com', 'youtu.be'
    ],
    'Directory/Listings': [
        '/listings/', '/directory/', 'businesses-for-sale',
        '/companies/', '/find-', '/locations/', '/businesses/',
        '-for-sale-and-investment/', '/marketplace/'
    ]
}

def is_problematic_url(url):
    """Check if URL matches problematic patterns"""
    url_lower = url.lower()
    for pattern in PROBLEMATIC_PATTERNS:
        if pattern in url_lower:
            if url_lower.endswith(pattern) or url_lower.endswith(pattern + '/'):
                return 'Hub/directory page'
    return None

def categorize_url(url):
    """Check if URL matches category patterns"""
    url_lower = url.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern in url_lower:
                return f'Category: {category}'
    return None

def main():
    # Load original files
    original_ids = {}

    with open(ORIGINAL_SUBSET) as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_ids[row['file_id']] = row

    with open(ORIGINAL_REMAINING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_ids[row['file_id']] = row

    # Load final quality-filtered files
    final_ids = set()

    with open(FINAL_SUBSET) as f:
        reader = csv.DictReader(f)
        for row in reader:
            final_ids.add(row['file_id'])

    with open(FINAL_REMAINING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            final_ids.add(row['file_id'])

    # Find removed files
    removed = []

    for file_id, row in original_ids.items():
        if file_id not in final_ids:
            url = row['url']
            html_file = HTML_DIR / f"{int(file_id):04d}.html"

            # Determine reason
            reason = None

            # Check file size
            if html_file.exists():
                size = html_file.stat().st_size
                if size > 1_000_000:
                    reason = f'Large file ({size//1024}KB)'

            # Check URL patterns
            if not reason:
                reason = is_problematic_url(url)

            if not reason:
                reason = categorize_url(url)

            if not reason:
                reason = 'Unknown'

            removed.append({
                'file_id': file_id,
                'url': url,
                'reason': reason,
                'file_size_kb': size//1024 if html_file.exists() else 'N/A'
            })

    # Sort by file_id
    removed.sort(key=lambda x: int(x['file_id']))

    # Write to CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['file_id', 'url', 'reason', 'file_size_kb']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(removed)

    print(f"\n{'='*80}")
    print("Filtered URLs Saved")
    print(f"{'='*80}\n")
    print(f"Total removed: {len(removed)} files")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"\nBreakdown:")

    # Count by reason
    from collections import Counter
    reasons = Counter(r['reason'] for r in removed)
    for reason, count in reasons.most_common():
        print(f"  {reason:40} {count:4} files")

    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
