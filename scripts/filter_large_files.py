"""
Filter out files larger than 1MB from both subsets
"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
SUBSET_FILE = DATA_DIR / "metadata_subset_2000.csv"
REMAINING_FILE = DATA_DIR / "metadata_remaining_404.csv"
SUBSET_FILTERED = DATA_DIR / "metadata_subset_filtered.csv"
REMAINING_FILTERED = DATA_DIR / "metadata_remaining_filtered.csv"

MAX_SIZE = 1_000_000  # 1MB

def filter_subset(input_file, output_file):
    """Filter a metadata CSV to exclude files > 1MB"""

    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter by file size
    kept = []
    removed = []

    for row in rows:
        file_id = int(row['file_id'])
        html_file = HTML_DIR / f"{file_id:04d}.html"

        if html_file.exists():
            size = html_file.stat().st_size
            if size <= MAX_SIZE:
                kept.append(row)
            else:
                removed.append({
                    'file_id': file_id,
                    'size': size,
                    'url': row['url']
                })
        else:
            kept.append(row)  # Keep if file doesn't exist (will be caught later)

    # Write filtered subset
    if kept:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(kept)

    return kept, removed

def main():
    """Filter both subsets"""

    print(f"\n{'='*80}")
    print("Filtering Large Files (> 1MB)")
    print(f"{'='*80}\n")

    # Filter subset_2000
    print("Processing metadata_subset_2000.csv...")
    kept_subset, removed_subset = filter_subset(SUBSET_FILE, SUBSET_FILTERED)

    print(f"  Original: 2,000 files")
    print(f"  Kept: {len(kept_subset)} files")
    print(f"  Removed: {len(removed_subset)} files")

    # Filter remaining_404
    print("\nProcessing metadata_remaining_404.csv...")
    kept_remaining, removed_remaining = filter_subset(REMAINING_FILE, REMAINING_FILTERED)

    print(f"  Original: 404 files")
    print(f"  Kept: {len(kept_remaining)} files")
    print(f"  Removed: {len(removed_remaining)} files")

    # Summary
    total_kept = len(kept_subset) + len(kept_remaining)
    total_removed = len(removed_subset) + len(removed_remaining)

    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}\n")
    print(f"Original total: 2,404 files")
    print(f"Filtered total: {total_kept} files")
    print(f"Removed total: {total_removed} files ({total_removed/2404*100:.1f}%)")

    # Show removed files
    if total_removed > 0:
        print(f"\nRemoved files (> 1MB):")
        all_removed = removed_subset + removed_remaining
        all_removed.sort(key=lambda x: x['size'], reverse=True)

        for item in all_removed[:20]:
            print(f"  {item['file_id']:04d}: {item['size']:,} bytes ({item['size']//1024}KB)")
            print(f"    {item['url'][:70]}")

        if len(all_removed) > 20:
            print(f"  ... and {len(all_removed) - 20} more")

    # New size stats
    print(f"\n{'='*80}")
    print("New Dataset Statistics")
    print(f"{'='*80}\n")

    # Calculate new stats
    sizes = []
    for row in kept_subset + kept_remaining:
        file_id = int(row['file_id'])
        html_file = HTML_DIR / f"{file_id:04d}.html"
        if html_file.exists():
            sizes.append(html_file.stat().st_size)

    sizes.sort()

    print(f"Files: {len(sizes)}")
    print(f"Average size: {sum(sizes)//len(sizes):,} bytes ({sum(sizes)//len(sizes)//1024}KB)")
    print(f"Median size: {sizes[len(sizes)//2]:,} bytes ({sizes[len(sizes)//2]//1024}KB)")
    print(f"Max size: {max(sizes):,} bytes ({max(sizes)//1024}KB)")
    print(f"\nFiles over 100KB: {sum(1 for s in sizes if s > 100_000)}")
    print(f"Files over 500KB: {sum(1 for s in sizes if s > 500_000)}")

    print(f"\n{'='*80}")
    print("Output Files")
    print(f"{'='*80}\n")
    print(f"Filtered subset: {SUBSET_FILTERED}")
    print(f"Filtered remaining: {REMAINING_FILTERED}")

    print(f"\n{'='*80}")
    print("Next Steps")
    print(f"{'='*80}\n")
    print(f"1. Review removed files above")
    print(f"2. Update annotate_batch.py to use: {SUBSET_FILTERED.name}")
    print(f"3. Update annotate_remaining.py to use: {REMAINING_FILTERED.name}")
    print(f"4. Remove truncation from both scripts")

if __name__ == "__main__":
    main()
