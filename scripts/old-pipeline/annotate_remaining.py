"""
Annotate the remaining 404 unannotated files
"""
import asyncio
import csv
import json
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
REMAINING_SUBSET = DATA_DIR / "metadata_remaining_final.csv"

# Deepseek API Configuration
DEEPSEEK_API_BASE = "https://api.deepseek.com"
MODEL = "deepseek-chat"
CONCURRENT_REQUESTS = 5

ANNOTATION_PROMPT = """You are an expert at analyzing web pages and extracting main content.

Given the HTML of a web page (preprocessed to remove script/style tags), analyze it and provide a structured annotation with:

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

def preprocess_html(html_content):
    """
    Preprocess HTML by removing script/style tags.

    This is CORRECT because:
    - All content extractors (Trafilatura, Readability, etc.) remove these tags first
    - Scripts/styles contain zero article content
    - Ground truth and extraction must use same preprocessing
    - This is standard practice, not "cleaning"
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script, style, and other non-content tags
    for tag in soup(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()

    return str(soup)

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
            # Preprocess HTML (remove script/style tags)
            # This matches what extractors do as their first step
            preprocessed_html = preprocess_html(html_content)

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
                        "content": ANNOTATION_PROMPT + "\n\n" + preprocessed_html
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )

            # Parse response
            result_text = response.choices[0].message.content.strip()

            # Extract JSON from response
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

async def annotate_remaining(api_key):
    """Annotate all remaining files"""

    # Check if subset exists
    if not REMAINING_SUBSET.exists():
        print(f"Error: {REMAINING_SUBSET} not found")
        print("Run: python scripts/create_remaining_subset.py")
        return

    # Load remaining subset
    with open(REMAINING_SUBSET, 'r') as f:
        reader = csv.DictReader(f)
        all_files = list(reader)

    print(f"\n{'='*80}")
    print(f"Annotating Remaining Files")
    print(f"{'='*80}\n")
    print(f"Total files to annotate: {len(all_files)}")
    print(f"File IDs: {all_files[0]['file_id']} to {all_files[-1]['file_id']}\n")

    # Create ground truth directory
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize client
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_API_BASE
    )

    # Prepare tasks
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    tasks = []

    for file_meta in all_files:
        file_id = int(file_meta['file_id'])
        html_file = HTML_DIR / f"{file_id:04d}.html"

        if not html_file.exists():
            print(f"⚠ File {file_id:04d}.html not found, skipping")
            continue

        # Read HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        url = file_meta['url']
        tasks.append(annotate_html(client, file_id, html_content, url, semaphore))

    # Run annotations
    if tasks:
        print(f"Starting annotation of {len(tasks)} files...\n")
        results = []
        total_tokens = 0

        for coro in tqdm.as_completed(tasks, total=len(tasks), desc="Remaining files"):
            result = await coro
            results.append(result)

            if result.get('tokens_used'):
                total_tokens += result['tokens_used']

            # Progress update every 50
            if len(results) % 50 == 0:
                successful = [r for r in results if r["status"] == "success"]
                failed = [r for r in results if r["status"] == "failed"]
                print(f"\n  Progress: {len(results)}/{len(tasks)} | Success: {len(successful)} | Failed: {len(failed)} | Tokens: {total_tokens:,}")

        # Report
        successful = [r for r in results if r["status"] == "success"]
        skipped = [r for r in results if r["status"] == "skipped"]
        failed = [r for r in results if r["status"] == "failed"]

        print(f"\n{'='*80}")
        print(f"Annotation Complete!")
        print(f"{'='*80}\n")
        print(f"✓ Total files: {len(results)}")
        print(f"✓ Successfully annotated: {len(successful)}")
        print(f"✓ Skipped (already done): {len(skipped)}")
        print(f"✓ Failed: {len(failed)}")
        print(f"✓ Success rate: {len(successful)/len(results)*100:.1f}%")
        print(f"\n✓ Total tokens used: {total_tokens:,}")
        print(f"✓ Average tokens per file: {total_tokens/len(successful):.0f}" if successful else "")
        print(f"✓ Estimated cost: ${total_tokens * 0.00014 + total_tokens * 0.00028:.2f}")

        if failed:
            print(f"\n⚠ Failed annotations:")
            for f in failed[:10]:
                print(f"  - File {f['file_id']:04d}: {f.get('error', 'Unknown error')[:60]}")
            if len(failed) > 10:
                print(f"  ... and {len(failed) - 10} more")

        print(f"\n✅ Annotations saved to: {GROUND_TRUTH_DIR}")
        print(f"\nNext steps:")
        print(f"  1. Run quality filter on new annotations")
        print(f"  2. Merge with existing clean dataset")

async def main():
    """Main function"""

    parser = argparse.ArgumentParser(description="Annotate remaining unannotated files")
    parser.add_argument("--api-key", required=True, help="Deepseek API key")

    args = parser.parse_args()

    await annotate_remaining(args.api_key)

if __name__ == "__main__":
    asyncio.run(main())
