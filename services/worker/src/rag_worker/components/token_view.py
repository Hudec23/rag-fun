"""TokenView: adds per-Document token-view meta ('tokens', 'token_count', 'over_limit').
House style of components/: pure logic in a module-level helper so it is easy to unit test."""

from dataclasses import replace
from typing import Any

from haystack import Document, component
from tokenizers import Tokenizer

MAX_TOKENS_SHOWN = 2048


def lifted_view(tokenizer: Any) -> Tokenizer:
    """A copy of `tokenizer` with its baked truncation/padding lifted (no_truncation/no_padding)."""
    view = Tokenizer.from_str(tokenizer.to_str())
    view.no_truncation()
    view.no_padding()
    return view


def tokenize(tokenizer: Any, text: str, max_tokens: int) -> dict[str, Any]:
    """enc = lifted_view(tokenizer).encode(text) (special tokens included) ->
    {'tokens': enc.tokens[:2048], 'token_count': len(enc.ids),
    'over_limit': len(enc.ids) > max_tokens}."""
    enc = lifted_view(tokenizer).encode(text)
    return {
        "tokens": enc.tokens[:MAX_TOKENS_SHOWN],
        "token_count": len(enc.ids),
        "over_limit": len(enc.ids) > max_tokens,
    }


@component
class TokenView:
    """Adds meta 'tokens', 'token_count', 'over_limit' to each Document (tokenize)."""

    def __init__(self, tokenizer: Any, max_tokens: int) -> None:
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens

    @component.output_types(documents=list[Document])
    def run(self, documents: list[Document]) -> dict[str, Any]:
        result: list[Document] = []
        for doc in documents:
            t = tokenize(self.tokenizer, doc.content or "", self.max_tokens)
            meta = dict(doc.meta)
            meta.update(t)
            result.append(replace(doc, meta=meta))
        return {"documents": result}
