"""
Run benchmark tests on all extractors
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
    BeautifulSoupExtractor
)

# Paths
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"  # 1,193 annotation files
RESULTS_DIR = BASE_DIR / "results"

def calculate_text_similarity(extracted: str, ground_truth: str) -> Dict[str, float]:
    """
    Calculate similarity metrics between extracted and ground truth text

    Returns precision, recall, and F1 score based on word-level overlap
    """
    if not extracted and not ground_truth:
        return {'precision': 1.0, 'recall': 1.0, 'f1': 1.0}

    if not extracted:
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

    if not ground_truth:
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

    # Normalize and tokenize
    extracted_words = set(extracted.lower().split())
    ground_truth_words = set(ground_truth.lower().split())

    # Calculate overlap
    common = extracted_words.intersection(ground_truth_words)

    precision = len(common) / len(extracted_words) if extracted_words else 0
    recall = len(common) / len(ground_truth_words) if ground_truth_words else 0

    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

def check_snippets(extracted: str, snippets: List[str]) -> Dict[str, float]:
    """
    Check how many snippets are present in extracted text

    Returns percentage of snippets found
    """
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
    """
    Evaluate extraction quality against ground truth

    Returns comprehensive evaluation metrics
    """
    # Main content similarity
    main_content_metrics = calculate_text_similarity(
        extracted.get('main_content', ''),
        ground_truth.get('main_content', '')
    )

    # "With" snippets (must be included)
    with_snippets = ground_truth.get('with', [])
    with_metrics = check_snippets(
        extracted.get('main_content', ''),
        with_snippets
    )

    # "Without" snippets (must NOT be included)
    without_snippets = ground_truth.get('without', [])
    without_metrics = check_snippets(
        extracted.get('main_content', ''),
        without_snippets
    )

    # Title match
    title_match = (
        extracted.get('title') and ground_truth.get('title') and
        extracted['title'].lower() == ground_truth['title'].lower()
    )

    return {
        'content_precision': main_content_metrics['precision'],
        'content_recall': main_content_metrics['recall'],
        'content_f1': main_content_metrics['f1'],
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
    Run benchmark on all or specific extractor

    Args:
        extractor_name: Name of specific extractor to test (or None for all)
        limit: Limit number of files to test (for quick tests)
    """
    # Initialize extractors
    extractors = {
        'trafilatura': TrafilaturaExtractor(),
        'readability': ReadabilityExtractor(),
        'boilerpy3-article': Boilerpy3Extractor('ArticleExtractor'),
        'boilerpy3-default': Boilerpy3Extractor('DefaultExtractor'),
        'beautifulsoup': BeautifulSoupExtractor(),
    }

    # Filter if specific extractor requested
    if extractor_name:
        if extractor_name not in extractors:
            print(f"Error: Unknown extractor '{extractor_name}'")
            print(f"Available: {', '.join(extractors.keys())}")
            return
        extractors = {extractor_name: extractors[extractor_name]}

    # Get all ground truth files
    ground_truth_files = sorted(GROUND_TRUTH_DIR.glob("*.json"))

    if limit:
        ground_truth_files = ground_truth_files[:limit]

    print(f"\n{'='*80}")
    print(f"Content Extraction Benchmark")
    print(f"{'='*80}\n")
    print(f"Testing {len(extractors)} extractor(s) on {len(ground_truth_files)} files\n")

    # Create results directory
    RESULTS_DIR.mkdir(exist_ok=True)

    # Run each extractor
    for ext_name, extractor in extractors.items():
        print(f"\n{'='*80}")
        print(f"Running: {extractor.name}")
        print(f"{'='*80}\n")

        results = []
        errors = 0

        for gt_file in tqdm(ground_truth_files, desc=extractor.name):
            # Load ground truth
            with open(gt_file, 'r', encoding='utf-8') as f:
                gt_data = json.load(f)

            file_id = gt_data['file_id']
            html_file = HTML_DIR / f"{file_id}.html"

            if not html_file.exists():
                print(f"Warning: HTML file {file_id}.html not found")
                continue

            # Load HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extract
            extracted = extractor.extract_safe(html_content, gt_data['url'])

            if 'error' in extracted:
                errors += 1

            # Evaluate
            evaluation = evaluate_extraction(extracted, gt_data['ground_truth'])

            # Store result
            result = {
                'file_id': file_id,
                'url': gt_data['url'],
                'extracted': extracted,
                'evaluation': evaluation
            }
            results.append(result)

        # Calculate aggregate metrics
        total_files = len(results)
        avg_precision = sum(r['evaluation']['content_precision'] for r in results) / total_files
        avg_recall = sum(r['evaluation']['content_recall'] for r in results) / total_files
        avg_f1 = sum(r['evaluation']['content_f1'] for r in results) / total_files
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
                'with_snippets_percentage': avg_with_snippets,
                'without_snippets_percentage': avg_without_snippets,
                'title_match_rate': title_match_rate,
            },
            'timestamp': datetime.now().isoformat(),
            'results': results
        }

        # Save results
        output_file = RESULTS_DIR / f"{ext_name}_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Print summary
        print(f"\n{'='*80}")
        print(f"{extractor.name} - Summary")
        print(f"{'='*80}\n")
        print(f"Files processed: {total_files}")
        print(f"Errors: {errors}\n")
        print(f"Content Metrics:")
        print(f"  Precision: {avg_precision:.3f}")
        print(f"  Recall:    {avg_recall:.3f}")
        print(f"  F1 Score:  {avg_f1:.3f}\n")
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
                'boilerpy3-default', 'beautifulsoup'],
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
