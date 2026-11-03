---
id: T-api-014
kind: impl
feature: F-stage-flow
title: build_payload for the ingest stages
service: api
depends_on:
- T-api-014t
- T-api-012
- T-api-013
edit:
- services/api/src/rag_api/services/job_payloads.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_job_payloads.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/job_payloads.py && uv run --frozen ruff check src/rag_api/services/job_payloads.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_job_payloads.py
max_attempts: 3
---

## Goal
Implement: build_payload for the ingest stages. The tests written by T-api-014t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Insert stage rows with status done and artifact_key set to simulate active upstream stages; use add_settings + add_collection. Stage params for those rows: copy `params` from the contract fixtures, e.g. `json.loads((FIXTURES / 'jobs__chunk.json').read_text())['params']` (`from tests.conftest import FIXTURES`; one file per stage: jobs__parse.json, jobs__chunk.json, jobs__embed.json, jobs__store.json, jobs__transform.json, jobs__retrieve.json, jobs__rerank.json, jobs__generate.json). Check payloads only with `errors(payload, 'jobs/<stage>.schema.json') == []`. Do not open anything under contracts/: the fixtures and this task contain everything you need.

Stub in `services/api/src/rag_api/services/job_payloads.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Build worker job payloads (contracts/jobs/{stage}.schema.json) for a freshly queued stage run."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import IngestRunRow, QueryRunRow, StageRunRow


def envelope(row: StageRunRow) -> dict[str, Any]:
    """{'stage_run_id', 'run_id', 'run_kind', 'stage', 'version'} from the row."""
    raise NotImplementedError("not implemented")

async def file_block(session: AsyncSession, run: IngestRunRow) -> dict[str, Any]:
    """jobs 'file' object: file_id, batch_id, batch_name, filename, mime, s3_key,
    tags = sorted(set(file.tags) | set(batch.tags))."""
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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
