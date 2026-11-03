---
id: T-api-026
kind: impl
feature: F-one-command
title: bootstrap migrations + seed
service: api
depends_on:
- T-api-026t
- T-api-003
- T-api-011
- T-api-023
edit:
- services/api/src/rag_api/services/bootstrap.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_bootstrap_seed.py
- tests/e2e/test_bootstrap.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/bootstrap.py && uv run --frozen ruff check src/rag_api/services/bootstrap.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_bootstrap_seed.py
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_bootstrap.py
max_attempts: 3
---

## Goal
Implement: bootstrap migrations + seed. The tests written by T-api-026t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
