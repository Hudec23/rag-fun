A smaller local model got stuck on a task in this repo. You get the task file and task id,
the failing verify-command output, and what was tried.

1. Read the task file, `autospec/AGENTS.md` (especially `# Commands`), and the files shown by
   `git diff` and `git status`.
2. Find the root cause. Fix it with the smallest change, only in files under the task's `edit:`.
   Never touch `locked:` tests, contracts, plan files, lockfiles or manifests.
3. Run the verify commands until they pass.
4. Do not commit and do not start other tasks.

Finish with one short paragraph: what was wrong and what you changed.
