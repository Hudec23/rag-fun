#!/usr/bin/env python3
"""autospec task loop (phase 2). Runs on the host; needs python3 (stdlib only), git and Docker.

For each pending task in .autospec/state.json whose depends_on are all done:
  1. start a fresh opencode session for that one task (via the opencode-docker run.sh),
  2. check that only files under the task's `edit:` changed (other changes are reverted),
  3. run the task's `verify:` (must pass) and `expect_fail:` (must fail) commands itself,
  4. pass -> commit the task's files + state.json, status done;
     fail -> retry with the failing output as feedback, up to max_attempts;
     then revert, status blocked. Tasks depending on a blocked task become skipped.

Logs: .autospec/runs/<task id>/ (gitignored).

Usage:
  python3 scripts/autospec-run.py                     # loop until nothing is runnable
  python3 scripts/autospec-run.py --only T-api-003t   # one task
  python3 scripts/autospec-run.py --max-tasks 5
  python3 scripts/autospec-run.py --dry-run           # print the order, run nothing
Runner: --runner PATH or $AUTOSPEC_RUNNER (default ~/Dev/opencode-docker/run.sh).
Run it from a terminal: run.sh uses `docker run -it`, which needs a TTY on stdin.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".autospec/state.json"
TASKS = ROOT / "plan/tasks"
RUNS = ROOT / ".autospec/runs"
BLOCKED = ROOT / ".autospec/BLOCKED_REASON"
STATE_REL = ".autospec/state.json"
BLOCKED_REL = ".autospec/BLOCKED_REASON"

CHECK_TIMEOUT = 3600  # e2e verify builds the whole stack
FEEDBACK_LINES = 150


# ── task files ────────────────────────────────────────────────────────────────


def _scalar(v: str):
    v = v.strip()
    if v == "[]":
        return []
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1].replace("''", "'")
    if v.startswith('"') and v.endswith('"'):
        return json.loads(v)
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def load_task(task_id: str) -> dict:
    """Parse the YAML frontmatter that scripts/plan/core.py writes (flat keys, block lists)."""
    lines = (TASKS / f"{task_id}.md").read_text().splitlines()
    if not lines or lines[0] != "---":
        sys.exit(f"{task_id}: no frontmatter")
    fm: dict = {}
    key = None
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith("- ") and key:
            fm[key].append(_scalar(line[2:]))
        elif m := re.match(r"^([a-z_]+):(.*)$", line):
            key, rest = m.group(1), m.group(2)
            fm[key] = _scalar(rest) if rest.strip() else []
        else:
            sys.exit(f"{task_id}: cannot parse frontmatter line: {line!r}")
    for k in ("edit", "verify", "expect_fail", "depends_on"):
        fm.setdefault(k, [])
    fm.setdefault("max_attempts", 3)
    return fm


# ── state ─────────────────────────────────────────────────────────────────────


def load_state() -> dict:
    return json.loads(STATE.read_text())


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def next_task(state: dict, only: str | None) -> str | None:
    """First pending task whose deps are done; marks tasks with blocked/skipped deps as skipped."""
    tasks = state["tasks"]
    changed = True
    while changed:  # skipping can cascade
        changed = False
        for tid, entry in tasks.items():
            if entry["status"] != "pending":
                continue
            deps = load_task(tid)["depends_on"]
            bad = [d for d in deps if tasks.get(d, {}).get("status") in ("blocked", "skipped")]
            if bad:
                entry.update(status="skipped", reason=f"dependency {bad[0]} is {tasks[bad[0]]['status']}")
                changed = True
    save_state(state)
    for tid, entry in tasks.items():
        if only and tid != only:
            continue
        if entry["status"] == "pending" and all(
            tasks.get(d, {}).get("status") == "done" for d in load_task(tid)["depends_on"]
        ):
            return tid
    return None


# ── git / working tree ────────────────────────────────────────────────────────


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True, text=True)


def dirty_paths() -> set[str]:
    out = git("status", "--porcelain=v1", "-z", "-uall").stdout.split("\0")
    paths, i = set(), 0
    while i < len(out):
        rec = out[i]
        i += 1
        if not rec:
            continue
        paths.add(rec[3:])
        if rec[0] in "RC":  # rename/copy: next field is the source path
            paths.add(out[i])
            i += 1
    return paths


def file_hash(rel: str) -> str | None:
    p = ROOT / rel
    return hashlib.sha1(p.read_bytes()).hexdigest() if p.is_file() else None


def snapshot() -> dict[str, str | None]:
    return {p: file_hash(p) for p in dirty_paths()}


def changed_since(snap: dict[str, str | None]) -> set[str]:
    """Paths whose content differs from the snapshot (a clean path's baseline is HEAD)."""
    out = set()
    for p in dirty_paths() | set(snap):
        if p not in snap or file_hash(p) != snap[p]:
            out.add(p)
    return out


def in_head(rel: str) -> bool:
    return git("cat-file", "-e", f"HEAD:{rel}", check=False).returncode == 0


def revert(paths: set[str], snap: dict[str, str | None]) -> list[str]:
    """Restore paths to their pre-task state. Returns paths that could not be restored."""
    lost = []
    for p in sorted(paths):
        if p in snap:  # was already dirty before the task: we have no copy of it
            lost.append(p)
        elif in_head(p):
            git("checkout", "HEAD", "--", p)
        else:
            (ROOT / p).unlink(missing_ok=True)
    return lost


# ── running ───────────────────────────────────────────────────────────────────


def run_logged(cmd: list[str] | str, log: Path, timeout: int | None, shell: bool = False) -> int:
    """Run cmd, stream output to the terminal and to log. Returns the exit code (124 on timeout)."""
    with log.open("a") as fh:
        fh.write(f"\n$ {cmd if shell else ' '.join(cmd)}\n")
        fh.flush()
        proc = subprocess.Popen(
            cmd, cwd=ROOT, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        start = time.monotonic()
        assert proc.stdout
        for line in proc.stdout:
            sys.stdout.write(line)
            fh.write(line)
            if timeout and time.monotonic() - start > timeout:
                proc.kill()
                fh.write(f"\n[autospec-run] timeout after {timeout}s\n")
                return 124
        return proc.wait()


def prompt_for(tid: str, attempt: int, feedback: Path) -> str:
    p = (
        f"You are the executor. Do exactly one task: plan/tasks/{tid}.md. Follow AGENTS.md. "
        f"Edit only the files under `edit:`. Do not start other tasks, do not touch "
        f".autospec/state.json, do not run git. Stop when its verify commands pass."
    )
    if attempt > 1:
        p += (
            f" This is attempt {attempt}: the previous attempt failed the runner's checks. "
            f"Read {feedback.relative_to(ROOT)} first. Your files from that attempt are still in place."
        )
    return p


def tail(log: Path, n: int = FEEDBACK_LINES) -> str:
    return "\n".join(log.read_text(errors="replace").splitlines()[-n:])


def check(task: dict, log: Path) -> str | None:
    """Run verify (must pass) and expect_fail (must fail). Returns a failure message or None."""
    for cmd in task["verify"]:
        if run_logged(cmd, log, CHECK_TIMEOUT, shell=True) != 0:
            return f"verify failed: {cmd}"
    for cmd in task["expect_fail"]:
        if run_logged(cmd, log, CHECK_TIMEOUT, shell=True) == 0:
            return f"expect_fail passed but must fail (tests not red against the stub): {cmd}"
    return None


def do_task(tid: str, runner: str, session_timeout: int) -> tuple[str, str]:
    """Run one task through all attempts. Returns (status, reason)."""
    task = load_task(tid)
    allowed = set(task["edit"]) | {BLOCKED_REL}
    run_dir = RUNS / tid
    run_dir.mkdir(parents=True, exist_ok=True)
    feedback = run_dir / "feedback.txt"
    BLOCKED.unlink(missing_ok=True)
    snap = snapshot()
    reason = ""

    for attempt in range(1, task["max_attempts"] + 1):
        log = run_dir / f"attempt-{attempt}.log"
        log.write_text(f"[autospec-run] {tid} attempt {attempt}\n")
        print(f"\n=== {tid} — attempt {attempt}/{task['max_attempts']}: {task['title']}")
        agent = [runner, "--project", str(ROOT), "--keep", "--", "run", prompt_for(tid, attempt, feedback)]
        code = run_logged(agent, log, session_timeout)

        changed = changed_since(snap)
        if STATE_REL in changed:  # the runner owns state.json
            git("checkout", "HEAD", "--", STATE_REL)
            changed.discard(STATE_REL)
        outside = changed - allowed
        if outside:
            lost = revert(outside, snap)
            reason = f"edited files outside `edit:` (reverted): {', '.join(sorted(outside))}"
            if lost:
                reason += f"; could not restore pre-dirty files: {', '.join(lost)}"
        elif BLOCKED.exists():
            reason = "agent blocked: " + BLOCKED.read_text().strip()
            BLOCKED.unlink()
            revert(changed - {BLOCKED_REL}, snap)
            return "blocked", reason
        elif not changed:
            reason = f"agent exited ({code}) without changing any file"
        else:
            reason = check(task, log) or ""
            if not reason:
                git("add", "--", *sorted(changed))
                return "done", ""

        print(f"[autospec-run] {tid} attempt {attempt} failed: {reason}")
        feedback.write_text(f"Runner check failed: {reason}\n\nLast output:\n{tail(log)}\n")

    revert(changed_since(snap) - {STATE_REL}, snap)
    return "blocked", f"failed {task['max_attempts']} attempts; last: {reason}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runner", default=os.environ.get("AUTOSPEC_RUNNER", "~/Dev/opencode-docker/run.sh"))
    ap.add_argument("--only", help="run just this task id")
    ap.add_argument("--max-tasks", type=int, default=0, help="stop after N tasks (0 = no limit)")
    ap.add_argument("--session-timeout", type=int, default=5400, help="seconds per agent session")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    runner = str(Path(args.runner).expanduser())

    if args.dry_run:
        state = load_state()
        for tid, e in state["tasks"].items():
            print(f"{e['status']:8} {tid}  deps={load_task(tid)['depends_on']}")
        return 0
    if not Path(runner).is_file():
        sys.exit(f"runner not found: {runner} (use --runner or $AUTOSPEC_RUNNER)")

    done_count = 0
    while True:
        state = load_state()
        tid = next_task(state, args.only)
        if not tid:
            break
        status, reason = do_task(tid, runner, args.session_timeout)
        state = load_state()
        state["tasks"][tid] = {"status": status, **({"reason": reason} if reason else {})}
        save_state(state)
        git("add", "--", STATE_REL)
        title = load_task(tid)["title"]
        git("commit", "-q", "-m", f"{tid}: {title}" if status == "done" else f"{tid}: blocked\n\n{reason}")
        print(f"[autospec-run] {tid} -> {status} {reason}")
        done_count += 1
        if args.only or (args.max_tasks and done_count >= args.max_tasks):
            break

    counts: dict[str, int] = {}
    for e in load_state()["tasks"].values():
        counts[e["status"]] = counts.get(e["status"], 0) + 1
    print(f"[autospec-run] finished: {counts}")
    pending = counts.get("pending", 0)
    if pending and not args.only and not args.max_tasks:
        print(f"[autospec-run] {pending} pending but none runnable (dependency cycle or missing ids)")
    return 1 if counts.get("blocked") else 0


if __name__ == "__main__":
    sys.exit(main())
