"""
Create ground truth annotations using Deepseek API
Reads HTML files and generates structured JSON annotations
"""
import asyncio
import json
import csv
from pathlib import Path
from datetime import datetime
import argparse
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm
from bs4 import BeautifulSoup

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
METADATA_FILE = DATA_DIR / "metadata.csv"
ANNOTATION_PROGRESS_FILE = DATA_DIR / "annotation_progress.json"

# Deepseek API Configuration
DEEPSEEK_API_BASE = "https://api.deepseek.com"
MODEL = "deepseek-chat"  # or deepseek-coder
CONCURRENT_REQUESTS = 5  # Parallel API calls


ANNOTATION_PROMPT = """You are an expert at analyzing web pages and extracting main content.

Given the HTML of a web page, analyze it and provide a structured annotation with:

1. **Title**: The main article/page title
2. **Author**: Author name (if available, otherwise null)
3. **Publish Date**: Publication date in YYYY-MM-DD format (if available, otherwise null)
4. **Main Content**: The complete main content text (article body, product description, etc.) - this should be the primary information the user came to read, excluding navigation, ads, sidebars, footers
5. **With**: 3-5 key sentences or paragraphs that MUST be included in any content extraction (these should be core content)
6. **Without**: 3-5 text snippets that should NOT be extracted (navigation, ads, cookie banners, related links, etc.)

Respond ONLY with valid JSON in this exact format:
{
  "title": "extracted title",
  "author": "author name or null",
  "publish_date": "YYYY-MM-DD or null",
  "main_content": "full main content text here...",
  "with": [
    "Key sentence 1 that must be extracted",
    "Key sentence 2 that must be extracted",
    "Key paragraph 3"
  ],
  "without": [
    "Advertisement text",
    "Cookie consent banner",
    "Navigation menu item",
    "Footer copyright notice"
  ]
}

Important:
- Be thorough in extracting main_content
- For "with" snippets: choose sentences that clearly identify main content
- For "without" snippets: choose text from boilerplate/navigation/ads
- Ensure all JSON is properly escaped
- Do not include any text before or after the JSON

HTML to analyze:
"""


def load_metadata():
    """Load metadata CSV"""
    metadata = {}
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'] == 'success':
                file_id = int(row['file_id'])
                metadata[file_id] = row
    return metadata


def load_progress():
    """Load annotation progress"""
    if ANNOTATION_PROGRESS_FILE.exists():
        with open(ANNOTATION_PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed": [], "failed": []}


def save_progress(progress):
    """Save annotation progress"""
    with open(ANNOTATION_PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def clean_html_for_api(html_content, max_chars=100000):
    """Clean and truncate HTML for API submission"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for tag in soup(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()

    # Get text or prettified HTML (you can choose)
    # Option 1: Send cleaned HTML
    cleaned = str(soup)

    # Truncate if too long (Deepseek has context limits)
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n\n[... HTML truncated due to length ...]"

    return cleaned


async def annotate_html(client, file_id, html_content, url, semaphore):
    """Generate annotation for single HTML file using Deepseek API"""
    async with semaphore:

        output_file = GROUND_TRUTH_DIR / f"{file_id:04d}.json"

        # Skip if already annotated
        if output_file.exists():
            return {
                "file_id": file_id,
                "status": "skipped",
                "output_file": str(output_file)
            }

        try:
            # Clean HTML
            cleaned_html = clean_html_for_api(html_content)

            # Call Deepseek API
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert web content analyzer. You extract structured information from HTML pages."
                    },
                    {
                        "role": "user",
                        "content": ANNOTATION_PROMPT + "\n\n" + cleaned_html
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=4000
            )

            # Parse response
            result_text = response.choices[0].message.content.strip()

            # Try to extract JSON from response
            # Sometimes API might add markdown code blocks
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0].strip()

            ground_truth = json.loads(result_text)

            # Create full annotation
            annotation = {
                "url": url,
                "file_id": f"{file_id:04d}",
                "downloaded_at": datetime.now().isoformat(),
                "ground_truth": ground_truth,
                "model": MODEL,
                "annotated_at": datetime.now().isoformat()
            }

            # Save annotation
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(annotation, f, indent=2, ensure_ascii=False)

            return {
                "file_id": file_id,
                "status": "success",
                "output_file": str(output_file),
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }

        except json.JSONDecodeError as e:
            return {
                "file_id": file_id,
                "status": "failed",
                "error": f"JSON parse error: {str(e)}",
                "response": result_text[:200] if 'result_text' in locals() else None
            }
        except Exception as e:
            return {
                "file_id": file_id,
                "status": "failed",
                "error": str(e)[:200]
            }


async def annotate_all(api_key, start_id=None, end_id=None):
    """Annotate all HTML files"""

    print(f"\n{'='*80}")
    print(f"Modern Content Benchmark - Deepseek Annotation")
    print(f"{'='*80}\n")

    # Create output directory
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    # Load metadata
    metadata = load_metadata()
    print(f"Loaded metadata for {len(metadata)} successful downloads")

    # Filter by range if specified
    file_ids = sorted(metadata.keys())
    if start_id:
        file_ids = [fid for fid in file_ids if fid >= start_id]
    if end_id:
        file_ids = [fid for fid in file_ids if fid <= end_id]

    print(f"Processing {len(file_ids)} files (IDs: {file_ids[0]} to {file_ids[-1]})")
    print(f"API: {DEEPSEEK_API_BASE}")
    print(f"Model: {MODEL}")
    print(f"Concurrent requests: {CONCURRENT_REQUESTS}\n")

    # Initialize Deepseek client (OpenAI-compatible)
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_API_BASE
    )

    # Prepare annotation tasks
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    tasks = []

    for file_id in file_ids:
        html_file = HTML_DIR / f"{file_id:04d}.html"
        if not html_file.exists():
            continue

        # Read HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        url = metadata[file_id]['url']
        tasks.append(annotate_html(client, file_id, html_content, url, semaphore))

    # Run annotations with progress bar
    if tasks:
        print(f"Starting annotation of {len(tasks)} HTML files...\n")
        results = []
        total_tokens = 0

        for coro in tqdm.as_completed(tasks, total=len(tasks), desc="Annotating"):
            result = await coro
            results.append(result)

            if result.get('tokens_used'):
                total_tokens += result['tokens_used']

            # Progress update
            if len(results) % 25 == 0:
                successful = [r for r in results if r["status"] == "success"]
                failed = [r for r in results if r["status"] == "failed"]
                print(f"\n  Progress: {len(results)}/{len(tasks)} | Success: {len(successful)} | Failed: {len(failed)} | Tokens: {total_tokens:,}")

        return results, total_tokens

    return [], 0


def generate_report(results, total_tokens):
    """Generate annotation summary report"""

    total = len(results)
    successful = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] == "failed"]

    print(f"\n{'='*80}")
    print(f"Annotation Complete!")
    print(f"{'='*80}\n")
    print(f"✓ Total files: {total}")
    print(f"✓ Successfully annotated: {len(successful)}")
    print(f"✓ Skipped (already done): {len(skipped)}")
    print(f"✓ Failed: {len(failed)}")
    print(f"✓ Success rate: {len(successful)/total*100:.1f}%")
    print(f"\n✓ Total tokens used: {total_tokens:,}")
    print(f"✓ Average tokens per file: {total_tokens/len(successful):.0f}" if successful else "")

    if failed:
        print(f"\n⚠ Failed annotations:")
        for f in failed[:10]:
            print(f"  - File {f['file_id']:04d}: {f.get('error', 'Unknown error')[:60]}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")


async def main():
    """Main annotation function"""
    global MODEL

    parser = argparse.ArgumentParser(description="Create ground truth annotations using Deepseek API")
    parser.add_argument("--api-key", required=True, help="Deepseek API key")
    parser.add_argument("--start", type=int, help="Start file ID (optional)")
    parser.add_argument("--end", type=int, help="End file ID (optional)")
    parser.add_argument("--model", default=MODEL, help=f"Model to use (default: {MODEL})")

    args = parser.parse_args()

    # Update model if specified
    MODEL = args.model

    # Run annotations
    results, total_tokens = await annotate_all(args.api_key, args.start, args.end)

    # Generate report
    generate_report(results, total_tokens)

    print(f"\n✅ All done! Annotations saved to: {GROUND_TRUTH_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
