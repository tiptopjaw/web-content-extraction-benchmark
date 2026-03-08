#!/usr/bin/env python3
"""Audit ground truth files against HTML to find mismatches."""

import json
import os
import re
import unicodedata
from html.parser import HTMLParser

BASE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.join(BASE, '..', 'data', 'html_files')
VERIFIED_DIR = os.path.join(BASE, 'verified')

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip_tags = {'script', 'style', 'noscript', 'svg', 'head'}
        self.current_skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.current_skip += 1

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.current_skip = max(0, self.current_skip - 1)

    def handle_data(self, data):
        if self.current_skip == 0:
            self.result.append(data)

    def handle_entityref(self, name):
        from html import unescape
        if self.current_skip == 0:
            self.result.append(unescape(f'&{name};'))

    def handle_charref(self, name):
        from html import unescape
        if self.current_skip == 0:
            self.result.append(unescape(f'&#{name};'))

    def get_text(self):
        return ' '.join(self.result)

def normalize(text):
    """Normalize text for comparison."""
    if not text:
        return ''
    # Unicode normalize
    text = unicodedata.normalize('NFKD', text)
    # Curly quotes to straight
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    # Dashes
    text = text.replace('\u2014', '-').replace('\u2013', '-')
    text = text.replace('\u00a0', ' ')
    # Ellipsis
    text = text.replace('\u2026', '...')
    # BOM / zero-width chars
    text = text.replace('\uFEFF', '').replace('\u200B', '')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip().lower()
    # Fix spaces before punctuation (caused by HTML tag boundaries)
    # e.g. "text </strong>: more" -> "text : more" should become "text: more"
    text = re.sub(r'\s+([,:;.!?)])', r'\1', text)
    # Fix spaces after opening quotes/parens
    text = re.sub(r'([("\'"])\s+', r'\1', text)
    return text

def extract_title_from_html(file_id):
    """Extract the <title> tag content from HTML."""
    html_path = os.path.join(HTML_DIR, f'{file_id}.html')
    if not os.path.exists(html_path):
        return ''
    with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    if m:
        from html import unescape
        return unescape(m.group(1).strip())
    return ''

def extract_html_text(file_id):
    """Extract plain text from HTML file."""
    html_path = os.path.join(HTML_DIR, f'{file_id}.html')
    if not os.path.exists(html_path):
        return None
    with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html)
    except:
        pass
    return extractor.get_text()

def split_sentences(text):
    """Split text into sentences."""
    # Split on period/question/exclamation followed by space and capital, or on newlines
    parts = re.split(r'\n+', text)
    sentences = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Further split on sentence boundaries
        sents = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', part)
        for s in sents:
            s = s.strip()
            if len(s) > 20:  # Skip very short fragments
                sentences.append(s)
    return sentences

def check_sentence_in_html(sentence, html_text_normalized):
    """Check if a sentence exists in the HTML text."""
    norm_sent = normalize(sentence)
    if not norm_sent:
        return True

    # Direct match
    if norm_sent in html_text_normalized:
        return True

    # Try with first/last 40 chars (handles minor middle differences)
    if len(norm_sent) > 80:
        first = norm_sent[:40]
        last = norm_sent[-40:]
        if first in html_text_normalized and last in html_text_normalized:
            return True

    # Try shingle matching - use 4-word shingles for shorter sentences, 6 for longer
    words = norm_sent.split()
    if len(words) >= 4:
        shingle_size = 4 if len(words) < 8 else 6
        total = len(words) - shingle_size + 1
        if total > 0:
            matches = 0
            for i in range(total):
                shingle = ' '.join(words[i:i+shingle_size])
                if shingle in html_text_normalized:
                    matches += 1
            ratio = matches / total
            if ratio > 0.6:
                return True

    return False

def audit_file(file_id):
    """Audit a single file's ground truth against HTML."""
    verified_path = os.path.join(VERIFIED_DIR, f'{file_id}.json')
    if not os.path.exists(verified_path):
        return None

    with open(verified_path, 'r') as f:
        data = json.load(f)

    gt = data.get('ground_truth', {})
    main_content = gt.get('main_content', '')
    with_snippets = gt.get('with', [])

    html_text = extract_html_text(file_id)
    if not html_text:
        return {'error': 'HTML file not found'}

    html_norm = normalize(html_text)

    # Check sentences in main_content
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

    # Check title - also check against <title> tag which is in <head> (excluded from body text)
    title = gt.get('title', '')
    title_ok = True
    if title:
        title_ok = check_sentence_in_html(title, html_norm)
        if not title_ok:
            # Title might only be in <title> tag (inside <head>, excluded from body)
            html_title = extract_title_from_html(file_id)
            if html_title:
                html_title_norm = normalize(html_title)
                gt_title_norm = normalize(title)
                # Check if GT title is a substring of HTML title or vice versa
                if gt_title_norm in html_title_norm or html_title_norm in gt_title_norm:
                    title_ok = True
                # Also check if most words match (titles often have site name appended)
                elif len(gt_title_norm) > 10:
                    gt_words = set(gt_title_norm.split())
                    html_words = set(html_title_norm.split())
                    overlap = len(gt_words & html_words) / max(len(gt_words), 1)
                    if overlap > 0.7:
                        title_ok = True

    return {
        'total_sentences': len(sentences),
        'missing_sentences': missing_sentences,
        'missing_count': len(missing_sentences),
        'bad_with': bad_with,
        'title_ok': title_ok,
        'content_length': len(main_content),
    }

def main():
    # Load progress to find approved files
    progress_path = os.path.join(BASE, 'progress.json')
    with open(progress_path, 'r') as f:
        progress = json.load(f)

    approved = [fid for fid, info in progress.items() if info['status'] == 'approved']
    approved.sort()

    print(f"Auditing {len(approved)} approved files...\n")

    clean = []
    needs_fix = []

    for fid in approved:
        result = audit_file(fid)
        if result is None:
            print(f"  {fid}: NO VERIFIED FILE")
            continue
        if 'error' in result:
            print(f"  {fid}: {result['error']}")
            continue

        issues = result['missing_count'] + len(result['bad_with'])
        if not result['title_ok']:
            issues += 1

        if issues == 0:
            clean.append(fid)
            print(f"  {fid}: CLEAN ({result['total_sentences']} sentences, {result['content_length']} chars)")
        else:
            needs_fix.append((fid, result))
            print(f"  {fid}: NEEDS FIX - {result['missing_count']} missing sentences, {len(result['bad_with'])} bad 'with' snippets, title_ok={result['title_ok']}")
            if result['missing_sentences']:
                for ms in result['missing_sentences'][:3]:
                    print(f"         MISS: {ms[:100]}...")
            if result['bad_with']:
                for bw in result['bad_with']:
                    print(f"         BAD WITH: {bw[:100]}...")

    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(clean)} clean, {len(needs_fix)} need fixes")
    print(f"Clean: {', '.join(clean)}")
    print(f"Need fix: {', '.join(fid for fid, _ in needs_fix)}")

if __name__ == '__main__':
    main()
