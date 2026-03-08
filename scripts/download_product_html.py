#!/usr/bin/env python3
"""
Download HTML for product page benchmark expansion.

Some sites require JavaScript rendering or block automated requests
and will need manual download via browser "Save As" (Ctrl+S, HTML Only).

Usage:
    python scripts/download_product_html.py           # Download all auto-downloadable
    python scripts/download_product_html.py --dry-run  # Just list URLs and IDs
    python scripts/download_product_html.py --manual-only  # Show which need manual download
    python scripts/download_product_html.py --stubs    # Create GT stub files
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
    "www.hellyhansen.com",       # 403
    "www.etsy.com",              # 403
    "www.bestbuy.com",           # timeout
    # Home Depot replaced with iFixit (geo-restricted)
    "www.nike.com",              # JS-heavy
    "en.zalando.de",             # timeout/403
    "www.bhphotovideo.com",      # 403
    "www.rei.com",               # timeout
    "www.sephora.com",           # 403
    "www.iherb.com",             # 403
    "hyosilver.com",             # JS bot protection
    "www.amazon.com",            # captcha/redirect
    # NEWTWIST removed - now downloads OK
}

# All 52 product page URLs with metadata
PRODUCT_PAGES = [
    # === Shopify (12) ===
    {"id": "0580", "platform": "shopify", "store": "Allbirds",
     "url": "https://www.allbirds.com/products/mens-wool-runners"},
    {"id": "0581", "platform": "shopify", "store": "Gymshark",
     "url": "https://www.gymshark.com/products/gymshark-arrival-t-shirt-black-ss22"},
    {"id": "0582", "platform": "shopify", "store": "Bombas",
     "url": "https://bombas.com/products/mens-quarter-socks"},
    {"id": "0583", "platform": "shopify", "store": "Death Wish Coffee",
     "url": "https://www.deathwishcoffee.com/products/death-wish-coffee"},
    {"id": "0584", "platform": "shopify", "store": "Brooklinen",
     "url": "https://www.brooklinen.com/products/classic-core-sheet-set"},
    {"id": "0585", "platform": "shopify", "store": "Ruggable",
     "url": "https://ruggable.com/products/beatrice-tan-tufted-rug"},
    {"id": "0586", "platform": "shopify", "store": "MVMT Watches",
     "url": "https://www.mvmt.com/mens-view-all/moon-silver/28000436.html"},
    {"id": "0587", "platform": "shopify", "store": "Ridge Wallet",
     "url": "https://ridge.com/products/aluminum-black"},
    {"id": "0588", "platform": "shopify", "store": "Nomad",
     "url": "https://nomadgoods.com/products/modern-leather-case-black-iphone-16-pro"},
    {"id": "0589", "platform": "shopify", "store": "Huel",
     "url": "https://huel.com/products/huel-black-edition"},
    {"id": "0590", "platform": "shopify", "store": "Beardbrand",
     "url": "https://www.beardbrand.com/products/beard-oil"},
    {"id": "0591", "platform": "shopify", "store": "Skullcandy",
     "url": "https://www.skullcandy.com/products/crusher-anc-2-sensory-bass-headphones-with-active-noise-canceling"},

    # === WooCommerce (10) ===
    {"id": "0592", "platform": "woocommerce", "store": "Forest Whole Foods",
     "url": "https://www.forestwholefoods.co.uk/product/organic-sunflower-seeds/"},
    {"id": "0593", "platform": "woocommerce", "store": "JOCO Cups",
     "url": "https://jococups.com/product/4oz-joco-cup/"},
    {"id": "0594", "platform": "woocommerce", "store": "Nord Republic",
     "url": "https://nordrepublic.com/product/nord-zero/"},
    {"id": "0595", "platform": "woocommerce", "store": "Karmin Hair Tools",
     "url": "https://karminhairtools.com/product/karmin-g3-pro-hair-dryer"},
    {"id": "0596", "platform": "woocommerce", "store": "MAHALO Skin Care",
     "url": "https://mahalo.care/shop/vitality-elixir/"},
    {"id": "0597", "platform": "woocommerce", "store": "SakeOne",
     "url": "https://www.sakeone.com/product/hakutsuru-premium-sake-selection-set-three-pack/"},
    {"id": "0598", "platform": "woocommerce", "store": "Hyo Silver",
     "url": "https://hyosilver.com/shop/buckles/texan-series-buckles/engraved-silver-fashion-belt-buckle/"},
    {"id": "0599", "platform": "woocommerce", "store": "NEWTWIST",
     "url": "https://www.newtwist.com/product/latelier-nawbar-warrior-princess-diamond-drop-necklace-small-handmade-18k-gold-bracelet-inlaid-with-0-18-ct-diamond-drop-and-encrusted-in-0-07-ct-of-round-white-diamonds/"},
    {"id": "0600", "platform": "woocommerce", "store": "Goshopia",
     "url": "https://www.goshopia.com/shop/womenswear/dress/iris-rust-hemp-dress/"},
    {"id": "0601", "platform": "woocommerce", "store": "Bird Buddy",
     "url": "https://mybirdbuddy.eu/product/smart-bird-feeder-pro/"},

    # === BigCommerce (4) ===
    {"id": "0602", "platform": "bigcommerce", "store": "UPLIFT Desk",
     "url": "https://www.upliftdesk.com/uplift-v2-24-deep-standing-desk/"},
    {"id": "0603", "platform": "bigcommerce", "store": "Green Roads",
     "url": "https://greenroads.com/cbd-relax-berries-300mg/"},
    {"id": "0604", "platform": "bigcommerce", "store": "AS Colour",
     "url": "https://ascolour.com/staple-tee-5001/"},
    {"id": "0605", "platform": "bigcommerce", "store": "Coco Republic",
     "url": "https://www.cocorepublic.com.au/345808-atelier-sofa.html"},

    # === Magento / PrestaShop (4) ===
    {"id": "0606", "platform": "magento", "store": "Helly Hansen",
     "url": "https://www.hellyhansen.com/en_us/loke-jacket-20-63396"},
    {"id": "0607", "platform": "magento", "store": "Solo Stove",
     "url": "https://www.solostove.com/us/en-us/p/solo-stove-summit?sku=SS24-SD-3.0"},
    {"id": "0608", "platform": "prestashop", "store": "Esprit Barbecue",
     "url": "https://www.esprit-barbecue.fr/barbecue-charbon/8866-1600-martinsen.html"},
    {"id": "0609", "platform": "prestashop", "store": "Les Raffineurs",
     "url": "https://www.lesraffineurs.com/idees-cadeau-decoration-et-cocooning/5134-diffuseur-dhuiles-essentielles.html"},

    # === Squarespace (2) ===
    {"id": "0610", "platform": "squarespace", "store": "Ghost Wares",
     "url": "https://www.ghostwares.com.au/shop/p/white-speckle-mug"},
    {"id": "0611", "platform": "squarespace", "store": "Supernatural Kitchen",
     "url": "https://www.supernaturalkitchen.com/shop-supernatural/natural-plant-based-food-coloring"},

    # === Custom Platform / Major Retailers (20) ===
    {"id": "0612", "platform": "custom-amazon", "store": "Amazon",
     "url": "https://www.amazon.com/Wireless-Headphones-Bluetooth-Waterproof-Headphone/dp/B0D1PC8551"},
    {"id": "0613", "platform": "custom-amazon", "store": "Amazon",
     "url": "https://www.amazon.com/Atomic-Habits-Proven-Build-Break/dp/0735211299"},
    {"id": "0614", "platform": "custom-ebay", "store": "eBay",
     "url": "https://www.ebay.com/itm/365999454668"},
    {"id": "0615", "platform": "custom-walmart", "store": "Walmart",
     "url": "https://www.walmart.com/ip/Ninja-Professional-Plus-Kitchen-Blender-System-with-Auto-iQ/562225800"},
    {"id": "0616", "platform": "custom-etsy", "store": "Etsy",
     "url": "https://www.etsy.com/listing/615442107/ceramic-mug-one-of-a-kind-mug-pottery"},
    {"id": "0617", "platform": "custom-etsy", "store": "Etsy",
     "url": "https://www.etsy.com/listing/1832770431/handmade-stoneware-coffee-mug-wabi-sabi"},
    {"id": "0618", "platform": "custom-bestbuy", "store": "Best Buy",
     "url": "https://www.bestbuy.com/product/microsoft-surface-laptop-copilot-pc-13-8-touchscreen-snapdragon-x-plus-2024-16gb-memory-512gb-storage-7th-ed-dune/JJGXP2VV5L"},
    {"id": "0619", "platform": "custom-target", "store": "Target",
     "url": "https://www.target.com/p/lodge-cast-iron-pre-seasoned-skillet-12-inch/-/A-10291923"},
    {"id": "0620", "platform": "custom-wayfair", "store": "Wayfair",
     "url": "https://www.wayfair.com/furniture/pdp/boss-office-products-executive-chair-bop1026.html"},
    {"id": "0621", "platform": "custom", "store": "iFixit",
     "url": "https://www.ifixit.com/products/pro-tech-toolkit"},
    {"id": "0622", "platform": "custom-ikea", "store": "IKEA",
     "url": "https://www.ikea.com/us/en/p/kallax-shelf-unit-white-80275887/"},
    {"id": "0623", "platform": "custom-apple", "store": "Apple Store",
     "url": "https://www.apple.com/shop/product/MYW83LL/A/macbook-air-15-inch-apple-m4-chip-16gb-memory-256gb"},
    {"id": "0624", "platform": "custom-nike", "store": "Nike",
     "url": "https://www.nike.com/t/pegasus-41-mens-road-running-shoes-extra-wide-LMhfRGdO"},
    {"id": "0625", "platform": "custom-zalando", "store": "Zalando",
     "url": "https://en.zalando.de/bershka-faux-leather-jacket-black-bej22t0pl-q11.html"},
    {"id": "0626", "platform": "custom-bhphoto", "store": "B&H Photo",
     "url": "https://www.bhphotovideo.com/c/product/1082604-REG/nikon_d750_dslr_camera_with.html"},
    {"id": "0627", "platform": "custom-newegg", "store": "Newegg",
     "url": "https://www.newegg.com/evga-12g-p4-3992-kr-geforce-gtx-titan-z-superclocked-12gb-graphics-card-with-fan/p/N82E16814487048"},
    {"id": "0628", "platform": "custom-rei", "store": "REI",
     "url": "https://www.rei.com/product/227955/rei-co-op-trail-25-pack"},
    {"id": "0629", "platform": "custom-sephora", "store": "Sephora",
     "url": "https://www.sephora.com/product/augustinus-bader-the-cream-with-tfc8-face-moisturizer-P470507"},
    {"id": "0630", "platform": "custom-nordstrom", "store": "Nordstrom",
     "url": "https://www.nordstrom.com/s/mens-adidas-black-lafc-2024-anthem-travel-raglan-sleeve-full-zip-jacket/7793539"},
    {"id": "0631", "platform": "custom-iherb", "store": "iHerb",
     "url": "https://www.iherb.com/pr/california-gold-nutrition-gold-c-vitamin-c-1-000-mg-60-veggie-capsules/61856"},
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
        "page_type": {"primary": "product"},
        "platform": page["platform"],
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
    parser = argparse.ArgumentParser(description="Download product page HTML for benchmark")
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
    for p in PRODUCT_PAGES:
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
            print(f"  {p['id']}  {exists:7s}  {p['store']:25s}  {p['url']}")
        print(f"\n=== Sites downloadable via script ({len(auto)}) ===\n")
        for p in auto:
            html_path = HTML_DIR / f"{p['id']}.html"
            exists = "EXISTS" if html_path.exists() else "MISSING"
            print(f"  {p['id']}  {exists:7s}  {p['store']:25s}  {p['url']}")
        return

    if args.dry_run:
        print(f"\n=== All {len(PRODUCT_PAGES)} product pages ===\n")
        for p in PRODUCT_PAGES:
            manual_flag = " [MANUAL]" if needs_manual_download(p["url"]) else ""
            print(f"  {p['id']}  {p['platform']:20s}  {p['store']:25s}{manual_flag}")
            print(f"          {p['url']}")
        return

    if args.stubs:
        print(f"\nCreating GT stub files in {GT_DIR}...\n")
        created = 0
        for p in PRODUCT_PAGES:
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
