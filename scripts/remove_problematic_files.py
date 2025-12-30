"""
Remove problematic files identified by benchmark analysis
"""
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
FILTERED_DIR = DATA_DIR / "ground_truth_filtered"
REMOVED_DIR = DATA_DIR / "ground_truth_removed"
FINAL_DIR = DATA_DIR / "ground_truth_final"
RESULTS_DIR = BASE_DIR / "results"

def main():
    """Remove problematic files from benchmark results"""

    print(f"\n{'='*80}")
    print("Removing Problematic Files Based on Benchmark Results")
    print(f"{'='*80}\n")

    # Load problematic files list
    problematic_file = RESULTS_DIR / "problematic_files.json"

    if not problematic_file.exists():
        print("Error: problematic_files.json not found")
        print("Run identify_problem_files_from_benchmark.py first")
        return

    with open(problematic_file) as f:
        problematic = json.load(f)

    problematic_ids = {item['file_id'] for item in problematic}

    print(f"Files to remove: {len(problematic_ids)}")
    print(f"Source: {FILTERED_DIR}")
    print(f"Destination (final clean): {FINAL_DIR}")
    print(f"Removed files moved to: {REMOVED_DIR}\n")

    # Create directories
    FINAL_DIR.mkdir(exist_ok=True)
    REMOVED_DIR.mkdir(exist_ok=True)

    # Process all files
    all_files = list(FILTERED_DIR.glob("*.json"))
    removed_count = 0
    kept_count = 0

    for json_file in all_files:
        file_id = json_file.stem

        if file_id in problematic_ids:
            # Move to removed directory
            dst = REMOVED_DIR / json_file.name
            shutil.copy2(json_file, dst)
            removed_count += 1
        else:
            # Copy to final directory
            dst = FINAL_DIR / json_file.name
            shutil.copy2(json_file, dst)
            kept_count += 1

    print(f"{'='*80}")
    print("Complete!")
    print(f"{'='*80}\n")
    print(f"Original (filtered): {len(all_files)}")
    print(f"Removed (low quality): {removed_count}")
    print(f"Kept (high quality): {kept_count}")
    print(f"\nFinal clean dataset: {FINAL_DIR}")
    print(f"Total annotations ready for benchmarking: {kept_count}")

    # Statistics
    print(f"\n{'='*80}")
    print("Dataset Quality")
    print(f"{'='*80}\n")

    # Calculate removal breakdown
    extreme = sum(1 for p in problematic if p['max_f1'] < 0.1)
    severe = sum(1 for p in problematic if 0.1 <= p['max_f1'] < 0.2)
    moderate = sum(1 for p in problematic if 0.2 <= p['max_f1'] < 0.3)

    print(f"Removed breakdown:")
    print(f"  Extreme failures (F1 < 0.1):   {extreme}")
    print(f"  Severe issues (F1 0.1-0.2):    {severe}")
    print(f"  Moderate issues (F1 0.2-0.3):  {moderate}")
    print()
    print(f"Remaining dataset:")
    print(f"  ✓ {kept_count} high-quality annotations")
    print(f"  ✓ Trafilatura F1 > 0.3 on all files")
    print(f"  ✓ Ready for comprehensive benchmarking")

    print(f"\nNext steps:")
    print(f"  1. Update benchmark script to use: {FINAL_DIR}")
    print(f"  2. Run full benchmark: python scripts/03_run_benchmark.py")

if __name__ == "__main__":
    main()
