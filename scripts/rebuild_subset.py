"""
Rebuild subset by removing problematic files and replacing with clean samples
"""
import csv
import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
FILTERED_METADATA = DATA_DIR / "metadata_filtered.csv"
SUBSET_FILE = DATA_DIR / "metadata_subset_2000.csv"
NEW_SUBSET_FILE = DATA_DIR / "metadata_subset_2000_clean.csv"

# Problematic URL patterns
PROBLEMATIC_PATTERNS = [
    '/education',
    '/topics',
    '/categories',
    '/sitemap',
    '/about-us',
    '/contact-us',
    '/menu',
    '/services',
    '/products',
    '/solutions',
]

def is_problematic_url(url):
    """Check if URL matches problematic patterns"""
    url_lower = url.lower()

    # Check patterns
    for pattern in PROBLEMATIC_PATTERNS:
        if pattern in url_lower:
            # But only if it's a leaf page (ends with pattern or pattern/)
            if url_lower.endswith(pattern) or url_lower.endswith(pattern + '/'):
                return True

    return False

def get_html_file_size(file_id):
    """Get HTML file size in bytes"""
    html_file = HTML_DIR / f"{file_id:04d}.html"
    if html_file.exists():
        return html_file.stat().st_size
    return 0

def get_annotation_content_length(file_id):
    """Get main_content length from annotation"""
    ann_file = GROUND_TRUTH_DIR / f"{file_id:04d}.json"
    if ann_file.exists():
        try:
            with open(ann_file, 'r') as f:
                data = json.load(f)
                return len(data.get('ground_truth', {}).get('main_content', ''))
        except:
            pass
    return None

def main():
    """Rebuild subset"""

    print(f"\n{'='*80}")
    print("Rebuilding Subset - Removing Problematic Files")
    print(f"{'='*80}\n")

    # Load current subset
    with open(SUBSET_FILE, 'r') as f:
        reader = csv.DictReader(f)
        current_subset = list(reader)

    print(f"Current subset size: {len(current_subset)}\n")

    # Identify problematic files
    problematic = []

    for row in current_subset:
        file_id = int(row['file_id'])
        url = row['url']
        reasons = []

        # Check URL pattern
        if is_problematic_url(url):
            reasons.append("Hub/directory page URL")

        # Check HTML file size
        html_size = get_html_file_size(file_id)
        if html_size < 15000:  # Less than 15KB
            reasons.append(f"Small HTML file ({html_size} bytes)")

        # Check annotation content (if exists)
        content_len = get_annotation_content_length(file_id)
        if content_len is not None and content_len < 500:
            reasons.append(f"Short annotation ({content_len} chars)")

        if reasons:
            problematic.append({
                'file_id': file_id,
                'url': url,
                'reasons': reasons
            })

    print(f"Problematic files found: {len(problematic)}")
    print("\nSample problematic files (first 20):")
    for i, p in enumerate(problematic[:20]):
        print(f"  {p['file_id']:04d}: {p['url']}")
        print(f"        Reasons: {', '.join(p['reasons'])}")

    if len(problematic) > 20:
        print(f"  ... and {len(problematic) - 20} more")

    # Load all filtered files
    with open(FILTERED_METADATA, 'r') as f:
        reader = csv.DictReader(f)
        all_files = list(reader)

    # Get file IDs already in subset
    current_ids = {int(row['file_id']) for row in current_subset}
    problematic_ids = {p['file_id'] for p in problematic}

    # Remove problematic from subset
    clean_subset = [row for row in current_subset if int(row['file_id']) not in problematic_ids]

    print(f"\nClean subset size after removal: {len(clean_subset)}")
    print(f"Need to add: {2000 - len(clean_subset)} new files\n")

    # Find replacement candidates
    candidates = []
    for row in all_files:
        file_id = int(row['file_id'])

        # Skip if already in subset
        if file_id in current_ids:
            continue

        # Check if candidate is clean
        url = row['url']
        html_size = get_html_file_size(file_id)

        if is_problematic_url(url):
            continue

        if html_size < 15000:
            continue

        candidates.append(row)

    print(f"Replacement candidates available: {len(candidates)}")

    # Sample replacements
    needed = 2000 - len(clean_subset)

    if len(candidates) < needed:
        print(f"\n⚠ Warning: Only {len(candidates)} candidates available, need {needed}")
        print("  Will use all available candidates")
        replacements = candidates
    else:
        random.seed(42)
        replacements = random.sample(candidates, needed)

    # Combine clean subset + replacements
    new_subset = clean_subset + replacements

    # Sort by file_id
    new_subset.sort(key=lambda x: int(x['file_id']))

    print(f"\nNew subset size: {len(new_subset)}")
    print(f"File ID range: {new_subset[0]['file_id']} to {new_subset[-1]['file_id']}")

    # Save new subset
    with open(NEW_SUBSET_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = new_subset[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_subset)

    print(f"\n✓ New subset saved to: {NEW_SUBSET_FILE}")

    # Show what changed in each batch
    print(f"\n{'='*80}")
    print("Changes by Batch")
    print(f"{'='*80}\n")

    for batch_num in range(1, 5):
        start_idx = (batch_num - 1) * 500
        end_idx = min(start_idx + 500, len(new_subset))

        batch_files = new_subset[start_idx:end_idx]
        batch_file_ids = {int(row['file_id']) for row in batch_files}

        # How many from this batch were problematic?
        old_batch_start = (batch_num - 1) * 500
        old_batch_end = min(old_batch_start + 500, len(current_subset))
        old_batch_ids = {int(current_subset[i]['file_id']) for i in range(old_batch_start, old_batch_end)}

        removed_from_batch = len([p for p in problematic if p['file_id'] in old_batch_ids])

        print(f"Batch {batch_num}: Files {start_idx+1}-{end_idx}")
        print(f"  File IDs: {batch_files[0]['file_id']} to {batch_files[-1]['file_id']}")
        print(f"  Removed: {removed_from_batch} files")
        print(f"  Added: {removed_from_batch} replacement files")

    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}\n")
    print(f"✓ Removed {len(problematic)} problematic files")
    print(f"✓ Added {len(replacements)} clean replacement files")
    print(f"✓ New subset ready with {len(new_subset)} files")
    print(f"\nTo use the new subset for annotation:")
    print(f"  mv {NEW_SUBSET_FILE} {SUBSET_FILE}")
    print(f"\nOr keep both and specify --subset parameter in annotation script")

if __name__ == "__main__":
    main()
