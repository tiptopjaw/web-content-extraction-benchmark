"""
Benchmark rs-trafilatura vs go-trafilatura on modern web pages

Runs both extractors on 488 annotated HTML files and compares results.
"""
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from tqdm import tqdm


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


def run_rs_trafilatura(html_file: Path, binary_path: Path) -> Dict:
    """Run rs-trafilatura and parse JSON output"""
    try:
        result = subprocess.run(
            [str(binary_path), str(html_file)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {'error': f'Exit code {result.returncode}', 'main_content': ''}

        data = json.loads(result.stdout)
        return {
            'title': data.get('title'),
            'author': data.get('author'),
            'date': data.get('date'),
            'main_content': data.get('main_content', ''),
            'hostname': data.get('hostname'),
            'description': data.get('description'),
            'sitename': data.get('sitename'),
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Timeout', 'main_content': ''}
    except json.JSONDecodeError as e:
        return {'error': f'JSON parse error: {e}', 'main_content': ''}
    except Exception as e:
        return {'error': f'Unexpected error: {e}', 'main_content': ''}


def run_go_trafilatura(html_file: Path, binary_path: Path) -> Dict:
    """Run go-trafilatura and parse JSON output"""
    try:
        result = subprocess.run(
            [str(binary_path), '-f', 'json', str(html_file)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {'error': f'Exit code {result.returncode}', 'main_content': ''}

        data = json.loads(result.stdout)
        metadata = data.get('metadata', {})

        return {
            'title': metadata.get('title'),
            'author': metadata.get('author'),
            'date': metadata.get('date'),
            'main_content': data.get('contentText', ''),
            'hostname': metadata.get('hostname'),
            'description': metadata.get('description'),
            'sitename': metadata.get('sitename'),
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Timeout', 'main_content': ''}
    except json.JSONDecodeError as e:
        return {'error': f'JSON parse error: {e}', 'main_content': ''}
    except Exception as e:
        return {'error': f'Unexpected error: {e}', 'main_content': ''}


def evaluate_extraction(extracted: Dict, ground_truth: Dict) -> Dict:
    """Evaluate extraction quality against ground truth"""
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
        'has_error': 'error' in extracted,
        'error': extracted.get('error', None),
    }


def run_benchmark(
    rs_binary: Path,
    go_binary: Path,
    ground_truth_dir: Path,
    html_dir: Path,
    output_file: Path
):
    """Run benchmark comparing both extractors"""

    # Get all ground truth files
    gt_files = sorted(ground_truth_dir.glob("*.json"))

    print(f"\n{'='*80}")
    print(f"rs-trafilatura vs go-trafilatura Benchmark")
    print(f"{'='*80}\n")
    print(f"Ground truth files: {len(gt_files)}")
    print(f"RS binary: {rs_binary}")
    print(f"GO binary: {go_binary}\n")

    rs_results = []
    go_results = []
    rs_errors = 0
    go_errors = 0

    for gt_file in tqdm(gt_files, desc="Running benchmark"):
        # Load ground truth
        with open(gt_file, 'r', encoding='utf-8') as f:
            gt_data = json.load(f)

        file_id = gt_data['file_id']
        html_file = html_dir / f"{file_id}.html"

        if not html_file.exists():
            print(f"Warning: HTML file {file_id}.html not found")
            continue

        # Run both extractors
        rs_extracted = run_rs_trafilatura(html_file, rs_binary)
        go_extracted = run_go_trafilatura(html_file, go_binary)

        # Evaluate both
        rs_eval = evaluate_extraction(rs_extracted, gt_data['ground_truth'])
        go_eval = evaluate_extraction(go_extracted, gt_data['ground_truth'])

        if rs_eval['has_error']:
            rs_errors += 1
        if go_eval['has_error']:
            go_errors += 1

        # Store results
        rs_results.append({
            'file_id': file_id,
            'url': gt_data['url'],
            'evaluation': rs_eval
        })

        go_results.append({
            'file_id': file_id,
            'url': gt_data['url'],
            'evaluation': go_eval
        })

    # Calculate aggregate metrics
    total_files = len(rs_results)

    def calc_aggregates(results):
        return {
            'content_f1': sum(r['evaluation']['content_f1'] for r in results) / total_files,
            'content_precision': sum(r['evaluation']['content_precision'] for r in results) / total_files,
            'content_recall': sum(r['evaluation']['content_recall'] for r in results) / total_files,
            'with_snippets_pct': sum(r['evaluation']['with_snippets_percentage'] for r in results) / total_files,
            'without_snippets_pct': sum(r['evaluation']['without_snippets_percentage'] for r in results) / total_files,
            'title_match_rate': sum(1 for r in results if r['evaluation']['title_match']) / total_files,
        }

    rs_metrics = calc_aggregates(rs_results)
    go_metrics = calc_aggregates(go_results)

    # Head-to-head comparison
    rs_wins = 0
    go_wins = 0
    ties = 0

    detailed_comparison = []
    for rs_r, go_r in zip(rs_results, go_results):
        rs_f1 = rs_r['evaluation']['content_f1']
        go_f1 = go_r['evaluation']['content_f1']

        if abs(rs_f1 - go_f1) < 0.001:  # Tie threshold
            winner = 'tie'
            ties += 1
        elif rs_f1 > go_f1:
            winner = 'rs'
            rs_wins += 1
        else:
            winner = 'go'
            go_wins += 1

        detailed_comparison.append({
            'file_id': rs_r['file_id'],
            'url': rs_r['url'],
            'rs_f1': rs_f1,
            'go_f1': go_f1,
            'delta': rs_f1 - go_f1,
            'winner': winner
        })

    # Create output summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_files': total_files,
        'rs_trafilatura': {
            **rs_metrics,
            'errors': rs_errors,
            'binary': str(rs_binary)
        },
        'go_trafilatura': {
            **go_metrics,
            'errors': go_errors,
            'binary': str(go_binary)
        },
        'comparison': {
            'rs_vs_go_f1_delta': rs_metrics['content_f1'] - go_metrics['content_f1'],
            'rs_wins': rs_wins,
            'go_wins': go_wins,
            'ties': ties,
            'rs_win_rate': rs_wins / total_files,
            'go_win_rate': go_wins / total_files,
        },
        'detailed_results': detailed_comparison
    }

    # Save results
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*80}")
    print(f"Benchmark Complete!")
    print(f"{'='*80}\n")
    print(f"Files processed: {total_files}\n")

    print(f"rs-trafilatura:")
    print(f"  F1:        {rs_metrics['content_f1']:.3f}")
    print(f"  Precision: {rs_metrics['content_precision']:.3f}")
    print(f"  Recall:    {rs_metrics['content_recall']:.3f}")
    print(f"  Errors:    {rs_errors}\n")

    print(f"go-trafilatura:")
    print(f"  F1:        {go_metrics['content_f1']:.3f}")
    print(f"  Precision: {go_metrics['content_precision']:.3f}")
    print(f"  Recall:    {go_metrics['content_recall']:.3f}")
    print(f"  Errors:    {go_errors}\n")

    print(f"Head-to-Head:")
    print(f"  RS wins:   {rs_wins} ({rs_wins/total_files:.1%})")
    print(f"  GO wins:   {go_wins} ({go_wins/total_files:.1%})")
    print(f"  Ties:      {ties} ({ties/total_files:.1%})")
    print(f"  F1 Delta:  {summary['comparison']['rs_vs_go_f1_delta']:+.3f}\n")

    print(f"Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark rs-trafilatura vs go-trafilatura")
    parser.add_argument(
        '--rs-binary',
        type=Path,
        required=True,
        help="Path to rs-trafilatura benchmark_extract binary"
    )
    parser.add_argument(
        '--go-binary',
        type=Path,
        required=True,
        help="Path to go-trafilatura binary"
    )
    parser.add_argument(
        '--ground-truth-dir',
        type=Path,
        required=True,
        help="Directory containing ground truth JSON files"
    )
    parser.add_argument(
        '--html-dir',
        type=Path,
        required=True,
        help="Directory containing HTML files"
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('results/rust_vs_go_comparison.json'),
        help="Output file for results (default: results/rust_vs_go_comparison.json)"
    )

    args = parser.parse_args()

    # Validate paths
    if not args.rs_binary.exists():
        print(f"Error: RS binary not found: {args.rs_binary}")
        return 1

    if not args.go_binary.exists():
        print(f"Error: GO binary not found: {args.go_binary}")
        return 1

    if not args.ground_truth_dir.exists():
        print(f"Error: Ground truth directory not found: {args.ground_truth_dir}")
        return 1

    if not args.html_dir.exists():
        print(f"Error: HTML directory not found: {args.html_dir}")
        return 1

    run_benchmark(
        rs_binary=args.rs_binary,
        go_binary=args.go_binary,
        ground_truth_dir=args.ground_truth_dir,
        html_dir=args.html_dir,
        output_file=args.output
    )

    return 0


if __name__ == '__main__':
    exit(main())
