#!/usr/bin/env python3
"""Annotate stub GT files using pre-extracted text from BeautifulSoup.

Reads /tmp/extracted_text/{id}.txt files and generates proper GT annotations
with main_content, title, with/without snippets.
"""

import json
import glob
import os
import re
from bs4 import BeautifulSoup


def extract_content_from_html(html_path):
    """Extract structured content directly from HTML using BeautifulSoup."""
    with open(html_path, 'r', errors='replace') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Get title
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else ''

    # Get h1
    h1 = soup.find('h1')
    h1_text = h1.get_text(strip=True) if h1 else ''

    # Remove unwanted elements
    for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'svg']):
        tag.decompose()

    # Try to find main content area
    main = None
    for selector in [
        lambda s: s.find('article'),
        lambda s: s.find('main'),
        lambda s: s.find(attrs={'role': 'main'}),
        lambda s: s.find(id='content'),
        lambda s: s.find(id='main-content'),
        lambda s: s.find(class_='content'),
        lambda s: s.find(class_='post-content'),
        lambda s: s.find(class_='article-content'),
        lambda s: s.find(class_='entry-content'),
        lambda s: s.find(class_='documentation-content'),
        lambda s: s.find(class_='doc-content'),
        lambda s: s.find(class_='product-detail'),
        lambda s: s.find(class_='product-info'),
    ]:
        main = selector(soup)
        if main:
            break

    if not main:
        main = soup.find('body') or soup

    # Remove nav, footer, aside within main
    for tag in main.find_all(['nav', 'footer', 'aside']):
        tag.decompose()

    # Build content with structure
    content_parts = []
    seen_texts = set()

    for el in main.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'pre',
                              'blockquote', 'dt', 'dd', 'figcaption', 'td', 'th',
                              'summary', 'label', 'span', 'div']):
        # Skip nested elements to avoid duplication
        if el.name in ('span', 'div'):
            # Only include if it's a direct text container (no block children)
            if el.find(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'table']):
                continue
            # Only include divs/spans with substantial direct text
            text = el.get_text(separator=' ', strip=True)
            if len(text) < 20:
                continue
        else:
            text = el.get_text(separator=' ', strip=True)

        if not text or len(text) < 3:
            continue

        # Deduplicate
        text_key = text[:100]
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)

        if el.name.startswith('h'):
            level = int(el.name[1])
            content_parts.append(('heading', text, level))
        elif el.name == 'li':
            content_parts.append(('list_item', text, 0))
        elif el.name == 'pre':
            content_parts.append(('code', text, 0))
        elif el.name in ('td', 'th'):
            content_parts.append(('table_cell', text, 0))
        elif el.name == 'blockquote':
            content_parts.append(('quote', text, 0))
        else:
            content_parts.append(('paragraph', text, 0))

    # Format content
    lines = []
    prev_type = None
    table_row = []

    for part_type, text, level in content_parts:
        if part_type == 'heading':
            if lines:
                lines.append('')  # blank line before heading
            lines.append(text)
            lines.append('')  # blank line after heading
        elif part_type == 'list_item':
            lines.append(f'- {text}')
        elif part_type == 'code':
            if lines and lines[-1] != '':
                lines.append('')
            lines.append(text)
            lines.append('')
        elif part_type == 'table_cell':
            # Skip table cells for now, they're hard to format properly
            continue
        elif part_type == 'quote':
            if lines and lines[-1] != '':
                lines.append('')
            lines.append(text)
            lines.append('')
        else:
            if prev_type == 'list_item' and part_type == 'paragraph':
                lines.append('')  # blank line after list
            if lines and lines[-1] != '' and prev_type != 'list_item':
                lines.append('')  # blank line between paragraphs
            lines.append(text)

        prev_type = part_type

    main_content = '\n'.join(lines).strip()

    # Clean up excessive blank lines
    main_content = re.sub(r'\n{3,}', '\n\n', main_content)

    # Remove title from start of content if it appears there
    if h1_text and main_content.startswith(h1_text):
        main_content = main_content[len(h1_text):].lstrip('\n')
    if title and main_content.startswith(title):
        main_content = main_content[len(title):].lstrip('\n')

    # Extract nav/footer text for without-snippets
    soup2 = BeautifulSoup(html, 'html.parser')
    for tag in soup2.find_all(['script', 'style', 'noscript']):
        tag.decompose()

    nav_footer_texts = []
    for tag in soup2.find_all(['nav', 'footer', 'header']):
        for el in tag.find_all(['a', 'span', 'p', 'li']):
            t = el.get_text(strip=True)
            if t and 10 < len(t) < 200:
                # Make sure it's not in main_content
                if t not in main_content:
                    nav_footer_texts.append(t)

    nav_footer_texts = list(dict.fromkeys(nav_footer_texts))

    # Use clean title
    clean_title = h1_text if h1_text else title
    # Remove site name suffixes
    for suffix in [' - Wikipedia', ' | MDN', ' - MDN Web Docs',
                   ' — Python documentation', ' - Stack Overflow',
                   ' - Super User', ' | Hacker News', ' - GeeksforGeeks']:
        if clean_title.endswith(suffix):
            clean_title = clean_title[:-len(suffix)]

    return clean_title, main_content, nav_footer_texts


def generate_with_snippets(main_content, n=5):
    """Pick representative sentences from different parts of main_content."""
    if not main_content or len(main_content) < 50:
        return []

    # Split into sentences/paragraphs
    paragraphs = [p.strip() for p in main_content.split('\n\n') if p.strip() and len(p.strip()) > 20]
    if not paragraphs:
        paragraphs = [p.strip() for p in main_content.split('\n') if p.strip() and len(p.strip()) > 20]

    if not paragraphs:
        return []

    snippets = []
    # Pick from evenly spaced positions
    step = max(1, len(paragraphs) // n)
    for i in range(0, len(paragraphs), step):
        if len(snippets) >= n:
            break
        p = paragraphs[i]
        # Pick a sentence or the whole paragraph if short
        sentences = re.split(r'(?<=[.!?])\s+', p)
        for s in sentences:
            s = s.strip()
            if 20 < len(s) < 300 and s in main_content:
                snippets.append(s)
                break
        else:
            # Use first 200 chars if no good sentence found
            snippet = p[:200].strip()
            if snippet in main_content:
                snippets.append(snippet)

    return snippets[:n]


def generate_without_snippets(nav_footer_texts, main_content, n=5):
    """Pick boilerplate text that should NOT be in main_content."""
    snippets = []
    for t in nav_footer_texts:
        if t not in main_content and len(t) > 10:
            snippets.append(t)
            if len(snippets) >= n:
                break
    return snippets


def annotate_stub(fid):
    """Annotate a single stub GT file."""
    gt_path = f'benchmark/ground-truth/{fid}.json'
    html_path = f'benchmark/html/{fid}.html'

    if not os.path.exists(html_path):
        return False, f"HTML missing: {html_path}"

    with open(gt_path) as f:
        gt = json.load(f)

    try:
        title, main_content, nav_footer = extract_content_from_html(html_path)
    except Exception as e:
        return False, f"Extraction error: {e}"

    if not main_content or len(main_content) < 30:
        return False, f"Too little content extracted ({len(main_content)} chars)"

    # Generate snippets
    with_snippets = generate_with_snippets(main_content)
    without_snippets = generate_without_snippets(nav_footer, main_content)

    # Update GT
    gt['ground_truth']['title'] = title
    gt['ground_truth']['main_content'] = main_content
    gt['ground_truth']['with'] = with_snippets
    gt['ground_truth']['without'] = without_snippets

    # Write back
    with open(gt_path, 'w') as f:
        json.dump(gt, f, indent=2, ensure_ascii=False)

    return True, f"OK: {len(main_content)} chars, {len(with_snippets)} with, {len(without_snippets)} without"


def main():
    # Find all stubs
    stubs = []
    for f in sorted(glob.glob('benchmark/ground-truth/*.json')):
        with open(f) as fh:
            d = json.load(fh)
        mc = d.get('ground_truth', {}).get('main_content', '')
        if not mc or len(mc) < 50:
            stubs.append(d.get('file_id', ''))

    print(f"Found {len(stubs)} stubs to annotate")

    success = 0
    failed = 0
    too_small = 0

    for fid in stubs:
        ok, msg = annotate_stub(fid)
        if ok:
            success += 1
            print(f"  {fid}: {msg}")
        else:
            failed += 1
            if 'Too little' in msg:
                too_small += 1
            print(f"  {fid}: FAILED - {msg}")

    print(f"\nDone: {success} annotated, {failed} failed ({too_small} too small)")


if __name__ == '__main__':
    main()
