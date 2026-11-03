---
name: autospec-tasks
description: autospec planning step 3 — walking skeleton, acceptance tests, test/impl task pairs, plan check. Run after autospec-contracts.
disable-model-invocation: true
---

# Planning step 3 — Skeleton, stubs, acceptance tests, task pairs

Read `.autospec/plan/SYSTEM.md`, `.autospec/plan/services/*`, `contracts/`. Produce the complete, ordered work
breakdown for an executor that is **much weaker than you** (`.autospec/plan/executor.yaml`): fresh
session per task, no memory of previous tasks, cannot ask questions, cannot add dependencies.

Division of labour for tests (keeps your planning cost low):
- **You write**: acceptance tests per feature, contract tests, test fakes/fixtures, one example
  test file per service, and the *list of test cases* inside each test task.
- **The executor writes**: the unit tests themselves, in a separate test task that runs before the
  implementation task. Once committed, those tests are locked for every later task.

## A. Walking skeleton (you write this code yourself, now)

For every service, commit a minimal skeleton so phase 2 starts from a green build:
- manifest with ALL dependencies from SYSTEM.md installed and locked,
- entrypoint that starts, config loading, health endpoint, logging, error shape,
- every row of SYSTEM.md §5a (Security baseline), so the safe way is the only way the executor
  sees: config module, redacting logger, error handler that hides internals, parameterized db
  helpers, default-deny auth,
- one example module and **one example test file** in the house style (the executor copies both),
- test fakes/fixtures the unit tests will need (fake repo, fake bus, fixed clock, seeded ids),
- **interface stubs** for every module a task will implement: real signatures and types, body
  throws "not implemented". This lets the executor's tests compile and fail for the right reason.
- generated code from contracts (step 2), committed,
- the service's `setup`, `build`, `lint` commands and its `baseline_tests` actually pass,
- `.gitignore` covers every build/test artifact of every language (`node_modules/`, `dist/`,
  `__pycache__/`, `target/`, `bin/`, coverage, caches) plus `.autospec/runs/`,
  `.autospec/BLOCKED_REASON` and `.autospec/STOP` (`.autospec/state.json` is committed).

Once for the whole system:
- a pinned `Dockerfile` per service and a root `docker-compose.yml` that starts the system,
- `.autospec/plan/services/integration.yaml` whose commands run `tests/e2e/` against that compose file.
- every infra container the tests use (database, cache, queue, object store, vector store, in
  the dev/test compose too) has a `healthcheck`, and everything that needs it waits with
  `depends_on: { condition: service_healthy }` — never `service_started`, which hides a container
  that crashes on boot. Mind images that run as non-root: a `tmpfs` or volume must be writable by
  that uid (e.g. `tmpfs: ["/data:uid=10001,gid=10001"]`).
- one baseline smoke test per service that really talks to each of those containers (write and
  read back one row / key / object / point), so broken test infra fails before phase 2, not in
  the first task that needs it.

Run them. Do not continue until every service is green.

## B. Features + acceptance tests (you write these, now)

1. List every user-visible capability in `.autospec/plan/features.yaml` (`.autospec/kit/templates/features.yaml`).
2. For each feature, write 1–2 acceptance tests through the public interface (HTTP call, CLI run,
   event in → event/DB out). Cover the main path and the most important failure from the contract.
   Cross-service features go in `tests/e2e/` against `docker compose up`.
3. Write contract tests: consumer side against the contract file, provider side against the
   running service. List them as acceptance tests of the matching feature.
4. Run them all: they must compile and fail because the stubs throw — not because of a typo.

These are the independent definition of "done". They must not be written by the executor.

## C. Task files — `.autospec/plan/tasks/T-<service>-<NNN>[t].md`

For each unit of behaviour, write a **pair**:

| | Test task `T-api-007t` (`.autospec/kit/templates/task-test.md`) | Impl task `T-api-007` (`.autospec/kit/templates/task-impl.md`) |
|---|---|---|
| kind | `test` | `impl` |
| edit | the new test file(s) only | the stub/source files only — never tests |
| body | Goal, Context (interface + fakes), **Test cases** (numbered, exact inputs → exact expected results), Do not, Done when | Goal, Context, Steps, Do not, Done when |
| verify | tests compile, are collected, lint clean | the unit tests (+ acceptance tests on the feature's last task) pass |
| expect_fail | running the new tests fails — every test red, none pass | – |
| depends_on | what the interface needs | its test task + anything else |
| locked | – | the test task's file(s); acceptance tests on the feature's last task |

Regression after every task = build + lint + `baseline_tests` + the locked tests of all `done`
tasks (via `test_files`). Never the full `test` suite: acceptance tests of unfinished features
are red by design. The full suite is expected green only when every task is done.

Before the cases of each feature, list the inputs a real user or attacker would send that the
contract is silent on (the likely failures no test covers yet); each one becomes a case in the
task that owns that code.

Every task's **Context** names what it consumes (exact signatures from earlier tasks) and what it
produces (exact exported names and types later tasks rely on). Later tasks copy those signatures
verbatim; a mismatch is a plan bug, not the executor's.

Writing **Test cases** is the part that matters: one line per case, concrete values, exact
expected status/error code/return value. Include happy path, every error the contract defines,
and edges (empty, max length, duplicate, zero, negative, unicode). For anything reachable from
outside (handler, consumer, CLI) also: unauthenticated → 401, someone else's resource → 403/404,
malformed input → 400, and an internal failure whose response contains no internal detail. This is cheap for you to write
and is what stops the executor from writing weak tests.

Trivial glue (wiring a route, config, a DTO) may be an impl task with no test task, as long as it
is locked to an acceptance or existing test that exercises it.

Hard limits:
- `edit:` at most `max_edit_files` (`.autospec/plan/executor.yaml`) files. Every file the task creates or changes is listed. Nothing else.
- Required reading (AGENTS.md + EXECUTOR.md + task file + `read:` + `locked:` files) ≤ `max_read_tokens`. Paste the exact
  snippet (signature, type, schema fragment) into Context instead of listing a large file.
- No two tasks that could run in either order edit the same file — add `depends_on`.
- One concern per task. If you write "and" in the title, split it.
- Order: data layer → domain logic → handlers/consumers → wiring →
  feature acceptance → cross-service e2e (service `integration`).

## D. Check

Initialise `.autospec/state.json` (every task `pending`), then run the checker from the repo root:

```sh
docker run --rm -v "$PWD":/w -w /w python:3.12.7-slim sh -c \
  'pip install -q --root-user-action=ignore --disable-pip-version-check pyyaml==6.0.2 \
   && python .autospec/kit/scripts/autospec-check.py'
```

It writes `.autospec/plan/TRACEABILITY.md` (never edit that by hand) and fails on: a requirement no feature
covers, a feature without tasks or acceptance tests, a feature whose last task doesn't lock and
run its acceptance tests, test/impl pairs that don't match, too many edit files or too much reading for
`.autospec/plan/executor.yaml`, a file read before any task writes it, unordered tasks editing the same file,
dependency cycles, a state file out of sync, a service `regression` that can't run, and any
plan file `autospec-run.py` would read differently than YAML does (keep values on one line). Fix and re-run until `PLAN CHECK: 0 errors`.

It cannot judge content, so also check:
- [ ] Every test task has ≥ 3 concrete test cases unless the unit is genuinely trivial.

Print the checker's output (task count per service, critical path).
