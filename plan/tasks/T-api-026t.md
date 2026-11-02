---
id: T-api-026t
kind: test
feature: F-one-command
title: 'Write tests: bootstrap migrations + seed'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_bootstrap_seed.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_bootstrap_seed.py && uv run --frozen ruff check tests/integration/test_bootstrap_seed.py && uv run --frozen pytest -q --collect-only tests/integration/test_bootstrap_seed.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_bootstrap_seed.py
max_attempts: 3
---

## Goal
Write unit tests for: bootstrap migrations + seed. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-026 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). For run_migrations create a throwaway database via an AUTOCOMMIT connection on the postgres-test server and drop it afterwards.

Stub in `services/api/src/rag_api/services/bootstrap.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Idempotent startup bootstrap (SYSTEM.md §5 Bootstrap)."""
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.config import Settings
from rag_api.s3 import ObjectStore


def run_migrations(database_url: str) -> None:
    """alembic upgrade head programmatically: cfg = alembic.config.Config();
    cfg.set_main_option('script_location', str(Path(__file__).resolve().parents[3] / 'alembic'))
    (= services/api/alembic in dev, /app/alembic in the runtime image); cfg.attributes['database_url']
    = database_url; alembic.command.upgrade(cfg, 'head'). Synchronous: alembic/env.py calls
    asyncio.run, so callers inside an event loop must use asyncio.to_thread(run_migrations, url)."""
    raise NotImplementedError("not implemented")

async def seed(session: AsyncSession, store: ObjectStore, settings: Settings) -> None:
    """1. store.ensure_bucket(uploads) and (artifacts). 2. If no settings row 'app': insert
    catalog.DEFAULT_SETTINGS with ollama.url = settings.ollama_url_default. 3. If no collection exists:
    create catalog.DEFAULT_COLLECTION via collections.create_collection. Commit. Running twice changes
    nothing."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. seed on an empty DB → buckets 'uploads' and 'artifacts' in store.buckets, settings row 'app' with ollama.url == settings.ollama_url_default and chat_model 'qwen3:8b', exactly one collection named 'default' (bge-m3, Qdrant/bm25, 1024)
2. seed twice → still one settings row and one collection; existing settings values are not overwritten
3. seed when another collection already exists → no 'default' created
4. run_migrations(DATABASE_URL of a fresh database 'ragfun_mig_<hex>' created with CREATE DATABASE), called as `await asyncio.to_thread(run_migrations, url)`, creates all 8 tables (query information_schema.tables); running it twice is a no-op

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
