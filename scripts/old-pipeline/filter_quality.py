"""
Filter out problematic annotations based on quality analysis
"""
import json
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
QUALITY_REPORT = DATA_DIR / "quality_analysis.json"
FILTERED_DIR = DATA_DIR / "ground_truth_filtered"
REMOVED_DIR = DATA_DIR / "ground_truth_removed"

# Quality thresholds
MIN_CONTENT_LENGTH = 500
MAX_NAV_KEYWORDS = 10
HUB_PAGE_MIN_LENGTH = 2000

def main():
    """Filter problematic annotations"""

    print(f"\n{'='*80}")
    print("Filtering Problematic Annotations")
    print(f"{'='*80}\n")

    # Load quality analysis
    if not QUALITY_REPORT.exists():
        print("Error: quality_analysis.json not found. Run analyze_annotation_quality.py first.")
        return

    with open(QUALITY_REPORT) as f:
        problematic = json.load(f)

    # Create filtered directory
    FILTERED_DIR.mkdir(exist_ok=True)
    REMOVED_DIR.mkdir(exist_ok=True)

    # Categorize issues
    files_to_remove = set()

    for item in problematic:
        file_id = item['file_id']
        issues = item['issues']

        # Remove if:
        # 1. Very short content (< 500 chars)
        # 2. Hub page with short content
        # 3. High boilerplate (>50% without snippets found)

        should_remove = False
        reasons = []

        for issue in issues:
            if 'SHORT_CONTENT' in issue:
                should_remove = True
                reasons.append("Short content")

            if 'HUB_PAGE_PATTERN' in issue:
                should_remove = True
                reasons.append("Hub/directory page")

            if 'BOILERPLATE_IN_CONTENT' in issue:
                # Check if >50% of without snippets are in content
                parts = issue.split('(')[1].split('/')
                if len(parts) >= 2:
                    found = int(parts[0])
                    total = int(parts[1].split()[0])
                    if found / total > 0.5:
                        should_remove = True
                        reasons.append("High boilerplate")

        if should_remove:
            files_to_remove.add((file_id, ', '.join(reasons)))

    print(f"Files to remove: {len(files_to_remove)}")
    print(f"\nCriteria:")
    print(f"  - Content length < {MIN_CONTENT_LENGTH} chars")
    print(f"  - Hub/directory page patterns")
    print(f"  - >50% of 'without' snippets found in content\n")

    # Show sample of files being removed
    print("Sample files being removed (first 20):")
    for i, (file_id, reasons) in enumerate(sorted(files_to_remove)[:20]):
        print(f"  {file_id}: {reasons}")

    if len(files_to_remove) > 20:
        print(f"  ... and {len(files_to_remove) - 20} more\n")

    # Copy files
    all_annotations = list(GROUND_TRUTH_DIR.glob("*.json"))
    removed_count = 0
    kept_count = 0

    for json_file in all_annotations:
        file_id = json_file.stem

        # Check if should be removed
        is_removed = any(fid == file_id for fid, _ in files_to_remove)

        if is_removed:
            # Move to removed directory
            shutil.copy2(json_file, REMOVED_DIR / json_file.name)
            removed_count += 1
        else:
            # Copy to filtered directory
            shutil.copy2(json_file, FILTERED_DIR / json_file.name)
            kept_count += 1

    print(f"\n{'='*80}")
    print("Filtering Complete")
    print(f"{'='*80}\n")
    print(f"Original annotations: {len(all_annotations)}")
    print(f"Removed: {removed_count}")
    print(f"Kept: {kept_count}")
    print(f"\nFiltered annotations saved to: {FILTERED_DIR}")
    print(f"Removed annotations saved to: {REMOVED_DIR}")
    print(f"\n✓ Ready for benchmarking!")
    print(f"\nNext step:")
    print(f"  Update scripts/03_run_benchmark.py to use:")
    print(f"  GROUND_TRUTH_DIR = BASE_DIR / \"data\" / \"ground_truth_filtered\"")

if __name__ == "__main__":
    main()
