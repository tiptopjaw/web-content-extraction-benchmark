#!/usr/bin/env python3
"""Fetch new web pages and create stub GT files for annotation.

Usage:
    python3 scripts/fetch_new_pages.py urls_product.txt product
    python3 scripts/fetch_new_pages.py urls_file.txt page_type

Input: text file with one URL per line (blank lines and # comments ignored)
Output: HTML files in benchmark/html/ and stub GT in benchmark/ground-truth/

The script:
1. Assigns the next available file ID (continues from highest existing)
2. Downloads each URL's HTML
3. Creates a stub GT JSON with the page type set
4. Skips URLs that are already in the benchmark (by URL match)
"""

import json
import os
import sys
import time
import re
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT_DIR = os.path.join(PROJ, "benchmark", "ground-truth")
HTML_DIR = os.path.join(PROJ, "benchmark", "html")

VALID_TYPES = ['article', 'forum', 'product', 'service', 'documentation', 'collection', 'listing']

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


class TitleParser(HTMLParser):
    """Extract <title> from HTML."""
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def get_next_id() -> int:
    """Find the next available file ID."""
    max_id = 0
    for f in os.listdir(GT_DIR):
        if f.endswith('.json'):
            try:
                fid = int(f.replace('.json', ''))
                max_id = max(max_id, fid)
            except ValueError:
                pass
    for f in os.listdir(HTML_DIR):
        if f.endswith('.html'):
            try:
                fid = int(f.replace('.html', ''))
                max_id = max(max_id, fid)
            except ValueError:
                pass
    return max_id + 1


def get_existing_urls() -> set:
    """Get all URLs already in the benchmark."""
    urls = set()
    for f in os.listdir(GT_DIR):
        if not f.endswith('.json'):
            continue
        try:
            with open(os.path.join(GT_DIR, f)) as fh:
                d = json.load(fh)
            url = d.get('url', '')
            if url:
                urls.add(url.rstrip('/'))
        except Exception:
            pass
    return urls


def fetch_url(url: str) -> str | None:
    """Download HTML from URL. Returns HTML string or None on failure."""
    req = Request(url, headers={
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    try:
        with urlopen(req, timeout=30) as resp:
            # Check content type
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                print(f"    SKIP: not HTML ({content_type})")
                return None

            data = resp.read(5_000_000)  # Max 5MB
            # Try to detect encoding
            encoding = 'utf-8'
            charset_match = re.search(r'charset=([^\s;]+)', content_type)
            if charset_match:
                encoding = charset_match.group(1)

            return data.decode(encoding, errors='replace')
    except HTTPError as e:
        print(f"    HTTP {e.code}: {e.reason}")
        return None
    except URLError as e:
        print(f"    URL error: {e.reason}")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def extract_title(html: str) -> str:
    """Extract title from HTML."""
    parser = TitleParser()
    try:
        parser.feed(html[:50000])  # First 50KB should have <title>
    except Exception:
        pass
    return parser.title.strip()


def create_stub_gt(fid: str, url: str, title: str, page_type: str) -> dict:
    """Create a stub GT file for annotation."""
    return {
        "schema_version": "2.0",
        "url": url,
        "file_id": fid,
        "ground_truth": {
            "title": title,
            "author": "",
            "publish_date": None,
            "main_content": "",
            "with": [],
            "without": []
        },
        "_internal": {
            "page_type": {
                "primary": page_type,
                "confidence": "high",
                "needs_review": True,
                "review_reason": "newly fetched, needs GT annotation",
                "tags": ["web-sourced"]
            }
        }
    }


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <urls_file> <page_type>")
        print(f"Valid types: {', '.join(VALID_TYPES)}")
        sys.exit(1)

    urls_file = sys.argv[1]
    page_type = sys.argv[2]

    if page_type not in VALID_TYPES:
        print(f"Invalid page type: {page_type}")
        print(f"Valid types: {', '.join(VALID_TYPES)}")
        sys.exit(1)

    # Read URLs
    with open(urls_file) as f:
        urls = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)

    print(f"URLs to fetch: {len(urls)}")
    print(f"Page type: {page_type}")

    # Check for duplicates
    existing = get_existing_urls()
    next_id = get_next_id()

    fetched = 0
    skipped = 0
    failed = 0

    for url in urls:
        url_clean = url.rstrip('/')
        if url_clean in existing:
            print(f"  SKIP (duplicate): {url[:70]}")
            skipped += 1
            continue

        fid = f"{next_id:04d}"
        print(f"  [{fid}] Fetching: {url[:70]}...")

        html = fetch_url(url)
        if html is None:
            failed += 1
            continue

        # Check minimum size
        if len(html) < 500:
            print(f"    SKIP: too small ({len(html)} bytes)")
            failed += 1
            continue

        title = extract_title(html)

        # Write HTML
        html_path = os.path.join(HTML_DIR, f"{fid}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # Write stub GT
        gt = create_stub_gt(fid, url, title, page_type)
        gt_path = os.path.join(GT_DIR, f"{fid}.json")
        with open(gt_path, 'w', encoding='utf-8') as f:
            json.dump(gt, f, indent=2, ensure_ascii=False)

        existing.add(url_clean)
        next_id += 1
        fetched += 1

        # Be polite
        time.sleep(0.5)

    print(f"\nDone: {fetched} fetched, {skipped} duplicates, {failed} failed")
    print(f"Total GT files: {len(os.listdir(GT_DIR))}")


if __name__ == '__main__':
    main()
