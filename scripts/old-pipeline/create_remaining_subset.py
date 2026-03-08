"""
Create subset of remaining unannotated files
"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
FILTERED_METADATA = DATA_DIR / "metadata_filtered.csv"
SUBSET_FILE = DATA_DIR / "metadata_subset_2000.csv"
REMAINING_SUBSET = DATA_DIR / "metadata_remaining_404.csv"

def main():
    """Create subset of unannotated files"""

    print(f"\n{'='*80}")
    print("Creating Subset of Remaining Unannotated Files")
    print(f"{'='*80}\n")

    # Load all filtered files
    with open(FILTERED_METADATA) as f:
        reader = csv.DictReader(f)
        all_filtered = list(reader)

    # Load already annotated subset
    with open(SUBSET_FILE) as f:
        reader = csv.DictReader(f)
        annotated_subset = list(reader)

    # Get IDs
    annotated_ids = {int(row['file_id']) for row in annotated_subset}

    # Find remaining files
    remaining = [row for row in all_filtered if int(row['file_id']) not in annotated_ids]

    print(f"Total filtered files: {len(all_filtered)}")
    print(f"Already annotated: {len(annotated_subset)}")
    print(f"Remaining to annotate: {len(remaining)}")

    # Sort by file_id
    remaining.sort(key=lambda x: int(x['file_id']))

    print(f"\nFile ID range: {remaining[0]['file_id']} to {remaining[-1]['file_id']}")

    # Save remaining subset
    with open(REMAINING_SUBSET, 'w', newline='', encoding='utf-8') as f:
        fieldnames = remaining[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining)

    print(f"\n✓ Remaining subset saved to: {REMAINING_SUBSET}")
    print(f"\n{'='*80}")
    print("Next Step")
    print(f"{'='*80}\n")
    print(f"Annotate the remaining files:")
    print(f"  python scripts/annotate_remaining.py --api-key YOUR_DEEPSEEK_API_KEY")
    print(f"\nEstimated:")
    print(f"  Files: {len(remaining)}")
    print(f"  Cost: ~${len(remaining) * 0.007:.2f}")
    print(f"  Time: ~{len(remaining) * 4 / 60:.0f} minutes")

if __name__ == "__main__":
    main()
