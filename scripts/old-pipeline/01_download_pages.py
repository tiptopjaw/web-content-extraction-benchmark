"""
Download HTML files from URL list
Saves files as sequential numbered HTML files (0001.html, 0002.html, etc.)
Creates metadata.csv mapping file IDs to URLs and categories
"""
import asyncio
import csv
import json
from pathlib import Path
from datetime import datetime
import httpx
from tqdm.asyncio import tqdm
import hashlib

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
URLS_FILE = DATA_DIR / "urls.txt"
METADATA_FILE = DATA_DIR / "metadata.csv"
PROGRESS_FILE = DATA_DIR / "download_progress.json"

# Configuration
CONCURRENT_DOWNLOADS = 10  # Parallel downloads
TIMEOUT = 30.0  # Seconds
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def load_urls():
    """Load URLs from file"""
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls


def load_progress():
    """Load download progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "last_id": 0}


def save_progress(progress):
    """Save download progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def url_to_hash(url):
    """Generate short hash from URL for deduplication"""
    return hashlib.md5(url.encode()).hexdigest()[:8]


async def download_url(client, url, file_id, semaphore):
    """Download a single URL and save HTML"""
    async with semaphore:
        file_path = HTML_DIR / f"{file_id:04d}.html"

        # Skip if already downloaded
        if file_path.exists():
            return {
                "file_id": file_id,
                "url": url,
                "status": "skipped",
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "downloaded_at": datetime.now().isoformat()
            }

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }

        try:
            response = await client.get(url, headers=headers, follow_redirects=True)

            if response.status_code == 200:
                # Save HTML
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)

                return {
                    "file_id": file_id,
                    "url": url,
                    "final_url": str(response.url),
                    "status": "success",
                    "status_code": response.status_code,
                    "file_path": str(file_path),
                    "file_size": len(response.text),
                    "content_type": response.headers.get("content-type", ""),
                    "downloaded_at": datetime.now().isoformat(),
                    "url_hash": url_to_hash(url)
                }
            else:
                return {
                    "file_id": file_id,
                    "url": url,
                    "status": "failed",
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}",
                    "downloaded_at": datetime.now().isoformat()
                }

        except asyncio.TimeoutError:
            return {
                "file_id": file_id,
                "url": url,
                "status": "failed",
                "error": "Timeout",
                "downloaded_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "file_id": file_id,
                "url": url,
                "status": "failed",
                "error": str(e)[:200],
                "downloaded_at": datetime.now().isoformat()
            }


async def download_all_urls(urls, start_id=1):
    """Download all URLs with progress tracking"""

    print(f"\n{'='*80}")
    print(f"Modern Content Benchmark - HTML Downloader")
    print(f"{'='*80}\n")
    print(f"Total URLs: {len(urls)}")
    print(f"Output directory: {HTML_DIR}")
    print(f"Concurrent downloads: {CONCURRENT_DOWNLOADS}")
    print(f"Timeout: {TIMEOUT}s\n")

    # Create output directory
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    # Load progress
    progress = load_progress()
    completed_urls = set(progress.get("completed", []))

    # Prepare download tasks
    semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)
    results = []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = []
        file_id = start_id

        for url in urls:
            if url in completed_urls:
                continue
            tasks.append(download_url(client, url, file_id, semaphore))
            file_id += 1

        # Download with progress bar
        if tasks:
            print(f"Starting download of {len(tasks)} URLs...\n")
            results = []
            for coro in tqdm.as_completed(tasks, total=len(tasks), desc="Downloading"):
                result = await coro
                results.append(result)

                # Update progress every 50 downloads
                if len(results) % 50 == 0:
                    successful = [r for r in results if r["status"] == "success"]
                    failed = [r for r in results if r["status"] == "failed"]
                    print(f"\n  Progress: {len(results)}/{len(tasks)} | Success: {len(successful)} | Failed: {len(failed)}")

    return results


def save_metadata(results):
    """Save metadata CSV"""

    fieldnames = [
        "file_id", "url", "final_url", "status", "status_code",
        "file_path", "file_size", "content_type", "error",
        "downloaded_at", "url_hash"
    ]

    with open(METADATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✓ Metadata saved to: {METADATA_FILE}")


def generate_report(results):
    """Generate download summary report"""

    total = len(results)
    successful = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] == "failed"]

    total_size = sum(r.get("file_size", 0) for r in successful)
    avg_size = total_size / len(successful) if successful else 0

    print(f"\n{'='*80}")
    print(f"Download Complete!")
    print(f"{'='*80}\n")
    print(f"✓ Total URLs: {total}")
    print(f"✓ Successful: {len(successful)}")
    print(f"✓ Skipped (already downloaded): {len(skipped)}")
    print(f"✓ Failed: {len(failed)}")
    print(f"✓ Success rate: {len(successful)/total*100:.1f}%")
    print(f"\n✓ Total size: {total_size/1024/1024:.1f} MB")
    print(f"✓ Average file size: {avg_size/1024:.1f} KB")

    if failed:
        print(f"\n⚠ Failed downloads:")
        error_counts = {}
        for f in failed[:10]:  # Show first 10
            error = f.get("error", "Unknown")
            error_counts[error] = error_counts.get(error, 0) + 1
            print(f"  - {f['url'][:60]}... ({error})")

        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

        print(f"\n Error summary:")
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error}: {count}")


async def main():
    """Main download function"""

    # Load URLs
    urls = load_urls()
    print(f"Loaded {len(urls)} URLs from {URLS_FILE}")

    # Download all
    results = await download_all_urls(urls)

    # Save metadata
    save_metadata(results)

    # Generate report
    generate_report(results)

    print(f"\n✅ All done! HTML files saved to: {HTML_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
