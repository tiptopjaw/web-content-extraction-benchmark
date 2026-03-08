"""
Annotation script v2 - with image extraction and page type classification

Supports both DeepSeek and MiniMax APIs.
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
SUBSET_FILE = DATA_DIR / "metadata_subset_final.csv"

# API Configurations (API keys can be overridden via --api-key argument)
API_CONFIGS = {
    'deepseek': {
        'base_url': 'https://api.deepseek.com',
        'model': 'deepseek-chat',
        'concurrent': 5,
        'api_key': None  # Set via --api-key or environment variable DEEPSEEK_API_KEY
    },
    'minimax': {
        'base_url': 'https://api.minimax.io/v1',
        'model': 'MiniMax-M2.1',
        'concurrent': 5,
        'api_key': 'sk-api-Nx6s6vLDd5o5vz56GuuDDzq9qcbea-waFq21MCbBEOB0GaH7iYMJJ4oyKsclZ4fkxDtrqzW85uzXthLnpR2E0WZXO6Tg2wAhj9PkNEgpoMa4zNQAtgiDcDs'
    }
}

ANNOTATION_PROMPT_V2 = """You are an expert at analyzing web pages. Extract structured information from the HTML.

## Task

Analyze this HTML and provide:

### 1. Page Type Classification
Classify this page into ONE primary type:
- `article`: News, blog posts, editorials, how-to guides
- `product`: E-commerce single product page
- `collection`: E-commerce category/listing page
- `service`: Service/landing page
- `documentation`: Help docs, technical docs
- `recipe`: Recipe pages
- `review`: Product/service reviews
- `forum`: Discussion threads, Q&A
- `directory`: Business listings
- `homepage`: Site homepages
- `other`: None of the above

Rate your confidence: `high` (clearly matches), `medium` (mostly matches), `low` (ambiguous)

### 2. Metadata
- Title: Main article/page title
- Author: Author name (null if not found)
- Publish Date: YYYY-MM-DD format (null if not found)

### 3. Main Content
The primary text content the user came to read. Exclude navigation, ads, sidebars, footers.

### 4. Images
You will be given a list of PRE-EXTRACTED images from the HTML. From this list, select the images that are part of the main content (max 10).

For each selected image, use the EXACT src/filename from the pre-extracted list and add:
- `caption`: Caption from figcaption or adjacent text in the HTML (null if none found)
- `is_hero`: true for the main/featured image, false otherwise

EXCLUDE from selection: icons, logos, ads, decorative backgrounds, UI elements, social media buttons

### 5. Validation Snippets
- `with`: 5 sentences that MUST appear in good extraction
- `without`: 5 items that should NOT be extracted (navigation, boilerplate, ads)

## Output Format

Respond with ONLY valid JSON:

```json
{
  "page_type": {
    "primary": "article",
    "confidence": "high",
    "needs_review": false,
    "review_reason": null,
    "tags": ["technology", "guide"]
  },
  "title": "Article Title Here",
  "author": "Author Name or null",
  "publish_date": "2025-01-15 or null",
  "main_content": "Full main content text...",
  "selected_images": [0, 2, 5],
  "image_details": {
    "0": {"caption": "Photo credit text", "is_hero": true},
    "2": {"caption": null, "is_hero": false},
    "5": {"caption": "Chart showing data", "is_hero": false}
  },
  "with": [
    "Key sentence 1",
    "Key sentence 2",
    "Key sentence 3",
    "Key sentence 4",
    "Key sentence 5"
  ],
  "without": [
    "Subscribe to newsletter",
    "Copyright 2025",
    "Privacy Policy",
    "Navigation item",
    "Cookie notice"
  ]
}
```

Important:
- `selected_images`: Array of indices from the PRE-EXTRACTED images list (use ONLY these indices!)
- `image_details`: Object mapping index to caption and is_hero status
- Set needs_review=true and provide review_reason when confidence is "low"
- Ensure exactly 5 items in both "with" and "without" arrays
- Keep your response concise - output ONLY the JSON, no lengthy explanations
"""


def extract_images_from_html(html_content: str) -> list:
    """
    Pre-extract all images from HTML before sending to LLM.
    Returns a list of image dicts with src, filename, alt, width, height.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    images = []
    seen_srcs = set()

    for img in soup.find_all('img'):
        # Get src - check lazy loading attributes first
        src = (img.get('data-src') or img.get('data-lazy-src') or
               img.get('data-original') or img.get('src') or '')

        if not src or src.startswith('data:'):
            continue

        # Skip duplicates
        if src in seen_srcs:
            continue
        seen_srcs.add(src)

        # Extract filename
        filename = src.split('/')[-1].split('?')[0] if '/' in src else src

        # Get dimensions
        width = img.get('width', '')
        height = img.get('height', '')

        # Skip tiny images (likely icons)
        try:
            w = int(width) if width else 0
            h = int(height) if height else 0
            if (w > 0 and w < 50) or (h > 0 and h < 50):
                continue
        except ValueError:
            pass

        # Get alt text
        alt = img.get('alt', '')

        images.append({
            'src': src,
            'filename': filename,
            'alt': alt if alt else None,
            'width': width if width else None,
            'height': height if height else None
        })

    return images[:50]  # Limit to 50 images for prompt


def preprocess_html(html_content: str) -> str:
    """
    Preprocess HTML by removing script/style tags.
    This matches what extractors do as their first step.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script, style, and other non-content tags
    for tag in soup(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()

    return str(soup)


def parse_llm_response(response_text: str) -> dict:
    """Parse JSON from LLM response, handling various formats"""
    text = response_text.strip()

    # Remove <think>...</think> blocks (MiniMax reasoning)
    import re
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = text.strip()

    # Remove markdown code blocks
    if text.startswith("```json"):
        text = text.split("```json", 1)[1]
        if "```" in text:
            text = text.split("```")[0]
    elif text.startswith("```"):
        text = text.split("```", 1)[1]
        if "```" in text:
            text = text.split("```")[0]

    text = text.strip()

    return json.loads(text)


def build_v2_annotation(url: str, file_id: int, parsed_response: dict,
                        pre_extracted_images: list, model: str) -> dict:
    """Build v2 annotation structure from parsed LLM response"""

    # Extract page_type (move to _internal)
    page_type = parsed_response.get('page_type', {
        'primary': 'other',
        'confidence': 'low',
        'needs_review': True,
        'review_reason': 'Page type not provided by LLM',
        'tags': []
    })

    # Build images from selected indices
    selected_indices = parsed_response.get('selected_images', [])
    image_details = parsed_response.get('image_details', {})

    image_items = []
    for idx in selected_indices[:10]:  # Max 10 images
        if idx < len(pre_extracted_images):
            img = pre_extracted_images[idx].copy()
            details = image_details.get(str(idx), {})
            img['caption'] = details.get('caption')
            img['is_hero'] = details.get('is_hero', False)
            # Remove width/height from final output
            img.pop('width', None)
            img.pop('height', None)
            image_items.append(img)

    images = {
        'total_in_content': len(pre_extracted_images),
        'annotated_count': len(image_items),
        'items': image_items
    }

    annotation = {
        'schema_version': '2.0',
        'url': url,
        'file_id': f"{file_id:04d}",
        '_internal': {
            'page_type': page_type
        },
        'ground_truth': {
            'title': parsed_response.get('title'),
            'author': parsed_response.get('author'),
            'publish_date': parsed_response.get('publish_date'),
            'main_content': parsed_response.get('main_content', ''),
            'with': parsed_response.get('with', [])[:5],
            'without': parsed_response.get('without', [])[:5],
            'images': images
        },
        'model': model,
        'annotated_at': datetime.now().isoformat()
    }

    return annotation


def format_image_list(images: list) -> str:
    """Format pre-extracted images list for the prompt"""
    if not images:
        return "No images found in HTML."

    lines = ["## PRE-EXTRACTED IMAGES (select by index):\n"]
    for i, img in enumerate(images):
        line = f"[{i}] {img['filename']}"
        if img.get('alt'):
            line += f" | alt: {img['alt'][:80]}"
        if img.get('width') and img.get('height'):
            line += f" | {img['width']}x{img['height']}"
        lines.append(line)

    return "\n".join(lines)


async def annotate_html_v2(client, file_id: int, html_content: str, url: str,
                           model: str, semaphore, force: bool = False) -> dict:
    """Generate v2 annotation for single HTML file"""
    async with semaphore:
        output_file = GROUND_TRUTH_DIR / f"{file_id:04d}.json"

        # Skip if already annotated with v2 (unless force)
        if output_file.exists() and not force:
            try:
                with open(output_file) as f:
                    existing = json.load(f)
                if existing.get('schema_version') == '2.0':
                    return {
                        'file_id': file_id,
                        'status': 'skipped',
                        'reason': 'v2 annotation exists'
                    }
            except:
                pass  # Will re-annotate if can't read

        try:
            # Pre-extract images from HTML BEFORE preprocessing
            pre_extracted_images = extract_images_from_html(html_content)

            # Preprocess HTML
            preprocessed_html = preprocess_html(html_content)

            # Truncate if too long (keep under token limit)
            max_chars = 100000
            if len(preprocessed_html) > max_chars:
                preprocessed_html = preprocessed_html[:max_chars] + "\n\n[HTML TRUNCATED]"

            # Build prompt with pre-extracted images
            image_list_str = format_image_list(pre_extracted_images)
            full_prompt = f"{ANNOTATION_PROMPT_V2}\n\n{image_list_str}\n\n## HTML to analyze:\n\n{preprocessed_html}"

            # Call API
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert web content analyzer. Extract structured information from HTML pages. Always respond with valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': full_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=8000
            )

            result_text = response.choices[0].message.content.strip()

            # Parse response
            parsed = parse_llm_response(result_text)

            # Build v2 annotation with pre-extracted images
            annotation = build_v2_annotation(url, file_id, parsed, pre_extracted_images, model)

            # Save
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(annotation, f, indent=2, ensure_ascii=False)

            return {
                'file_id': file_id,
                'status': 'success',
                'page_type': annotation['_internal']['page_type']['primary'],
                'image_count': annotation['ground_truth']['images']['annotated_count'],
                'tokens': response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            }

        except json.JSONDecodeError as e:
            # Debug: save raw response for inspection
            debug_file = GROUND_TRUTH_DIR / f"{file_id:04d}_debug.txt"
            with open(debug_file, 'w') as f:
                f.write(result_text if 'result_text' in locals() else 'NO RESPONSE')
            return {
                'file_id': file_id,
                'status': 'failed',
                'error': f'JSON parse error: {str(e)[:100]}',
                'response_preview': result_text[:200] if 'result_text' in locals() else None
            }
        except Exception as e:
            return {
                'file_id': file_id,
                'status': 'failed',
                'error': str(e)[:200]
            }


def needs_annotation(file_id: int) -> bool:
    """Check if a file needs (re)annotation - no valid v2 annotation exists"""
    output_file = GROUND_TRUTH_DIR / f"{file_id:04d}.json"
    if not output_file.exists():
        return True
    try:
        with open(output_file) as f:
            data = json.load(f)
        return data.get('schema_version') != '2.0'
    except:
        return True


async def annotate_files(api_key: str, api_provider: str, file_ids: list = None,
                         start: int = None, end: int = None, limit: int = None,
                         force: bool = False, retry_failed: bool = False):
    """Annotate files with v2 schema"""

    config = API_CONFIGS.get(api_provider)
    if not config:
        print(f"Unknown API provider: {api_provider}")
        return

    # Load file list
    with open(SUBSET_FILE, 'r') as f:
        reader = csv.DictReader(f)
        all_files = list(reader)

    # Filter files
    if file_ids:
        files_to_process = [f for f in all_files if int(f['file_id']) in file_ids]
    elif start is not None and end is not None:
        files_to_process = [f for f in all_files if start <= int(f['file_id']) <= end]
    else:
        files_to_process = all_files

    # Filter to only failed/missing if retry_failed
    if retry_failed:
        files_to_process = [f for f in files_to_process if needs_annotation(int(f['file_id']))]
        print(f"Retry mode: found {len(files_to_process)} files needing annotation")

    if limit:
        files_to_process = files_to_process[:limit]

    print(f"\n{'='*60}")
    print(f"Annotation v2 - {api_provider.upper()}")
    print(f"{'='*60}\n")
    print(f"API: {config['base_url']}")
    print(f"Model: {config['model']}")
    print(f"Files to process: {len(files_to_process)}")
    if force:
        print(f"Force re-annotation: enabled")
    print()

    # Create directories
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize client
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=config['base_url']
    )

    # Prepare tasks
    semaphore = asyncio.Semaphore(config['concurrent'])
    tasks = []

    for file_meta in files_to_process:
        file_id = int(file_meta['file_id'])
        html_file = HTML_DIR / f"{file_id:04d}.html"

        if not html_file.exists():
            print(f"⚠ File {file_id:04d}.html not found, skipping")
            continue

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        tasks.append(annotate_html_v2(
            client, file_id, html_content, file_meta['url'],
            config['model'], semaphore, force
        ))

    if not tasks:
        print("No files to process")
        return

    # Run
    print(f"Starting annotation of {len(tasks)} files...")
    print(f"Concurrent requests: {config['concurrent']}\n")

    results = []
    total_tokens = 0
    page_types = {}

    for coro in tqdm.as_completed(tasks, total=len(tasks)):
        result = await coro
        results.append(result)

        if result.get('tokens'):
            total_tokens += result['tokens']

        if result.get('page_type'):
            pt = result['page_type']
            page_types[pt] = page_types.get(pt, 0) + 1

    # Summary
    successful = [r for r in results if r['status'] == 'success']
    skipped = [r for r in results if r['status'] == 'skipped']
    failed = [r for r in results if r['status'] == 'failed']

    print(f"\n{'='*60}")
    print("Annotation Complete")
    print(f"{'='*60}\n")
    print(f"Total: {len(results)}")
    print(f"Success: {len(successful)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Failed: {len(failed)}")
    print(f"Tokens used: {total_tokens:,}")

    if page_types:
        print(f"\nPage types detected:")
        for pt, count in sorted(page_types.items(), key=lambda x: -x[1]):
            print(f"  {pt}: {count}")

    if failed:
        print(f"\nFailed files:")
        for f in failed[:5]:
            print(f"  {f['file_id']:04d}: {f.get('error', 'Unknown')[:60]}")
        if len(failed) > 5:
            print(f"  ... and {len(failed)-5} more")


async def main():
    parser = argparse.ArgumentParser(description="Annotate HTML files with v2 schema")
    parser.add_argument('--api-key', help="API key (optional if configured in script)")
    parser.add_argument('--api', choices=['deepseek', 'minimax'], default='minimax',
                        help="API provider (default: minimax)")
    parser.add_argument('--file-ids', type=int, nargs='+',
                        help="Specific file IDs to annotate")
    parser.add_argument('--start', type=int, help="Start file ID")
    parser.add_argument('--end', type=int, help="End file ID")
    parser.add_argument('--limit', type=int, help="Max files to process")
    parser.add_argument('--force', action='store_true',
                        help="Force re-annotation of existing v2 files")
    parser.add_argument('--retry-failed', action='store_true',
                        help="Only retry files that failed or have no v2 annotation")

    args = parser.parse_args()

    # Get API key: command line > config > environment variable
    api_key = args.api_key
    if not api_key:
        api_key = API_CONFIGS[args.api].get('api_key')
    if not api_key:
        import os
        env_var = f"{args.api.upper()}_API_KEY"
        api_key = os.environ.get(env_var)

    if not api_key:
        print(f"Error: No API key found for {args.api}")
        print(f"Provide via --api-key or set {args.api.upper()}_API_KEY environment variable")
        return

    await annotate_files(
        api_key=api_key,
        api_provider=args.api,
        file_ids=args.file_ids,
        start=args.start,
        end=args.end,
        limit=args.limit,
        force=args.force,
        retry_failed=args.retry_failed
    )


if __name__ == "__main__":
    asyncio.run(main())
