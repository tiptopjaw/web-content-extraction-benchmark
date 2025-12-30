"""
Analyze and compare benchmark results across extractors
"""
import json
from pathlib import Path
from typing import Dict, List
import pandas as pd
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"

def load_results() -> Dict[str, Dict]:
    """Load all benchmark results"""
    results = {}

    for result_file in RESULTS_DIR.glob("*_results.json"):
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            results[data['extractor_key']] = data

    return results

def create_comparison_table(results: Dict[str, Dict]) -> pd.DataFrame:
    """Create comparison table of all extractors"""
    rows = []

    for ext_key, data in results.items():
        metrics = data['metrics']
        row = {
            'Extractor': data['extractor'],
            'Precision': metrics['content_precision'],
            'Recall': metrics['content_recall'],
            'F1 Score': metrics['content_f1'],
            'With Snippets': metrics['with_snippets_percentage'],
            'Without Snippets': metrics['without_snippets_percentage'],
            'Title Match': metrics['title_match_rate'],
            'Errors': data['errors'],
            'Files': data['total_files']
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sort_values('F1 Score', ascending=False)
    return df

def analyze_best_worst_cases(results: Dict[str, Dict], top_n: int = 10):
    """Identify best and worst performing files for each extractor"""
    analysis = {}

    for ext_key, data in results.items():
        # Sort by F1 score
        sorted_results = sorted(
            data['results'],
            key=lambda x: x['evaluation']['content_f1'],
            reverse=True
        )

        best = sorted_results[:top_n]
        worst = sorted_results[-top_n:]

        analysis[ext_key] = {
            'extractor': data['extractor'],
            'best': [
                {
                    'file_id': r['file_id'],
                    'url': r['url'],
                    'f1': r['evaluation']['content_f1'],
                    'precision': r['evaluation']['content_precision'],
                    'recall': r['evaluation']['content_recall']
                }
                for r in best
            ],
            'worst': [
                {
                    'file_id': r['file_id'],
                    'url': r['url'],
                    'f1': r['evaluation']['content_f1'],
                    'precision': r['evaluation']['content_precision'],
                    'recall': r['evaluation']['content_recall']
                }
                for r in worst
            ]
        }

    return analysis

def analyze_length_distribution(results: Dict[str, Dict]):
    """Analyze performance across different content lengths"""
    length_bins = {
        'Very Short (0-1000 chars)': (0, 1000),
        'Short (1000-3000 chars)': (1000, 3000),
        'Medium (3000-10000 chars)': (3000, 10000),
        'Long (10000+ chars)': (10000, float('inf'))
    }

    analysis = defaultdict(lambda: defaultdict(list))

    for ext_key, data in results.items():
        for result in data['results']:
            gt_length = result['evaluation']['ground_truth_length']

            # Find bin
            for bin_name, (min_len, max_len) in length_bins.items():
                if min_len <= gt_length < max_len:
                    analysis[ext_key][bin_name].append(result['evaluation']['content_f1'])
                    break

    # Calculate averages
    summary = {}
    for ext_key in analysis:
        summary[ext_key] = {
            bin_name: {
                'count': len(scores),
                'avg_f1': sum(scores) / len(scores) if scores else 0
            }
            for bin_name, scores in analysis[ext_key].items()
        }

    return summary

def main():
    """Generate comprehensive analysis report"""
    print(f"\n{'='*80}")
    print(f"Content Extraction Benchmark - Analysis")
    print(f"{'='*80}\n")

    # Load results
    results = load_results()

    if not results:
        print("No results found. Please run benchmark first.")
        print("Usage: python scripts/03_run_benchmark.py")
        return

    print(f"Loaded results for {len(results)} extractor(s)\n")

    # Overall comparison
    print(f"{'='*80}")
    print(f"Overall Performance Comparison")
    print(f"{'='*80}\n")

    comparison = create_comparison_table(results)
    print(comparison.to_string(index=False, float_format=lambda x: f'{x:.3f}'))

    # Save comparison
    comparison.to_csv(RESULTS_DIR / 'comparison.csv', index=False)
    print(f"\nComparison table saved to: {RESULTS_DIR / 'comparison.csv'}")

    # Best/worst cases
    print(f"\n{'='*80}")
    print(f"Best and Worst Performing Files (Top 5)")
    print(f"{'='*80}\n")

    best_worst = analyze_best_worst_cases(results, top_n=5)

    for ext_key, data in best_worst.items():
        print(f"\n{data['extractor']}:")
        print(f"  Best performing:")
        for i, case in enumerate(data['best'][:5], 1):
            print(f"    {i}. {case['file_id']} | F1: {case['f1']:.3f} | {case['url'][:60]}")

        print(f"  Worst performing:")
        for i, case in enumerate(data['worst'][:5], 1):
            print(f"    {i}. {case['file_id']} | F1: {case['f1']:.3f} | {case['url'][:60]}")

    # Save detailed analysis
    with open(RESULTS_DIR / 'best_worst_analysis.json', 'w') as f:
        json.dump(best_worst, f, indent=2)

    # Length distribution analysis
    print(f"\n{'='*80}")
    print(f"Performance by Content Length")
    print(f"{'='*80}\n")

    length_analysis = analyze_length_distribution(results)

    for ext_key, bins in length_analysis.items():
        extractor_name = results[ext_key]['extractor']
        print(f"\n{extractor_name}:")
        for bin_name, stats in bins.items():
            if stats['count'] > 0:
                print(f"  {bin_name:30} | Count: {stats['count']:4} | Avg F1: {stats['avg_f1']:.3f}")

    # Save length analysis
    with open(RESULTS_DIR / 'length_analysis.json', 'w') as f:
        json.dump(length_analysis, f, indent=2)

    # Summary recommendations
    print(f"\n{'='*80}")
    print(f"Recommendations")
    print(f"{'='*80}\n")

    # Find best overall
    best_f1_ext = max(results.items(), key=lambda x: x[1]['metrics']['content_f1'])
    best_precision_ext = max(results.items(), key=lambda x: x[1]['metrics']['content_precision'])
    best_recall_ext = max(results.items(), key=lambda x: x[1]['metrics']['content_recall'])

    print(f"Best Overall (F1):     {best_f1_ext[1]['extractor']} (F1: {best_f1_ext[1]['metrics']['content_f1']:.3f})")
    print(f"Best Precision:        {best_precision_ext[1]['extractor']} ({best_precision_ext[1]['metrics']['content_precision']:.3f})")
    print(f"Best Recall:           {best_recall_ext[1]['extractor']} ({best_recall_ext[1]['metrics']['content_recall']:.3f})")

    print(f"\n{'='*80}")
    print(f"Analysis Complete!")
    print(f"{'='*80}\n")
    print(f"All analysis files saved to: {RESULTS_DIR}")

if __name__ == "__main__":
    main()
