"""
Filter out problematic HTML files that won't be useful for benchmarking
- Files under 10KB (likely SPAs, error pages, firewalls)
- Files with specific patterns (Incapsula, CloudFlare blocks, etc.)
"""
import os
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
METADATA_FILE = DATA_DIR / "metadata.csv"
FILTERED_METADATA = DATA_DIR / "metadata_filtered.csv"

MIN_SIZE = 10240  # 10KB minimum

def analyze_files():
    """Analyze HTML files and filter problematic ones"""

    # Load metadata
    metadata = {}
    with open(METADATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'] == 'success':
                metadata[int(row['file_id'])] = row

    print(f"\n{'='*80}")
    print("Filtering Problematic HTML Files")
    print(f"{'='*80}\n")
    print(f"Total successful downloads: {len(metadata)}")

    # Analyze files
    too_small = []
    good_files = []

    for file_id, meta in sorted(metadata.items()):
        html_file = HTML_DIR / f"{file_id:04d}.html"

        if not html_file.exists():
            continue

        size = html_file.stat().st_size

        # Filter by size
        if size < MIN_SIZE:
            too_small.append({
                'file_id': file_id,
                'size': size,
                'url': meta['url'],
                'reason': f'Too small ({size} bytes)'
            })
        else:
            # Check for known blocking patterns
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # Read first 2KB

            is_blocked = False
            reason = None

            # Incapsula/Imperva firewall
            if 'Incapsula' in content or '_Incapsula_Resource' in content:
                is_blocked = True
                reason = 'Incapsula firewall block'

            # Cloudflare challenge
            elif 'Checking your browser' in content or 'cf-browser-verification' in content:
                is_blocked = True
                reason = 'Cloudflare challenge'

            # Empty body SPAs (React, Vue, Angular apps with no SSR)
            elif '<div id="root"></div>' in content or '<div id="app"></div>' in content:
                # Check if there's actual content beyond the SPA div
                if len(content) < 3000:  # Very minimal HTML
                    is_blocked = True
                    reason = 'JavaScript SPA with no server-side rendering'

            if is_blocked:
                too_small.append({
                    'file_id': file_id,
                    'size': size,
                    'url': meta['url'],
                    'reason': reason
                })
            else:
                good_files.append(meta)

    # Report
    print(f"\n✓ Good files: {len(good_files)}")
    print(f"✗ Filtered out: {len(too_small)}")
    print(f"  - Under 10KB: {len([f for f in too_small if 'Too small' in f['reason']])}")
    print(f"  - Firewall blocks: {len([f for f in too_small if 'firewall' in f['reason'].lower()])}")
    print(f"  - Cloudflare: {len([f for f in too_small if 'Cloudflare' in f['reason']])}")
    print(f"  - SPAs: {len([f for f in too_small if 'SPA' in f['reason']])}")

    # Show examples
    print(f"\n📋 Examples of filtered files:")
    for item in too_small[:10]:
        print(f"  - {item['url'][:60]}... ({item['reason']})")

    # Save filtered metadata
    with open(FILTERED_METADATA, 'w', newline='', encoding='utf-8') as f:
        if good_files:
            fieldnames = good_files[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(good_files)

    print(f"\n✓ Filtered metadata saved to: {FILTERED_METADATA}")
    print(f"✓ Good files for annotation: {len(good_files)}")

    return good_files, too_small


if __name__ == "__main__":
    good_files, filtered = analyze_files()
