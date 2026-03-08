#!/usr/bin/env python3
"""Batch-approve GT files that pass audit with 0 issues."""

import json
import os
from datetime import datetime
from batch_audit import audit_original_gt

BASE = os.path.dirname(os.path.abspath(__file__))
GT_DIR = os.path.join(BASE, '..', 'data', 'ground_truth')
VERIFIED_DIR = os.path.join(BASE, 'verified')
PROGRESS_FILE = os.path.join(BASE, 'progress.json')
FILE_LIST_FILE = os.path.join(BASE, 'file_list.json')


def main():
    with open(FILE_LIST_FILE) as f:
        file_list = json.load(f)

    with open(PROGRESS_FILE) as f:
        progress = json.load(f)

    pending = [fid for fid in file_list if fid not in progress]
    print(f"Checking {len(pending)} pending files...")

    approved = []
    skipped = []

    for fid in pending:
        result = audit_original_gt(fid)

        if 'error' in result:
            skipped.append((fid, result['error']))
            continue

        issues = result['missing_count'] + len(result['bad_with'])
        if not result['title_ok']:
            issues += 1

        if issues > 0:
            skipped.append((fid, f"{issues} issues"))
            continue

        # Load original GT
        gt_path = os.path.join(GT_DIR, f'{fid}.json')
        with open(gt_path, 'r', encoding='utf-8') as f:
            original = json.load(f)

        gt = original.get('ground_truth', {})
        now = datetime.now().isoformat()

        # Create verified file in the same format as the annotation tool
        verified = {
            "status": "approved",
            "ground_truth": {
                "title": gt.get('title', ''),
                "author": gt.get('author'),
                "publish_date": gt.get('publish_date'),
                "main_content": gt.get('main_content', ''),
                "with": gt.get('with', []),
                "without": gt.get('without', []),
            },
            "original_url": original.get('url', ''),
            "file_id": fid,
            "verified_at": now,
        }

        # Save verified file
        vpath = os.path.join(VERIFIED_DIR, f'{fid}.json')
        with open(vpath, 'w', encoding='utf-8') as f:
            json.dump(verified, f, indent=2, ensure_ascii=False)

        # Update progress
        progress[fid] = {
            "status": "approved",
            "verified_at": now,
        }

        approved.append(fid)

    # Save progress
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

    print(f"\nApproved: {len(approved)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Total approved (including previous): {sum(1 for v in progress.values() if v['status'] == 'approved')}")

    if approved:
        print(f"\nNewly approved: {', '.join(approved)}")


if __name__ == '__main__':
    main()
