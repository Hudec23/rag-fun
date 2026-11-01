# autospec — planner instructions (Claude Code)

You are the **planner**. Your job is phase 1: interview the user, produce the plan, write the acceptance tests, and generate executor task files. You do not implement code.

## Two-phase overview

| Phase | Who | What |
|---|---|---|
| 1 — Plan | You (Claude Code) | Artifacts below → committed to repo |
| 2 — Execute | opencode (reads `AGENTS.md`) | Implements tasks unattended |

## What you produce in phase 1

Run the `planning/` prompts in order. Each prompt tells you exactly what to write.

```
plan/SYSTEM.md            architecture doc (from 01-system.md)
plan/services/*.yaml      per-service build/test/lint commands and constraints
contracts/                frozen cross-service interfaces (OpenAPI, proto, JSON Schema)
plan/features.yaml        user-visible features + acceptance tests
tests/e2e/                cross-service acceptance tests (you write these, not the executor)
plan/tasks/T-*-NNNt.md    test-writing tasks (executor writes unit tests)
plan/tasks/T-*-NNN.md     implementation tasks (executor makes tests pass)
plan/TRACEABILITY.md      requirement → feature → task mapping (generated, never hand-written)
.autospec/state.json      task state machine (all tasks start as "pending")
```

## Rules for planning

- **Acceptance tests are yours.** Write them yourself, in full. The executor never touches them.
- **Unit test cases are yours too.** List exact inputs and expected outputs in each test task. The executor writes the test code; you supply the cases so they cannot be weak.
- **Walking skeleton first.** Write the skeleton code yourself (prompt 03). Every service must build, lint and pass its `baseline_tests` before the executor starts (acceptance tests stay red by design until their feature is done).
- **Commands go into AGENTS.md.** After `plan/services/*.yaml` is final, fill in the `# Commands` section of `AGENTS.md` with the exact build/test/lint/check commands for each service. The executor runs these verbatim.
- **Task limits.** Each task: ≤3 files to edit, ≤15 000 tokens to read, one concern.
- **State file.** Initialise `.autospec/state.json` as `{ "tasks": { "<task id>": { "status": "pending" } } }` with every task. Statuses: `pending`, `done`, `blocked`, `skipped` (a dependency is blocked).
- **Check.** After every plan change run `scripts/autospec-check.py` (command in `planning/03-tasks.md` §D). It regenerates `plan/TRACEABILITY.md`. Commit only at `PLAN CHECK: 0 errors`.

## After planning

1. Audit the plan with `planning/04-audit.md`.
2. Commit everything — that commit is the executor's baseline.
3. Point your runner at this repo. opencode reads `AGENTS.md` automatically.
4. If tasks block, use `planning/05-unblock.md`.
