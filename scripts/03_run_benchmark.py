"""
Run benchmark tests on all extractors.

Uses all ground truth files in benchmark/ground-truth/ paired with
matching HTML files in benchmark/html/. No external exclusion lists.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List
import argparse
from datetime import datetime
from tqdm import tqdm

# Add parent directory to path to import extractors
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from extractors import (
    TrafilaturaExtractor,
    ReadabilityExtractor,
    Boilerpy3Extractor,
    BeautifulSoupExtractor,
    RsTrafilaturaExtractor,
    DomContentExtractionExtractor,
    DomSmoothieExtractor,
    Nanohtml2textExtractor,
    FastHtml2mdExtractor,
    MagicHtmlExtractor,
    MineruHtmlExtractor,
    ReaderLmExtractor,
)

# Paths
BENCHMARK_DIR = BASE_DIR / "benchmark"
HTML_DIR = BENCHMARK_DIR / "html"
GROUND_TRUTH_DIR = BENCHMARK_DIR / "ground-truth"
RESULTS_DIR = BASE_DIR / "results"


def calculate_text_similarity(extracted: str, ground_truth: str) -> Dict[str, float]:
    """
    Calculate similarity metrics between extracted and ground truth text.

    Returns precision, recall, F1 score, and accuracy based on word-level overlap.
    """
    if not extracted and not ground_truth:
        return {'precision': 1.0, 'recall': 1.0, 'f1': 1.0, 'accuracy': 1.0}

    if not extracted or not ground_truth:
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'accuracy': 0.0}

    # Normalize and tokenize
    extracted_words = extracted.lower().split()
    ground_truth_words = ground_truth.lower().split()

    # Calculate accuracy (exact match after tokenization)
    accuracy = 1.0 if extracted_words == ground_truth_words else 0.0

    # Convert to sets for precision/recall calculation
    extracted_set = set(extracted_words)
    ground_truth_set = set(ground_truth_words)

    # Calculate overlap
    common = extracted_set.intersection(ground_truth_set)

    precision = len(common) / len(extracted_set) if extracted_set else 0
    recall = len(common) / len(ground_truth_set) if ground_truth_set else 0

    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'accuracy': accuracy
    }


def check_snippets(extracted: str, snippets: List[str]) -> Dict[str, float]:
    """Check how many snippets are present in extracted text."""
    if not snippets:
        return {'found': 0, 'total': 0, 'percentage': 1.0}

    extracted_lower = extracted.lower()
    found = sum(1 for snippet in snippets if snippet.lower() in extracted_lower)

    return {
        'found': found,
        'total': len(snippets),
        'percentage': found / len(snippets) if snippets else 1.0
    }


def evaluate_extraction(extracted: Dict, ground_truth: Dict) -> Dict:
    """Evaluate extraction quality against ground truth."""
    main_content_metrics = calculate_text_similarity(
        extracted.get('main_content', ''),
        ground_truth.get('main_content', '')
    )

    with_metrics = check_snippets(
        extracted.get('main_content', ''),
        ground_truth.get('with', [])
    )

    without_metrics = check_snippets(
        extracted.get('main_content', ''),
        ground_truth.get('without', [])
    )

    title_match = (
        extracted.get('title') and ground_truth.get('title') and
        extracted['title'].lower() == ground_truth['title'].lower()
    )

    return {
        'content_precision': main_content_metrics['precision'],
        'content_recall': main_content_metrics['recall'],
        'content_f1': main_content_metrics['f1'],
        'content_accuracy': main_content_metrics['accuracy'],
        'with_snippets_found': with_metrics['found'],
        'with_snippets_total': with_metrics['total'],
        'with_snippets_percentage': with_metrics['percentage'],
        'without_snippets_found': without_metrics['found'],
        'without_snippets_total': without_metrics['total'],
        'without_snippets_percentage': without_metrics['percentage'],
        'title_match': title_match,
        'extracted_length': len(extracted.get('main_content', '')),
        'ground_truth_length': len(ground_truth.get('main_content', '')),
    }


def run_benchmark(extractor_name: str = None, limit: int = None):
    """
    Run benchmark on all or specific extractor.

    Args:
        extractor_name: Name of specific extractor to test (or None for all)
        limit: Limit number of files to test (for quick tests)
    """
    extractors = {
        'trafilatura': TrafilaturaExtractor(),
        'readability': ReadabilityExtractor(),
        'boilerpy3-article': Boilerpy3Extractor('ArticleExtractor'),
        'boilerpy3-default': Boilerpy3Extractor('DefaultExtractor'),
        'beautifulsoup': BeautifulSoupExtractor(),
        'rs-trafilatura': RsTrafilaturaExtractor(),
        'dom-content-extraction': DomContentExtractionExtractor(),
        'dom-smoothie': DomSmoothieExtractor(),
        'nanohtml2text': Nanohtml2textExtractor(),
        'fast-html2md': FastHtml2mdExtractor(),
        'magic-html': MagicHtmlExtractor(),
        'mineru-html': MineruHtmlExtractor(),
        'readerlm-v2': ReaderLmExtractor(),
    }

    if extractor_name:
        if extractor_name not in extractors:
            print(f"Error: Unknown extractor '{extractor_name}'")
            print(f"Available: {', '.join(extractors.keys())}")
            return
        extractors = {extractor_name: extractors[extractor_name]}

    # Use all ground truth files that have matching HTML
    ground_truth_files = sorted(GROUND_TRUTH_DIR.glob("*.json"))
    ground_truth_files = [
        f for f in ground_truth_files
        if (HTML_DIR / f"{f.stem}.html").exists()
    ]

    if limit:
        ground_truth_files = ground_truth_files[:limit]

    print(f"\n{'='*80}")
    print(f"Content Extraction Benchmark")
    print(f"{'='*80}\n")
    print(f"Testing {len(extractors)} extractor(s) on {len(ground_truth_files)} files\n")

    RESULTS_DIR.mkdir(exist_ok=True)

    for ext_name, extractor in extractors.items():
        print(f"\n{'='*80}")
        print(f"Running: {extractor.name}")
        print(f"{'='*80}\n")

        results = []
        errors = 0
        extractor_start_time = datetime.now()

        for gt_file in tqdm(ground_truth_files, desc=extractor.name):
            with open(gt_file, 'r', encoding='utf-8') as f:
                gt_data = json.load(f)

            file_id = gt_data['file_id']
            html_file = HTML_DIR / f"{file_id}.html"

            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            extracted = extractor.extract_safe(html_content, gt_data.get('url', ''))

            if 'error' in extracted:
                errors += 1

            evaluation = evaluate_extraction(extracted, gt_data['ground_truth'])

            results.append({
                'file_id': file_id,
                'url': gt_data.get('url', ''),
                'extracted': extracted,
                'evaluation': evaluation
            })

        extractor_elapsed = (datetime.now() - extractor_start_time).total_seconds()

        total_files = len(results)
        avg_precision = sum(r['evaluation']['content_precision'] for r in results) / total_files
        avg_recall = sum(r['evaluation']['content_recall'] for r in results) / total_files
        avg_f1 = sum(r['evaluation']['content_f1'] for r in results) / total_files
        avg_accuracy = sum(r['evaluation']['content_accuracy'] for r in results) / total_files
        avg_with_snippets = sum(r['evaluation']['with_snippets_percentage'] for r in results) / total_files
        avg_without_snippets = sum(r['evaluation']['without_snippets_percentage'] for r in results) / total_files
        title_match_rate = sum(1 for r in results if r['evaluation']['title_match']) / total_files

        summary = {
            'extractor': extractor.name,
            'extractor_key': ext_name,
            'total_files': total_files,
            'errors': errors,
            'metrics': {
                'content_precision': avg_precision,
                'content_recall': avg_recall,
                'content_f1': avg_f1,
                'content_accuracy': avg_accuracy,
                'with_snippets_percentage': avg_with_snippets,
                'without_snippets_percentage': avg_without_snippets,
                'title_match_rate': title_match_rate,
            },
            'timing': {
                'total_seconds': extractor_elapsed,
                'per_file_seconds': extractor_elapsed / total_files if total_files else 0,
            },
            'timestamp': datetime.now().isoformat(),
            'results': results
        }

        output_file = RESULTS_DIR / f"{ext_name}_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*80}")
        print(f"{extractor.name} - Summary")
        print(f"{'='*80}\n")
        print(f"Files processed: {total_files}")
        print(f"Errors: {errors}")
        print(f"Time: {extractor_elapsed:.1f}s ({extractor_elapsed/total_files:.1f}s/file)\n")
        print(f"Content Metrics:")
        print(f"  Precision: {avg_precision:.3f}")
        print(f"  Recall:    {avg_recall:.3f}")
        print(f"  F1 Score:  {avg_f1:.3f}")
        print(f"  Accuracy:  {avg_accuracy:.3f}\n")
        print(f"Snippet Metrics:")
        print(f"  'With' snippets found:    {avg_with_snippets:.1%}")
        print(f"  'Without' snippets found: {avg_without_snippets:.1%} (lower is better)\n")
        print(f"Title match rate: {title_match_rate:.1%}\n")
        print(f"Results saved to: {output_file}")

    print(f"\n{'='*80}")
    print(f"Benchmark Complete!")
    print(f"{'='*80}\n")
    print(f"Results saved to: {RESULTS_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Run content extraction benchmark")
    parser.add_argument(
        '--extractor',
        choices=['trafilatura', 'readability', 'boilerpy3-article',
                'boilerpy3-default', 'beautifulsoup', 'rs-trafilatura',
                'dom-content-extraction', 'dom-smoothie', 'nanohtml2text', 'fast-html2md',
                'magic-html', 'mineru-html', 'readerlm-v2'],
        help="Test only specific extractor (default: all)"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help="Limit number of files to test (for quick tests)"
    )

    args = parser.parse_args()
    run_benchmark(args.extractor, args.limit)


if __name__ == "__main__":
    main()
