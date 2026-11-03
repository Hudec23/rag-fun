#!/usr/bin/env python3
"""autospec plan checker and traceability generator.

Reads .autospec/plan/SYSTEM.md (requirements table), .autospec/plan/executor.yaml, .autospec/plan/features.yaml,
.autospec/plan/tasks/*.md, .autospec/plan/services/*.yaml and .autospec/state.json. Writes .autospec/plan/TRACEABILITY.md and
exits 1 if the plan breaks any rule. Re-run it after every plan change.

Run from the project root (needs only Docker):
  docker run --rm -v "$PWD":/w -w /w python:3.12.7-slim sh -c \
    'pip install -q --root-user-action=ignore --disable-pip-version-check pyyaml==6.0.2 \
     && python .autospec/kit/scripts/autospec-check.py'
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("autospec-check: needs PyYAML (pip install pyyaml==6.0.2)")

import autospec_yaml  # the stdlib reader autospec-run.py uses; must agree with PyYAML

CHARS_PER_TOKEN = 4  # rough estimate, good enough for a budget check
REQ_ID = re.compile(r"^R-\d{3}$")
TASK_ID = re.compile(r"^T-([a-z0-9-]+)-(\d{3})(t?)$")
STATUSES = {"pending", "done", "blocked", "skipped"}
LIST_KEYS = ("depends_on", "edit", "read", "locked", "verify", "expect_fail")
REGRESSION_STEPS = {"build", "lint", "baseline_tests", "done_tests"}

errors = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


# ---------------------------------------------------------------- loading

def load_requirements(root):
    """Rows of the markdown table under the '## ... Requirements' heading."""
    path = root / ".autospec/plan/SYSTEM.md"
    reqs = {}
    if not path.exists():
        err(".autospec/plan/SYSTEM.md", "missing")
        return reqs
    in_section = False
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if line.startswith("## "):
            in_section = "requirements" in line.lower()
            continue
        if not in_section or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] == "ID" or set(cells[0]) <= set("-: "):
            continue  # header or separator row
        where = f".autospec/plan/SYSTEM.md:{n}"
        if len(cells) < 4:
            err(where, "requirement row needs 4 columns: ID | Requirement | Kind | Covered by")
            continue
        rid, text, kind, covered = cells[:4]
        covered = covered.lower()
        if not REQ_ID.match(rid):
            err(where, f"requirement id {rid!r} must look like R-001")
            continue
        if rid in reqs:
            err(where, f"duplicate requirement id {rid}")
        if covered not in ("features", "skeleton"):
            err(where, f"{rid}: 'Covered by' must be 'features' or 'skeleton', got {covered!r}")
        reqs[rid] = {"text": text, "kind": kind, "covered": covered}
    if not reqs:
        err(".autospec/plan/SYSTEM.md", "no requirement rows found under a '## ... Requirements' heading")
    return reqs


def same_as_runner(where, text, parsed, read):
    """Error unless autospec-run.py's reader (`read`) gets exactly what PyYAML got."""
    hint = "keep values on one line; lists as [a, b] or '- item' lines; quote odd strings"
    try:
        mine = read(text)
    except ValueError as e:
        err(where, f"autospec-run.py cannot read this: {e} ({hint})")
        return
    for key in sorted(set(mine) | set(parsed)):
        if mine.get(key) != parsed.get(key):
            err(where, f"'{key}' reads as {mine.get(key)!r} in autospec-run.py but "
                f"{parsed.get(key)!r} in YAML ({hint})")


def load_yaml(path, runner_reads=False):
    try:
        text = path.read_text()
        data = yaml.safe_load(text) or {}
    except (OSError, yaml.YAMLError) as e:
        err(str(path), f"cannot parse: {e}")
        return {}
    if runner_reads:
        same_as_runner(str(path), text, data, autospec_yaml.load)
    return data


def load_executor(root):
    """Task size limits from .autospec/plan/executor.yaml."""
    path = root / ".autospec/plan/executor.yaml"
    if not path.exists():
        err(".autospec/plan/executor.yaml", "missing (copy .autospec/kit/templates/executor.yaml)")
        return {"max_read_tokens": 16000, "max_edit_files": 3}
    ex = load_yaml(path)
    ctx = ex.get("context_tokens")
    if not isinstance(ctx, int) or ctx <= 0:
        err(".autospec/plan/executor.yaml", "context_tokens must be a positive integer")
        ctx = 65536
    ex.setdefault("max_read_tokens", ctx // 4)
    ex.setdefault("max_edit_files", 3)
    for key in ("max_read_tokens", "max_edit_files"):
        if not isinstance(ex[key], int) or ex[key] <= 0:
            err(".autospec/plan/executor.yaml", f"{key} must be a positive integer")
    if isinstance(ex["max_read_tokens"], int) and ex["max_read_tokens"] > ctx // 2:
        err(".autospec/plan/executor.yaml", f"max_read_tokens {ex['max_read_tokens']} leaves less than half of "
            f"context_tokens {ctx} for reasoning and tool output")
    return ex


def load_services(root):
    services = {}
    for p in sorted((root / ".autospec/plan/services").glob("*.yaml")):
        services[p.stem] = load_yaml(p, runner_reads=True)
    if not services:
        err(".autospec/plan/services", "no <name>.yaml files")
    return services


def load_features(root):
    path = root / ".autospec/plan/features.yaml"
    if not path.exists():
        err(".autospec/plan/features.yaml", "missing")
        return {}
    features = {}
    for f in load_yaml(path).get("features") or []:
        fid = f.get("id")
        if not fid or not str(fid).startswith("F-"):
            err(".autospec/plan/features.yaml", f"feature id {fid!r} must start with F-")
            continue
        if fid in features:
            err(".autospec/plan/features.yaml", f"duplicate feature id {fid}")
        for key in ("requirements", "contracts", "acceptance"):
            f[key] = f.get(key) or []
        features[fid] = f
    return features


def load_tasks(root):
    tasks = {}
    for p in sorted((root / ".autospec/plan/tasks").glob("T-*.md")):
        where = f".autospec/plan/tasks/{p.name}"
        text = p.read_text()
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            err(where, "no YAML frontmatter between --- lines")
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            err(where, f"cannot parse frontmatter: {e}")
            continue
        same_as_runner(where, text, dict(fm), autospec_yaml.frontmatter)
        for key in ("id", "kind", "feature", "title", "service"):
            if not fm.get(key):
                err(where, f"missing '{key}'")
        for key in LIST_KEYS:
            fm[key] = fm.get(key) or []
        if fm.get("id") != p.stem:
            err(where, f"id {fm.get('id')!r} does not match file name")
        fm["_where"] = where
        fm["_chars"] = len(text)
        tasks[p.stem] = fm
    if not tasks:
        err(".autospec/plan/tasks", "no T-*.md task files")
    return tasks


def load_state(root, tasks):
    path = root / ".autospec/state.json"
    if not path.exists():
        err(".autospec/state.json", "missing (initialise every task as pending)")
        return {}
    try:
        entries = json.loads(path.read_text()).get("tasks") or {}
    except (OSError, json.JSONDecodeError, AttributeError) as e:
        err(".autospec/state.json", f"cannot parse: {e}")
        return {}
    status = {}
    for tid, entry in entries.items():
        s = (entry or {}).get("status")
        if tid not in tasks:
            err(".autospec/state.json", f"{tid} has no task file")
        if s not in STATUSES:
            err(".autospec/state.json", f"{tid}: status {s!r} not one of {sorted(STATUSES)}")
        status[tid] = s
    for tid in tasks:
        if tid not in entries:
            err(".autospec/state.json", f"{tid} missing")
    return status


def check_services(root, services):
    for name, svc in services.items():
        where = f".autospec/plan/services/{name}.yaml"
        cmds = svc.get("commands") or {}
        steps = svc.get("regression") or sorted(REGRESSION_STEPS)
        for step in steps:
            if step not in REGRESSION_STEPS:
                err(where, f"unknown regression step {step!r} (use {sorted(REGRESSION_STEPS)})")
            elif step in ("build", "lint") and not cmds.get(step):
                err(where, f"regression lists {step} but commands.{step} is missing")
        if {"baseline_tests", "done_tests"} & set(steps):
            if "{files}" not in str(cmds.get("test_files", "")):
                err(where, "regression runs tests: commands.test_files must contain {files}")
        for path in svc.get("baseline_tests") or []:
            if not (root / path).exists():
                err(where, f"baseline test {path} does not exist")


# ---------------------------------------------------------------- graph

def ancestors_of(tasks):
    """Transitive depends_on per task, or None if the graph has a cycle."""
    anc = {}
    visiting = set()

    def walk(tid, stack):
        if tid in anc:
            return anc[tid]
        if tid in visiting:
            err(tasks[tid]["_where"], "dependency cycle: " + " -> ".join(stack + [tid]))
            raise ValueError
        visiting.add(tid)
        out = set()
        for d in tasks[tid]["depends_on"]:
            if d in tasks:
                out |= {d} | walk(d, stack + [tid])
        visiting.discard(tid)
        anc[tid] = out
        return out

    try:
        for tid in tasks:
            walk(tid, [])
    except ValueError:
        return None
    return anc


def critical_path(tasks):
    best = {}

    def longest(tid):
        if tid not in best:
            deps = [d for d in tasks[tid]["depends_on"] if d in tasks]
            prev = max((longest(d) for d in deps), key=len, default=[])
            best[tid] = prev + [tid]
        return best[tid]

    return max((longest(t) for t in tasks), key=len, default=[])


# ---------------------------------------------------------------- checks

def check_requirements(reqs, features):
    for fid, f in features.items():
        if not f["requirements"]:
            err(".autospec/plan/features.yaml", f"{fid} lists no requirements")
        for rid in f["requirements"]:
            if rid not in reqs:
                err(".autospec/plan/features.yaml", f"{fid} references unknown requirement {rid}")
    for rid, r in reqs.items():
        if r["covered"] == "features" and not any(rid in f["requirements"] for f in features.values()):
            err(".autospec/plan/SYSTEM.md", f"{rid} is covered by features, but no feature lists it")


def check_features(root, features):
    for fid, f in features.items():
        if not f["acceptance"]:
            err(".autospec/plan/features.yaml", f"{fid} has no acceptance tests")
        for path in f["acceptance"]:
            if not (root / path).exists():
                err(".autospec/plan/features.yaml", f"{fid}: acceptance test {path} does not exist")
        for ref in f["contracts"]:
            if not (root / ref.split("#")[0]).exists():
                err(".autospec/plan/features.yaml", f"{fid}: contract {ref} does not exist")


def check_tasks(root, tasks, features, services, anc, executor):
    test_files = {p for f in features.values() for p in f["acceptance"]}
    test_files |= {p for t in tasks.values() if t.get("kind") == "test" for p in t["edit"]}
    max_edit, max_read = executor["max_edit_files"], executor["max_read_tokens"]
    # The harness loads both into every session.
    always = [root / "AGENTS.md", Path(__file__).resolve().parents[1] / "EXECUTOR.md"]
    base_chars = sum(p.stat().st_size for p in always if p.exists())

    for tid, t in tasks.items():
        w = t["_where"]
        m = TASK_ID.match(tid)
        kind = t.get("kind")
        if not m:
            err(w, "id must look like T-<service>-NNN or T-<service>-NNNt")
        elif (m.group(3) == "t") != (kind == "test"):
            err(w, "ids ending in 't' are test tasks and only those; check 'kind'")
        if kind not in ("test", "impl"):
            err(w, f"kind {kind!r} must be 'test' or 'impl'")
        if t.get("service") and t["service"] not in services:
            err(w, f"service {t['service']!r} has no .autospec/plan/services/{t['service']}.yaml")
        if t.get("feature") and t["feature"] not in features:
            err(w, f"feature {t['feature']!r} not in .autospec/plan/features.yaml")
        for d in t["depends_on"]:
            if d not in tasks:
                err(w, f"depends_on unknown task {d}")
        if not t["edit"]:
            err(w, "edit: is empty")
        if len(t["edit"]) > max_edit:
            err(w, f"edits {len(t['edit'])} files (max {max_edit}, .autospec/plan/executor.yaml)")
        if not t["verify"]:
            err(w, "verify: is empty")
        for path in t["edit"]:
            if path.startswith(("contracts/", ".autospec/")):
                err(w, f"may not edit {path}")
        if kind == "test":
            if not t["expect_fail"]:
                err(w, "test task needs expect_fail:")
            impl_id = tid[:-1]
            impl = tasks.get(impl_id)
            if not impl:
                err(w, f"no paired impl task {impl_id}")
            else:
                if tid not in impl["depends_on"]:
                    err(impl["_where"], f"must depend_on its test task {tid}")
                for path in t["edit"]:
                    if path not in impl["locked"]:
                        err(impl["_where"], f"must lock {path} (written by {tid})")
        if kind == "impl":
            for path in t["edit"]:
                if path in test_files:
                    err(w, f"impl task may not edit test file {path}")

        # Files to read must exist now or be written by a task that runs earlier.
        before = anc[tid] if anc else set()
        written_before = {p for d in before for p in tasks[d]["edit"]}
        chars = base_chars + t["_chars"]
        for path in t["read"] + t["locked"]:
            f = root / path
            if f.exists():
                chars += f.stat().st_size
            elif anc is not None and path not in written_before:
                err(w, f"reads {path}, which does not exist and no earlier task writes it")
        if chars // CHARS_PER_TOKEN > max_read:
            err(w, f"required reading ~{chars // CHARS_PER_TOKEN} tokens incl. AGENTS.md + EXECUTOR.md "
                f"(max {max_read}, .autospec/plan/executor.yaml)")

    if anc is None:
        return
    editors = {}
    for tid, t in tasks.items():
        for path in t["edit"]:
            editors.setdefault(path, []).append(tid)
    for path, tids in editors.items():
        for i, a in enumerate(tids):
            for b in tids[i + 1:]:
                if a not in anc[b] and b not in anc[a]:
                    err(".autospec/plan/tasks", f"{a} and {b} both edit {path} but neither depends on the other")


def last_tasks(features, tasks, anc):
    """The one task per feature that every other task of the feature precedes."""
    last = {}
    for fid, f in features.items():
        own = [tid for tid, t in tasks.items() if t.get("feature") == fid]
        if not own:
            err(".autospec/plan/features.yaml", f"{fid} has no tasks")
            continue
        if anc is None:
            continue
        sinks = [t for t in own if not any(t in anc[o] for o in own if o != t)]
        if len(sinks) != 1:
            err(".autospec/plan/features.yaml", f"{fid} has {len(sinks)} final tasks ({', '.join(sinks)}); "
                "add depends_on so exactly one comes last")
            continue
        last[fid] = sinks[0]
    return last


def check_last_tasks(features, tasks, services, last):
    for fid, tid in last.items():
        t = tasks[tid]
        if t.get("kind") != "impl":
            err(t["_where"], f"last task of {fid} must be an impl task")
        svc_path = str((services.get(t.get("service")) or {}).get("path", "")).rstrip("/")
        verify = "\n".join(map(str, t["verify"]))
        for path in features[fid]["acceptance"]:
            if path not in t["locked"]:
                err(t["_where"], f"last task of {fid} must lock acceptance test {path}")
            rel = path[len(svc_path) + 1:] if svc_path and path.startswith(svc_path + "/") else path
            if path not in verify and rel not in verify:
                err(t["_where"], f"last task of {fid} must run acceptance test {path} in verify")


# ---------------------------------------------------------------- report

def done_count(tids, status):
    return f"{sum(status.get(t) == 'done' for t in tids)}/{len(tids)}"


def render(reqs, features, tasks, last, status):
    feature_tasks = {fid: sorted(t for t, v in tasks.items() if v.get("feature") == fid) for fid in features}
    out = [
        "# Traceability",
        "",
        "Generated by `.autospec/kit/scripts/autospec-check.py` from .autospec/plan/SYSTEM.md, .autospec/plan/features.yaml, .autospec/plan/tasks/",
        "and .autospec/state.json. Do not edit by hand; re-run the script.",
        "",
        "## Requirements",
        "",
        "| Req | Requirement | Features | Done |",
        "|---|---|---|---|",
    ]
    for rid, r in reqs.items():
        if r["covered"] == "skeleton":
            out.append(f"| {rid} | {r['text']} | walking skeleton (`baseline_tests`) | – |")
            continue
        fids = [fid for fid, f in features.items() if rid in f["requirements"]]
        tids = sorted({t for fid in fids for t in feature_tasks[fid]})
        out.append(f"| {rid} | {r['text']} | {', '.join(fids) or '**none**'} | {done_count(tids, status)} |")
    out += [
        "",
        "## Features",
        "",
        "| Feature | Title | Acceptance tests | Last task | Tasks | Done |",
        "|---|---|---|---|---|---|",
    ]
    for fid, f in features.items():
        tids = feature_tasks[fid]
        acc = "<br>".join(f"`{p}`" for p in f["acceptance"])
        out.append(f"| {fid} | {f.get('title', '')} | {acc} | {last.get(fid, '**?**')} | "
                   f"{', '.join(tids)} | {done_count(tids, status)} |")
    out += [
        "",
        "## Tasks",
        "",
        "| Task | Kind | Service | Feature | Depends on | Status |",
        "|---|---|---|---|---|---|",
    ]
    for tid, t in tasks.items():
        out.append(f"| {tid} | {t.get('kind')} | {t.get('service')} | {t.get('feature')} | "
                   f"{', '.join(t['depends_on']) or '–'} | {status.get(tid) or 'pending'} |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="repo root (default: current directory)")
    ap.add_argument("--no-write", action="store_true", help="check only, do not write TRACEABILITY.md")
    args = ap.parse_args()
    root = Path(args.root)

    reqs = load_requirements(root)
    executor = load_executor(root)
    services = load_services(root)
    features = load_features(root)
    tasks = load_tasks(root)
    status = load_state(root, tasks)
    anc = ancestors_of(tasks)

    check_services(root, services)
    check_requirements(reqs, features)
    check_features(root, features)
    check_tasks(root, tasks, features, services, anc, executor)
    last = last_tasks(features, tasks, anc)
    check_last_tasks(features, tasks, services, last)

    if not args.no_write:
        (root / ".autospec/plan/TRACEABILITY.md").write_text(render(reqs, features, tasks, last, status))

    for service in sorted(services):
        kinds = [t.get("kind") for t in tasks.values() if t.get("service") == service]
        print(f"{service}: {kinds.count('test')} test / {kinds.count('impl')} impl")
    if anc is not None:
        print("critical path:", " -> ".join(critical_path(tasks)))
    for e in errors:
        print("ERROR", e)
    print(f"PLAN CHECK: {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
