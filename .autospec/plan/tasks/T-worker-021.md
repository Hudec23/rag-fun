---
id: T-worker-021
kind: impl
feature: F-chunk
title: chunk pipelines for 6 strategies
service: worker
depends_on:
- T-worker-021t
- T-worker-018
- T-worker-019
- T-worker-020
edit:
- services/worker/src/rag_worker/pipelines/chunk.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_chunk_pipeline.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/chunk.py && uv run --frozen ruff check src/rag_worker/pipelines/chunk.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_chunk_pipeline.py
max_attempts: 3
---

## Goal
Implement: chunk pipelines for 6 strategies. The tests written by T-worker-021t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
