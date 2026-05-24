"""
Vietnamese Tokenizer Handler using vntokenizer4.1
Stopwords loaded from: stopwords_vi.txt
"""
from vntokenizer import VnTokenizer
from functools import lru_cache
import os


class TokenizerHandler:
    """Handle Vietnamese text tokenization and stopword filtering"""
    
    _STOPWORDS_VI = None
    
    @classmethod
    def _load_stopwords(cls):
        """Load stopwords from file"""
        if cls._STOPWORDS_VI is not None:
            return cls._STOPWORDS_VI
        
        stopwords_file = os.path.join(os.path.dirname(__file__), 'stopwords_vi.txt')
        stopwords = set()
        
        if os.path.exists(stopwords_file):
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        stopwords.add(word)
        
        cls._STOPWORDS_VI = stopwords
        return stopwords
    
    @classmethod
    def get_stopwords(cls):
        """Get stopwords set"""
        if cls._STOPWORDS_VI is None:
            cls._load_stopwords()
        return cls._STOPWORDS_VI
    
    def __init__(self):
        """Initialize tokenizer"""
        self.tokenizer = VnTokenizer
        self.stopwords = self.get_stopwords()
    
    @staticmethod
    @lru_cache(maxsize=1024)
    def tokenize(text):
        """Tokenize Vietnamese text"""
        if not text or not isinstance(text, str):
            return []
        try:
            tokens = VnTokenizer.tokenize(text)
            return tokens.split()
        except:
            return []
    
    def clean_and_tokenize(self, text):
        """Clean, tokenize and remove stopwords"""
        if not text:
            return []
        text = text.lower().strip()
        tokens = self.tokenize(text)
        return [t for t in tokens if t not in self.stopwords and len(t.strip()) > 1 and not t.startswith('http')]
    
    def extract_keywords(self, text, min_length=2):
        """Extract keywords from text"""
        tokens = self.clean_and_tokenize(text)
        return [t for t in tokens if len(t) >= min_length]
    def __init__(self):
        """Initialize tokenizer"""
        self.tokenizer = VnTokenizer
    
    @staticmethod
    @lru_cache(maxsize=1024)
    def tokenize(text):
        """
        Tokenize Vietnamese text
        Args:
            text: Vietnamese text string
        Returns:
            List of tokens
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            # Tokenize using vntokenizer
            tokens = VnTokenizer.tokenize(text)
            return tokens.split()
        except Exception as e:
            print(f"Tokenization error for text: {text[:50]}... Error: {e}")
            return []
    
    @staticmethod
    def clean_and_tokenize(text):
        """
        Clean, tokenize and remove stopwords
        Args:
            text: Vietnamese text string
        Returns:
            List of cleaned tokens (lowercased, stopwords removed)
        """
        if not text:
            return []
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Tokenize
        tokens = TokenizerHandler.tokenize(text)
        
        # Remove stopwords and clean
        cleaned_tokens = [
            token for token in tokens 
            if token not in TokenizerHandler.STOPWORDS_VI 
            and len(token.strip()) > 1
            and not token.startswith('http')
        ]
        
        return cleaned_tokens
    
    @staticmethod
    def extract_keywords(text, min_length=2):
        """
        Extract keywords from Vietnamese text
        Args:
            text: Vietnamese text string
            min_length: Minimum token length to include
        Returns:
            List of keyword tokens
        """
        tokens = TokenizerHandler.clean_and_tokenize(text)
        return [t for t in tokens if len(t) >= min_length]
