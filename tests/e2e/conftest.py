"""Acceptance tests against the running stack (MODEL_BACKEND=fake). Each test creates its own
collection/batch with unique names, so tests are independent and can run in any order."""

import json
import os
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

API = os.environ.get("E2E_API_URL", "http://api:8000/api/v1")
FIXTURES = Path(__file__).parent / "fixtures"
CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"


@pytest.fixture(scope="session")
def api() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=API, timeout=60) as c:
        yield c


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def upload(api: httpx.Client, *names: str, tags: str = "", name: str | None = None) -> dict[str, Any]:
    files = [("files", (n, (FIXTURES / n).read_bytes())) for n in names]
    data = {"tags": tags} if tags else {}
    if name:
        data["name"] = name
    r = api.post("/batches", files=files, data=data)
    assert r.status_code == 201, r.text
    return r.json()


def new_collection(api: httpx.Client, dense: str = "all-minilm", sparse: str = "Qdrant/bm25") -> dict[str, Any]:
    r = api.post("/collections", json={"name": unique("c"), "dense_model": dense, "sparse_model": sparse})
    assert r.status_code == 201, r.text
    return r.json()


def wait_stage(api: httpx.Client, stage_run_id: str, timeout: float = 240) -> dict[str, Any]:
    """Poll GET /stage-runs/{id} until done/failed."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        sr = api.get(f"/stage-runs/{stage_run_id}").json()
        if sr["status"] in ("done", "failed"):
            return sr
        time.sleep(0.5)
    raise AssertionError(f"stage run {stage_run_id} not finished after {timeout}s")


def run_stage(api: httpx.Client, kind: str, run_id: str, stage: str, params: dict[str, Any]) -> dict[str, Any]:
    r = api.post(f"/{kind}-runs/{run_id}/stages/{stage}", json={"params": params})
    assert r.status_code == 202, r.text
    return wait_stage(api, r.json()["id"])


def artifact(api: httpx.Client, stage_run: dict[str, Any]) -> Any:
    r = api.get(f"/stage-runs/{stage_run['id']}/artifact")
    assert r.status_code == 200, r.text
    return r.json()


PARSE = {"strategy": "docling_layout", "extract_tables": True, "page_images": True}
PLAIN = {"strategy": "plain_text"}
RECURSIVE = {"strategy": "recursive", "length": 300, "overlap": 30, "separators": ["\n\n", "sentence", "\n", " "]}
EMBED = {"batch_size": 16}


def ingest_file(api: httpx.Client, filename: str, collection: dict[str, Any], *, parse: dict[str, Any] = PLAIN,
                chunk: dict[str, Any] = RECURSIVE, tags: str = "") -> dict[str, Any]:
    """Upload + run parse, chunk, embed, store; returns {'run', 'file', 'stages': {stage: stage_run}}."""
    batch = upload(api, filename, tags=tags)
    f = batch["files"][0]
    run = api.post("/ingest-runs", json={"file_id": f["id"], "collection_id": collection["id"]}).json()
    stages = {}
    for stage, params in (("parse", parse), ("chunk", chunk), ("embed", EMBED), ("store", {})):
        stages[stage] = run_stage(api, "ingest", run["id"], stage, params)
        assert stages[stage]["status"] == "done", stages[stage]
    return {"run": run, "file": f, "batch": batch["batch"], "stages": stages}


def _registry() -> Registry:
    pairs = []
    for p in CONTRACTS.rglob("*.schema.json"):
        doc = json.loads(p.read_text())
        pairs.append((doc["$id"], Resource.from_contents(doc, default_specification=DRAFT202012)))
    return Registry().with_resources(pairs)


def assert_valid(instance: Any, schema_path: str) -> None:
    """Validate against contracts/<schema_path>[#/$defs/X]."""
    path, _, frag = schema_path.partition("#")
    doc = json.loads((CONTRACTS / path).read_text())
    v = Draft202012Validator({"$ref": doc["$id"] + (("#" + frag) if frag else "")}, registry=_registry())
    errs = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in v.iter_errors(instance)]
    assert not errs, errs[:5]


@pytest.fixture(scope="session")
def coll(api: httpx.Client) -> dict[str, Any]:
    """Collection with handbook.md (tag hr) and notes.txt (tag tax) fully ingested — query tests."""
    c = new_collection(api)
    ingest_file(api, "handbook.md", c, tags="hr")
    ingest_file(api, "notes.txt", c, tags="tax")
    return c
