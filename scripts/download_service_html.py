#!/usr/bin/env python3
"""
Download HTML for service page benchmark expansion.

Usage:
    python scripts/download_service_html.py              # Download all
    python scripts/download_service_html.py --dry-run     # Just list URLs and IDs
    python scripts/download_service_html.py --stubs       # Create GT stub files
    python scripts/download_service_html.py --skip-existing  # Skip already downloaded
"""
import argparse
import json
import time
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
HTML_DIR = BASE_DIR / "benchmark" / "html"
GT_DIR = BASE_DIR / "benchmark" / "ground-truth"

SERVICE_PAGES = [
    # === Major SaaS / Cloud (10) ===
    {"id": "0690", "source": "HubSpot",
     "url": "https://www.hubspot.com/products/marketing",
     "category": "marketing-automation"},
    {"id": "0691", "source": "Salesforce",
     "url": "https://www.salesforce.com/crm/",
     "category": "crm"},
    {"id": "0692", "source": "Cloudflare",
     "url": "https://www.cloudflare.com/application-services/products/cdn/",
     "category": "cdn-security"},
    {"id": "0693", "source": "Zendesk",
     "url": "https://www.zendesk.com/service/",
     "category": "customer-support"},
    {"id": "0694", "source": "Mailchimp",
     "url": "https://mailchimp.com/features/email/",
     "category": "email-marketing"},
    {"id": "0695", "source": "Webflow",
     "url": "https://webflow.com/cms",
     "category": "cms"},
    {"id": "0696", "source": "Monday.com",
     "url": "https://monday.com/work-management",
     "category": "project-management"},
    {"id": "0697", "source": "Freshdesk",
     "url": "https://www.freshworks.com/freshdesk/",
     "category": "helpdesk"},
    {"id": "0698", "source": "Stripe",
     "url": "https://stripe.com/payments",
     "category": "payments"},
    {"id": "0699", "source": "Zapier",
     "url": "https://zapier.com/platform",
     "category": "automation"},

    # === Cloud Providers (3) ===
    {"id": "0700", "source": "AWS",
     "url": "https://aws.amazon.com/lambda/",
     "category": "serverless"},
    {"id": "0701", "source": "Google Cloud",
     "url": "https://cloud.google.com/bigquery",
     "category": "data-warehouse"},
    {"id": "0702", "source": "Azure",
     "url": "https://azure.microsoft.com/en-us/products/functions",
     "category": "serverless"},

    # === SEO / Marketing Tools (3) ===
    {"id": "0703", "source": "Ahrefs",
     "url": "https://ahrefs.com/seo",
     "category": "seo-tools"},
    {"id": "0704", "source": "BrightLocal",
     "url": "https://www.brightlocal.com/local-seo-tools/",
     "category": "local-seo"},
    {"id": "0705", "source": "Intercom",
     "url": "https://www.intercom.com/customer-support-software",
     "category": "support-platform"},

    # === Freelance / Marketplace (3) ===
    {"id": "0706", "source": "Fiverr",
     "url": "https://www.fiverr.com/categories/writing-translation",
     "category": "writing-services"},
    {"id": "0707", "source": "Toptal",
     "url": "https://www.toptal.com/designers",
     "category": "design-talent"},
    {"id": "0708", "source": "Twilio",
     "url": "https://www.twilio.com/en-us/messaging",
     "category": "messaging-api"},

    # === Consulting / Professional (2) ===
    {"id": "0709", "source": "Deloitte",
     "url": "https://www2.deloitte.com/us/en/services/consulting.html",
     "category": "management-consulting"},
    {"id": "0710", "source": "PwC",
     "url": "https://www.pwc.com/us/en/services/consulting.html",
     "category": "strategy-consulting"},

    # === IT / Dev Agencies (6) ===
    {"id": "0711", "source": "LeewayHertz",
     "url": "https://www.leewayhertz.com/ai-development-company/",
     "category": "ai-development"},
    {"id": "0712", "source": "ScienceSoft",
     "url": "https://www.scnsoft.com/services/analytics/managed",
     "category": "managed-analytics"},
    {"id": "0713", "source": "Neoteric",
     "url": "https://neoteric.eu/services/progressive-web-app-development-company",
     "category": "pwa-development"},
    {"id": "0714", "source": "SmartCat",
     "url": "https://smartcat.io/genai/",
     "category": "genai-services"},
    {"id": "0715", "source": "QBurst",
     "url": "https://www.qburst.com/en-in/software-testing-services/",
     "category": "qa-testing"},
    {"id": "0716", "source": "BrandWisdom",
     "url": "https://brandwisdom.in/services/digital-marketing-services-management/marketing-and-advertising/",
     "category": "digital-marketing"},

    # === Creative / Design (3) ===
    {"id": "0717", "source": "DoodloDesigns",
     "url": "https://doodlodesigns.com/services/packaging/cosmetic-packaging-design",
     "category": "packaging-design"},
    {"id": "0718", "source": "Netsmartz",
     "url": "https://netsmartz.com/generative-ai-consulting-services/",
     "category": "ai-consulting"},
    {"id": "0719", "source": "LeverX",
     "url": "https://leverx.com/services/ai-consulting-services",
     "category": "sap-ai-consulting"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def download_html(url: str, output_path: Path, timeout: int = 30) -> dict:
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
    gt_data = {
        "file_id": page["id"],
        "url": page["url"],
        "source": page["source"],
        "page_type": {"primary": "service"},
        "category": page["category"],
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
    parser = argparse.ArgumentParser(description="Download service page HTML for benchmark")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--stubs", action="store_true")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    HTML_DIR.mkdir(parents=True, exist_ok=True)
    GT_DIR.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print(f"\n=== All {len(SERVICE_PAGES)} service pages ===\n")
        for p in SERVICE_PAGES:
            print(f"  {p['id']}  {p['category']:25s}  {p['source']}")
            print(f"          {p['url']}")
        return

    if args.stubs:
        print(f"\nCreating GT stub files in {GT_DIR}...\n")
        created = 0
        for p in SERVICE_PAGES:
            gt_path = GT_DIR / f"{p['id']}.json"
            if not gt_path.exists():
                create_gt_stub(p, gt_path)
                created += 1
                print(f"  Created {gt_path.name}")
            else:
                print(f"  Skipped {gt_path.name} (exists)")
        print(f"\nCreated {created} stub files.")
        return

    print(f"\n=== Downloading {len(SERVICE_PAGES)} service pages ===\n")

    ok = 0
    skipped = 0
    failed = []

    for i, p in enumerate(SERVICE_PAGES):
        html_path = HTML_DIR / f"{p['id']}.html"

        if args.skip_existing and html_path.exists() and html_path.stat().st_size > 1000:
            print(f"  [{i+1}/{len(SERVICE_PAGES)}] {p['id']} SKIP (exists, {html_path.stat().st_size//1024} KB) — {p['source']}")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(SERVICE_PAGES)}] {p['id']} downloading — {p['source']}...", end=" ", flush=True)
        result = download_html(p["url"], html_path)

        if result["status"] == "ok":
            size_kb = result["size"] / 1024
            print(f"OK ({size_kb:.0f} KB)")
            ok += 1
        else:
            print(f"FAILED: {result}")
            failed.append(p)

        if i < len(SERVICE_PAGES) - 1:
            time.sleep(args.delay)

    print(f"\n=== Results ===")
    print(f"  Downloaded: {ok}")
    print(f"  Skipped:    {skipped}")
    print(f"  Failed:     {len(failed)}")

    if failed:
        print(f"\n=== Failed downloads ===")
        for p in failed:
            print(f"  {p['id']}  {p['source']:25s}  {p['url']}")


if __name__ == "__main__":
    main()
