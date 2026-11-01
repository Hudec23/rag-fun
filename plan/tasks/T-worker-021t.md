---
id: T-worker-021t
kind: test
feature: F-chunk
title: 'Write tests: chunk pipelines for 6 strategies'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_chunk_pipeline.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_chunk_pipeline.py && uv run --frozen ruff check tests/unit/test_chunk_pipeline.py && uv run --frozen pytest -q --collect-only tests/unit/test_chunk_pipeline.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_chunk_pipeline.py
max_attempts: 3
---

## Goal
Write unit tests for: chunk pipelines for 6 strategies. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-021 implements it.

## Context
Use FakeModelSet and DenseModelConfig(model='all-minilm', dims=384, ollama_url='http://x').

Stub in `services/worker/src/rag_worker/pipelines/chunk.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.contracts_gen.shared.common_schema import DenseModelConfig
from rag_worker.models.registry import ModelSet


def build_chunk_pipeline(
    strategy: str, params: dict[str, Any], models: ModelSet, dense: DenseModelConfig
) -> Pipeline:
    """'splitter' -> 'annotator' (ChunkAnnotator; splitter.documents -> annotator.documents).
    fixed + split_by word: DocumentSplitter(split_by='word', split_length=length, split_overlap=overlap).
    fixed + split_by char: DocumentSplitter(split_by='function', splitting_function=chars (module-level
    `def chars(text): return list(text)`), split_length=length, split_overlap=overlap) — exact character
    windows. sentence: DocumentSplitter(split_by='sentence', split_length, split_overlap, language='en').
    recursive: RecursiveDocumentSplitter(split_length, split_overlap, split_unit='char', separators).
    semantic: SemanticSplitter(models.dense_text_embedder(dense), breakpoint_percentile, min_sentences,
    max_sentences). structure: StructureChunker(models.tokenizer(dense.model), max_tokens, merge_peers)
    — input docling_json. table: TableChunker(row_chunks, text_length, text_overlap) — input elements +
    source_text. Every splitter: from haystack.components.preprocessors import DocumentSplitter,
    RecursiveDocumentSplitter."""
    raise NotImplementedError("not implemented")

def run_chunk(
    pipeline: Pipeline,
    strategy: str,
    parse_artifact: dict[str, Any],
    docling_json: str | None,
    file_id: str,
) -> dict[str, Any]:
    """Feed the pipeline per strategy (fixed/sentence/recursive/semantic: documents=[Document(
    content=full_text)]; structure: docling_json (None -> WorkerError('UNSUPPORTED_FOR_STRATEGY',
    details={'parse_strategy': 'plain_text'})); table: elements + source_text); annotator also gets
    elements, source_text = full_text, file_id. -> {'chunks': [...], 'semantic': dict | None}."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. fixed word length 4 overlap 2 on parse artifact FIXTURES/artifact_parse.json → chunks of ≤4 words, consecutive chunks share 2 words, every chunk has a valid span into full_text
2. fixed char length 10 overlap 0 → every chunk text length ≤ 10 and joined texts == full_text
3. sentence length 1 → one chunk per sentence; recursive length 80 → every chunk ≤ 80 chars
4. semantic → result['semantic'] not None with gaps; others → semantic None
5. structure with docling_json None → WorkerError UNSUPPORTED_FOR_STRATEGY details {'parse_strategy': 'plain_text'}
6. table strategy on an artifact containing a table element → a chunk with element_type 'table'
7. pipeline graph names: pipeline.to_dict()['components'] keys == {'splitter', 'annotator'}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
