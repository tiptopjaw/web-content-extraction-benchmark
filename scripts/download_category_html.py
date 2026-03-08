#!/usr/bin/env python3
"""
Download HTML for category page benchmark expansion.

Some sites require JavaScript rendering or block automated requests
and will need manual download via browser "Save As" (Ctrl+S, HTML Only).

Usage:
    python scripts/download_category_html.py           # Download all auto-downloadable
    python scripts/download_category_html.py --dry-run  # Just list URLs and IDs
    python scripts/download_category_html.py --manual-only  # Show which need manual download
    python scripts/download_category_html.py --stubs    # Create GT stub files
"""
import argparse
import json
import time
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
HTML_DIR = BASE_DIR / "benchmark" / "html"
GT_DIR = BASE_DIR / "benchmark" / "ground-truth"

# Domains that block curl or require JS rendering — must be saved manually via browser
MANUAL_DOMAINS = {
    "www.amazon.com",            # captcha risk
    "www.nike.com",              # JS-heavy
}

# All 29 category page URLs with metadata
CATEGORY_PAGES = [
    # === Shopify (8) ===
    {"id": "0632", "platform": "shopify", "store": "Allbirds",
     "url": "https://www.allbirds.com/collections/mens-runners",
     "has_desc": True},
    {"id": "0633", "platform": "shopify", "store": "Gymshark",
     "url": "https://www.gymshark.com/collections/t-shirts-tops/mens",
     "has_desc": True},
    {"id": "0634", "platform": "shopify", "store": "Brooklinen",
     "url": "https://www.brooklinen.com/collections/sheets",
     "has_desc": True},
    {"id": "0635", "platform": "shopify", "store": "Ridge Wallet",
     "url": "https://ridge.com/collections/wallets",
     "has_desc": True},
    {"id": "0636", "platform": "shopify", "store": "Beardbrand",
     "url": "https://www.beardbrand.com/collections/beard-oil",
     "has_desc": True},
    {"id": "0637", "platform": "shopify", "store": "Skullcandy",
     "url": "https://www.skullcandy.com/collections/headphones",
     "has_desc": True},
    {"id": "0638", "platform": "shopify", "store": "Death Wish Coffee",
     "url": "https://www.deathwishcoffee.com/collections/coffee",
     "has_desc": False},
    {"id": "0639", "platform": "shopify", "store": "Bombas",
     "url": "https://bombas.com/collections/mens-socks",
     "has_desc": False},

    # === BigCommerce (4) ===
    {"id": "0640", "platform": "bigcommerce", "store": "UPLIFT Desk",
     "url": "https://www.upliftdesk.com/desk-accessories/",
     "has_desc": True},
    {"id": "0641", "platform": "bigcommerce", "store": "Green Roads",
     "url": "https://greenroads.com/cbd-gummies",
     "has_desc": True},
    {"id": "0642", "platform": "bigcommerce", "store": "Green Roads",
     "url": "https://greenroads.com/thc-gummies",
     "has_desc": True},
    {"id": "0643", "platform": "bigcommerce", "store": "UPLIFT Desk",
     "url": "https://www.upliftdesk.com/standing-desks/",
     "has_desc": True},

    # === PrestaShop (2) ===
    {"id": "0644", "platform": "prestashop", "store": "Esprit Barbecue",
     "url": "https://www.esprit-barbecue.fr/11-barbecue-charbon",
     "has_desc": True},
    {"id": "0645", "platform": "prestashop", "store": "Esprit Barbecue",
     "url": "https://www.esprit-barbecue.fr/10-barbecue-charbon",
     "has_desc": True},

    # === Magento (1) ===
    {"id": "0646", "platform": "magento", "store": "Solo Stove",
     "url": "https://www.solostove.com/us/en-us/c/fire-pits",
     "has_desc": True},

    # === Custom Platform / Major Retailers (12) ===
    {"id": "0647", "platform": "custom-ikea", "store": "IKEA",
     "url": "https://www.ikea.com/us/en/cat/bookcases-shelving-units-st002/",
     "has_desc": True},
    {"id": "0648", "platform": "custom-ikea", "store": "IKEA",
     "url": "https://www.ikea.com/us/en/cat/sofas-fu003/",
     "has_desc": True},
    {"id": "0649", "platform": "custom-newegg", "store": "Newegg",
     "url": "https://www.newegg.com/GPUs-Video-Graphics-Cards/SubCategory/ID-48",
     "has_desc": True},
    {"id": "0650", "platform": "custom-apple", "store": "Apple Store",
     "url": "https://www.apple.com/shop/buy-mac/macbook-air",
     "has_desc": True},
    {"id": "0651", "platform": "custom-ifixit", "store": "iFixit",
     "url": "https://www.ifixit.com/Parts",
     "has_desc": True},
    {"id": "0652", "platform": "custom-ifixit", "store": "iFixit",
     "url": "https://www.ifixit.com/Parts/iPhone",
     "has_desc": True},
    {"id": "0653", "platform": "custom-target", "store": "Target",
     "url": "https://www.target.com/c/bedding/-/N-5xtnr",
     "has_desc": True},
    {"id": "0654", "platform": "custom-target", "store": "Target",
     "url": "https://www.target.com/c/electronics/-/N-5xtg5",
     "has_desc": False},
    {"id": "0655", "platform": "custom-amazon", "store": "Amazon",
     "url": "https://www.amazon.com/Headphones-Accessories-Supplies/b?node=172541",
     "has_desc": False},
    {"id": "0656", "platform": "custom-nike", "store": "Nike",
     "url": "https://www.nike.com/w/mens-running-shoes-37v7jznik1zy7ok",
     "has_desc": False},
    {"id": "0657", "platform": "custom-nordstrom", "store": "Nordstrom",
     "url": "https://www.nordstrom.com/browse/men/clothing/jackets-coats",
     "has_desc": False},
    {"id": "0658", "platform": "custom-ebay", "store": "eBay",
     "url": "https://www.ebay.com/b/Collectibles-Art/bn_7000259855",
     "has_desc": False},

    # === WooCommerce (2) ===
    {"id": "0659", "platform": "woocommerce", "store": "JOCO Cups",
     "url": "https://jococups.com/shop/",
     "has_desc": True},
    {"id": "0660", "platform": "woocommerce", "store": "Bird Buddy",
     "url": "https://mybirdbuddy.eu/shop/",
     "has_desc": False},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def needs_manual_download(url: str) -> bool:
    """Check if a URL requires manual browser download."""
    domain = urlparse(url).netloc
    return domain in MANUAL_DOMAINS


def download_html(url: str, output_path: Path, timeout: int = 30) -> dict:
    """Download HTML from a URL. Returns status dict."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        content = resp.text
        if len(content) < 500:
            return {"status": "too_small", "size": len(content)}

        output_path.write_text(content, encoding="utf-8")
        return {"status": "ok", "size": len(content)}

    except requests.exceptions.HTTPError as e:
        return {"status": "http_error", "code": e.response.status_code if e.response else None}
    except requests.exceptions.ConnectionError:
        return {"status": "connection_error"}
    except requests.exceptions.Timeout:
        return {"status": "timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_gt_stub(page: dict, gt_path: Path):
    """Create a minimal ground truth stub file for later annotation."""
    gt_data = {
        "file_id": page["id"],
        "url": page["url"],
        "source": page["store"],
        "page_type": {"primary": "category"},
        "platform": page["platform"],
        "has_description": page["has_desc"],
        "ground_truth": {
            "title": "",
            "author": "",
            "publish_date": None,
            "main_content": "",
            "with": [],
            "without": []
        }
    }
    gt_path.write_text(json.dumps(gt_data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Download category page HTML for benchmark")
    parser.add_argument("--dry-run", action="store_true", help="Just list URLs and IDs")
    parser.add_argument("--manual-only", action="store_true", help="Show which need manual download")
    parser.add_argument("--skip-existing", action="store_true", help="Skip files that already exist")
    parser.add_argument("--stubs", action="store_true", help="Create GT stub files")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests (seconds)")
    args = parser.parse_args()

    HTML_DIR.mkdir(parents=True, exist_ok=True)
    GT_DIR.mkdir(parents=True, exist_ok=True)

    manual = []
    auto = []
    for p in CATEGORY_PAGES:
        if needs_manual_download(p["url"]):
            manual.append(p)
        else:
            auto.append(p)

    if args.manual_only:
        print(f"\n=== Sites requiring manual browser download ({len(manual)}) ===\n")
        print("Save each page via browser: Ctrl+S > 'HTML Only'\n")
        for p in manual:
            html_path = HTML_DIR / f"{p['id']}.html"
            exists = "EXISTS" if html_path.exists() else "MISSING"
            desc = "has-desc" if p["has_desc"] else "no-desc"
            print(f"  {p['id']}  {exists:7s}  {desc:8s}  {p['store']:25s}  {p['url']}")
        print(f"\n=== Sites downloadable via script ({len(auto)}) ===\n")
        for p in auto:
            html_path = HTML_DIR / f"{p['id']}.html"
            exists = "EXISTS" if html_path.exists() else "MISSING"
            desc = "has-desc" if p["has_desc"] else "no-desc"
            print(f"  {p['id']}  {exists:7s}  {desc:8s}  {p['store']:25s}  {p['url']}")
        return

    if args.dry_run:
        print(f"\n=== All {len(CATEGORY_PAGES)} category pages ===\n")
        for p in CATEGORY_PAGES:
            manual_flag = " [MANUAL]" if needs_manual_download(p["url"]) else ""
            desc = "has-desc" if p["has_desc"] else "no-desc"
            print(f"  {p['id']}  {p['platform']:20s}  {desc:8s}  {p['store']:25s}{manual_flag}")
            print(f"          {p['url']}")
        return

    if args.stubs:
        print(f"\nCreating GT stub files in {GT_DIR}...\n")
        created = 0
        for p in CATEGORY_PAGES:
            gt_path = GT_DIR / f"{p['id']}.json"
            if not gt_path.exists():
                create_gt_stub(p, gt_path)
                created += 1
                print(f"  Created {gt_path.name}")
            else:
                print(f"  Skipped {gt_path.name} (exists)")
        print(f"\nCreated {created} stub files.")
        return

    # Download automated ones
    print(f"\n=== Downloading {len(auto)} pages (skipping {len(manual)} manual) ===\n")

    ok = 0
    skipped = 0
    failed = []

    for i, p in enumerate(auto):
        html_path = HTML_DIR / f"{p['id']}.html"

        if args.skip_existing and html_path.exists() and html_path.stat().st_size > 1000:
            print(f"  [{i+1}/{len(auto)}] {p['id']} SKIP (exists, {html_path.stat().st_size//1024} KB) — {p['store']}")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(auto)}] {p['id']} downloading — {p['store']}...", end=" ", flush=True)
        result = download_html(p["url"], html_path)

        if result["status"] == "ok":
            size_kb = result["size"] / 1024
            print(f"OK ({size_kb:.0f} KB)")
            ok += 1
        else:
            print(f"FAILED: {result}")
            failed.append(p)

        if i < len(auto) - 1:
            time.sleep(args.delay)

    print(f"\n=== Results ===")
    print(f"  Downloaded: {ok}")
    print(f"  Skipped:    {skipped}")
    print(f"  Failed:     {len(failed)}")
    print(f"  Manual:     {len(manual)}")

    if failed:
        print(f"\n=== Failed downloads (try manually) ===")
        for p in failed:
            print(f"  {p['id']}  {p['store']:25s}  {p['url']}")

    if manual:
        print(f"\n=== Needs manual browser download ({len(manual)}) ===")
        print("Save each page via browser: Ctrl+S > 'HTML Only'")
        for p in manual:
            html_path = HTML_DIR / f"{p['id']}.html"
            exists = "EXISTS" if html_path.exists() else "MISSING"
            print(f"  {p['id']}  {exists:7s}  {p['store']:25s}  {p['url']}")


if __name__ == "__main__":
    main()
