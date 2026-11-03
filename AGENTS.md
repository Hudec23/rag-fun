# Project commands for the executor

Executor rules: `.autospec/kit/EXECUTOR.md` (opencode loads it through `opencode.json`).

# Commands

Run every command from the repo root. They need only Docker. Copy them verbatim; the task's
`verify:` lines are the ones that decide pass/fail.

| Service | Path | Lint + types | Tests (files relative to the service path) |
|---|---|---|---|
| api | services/api | `docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check . && uv run --frozen ruff check . && uv run --frozen mypy src'` | `docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_x.py` |
| worker | services/worker | `docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check . && uv run --frozen ruff check . && uv run --frozen mypy src'` | `docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_x.py` |
| web | services/web | `docker compose -f docker-compose.dev.yml run --rm web-dev npm run lint` and `... web-dev npx tsc -b` | `docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/x/X.test.tsx` |
| e2e | tests/e2e | – | `docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_x.py` |

Formatting: `uv run --frozen ruff format <file>` (python) / `npx prettier --write <file>` (web) inside the same
containers — run them on the files you edited before verifying.

Project facts you need in almost every task:
- Python house style: services/api/src/rag_api/services/collections.py (api), services/worker/src/rag_worker/components/chunk_annotator.py (worker). Tests: tests/integration/test_collections_get.py (api), tests/unit/test_chunk_annotator.py (worker).
- Web house style: src/pages/CollectionsPage.tsx and tests/pages/CollectionsPage.test.tsx.
- Errors: api raises `AppError(code, details=...)` (rag_api.errors); worker raises `WorkerError(code, details=...)` (rag_worker.errors). Codes: contracts/shared/errors.json.
- Time: always `ids.utcnow()` / `ids.to_iso(dt)`; ids: `ids.new_id()`.
- Generated contract models: `rag_api.contracts_gen.*`, `rag_worker.contracts_gen.*`, `services/web/src/api/schema.d.ts` — read-only.
- Tests never call real models: the worker uses `MODEL_BACKEND=fake` (rag_worker.models.fakes).
