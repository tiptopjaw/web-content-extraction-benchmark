#!/usr/bin/env python3
"""Comprehensive GT quality analysis across all files."""
import json
import os
import glob
import re
import statistics

files = sorted(glob.glob('benchmark/ground-truth/*.json'))
print(f'Total GT files: {len(files)}')

# Analysis categories
missing_schema = []
missing_title = []
missing_content = []
short_content = []
empty_with = []
empty_without = []
few_with = []
markdown_headings = []
markdown_bold = []
encoding_issues = []
bullet_issues = []
title_in_content = []
no_paragraph_breaks = []
html_tags = []
bad_with = []
bad_without = []
lengths = []
with_counts = []
without_counts = []

for f in files:
    fid = os.path.basename(f).replace('.json', '')
    with open(f) as fp:
        data = json.load(fp)

    gt = data.get('ground_truth', {})
    mc = gt.get('main_content', '')
    title = gt.get('title', '') or ''
    with_snips = gt.get('with', [])
    without_snips = gt.get('without', [])

    lengths.append((fid, len(mc)))
    with_counts.append(len(with_snips))
    without_counts.append(len(without_snips))

    # Schema version
    if data.get('schema_version') != '2.0':
        missing_schema.append(fid)

    # Title
    if not title:
        missing_title.append(fid)

    # Content checks
    if not mc:
        missing_content.append(fid)
    elif len(mc) < 200:
        short_content.append((fid, len(mc)))

    # Snippet counts
    if len(with_snips) == 0:
        empty_with.append(fid)
    elif len(with_snips) < 3:
        few_with.append((fid, len(with_snips)))

    if len(without_snips) == 0:
        empty_without.append(fid)

    # Markdown headings (## or # at start of line)
    for line in mc.split('\n'):
        stripped = line.strip()
        if stripped.startswith('## ') or (stripped.startswith('# ') and len(stripped) < 200):
            markdown_headings.append(fid)
            break

    # Markdown bold
    if '**' in mc:
        markdown_bold.append(fid)

    # Encoding artifacts
    for artifact in ['\u00e2\u0080\u0099', '\u00e2\u0080\u0094', '\u00c3\u00a9', '\u00c3\u00a8', '\u00c2\u00a0', '\u00e2\u0080\u009c', '\u00e2\u0080\u009d']:
        if artifact in mc:
            encoding_issues.append((fid, repr(artifact)))
            break

    # Bullet character issues
    if '\u2022' in mc:
        bullet_issues.append(fid)

    # Title repeated at start
    if title and mc.startswith(title):
        title_in_content.append(fid)

    # No paragraph breaks (wall of text > 1000 chars without \n\n)
    if len(mc) > 1000 and '\n\n' not in mc:
        no_paragraph_breaks.append((fid, len(mc)))

    # HTML tags in content
    if re.search(r'<(p|div|span|br|h[1-6]|ul|ol|li|a |img |table|tr|td|th)[> /]', mc):
        html_tags.append(fid)

    # Snippet integrity
    for i, snip in enumerate(with_snips):
        if snip not in mc:
            bad_with.append((fid, i, snip[:80]))

    for i, snip in enumerate(without_snips):
        if snip in mc:
            bad_without.append((fid, i, snip[:80]))

# ============ REPORT ============
print()
print('=' * 70)
print('COMPREHENSIVE GT QUALITY ANALYSIS')
print('=' * 70)

print('\n--- Schema ---')
print(f'  Missing schema_version 2.0: {len(missing_schema)}')
if missing_schema:
    print(f'  Files: {", ".join(missing_schema[:30])}{"..." if len(missing_schema) > 30 else ""}')

print('\n--- Content ---')
print(f'  Missing main_content: {len(missing_content)}')
print(f'  Short content (<200 chars): {len(short_content)}')
for fid, sz in short_content:
    print(f'    {fid}: {sz} chars')
print(f'  No paragraph breaks (wall of text >1k): {len(no_paragraph_breaks)}')
for fid, sz in no_paragraph_breaks:
    print(f'    {fid}: {sz} chars')
print(f'  Title repeated at start of content: {len(title_in_content)}')
if title_in_content:
    print(f'    Files: {", ".join(title_in_content[:30])}{"..." if len(title_in_content) > 30 else ""}')

print('\n--- Metadata ---')
print(f'  Missing title: {len(missing_title)}')
if missing_title:
    print(f'    Files: {", ".join(missing_title[:20])}')

print('\n--- Snippets ---')
print(f'  Empty with[]: {len(empty_with)}')
if empty_with:
    print(f'    Files: {", ".join(empty_with[:30])}{"..." if len(empty_with) > 30 else ""}')
print(f'  Few with[] (1-2 snippets): {len(few_with)}')
if few_with:
    for fid, n in few_with[:30]:
        print(f'    {fid}: {n} snippet(s)')
    if len(few_with) > 30:
        print(f'    ... and {len(few_with) - 30} more')
print(f'  Empty without[]: {len(empty_without)}')
if empty_without:
    print(f'    Files: {", ".join(empty_without[:30])}{"..." if len(empty_without) > 30 else ""}')

print('\n--- Snippet Integrity ---')
print(f'  With-snippets NOT in main_content: {len(bad_with)}')
for fid, i, snip in bad_with:
    print(f'    {fid}[{i}]: {snip}')
print(f'  Without-snippets FOUND in main_content: {len(bad_without)}')
for fid, i, snip in bad_without:
    print(f'    {fid}[{i}]: {snip}')

print('\n--- Formatting ---')
print(f'  Markdown headings (# or ##): {len(markdown_headings)}')
if markdown_headings:
    print(f'    Files: {", ".join(markdown_headings[:30])}{"..." if len(markdown_headings) > 30 else ""}')
print(f'  Markdown bold (**): {len(markdown_bold)}')
if markdown_bold:
    print(f'    Files: {", ".join(markdown_bold[:30])}{"..." if len(markdown_bold) > 30 else ""}')
print(f'  Bullet char (\u2022) instead of dash: {len(bullet_issues)}')
if bullet_issues:
    print(f'    Files: {", ".join(bullet_issues[:30])}{"..." if len(bullet_issues) > 30 else ""}')
print(f'  HTML tags in content: {len(html_tags)}')
if html_tags:
    print(f'    Files: {", ".join(html_tags[:20])}{"..." if len(html_tags) > 20 else ""}')

print('\n--- Encoding ---')
print(f'  Encoding artifacts (mojibake): {len(encoding_issues)}')
for fid, art in encoding_issues:
    print(f'    {fid}: found {art}')

# Content length distribution
lengths_only = [l for _, l in lengths]
print()
print('=' * 70)
print('CONTENT LENGTH DISTRIBUTION')
print('=' * 70)
print(f'  Mean:   {statistics.mean(lengths_only):>10,.0f} chars')
print(f'  Median: {statistics.median(lengths_only):>10,.0f} chars')
print(f'  Stdev:  {statistics.stdev(lengths_only):>10,.0f} chars')
print(f'  Min:    {min(lengths_only):>10,} chars')
print(f'  Max:    {max(lengths_only):>10,} chars')
print()

buckets = [
    (0, 500, '< 500'), (500, 1000, '500-1k'), (1000, 2000, '1k-2k'),
    (2000, 5000, '2k-5k'), (5000, 10000, '5k-10k'), (10000, 20000, '10k-20k'),
    (20000, 50000, '20k-50k'), (50000, 200000, '50k+')
]
for lo, hi, label in buckets:
    count = sum(1 for l in lengths_only if lo <= l < hi)
    bar = '#' * (count // 2)
    print(f'  {label:>8}: {count:3d} {bar}')

sorted_lens = sorted(lengths, key=lambda x: x[1])
print(f'\n  Shortest 10:')
for fid, l in sorted_lens[:10]:
    print(f'    {fid}: {l:>8,} chars')
print(f'\n  Longest 10:')
for fid, l in sorted_lens[-10:]:
    print(f'    {fid}: {l:>8,} chars')

# Snippet count distribution
print()
print('=' * 70)
print('SNIPPET COUNT DISTRIBUTION')
print('=' * 70)
print(f'  With:    mean={statistics.mean(with_counts):.1f}, min={min(with_counts)}, max={max(with_counts)}')
print(f'  Without: mean={statistics.mean(without_counts):.1f}, min={min(without_counts)}, max={max(without_counts)}')
for n in range(0, max(max(with_counts), max(without_counts)) + 1):
    w = sum(1 for c in with_counts if c == n)
    wo = sum(1 for c in without_counts if c == n)
    if w or wo:
        print(f'    Count {n}: with={w:3d} files, without={wo:3d} files')

# Overall score
total_issues = (len(missing_schema) + len(missing_content) + len(short_content) +
                len(no_paragraph_breaks) + len(title_in_content) + len(empty_with) +
                len(empty_without) + len(markdown_headings) + len(markdown_bold) +
                len(bullet_issues) + len(html_tags) + len(encoding_issues) +
                len(bad_with) + len(bad_without))

print()
print('=' * 70)
print('OVERALL SUMMARY')
print('=' * 70)
print(f'  Total files: {len(files)}')
print(f'  Total issue instances: {total_issues}')

# Files with any issue
issue_files = set()
issue_files.update(missing_schema)
issue_files.update(missing_content)
issue_files.update(f for f, _ in short_content)
issue_files.update(f for f, _ in no_paragraph_breaks)
issue_files.update(title_in_content)
issue_files.update(empty_with)
issue_files.update(empty_without)
issue_files.update(markdown_headings)
issue_files.update(markdown_bold)
issue_files.update(bullet_issues)
issue_files.update(html_tags)
issue_files.update(f for f, _ in encoding_issues)
issue_files.update(f for f, _, _ in bad_with)
issue_files.update(f for f, _, _ in bad_without)

clean_files = set(os.path.basename(f).replace('.json', '') for f in files) - issue_files
print(f'  Files with issues: {len(issue_files)}')
print(f'  Clean files: {len(clean_files)}')
print(f'  Clean rate: {len(clean_files)/len(files)*100:.1f}%')

# Breakdown by verified vs unverified range
verified = set()
for i in range(240, 501):
    verified.add(f'{i:04d}')
unverified = set(os.path.basename(f).replace('.json', '') for f in files) - verified

v_issues = issue_files & verified
u_issues = issue_files & unverified
print(f'\n  Verified range (0240-0500): {len(verified & set(os.path.basename(f).replace(".json","") for f in files))} files, {len(v_issues)} with issues')
print(f'  Unverified range (0001-0239): {len(unverified)} files, {len(u_issues)} with issues')
