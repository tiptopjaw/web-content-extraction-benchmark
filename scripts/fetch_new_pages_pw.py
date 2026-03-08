#!/usr/bin/env python3
"""Fetch new web pages using Playwright (stealth mode) and create stub GT files.

Usage:
    python3 scripts/fetch_new_pages_pw.py urls_product.txt product
    python3 scripts/fetch_new_pages_pw.py urls_file.txt page_type [--headless]

Uses a real browser to bypass bot protection. Defaults to headed mode
so you can see what's happening.
"""

import json
import os
import sys
import time
import re
from html.parser import HTMLParser
from playwright.sync_api import sync_playwright

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT_DIR = os.path.join(PROJ, "benchmark", "ground-truth")
HTML_DIR = os.path.join(PROJ, "benchmark", "html")

VALID_TYPES = ['article', 'forum', 'product', 'service', 'documentation', 'collection', 'listing']


class TitleParser(HTMLParser):
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


def extract_title(html: str) -> str:
    parser = TitleParser()
    try:
        parser.feed(html[:50000])
    except Exception:
        pass
    return parser.title.strip()


def create_stub_gt(fid: str, url: str, title: str, page_type: str) -> dict:
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
        print(f"Usage: {sys.argv[0]} <urls_file> <page_type> [--headless]")
        print(f"Valid types: {', '.join(VALID_TYPES)}")
        sys.exit(1)

    urls_file = sys.argv[1]
    page_type = sys.argv[2]
    headless = '--headless' in sys.argv

    if page_type not in VALID_TYPES:
        print(f"Invalid page type: {page_type}")
        sys.exit(1)

    with open(urls_file) as f:
        urls = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)

    print(f"URLs to fetch: {len(urls)}")
    print(f"Page type: {page_type}")
    print(f"Mode: {'headless' if headless else 'headed'}")

    existing = get_existing_urls()
    next_id = get_next_id()

    fetched = 0
    skipped = 0
    failed = 0

    with sync_playwright() as p:
        # Use chromium with stealth
        browser = p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
        )

        # Apply stealth
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(context)
        except ImportError:
            print("  (stealth not available, continuing without)")

        page = context.new_page()

        for url in urls:
            url_clean = url.rstrip('/')
            if url_clean in existing:
                print(f"  SKIP (duplicate): {url[:70]}")
                skipped += 1
                continue

            fid = f"{next_id:04d}"
            print(f"  [{fid}] Fetching: {url[:70]}...")

            try:
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                # Wait a bit for JS to render
                page.wait_for_timeout(2000)

                html = page.content()

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

                print(f"    OK: {len(html)} bytes, title: {title[:50]}")
                existing.add(url_clean)
                next_id += 1
                fetched += 1

            except Exception as e:
                print(f"    ERROR: {e}")
                failed += 1

            # Be polite
            time.sleep(1)

        browser.close()

    print(f"\nDone: {fetched} fetched, {skipped} duplicates, {failed} failed")

    gt_count = len([f for f in os.listdir(GT_DIR) if f.endswith('.json')])
    print(f"Total GT files: {gt_count}")


if __name__ == '__main__':
    main()
