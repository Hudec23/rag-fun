---
id: T-worker-030t
kind: test
feature: F-retrieve
title: 'Write tests: Hit conversions'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_hits.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_hits.py && uv run --frozen ruff check tests/unit/test_hits.py && uv run --frozen pytest -q --collect-only tests/unit/test_hits.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_hits.py
max_attempts: 3
---

## Goal
Write unit tests for: Hit conversions. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-030 implements it.

## Context
Stub in `services/worker/src/rag_worker/components/hits.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Document
from rag_worker.contracts_gen.qdrant.payload_schema import Meta


def to_hit(doc: Document, rank: int, score: float | None = None) -> dict[str, Any]:
    """Retrieved Haystack Document -> Hit (contracts/shared/common.schema.json#/$defs/Hit):
    point_id = qdrant convert_id(doc.id), doc_id = doc.id, rank, score = score or doc.score or 0.0
    (round 6), content, meta = doc.meta (validated with Meta)."""
    _ = Meta
    raise NotImplementedError("not implemented")

def hit_to_document(hit: dict[str, Any]) -> Document:
    """Inverse for reranking: Document(id=doc_id, content, meta, score)."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. to_hit(Document(id=doc_id, content='x', meta=fixture meta, score=0.12345678), 1) → point_id == convert_id(doc_id), rank 1, score 0.123457, validates shared/common.schema.json#/$defs/Hit
2. explicit score argument wins over doc.score; missing score → 0.0
3. invalid meta (missing file_id) → pydantic ValidationError
4. hit_to_document(to_hit(doc, 1)) has the same id, content, meta, score

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
