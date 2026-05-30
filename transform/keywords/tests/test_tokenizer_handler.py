from ..trending_words_job import extract_keywords, tokenize

def test_extract_keywords_filters_stopwords_short_and_urls(monkeypatch):
    monkeypatch.setattr(
        "trending_words_job.tokenize",
        lambda _text: ["xin", "chao", "la", "http://abc", "ai", "vietnam"],
    )
    monkeypatch.setattr(
        "trending_words_job._load_stopwords",
        lambda: {"la"}
    )
    
    keywords = extract_keywords("Xin chao la http://abc AI vietnam")
    assert keywords == ["xin", "chao", "ai", "vietnam"]


def test_extract_keywords_applies_min_length(monkeypatch):
    monkeypatch.setattr(
        "trending_words_job.tokenize",
        lambda _text: ["a", "ab", "abc", "tin"],
    )
    monkeypatch.setattr(
        "trending_words_job._load_stopwords",
        lambda: set()
    )
    
    keywords = extract_keywords("dummy", min_length=3)
    assert keywords == ["abc", "tin"]




def test_tokenize_returns_empty_for_invalid_input():
    assert TokenizerHandler.tokenize(None) == []
    assert TokenizerHandler.tokenize(123) == []
