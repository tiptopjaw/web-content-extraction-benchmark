"""
ReaderLM-v2 extractor wrapper (https://huggingface.co/jinaai/ReaderLM-v2)
Uses Jina's 1.5B model via Ollama to convert HTML to Markdown, then strips formatting.
"""
import json
import re
import urllib.request
from typing import Dict, Optional

from .base_extractor import BaseExtractor

SCRIPT_PATTERN = r"<[ ]*script.*?\/[ ]*script[ ]*>"
STYLE_PATTERN = r"<[ ]*style.*?\/[ ]*style[ ]*>"
META_PATTERN = r"<[ ]*meta.*?>"
COMMENT_PATTERN = r"<[ ]*!--.*?--[ ]*>"
LINK_PATTERN = r"<[ ]*link.*?>"
SVG_PATTERN = r"(<svg[^>]*>)(.*?)(<\/svg>)"
BASE64_IMG_PATTERN = r'<img[^>]+src="data:image/[^;]+;base64,[^"]+"[^>]*>'


def clean_html(html: str) -> str:
    """Strip scripts, styles, comments, meta, SVGs, base64 images from HTML."""
    html = re.sub(SCRIPT_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    html = re.sub(STYLE_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    html = re.sub(META_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    html = re.sub(COMMENT_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    html = re.sub(LINK_PATTERN, "", html, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    html = re.sub(SVG_PATTERN, lambda m: f"{m.group(1)}placeholder{m.group(3)}", html, flags=re.DOTALL)
    html = re.sub(BASE64_IMG_PATTERN, '<img src="#"/>', html)
    return html


def markdown_to_plain_text(md: str) -> str:
    """Convert Markdown to plain text by stripping formatting."""
    # Remove markdown code fences wrapping the output
    md = re.sub(r'^```markdown\s*\n?', '', md, flags=re.MULTILINE)
    md = re.sub(r'\n?```\s*$', '', md, flags=re.MULTILINE)
    # Remove heading markers
    md = re.sub(r'^#{1,6}\s+', '', md, flags=re.MULTILINE)
    # Remove bold/italic markers
    md = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', md)
    md = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', md)
    # Convert markdown links to just the text
    md = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', md)
    # Remove image syntax
    md = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', md)
    # Clean up extra whitespace
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip()


class ReaderLmExtractor(BaseExtractor):
    """Wrapper for Jina ReaderLM-v2 via Ollama"""

    OLLAMA_MODEL = "GFalcon-UA/ReaderLM-v2:Q8"
    OLLAMA_URL = "http://localhost:11434/api/chat"

    @property
    def name(self) -> str:
        return "readerlm-v2"

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        # Step 1: Clean HTML
        cleaned = clean_html(html)

        # Step 2: Build prompt per ReaderLM-v2 spec
        prompt = (
            "Extract the main content from the given HTML and "
            "convert it to Markdown format.\n"
            f"```html\n{cleaned}\n```"
        )

        # Step 3: Call Ollama
        payload = json.dumps({
            "model": self.OLLAMA_MODEL,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 8192,
                "repeat_penalty": 1.08,
                "num_ctx": 32768,
            },
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = urllib.request.Request(
            self.OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read())

        markdown_content = result['message']['content']

        # Step 4: Extract title from first heading if present
        title = None
        title_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Step 5: Convert Markdown to plain text
        main_content = markdown_to_plain_text(markdown_content)

        return {
            'title': title,
            'author': None,
            'publish_date': None,
            'main_content': main_content,
        }
