"""
Remove specific categories of pages from the dataset
- News category pages
- Shopping/store pages
- YouTube links
- Directory/listing pages
"""
import json
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
FINAL_DIR = DATA_DIR / "ground_truth_final"
REMOVED_DIR = DATA_DIR / "ground_truth_removed"
CLEAN_DIR = DATA_DIR / "ground_truth"

# URL patterns to identify and remove
PATTERNS = {
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

def categorize_url(url):
    """Check if URL matches any removal patterns"""
    url_lower = url.lower()

    for category, patterns in PATTERNS.items():
        for pattern in patterns:
            if pattern in url_lower:
                return category

    return None

def main():
    """Remove category pages from final dataset"""

    print(f"\n{'='*80}")
    print("Removing Specific Category Pages")
    print(f"{'='*80}\n")

    # Create clean directory
    CLEAN_DIR.mkdir(exist_ok=True)

    # Load all files from final directory
    all_files = list(FINAL_DIR.glob("*.json"))

    # Categorize files
    to_remove = {cat: [] for cat in PATTERNS.keys()}
    to_keep = []

    for json_file in all_files:
        with open(json_file) as f:
            data = json.load(f)
            url = data.get('url', '')

        category = categorize_url(url)

        if category:
            to_remove[category].append({
                'file_id': json_file.stem,
                'url': url,
                'file': json_file
            })
        else:
            to_keep.append(json_file)

    # Show what will be removed
    print("Files to remove by category:")
    total_remove = 0
    for category, items in to_remove.items():
        print(f"  {category:20} {len(items):4} files")
        total_remove += len(items)

    print(f"\nTotal to remove: {total_remove}")
    print(f"Total to keep: {len(to_keep)}")
    print(f"\n{'='*80}\n")

    # Show samples
    print("Sample files being removed (first 5 per category):\n")
    for category, items in to_remove.items():
        if items:
            print(f"{category}:")
            for item in items[:5]:
                print(f"  {item['file_id']}: {item['url'][:70]}")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
            print()

    # Confirm removal
    print(f"{'='*80}")
    response = input(f"\nProceed with removal? (yes/no): ").strip().lower()

    if response != 'yes':
        print("Cancelled.")
        return

    print(f"\n{'='*80}\n")

    # Move files to remove
    removed_count = 0
    for category, items in to_remove.items():
        for item in items:
            dst = REMOVED_DIR / item['file'].name
            shutil.copy2(item['file'], dst)
            removed_count += 1

    # Copy files to keep
    kept_count = 0
    for json_file in to_keep:
        dst = CLEAN_DIR / json_file.name
        shutil.copy2(json_file, dst)
        kept_count += 1

    print(f"{'='*80}")
    print("Complete!")
    print(f"{'='*80}\n")
    print(f"Original dataset: {len(all_files)}")
    print(f"Removed: {removed_count}")
    print(f"Kept: {kept_count}")
    print(f"\nClean dataset location: {CLEAN_DIR}")
    print(f"Total high-quality annotations: {kept_count}")

    # Save removal report
    report = {
        'total_original': len(all_files),
        'total_removed': removed_count,
        'total_kept': kept_count,
        'removed_by_category': {
            cat: len(items) for cat, items in to_remove.items()
        },
        'removed_files': {
            cat: [{'file_id': item['file_id'], 'url': item['url']}
                  for item in items]
            for cat, items in to_remove.items()
        }
    }

    report_file = DATA_DIR / "category_removal_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nRemoval report saved to: {report_file}")

    print(f"\n{'='*80}")
    print("Next Steps")
    print(f"{'='*80}\n")
    print(f"1. Update benchmark script to use: {CLEAN_DIR}")
    print(f"2. Run benchmark on clean dataset")
    print(f"3. Your final dataset has {kept_count} diverse, high-quality web pages")

if __name__ == "__main__":
    main()
