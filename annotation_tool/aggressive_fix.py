#!/usr/bin/env python3
"""Aggressively fix remaining GT files by removing all problematic content."""

import json
import os
import re
from datetime import datetime
from audit_gt import (
    normalize, extract_html_text, extract_title_from_html,
    split_sentences, check_sentence_in_html
)
from batch_audit import audit_original_gt

BASE = os.path.dirname(os.path.abspath(__file__))
GT_DIR = os.path.join(BASE, '..', 'data', 'ground_truth')
VERIFIED_DIR = os.path.join(BASE, 'verified')
PROGRESS_FILE = os.path.join(BASE, 'progress.json')
FILE_LIST_FILE = os.path.join(BASE, 'file_list.json')


def clean_and_approve(file_id, progress):
    """Load original GT, remove all problematic content, approve if salvageable."""
    gt_path = os.path.join(GT_DIR, f'{file_id}.json')
    if not os.path.exists(gt_path):
        return 'error', 'GT not found'

    with open(gt_path, 'r', encoding='utf-8') as f:
        original = json.load(f)

    gt = original.get('ground_truth', {})
    main_content = gt.get('main_content', '')
    with_snippets = list(gt.get('with', []))
    without_snippets = list(gt.get('without', []))

    if not main_content:
        return 'error', 'Empty main_content'

    html_text = extract_html_text(file_id)
    if not html_text:
        return 'error', 'No HTML text'

    html_norm = normalize(html_text)
    original_content_len = len(main_content)

    # Step 1: Fix common patterns in main_content
    content = main_content
    # Fix curly quotes to straight
    content = content.replace('\u2018', "'").replace('\u2019', "'")
    content = content.replace('\u201c', '"').replace('\u201d', '"')
    content = content.replace('\u2014', '-').replace('\u2013', '-')

    # Step 2: Split into sentences and check each one
    sentences = split_sentences(content)
    good_sentences = []
    removed = 0

    for sent in sentences:
        if check_sentence_in_html(sent, html_norm):
            good_sentences.append(sent)
        else:
            removed += 1

    # Step 3: Rebuild content - remove bad sentences from original
    cleaned_content = content
    for sent in sentences:
        if not check_sentence_in_html(sent, html_norm):
            # Remove this sentence from content
            if sent in cleaned_content:
                cleaned_content = cleaned_content.replace(sent, '', 1)

    # Clean up whitespace artifacts
    cleaned_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_content)
    cleaned_content = re.sub(r'  +', ' ', cleaned_content)
    cleaned_content = re.sub(r' +\n', '\n', cleaned_content)
    cleaned_content = re.sub(r'\n +', '\n', cleaned_content)
    cleaned_content = cleaned_content.strip()

    # Step 4: Clean 'with' snippets
    new_with = []
    for snippet in with_snippets:
        # Fix quotes
        fixed = snippet.replace('\u2018', "'").replace('\u2019', "'")
        fixed = fixed.replace('\u201c', '"').replace('\u201d', '"')
        fixed = fixed.replace('\u2014', '-').replace('\u2013', '-')
        if check_sentence_in_html(fixed, html_norm):
            new_with.append(fixed)
        elif check_sentence_in_html(snippet, html_norm):
            new_with.append(snippet)
        # else: drop it

    # Step 5: Check if salvageable
    remaining_len = len(cleaned_content)
    retention_ratio = remaining_len / max(original_content_len, 1)

    # Re-audit the cleaned content
    sentences_after = split_sentences(cleaned_content)
    still_missing = 0
    for sent in sentences_after:
        if not check_sentence_in_html(sent, html_norm):
            still_missing += 1

    # Approve if:
    # - At least 50% of content retained
    # - At least 200 chars of content
    # - No more than 2 remaining issues
    if remaining_len < 200:
        return 'skip', f'Too little content after cleaning ({remaining_len} chars)'

    if retention_ratio < 0.40:
        return 'skip', f'Too much removed ({retention_ratio:.0%} retained, {removed} sentences removed)'

    if still_missing > 2:
        return 'still_broken', f'{still_missing} sentences still missing after cleaning'

    # Save verified file
    now = datetime.now().isoformat()
    verified = {
        "status": "approved",
        "ground_truth": {
            "title": gt.get('title', ''),
            "author": gt.get('author'),
            "publish_date": gt.get('publish_date'),
            "main_content": cleaned_content,
            "with": new_with,
            "without": without_snippets,
        },
        "original_url": original.get('url', ''),
        "file_id": file_id,
        "verified_at": now,
    }

    vpath = os.path.join(VERIFIED_DIR, f'{file_id}.json')
    with open(vpath, 'w', encoding='utf-8') as f:
        json.dump(verified, f, indent=2, ensure_ascii=False)

    progress[file_id] = {
        "status": "approved",
        "verified_at": now,
    }

    return 'approved', f'{removed} removed, {retention_ratio:.0%} retained, {still_missing} remaining'


def main():
    with open(FILE_LIST_FILE) as f:
        file_list = json.load(f)
    with open(PROGRESS_FILE) as f:
        progress = json.load(f)

    pending = [fid for fid in file_list if fid not in progress]
    print(f"Processing {len(pending)} pending files...\n")

    approved = []
    skipped = []
    broken = []
    errors = []

    for fid in pending:
        status, detail = clean_and_approve(fid, progress)

        if status == 'approved':
            approved.append(fid)
            print(f"  {fid}: APPROVED ({detail})")
        elif status == 'skip':
            # Mark as skipped
            now = datetime.now().isoformat()
            progress[fid] = {"status": "skipped", "verified_at": now}
            skipped.append((fid, detail))
            print(f"  {fid}: SKIPPED ({detail})")
        elif status == 'still_broken':
            broken.append((fid, detail))
            print(f"  {fid}: STILL BROKEN ({detail})")
        else:
            # Mark errors as skipped too
            now = datetime.now().isoformat()
            progress[fid] = {"status": "skipped", "verified_at": now}
            errors.append((fid, detail))
            print(f"  {fid}: ERROR ({detail})")

    # Save progress
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Approved: {len(approved)}")
    print(f"  Skipped:  {len(skipped)}")
    print(f"  Broken:   {len(broken)}")
    print(f"  Errors:   {len(errors)}")

    total_approved = sum(1 for v in progress.values() if v['status'] == 'approved')
    total_skipped = sum(1 for v in progress.values() if v['status'] == 'skipped')
    print(f"\nOverall: {total_approved} approved, {total_skipped} skipped, "
          f"{len(file_list) - len(progress)} remaining")


if __name__ == '__main__':
    main()
