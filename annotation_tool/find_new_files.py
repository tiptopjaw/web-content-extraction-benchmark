#!/usr/bin/env python3
"""Find new clean GT files to add to the benchmark from the pool of unused files."""

import json
import os
from pathlib import Path
from audit_gt import (
    normalize, extract_html_text, extract_title_from_html,
    split_sentences, check_sentence_in_html
)

BASE = os.path.dirname(os.path.abspath(__file__))
GT_DIR = os.path.join(BASE, '..', 'data', 'ground_truth')
HTML_DIR = os.path.join(BASE, '..', 'data', 'html_files')
FILE_LIST_FILE = os.path.join(BASE, 'file_list.json')


def audit_candidate(file_id):
    """Audit a candidate file's GT against its HTML."""
    gt_path = os.path.join(GT_DIR, f'{file_id}.json')
    html_path = os.path.join(HTML_DIR, f'{file_id}.html')

    if not os.path.exists(gt_path) or not os.path.exists(html_path):
        return None

    with open(gt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    gt = data.get('ground_truth', {})
    main_content = gt.get('main_content', '')
    with_snippets = gt.get('with', [])

    if not main_content or len(main_content) < 200:
        return None  # Skip very short content

    html_text = extract_html_text(file_id)
    if not html_text or len(html_text) < 100:
        return None

    html_norm = normalize(html_text)

    # Check sentences
    sentences = split_sentences(main_content)
    if not sentences:
        return None

    missing = 0
    for sent in sentences:
        if not check_sentence_in_html(sent, html_norm):
            missing += 1

    # Check with snippets
    bad_with = 0
    for snippet in with_snippets:
        if not check_sentence_in_html(snippet, html_norm):
            bad_with += 1

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

    total_issues = missing + bad_with + (0 if title_ok else 1)
    missing_ratio = missing / max(len(sentences), 1)

    return {
        'file_id': file_id,
        'total_issues': total_issues,
        'missing': missing,
        'total_sentences': len(sentences),
        'missing_ratio': missing_ratio,
        'bad_with': bad_with,
        'title_ok': title_ok,
        'content_length': len(main_content),
        'page_type': data.get('_internal', {}).get('page_type', {}).get('primary', ''),
    }


def main():
    with open(FILE_LIST_FILE) as f:
        current = set(json.load(f))

    gt_dir = Path(GT_DIR)
    html_dir = Path(HTML_DIR)
    all_gt = {p.stem for p in gt_dir.glob('*.json')}
    all_html = {p.stem for p in html_dir.glob('*.html')}
    candidates = sorted(all_gt & all_html - current)

    print(f"Auditing {len(candidates)} candidate files...\n")

    results = []
    for fid in candidates:
        r = audit_candidate(fid)
        if r:
            results.append(r)

    # Sort by quality: clean first, then by content length (prefer longer articles)
    clean = [r for r in results if r['total_issues'] == 0]
    minor = [r for r in results if 0 < r['total_issues'] <= 2 and r['missing_ratio'] < 0.10]
    fixable = [r for r in results if 2 < r['total_issues'] <= 5 and r['missing_ratio'] < 0.20]

    # Sort each group by content length (prefer longer, more substantial articles)
    clean.sort(key=lambda r: -r['content_length'])
    minor.sort(key=lambda r: (r['total_issues'], -r['content_length']))
    fixable.sort(key=lambda r: (r['missing_ratio'], -r['content_length']))

    print(f"Results:")
    print(f"  Clean (0 issues): {len(clean)}")
    print(f"  Minor (1-2 issues, <10% missing): {len(minor)}")
    print(f"  Fixable (3-5 issues, <20% missing): {len(fixable)}")
    print(f"  Total usable: {len(clean) + len(minor) + len(fixable)}")

    # Save ranked list
    ranked = clean + minor + fixable
    output = {
        'clean_count': len(clean),
        'minor_count': len(minor),
        'fixable_count': len(fixable),
        'files': ranked,
    }

    with open('new_candidates.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(ranked)} ranked candidates to new_candidates.json")
    print(f"\nTop 20 clean files:")
    for r in clean[:20]:
        print(f"  {r['file_id']}: {r['total_sentences']} sentences, {r['content_length']} chars, type={r['page_type']}")


if __name__ == '__main__':
    main()
