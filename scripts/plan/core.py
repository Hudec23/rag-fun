"""Planner tool: turn compact unit specs into plan/tasks/*.md, plan/features.yaml, .autospec/state.json."""
import ast, json, re, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SVC = {
    "api": ("services/api", "api-dev", "py"),
    "worker": ("services/worker", "worker-dev", "py"),
    "web": ("services/web", "web-dev", "ts"),
}
DEV = "docker compose -f docker-compose.dev.yml run --rm"
E2E_UP = "docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait"
E2E_RUN = "docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q"
EXAMPLES = {
    "api": ["services/api/src/rag_api/services/collections.py", "services/api/tests/integration/test_collections_get.py"],
    "worker": ["services/worker/src/rag_worker/components/chunk_annotator.py", "services/worker/tests/unit/test_chunk_annotator.py"],
    "web": ["services/web/src/pages/CollectionsPage.tsx", "services/web/tests/pages/CollectionsPage.test.tsx"],
}
FIXTURE_NOTES = {
    "api": "Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.",
    "worker": "Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').",
    "web": "Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid=\"plot\" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.",
}

def py_src(path: str, names: list[str]) -> str:
    """Exact source of top-level defs/classes (stubs) for the Context section."""
    p = ROOT / path
    tree = ast.parse(p.read_text())
    lines = p.read_text().splitlines()
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in names:
            start = (node.decorator_list[0].lineno if node.decorator_list else node.lineno) - 1
            out.append("\n".join(lines[start:node.end_lineno]))
    missing = set(names) - {n.name for n in tree.body if hasattr(n, "name")}
    assert not missing, (path, missing)
    return "\n\n".join(out)

def py_header(path: str) -> str:
    """Imports + module docstring + constants (everything that is not a def/class)."""
    p = ROOT / path
    tree = ast.parse(p.read_text())
    lines = p.read_text().splitlines()
    keep = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            keep.append("\n".join(lines[node.lineno - 1 : node.end_lineno]))
    return "\n".join(keep)

def ts_src(path: str) -> str:
    return (ROOT / path).read_text().strip()

def rel(svc: str, path: str) -> str:
    base = ("tests/e2e" if svc == "integration" else SVC[svc][0]) + "/"
    return path[len(base):] if path.startswith(base) else path

TASKS: dict[str, dict] = {}
FEATURES: dict[str, dict] = {}

def feature(fid, title, reqs, contracts, acceptance):
    FEATURES[fid] = {"id": fid, "title": title, "requirements": reqs, "contracts": contracts, "acceptance": acceptance}

def verify_test(svc, files):
    _, dev, lang = SVC[svc]
    r = " ".join(rel(svc, f) for f in files)
    if lang == "py":
        return [f"{DEV} {dev} sh -c 'uv run --frozen ruff format --check {r} && uv run --frozen ruff check {r} && uv run --frozen pytest -q --collect-only {r}'"], \
               [f"{DEV} {dev} uv run --frozen pytest -q {r}"]
    return [f"{DEV} {dev} sh -c 'npx tsc -b && npx prettier --check {r} && npx eslint {r} && npx vitest list {r}'"], \
           [f"{DEV} {dev} npx vitest run {r}"]

def verify_impl(svc, tests, edit):
    _, dev, lang = SVC[svc]
    r = " ".join(rel(svc, f) for f in tests)
    e = " ".join(rel(svc, f) for f in edit)
    if lang == "py":
        return [f"{DEV} {dev} sh -c 'uv run --frozen ruff format --check {e} && uv run --frozen ruff check {e} && uv run --frozen mypy src'",
                f"{DEV} {dev} uv run --frozen pytest -q {r}"]
    return [f"{DEV} {dev} sh -c 'npx tsc -b && npx prettier --check {e} && npx eslint {e}'",
            f"{DEV} {dev} npx vitest run {r}"]

def unit(svc, num, feat, title, src, test, context, cases, steps=None, deps=(), tdeps=(), read=(), tread=(),
         dont=(), extra_edit=(), notest=False, accept=(), e2e=()):
    """One test+impl pair. src = edit file(s) of the impl; test = new test file; context = markdown."""
    tid = f"T-{svc}-{num:03d}"
    src = [src] if isinstance(src, str) else list(src)
    edit = src + list(extra_edit)
    lang = SVC[svc][2]
    ex_src, ex_test = EXAMPLES[svc]
    if not notest:
        vt, ef = verify_test(svc, [test])
        TASKS[tid + "t"] = dict(id=tid + "t", kind="test", feature=feat, title=f"Write tests: {title}", service=svc,
            depends_on=list(tdeps), edit=[test], read=[ex_test] + list(tread), verify=vt, expect_fail=ef,
            body=dict(goal=f"Write unit tests for: {title}. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task {tid} implements it.",
                      context=context + "\n\n" + FIXTURE_NOTES[svc], cases=cases, src=src))
    tests = ([] if notest else [test]) + list(accept)
    vi = verify_impl(svc, tests, edit)
    if e2e:
        vi.append(f"{E2E_UP} && {E2E_RUN} {' '.join('/workspace/' + p for p in e2e)}")
    TASKS[tid] = dict(id=tid, kind="impl", feature=feat, title=title, service=svc,
        depends_on=([] if notest else [tid + "t"]) + list(deps), edit=edit, read=[ex_src] + list(read),
        locked=tests + list(e2e), verify=vi,
        body=dict(goal=f"Implement: {title}." + ("" if notest else f" The tests written by {tid}t define done."),
                  context=context, steps=steps, dont=list(dont), src=src))
    return tid

def py_ctx(path, names, intro="", header=True):
    h = py_header(path) if header else ""
    code = (h + "\n\n\n" if h.strip() else "") + py_src(path, names)
    return (intro + "\n\n" if intro else "") + f"Stub in `{path}` (signatures are final; replace only the bodies that raise NotImplementedError):\n```python\n{code}\n```"

def ts_ctx(path, intro=""):
    return (intro + "\n\n" if intro else "") + f"Stub `{path}` (signature and props are final):\n```tsx\n{ts_src(path)}\n```"

PY_DONT = ["Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.",
           "Do not add dependencies or change signatures of existing functions/classes.",
           "Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes."]
TS_DONT = ["Do not edit any test file, src/api/schema.d.ts, package.json or package-lock.json.",
           "Do not add dependencies; Tailwind classes only for styling.",
           "Do not change exported names or props."]

def render(t):
    fm = {k: t[k] for k in ("id", "kind", "feature", "title", "service", "depends_on", "edit", "read") if k in t}
    if t["kind"] == "impl":
        fm["locked"] = t["locked"]
    fm["verify"] = t["verify"]
    if t["kind"] == "test":
        fm["expect_fail"] = t["expect_fail"]
    fm["max_attempts"] = 3
    import yaml
    head = yaml.safe_dump(fm, sort_keys=False, width=10000, allow_unicode=True)
    b = t["body"]; lang = SVC[t["service"]][2] if t["service"] in SVC else "py"
    dont = PY_DONT if lang == "py" else TS_DONT
    parts = [f"## Goal\n{b['goal']}", f"## Context\n{b['context']}"]
    if t["kind"] == "test":
        cases = "\n".join(f"{i}. {c}" for i, c in enumerate(b["cases"], 1))
        style = "Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts)." if lang == "py" else "Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text)."
        parts.append(f"## Test cases\nOne test per case, named after the case. {style}\n{cases}")
        parts.append("## Do not\n- Do not write implementation code (not even to make a test compile).\n- Do not use skip/xfail/todo, empty tests or always-true assertions.\n- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).")
        parts.append("## Done when\n`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.")
    else:
        steps = b.get("steps") or ["Implement every stub listed in Context exactly as its docstring says.", "Run the verify commands; fix until green."]
        parts.append("## Steps\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1)))
        parts.append("## Do not\n" + "\n".join(f"- {d}" for d in dont + b.get("dont", [])))
        parts.append("## Done when\nAll verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.")
    return f"---\n{head}---\n\n" + "\n\n".join(parts) + "\n"

def finalize():
    # each feature's last task (by spec: flagged via accept/e2e) must depend on every other task of the feature
    import collections
    anc = {}
    def ancestors(tid, seen=None):
        if tid in anc: return anc[tid]
        out = set()
        for d in TASKS[tid]["depends_on"]:
            out |= {d} | ancestors(d)
        anc[tid] = out
        return out
    for fid in FEATURES:
        own = [t for t, v in TASKS.items() if v["feature"] == fid]
        lasts = [t for t in own if TASKS[t]["kind"] == "impl" and set(FEATURES[fid]["acceptance"]) <= set(TASKS[t].get("locked", []))]
        assert len(lasts) == 1, (fid, lasts)
        last = lasts[0]
        anc.clear()
        for t in own:
            if t != last and t not in ancestors(last):
                TASKS[last]["depends_on"].append(t)
                anc.clear()
    # same-file editors must be ordered: add dependency from later (by id order) to earlier
    editors = collections.defaultdict(list)
    for tid in TASKS:
        for p in TASKS[tid]["edit"]:
            editors[p].append(tid)
    for p, tids in editors.items():
        for a, b in zip(tids, tids[1:]):
            anc.clear()
            if a not in ancestors(b) and b not in ancestors(a):
                TASKS[b]["depends_on"].append(a)
    out = ROOT / "plan/tasks"
    out.mkdir(exist_ok=True)
    for f in out.glob("T-*.md"):
        f.unlink()
    for t in TASKS.values():
        (out / f"{t['id']}.md").write_text(render(t))
    import yaml
    fy = "# plan/features.yaml — generated by the planner. Acceptance tests are planner-written and locked\n# in each feature's last task.\n" + yaml.safe_dump({"features": list(FEATURES.values())}, sort_keys=False, width=10000)
    (ROOT / "plan/features.yaml").write_text(fy)
    (ROOT / ".autospec").mkdir(exist_ok=True)
    (ROOT / ".autospec/state.json").write_text(json.dumps({"tasks": {t: {"status": "pending"} for t in TASKS}}, indent=2) + "\n")
    print(len(TASKS), "tasks,", len(FEATURES), "features")
