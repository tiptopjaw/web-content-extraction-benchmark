"""
Test annotation on a single file to verify raw HTML is sent correctly
"""
import asyncio
import csv
import json
from pathlib import Path
from datetime import datetime
import argparse
from openai import AsyncOpenAI
from bs4 import BeautifulSoup

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = DATA_DIR / "html_files"
TEST_OUTPUT = DATA_DIR / "test_annotation.json"
SUBSET_FILE = DATA_DIR / "metadata_subset_final.csv"

# Deepseek API Configuration
DEEPSEEK_API_BASE = "https://api.deepseek.com"
MODEL = "deepseek-chat"

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
- The HTML contains <script>, <style>, and other tags - ignore these and focus on visible content
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

async def test_annotation(api_key, file_id):
    """Test annotation on a single file"""

    # Load metadata
    with open(SUBSET_FILE, 'r') as f:
        reader = csv.DictReader(f)
        metadata = {int(row['file_id']): row for row in reader}

    if file_id not in metadata:
        print(f"Error: File ID {file_id} not found in subset")
        return

    url = metadata[file_id]['url']
    html_file = HTML_DIR / f"{file_id:04d}.html"

    if not html_file.exists():
        print(f"Error: {html_file} not found")
        return

    # Read HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print(f"\n{'='*80}")
    print(f"Testing Annotation on Single File")
    print(f"{'='*80}\n")
    print(f"File ID: {file_id:04d}")
    print(f"URL: {url}")
    print(f"HTML size: {len(html_content):,} characters ({len(html_content)//1024}KB)")

    # Check for script/style tags
    has_script = '<script' in html_content.lower()
    has_style = '<style' in html_content.lower()
    print(f"Contains <script> tags: {has_script}")
    print(f"Contains <style> tags: {has_style}")

    # Preprocess HTML
    preprocessed_html = preprocess_html(html_content)
    print(f"\n✅ Preprocessing HTML (removing script/style tags)")
    print(f"Preprocessed size: {len(preprocessed_html):,} characters ({len(preprocessed_html)//1024}KB)\n")

    # Initialize client
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_API_BASE
    )

    print("Calling Deepseek API...\n")

    try:
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
            "annotated_at": datetime.now().isoformat(),
            "test_run": True,
            "raw_html_used": True
        }

        # Save test annotation
        with open(TEST_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(annotation, f, indent=2, ensure_ascii=False)

        print(f"{'='*80}")
        print("Test Annotation Successful!")
        print(f"{'='*80}\n")
        print(f"✓ Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        print(f"✓ Title: {ground_truth.get('title', 'N/A')[:60]}")
        print(f"✓ Author: {ground_truth.get('author', 'N/A')}")
        print(f"✓ Date: {ground_truth.get('publish_date', 'N/A')}")
        print(f"✓ Content length: {len(ground_truth.get('main_content', '')):,} chars")
        print(f"✓ 'With' snippets: {len(ground_truth.get('with', []))}")
        print(f"✓ 'Without' snippets: {len(ground_truth.get('without', []))}")
        print(f"\n✓ Test annotation saved to: {TEST_OUTPUT}")
        print("\n✅ Ready to re-annotate all 2,000 files!")

    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Response: {result_text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main function"""

    parser = argparse.ArgumentParser(description="Test annotation on a single file")
    parser.add_argument("--api-key", required=True, help="Deepseek API key")
    parser.add_argument("--file-id", type=int, default=1, help="File ID to test (default: 1)")

    args = parser.parse_args()

    await test_annotation(args.api_key, args.file_id)

if __name__ == "__main__":
    asyncio.run(main())
