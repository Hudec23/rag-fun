"""Docling HybridChunker strategy 'structure': one class per file, @component, typed
output_types, pure logic in module-level helpers (house style of components/)."""

from collections.abc import Iterator
from typing import Any, cast

from docling.chunking import HybridChunker
from docling_core.transforms.chunker import DocChunk
from docling_core.transforms.chunker.tokenizer.base import BaseTokenizer
from docling_core.types.doc import DocItem, DocItemLabel, DoclingDocument
from haystack import Document, component


def page_numbers_of(items: list[DocItem]) -> list[int]:
    """Sorted unique page numbers over all provenance items of the doc items."""
    return sorted({p.page_no for it in items for p in it.prov})


def element_type_of(items: list[DocItem]) -> str:
    """table only -> 'table'; table + other -> 'mixed'; no table -> 'text'."""
    if not items:
        return "text"
    tables = [it for it in items if it.label == DocItemLabel.TABLE]
    if tables and len(tables) == len(items):
        return "table"
    if tables:
        return "mixed"
    return "text"


class TokenizerAdapter(BaseTokenizer):
    """docling_core BaseTokenizer over a `tokenizers.Tokenizer`: count_tokens(text) =
    number of non-pad ids of encode(text, add_special_tokens=False); get_max_tokens() =
    max_tokens; get_tokenizer() = the tokenizer."""

    def __init__(self, tokenizer: Any, max_tokens: int) -> None:
        super().__init__(tokenizer=tokenizer, max_tokens=max_tokens)

    tokenizer: Any
    max_tokens: int

    def count_tokens(self, text: str) -> int:
        ids = self.tokenizer.encode(text, add_special_tokens=False).ids
        return len([i for i in ids if i != 0])

    def get_max_tokens(self) -> int:
        return self.max_tokens

    def get_tokenizer(self) -> Any:
        return self.tokenizer


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
        doc = DoclingDocument.model_validate_json(docling_json)
        chunker = HybridChunker(
            tokenizer=TokenizerAdapter(tokenizer=self.tokenizer, max_tokens=self.max_tokens),
            merge_peers=self.merge_peers,
        )
        documents: list[Document] = []
        for chunk in cast(Iterator[DocChunk], chunker.chunk(doc)):
            items = chunk.meta.doc_items
            documents.append(
                Document(
                    content=chunker.contextualize(chunk),
                    meta={
                        "no_span": True,
                        "section_path": chunk.meta.headings or [],
                        "page_numbers": page_numbers_of(items),
                        "element_type": element_type_of(items),
                    },
                )
            )
        return {"documents": documents}
