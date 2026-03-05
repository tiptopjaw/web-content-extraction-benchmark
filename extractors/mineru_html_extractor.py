"""
MinerU-HTML (Dripper) extractor wrapper
Uses a fine-tuned Qwen3-0.6B model to classify HTML elements as main/other content.
https://github.com/opendatalab/MinerU-HTML
"""
import json
import re
from typing import Dict, Optional

from .base_extractor import BaseExtractor

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from dripper.process.simplify_html import simplify_html
    from dripper.inference.prompt import get_full_prompt
    from dripper.process.map_to_main import extract_main_html
    from bs4 import BeautifulSoup
    MINERU_AVAILABLE = True
except ImportError:
    MINERU_AVAILABLE = False

# Singleton model holder to avoid reloading for each file
_model = None
_tokenizer = None


def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    model_path = '/home/slimbook/models/MinerU-HTML'
    _tokenizer = AutoTokenizer.from_pretrained(model_path)

    # Force CPU to avoid GPU memory conflicts with Ollama / ROCm instability
    _model = AutoModelForCausalLM.from_pretrained(model_path, dtype=torch.float32)
    _model.eval()

    return _model, _tokenizer


class MineruHtmlExtractor(BaseExtractor):
    """Wrapper for MinerU-HTML (Dripper) content extractor"""

    def __init__(self):
        if MINERU_AVAILABLE:
            _load_model()

    @property
    def name(self) -> str:
        return "mineru-html"

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        if not MINERU_AVAILABLE:
            raise ImportError(
                "MinerU-HTML dependencies not available. "
                "Need: transformers, torch, dripper, beautifulsoup4"
            )

        model, tokenizer = _load_model()

        # Step 1: Simplify HTML and add item IDs
        simplified_html, mapped_html = simplify_html(html)

        # Step 2: Build classification prompt
        prompt = get_full_prompt(simplified_html)

        # Step 3: Tokenize and check length
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=32768)
        # Model runs on CPU — no device transfer needed

        # Step 4: Generate classification
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=4096,
                temperature=0.0,
                do_sample=False,
            )

        response_text = tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        # Strip <think> tags from Qwen3 thinking output
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()

        # Step 5: Parse JSON response
        response_dict = json.loads(response_text)

        # Step 6: Extract main content HTML using classification
        main_html = extract_main_html(mapped_html, response_dict)

        # Step 7: Convert to plain text
        soup = BeautifulSoup(main_html, 'html.parser')
        main_content = soup.get_text(separator='\n', strip=True)

        return {
            'title': None,  # MinerU-HTML doesn't extract titles
            'author': None,
            'publish_date': None,
            'main_content': main_content,
        }
