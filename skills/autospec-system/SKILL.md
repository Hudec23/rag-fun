---
name: autospec-system
description: autospec planning step 1 — interview the user, write .autospec/plan/SYSTEM.md, .autospec/plan/executor.yaml and .autospec/plan/services/*.yaml. The only step that asks questions.
disable-model-invocation: true
---

# Planning step 1 — System spec (interactive)

You are the architect for a multi-service system that will be implemented **entirely by a weaker
local model with no human available**. Anything you leave undecided,
it will decide badly. Your job in this step is to remove every decision from its path.

## What to do

1. Read whatever the user provides (idea, notes, existing repo). If there is an existing repo,
   inspect it first: languages, frameworks, build tools, test runners, conventions. Never ask
   what the repo or the notes already answer.
   Then, in one short message, say back what you understood: what it is, who uses it, why, what
   success looks like, what is out of scope. End with the one question whose answer would most
   change the design. Do not start the checklist until the user confirms the purpose.
2. Ask which model executes phase 2 and its context window; write `.autospec/plan/executor.yaml` from
   `.autospec/kit/templates/executor.yaml`. Every later step sizes tasks from it.
3. Interview the user. Ask in batches of at most 5 questions, multiple-choice where possible,
   always with your recommended default. Keep going until every item in the checklist below is
   decided. For choices that shape the system (service split, sync vs async, datastore, auth),
   first lay out 2–3 options with their trade-offs and your recommendation; the user picks.
   If the user says "you decide", decide and record it in the decisions log as **planner's call**,
   never as something the user agreed to.
4. Write `.autospec/plan/SYSTEM.md` using `.autospec/kit/templates/SYSTEM.md`.
5. Write one `.autospec/plan/services/<name>.yaml` per service using `.autospec/kit/templates/service.yaml`.
   Every command must run inside a container (`docker compose run --rm ...`), so the runner
   only needs Docker. Pin every image tag and dependency version. `lint` includes a security
   linter and a secret scanner (e.g. semgrep or bandit / gosec / eslint-plugin-security, plus
   gitleaks), pinned in the dev container: regression runs `lint` after every task.
6. Write `docker-compose.dev.yml` at repo root: one `<name>-dev` toolchain container per service
   (workspace mounted at `/workspace`), plus databases/brokers the tests need.

## Decision checklist (all must be answered in SYSTEM.md)

- Requirements: every one as a row in §1a with an ID (`R-001`, …) and `Covered by`
  (`features`, or `skeleton` for cross-cutting ones like error shape or logging).
- Services: name, language + exact version, framework + version, responsibility (one sentence),
  what it owns (data), what it must NOT do.
- Communication: sync (REST/gRPC) vs async (queue/topic) for every service pair that talks.
- Data: which DB per service, migration tool, no shared tables between services.
- Auth between services and for users: who may call what (default deny). Secrets come from env
  vars only; list every var and mark secrets.
- Security baseline (SYSTEM.md §5a): the one module that reads env, log redaction list, input
  validation library, what error responses may reveal, CORS, security linter + secret scanner.
- Error model: one shared error shape, status code / error code mapping.
- Logging format, config loading, ID format (UUIDv7?), time format (UTC ISO-8601), money/decimals.
- Repo layout: exact directory tree to two levels.
- Per-language conventions: formatter, linter, test framework, file naming, folder structure,
  how a module is laid out (copy one tiny example into SYSTEM.md — the local model imitates examples).
- Dependency policy: the full list of allowed libraries per service. **The executor may not add
  dependencies.** Anything it will need must be in the manifest before phase 2.
- Out of scope: list what will not be built.

## Self-check before finishing

- [ ] Could someone implement any service without asking a question? If not, ask it now.
- [ ] Every library the code will need is listed with a version.
- [ ] Every requirement has an ID and a `Covered by` in §1a.
- [ ] Every service has working `setup`, `build`, `lint`, `test` commands in its yaml.
- [ ] `Open questions` section in SYSTEM.md is empty.

End by printing: the service list, and "OPEN QUESTIONS: 0" (or the list).
