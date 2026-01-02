"""
Filter and merge new annotations with existing clean dataset
"""
import json
import shutil
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
CLEAN_DIR = DATA_DIR / "ground_truth"
MERGED_DIR = DATA_DIR / "ground_truth_merged"
REMOVED_DIR = DATA_DIR / "ground_truth_removed"

# Quality thresholds
MIN_CONTENT_LENGTH = 500
MAX_NAV_KEYWORDS = 10

# Navigation/boilerplate keywords
NAV_KEYWORDS = [
    'menu', 'navigation', 'close', 'open', 'submenu', 'contact', 'store',
    'subscribe', 'sign up', 'login', 'search', 'footer', 'header',
    'cookie', 'privacy', 'terms', 'copyright', 'all rights reserved'
]

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

def analyze_quality(annotation):
    """Analyze annotation quality"""
    gt = annotation.get('ground_truth', {})
    url = annotation.get('url', '')
    main_content = gt.get('main_content', '')
    content_length = len(main_content)

    issues = []

    # Check content length
    if content_length < MIN_CONTENT_LENGTH:
        issues.append(f"Short content ({content_length} chars)")

    # Check URL patterns
    if is_problematic_url(url):
        issues.append("Hub/directory page")

    # Check navigation keywords
    main_lower = main_content.lower()
    nav_count = sum(main_lower.count(kw) for kw in NAV_KEYWORDS)
    if nav_count > MAX_NAV_KEYWORDS:
        issues.append(f"High nav keywords ({nav_count})")

    # Check category patterns
    category = categorize_url(url)
    if category:
        issues.append(f"Category page: {category}")

    # Check boilerplate
    without_snippets = gt.get('without', [])
    if without_snippets:
        without_in_content = sum(1 for snippet in without_snippets
                                if snippet.lower() in main_lower)
        if without_in_content > len(without_snippets) / 2:
            issues.append(f"High boilerplate ({without_in_content}/{len(without_snippets)})")

    return issues

def get_existing_clean_ids():
    """Get file IDs from existing clean dataset"""
    clean_files = list(CLEAN_DIR.glob("*.json"))
    return {f.stem for f in clean_files}

def main():
    """Filter new annotations and merge with existing clean dataset"""

    print(f"\n{'='*80}")
    print("Filtering and Merging New Annotations")
    print(f"{'='*80}\n")

    # Get existing clean dataset
    existing_clean = get_existing_clean_ids()
    print(f"Existing clean dataset: {len(existing_clean)} files")

    # Find new annotations (not in existing clean dataset)
    all_annotations = list(GROUND_TRUTH_DIR.glob("*.json"))
    new_annotations = [f for f in all_annotations if f.stem not in existing_clean]

    print(f"Total annotations in ground_truth/: {len(all_annotations)}")
    print(f"New annotations to process: {len(new_annotations)}\n")

    if not new_annotations:
        print("No new annotations found!")
        return

    # Analyze new annotations
    keep = []
    remove = []

    for ann_file in new_annotations:
        with open(ann_file) as f:
            data = json.load(f)

        issues = analyze_quality(data)

        if issues:
            remove.append({
                'file_id': ann_file.stem,
                'url': data.get('url', ''),
                'issues': issues,
                'file': ann_file
            })
        else:
            keep.append(ann_file)

    # Report
    print(f"{'='*80}")
    print("Quality Analysis Results")
    print(f"{'='*80}\n")
    print(f"New annotations analyzed: {len(new_annotations)}")
    print(f"Passed quality checks: {len(keep)} ({len(keep)/len(new_annotations)*100:.1f}%)")
    print(f"Failed quality checks: {len(remove)} ({len(remove)/len(new_annotations)*100:.1f}%)")

    # Breakdown of issues
    if remove:
        issue_counts = Counter()
        for item in remove:
            for issue in item['issues']:
                issue_type = issue.split('(')[0].strip()
                issue_counts[issue_type] += 1

        print(f"\nIssues found:")
        for issue_type, count in issue_counts.most_common():
            print(f"  {issue_type:30} {count:4} files")

    # Show samples
    if remove:
        print(f"\nSample removed files (first 10):")
        for item in remove[:10]:
            print(f"  {item['file_id']}: {', '.join(item['issues'])}")
            print(f"    {item['url'][:70]}")
        if len(remove) > 10:
            print(f"  ... and {len(remove) - 10} more")

    print(f"\n{'='*80}")

    # Create merged directory
    MERGED_DIR.mkdir(exist_ok=True)

    # Copy existing clean files to merged
    print(f"\nCopying existing clean dataset...")
    for clean_file in CLEAN_DIR.glob("*.json"):
        dst = MERGED_DIR / clean_file.name
        shutil.copy2(clean_file, dst)

    # Copy new clean files to merged
    print(f"Adding new clean annotations...")
    for new_file in keep:
        dst = MERGED_DIR / new_file.name
        shutil.copy2(new_file, dst)

    # Move removed files
    print(f"Moving rejected files to removed directory...")
    for item in remove:
        dst = REMOVED_DIR / item['file'].name
        shutil.copy2(item['file'], dst)

    # Final count
    merged_files = list(MERGED_DIR.glob("*.json"))

    print(f"\n{'='*80}")
    print("Merge Complete!")
    print(f"{'='*80}\n")
    print(f"Existing clean dataset: {len(existing_clean)}")
    print(f"New annotations added: {len(keep)}")
    print(f"New annotations rejected: {len(remove)}")
    print(f"Final merged dataset: {len(merged_files)}")
    print(f"\nMerged dataset location: {MERGED_DIR}")

    # Save report
    report = {
        'existing_clean': len(existing_clean),
        'new_processed': len(new_annotations),
        'new_kept': len(keep),
        'new_removed': len(remove),
        'final_total': len(merged_files),
        'removed_breakdown': {
            issue_type: count
            for issue_type, count in issue_counts.most_common()
        } if remove else {}
    }

    report_file = DATA_DIR / "merge_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to: {report_file}")

    print(f"\n{'='*80}")
    print("Next Steps")
    print(f"{'='*80}\n")
    print(f"1. Update benchmark script to use: {MERGED_DIR}")
    print(f"2. Run benchmark on merged dataset")
    print(f"3. Your dataset now has {len(merged_files)} high-quality annotations!")

if __name__ == "__main__":
    main()
