"""
Save list of final URLs that will be annotated
"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"

# Final filtered files (after all filters)
FINAL_SUBSET = DATA_DIR / "metadata_subset_final.csv"
FINAL_REMAINING = DATA_DIR / "metadata_remaining_final.csv"

# Output file
OUTPUT_FILE = DATA_DIR / "final_urls_to_annotate.csv"

def main():
    final_urls = []

    # Load subset
    with open(FINAL_SUBSET) as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_id = row['file_id']
            url = row['url']
            html_file = HTML_DIR / f"{int(file_id):04d}.html"

            final_urls.append({
                'file_id': file_id,
                'url': url,
                'file_size_kb': html_file.stat().st_size // 1024 if html_file.exists() else 'N/A',
                'source': 'subset'
            })

    # Load remaining
    with open(FINAL_REMAINING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_id = row['file_id']
            url = row['url']
            html_file = HTML_DIR / f"{int(file_id):04d}.html"

            final_urls.append({
                'file_id': file_id,
                'url': url,
                'file_size_kb': html_file.stat().st_size // 1024 if html_file.exists() else 'N/A',
                'source': 'remaining'
            })

    # Sort by file_id
    final_urls.sort(key=lambda x: int(x['file_id']))

    # Write to CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['file_id', 'url', 'file_size_kb', 'source']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_urls)

    print(f"\n{'='*80}")
    print("Final URLs to Annotate - Saved")
    print(f"{'='*80}\n")
    print(f"Total files: {len(final_urls)}")
    print(f"  From subset: {sum(1 for u in final_urls if u['source'] == 'subset')}")
    print(f"  From remaining: {sum(1 for u in final_urls if u['source'] == 'remaining')}")
    print(f"\nOutput file: {OUTPUT_FILE}")
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
