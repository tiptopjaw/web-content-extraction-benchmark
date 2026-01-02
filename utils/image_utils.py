"""
Image normalization and matching utilities for benchmarking
"""
import re
from urllib.parse import urlparse, unquote
from typing import List, Dict, Optional, Tuple


def normalize_filename(url_or_filename: str) -> str:
    """
    Extract and normalize filename from URL or path

    - Extracts filename from URL path
    - Removes query parameters
    - Lowercases
    - Handles encoded characters
    """
    if not url_or_filename:
        return ""

    # Parse URL if it looks like one
    if url_or_filename.startswith(('http://', 'https://', '//')):
        parsed = urlparse(url_or_filename)
        path = parsed.path
    else:
        path = url_or_filename

    # URL decode
    path = unquote(path)

    # Extract filename from path
    filename = path.rstrip('/').split('/')[-1]

    # Remove query string if present (shouldn't be after urlparse, but safety check)
    filename = filename.split('?')[0]
    filename = filename.split('#')[0]

    # Lowercase for comparison
    filename = filename.lower()

    return filename


def normalize_image_src(src: str) -> str:
    """
    Normalize image source URL for comparison

    - Handles protocol-relative URLs
    - Removes tracking parameters
    - Normalizes CDN variations
    """
    if not src:
        return ""

    # Handle protocol-relative URLs
    if src.startswith('//'):
        src = 'https:' + src

    # Parse
    parsed = urlparse(src)

    # Reconstruct without query/fragment for comparison
    # Keep path only for matching
    normalized = parsed.path.lower()

    return normalized


def extract_real_src(img_attrs: Dict[str, str]) -> str:
    """
    Extract the real image source from potentially lazy-loaded image

    Checks attributes in order:
    1. data-src
    2. data-lazy-src
    3. data-original
    4. data-srcset (first URL)
    5. srcset (first URL)
    6. src

    Returns the most likely real image URL
    """
    # Priority order for lazy-loading attributes
    lazy_attrs = ['data-src', 'data-lazy-src', 'data-original', 'data-lazy', 'data-url']

    for attr in lazy_attrs:
        if attr in img_attrs and img_attrs[attr]:
            return img_attrs[attr]

    # Check srcset
    for attr in ['data-srcset', 'srcset']:
        if attr in img_attrs and img_attrs[attr]:
            # Extract first URL from srcset
            srcset = img_attrs[attr]
            first_src = srcset.split(',')[0].strip().split()[0]
            if first_src and not first_src.startswith('data:'):
                return first_src

    # Fallback to src
    src = img_attrs.get('src', '')

    # Skip base64 data URLs and placeholder patterns
    if src.startswith('data:'):
        return ""

    placeholder_patterns = [
        'placeholder', 'loading', 'blank', 'pixel',
        '1x1', 'spacer', 'transparent'
    ]
    src_lower = src.lower()
    if any(p in src_lower for p in placeholder_patterns):
        # Check if there's a real src elsewhere
        for attr in lazy_attrs:
            if attr in img_attrs:
                return img_attrs[attr]

    return src


def match_images(extracted: List[Dict], ground_truth: List[Dict],
                 threshold: float = 0.8) -> Dict:
    """
    Match extracted images against ground truth

    Returns:
        {
            'matched': [(gt_idx, ex_idx, score), ...],
            'gt_unmatched': [idx, ...],
            'ex_unmatched': [idx, ...],
            'precision': float,
            'recall': float,
            'f1': float
        }
    """
    if not ground_truth:
        return {
            'matched': [],
            'gt_unmatched': [],
            'ex_unmatched': list(range(len(extracted))),
            'precision': 1.0 if not extracted else 0.0,
            'recall': 1.0,
            'f1': 1.0 if not extracted else 0.0
        }

    if not extracted:
        return {
            'matched': [],
            'gt_unmatched': list(range(len(ground_truth))),
            'ex_unmatched': [],
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0
        }

    # Normalize filenames
    gt_filenames = [normalize_filename(img.get('filename', img.get('src', '')))
                    for img in ground_truth]
    ex_filenames = [normalize_filename(img.get('filename', img.get('src', '')))
                    for img in extracted]

    matched = []
    gt_used = set()
    ex_used = set()

    # First pass: exact matches
    for ex_idx, ex_fn in enumerate(ex_filenames):
        if not ex_fn:
            continue
        for gt_idx, gt_fn in enumerate(gt_filenames):
            if gt_idx in gt_used:
                continue
            if ex_fn == gt_fn:
                matched.append((gt_idx, ex_idx, 1.0))
                gt_used.add(gt_idx)
                ex_used.add(ex_idx)
                break

    # Second pass: partial matches (filename contains)
    for ex_idx, ex_fn in enumerate(ex_filenames):
        if ex_idx in ex_used or not ex_fn:
            continue
        for gt_idx, gt_fn in enumerate(gt_filenames):
            if gt_idx in gt_used or not gt_fn:
                continue
            # Check if one contains the other
            if ex_fn in gt_fn or gt_fn in ex_fn:
                matched.append((gt_idx, ex_idx, 0.9))
                gt_used.add(gt_idx)
                ex_used.add(ex_idx)
                break

    gt_unmatched = [i for i in range(len(ground_truth)) if i not in gt_used]
    ex_unmatched = [i for i in range(len(extracted)) if i not in ex_used]

    # Calculate metrics
    true_positives = len(matched)
    precision = true_positives / len(extracted) if extracted else 0.0
    recall = true_positives / len(ground_truth) if ground_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'matched': matched,
        'gt_unmatched': gt_unmatched,
        'ex_unmatched': ex_unmatched,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def evaluate_image_metadata(extracted: Dict, ground_truth: Dict) -> Dict:
    """
    Evaluate extracted image metadata against ground truth

    Checks: alt text, caption
    """
    results = {
        'alt_match': False,
        'caption_match': False,
        'alt_similarity': 0.0,
        'caption_similarity': 0.0
    }

    # Alt text comparison
    ex_alt = (extracted.get('alt') or '').lower().strip()
    gt_alt = (ground_truth.get('alt') or '').lower().strip()

    if ex_alt and gt_alt:
        # Simple containment check
        if ex_alt == gt_alt:
            results['alt_match'] = True
            results['alt_similarity'] = 1.0
        elif ex_alt in gt_alt or gt_alt in ex_alt:
            results['alt_similarity'] = 0.8
    elif not ex_alt and not gt_alt:
        results['alt_match'] = True
        results['alt_similarity'] = 1.0

    # Caption comparison
    ex_caption = (extracted.get('caption') or '').lower().strip()
    gt_caption = (ground_truth.get('caption') or '').lower().strip()

    if ex_caption and gt_caption:
        if ex_caption == gt_caption:
            results['caption_match'] = True
            results['caption_similarity'] = 1.0
        elif ex_caption in gt_caption or gt_caption in ex_caption:
            results['caption_similarity'] = 0.8
    elif not ex_caption and not gt_caption:
        results['caption_match'] = True
        results['caption_similarity'] = 1.0

    return results


def evaluate_hero_image(extracted: List[Dict], ground_truth: List[Dict]) -> Dict:
    """
    Evaluate hero image detection

    Returns:
        {
            'hero_found': bool,
            'correct_hero': bool,
            'hero_position': int or None
        }
    """
    # Find hero in ground truth
    gt_hero = None
    gt_hero_idx = None
    for idx, img in enumerate(ground_truth):
        if img.get('is_hero', False):
            gt_hero = img
            gt_hero_idx = idx
            break

    if gt_hero is None:
        return {
            'hero_found': False,
            'correct_hero': True,  # No hero expected, so not finding one is correct
            'hero_position': None
        }

    # Find hero in extracted
    ex_hero = None
    ex_hero_idx = None
    for idx, img in enumerate(extracted):
        if img.get('is_hero', False):
            ex_hero = img
            ex_hero_idx = idx
            break

    if ex_hero is None:
        return {
            'hero_found': False,
            'correct_hero': False,
            'hero_position': None
        }

    # Check if correct hero
    gt_fn = normalize_filename(gt_hero.get('filename', gt_hero.get('src', '')))
    ex_fn = normalize_filename(ex_hero.get('filename', ex_hero.get('src', '')))

    correct = gt_fn == ex_fn or (gt_fn and ex_fn and (gt_fn in ex_fn or ex_fn in gt_fn))

    return {
        'hero_found': True,
        'correct_hero': correct,
        'hero_position': ex_hero_idx
    }
