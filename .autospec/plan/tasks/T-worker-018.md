---
id: T-worker-018
kind: impl
feature: F-chunk
title: SemanticSplitter
service: worker
depends_on:
- T-worker-018t
edit:
- services/worker/src/rag_worker/components/semantic_splitter.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_semantic_splitter.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/semantic_splitter.py && uv run --frozen ruff check src/rag_worker/components/semantic_splitter.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_semantic_splitter.py
max_attempts: 3
---

## Goal
Implement: SemanticSplitter. The tests written by T-worker-018t define done.

## Context
Stub in `services/worker/src/rag_worker/components/semantic_splitter.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Document, component


def breakpoints(distances: list[float], percentile: int) -> tuple[float, list[bool]]:
    """threshold = numpy.percentile(distances, percentile); is_break[i] = distances[i] > threshold.
    [] -> (0.0, [])."""
    raise NotImplementedError("not implemented")

def group_sentences(
    sentences: list[str], is_break: list[bool], min_sentences: int, max_sentences: int
) -> list[list[int]]:
    """Group sentence indices: start a new group after sentence i when is_break[i] and the current
    group has >= min_sentences, or when the group reached max_sentences. Every index appears once,
    in order."""
    raise NotImplementedError("not implemented")

@component
class SemanticSplitter:
    """Sentences via NLTK punkt (nltk.sent_tokenize, language english) on the single input Document;
    embed every sentence with `embedder` (a Haystack text embedder component: run(text) ->
    {'embedding'}); distance[i] = 1 - cosine(sentence i, sentence i+1); breakpoints; group; each
    group -> Document(content = joined sentence texts exactly as in the source (from first sentence
    start to last sentence end), meta split_idx_start). Also outputs the gaps for the artifact
    'semantic' block: {'threshold', 'gaps': [{'after_sentence', 'distance', 'is_break'}]}."""

    def __init__(
        self, embedder: Any, breakpoint_percentile: int, min_sentences: int, max_sentences: int
    ) -> None:
        self.embedder = embedder
        self.breakpoint_percentile = breakpoint_percentile
        self.min_sentences = min_sentences
        self.max_sentences = max_sentences

    @component.output_types(documents=list[Document], semantic=dict[str, Any])
    def run(self, documents: list[Document]) -> dict[str, Any]:
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
