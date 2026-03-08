#!/usr/bin/env python3
"""Import selected pool candidates into the curated benchmark.

Reads pool_candidates.json, copies HTML files, and converts GT from
benchmark-package format (articleBody) to v2.0 schema.
"""

import json
import os
import gzip
import shutil

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL_FILE = os.path.join(PROJ, "pool_candidates.json")
PKG_GT = os.path.join(PROJ, "benchmark-package", "ground-truth.json")
PKG_HTML = os.path.join(PROJ, "benchmark-package", "html")
CUR_GT = os.path.join(PROJ, "benchmark", "ground-truth")
CUR_HTML = os.path.join(PROJ, "benchmark", "html")

# Map our classifier types to GT _internal.page_type.primary values
TYPE_MAP = {
    'article': 'article',
    'forum': 'forum',
    'product': 'product',
    'service': 'service',
    'documentation': 'documentation',
    'collection': 'collection',
    'listing': 'listing',
}


def convert_gt(fid: str, pkg_entry: dict, page_type: str) -> dict:
    """Convert benchmark-package GT format to v2.0 schema."""
    return {
        "schema_version": "2.0",
        "url": pkg_entry.get("url", ""),
        "file_id": fid,
        "ground_truth": {
            "title": pkg_entry.get("title", ""),
            "author": pkg_entry.get("author", ""),
            "publish_date": pkg_entry.get("publish_date", None),
            "main_content": pkg_entry.get("articleBody", ""),
            "with": pkg_entry.get("with", []),
            "without": pkg_entry.get("without", []),
        },
        "_internal": {
            "page_type": {
                "primary": TYPE_MAP.get(page_type, "article"),
                "confidence": "medium",
                "needs_review": True,
                "review_reason": "imported from pool, needs verification",
                "tags": ["pool-import"]
            }
        }
    }


def main():
    with open(POOL_FILE) as f:
        pool = json.load(f)

    with open(PKG_GT) as f:
        pkg_gt = json.load(f)

    selected = pool["selected"]
    print(f"Importing {len(selected)} files from pool...")

    imported = 0
    skipped = 0
    by_type = {}

    for candidate in selected:
        fid = candidate["file_id"]
        page_type = candidate["page_type"]

        # Check not already in curated set
        gt_path = os.path.join(CUR_GT, f"{fid}.json")
        html_path = os.path.join(CUR_HTML, f"{fid}.html")
        pkg_html_path = os.path.join(PKG_HTML, f"{fid}.html.gz")

        if os.path.exists(gt_path):
            print(f"  SKIP {fid}: already exists in curated GT")
            skipped += 1
            continue

        if not os.path.exists(pkg_html_path):
            print(f"  SKIP {fid}: no HTML in package")
            skipped += 1
            continue

        if fid not in pkg_gt:
            print(f"  SKIP {fid}: no GT in package")
            skipped += 1
            continue

        # Decompress HTML
        with gzip.open(pkg_html_path, 'rb') as gz:
            html_data = gz.read()
        with open(html_path, 'wb') as f:
            f.write(html_data)

        # Convert and write GT
        gt_data = convert_gt(fid, pkg_gt[fid], page_type)
        with open(gt_path, 'w') as f:
            json.dump(gt_data, f, indent=2, ensure_ascii=False)

        imported += 1
        by_type[page_type] = by_type.get(page_type, 0) + 1

    print(f"\nImported: {imported}")
    print(f"Skipped: {skipped}")
    print(f"\nBy type:")
    for t in sorted(by_type, key=by_type.get, reverse=True):
        print(f"  {t:<15} +{by_type[t]}")

    # Final counts
    gt_count = len([f for f in os.listdir(CUR_GT) if f.endswith('.json')])
    html_count = len([f for f in os.listdir(CUR_HTML) if f.endswith('.html')])
    print(f"\nFinal: {gt_count} GT files, {html_count} HTML files")


if __name__ == '__main__':
    main()
