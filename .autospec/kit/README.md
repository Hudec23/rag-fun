# autospec — AI-agent planning kit

Plan a multi-service system with Claude Code, then let a weak local model build it unattended,
one small task at a time. A Python loop, not the model, decides when a task is done.

You bring the sandbox runner: [opencodocker](https://github.com/Hudec23/opencodocker)
(opencode in Docker with Docker-in-Docker), or any wrapper with the same interface.

## Quick start

The kit and your plan live in `.autospec/`. The project root holds only your app, plus three
small stub files the tools need.

```sh
# 1. In your project (an existing or new git repo with at least one commit), add the kit:
git subtree add --prefix .autospec/kit https://github.com/Hudec23/autospec-kit main --squash

# 2. Wire it in (creates small stub files, never overwrites yours):
sh .autospec/kit/init.sh
git add -A && git commit -m "Add autospec kit"

# 3. Plan: open Claude Code in the project root and run, in order:
#    /autospec-system  /autospec-contracts  /autospec-tasks  /autospec-audit
#    then commit everything.

# 4. Build: run the loop (from the project root, in a terminal):
export AUTOSPEC_RUNNER=~/path/to/opencodocker/run.sh
python3 .autospec/kit/scripts/autospec-run.py
```

New empty project? `git init && git commit --allow-empty -m init` first. Subtree needs a commit.

### Update the kit later

```sh
git subtree pull --prefix .autospec/kit https://github.com/Hudec23/autospec-kit main --squash
sh .autospec/kit/init.sh   # links new skills, if any
git add -A && git commit -m "Update autospec kit"
```

Only `.autospec/kit/` changes. Your plan, state, code and stub files are outside it, so a pull
never conflicts with them. **Never edit files inside `.autospec/kit/` in a project.** Change the
kit in this repo and pull instead, or the next pull can hit a merge conflict.

## What lives where

```
your-project/
├── .autospec/
│   ├── kit/              THE KIT. Read-only in your project, updated by subtree pull
│   ├── plan/             yours: SYSTEM.md, executor.yaml, services/, features.yaml, tasks/T-*.md
│   ├── state.json        task status (written by the planner, then the runner)
│   ├── REPORT.md         last run's report (written by the runner)
│   └── runs/             per-task logs (gitignored)
├── contracts/            frozen interfaces between services
├── tests/e2e/            acceptance tests written by the planner
├── services/...          the code
├── CLAUDE.md             stub: imports .autospec/kit/PLANNER.md, plus your own notes
├── AGENTS.md             stub: this project's # Commands (the planner fills them in)
├── opencode.json         stub: loads the kit's EXECUTOR.md, hides planner skills, rescue agent
└── .claude/skills/autospec-*   symlinks into the kit (the planning steps)
```

How each tool finds the kit:

| Tool | Reads | Kit content reaches it via |
|---|---|---|
| Claude Code (planner) | `CLAUDE.md`, `.claude/skills/` | `@.autospec/kit/PLANNER.md` import; skill symlinks |
| opencode (executor) | `AGENTS.md`, `opencode.json` | `"instructions": [".autospec/kit/EXECUTOR.md"]` |
| Runner, checker | — | run as `python3 .autospec/kit/scripts/...` from the project root |

`AGENTS.md` must exist: without it opencode falls back to `CLAUDE.md`, i.e. the planner's
instructions. `init.sh` always creates it.

### The kit itself

```
PLANNER.md             planner rules (Claude Code, phase 1)
EXECUTOR.md            executor rules (opencode, phase 2)
init.sh                wires the kit into a project
skills/autospec-*      planning steps, run in order as slash commands:
  autospec-system        interview → .autospec/plan/SYSTEM.md, .autospec/plan/executor.yaml, .autospec/plan/services/*.yaml
  autospec-contracts     freeze every cross-service interface in contracts/
  autospec-tasks         walking skeleton, acceptance tests, test/impl task pairs
  autospec-audit         audit every task as the weak executor
  autospec-unblock       diagnose and fix blocked tasks after a run
templates/             SYSTEM.md, executor.yaml, service.yaml, features.yaml, task-*.md,
                       and the AGENTS.md / opencode.json stubs init.sh copies
scripts/
  autospec-check.py    plan checker; generates .autospec/plan/TRACEABILITY.md
  autospec-run.py      phase 2 task loop (python3 stdlib only)
  autospec_yaml.py     YAML subset reader shared by both
opencode/rescue.md     prompt of the stronger-model subagent the executor calls when stuck
```

## Phase 1 — plan with Claude Code

Run each skill in order. Step 3 builds and runs code in Docker, so Claude Code is needed, not
just claude.ai. Each step ends with a self-check; don't move on until it reports zero open
questions.

1. `/autospec-system` — interviews you, writes `.autospec/plan/SYSTEM.md`, `.autospec/plan/executor.yaml` (which model
   executes, its context window, task size limits) and `.autospec/plan/services/*.yaml`.
   **The only step that asks you questions.**
2. `/autospec-contracts` — freezes every cross-service interface in `contracts/`.
3. `/autospec-tasks` — walking skeleton with stubs and security baseline, acceptance tests,
   test/impl task pairs, plan check (`PLAN CHECK: 0 errors`).
4. `/autospec-audit` — audits every task as if it were the weak executor.
5. Commit everything. That commit is the baseline the runner works from.

## Phase 2 — unattended build

`.autospec/kit/scripts/autospec-run.py` runs on the host (python3, git, Docker). For each pending
task whose dependencies are done it:

1. starts a fresh opencode session for that one task through your runner, called as
   `<runner> --project <repo> --keep -- run "<task prompt>"` (the interface of opencodocker's `run.sh`),
2. reverts any change outside the task's `edit:` list,
3. runs the gate itself, inside the agent's dind container (`oc-dind-<project>`, override with
   `$AUTOSPEC_DIND`): `verify:` must pass, `expect_fail:` must fail, then the service's
   `regression` (build, lint, `baseline_tests`, tests of done tasks) must pass,
4. commits on green and marks the task `done`; otherwise retries with the failing command's output
   as feedback, then marks it `blocked` (dependents become `skipped`).

```sh
export AUTOSPEC_RUNNER=~/path/to/opencodocker/run.sh
python3 .autospec/kit/scripts/autospec-run.py --dry-run          # show order and status
python3 .autospec/kit/scripts/autospec-run.py --only T-api-001t  # one task
python3 .autospec/kit/scripts/autospec-run.py --max-tasks 3      # short trial
python3 .autospec/kit/scripts/autospec-run.py                    # loop until nothing is runnable
```

- Start from a clean working tree (commit or stash first).
- Run in a terminal (`run.sh` uses `docker run -it`).
- Ctrl-C stops now and leaves the current task pending; `touch .autospec/STOP` stops after the
  current task.
- At the end the runner commits `.autospec/REPORT.md`. If tasks are blocked, open Claude Code and
  run `/autospec-unblock`.

## What each rule produces

| Rule | Output |
|---|---|
| Acceptance tests by Claude | Independent definition of done; executor can't grade its own understanding |
| Unit tests in a separate earlier task | Implementation can't bend tests to fit |
| Must-fail check | Catches empty, skipped or always-true tests |
| Regression after every task | A task can't silently break an earlier one |
| Fresh session per task | No context bleed across tasks |
| Edit-file and read limits from `.autospec/plan/executor.yaml` | Leaves headroom for reasoning and tool output |
| Security baseline in the skeleton, security linter in `lint` | The safe way is the only way the executor sees |
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

What is new: the file formats (`.autospec/plan/services/*.yaml`, task frontmatter, `features.yaml`), the
token and file-count limits (`.autospec/plan/executor.yaml`; defaults are heuristics for a 64K window —
adjust after your first real run), and the test-task / impl-task split with auto-locking applied
to a weak local executor.
