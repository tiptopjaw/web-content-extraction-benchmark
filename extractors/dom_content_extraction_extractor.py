"""
dom-content-extraction extractor wrapper

Calls the Rust CLI binary (CETD algorithm) and parses JSON output.
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional
from .base_extractor import BaseExtractor


class DomContentExtractionExtractor(BaseExtractor):
    """Wrapper for dom-content-extraction Rust content extractor (CETD algorithm)"""

    def __init__(self, binary_path: Optional[str] = None):
        """
        Initialize the extractor.

        Args:
            binary_path: Path to binary. If None, looks in:
                1. DOM_CONTENT_EXTRACTION_BIN environment variable
                2. ./rust-extractors/target/release/dce-extract
        """
        self._binary_path = binary_path
        self._resolved_path = None

    @property
    def name(self) -> str:
        return "dom-content-extraction"

    def _get_binary_path(self) -> str:
        """Resolve the binary path"""
        if self._resolved_path:
            return self._resolved_path

        import os

        # Check explicit path
        if self._binary_path:
            self._resolved_path = self._binary_path
            return self._resolved_path

        # Check environment variable
        env_path = os.environ.get('DOM_CONTENT_EXTRACTION_BIN')
        if env_path and Path(env_path).exists():
            self._resolved_path = env_path
            return self._resolved_path

        # Check relative path to rust-extractors
        relative_paths = [
            Path(__file__).parent.parent / 'rust-extractors' / 'target' / 'release' / 'dce-extract',
        ]
        for path in relative_paths:
            if path.exists():
                self._resolved_path = str(path)
                return self._resolved_path

        # Fall back to PATH
        self._resolved_path = 'dce-extract'
        return self._resolved_path

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """Extract content using dom-content-extraction CLI"""
        binary = self._get_binary_path()

        try:
            # Run the CLI with HTML on stdin
            result = subprocess.run(
                [binary],
                input=html,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {
                    'title': None,
                    'author': None,
                    'publish_date': None,
                    'main_content': ''
                }

            # Parse JSON output
            output = json.loads(result.stdout)

            return {
                'title': output.get('title'),
                'author': output.get('author'),
                'publish_date': output.get('date'),
                'main_content': output.get('main_content', '') or ''
            }

        except FileNotFoundError:
            raise RuntimeError(
                f"dce-extract binary not found at '{binary}'. "
                "Build it with: cd rust-extractors && cargo build --release"
            )
        except subprocess.TimeoutExpired:
            return {
                'title': None,
                'author': None,
                'publish_date': None,
                'main_content': ''
            }
        except json.JSONDecodeError:
            return {
                'title': None,
                'author': None,
                'publish_date': None,
                'main_content': ''
            }
