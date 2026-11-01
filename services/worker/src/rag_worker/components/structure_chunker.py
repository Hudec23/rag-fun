from typing import Any

from haystack import Document, component


class TokenizerAdapter:
    """docling_core BaseTokenizer over a `tokenizers.Tokenizer`: count_tokens(text) =
    len(encode(text, add_special_tokens=False).ids); get_max_tokens() = max_tokens;
    get_tokenizer() = the tokenizer."""

    def __init__(self, tokenizer: Any, max_tokens: int) -> None:
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens


@component
class StructureChunker:
    """strategy 'structure': docling HybridChunker(tokenizer=TokenizerAdapter(..., max_tokens),
    merge_peers) over the DoclingDocument JSON; each chunk -> Document(content =
    chunker.contextualize(chunk), meta no_span True, section_path = chunk.meta.headings or [],
    page_numbers = sorted pages of chunk.meta.doc_items prov, element_type 'table' if every doc item is
    a table else 'mixed' if any is a table else 'text')."""

    def __init__(self, tokenizer: Any, max_tokens: int, merge_peers: bool) -> None:
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens
        self.merge_peers = merge_peers

    @component.output_types(documents=list[Document])
    def run(self, docling_json: str) -> dict[str, Any]:
        raise NotImplementedError("not implemented")
