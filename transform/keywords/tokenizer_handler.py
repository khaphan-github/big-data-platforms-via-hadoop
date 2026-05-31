"""
Vietnamese tokenizer handler with stopword filtering.
Uses pyvi when available, otherwise falls back to whitespace split.
"""

from functools import lru_cache
import os

try:
    from pyvi import ViTokenizer  # type: ignore
except Exception:
    ViTokenizer = None


class TokenizerHandler:
    """Handle Vietnamese text tokenization and stopword filtering."""

    _STOPWORDS_VI = None

    @classmethod
    def _load_stopwords(cls):
        """Load stopwords from stopwords_vi.txt once."""
        if cls._STOPWORDS_VI is not None:
            return cls._STOPWORDS_VI

        stopwords_file = os.path.join(os.path.dirname(__file__), "stopwords_vi.txt")
        stopwords = set()

        if os.path.exists(stopwords_file):
            with open(stopwords_file, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:
                        stopwords.add(word)

        cls._STOPWORDS_VI = stopwords
        return stopwords

    @classmethod
    def get_stopwords(cls):
        """Return cached stopwords set."""
        if cls._STOPWORDS_VI is None:
            cls._load_stopwords()
        return cls._STOPWORDS_VI

    def __init__(self):
        self.stopwords = self.get_stopwords()

    @staticmethod
    @lru_cache(maxsize=1024)
    def tokenize(text):
        """Tokenize text using pyvi if available; fallback otherwise."""
        if not text or not isinstance(text, str):
            return []

        if ViTokenizer is not None:
            try:
                tokens = ViTokenizer.tokenize(text)
                return tokens.split()
            except Exception:
                return []

        return text.split()

    def clean_and_tokenize(self, text):
        """Lowercase, tokenize, remove stopwords/noise tokens."""
        if not text:
            return []

        text = text.lower().strip()
        tokens = self.tokenize(text)

        return [
            t
            for t in tokens
            if t not in self.stopwords and len(t.strip()) > 1 and not t.startswith("http")
        ]

    @classmethod
    def extract_keywords(cls, text, min_length=2):
        """Extract keyword tokens by length threshold."""
        handler = cls()
        tokens = handler.clean_and_tokenize(text)
        return [t for t in tokens if len(t) >= min_length]
