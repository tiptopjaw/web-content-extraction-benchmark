"""
Build a clean benchmark package with sequential IDs (0001-0500).

Reads the 500 verified benchmark file IDs, copies HTML and ground truth files
into a new benchmark/ directory with sequential numbering, and creates an
ID mapping file for traceability.

Original data/ directory is left untouched.
"""
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
BENCHMARK_DIR = BASE_DIR / "benchmark"

HTML_SRC = DATA_DIR / "html_files"
GT_SRC = DATA_DIR / "ground_truth"
VERIFIED_FILE = DATA_DIR / "verified_benchmark_files.json"

HTML_DST = BENCHMARK_DIR / "html"
GT_DST = BENCHMARK_DIR / "ground-truth"
MAPPING_FILE = BENCHMARK_DIR / "id-mapping.json"


def build():
    # Load verified IDs (already sorted)
    with open(VERIFIED_FILE) as f:
        old_ids = json.load(f)

    print(f"Found {len(old_ids)} verified benchmark files")

    # Create output directories
    if BENCHMARK_DIR.exists():
        shutil.rmtree(BENCHMARK_DIR)
    HTML_DST.mkdir(parents=True)
    GT_DST.mkdir(parents=True)

    # Build sequential mapping
    id_mapping = {}  # old_id -> new_id
    for i, old_id in enumerate(old_ids, start=1):
        new_id = f"{i:04d}"
        id_mapping[old_id] = new_id

    # Copy files
    missing = []
    for old_id, new_id in id_mapping.items():
        # Copy HTML
        html_src = HTML_SRC / f"{old_id}.html"
        if not html_src.exists():
            missing.append(f"HTML: {old_id}")
            continue
        shutil.copy2(html_src, HTML_DST / f"{new_id}.html")

        # Copy and update ground truth JSON
        gt_src = GT_SRC / f"{old_id}.json"
        if not gt_src.exists():
            missing.append(f"GT: {old_id}")
            continue

        with open(gt_src, encoding="utf-8") as f:
            gt_data = json.load(f)

        # Update file_id to new sequential ID
        gt_data["file_id"] = new_id

        with open(GT_DST / f"{new_id}.json", "w", encoding="utf-8") as f:
            json.dump(gt_data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    # Save ID mapping
    with open(MAPPING_FILE, "w") as f:
        json.dump(id_mapping, f, indent=2)
        f.write("\n")

    # Report
    if missing:
        print(f"\nWARNING: {len(missing)} missing files:")
        for m in missing:
            print(f"  {m}")

    html_count = len(list(HTML_DST.glob("*.html")))
    gt_count = len(list(GT_DST.glob("*.json")))
    print(f"\nBenchmark package built in: {BENCHMARK_DIR}")
    print(f"  HTML files:         {html_count}")
    print(f"  Ground truth files: {gt_count}")
    print(f"  ID mapping entries: {len(id_mapping)}")


if __name__ == "__main__":
    build()
