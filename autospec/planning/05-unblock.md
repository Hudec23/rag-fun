# After a run — unblock

Give Claude: `REPORT.md`, and for each blocked task `autospec/.autospec/runs/<task>/attempt-*.log`
(last attempt is usually enough) plus the task file.

Prompt:

> These tasks were blocked by the local executor. For each one, diagnose the root cause from the
> logs and classify it:
> - **plan defect** — missing context, vague step, wrong path, missing dependency/fixture → fix the task file;
> - **test defect** — test is wrong or over-specified → fix the test (this is the only time tests change);
> - **too big** — split into smaller tasks with new ids, keep dependents' `depends_on` correct;
> - **too hard for the executor** — implement it yourself and mark it `status: done` in
>   `autospec/.autospec/state.json`, or leave for a human.
>
> Then list which `skipped` tasks will run again once these are fixed.

Re-run the checker (step 3D); split tasks need new entries in `autospec/.autospec/state.json`.
Commit the fixes, set blocked/skipped entries in `autospec/.autospec/state.json` back to `"status": "pending"`, and start the runner again.
