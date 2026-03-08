#!/usr/bin/env python3
"""Add the top N clean candidate files to the benchmark."""

import json
import os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
GT_DIR = os.path.join(BASE, '..', 'data', 'ground_truth')
VERIFIED_DIR = os.path.join(BASE, 'verified')
PROGRESS_FILE = os.path.join(BASE, 'progress.json')
FILE_LIST_FILE = os.path.join(BASE, 'file_list.json')
CANDIDATES_FILE = os.path.join(BASE, 'new_candidates.json')
VERIFIED_BENCHMARK = os.path.join(BASE, '..', 'data', 'verified_benchmark_files.json')

TARGET_NEW = 98  # files to add


def main():
    with open(CANDIDATES_FILE) as f:
        candidates = json.load(f)

    with open(FILE_LIST_FILE) as f:
        file_list = json.load(f)

    with open(PROGRESS_FILE) as f:
        progress = json.load(f)

    # Take top N clean files (0 issues)
    clean = [r for r in candidates['files'] if r['total_issues'] == 0]
    to_add = clean[:TARGET_NEW]

    print(f"Adding {len(to_add)} new clean files to benchmark...\n")

    added = 0
    for r in to_add:
        fid = r['file_id']

        # Load original GT
        gt_path = os.path.join(GT_DIR, f'{fid}.json')
        with open(gt_path, 'r', encoding='utf-8') as f:
            original = json.load(f)

        gt = original.get('ground_truth', {})
        now = datetime.now().isoformat()

        # Create verified file
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

        vpath = os.path.join(VERIFIED_DIR, f'{fid}.json')
        with open(vpath, 'w', encoding='utf-8') as f:
            json.dump(verified, f, indent=2, ensure_ascii=False)

        # Add to file list and progress
        if fid not in file_list:
            file_list.append(fid)
        progress[fid] = {
            "status": "approved",
            "verified_at": now,
        }

        added += 1
        print(f"  {fid}: {r['total_sentences']} sentences, {r['content_length']} chars")

    # Sort file list
    file_list.sort()

    # Save everything
    with open(FILE_LIST_FILE, 'w') as f:
        json.dump(file_list, f, indent=2)

    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

    # Update verified benchmark list
    approved = sorted([fid for fid, info in progress.items() if info['status'] == 'approved'])
    with open(VERIFIED_BENCHMARK, 'w') as f:
        json.dump(approved, f, indent=2)

    print(f"\nAdded {added} files")
    print(f"Total in file list: {len(file_list)}")
    print(f"Total approved: {len(approved)}")
    print(f"Verified benchmark files: {len(approved)}")


if __name__ == '__main__':
    main()
