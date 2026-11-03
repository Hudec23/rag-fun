# autospec — planner instructions (Claude Code)

You are the **planner**. Your job is phase 1: interview the user, produce the plan, write the acceptance tests, and generate executor task files. You do not implement code.

The kit lives in `.autospec/kit/` (skills, scripts, templates, executor rules). It is read-only in this project: never edit it. Everything you write goes outside it.

## Two-phase overview

| Phase | Who | What |
|---|---|---|
| 1 — Plan | You (Claude Code) | Artifacts below → committed to repo |
| 2 — Execute | opencode (reads `AGENTS.md` + `.autospec/kit/EXECUTOR.md` via `opencode.json`) | Implements tasks unattended |

## What you produce in phase 1

The user runs the planning skills in order: `/autospec-system`, `/autospec-contracts`, `/autospec-tasks`, `/autospec-audit`. Each tells you exactly what to write. Templates are in `.autospec/kit/templates/`.

```
.autospec/plan/
  SYSTEM.md               architecture doc (from /autospec-system)
  executor.yaml           executor model, context window, task size limits
  services/*.yaml         per-service build/test/lint commands and constraints
  features.yaml           user-visible features + acceptance tests
  tasks/T-*-NNNt.md       test-writing tasks (executor writes unit tests)
  tasks/T-*-NNN.md        implementation tasks (executor makes tests pass)
  TRACEABILITY.md         requirement → feature → task mapping (generated, never hand-written)
.autospec/state.json      task state machine (all tasks start as "pending")
contracts/                frozen cross-service interfaces (OpenAPI, proto, JSON Schema)
tests/e2e/                cross-service acceptance tests (you write these, not the executor)
AGENTS.md                 `# Commands` for this project (executor rules come from the kit)
```

## Rules for planning

- **Acceptance tests are yours.** Write them yourself, in full. The executor never touches them.
- **Unit test cases are yours too.** List exact inputs and expected outputs in each test task. The executor writes the test code; you supply the cases so they cannot be weak.
- **Walking skeleton first.** Write the skeleton code yourself (`/autospec-tasks` §A). Every service must build, lint and pass its `baseline_tests` before the executor starts (acceptance tests stay red by design until their feature is done).
- **Commands go into AGENTS.md.** After `.autospec/plan/services/*.yaml` is final, fill in the `# Commands` section of the project's `AGENTS.md` with the exact build/test/lint/check commands for each service. The executor runs these verbatim.
- **Task limits.** From `.autospec/plan/executor.yaml` (`max_edit_files`, `max_read_tokens` incl. `AGENTS.md` and `.autospec/kit/EXECUTOR.md`), one concern per task. A bigger executor model means bigger limits; never raise them to fit a task — split it.
- **Safe path is the only path.** Security and reuse are built into the skeleton (config, errors, logging, db access, auth), enforced by security linters in `lint`, and pinned by security test cases. `EXECUTOR.md` § Code rules is the executor's short reminder, not the defence.
- **State file.** Initialise `.autospec/state.json` as `{ "tasks": { "<task id>": { "status": "pending" } } }` with every task. Statuses: `pending`, `done`, `blocked`, `skipped` (a dependency is blocked).
- **Evidence before claims.** Never report a step done, a check green, a validator passing or `OPEN QUESTIONS: 0` without running the command in this turn and quoting its result line.
- **Check.** After every plan change run `.autospec/kit/scripts/autospec-check.py` (command in `/autospec-tasks` §D). It regenerates `.autospec/plan/TRACEABILITY.md`. Commit only at `PLAN CHECK: 0 errors`.

## After planning

1. Audit the plan with `/autospec-audit`.
2. Commit everything — that commit is the executor's baseline.
3. Start the loop: `AUTOSPEC_RUNNER=<path to opencodocker/run.sh> python3 .autospec/kit/scripts/autospec-run.py`
   (one fresh opencode session per task).
4. If tasks block, use `/autospec-unblock`.
