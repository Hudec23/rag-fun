#!/usr/bin/env python3
"""autospec task loop (phase 2). Runs on the host; needs python3 (stdlib only), git and Docker.

Starts from a clean working tree. For each pending task in .autospec/state.json whose depends_on
are all done:
  1. start a fresh agent session for that one task through the sandbox runner,
  2. check that only files under the task's `edit:` changed (other changes are reverted),
  3. run the gate itself, inside the agent's dind container (same image cache and volumes the
     agent built with): `verify:` must pass, `expect_fail:` must fail, then the service's
     `regression` (build, lint, baseline_tests, tests locked by done impl tasks) must pass,
  4. pass -> commit the task's files + state.json, status done;
     fail -> retry with the failing check's output as feedback, up to max_attempts;
     then revert, status blocked. Tasks depending on a blocked task become skipped.
At the end it writes and commits .autospec/REPORT.md (input for /autospec-unblock).

Logs: .autospec/runs/<task id>/ (gitignored).

Stopping: Ctrl-C stops the agent and the loop, leaving that task pending with its changes
reverted. To stop after the current task instead: `touch .autospec/STOP` (removed on next start).

Usage:
  python3 .autospec/kit/scripts/autospec-run.py                     # loop until nothing is runnable
  python3 .autospec/kit/scripts/autospec-run.py --only T-api-003t   # one task
  python3 .autospec/kit/scripts/autospec-run.py --max-tasks 5
  python3 .autospec/kit/scripts/autospec-run.py --dry-run           # print the order, run nothing
Runner (required): --runner PATH or $AUTOSPEC_RUNNER. It is called as
  <runner> --project <repo root> --keep -- run "<task prompt>"
which is the interface of opencodocker's run.sh (https://github.com/Hudec23/opencodocker):
--keep reuses its Docker-in-Docker daemon (and image cache) between tasks, `run` is opencode's
non-interactive mode. Any wrapper with that interface works.
Run it from the project root, in a terminal: run.sh uses `docker run -it`, which needs a TTY on stdin.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import functools
import json
import os
import re
import shlex
import subprocess
import sys
import threading
from pathlib import Path

import autospec_yaml

def _project_root() -> Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode != 0 or not (Path(r.stdout.strip()) / ".autospec/state.json").is_file():
        sys.exit("[autospec-run] run from the project root (a git repo with .autospec/state.json)")
    return Path(r.stdout.strip()).resolve()


ROOT = _project_root()
KIT_REL = Path(__file__).resolve().parents[1].relative_to(ROOT).as_posix()  # .autospec/kit
STATE_REL = ".autospec/state.json"
REPORT_REL = ".autospec/REPORT.md"
STATE = ROOT / STATE_REL
REPORT = ROOT / REPORT_REL
TASKS = ROOT / ".autospec/plan/tasks"
SERVICES = ROOT / ".autospec/plan/services"
RUNS = ROOT / ".autospec/runs"
BLOCKED = ROOT / ".autospec/BLOCKED_REASON"
STOP = ROOT / ".autospec/STOP"
MUST_IGNORE = (".autospec/runs/x", ".autospec/BLOCKED_REASON", ".autospec/STOP")
INTERRUPTED = (130, 143)  # agent killed by SIGINT / SIGTERM: the user wants to stop
DEFAULT_REGRESSION = ["build", "lint", "baseline_tests", "done_tests"]
CHECK_TIMEOUT = 3600  # e2e verify builds the whole stack
FEEDBACK_LINES = 150


class Interrupted(Exception):
    pass


# ── plan files ────────────────────────────────────────────────────────────────


@functools.cache
def load_task(task_id: str) -> dict:
    path = TASKS / f"{task_id}.md"
    try:
        fm = autospec_yaml.frontmatter(path.read_text())
    except (OSError, ValueError) as e:
        sys.exit(f"{path.relative_to(ROOT)}: {e} (run .autospec/kit/scripts/autospec-check.py)")
    for k in ("edit", "verify", "expect_fail", "depends_on", "locked"):
        fm[k] = fm.get(k) or []
    fm.setdefault("max_attempts", 3)
    return fm


@functools.cache
def load_service(name: str) -> dict:
    path = SERVICES / f"{name}.yaml"
    try:
        return autospec_yaml.load(path.read_text())
    except (OSError, ValueError) as e:
        sys.exit(f"{path.relative_to(ROOT)}: {e} (run .autospec/kit/scripts/autospec-check.py)")


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
# The loop starts from a clean tree and commits after every task, so during a task every path
# `git status` reports was changed by that task.


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True, text=True)


def changed_paths() -> set[str]:
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


def require_clean() -> None:
    missing = [p for p in MUST_IGNORE if git("check-ignore", "-q", p, check=False).returncode]
    if missing:
        sys.exit("[autospec-run] add to .gitignore: .autospec/runs/, .autospec/BLOCKED_REASON, .autospec/STOP")
    dirty = changed_paths()
    if dirty:
        sys.exit(
            f"[autospec-run] working tree not clean: {', '.join(sorted(dirty)[:10])}\n"
            "Commit or stash them (git stash -u), or gitignore build artifacts, then run again."
        )


def discard(paths: set[str]) -> None:
    """Restore paths to HEAD (delete them if HEAD doesn't have them)."""
    for p in sorted(paths):
        if git("cat-file", "-e", f"HEAD:{p}", check=False).returncode == 0:
            git("checkout", "HEAD", "--", p)
        else:
            (ROOT / p).unlink(missing_ok=True)


def discard_all() -> None:
    git("reset", "-q", "--hard", "HEAD")
    git("clean", "-q", "-fd")  # untracked, not ignored: only the task created those


# ── running ───────────────────────────────────────────────────────────────────


def run_logged(cmd: list[str] | str, log: Path, timeout: int | None, shell: bool = False) -> tuple[int, str]:
    """Run cmd, stream output to the terminal and to log.

    Returns (exit code, last FEEDBACK_LINES of output); the code is 124 on timeout.
    """
    tail: collections.deque[str] = collections.deque(maxlen=FEEDBACK_LINES)
    with log.open("a") as fh:
        fh.write(f"\n$ {cmd if shell else shlex.join(cmd)}\n")
        fh.flush()
        proc = subprocess.Popen(
            cmd, cwd=ROOT, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        def pump() -> None:
            assert proc.stdout
            for line in proc.stdout:
                sys.stdout.write(line)
                fh.write(line)
                tail.append(line)

        reader = threading.Thread(target=pump, daemon=True)
        reader.start()
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            code = 124
        except KeyboardInterrupt:  # Ctrl-C reached the child too; give it a moment to exit
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
            raise
        reader.join(5)
        if code == 124:
            fh.write(f"\n[autospec-run] timeout after {timeout}s\n")
            tail.append(f"[autospec-run] timeout after {timeout}s\n")
    return code, "".join(tail)


def agent_cmd(runner: str, prompt: str) -> list[str]:
    """The one place that knows the runner's interface."""
    return [runner, "--project", str(ROOT), "--keep", "--", "run", prompt]


def prompt_for(tid: str, attempt: int, feedback: Path) -> str:
    p = (
        f"You are the executor. Do exactly one task: .autospec/plan/tasks/{tid}.md. Follow AGENTS.md and {KIT_REL}/EXECUTOR.md. "
        f"Edit only the files under `edit:`. Do not start other tasks, do not touch "
        f".autospec/state.json, do not run git. Stop when its verify commands pass."
    )
    if attempt > 1:
        p += (
            f" This is attempt {attempt}: the previous attempt failed the runner's checks. "
            f"Read {feedback.relative_to(ROOT)} first. Your files from that attempt are still in place."
        )
    return p


def dind_name() -> str:
    """The dind container run.sh starts for this project (instance = sanitized project basename)."""
    instance = re.sub(r"[^a-z0-9-]+", "-", ROOT.name.lower()).strip("-")
    return os.environ.get("AUTOSPEC_DIND", f"oc-dind-{instance}")


def dind_for_checks() -> str | None:
    """Running dind container that mounts this project, or None (checks then use host Docker)."""
    name = dind_name()
    r = subprocess.run(
        ["docker", "inspect", "-f", '{{.State.Running}} {{index .Config.Labels "opencode.project"}}', name],
        capture_output=True, text=True,
    )
    running, _, project = r.stdout.strip().partition(" ")
    if r.returncode != 0 or running != "true" or project != str(ROOT):
        print(f"[autospec-run] warning: {name} not running for {ROOT}; checks use host Docker (cold cache)")
        return None
    return name


# ── gate ──────────────────────────────────────────────────────────────────────


def done_tests(service: str, state: dict) -> list[str]:
    """Tests locked by done impl tasks of this service: proven green, must stay green."""
    files = []
    for tid, entry in state["tasks"].items():
        t = load_task(tid)
        if entry["status"] == "done" and t["kind"] == "impl" and t["service"] == service:
            files += t["locked"]
    return files


def regression(task: dict, state: dict) -> list[tuple[str, str]]:
    """(name, command) pairs of the service's regression, per .autospec/plan/services/<service>.yaml."""
    name = task["service"]
    svc = load_service(name)
    cmds = svc.get("commands") or {}
    out, files = [], []
    for step in svc.get("regression") or DEFAULT_REGRESSION:
        if step in ("build", "lint"):
            if cmds.get(step):
                out.append((step, cmds[step]))
        elif step == "baseline_tests":
            files += svc.get("baseline_tests") or []
        elif step == "done_tests":
            files += done_tests(name, state)
        else:
            sys.exit(f".autospec/plan/services/{name}.yaml: unknown regression step {step!r}")
    files = list(dict.fromkeys(files))
    if files:
        if not cmds.get("test_files"):
            sys.exit(f".autospec/plan/services/{name}.yaml: regression runs tests but commands.test_files is missing")
        base = str(svc.get("path") or "").strip("/")
        rel = [f[len(base) + 1:] if base not in ("", ".") and f.startswith(base + "/") else f for f in files]
        out.append(("tests", cmds["test_files"].replace("{files}", " ".join(map(shlex.quote, rel)))))
    return out


def gate(task: dict, state: dict, log: Path) -> tuple[str, str]:
    """Run verify (must pass), expect_fail (must fail), regression (must pass).

    Returns (failure reason, output of the failing command), or ("", "") when everything holds.
    Commands run inside the agent's dind container (project mounted at /workspace), so they reuse
    the images and volumes the agent already built instead of rebuilding on the host engine.
    """
    dind = dind_for_checks()

    def run(cmd: str) -> tuple[int, str]:
        if dind:
            return run_logged(["docker", "exec", "-w", "/workspace", dind, "sh", "-c", cmd], log, CHECK_TIMEOUT)
        return run_logged(cmd, log, CHECK_TIMEOUT, shell=True)

    for cmd in task["verify"]:
        code, out = run(cmd)
        if code != 0:
            return f"verify failed: {cmd}", out
    for cmd in task["expect_fail"]:
        code, out = run(cmd)
        if code == 0:
            return f"expect_fail passed but must fail (tests not red against the stub): {cmd}", out
    for name, cmd in regression(task, state):
        code, out = run(cmd)
        if code != 0:
            return f"regression {name} failed — this task broke something that worked before: {cmd}", out
    return "", ""


# ── one task ──────────────────────────────────────────────────────────────────


def do_task(tid: str, state: dict, runner: str, session_timeout: int) -> tuple[str, str]:
    """Run one task through all attempts. Returns (status, reason)."""
    task = load_task(tid)
    allowed = set(task["edit"])
    run_dir = RUNS / tid
    run_dir.mkdir(parents=True, exist_ok=True)
    feedback = run_dir / "feedback.txt"
    BLOCKED.unlink(missing_ok=True)
    reason = ""

    try:
        for attempt in range(1, task["max_attempts"] + 1):
            log = run_dir / f"attempt-{attempt}.log"
            log.write_text(f"[autospec-run] {tid} attempt {attempt}\n")
            print(f"\n=== {tid} — attempt {attempt}/{task['max_attempts']}: {task['title']}")
            code, _ = run_logged(agent_cmd(runner, prompt_for(tid, attempt, feedback)), log, session_timeout)
            if code in INTERRUPTED:
                raise Interrupted(f"agent exited {code}")

            output = ""
            changed = changed_paths()
            if STATE_REL in changed:  # the runner owns state.json
                discard({STATE_REL})
                changed.discard(STATE_REL)
            outside = changed - allowed
            if outside:
                discard(outside)
                reason = f"edited files outside `edit:` (reverted): {', '.join(sorted(outside))}"
            elif BLOCKED.exists():
                reason = "agent blocked: " + BLOCKED.read_text().strip()
                BLOCKED.unlink()
                discard_all()
                return "blocked", reason
            elif not changed:
                reason = f"agent exited ({code}) without changing any file"
            else:
                reason, output = gate(task, state, run_dir / f"attempt-{attempt}.checks.log")
                if not reason:
                    git("add", "--", *sorted(changed))
                    return "done", ""

            print(f"[autospec-run] {tid} attempt {attempt} failed: {reason}")
            text = f"Runner check failed: {reason}\n"
            if output:
                text += f"\nOutput of that command (last {FEEDBACK_LINES} lines):\n{output}"
            feedback.write_text(text)
    except (Interrupted, KeyboardInterrupt) as e:
        discard_all()
        raise Interrupted(f"{tid}: {str(e) or 'interrupted'}; task left pending, changes reverted") from None

    discard_all()
    return "blocked", f"failed {task['max_attempts']} attempts; last: {reason}"


# ── report ────────────────────────────────────────────────────────────────────


def write_report(state: dict) -> None:
    tasks = state["tasks"]
    counts = collections.Counter(e["status"] for e in tasks.values())
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = [
        "# autospec run report",
        "",
        f"Generated {now} at commit {git('rev-parse', '--short', 'HEAD').stdout.strip()}. "
        + ", ".join(f"{s}: {counts.get(s, 0)}" for s in ("done", "blocked", "skipped", "pending")),
        "",
        "Input for /autospec-unblock. Logs: `.autospec/runs/<task>/` on the machine that ran the loop.",
    ]
    for status in ("blocked", "skipped", "pending"):
        rows = [(tid, e) for tid, e in tasks.items() if e["status"] == status]
        if not rows:
            continue
        out += ["", f"## {status.capitalize()}", "", "| Task | Title | Reason |", "|---|---|---|"]
        for tid, e in rows:
            why = (e.get("reason") or "–").replace("|", "\\|").replace("\n", " ")
            out.append(f"| {tid} | {load_task(tid)['title']} | {why} |")
    REPORT.write_text("\n".join(out) + "\n")


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runner", default=os.environ.get("AUTOSPEC_RUNNER", ""), help="sandbox runner script")
    ap.add_argument("--only", help="run just this task id")
    ap.add_argument("--max-tasks", type=int, default=0, help="stop after N tasks (0 = no limit)")
    ap.add_argument("--session-timeout", type=int, default=5400, help="seconds per agent session")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    runner = str(Path(args.runner).expanduser())

    if args.dry_run:
        for tid, e in load_state()["tasks"].items():
            print(f"{e['status']:8} {tid}  deps={load_task(tid)['depends_on']}")
        return 0
    if not args.runner:
        sys.exit("no runner: pass --runner PATH or set $AUTOSPEC_RUNNER (e.g. opencodocker/run.sh)")
    if not Path(runner).is_file():
        sys.exit(f"runner not found: {runner}")
    require_clean()

    STOP.unlink(missing_ok=True)
    done_count, stopped, code = 0, False, 0
    while True:
        if STOP.exists():
            STOP.unlink()
            print("[autospec-run] .autospec/STOP found, stopping")
            stopped = True
            break
        state = load_state()
        tid = next_task(state, args.only)
        if not tid:
            break
        try:
            status, reason = do_task(tid, state, runner, args.session_timeout)
        except Interrupted as e:
            print(f"\n[autospec-run] stopped: {e}")
            stopped, code = True, 130
            break
        state["tasks"][tid] = {"status": status, **({"reason": reason} if reason else {})}
        save_state(state)
        git("add", "--", STATE_REL)
        title = load_task(tid)["title"]
        git("commit", "-q", "-m", f"{tid}: {title}" if status == "done" else f"{tid}: blocked\n\n{reason}")
        print(f"[autospec-run] {tid} -> {status} {reason}")
        leftover = changed_paths()
        if leftover:  # the gate's commands wrote files outside .gitignore
            sys.exit(
                f"[autospec-run] checks left files that are not gitignored: {', '.join(sorted(leftover)[:10])}\n"
                "Gitignore them (build/test artifacts) or fix the command that writes them, then run again."
            )
        done_count += 1
        if args.only or (args.max_tasks and done_count >= args.max_tasks):
            break

    state = load_state()
    write_report(state)
    git("add", "--", REPORT_REL, STATE_REL)  # state: the final skip cascade
    git("commit", "-q", "-m", "autospec: run report")
    counts = collections.Counter(e["status"] for e in state["tasks"].values())
    print(f"[autospec-run] finished: {dict(counts)} — see {REPORT_REL}")
    pending = counts.get("pending", 0)
    if pending and not (stopped or args.only or args.max_tasks):
        print(f"[autospec-run] {pending} pending but none runnable (dependency cycle or missing ids)")
    return code or (1 if counts.get("blocked") else 0)


if __name__ == "__main__":
    sys.exit(main())
