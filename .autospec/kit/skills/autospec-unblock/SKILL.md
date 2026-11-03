---
name: autospec-unblock
description: autospec after a run — diagnose blocked tasks from .autospec/REPORT.md and logs, fix the plan, requeue.
disable-model-invocation: true
---

# After a run — unblock

Input: `.autospec/REPORT.md` (committed by the runner), the task file of each blocked task, and its
logs in `.autospec/runs/<task>/` (`attempt-N.log` = agent session, `attempt-N.checks.log` = runner
checks; the last attempt is usually enough). Logs exist only on the machine that ran the loop.

For each blocked task, find the root cause before changing anything:
1. Read the failing check's full output in the last attempt's `.checks.log`, not just the reason line.
2. Reproduce it: run the failing verify command yourself and see the same failure.
3. Compare with a done task of the same kind and service: what does that one have that this lacks
   (context, fixture, stub, import)?
4. State one hypothesis and the evidence for it. Fix that cause in the plan, not the symptom.
   If the same task was already fixed once and blocked again, question its decomposition or
   interface before patching its text a second time.

Then classify it:
- **plan defect** — missing context, vague step, wrong path, missing dependency/fixture → fix the task file;
- **test defect** — test is wrong or over-specified → fix the test (this is the only time tests change);
- **too big** — split into smaller tasks with new ids, keep dependents' `depends_on` correct;
- **too hard for the executor** — implement it yourself and mark it `status: done` in
  `.autospec/state.json`, or leave for a human.

Then list which `skipped` tasks will run again once these are fixed.

Re-run the checker (autospec-tasks §D); split tasks need new entries in `.autospec/state.json`.
Commit the fixes, set blocked/skipped entries in `.autospec/state.json` back to `"status": "pending"`, and start the loop again (`python3 .autospec/kit/scripts/autospec-run.py`).
