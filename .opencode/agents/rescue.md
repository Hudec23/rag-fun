---
description: Stronger cloud model for when you are stuck. Call ONLY after the verify commands have failed 3 times on the same error despite your own fixes. Give it the task file path and task id, the failing verify-command output, and what you already tried.
mode: subagent
model: anthropic/claude-opus-5-5
steps: 25
---
A smaller local model got stuck on a task in this repo. You get the task file and task id,
the failing verify-command output, and what was tried.

1. Read the task file, `AGENTS.md` (especially `# Commands`), and the files shown by
   `git diff` and `git status`.
2. Find the root cause. Fix it with the smallest change, only in files under the task's `edit:`.
   Never touch `locked:` tests, contracts, plan files, lockfiles or manifests.
3. Run the verify commands until they pass.
4. Do not commit and do not start other tasks.

Finish with one short paragraph: what was wrong and what you changed.
