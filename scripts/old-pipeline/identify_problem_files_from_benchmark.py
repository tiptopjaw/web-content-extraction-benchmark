"""
Identify problematic files based on benchmark results
Files where ALL extractors fail are likely problematic
"""
import json
from pathlib import Path
from collections import defaultdict
import statistics

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR = BASE_DIR / "data"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth_filtered"

# Thresholds for identifying problematic files
MIN_F1_THRESHOLD = 0.3  # If all extractors get < 0.3 F1, file is likely problematic
MIN_WITH_SNIPPETS = 0.3  # If all extractors find < 30% of "with" snippets

def load_all_results():
    """Load results from all extractors"""
    all_results = {}

    for result_file in RESULTS_DIR.glob("*_results.json"):
        with open(result_file) as f:
            data = json.load(f)
            all_results[data['extractor_key']] = data

    return all_results

def analyze_per_file_performance(all_results):
    """Analyze how each file performs across all extractors"""

    # Aggregate results by file_id
    file_performance = defaultdict(lambda: {
        'f1_scores': [],
        'with_snippets': [],
        'url': None,
        'extractors': []
    })

    for ext_key, data in all_results.items():
        for result in data['results']:
            file_id = result['file_id']
            eval_data = result['evaluation']

            file_performance[file_id]['f1_scores'].append(eval_data['content_f1'])
            file_performance[file_id]['with_snippets'].append(eval_data['with_snippets_percentage'])
            file_performance[file_id]['url'] = result['url']
            file_performance[file_id]['extractors'].append(ext_key)

    return file_performance

def identify_problematic_files(file_performance):
    """Identify files where all extractors perform poorly"""

    problematic = []

    for file_id, perf in file_performance.items():
        # Calculate stats
        max_f1 = max(perf['f1_scores']) if perf['f1_scores'] else 0
        avg_f1 = statistics.mean(perf['f1_scores']) if perf['f1_scores'] else 0
        max_with = max(perf['with_snippets']) if perf['with_snippets'] else 0

        # Identify issues
        issues = []

        # All extractors get very low F1
        if max_f1 < MIN_F1_THRESHOLD:
            issues.append(f"Low F1 (max: {max_f1:.3f})")

        # All extractors find few "with" snippets
        if max_with < MIN_WITH_SNIPPETS:
            issues.append(f"Low snippet coverage (max: {max_with:.1%})")

        # Check if extracted content is consistently empty
        if avg_f1 < 0.1:
            issues.append(f"Very low avg F1 ({avg_f1:.3f})")

        if issues:
            problematic.append({
                'file_id': file_id,
                'url': perf['url'],
                'max_f1': max_f1,
                'avg_f1': avg_f1,
                'max_with_snippets': max_with,
                'issues': issues,
                'num_extractors': len(perf['f1_scores'])
            })

    # Sort by avg F1 (worst first)
    problematic.sort(key=lambda x: x['avg_f1'])

    return problematic

def main():
    """Main analysis"""

    print(f"\n{'='*80}")
    print("Identifying Problematic Files from Benchmark Results")
    print(f"{'='*80}\n")

    # Load results
    all_results = load_all_results()

    if not all_results:
        print("Error: No benchmark results found.")
        print("Run benchmark first: python scripts/03_run_benchmark.py")
        return

    print(f"Loaded results from {len(all_results)} extractors")

    # Analyze per-file performance
    file_performance = analyze_per_file_performance(all_results)
    print(f"Analyzed {len(file_performance)} files\n")

    # Identify problematic files
    problematic = identify_problematic_files(file_performance)

    print(f"{'='*80}")
    print(f"Problematic Files Found: {len(problematic)}")
    print(f"{'='*80}\n")

    if not problematic:
        print("✓ No problematic files found!")
        print("  All files have at least one extractor with decent performance.")
        return

    print(f"Criteria:")
    print(f"  - Max F1 score < {MIN_F1_THRESHOLD}")
    print(f"  - Max 'with' snippets found < {MIN_WITH_SNIPPETS:.0%}")
    print(f"  - Avg F1 score < 0.1\n")

    print(f"Problematic files (showing all {len(problematic)}):")
    print(f"{'-'*80}")

    for i, item in enumerate(problematic, 1):
        print(f"\n{i}. File: {item['file_id']}")
        print(f"   URL: {item['url']}")
        print(f"   Best F1: {item['max_f1']:.3f} | Avg F1: {item['avg_f1']:.3f}")
        print(f"   Best snippet coverage: {item['max_with_snippets']:.1%}")
        print(f"   Issues: {', '.join(item['issues'])}")

    # Save to file
    output_file = RESULTS_DIR / "problematic_files.json"
    with open(output_file, 'w') as f:
        json.dump(problematic, f, indent=2)

    print(f"\n{'='*80}")
    print("Summary")
    print(f"{'='*80}\n")
    print(f"Total files analyzed: {len(file_performance)}")
    print(f"Problematic files: {len(problematic)} ({len(problematic)/len(file_performance)*100:.1f}%)")
    print(f"\nFull report saved to: {output_file}")

    # Recommendations
    print(f"\n{'='*80}")
    print("Recommendations")
    print(f"{'='*80}\n")

    if len(problematic) > 50:
        print(f"⚠ {len(problematic)} problematic files is significant.")
        print(f"  Consider:")
        print(f"  1. Review the URLs manually to understand patterns")
        print(f"  2. Remove these files from the dataset")
        print(f"  3. Re-run benchmark on cleaned dataset")
    elif len(problematic) > 0:
        print(f"✓ Only {len(problematic)} problematic files ({len(problematic)/len(file_performance)*100:.1f}%)")
        print(f"  You can:")
        print(f"  1. Keep them as challenging test cases")
        print(f"  2. Remove them for cleaner benchmark results")
        print(f"  3. Document them as known difficult cases")

    print(f"\nTo remove these files:")
    print(f"  python3 << 'EOF'")
    print(f"from pathlib import Path")
    print(f"import shutil")
    print(f"import json")
    print(f"")
    print(f"with open('results/problematic_files.json') as f:")
    print(f"    problematic = json.load(f)")
    print(f"")
    print(f"filtered_dir = Path('data/ground_truth_filtered')")
    print(f"removed_dir = Path('data/ground_truth_removed')")
    print(f"")
    print(f"for item in problematic:")
    print(f"    file_id = item['file_id']")
    print(f"    src = filtered_dir / f'{{file_id}}.json'")
    print(f"    dst = removed_dir / f'{{file_id}}.json'")
    print(f"    if src.exists():")
    print(f"        shutil.move(src, dst)")
    print(f"        print(f'Moved {{file_id}}')")
    print(f"EOF")

if __name__ == "__main__":
    main()
