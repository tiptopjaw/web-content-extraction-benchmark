#!/usr/bin/env python3
"""
Download HTML for documentation page benchmark expansion.

Documentation sites are generally well-behaved and don't block automated requests.

Usage:
    python scripts/download_docs_html.py              # Download all
    python scripts/download_docs_html.py --dry-run     # Just list URLs and IDs
    python scripts/download_docs_html.py --stubs       # Create GT stub files
    python scripts/download_docs_html.py --skip-existing  # Skip already downloaded
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

DOCS_PAGES = [
    # === Sphinx / ReadTheDocs (5) ===
    {"id": "0661", "platform": "sphinx", "source": "Django",
     "url": "https://docs.djangoproject.com/en/5.1/ref/models/querysets/",
     "content_type": "api-reference"},
    {"id": "0662", "platform": "sphinx", "source": "Flask",
     "url": "https://flask.palletsprojects.com/en/stable/quickstart/",
     "content_type": "tutorial"},
    {"id": "0663", "platform": "readthedocs", "source": "Requests",
     "url": "https://requests.readthedocs.io/en/latest/user/advanced/",
     "content_type": "guide"},
    {"id": "0664", "platform": "sphinx", "source": "SQLAlchemy",
     "url": "https://docs.sqlalchemy.org/en/20/orm/quickstart.html",
     "content_type": "tutorial"},
    {"id": "0665", "platform": "sphinx", "source": "Celery",
     "url": "https://docs.celeryq.dev/en/stable/userguide/tasks.html",
     "content_type": "guide"},

    # === Language Official Docs (5) ===
    {"id": "0666", "platform": "python-docs", "source": "Python",
     "url": "https://docs.python.org/3/library/itertools.html",
     "content_type": "stdlib-reference"},
    {"id": "0667", "platform": "mdbook", "source": "Rust",
     "url": "https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html",
     "content_type": "book-chapter"},
    {"id": "0668", "platform": "custom", "source": "Go",
     "url": "https://go.dev/doc/effective_go",
     "content_type": "style-guide"},
    {"id": "0669", "platform": "custom", "source": "TypeScript",
     "url": "https://www.typescriptlang.org/docs/handbook/2/types-from-types.html",
     "content_type": "handbook"},
    {"id": "0670", "platform": "custom", "source": "PostgreSQL",
     "url": "https://www.postgresql.org/docs/current/sql-select.html",
     "content_type": "sql-reference"},

    # === MDN Web Docs (3) ===
    {"id": "0671", "platform": "mdn", "source": "MDN",
     "url": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch",
     "content_type": "api-guide"},
    {"id": "0672", "platform": "mdn", "source": "MDN",
     "url": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Flexbox",
     "content_type": "tutorial"},
    {"id": "0673", "platform": "mdn", "source": "MDN",
     "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises",
     "content_type": "guide"},

    # === Docusaurus / React-based (4) ===
    {"id": "0674", "platform": "docusaurus", "source": "React",
     "url": "https://react.dev/learn",
     "content_type": "tutorial"},
    {"id": "0675", "platform": "docusaurus", "source": "Docusaurus",
     "url": "https://docusaurus.io/docs",
     "content_type": "getting-started"},
    {"id": "0676", "platform": "docusaurus", "source": "Supabase",
     "url": "https://supabase.com/docs/guides/auth",
     "content_type": "guide"},
    {"id": "0677", "platform": "docusaurus", "source": "Tauri",
     "url": "https://v2.tauri.app/start/",
     "content_type": "getting-started"},

    # === MkDocs / Material (2) ===
    {"id": "0678", "platform": "mkdocs", "source": "FastAPI",
     "url": "https://fastapi.tiangolo.com/tutorial/",
     "content_type": "tutorial"},
    {"id": "0679", "platform": "mkdocs", "source": "Pydantic",
     "url": "https://docs.pydantic.dev/latest/concepts/models/",
     "content_type": "concepts"},

    # === API Reference (2) ===
    {"id": "0680", "platform": "custom", "source": "Stripe",
     "url": "https://docs.stripe.com/api/charges",
     "content_type": "api-reference"},
    {"id": "0681", "platform": "custom", "source": "Twilio",
     "url": "https://www.twilio.com/docs/sms/send-messages",
     "content_type": "api-guide"},

    # === Wiki-style (3) ===
    {"id": "0682", "platform": "mediawiki", "source": "ArchWiki",
     "url": "https://wiki.archlinux.org/title/OpenSSH",
     "content_type": "reference"},
    {"id": "0683", "platform": "mediawiki", "source": "Gentoo Wiki",
     "url": "https://wiki.gentoo.org/wiki/Portage",
     "content_type": "reference"},
    {"id": "0684", "platform": "custom", "source": "Nginx",
     "url": "https://nginx.org/en/docs/http/ngx_http_core_module.html",
     "content_type": "module-reference"},

    # === DevOps / Infrastructure (3) ===
    {"id": "0685", "platform": "docusaurus", "source": "Kubernetes",
     "url": "https://kubernetes.io/docs/concepts/workloads/pods/",
     "content_type": "concepts"},
    {"id": "0686", "platform": "custom", "source": "Terraform",
     "url": "https://developer.hashicorp.com/terraform/language/resources/syntax",
     "content_type": "language-reference"},
    {"id": "0687", "platform": "sphinx", "source": "Ansible",
     "url": "https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html",
     "content_type": "guide"},

    # === Man Pages / CLI (2) ===
    {"id": "0688", "platform": "man-page", "source": "man7.org",
     "url": "https://man7.org/linux/man-pages/man1/grep.1.html",
     "content_type": "man-page"},
    {"id": "0689", "platform": "custom", "source": "Git",
     "url": "https://git-scm.com/docs/git-commit",
     "content_type": "man-page"},
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
        "page_type": {"primary": "documentation"},
        "platform": page["platform"],
        "content_type": page["content_type"],
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
    parser = argparse.ArgumentParser(description="Download documentation page HTML for benchmark")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--stubs", action="store_true")
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()

    HTML_DIR.mkdir(parents=True, exist_ok=True)
    GT_DIR.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print(f"\n=== All {len(DOCS_PAGES)} documentation pages ===\n")
        for p in DOCS_PAGES:
            print(f"  {p['id']}  {p['platform']:15s}  {p['content_type']:20s}  {p['source']}")
            print(f"          {p['url']}")
        return

    if args.stubs:
        print(f"\nCreating GT stub files in {GT_DIR}...\n")
        created = 0
        for p in DOCS_PAGES:
            gt_path = GT_DIR / f"{p['id']}.json"
            if not gt_path.exists():
                create_gt_stub(p, gt_path)
                created += 1
                print(f"  Created {gt_path.name}")
            else:
                print(f"  Skipped {gt_path.name} (exists)")
        print(f"\nCreated {created} stub files.")
        return

    print(f"\n=== Downloading {len(DOCS_PAGES)} documentation pages ===\n")

    ok = 0
    skipped = 0
    failed = []

    for i, p in enumerate(DOCS_PAGES):
        html_path = HTML_DIR / f"{p['id']}.html"

        if args.skip_existing and html_path.exists() and html_path.stat().st_size > 1000:
            print(f"  [{i+1}/{len(DOCS_PAGES)}] {p['id']} SKIP (exists, {html_path.stat().st_size//1024} KB) — {p['source']}")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(DOCS_PAGES)}] {p['id']} downloading — {p['source']}...", end=" ", flush=True)
        result = download_html(p["url"], html_path)

        if result["status"] == "ok":
            size_kb = result["size"] / 1024
            print(f"OK ({size_kb:.0f} KB)")
            ok += 1
        else:
            print(f"FAILED: {result}")
            failed.append(p)

        if i < len(DOCS_PAGES) - 1:
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
