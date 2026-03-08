"""
Apply additional URL filtering patterns
"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Input files (current quality-filtered)
SUBSET_QUALITY = DATA_DIR / "metadata_subset_quality.csv"
REMAINING_QUALITY = DATA_DIR / "metadata_remaining_quality.csv"

# Output files (with additional filters)
SUBSET_FINAL = DATA_DIR / "metadata_subset_final.csv"
REMAINING_FINAL = DATA_DIR / "metadata_remaining_final.csv"

# Additional patterns to exclude
ADDITIONAL_PATTERNS = {
    'Contains /solutions/': ['/solutions/'],
    'Contains /services/': ['/services/'],
    'Ends with /latest-news': ['/latest-news/', '/latest-news'],
    'Ends with /news': ['/news/', '/news']
}

def should_exclude(url):
    """Check if URL matches additional exclusion patterns"""
    url_lower = url.lower()

    # Check contains patterns
    if '/solutions/' in url_lower:
        return 'Contains /solutions/'
    if '/services/' in url_lower:
        return 'Contains /services/'

    # Check ending patterns
    url_stripped = url_lower.rstrip('/')
    if url_stripped.endswith('/latest-news'):
        return 'Ends with /latest-news'
    if url_stripped.endswith('/news'):
        return 'Ends with /news'

    return None

def filter_additional(input_file, output_file):
    """Apply additional filters to a metadata file"""

    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    kept = []
    removed = []

    for row in rows:
        url = row['url']
        reason = should_exclude(url)

        if reason:
            removed.append({
                'file_id': row['file_id'],
                'url': url,
                'reason': reason
            })
        else:
            kept.append(row)

    # Write filtered subset
    if kept:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(kept)

    return kept, removed

def main():
    """Apply additional filters to both datasets"""

    print(f"\n{'='*80}")
    print("Applying Additional URL Filters")
    print(f"{'='*80}\n")
    print("Additional patterns:")
    print("  - Contains /solutions/")
    print("  - Contains /services/")
    print("  - Ends with /latest-news")
    print("  - Ends with /news")
    print()

    # Filter subset
    print("Processing metadata_subset_quality.csv...")
    kept_subset, removed_subset = filter_additional(SUBSET_QUALITY, SUBSET_FINAL)

    print(f"  Original: 1,704 files")
    print(f"  Kept: {len(kept_subset)} files")
    print(f"  Removed: {len(removed_subset)} files")

    # Filter remaining
    print("\nProcessing metadata_remaining_quality.csv...")
    kept_remaining, removed_remaining = filter_additional(REMAINING_QUALITY, REMAINING_FINAL)

    print(f"  Original: 358 files")
    print(f"  Kept: {len(kept_remaining)} files")
    print(f"  Removed: {len(removed_remaining)} files")

    # Summary
    total_kept = len(kept_subset) + len(kept_remaining)
    total_removed = len(removed_subset) + len(removed_remaining)

    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}\n")
    print(f"Previous total: 2,062 files")
    print(f"New total: {total_kept} files")
    print(f"Additional removed: {total_removed} files ({total_removed/2062*100:.1f}%)")

    # Breakdown by reason
    from collections import Counter
    all_removed = removed_subset + removed_remaining
    reason_counts = Counter(r['reason'] for r in all_removed)

    print(f"\nRemoval reasons:")
    for reason, count in reason_counts.most_common():
        print(f"  {reason:30} {count:4} files")

    # Show samples
    if all_removed:
        print(f"\nSample removed URLs (first 15):")
        for item in all_removed[:15]:
            print(f"  {item['file_id']}: {item['reason']}")
            print(f"    {item['url'][:75]}")

        if len(all_removed) > 15:
            print(f"  ... and {len(all_removed) - 15} more")

    print(f"\n{'='*80}")
    print("Output Files")
    print(f"{'='*80}\n")
    print(f"Final subset: {SUBSET_FINAL}")
    print(f"Final remaining: {REMAINING_FINAL}")
    print(f"\nTotal files ready for annotation: {total_kept}")

    # Cost estimate
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
    print(f"1. Review removed URLs above")
    print(f"2. Update annotate_batch.py to use: {SUBSET_FINAL.name}")
    print(f"3. Update annotate_remaining.py to use: {REMAINING_FINAL.name}")

if __name__ == "__main__":
    main()
