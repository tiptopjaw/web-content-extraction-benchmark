"""
Re-annotate files with incomplete ground truth using DeepSeek API

This script processes files identified as having incomplete annotations
(only intro paragraphs captured instead of full article content).
"""
import asyncio
import json
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import os
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
BACKUP_DIR = DATA_DIR / "ground_truth_backup"
REANNOTATION_QUEUE = DATA_DIR / "reannotation_queue.json"

# DeepSeek API Configuration
DEEPSEEK_API_BASE = "https://api.deepseek.com"
MODEL = "deepseek-chat"
CONCURRENT_REQUESTS = 20  # Increased for faster processing

# Improved prompt that emphasizes COMPLETE content extraction
ANNOTATION_PROMPT = """You are an expert at analyzing web pages and extracting main content.

Given the HTML of a web page, analyze it and provide a structured annotation.

CRITICAL: Extract the COMPLETE main content, not just the introduction or summary.
- For listicle articles ("Top 10...", "Best X..."), include ALL items in the list
- For tutorials, include ALL steps
- For reviews, include the FULL review text
- For news articles, include the ENTIRE article body

Provide a structured annotation with:

1. **Title**: The main article/page title
2. **Author**: Author name (if available, otherwise null)
3. **Publish Date**: Publication date in YYYY-MM-DD format (if available, otherwise null)
4. **Main Content**: The COMPLETE main content text - this means:
   - For listicle articles: Include the intro AND every single item/entry with its description
   - For how-to guides: Include ALL steps, not just the overview
   - For product reviews: Include the FULL review, all sections
   - For news: Include the ENTIRE article from start to finish
   - DO NOT summarize or truncate - extract the FULL text
5. **With**: 3-5 key sentences that MUST be included (choose from DIFFERENT sections of the article)
6. **Without**: 3-5 text snippets that should NOT be extracted (navigation, ads, sidebars, footers)

Respond ONLY with valid JSON in this exact format:
{
  "title": "extracted title",
  "author": "author name or null",
  "publish_date": "YYYY-MM-DD or null",
  "main_content": "THE COMPLETE FULL ARTICLE TEXT HERE - DO NOT TRUNCATE OR SUMMARIZE",
  "with": [
    "Key sentence from beginning of article",
    "Key sentence from middle of article",
    "Key sentence from end of article"
  ],
  "without": [
    "Navigation or menu text",
    "Advertisement text",
    "Footer or sidebar content"
  ]
}

IMPORTANT REMINDERS:
- Extract the ENTIRE article content, not a summary
- For listicles with 10, 20, 50, or 100 items - include ALL of them
- The main_content should be LONG for long articles
- If the article has multiple sections, include ALL sections
- Do not include any text before or after the JSON

HTML to analyze:
"""


def load_reannotation_queue():
    """Load the queue of files needing re-annotation"""
    if not REANNOTATION_QUEUE.exists():
        print(f"Error: Re-annotation queue not found at {REANNOTATION_QUEUE}")
        return []

    with open(REANNOTATION_QUEUE, 'r') as f:
        data = json.load(f)

    return data.get('queue', [])


def clean_html_for_api(html_content, max_chars=120000):
    """Clean and truncate HTML for API submission"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
        tag.decompose()

    cleaned = str(soup)

    # Truncate if too long
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n\n[... HTML truncated due to length ...]"

    return cleaned


def backup_annotation(file_id):
    """Backup existing annotation before overwriting"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    original = GROUND_TRUTH_DIR / f"{file_id}.json"
    if original.exists():
        backup = BACKUP_DIR / f"{file_id}.json"
        shutil.copy2(original, backup)
        return True
    return False


async def reannotate_html(client, file_id, html_content, url, semaphore):
    """Re-annotate a single HTML file"""
    async with semaphore:
        output_file = GROUND_TRUTH_DIR / f"{file_id}.json"

        # Skip if already re-annotated
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                if existing.get('reannotated'):
                    return {
                        "file_id": file_id,
                        "status": "skipped",
                        "reason": "already_reannotated"
                    }

        try:
            # Backup existing annotation
            backup_annotation(file_id)

            # Clean HTML
            cleaned_html = clean_html_for_api(html_content)

            # Call DeepSeek API
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert web content analyzer. You extract the COMPLETE content from HTML pages - never summarize or truncate. For listicle articles, you include EVERY item."
                    },
                    {
                        "role": "user",
                        "content": ANNOTATION_PROMPT + "\n\n" + cleaned_html
                    }
                ],
                temperature=0.2,  # Lower for consistency
                max_tokens=8000  # DeepSeek limit
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
                "file_id": file_id,
                "downloaded_at": datetime.now().isoformat(),
                "ground_truth": ground_truth,
                "model": MODEL,
                "annotated_at": datetime.now().isoformat(),
                "reannotated": True,
                "reannotation_reason": "incomplete_annotation"
            }

            # Save annotation
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(annotation, f, indent=2, ensure_ascii=False)

            # Calculate content length for reporting
            content_len = len(ground_truth.get('main_content', ''))

            return {
                "file_id": file_id,
                "status": "success",
                "output_file": str(output_file),
                "content_length": content_len,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }

        except json.JSONDecodeError as e:
            return {
                "file_id": file_id,
                "status": "failed",
                "error": f"JSON parse error: {str(e)}",
                "response": result_text[:500] if 'result_text' in locals() else None
            }
        except Exception as e:
            return {
                "file_id": file_id,
                "status": "failed",
                "error": str(e)[:200]
            }


async def reannotate_queue(api_key, priority=None, limit=None, dry_run=False):
    """Re-annotate files from the queue"""

    print(f"\n{'='*80}")
    print(f"Re-annotation of Incomplete Ground Truth")
    print(f"{'='*80}\n")

    # Load queue
    queue = load_reannotation_queue()
    if not queue:
        print("No files in re-annotation queue")
        return [], 0

    # Filter by priority if specified
    if priority:
        queue = [q for q in queue if q.get('priority_label') == priority]

    # Apply limit
    if limit:
        queue = queue[:limit]

    print(f"Files to process: {len(queue)}")
    print(f"API: {DEEPSEEK_API_BASE}")
    print(f"Model: {MODEL}")
    print(f"Concurrent requests: {CONCURRENT_REQUESTS}")

    if dry_run:
        print(f"\n[DRY RUN] Would re-annotate these files:")
        for item in queue[:10]:
            print(f"  {item['file_id']}: {item['url'][:60]}...")
        if len(queue) > 10:
            print(f"  ... and {len(queue) - 10} more")
        return [], 0

    # Initialize client
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_API_BASE
    )

    # Prepare tasks
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    tasks = []

    for item in queue:
        file_id = item['file_id']
        html_file = HTML_DIR / f"{file_id}.html"

        if not html_file.exists():
            print(f"Warning: HTML file {file_id}.html not found")
            continue

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        tasks.append(reannotate_html(client, file_id, html_content, item['url'], semaphore))

    # Run with progress bar
    if tasks:
        print(f"\nStarting re-annotation of {len(tasks)} files...\n")
        results = []
        total_tokens = 0

        for coro in tqdm.as_completed(tasks, total=len(tasks), desc="Re-annotating"):
            result = await coro
            results.append(result)

            if result.get('tokens_used'):
                total_tokens += result['tokens_used']

            # Progress update every 25 files
            if len(results) % 25 == 0:
                successful = [r for r in results if r["status"] == "success"]
                failed = [r for r in results if r["status"] == "failed"]
                avg_len = sum(r.get('content_length', 0) for r in successful) / len(successful) if successful else 0
                print(f"\n  Progress: {len(results)}/{len(tasks)} | Success: {len(successful)} | Failed: {len(failed)} | Avg content: {avg_len:,.0f} chars")

        return results, total_tokens

    return [], 0


def generate_report(results, total_tokens):
    """Generate re-annotation summary"""

    total = len(results)
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]

    print(f"\n{'='*80}")
    print(f"Re-annotation Complete!")
    print(f"{'='*80}\n")
    print(f"✓ Total files processed: {total}")
    print(f"✓ Successfully re-annotated: {len(successful)}")
    print(f"✓ Failed: {len(failed)}")

    if successful:
        avg_content = sum(r.get('content_length', 0) for r in successful) / len(successful)
        print(f"✓ Average content length: {avg_content:,.0f} characters")

    print(f"✓ Total tokens used: {total_tokens:,}")

    if failed:
        print(f"\n⚠ Failed re-annotations:")
        for f in failed[:10]:
            print(f"  - File {f['file_id']}: {f.get('error', 'Unknown error')[:60]}")

    print(f"\n✓ Original annotations backed up to: {BACKUP_DIR}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Re-annotate files with incomplete ground truth")
    parser.add_argument("--api-key", help="DeepSeek API key (or set DEEPSEEK_API_KEY env var)")
    parser.add_argument("--priority", choices=['critical', 'high', 'medium'],
                        help="Only process files of this priority")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get('DEEPSEEK_API_KEY')
    if not api_key and not args.dry_run:
        print("Error: API key required. Use --api-key or set DEEPSEEK_API_KEY environment variable")
        return

    # Run re-annotation
    results, total_tokens = await reannotate_queue(
        api_key,
        priority=args.priority,
        limit=args.limit,
        dry_run=args.dry_run
    )

    if results:
        generate_report(results, total_tokens)

        # Save results log
        log_file = DATA_DIR / f"reannotation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(results),
                'successful': len([r for r in results if r['status'] == 'success']),
                'failed': len([r for r in results if r['status'] == 'failed']),
                'total_tokens': total_tokens,
                'results': results
            }, f, indent=2)
        print(f"✓ Log saved to: {log_file}")


if __name__ == "__main__":
    asyncio.run(main())
