from transform.keywords.tokenizer_handler import TokenizerHandler


def test_clean_and_tokenize_filters_stopwords_short_and_urls(monkeypatch):
    handler = TokenizerHandler()

    # Keep this test deterministic and independent from external tokenizer package.
    monkeypatch.setattr(
        TokenizerHandler,
        "tokenize",
        staticmethod(lambda _text: ["xin", "chao", "la", "http://abc", "ai", "vietnam"]),
    )
    handler.stopwords = {"la"}

    tokens = handler.clean_and_tokenize("Xin chao la http://abc AI vietnam")

    assert tokens == ["xin", "chao", "ai", "vietnam"]


def test_extract_keywords_applies_min_length(monkeypatch):
    monkeypatch.setattr(TokenizerHandler, "get_stopwords", classmethod(lambda cls: set()))
    monkeypatch.setattr(
        TokenizerHandler,
        "tokenize",
        staticmethod(lambda _text: ["a", "ab", "abc", "tin"]),
    )

    keywords = TokenizerHandler.extract_keywords("dummy", min_length=3)

    assert keywords == ["abc", "tin"]


def test_tokenize_returns_empty_for_invalid_input():
    assert TokenizerHandler.tokenize(None) == []
    assert TokenizerHandler.tokenize(123) == []
