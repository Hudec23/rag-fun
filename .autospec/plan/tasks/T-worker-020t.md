---
id: T-worker-020t
kind: test
feature: F-chunk
title: 'Write tests: StructureChunker (Docling HybridChunker)'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_structure_chunker.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_structure_chunker.py && uv run --frozen ruff check tests/unit/test_structure_chunker.py && uv run --frozen pytest -q --collect-only tests/unit/test_structure_chunker.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_structure_chunker.py
max_attempts: 3
---

## Goal
Write unit tests for: StructureChunker (Docling HybridChunker). Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-020 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. TokenizerAdapter(load_tokenizer('all-minilm'), 128).count_tokens('hello world') == 2 and get_max_tokens() == 128
2. StructureChunker(tokenizer, 64, True).run(docling_json of a DoclingDocument with title, 2 headings and 6 paragraphs) → documents; each has meta no_span True and section_path a list of headings
3. every chunk's token count (adapter) ≤ 64 + heading context
4. a document with a table item → at least one chunk with element_type 'table' or 'mixed'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
