#!/usr/bin/env python3
"""
Build the distributable benchmark package.

This script:
1. Converts individual ground truth files to single ground-truth.json
2. Compresses HTML files to gzip format in html/ directory
3. Creates example output file
4. Copies evaluate.py and other needed files

Run from the repository root:
    python scripts/build_benchmark_package.py

Output is created in benchmark-package/ directory.
"""

import gzip
import json
import shutil
from pathlib import Path
from tqdm import tqdm

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
CATEGORY_REMOVAL_REPORT = DATA_DIR / "category_removal_report.json"
DIRECTORY_EXCLUSION_REPORT = DATA_DIR / "directory_exclusion_report.json"

OUTPUT_DIR = BASE_DIR / "benchmark-package"


def load_excluded_file_ids() -> set:
    """Load file IDs that should be excluded from the benchmark."""
    excluded = set()

    if CATEGORY_REMOVAL_REPORT.exists():
        with open(CATEGORY_REMOVAL_REPORT, 'r') as f:
            report = json.load(f)
            for category, files in report.get('removed_files', {}).items():
                for file_info in files:
                    excluded.add(file_info['file_id'])

    if DIRECTORY_EXCLUSION_REPORT.exists():
        with open(DIRECTORY_EXCLUSION_REPORT, 'r') as f:
            report = json.load(f)
            for file_info in report.get('excluded_files', []):
                excluded.add(file_info['file_id'])

    return excluded


def build_ground_truth_json(excluded_ids: set) -> dict:
    """Convert individual ground truth files to single dictionary."""
    ground_truth = {}

    gt_files = sorted(GROUND_TRUTH_DIR.glob("*.json"))
    print(f"Processing {len(gt_files)} ground truth files...")

    for gt_file in tqdm(gt_files, desc="Building ground-truth.json"):
        file_id = gt_file.stem

        # Skip excluded files
        if file_id in excluded_ids:
            continue

        with open(gt_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        gt = data.get('ground_truth', {})

        # Convert to benchmark format
        entry = {
            'articleBody': gt.get('main_content', ''),
            'url': data.get('url', ''),
        }

        # Include optional fields for snippet evaluation
        if gt.get('with'):
            entry['with'] = gt['with']
        if gt.get('without'):
            entry['without'] = gt['without']

        # Include metadata (optional, for reference)
        if gt.get('title'):
            entry['title'] = gt['title']
        if gt.get('author'):
            entry['author'] = gt['author']
        if gt.get('publish_date'):
            entry['publish_date'] = gt['publish_date']

        ground_truth[file_id] = entry

    return ground_truth


def compress_html_files(ground_truth_ids: set):
    """Compress HTML files to gzip format."""
    html_output_dir = OUTPUT_DIR / "html"
    html_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nCompressing {len(ground_truth_ids)} HTML files...")

    for file_id in tqdm(sorted(ground_truth_ids), desc="Compressing HTML"):
        html_file = HTML_DIR / f"{file_id}.html"

        if not html_file.exists():
            print(f"Warning: HTML file not found: {html_file}")
            continue

        output_file = html_output_dir / f"{file_id}.html.gz"

        with open(html_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb', compresslevel=9) as f_out:
                f_out.write(f_in.read())


def create_example_output(ground_truth: dict):
    """Create example output file showing expected format."""
    output_dir = OUTPUT_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Take first 3 entries as example
    example_ids = list(ground_truth.keys())[:3]
    example = {}

    for file_id in example_ids:
        # Show format with placeholder text
        example[file_id] = {
            'articleBody': f"[Your extracted content for {file_id} goes here...]"
        }

    example_file = output_dir / "_example_format.json"
    with open(example_file, 'w', encoding='utf-8') as f:
        json.dump(example, f, indent=2)

    print(f"\nCreated example output file: {example_file}")


def copy_static_files():
    """Copy evaluate.py and other static files."""
    # Copy evaluate.py
    shutil.copy(BASE_DIR / "evaluate.py", OUTPUT_DIR / "evaluate.py")
    print(f"Copied evaluate.py")


def create_gitignore():
    """Create .gitignore for the output directory."""
    gitignore_content = """# Ignore prediction outputs (users add their own)
output/*.json
!output/_example_format.json

# Python
__pycache__/
*.pyc
"""
    with open(OUTPUT_DIR / ".gitignore", 'w') as f:
        f.write(gitignore_content)
    print("Created .gitignore")


def main():
    print("=" * 60)
    print("Building Benchmark Package")
    print("=" * 60)

    # Create output directory
    if OUTPUT_DIR.exists():
        print(f"\nRemoving existing {OUTPUT_DIR}...")
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # Load exclusions
    excluded_ids = load_excluded_file_ids()
    print(f"\nExcluding {len(excluded_ids)} files based on filters")

    # Build ground truth
    ground_truth = build_ground_truth_json(excluded_ids)
    print(f"Included {len(ground_truth)} files in ground-truth.json")

    # Save ground truth
    gt_output = OUTPUT_DIR / "ground-truth.json"
    with open(gt_output, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)
    print(f"Saved {gt_output}")

    # Compress HTML files
    compress_html_files(set(ground_truth.keys()))

    # Create example output
    create_example_output(ground_truth)

    # Copy static files
    copy_static_files()

    # Create gitignore
    create_gitignore()

    # Calculate sizes
    gt_size = gt_output.stat().st_size / (1024 * 1024)
    html_size = sum(f.stat().st_size for f in (OUTPUT_DIR / "html").glob("*.gz")) / (1024 * 1024)

    print("\n" + "=" * 60)
    print("Package Summary")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Ground truth entries: {len(ground_truth)}")
    print(f"Ground truth size: {gt_size:.1f} MB")
    print(f"HTML files (gzipped): {html_size:.1f} MB")
    print(f"\nPackage is ready in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
