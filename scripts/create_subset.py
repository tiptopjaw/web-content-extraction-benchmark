"""
Create a random subset of 2,000 files from the 2,404 good files
"""
import csv
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
FILTERED_METADATA = DATA_DIR / "metadata_filtered.csv"
SUBSET_METADATA = DATA_DIR / "metadata_subset_2000.csv"

def create_subset(total_files=2000):
    """Create random subset of files"""

    # Load filtered metadata
    with open(FILTERED_METADATA, 'r') as f:
        reader = csv.DictReader(f)
        all_files = list(reader)

    print(f"\n{'='*80}")
    print("Creating Subset for Annotation")
    print(f"{'='*80}\n")
    print(f"Total good files: {len(all_files)}")
    print(f"Target subset: {total_files}")

    # Random sample
    random.seed(42)  # For reproducibility
    subset = random.sample(all_files, total_files)

    # Sort by file_id for easier processing
    subset.sort(key=lambda x: int(x['file_id']))

    # Save subset
    with open(SUBSET_METADATA, 'w', newline='', encoding='utf-8') as f:
        fieldnames = subset[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(subset)

    print(f"\n✓ Subset created: {len(subset)} files")
    print(f"✓ File ID range: {subset[0]['file_id']} to {subset[-1]['file_id']}")
    print(f"✓ Saved to: {SUBSET_METADATA}")

    # Show batch info
    print(f"\n📊 Batch Plan (500 files each):")
    for i in range(0, total_files, 500):
        batch_num = i // 500 + 1
        start_idx = i
        end_idx = min(i + 500, total_files)
        batch_files = subset[start_idx:end_idx]
        start_id = batch_files[0]['file_id']
        end_id = batch_files[-1]['file_id']
        print(f"  Batch {batch_num}: Files {start_idx+1}-{end_idx} (IDs: {start_id} to {end_id})")

    return subset

if __name__ == "__main__":
    subset = create_subset(2000)
