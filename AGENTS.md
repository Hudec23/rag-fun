# Rules for the executor (you)

You are doing ONE task in a larger system. Nobody will answer questions. Everything you need is
in the task below and in the files it lists. Work until the verify commands pass.

The runner (`scripts/autospec-run.py`) names your task in the prompt and starts a fresh session per
task. Do only that task, then stop. It re-runs the verify commands itself, reverts edits outside
`edit:`, commits and updates `.autospec/state.json` — never edit that file. On a retry the prompt
points you to `.autospec/runs/<task id>/feedback.txt` with the failed check's output: read it first.

There are two kinds of task:
- **Test-writing task** — write unit tests for behaviour that does not exist yet. Do not implement it.
- **Implementation task** — make the locked tests pass. Do not touch any test.

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

## Hard rules

1. Only create or modify files listed under `edit:`. Any other change fails the task.
   Sole exception: `.autospec/BLOCKED_REASON`.
2. Never modify a test file that existed before this task started, a contract, a plan file,
   a lockfile or a dependency manifest.
   The runner checks this; changing one fails the task automatically.
3. Never add dependencies or install packages.
4. Do not rename, move or change the signature of existing exported symbols unless the task says so.
5. Do not run `git` commands. The runner commits for you.
6. Do not start long-running servers in the foreground. Use the given verify commands.

## Method — implementation task

1. Read the task fully. Open the files under `read:`, then the tests under `locked:` — the tests
   are the definition of done.
2. Imitate the example module named in the task: same structure, naming, imports, error handling.
3. Implement the smallest change that makes the tests pass.
4. Run the `verify:` commands yourself. Read the failure, fix, repeat.
5. When all `verify:` commands pass, stop. Write a one-line summary. Do not refactor other code.
   Red tests outside `locked:` belong to unfinished tasks — ignore them.

## Method — test-writing task

1. Read the interface in **Context** (signatures, types, error codes). Tests call only that interface.
2. Write one test per item in **Test cases**, named after the case. Assert exact values, error codes
   and side effects — never just "does not throw".
3. Follow the style of the example test file named in the task (setup, fixtures, naming).
4. No real network, no wall clock, no unseeded randomness. Use the fakes/fixtures the task names.
5. **Red-first:**
   - Run the `verify:` commands — tests must compile, be collected and lint clean.
   - Run the `expect_fail:` commands — **every** test must be red because the implementation is
     missing (the stub's "not implemented" error), not because of a typo. If any single test
     passes against the stub, it is wrong; fix it before continuing.
6. Do not write any implementation code, not even a stub, unless the task lists the stub file.

## If you are stuck

**Verify commands keep failing after your own fixes:**
- After 3 fix attempts on the same error, call the `rescue` subagent.
  Give it: the task file path and task id, the failing verify-command output, what you tried.
- At most 2 rescue calls per task. If still failing after that, write the error into
  `.autospec/BLOCKED_REASON` and stop.
- Do not call `rescue` for easy errors (typos, missing imports, formatting).

**Task seems impossible** (missing type, contradictory requirement, wrong path):
Do NOT work around it by editing other files. Write the reason into `.autospec/BLOCKED_REASON`
(allowed) and stop. The planner will fix the task.
