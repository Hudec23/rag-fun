"""Unit tests for TokenView/tokenize (enc = tokenizer.encode(text), special tokens included):
build inputs inline, call tokenize()/run() directly, assert exact dicts.
TokenView is a stub — every test here is red until T-worker-023."""

from haystack import Document
from tokenizers import Tokenizer

from rag_worker.components.token_view import MAX_TOKENS_SHOWN, TokenView, tokenize
from rag_worker.models.registry import load_tokenizer

OVER_LIMIT_TEXT = " ".join(f"word{n}" for n in range(300))
VERY_LONG_TEXT = " ".join(f"verylongword{n}" for n in range(2500))


def test_tokenize_exact_tokens_count_and_over_limit() -> None:
    result = tokenize(load_tokenizer("all-minilm"), "Hello world", 256)
    assert result == {
        "tokens": ["[CLS]", "hello", "world", "[SEP]"],
        "token_count": 4,
        "over_limit": False,
    }


def test_tokenize_over_limit_true_when_count_exceeds_max_tokens() -> None:
    result = tokenize(load_tokenizer("all-minilm"), OVER_LIMIT_TEXT, 256)
    assert result["token_count"] > 256
    assert result["over_limit"] is True


def test_tokenize_truncates_tokens_to_max_shown_but_counts_all() -> None:
    tokenizer = load_tokenizer("all-minilm")
    result = tokenize(tokenizer, VERY_LONG_TEXT, 256)
    # full count = the tokenizer with its baked truncation(128)/padding(128) config lifted
    oracle = Tokenizer.from_str(tokenizer.to_str())
    oracle.no_truncation()
    oracle.no_padding()
    full_count = len(oracle.encode(VERY_LONG_TEXT).ids)
    assert full_count > MAX_TOKENS_SHOWN
    assert len(result["tokens"]) == MAX_TOKENS_SHOWN
    assert result["token_count"] == full_count
    assert result["over_limit"] is True


def test_run_returns_copies_with_token_meta_originals_unchanged() -> None:
    doc = Document(content="Hello world", meta={"note": "keep"})
    [out] = TokenView(load_tokenizer("all-minilm"), 256).run(documents=[doc])["documents"]
    assert out is not doc
    assert out.content == "Hello world"
    assert out.meta["tokens"] == ["[CLS]", "hello", "world", "[SEP]"]
    assert out.meta["token_count"] == 4
    assert out.meta["over_limit"] is False
    assert out.meta["note"] == "keep"
    assert doc.meta == {"note": "keep"}
    assert doc.content == "Hello world"
