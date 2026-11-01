---
id: T-worker-038t
kind: test
feature: F-generate
title: 'Write tests: generate job with streaming'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_generate_job.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_generate_job.py && uv run --frozen ruff check tests/unit/test_generate_job.py && uv run --frozen pytest -q --collect-only tests/unit/test_generate_job.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_generate_job.py
max_attempts: 3
---

## Goal
Write unit tests for: generate job with streaming. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-038 implements it.

## Context
Streaming callbacks run in a worker thread (pipeline.run inside asyncio.to_thread): publish tokens via asyncio.run_coroutine_threadsafe(events.publish(...), loop) captured before to_thread.

Stub in `services/worker/src/rag_worker/jobs/generate.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.generate_schema import JobPayloadGenerate
from rag_worker.report import StageReporter, run_stage


async def generate_body(
    job: JobPayloadGenerate, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/generate.schema.json and the generate summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. rerank artifact fixture stored, payload context_source 'rerank' → done; context hits == rerank after hits (n 1..k) within budget; artifact validates
2. context_source 'retrieve' uses retrieve fused hits
3. generate.token events published with contiguous index from 0 and texts joining to the answer
4. budget: system_tokens + question_tokens counted with the bge-m3 tokenizer; used_context_tokens ≤ max_context_tokens
5. summary {'stage': 'generate', 'answer_chars': len(answer), 'citations': 1, 'chunks_included': k, 'prompt_tokens', 'completion_tokens'} from fake usage
6. LLM error → failed LLM_ERROR

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
