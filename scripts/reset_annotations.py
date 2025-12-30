"""
Backup and delete all existing annotations to prepare for re-annotation
"""
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
GROUND_TRUTH_CLEAN = DATA_DIR / "ground_truth_clean"
GROUND_TRUTH_MERGED = DATA_DIR / "ground_truth_merged"
GROUND_TRUTH_REMOVED = DATA_DIR / "ground_truth_removed"

# Backup directory with timestamp
BACKUP_DIR = DATA_DIR / f"annotations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def main():
    """Backup and delete all annotations"""

    print(f"\n{'='*80}")
    print("Reset Annotations - Backup and Delete")
    print(f"{'='*80}\n")

    # Count existing annotations
    ground_truth_files = list(GROUND_TRUTH_DIR.glob("*.json")) if GROUND_TRUTH_DIR.exists() else []
    clean_files = list(GROUND_TRUTH_CLEAN.glob("*.json")) if GROUND_TRUTH_CLEAN.exists() else []
    merged_files = list(GROUND_TRUTH_MERGED.glob("*.json")) if GROUND_TRUTH_MERGED.exists() else []
    removed_files = list(GROUND_TRUTH_REMOVED.glob("*.json")) if GROUND_TRUTH_REMOVED.exists() else []

    print("Current annotation state:")
    print(f"  ground_truth/: {len(ground_truth_files)} files")
    print(f"  ground_truth_clean/: {len(clean_files)} files")
    print(f"  ground_truth_merged/: {len(merged_files)} files")
    print(f"  ground_truth_removed/: {len(removed_files)} files")

    total_files = len(ground_truth_files) + len(clean_files) + len(merged_files) + len(removed_files)

    if total_files == 0:
        print("\n✓ No annotations found - already clean!")
        return

    print(f"\nTotal files to backup: {total_files}")
    print(f"Backup location: {BACKUP_DIR}\n")

    # Confirm
    response = input("Proceed with backup and deletion? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Backup ground_truth/
    if ground_truth_files:
        backup_gt = BACKUP_DIR / "ground_truth"
        backup_gt.mkdir(exist_ok=True)
        for f in ground_truth_files:
            shutil.copy2(f, backup_gt / f.name)
        print(f"✓ Backed up {len(ground_truth_files)} files from ground_truth/")

    # Backup ground_truth_clean/
    if clean_files:
        backup_clean = BACKUP_DIR / "ground_truth_clean"
        backup_clean.mkdir(exist_ok=True)
        for f in clean_files:
            shutil.copy2(f, backup_clean / f.name)
        print(f"✓ Backed up {len(clean_files)} files from ground_truth_clean/")

    # Backup ground_truth_merged/
    if merged_files:
        backup_merged = BACKUP_DIR / "ground_truth_merged"
        backup_merged.mkdir(exist_ok=True)
        for f in merged_files:
            shutil.copy2(f, backup_merged / f.name)
        print(f"✓ Backed up {len(merged_files)} files from ground_truth_merged/")

    # Backup ground_truth_removed/
    if removed_files:
        backup_removed = BACKUP_DIR / "ground_truth_removed"
        backup_removed.mkdir(exist_ok=True)
        for f in removed_files:
            shutil.copy2(f, backup_removed / f.name)
        print(f"✓ Backed up {len(removed_files)} files from ground_truth_removed/")

    # Delete original directories
    if GROUND_TRUTH_DIR.exists():
        shutil.rmtree(GROUND_TRUTH_DIR)
        print(f"\n✓ Deleted ground_truth/")

    if GROUND_TRUTH_CLEAN.exists():
        shutil.rmtree(GROUND_TRUTH_CLEAN)
        print(f"✓ Deleted ground_truth_clean/")

    if GROUND_TRUTH_MERGED.exists():
        shutil.rmtree(GROUND_TRUTH_MERGED)
        print(f"✓ Deleted ground_truth_merged/")

    if GROUND_TRUTH_REMOVED.exists():
        shutil.rmtree(GROUND_TRUTH_REMOVED)
        print(f"✓ Deleted ground_truth_removed/")

    # Recreate ground_truth directory
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Recreated empty ground_truth/")

    print(f"\n{'='*80}")
    print("Reset Complete!")
    print(f"{'='*80}\n")
    print(f"✓ Backed up {total_files} files to: {BACKUP_DIR}")
    print(f"✓ All annotation directories cleared")
    print(f"✓ Ready for fresh annotation with raw HTML")
    print(f"\nNext steps:")
    print(f"  1. Test annotation: python scripts/test_annotation.py --api-key YOUR_KEY --file-id 1")
    print(f"  2. Run batches: python scripts/annotate_batch.py --api-key YOUR_KEY --batch 1")
    print(f"  3. Continue with batches 2-4")

if __name__ == "__main__":
    main()
