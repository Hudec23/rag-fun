---
id: T-worker-018t
kind: test
feature: F-chunk
title: 'Write tests: SemanticSplitter'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_semantic_splitter.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_semantic_splitter.py && uv run --frozen ruff check tests/unit/test_semantic_splitter.py && uv run --frozen pytest -q --collect-only tests/unit/test_semantic_splitter.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_semantic_splitter.py
max_attempts: 3
---

## Goal
Write unit tests for: SemanticSplitter. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-018 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. breakpoints([0.1, 0.9, 0.2], 50) → threshold 0.2, is_break [False, True, False]
2. breakpoints([], 90) == (0.0, [])
3. group_sentences(4 sentences, [False, True, False], 1, 10) == [[0, 1], [2, 3]]
4. min_sentences 3 suppresses an early break: is_break [True, False, False], min 3 → [[0, 1, 2, 3]]
5. max_sentences 2 forces splits: 5 sentences, no breaks → [[0, 1], [2, 3], [4]]
6. SemanticSplitter(FakeDenseTextEmbedder(64), 50, 1, 10).run([Document(content='Cats purr. Cats sleep. Taxes rise. Taxes hurt.')]) → ≥2 documents whose contents are exact substrings of the input with meta split_idx_start matching; semantic['gaps'] has 3 entries

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
