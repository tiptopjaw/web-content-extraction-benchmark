#!/usr/bin/env python3
"""Batch audit ALL pending ground truth files against HTML to triage quality."""

import json
import os
import sys
from audit_gt import (
    normalize, extract_html_text, extract_title_from_html,
    split_sentences, check_sentence_in_html
)

BASE = os.path.dirname(os.path.abspath(__file__))
GT_DIR = os.path.join(BASE, '..', 'data', 'ground_truth')
HTML_DIR = os.path.join(BASE, '..', 'data', 'html_files')
PROGRESS_FILE = os.path.join(BASE, 'progress.json')
FILE_LIST_FILE = os.path.join(BASE, 'file_list.json')


def audit_original_gt(file_id):
    """Audit original GT file (from data/ground_truth/) against HTML."""
    gt_path = os.path.join(GT_DIR, f'{file_id}.json')
    if not os.path.exists(gt_path):
        return {'error': 'GT file not found'}

    with open(gt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    gt = data.get('ground_truth', {})
    main_content = gt.get('main_content', '')
    with_snippets = gt.get('with', [])

    if not main_content:
        return {'error': 'Empty main_content'}

    html_text = extract_html_text(file_id)
    if not html_text:
        return {'error': 'HTML file not found'}

    html_norm = normalize(html_text)

    # Check sentences
    sentences = split_sentences(main_content)
    missing_sentences = []
    for sent in sentences:
        if not check_sentence_in_html(sent, html_norm):
            missing_sentences.append(sent)

    # Check with snippets
    bad_with = []
    for snippet in with_snippets:
        if not check_sentence_in_html(snippet, html_norm):
            bad_with.append(snippet)

    # Check title
    title = gt.get('title', '')
    title_ok = True
    if title:
        title_ok = check_sentence_in_html(title, html_norm)
        if not title_ok:
            html_title = extract_title_from_html(file_id)
            if html_title:
                html_title_norm = normalize(html_title)
                gt_title_norm = normalize(title)
                if gt_title_norm in html_title_norm or html_title_norm in gt_title_norm:
                    title_ok = True
                elif len(gt_title_norm) > 10:
                    gt_words = set(gt_title_norm.split())
                    html_words = set(html_title_norm.split())
                    overlap = len(gt_words & html_words) / max(len(gt_words), 1)
                    if overlap > 0.7:
                        title_ok = True

    # Calculate missing ratio
    missing_ratio = len(missing_sentences) / max(len(sentences), 1)

    return {
        'total_sentences': len(sentences),
        'missing_sentences': missing_sentences,
        'missing_count': len(missing_sentences),
        'missing_ratio': missing_ratio,
        'bad_with': bad_with,
        'title_ok': title_ok,
        'content_length': len(main_content),
    }


def main():
    with open(FILE_LIST_FILE) as f:
        file_list = json.load(f)

    with open(PROGRESS_FILE) as f:
        progress = json.load(f)

    # Find pending files
    pending = [fid for fid in file_list if fid not in progress]

    print(f"Batch auditing {len(pending)} pending files...\n")

    clean = []         # 0 issues
    minor = []         # 1-2 missing sentences, <10% missing
    moderate = []      # 3-5 missing or 10-25% missing
    major = []         # >5 missing or >25% missing
    errors = []        # errors

    for fid in pending:
        result = audit_original_gt(fid)

        if 'error' in result:
            errors.append((fid, result['error']))
            continue

        issues = result['missing_count'] + len(result['bad_with'])
        if not result['title_ok']:
            issues += 1

        if issues == 0:
            clean.append(fid)
        elif result['missing_count'] <= 2 and result['missing_ratio'] < 0.10:
            minor.append((fid, result))
        elif result['missing_count'] <= 5 or result['missing_ratio'] < 0.25:
            moderate.append((fid, result))
        else:
            major.append((fid, result))

    # Print summary
    print(f"\n{'='*60}")
    print(f"BATCH AUDIT SUMMARY")
    print(f"{'='*60}")
    print(f"  CLEAN (0 issues):     {len(clean)}")
    print(f"  MINOR (1-2 issues):   {len(minor)}")
    print(f"  MODERATE (3-5):       {len(moderate)}")
    print(f"  MAJOR (>5):           {len(major)}")
    print(f"  ERRORS:               {len(errors)}")
    print(f"  TOTAL:                {len(pending)}")

    # Print clean files
    print(f"\n--- CLEAN ({len(clean)}) ---")
    for fid in clean:
        print(f"  {fid}")

    # Print minor
    print(f"\n--- MINOR ({len(minor)}) ---")
    for fid, r in minor:
        print(f"  {fid}: {r['missing_count']} missing/{r['total_sentences']} sentences, "
              f"{len(r['bad_with'])} bad_with, title_ok={r['title_ok']}")
        for ms in r['missing_sentences'][:2]:
            print(f"         MISS: {ms[:100]}...")

    # Print moderate
    print(f"\n--- MODERATE ({len(moderate)}) ---")
    for fid, r in moderate:
        print(f"  {fid}: {r['missing_count']} missing/{r['total_sentences']} sentences ({r['missing_ratio']:.0%}), "
              f"{len(r['bad_with'])} bad_with, title_ok={r['title_ok']}")

    # Print major
    print(f"\n--- MAJOR ({len(major)}) ---")
    for fid, r in major:
        print(f"  {fid}: {r['missing_count']} missing/{r['total_sentences']} sentences ({r['missing_ratio']:.0%}), "
              f"{len(r['bad_with'])} bad_with, title_ok={r['title_ok']}")

    # Print errors
    if errors:
        print(f"\n--- ERRORS ({len(errors)}) ---")
        for fid, err in errors:
            print(f"  {fid}: {err}")


if __name__ == '__main__':
    main()
