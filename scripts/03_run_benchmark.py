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
    BeautifulSoupExtractor,
    RsTrafilaturaExtractor,
    DomContentExtractionExtractor,
    DomSmoothieExtractor,
    Nanohtml2textExtractor,
    FastHtml2mdExtractor,
)

# Paths
DATA_DIR = BASE_DIR / "data"
BENCHMARK_DIR = BASE_DIR / "benchmark"
HTML_DIR = BENCHMARK_DIR / "html"
GROUND_TRUTH_DIR = BENCHMARK_DIR / "ground-truth"
RESULTS_DIR = BASE_DIR / "results"
VERIFIED_BENCHMARK_FILES = DATA_DIR / "verified_benchmark_files.json"
CATEGORY_REMOVAL_REPORT = DATA_DIR / "category_removal_report.json"
DIRECTORY_EXCLUSION_REPORT = DATA_DIR / "directory_exclusion_report.json"
INCOMPLETE_ANNOTATION_FLAGS = DATA_DIR / "incomplete_annotation_flags.json"

def load_incomplete_annotation_ids() -> set:
    """Load file IDs flagged as having incomplete annotations"""
    if not INCOMPLETE_ANNOTATION_FLAGS.exists():
        return set()
    with open(INCOMPLETE_ANNOTATION_FLAGS, 'r') as f:
        report = json.load(f)
        return set(report.get('flagged_file_ids', []))

def load_excluded_file_ids() -> set:
    """Load file IDs that should be excluded from benchmarking"""
    excluded = set()

    # Load category removal report (original filter)
    if CATEGORY_REMOVAL_REPORT.exists():
        with open(CATEGORY_REMOVAL_REPORT, 'r') as f:
            report = json.load(f)
            for category, files in report.get('removed_files', {}).items():
                for file_info in files:
                    excluded.add(file_info['file_id'])

    # Load directory exclusion report (from benchmark analysis)
    if DIRECTORY_EXCLUSION_REPORT.exists():
        with open(DIRECTORY_EXCLUSION_REPORT, 'r') as f:
            report = json.load(f)
            for file_info in report.get('excluded_files', []):
                excluded.add(file_info['file_id'])

    return excluded

def calculate_text_similarity(extracted: str, ground_truth: str) -> Dict[str, float]:
    """
    Calculate similarity metrics between extracted and ground truth text

    Returns precision, recall, F1 score, and accuracy based on word-level overlap
    """
    if not extracted and not ground_truth:
        return {'precision': 1.0, 'recall': 1.0, 'f1': 1.0, 'accuracy': 1.0}

    if not extracted:
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'accuracy': 0.0}

    if not ground_truth:
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
        'rs-trafilatura': RsTrafilaturaExtractor(),
        # New Rust extractors
        'dom-content-extraction': DomContentExtractionExtractor(),
        'dom-smoothie': DomSmoothieExtractor(),
        'nanohtml2text': Nanohtml2textExtractor(),
        'fast-html2md': FastHtml2mdExtractor(),
    }

    # Filter if specific extractor requested
    if extractor_name:
        if extractor_name not in extractors:
            print(f"Error: Unknown extractor '{extractor_name}'")
            print(f"Available: {', '.join(extractors.keys())}")
            return
        extractors = {extractor_name: extractors[extractor_name]}

    # Get ground truth files - prefer verified benchmark list if available
    incomplete_annotation_ids = load_incomplete_annotation_ids()
    if VERIFIED_BENCHMARK_FILES.exists():
        with open(VERIFIED_BENCHMARK_FILES, 'r') as f:
            verified_ids = json.load(f)
        ground_truth_files = [
            GROUND_TRUTH_DIR / f"{fid}.json" for fid in verified_ids
            if (GROUND_TRUTH_DIR / f"{fid}.json").exists()
        ]
        filter_msg = f"Using {len(ground_truth_files)} verified benchmark files"
    else:
        excluded_ids = load_excluded_file_ids()
        all_ground_truth_files = sorted(GROUND_TRUTH_DIR.glob("*.json"))
        ground_truth_files = [
            f for f in all_ground_truth_files
            if f.stem not in excluded_ids
        ]
        filter_msg = f"Excluded {len(excluded_ids)} files based on category filters"

    if limit:
        ground_truth_files = ground_truth_files[:limit]

    print(f"\n{'='*80}")
    print(f"Content Extraction Benchmark")
    print(f"{'='*80}\n")
    print(filter_msg)
    print(f"Flagged {len(incomplete_annotation_ids)} files with potentially incomplete annotations")
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

        # Calculate aggregate metrics for ALL files
        total_files = len(results)
        avg_precision = sum(r['evaluation']['content_precision'] for r in results) / total_files
        avg_recall = sum(r['evaluation']['content_recall'] for r in results) / total_files
        avg_f1 = sum(r['evaluation']['content_f1'] for r in results) / total_files
        avg_accuracy = sum(r['evaluation']['content_accuracy'] for r in results) / total_files
        avg_with_snippets = sum(r['evaluation']['with_snippets_percentage'] for r in results) / total_files
        avg_without_snippets = sum(r['evaluation']['without_snippets_percentage'] for r in results) / total_files
        title_match_rate = sum(1 for r in results if r['evaluation']['title_match']) / total_files

        # Calculate metrics for GOOD GT files (excluding incomplete annotations)
        good_gt_results = [r for r in results if r['file_id'] not in incomplete_annotation_ids]
        good_gt_count = len(good_gt_results)
        if good_gt_count > 0:
            good_gt_precision = sum(r['evaluation']['content_precision'] for r in good_gt_results) / good_gt_count
            good_gt_recall = sum(r['evaluation']['content_recall'] for r in good_gt_results) / good_gt_count
            good_gt_f1 = sum(r['evaluation']['content_f1'] for r in good_gt_results) / good_gt_count
            good_gt_accuracy = sum(r['evaluation']['content_accuracy'] for r in good_gt_results) / good_gt_count
        else:
            good_gt_precision = good_gt_recall = good_gt_f1 = good_gt_accuracy = 0.0

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
            'metrics_good_gt': {
                'files_count': good_gt_count,
                'content_precision': good_gt_precision,
                'content_recall': good_gt_recall,
                'content_f1': good_gt_f1,
                'content_accuracy': good_gt_accuracy,
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
        print(f"Content Metrics (all {total_files} files):")
        print(f"  Precision: {avg_precision:.3f}")
        print(f"  Recall:    {avg_recall:.3f}")
        print(f"  F1 Score:  {avg_f1:.3f}")
        print(f"  Accuracy:  {avg_accuracy:.3f}\n")
        print(f"Content Metrics (good GT only, {good_gt_count} files):")
        print(f"  Precision: {good_gt_precision:.3f}")
        print(f"  Recall:    {good_gt_recall:.3f}")
        print(f"  F1 Score:  {good_gt_f1:.3f}")
        print(f"  Accuracy:  {good_gt_accuracy:.3f}\n")
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
                'dom-content-extraction', 'dom-smoothie', 'nanohtml2text', 'fast-html2md'],
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
