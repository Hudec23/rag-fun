# autospec — AI-agent planning kit

A set of structured prompts and templates for designing a multi-service system so a weak local model can implement it unattended. You bring the runner (e.g. [opencode-docker](https://github.com/Hudec23/opencode-docker)).

```
planning/          Claude prompts — run in order during phase 1
  01-system.md     Interview → plan/SYSTEM.md + plan/services/*.yaml
  02-contracts.md  Freeze every cross-service interface in contracts/
  03-tasks.md      Walking skeleton, acceptance tests, task pairs
  04-audit.md      Claude audits the plan as the weak executor
  05-unblock.md    Diagnose and fix blocked tasks after a run

templates/         Copy these into plan/ when Claude writes output
  SYSTEM.md        Architecture doc template
  service.yaml     Per-service build/test config
  features.yaml    Feature → acceptance test mapping
  task-impl.md     Implementation task template
  task-test.md     Test-writing task template

scripts/
  autospec-check.py  Plan checker; generates plan/TRACEABILITY.md

CLAUDE.md                      Loaded by Claude Code — planner instructions (phase 1)
AGENTS.md                      Loaded by opencode — executor rules (phase 2)
.opencode/agents/rescue.md     Stronger-model subagent opencode spawns when executor is stuck
```

## How to use

### Phase 1 — plan with Claude

Run each `planning/` prompt in Claude Code, in order (step 3 builds and runs code in Docker, so claude.ai alone is not enough). Each ends with a self-check; don't move on until Claude reports zero open questions.

1. `planning/01-system.md` — Claude interviews you, writes `plan/SYSTEM.md` and `plan/services/*.yaml`.  
   **This is the only step that asks you questions.**
2. `planning/02-contracts.md` — freezes every cross-service interface in `contracts/`.
3. `planning/03-tasks.md` — walking skeleton with stubs, acceptance tests, and test/impl task pairs.
4. `planning/04-audit.md` — Claude audits the plan as if it were the weak executor.
5. Commit everything. That commit is the baseline the runner works from.

### Phase 2 — unattended build

`scripts/autospec-run.py` drives the build. It runs on the host (python3 stdlib, git, Docker) and, for each pending task whose dependencies are done:

1. starts a fresh opencode session for that one task through your sandbox runner (default `~/Dev/opencode-docker/run.sh --keep -- run "<task prompt>"`; override with `--runner` or `$AUTOSPEC_RUNNER`),
2. reverts any change outside the task's `edit:` list,
3. runs the task's `verify:` / `expect_fail:` commands itself — the agent never grades its own work,
4. commits on green and marks the task `done`; otherwise retries with the failing output as feedback, then marks it `blocked` (dependents become `skipped`).

```sh
python3 scripts/autospec-run.py --dry-run          # show order and status
python3 scripts/autospec-run.py --only T-api-001t  # one task
python3 scripts/autospec-run.py                    # loop until nothing is runnable
```

Run it from a terminal (opencode-docker uses `docker run -it`). Logs land in `.autospec/runs/<task>/`. opencode picks up `AGENTS.md` from the project root automatically. Blocked tasks: `planning/05-unblock.md`.

## What each rule produces

| Rule | Output |
|---|---|
| Acceptance tests by Claude | Independent definition of done; executor can't grade its own understanding |
| Unit tests in a separate earlier task | Implementation can't bend tests to fit |
| Must-fail check | Catches empty, skipped or always-true tests |
| Fresh session per task | No context bleed across tasks |
| ≤3 files to edit, ≤15K tokens to read | Leaves headroom for reasoning and tool output |
| Contracts frozen first | Services in different languages can be built in any order |
| Each service tested in its own container | Runner needs only Docker, no language toolchains |

## Prior art

Most ideas here are established practice; the assembly and file formats are new.

| Piece | Origin |
|---|---|
| Spec → plan → tasks phases | Spec-driven development (GitHub Spec Kit, OpenSpec, AWS Kiro) |
| Fresh session per task, commit on green, loop until done | "Ralph" loop pattern (community convention) |
| Acceptance tests outside, unit tests inside | Double-loop TDD / ATDD — Freeman & Pryce, *Growing Object-Oriented Software* |
| Tests must fail before implementation | TDD red-green-refactor — Kent Beck |
| Tests written by someone other than the implementer | Separation of duties; holdout test sets in SWE-bench and dark-factory CI |
| Contracts frozen first (OpenAPI, proto, JSON Schema) | API-first / contract-first design; consumer-driven contract testing (Pact) |
| Walking skeleton before features | Alistair Cockburn |
| Small, independent, testable tasks | INVEST user stories; trunk-based development |
| Pinned deps, per-service build containers | Hermetic / reproducible builds |
| `git reset` on failure, CI-style gates | Standard CI practice |

What is new: the file formats (`plan/services/*.yaml`, task frontmatter, `features.yaml`), the specific token and file-count limits (heuristics for a 64K window — adjust after your first real run), and the test-task / impl-task split with auto-locking applied to a weak local executor.
