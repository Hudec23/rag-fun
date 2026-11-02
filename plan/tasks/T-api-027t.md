---
id: T-api-027t
kind: test
feature: F-stage-flow
title: 'Write tests: build_payload for the query stages'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_job_payloads_query.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_job_payloads_query.py && uv run --frozen ruff check tests/integration/test_job_payloads_query.py && uv run --frozen pytest -q --collect-only tests/integration/test_job_payloads_query.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_job_payloads_query.py
max_attempts: 3
---

## Goal
Write unit tests for: build_payload for the query stages. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-027 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Insert stage rows with status done and artifact_key set to simulate active upstream stages; use add_settings + add_collection. Stage params for those rows: copy `params` from the contract fixtures, e.g. `json.loads((FIXTURES / 'jobs__chunk.json').read_text())['params']` (`from tests.conftest import FIXTURES`; one file per stage: jobs__parse.json, jobs__chunk.json, jobs__embed.json, jobs__store.json, jobs__transform.json, jobs__retrieve.json, jobs__rerank.json, jobs__generate.json). Check payloads only with `errors(payload, 'jobs/<stage>.schema.json') == []`. Do not open anything under contracts/: the fixtures and this task contain everything you need. Create a query run (QueryRunRow) for these stages. The ingest stages are already implemented (T-api-014); keep their tests green.

Stub in `services/api/src/rag_api/services/job_payloads.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Build worker job payloads (contracts/jobs/{stage}.schema.json) for a freshly queued stage run."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import IngestRunRow, QueryRunRow, StageRunRow


def envelope(row: StageRunRow) -> dict[str, Any]:
    """{'stage_run_id', 'run_id', 'run_kind', 'stage', 'version'} from the row."""
    raise NotImplementedError("not implemented")

async def build_payload(
    session: AsyncSession,
    run: IngestRunRow | QueryRunRow,
    row: StageRunRow,
    latest: dict[str, StageRunRow],
) -> dict[str, Any]:
    """envelope + params + stage specific fields. `latest` = rows BEFORE `row` was inserted.
    parse: file. chunk: file, parse_artifact_key (active parse), dense (collection dense model config,
    ollama_url from settings). embed: chunk_artifact_key, collection (CollectionRef).
    store: file, chunk_artifact_key, embed_artifact_key, collection, parse_strategy, chunk_strategy
    (from the active parse/chunk rows' params). transform: question, chat (app_settings.resolve_chat).
    retrieve: question, transform_artifact_key (active transform or None), collection.
    rerank: question, retrieve_artifact_key, model (app_settings reranker_model).
    generate: question, context_artifact_key + context_source ('rerank' if rerank active else
    'retrieve'), chat. The result must validate against contracts/jobs/{stage}.schema.json."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. transform payload validates (errors(payload, 'jobs/transform.schema.json') == []) and payload['chat'] == app_settings.resolve_chat(settings row)
2. generate payload 'chat' == app_settings.resolve_chat; context_source 'rerank' with the rerank row's artifact_key when rerank is active
3. generate payload context_source 'retrieve' with the retrieve row's artifact_key when rerank never ran
4. retrieve payload transform_artifact_key is None when transform never ran; validates against jobs/retrieve.schema.json
5. rerank payload model == settings reranker_model; validates against jobs/rerank.schema.json

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
