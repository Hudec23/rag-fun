# Rules for the executor (you)

You are doing ONE task in a larger system. Nobody will answer questions. Everything you need is
in the task below and in the files it lists. Work until the verify commands pass.

The runner (`.autospec/kit/scripts/autospec-run.py`) names your task in the prompt and starts a fresh session per
task. Do only that task, then stop. It re-runs the verify commands itself, reverts edits outside
`edit:`, commits and updates `.autospec/state.json` — never edit that file. On a retry the prompt
points you to `.autospec/runs/<task id>/feedback.txt` with the failed check's output: read it first.

There are two kinds of task:
- **Test-writing task** — write unit tests for behaviour that does not exist yet. Do not implement it.
- **Implementation task** — make the locked tests pass. Do not touch any test.

The build/test/lint commands for this project are in `AGENTS.md` § Commands.

## Hard rules

1. Only create or modify files listed under `edit:`. Any other change fails the task.
   Sole exception: `.autospec/BLOCKED_REASON`.
2. Never modify a test file that existed before this task started, a contract, a plan file,
   a lockfile, a dependency manifest or anything under `.autospec/`.
   The runner checks this; changing one fails the task automatically.
3. Never add dependencies or install packages.
4. Do not rename, move or change the signature of existing exported symbols unless the task says so.
5. Do not run `git` commands. The runner commits for you.
6. Do not start long-running servers in the foreground. Use the given verify commands.

## Code rules

- **Reuse, don't copy.** If a helper in the repo already does it (config, errors, logging, db,
  validation, clock, ids), call it. Never paste the same logic twice.
- **Smallest code that passes.** No options, parameters or abstractions the task doesn't ask for.
  No dead code, commented-out code, TODOs or debug prints left behind.
- **Secrets and config:** read env vars only through the config module. Never hard-code a secret,
  token, password or credentialed URL. Never log, print or return them.
- **Errors:** use the shared error helper. Responses carry `code` + `message` only — never a stack
  trace, SQL, file path or internal message. No empty `catch`, no catch-all that reports success.
- **Untrusted input:** validate at the boundary with the schema the task names. Never build SQL,
  shell commands, HTML or file paths by string concatenation: use parameters, argument arrays,
  the escaping helper.
- **Never loosen security** to make a test pass: no skipped auth or permission checks, no disabled
  TLS verification, no `eval`, no wildcard CORS. If a test seems to need it, write
  `.autospec/BLOCKED_REASON` and stop.
- **Determinism:** time, ids and randomness come from the injected clock / id generator.

## Method — implementation task

1. Read the task fully. Open the files under `read:`, then the tests under `locked:` — the tests
   are the definition of done.
2. Imitate the example module named in the task: same structure, naming, imports, error handling.
3. Implement the smallest change that makes the tests pass.
4. Run the `verify:` commands yourself. Read the failure, fix, repeat.
5. When all `verify:` commands pass, stop. Write a one-line summary. Do not refactor other code.
   Red tests outside `locked:` belong to unfinished tasks — ignore them. The runner also runs the
   service regression (build, lint, tests that were green before); breaking any of them fails the task.

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
