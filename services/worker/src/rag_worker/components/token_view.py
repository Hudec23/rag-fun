from typing import Any

from haystack import Document, component

MAX_TOKENS_SHOWN = 2048


def tokenize(tokenizer: Any, text: str, max_tokens: int) -> dict[str, Any]:
    """enc = tokenizer.encode(text) (special tokens included) -> {'tokens': enc.tokens[:2048],
    'token_count': len(enc.ids), 'over_limit': len(enc.ids) > max_tokens}."""
    raise NotImplementedError("not implemented")


@component
class TokenView:
    """Adds meta 'tokens', 'token_count', 'over_limit' to each Document (tokenize)."""

    def __init__(self, tokenizer: Any, max_tokens: int) -> None:
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens

    @component.output_types(documents=list[Document])
    def run(self, documents: list[Document]) -> dict[str, Any]:
        raise NotImplementedError("not implemented")
