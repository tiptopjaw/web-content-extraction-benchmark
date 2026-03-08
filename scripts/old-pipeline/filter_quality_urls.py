"""
Filter out category pages, shopping pages, and other low-quality URLs before annotation
"""
import csv
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SUBSET_FILTERED = DATA_DIR / "metadata_subset_filtered.csv"
REMAINING_FILTERED = DATA_DIR / "metadata_remaining_filtered.csv"
SUBSET_QUALITY = DATA_DIR / "metadata_subset_quality.csv"
REMAINING_QUALITY = DATA_DIR / "metadata_remaining_quality.csv"

# Problematic URL patterns
PROBLEMATIC_PATTERNS = [
    '/education', '/topics', '/categories', '/sitemap',
    '/about-us', '/contact-us', '/menu', '/services',
    '/products', '/solutions',
]

# Category patterns to exclude
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
                return True
    return False

def categorize_url(url):
    """Check if URL matches category patterns to exclude"""
    url_lower = url.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern in url_lower:
                return category
    return None

def filter_by_url_quality(input_file, output_file):
    """Filter metadata CSV by URL quality"""

    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    kept = []
    removed = []

    for row in rows:
        url = row['url']

        # Check problematic patterns
        if is_problematic_url(url):
            removed.append({
                'file_id': row['file_id'],
                'url': url,
                'reason': 'Hub/directory page'
            })
            continue

        # Check category patterns
        category = categorize_url(url)
        if category:
            removed.append({
                'file_id': row['file_id'],
                'url': url,
                'reason': f'Category page: {category}'
            })
            continue

        # Keep the file
        kept.append(row)

    # Write filtered subset
    if kept:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(kept)

    return kept, removed

def main():
    """Filter both subsets by URL quality"""

    print(f"\n{'='*80}")
    print("Filtering by URL Quality")
    print(f"{'='*80}\n")

    # Filter subset
    print("Processing metadata_subset_filtered.csv...")
    kept_subset, removed_subset = filter_by_url_quality(SUBSET_FILTERED, SUBSET_QUALITY)

    print(f"  Original: 1,899 files")
    print(f"  Kept: {len(kept_subset)} files")
    print(f"  Removed: {len(removed_subset)} files ({len(removed_subset)/1899*100:.1f}%)")

    # Filter remaining
    print("\nProcessing metadata_remaining_filtered.csv...")
    kept_remaining, removed_remaining = filter_by_url_quality(REMAINING_FILTERED, REMAINING_QUALITY)

    print(f"  Original: 388 files")
    print(f"  Kept: {len(kept_remaining)} files")
    print(f"  Removed: {len(removed_remaining)} files ({len(removed_remaining)/388*100:.1f}%)")

    # Summary
    total_original = 1899 + 388
    total_kept = len(kept_subset) + len(kept_remaining)
    total_removed = len(removed_subset) + len(removed_remaining)

    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}\n")
    print(f"Original total: {total_original:,} files (after size filtering)")
    print(f"Quality filtered: {total_kept:,} files")
    print(f"Removed: {total_removed:,} files ({total_removed/total_original*100:.1f}%)")

    # Breakdown of reasons
    reason_counts = Counter()
    all_removed = removed_subset + removed_remaining
    for item in all_removed:
        reason_counts[item['reason']] += 1

    print(f"\nRemoval reasons:")
    for reason, count in reason_counts.most_common():
        print(f"  {reason:40} {count:4} files")

    # Show samples
    if all_removed:
        print(f"\nSample removed files (first 15):")
        for item in all_removed[:15]:
            print(f"  {item['file_id']}: {item['reason']}")
            print(f"    {item['url'][:75]}")

        if len(all_removed) > 15:
            print(f"  ... and {len(all_removed) - 15} more")

    print(f"\n{'='*80}")
    print("Output Files")
    print(f"{'='*80}\n")
    print(f"Quality filtered subset: {SUBSET_QUALITY}")
    print(f"Quality filtered remaining: {REMAINING_QUALITY}")
    print(f"\nTotal files ready for annotation: {total_kept:,}")

    # Cost estimate update
    tokens_estimate = total_kept * 2000
    cost_estimate = tokens_estimate * 0.00014 + tokens_estimate * 0.00028

    print(f"\n{'='*80}")
    print("Updated Cost Estimate")
    print(f"{'='*80}\n")
    print(f"Files to annotate: {total_kept:,}")
    print(f"Estimated tokens: ~{tokens_estimate/1_000_000:.1f}M")
    print(f"Estimated cost: ~${cost_estimate:.2f}")
    print(f"Estimated time: ~{total_kept * 10 / 3600:.1f} hours")

    print(f"\n{'='*80}")
    print("Next Steps")
    print(f"{'='*80}\n")
    print(f"1. Review removed files above")
    print(f"2. Update annotate_batch.py to use: {SUBSET_QUALITY.name}")
    print(f"3. Update annotate_remaining.py to use: {REMAINING_QUALITY.name}")
    print(f"4. Proceed with testing and annotation")

if __name__ == "__main__":
    main()
