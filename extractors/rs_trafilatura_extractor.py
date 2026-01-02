"""
rs-trafilatura extractor wrapper

Calls the Rust CLI binary and parses JSON output.
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional
from .base_extractor import BaseExtractor


class RsTrafilaturaExtractor(BaseExtractor):
    """Wrapper for rs-trafilatura Rust content extractor"""

    def __init__(self, binary_path: Optional[str] = None):
        """
        Initialize the extractor.

        Args:
            binary_path: Path to rs-trafilatura binary. If None, looks in:
                1. RS_TRAFILATURA_BIN environment variable
                2. ../rs-trafilatura-private/target/release/rs-trafilatura
                3. rs-trafilatura in PATH
        """
        self._binary_path = binary_path
        self._resolved_path = None

    @property
    def name(self) -> str:
        return "rs-trafilatura"

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
        env_path = os.environ.get('RS_TRAFILATURA_BIN')
        if env_path and Path(env_path).exists():
            self._resolved_path = env_path
            return self._resolved_path

        # Check relative path to rs-trafilatura (submodule or sibling directory)
        relative_paths = [
            Path(__file__).parent.parent / 'rs-trafilatura' / 'target' / 'release' / 'extract_stdin',
            Path(__file__).parent.parent.parent.parent / 'rs-trafilatura-private' / 'target' / 'release' / 'extract_stdin',
            Path.home() / 'rs-trafilatura-private' / 'target' / 'release' / 'extract_stdin',
        ]
        for path in relative_paths:
            if path.exists():
                self._resolved_path = str(path)
                return self._resolved_path

        # Fall back to PATH
        self._resolved_path = 'rs-trafilatura'
        return self._resolved_path

    def extract(self, html: str, url: str) -> Dict[str, Optional[str]]:
        """Extract content using rs-trafilatura CLI"""
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
                # Return empty result on error
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
                f"rs-trafilatura binary not found at '{binary}'. "
                "Build it with: cd rs-trafilatura-private && cargo build --release"
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
