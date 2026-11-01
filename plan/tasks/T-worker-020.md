---
id: T-worker-020
kind: impl
feature: F-chunk
title: StructureChunker (Docling HybridChunker)
service: worker
depends_on:
- T-worker-020t
- T-worker-012
edit:
- services/worker/src/rag_worker/components/structure_chunker.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_structure_chunker.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/structure_chunker.py && uv run --frozen ruff check src/rag_worker/components/structure_chunker.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_structure_chunker.py
max_attempts: 3
---

## Goal
Implement: StructureChunker (Docling HybridChunker). The tests written by T-worker-020t define done.

## Context
Build the DoclingDocument in the test with docling_core (no model files). load_tokenizer from rag_worker.models.registry.

Stub in `services/worker/src/rag_worker/components/structure_chunker.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
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
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
