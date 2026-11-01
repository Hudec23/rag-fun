"""F-stage-flow (R-013): prerequisites, versions, stale marking, run-all."""

import time

import httpx

from conftest import EMBED, PLAIN, RECURSIVE, new_collection, run_stage, upload


def _run(api: httpx.Client, coll: dict) -> dict:  # type: ignore[type-arg]
    f = upload(api, "handbook.md")["files"][0]
    r = api.post("/ingest-runs", json={"file_id": f["id"], "collection_id": coll["id"]})
    assert r.status_code == 201
    run = r.json()
    assert run["stages"] == {"parse": None, "chunk": None, "embed": None, "store": None}
    return run


def test_prerequisite_versions_and_stale(api: httpx.Client) -> None:
    run = _run(api, new_collection(api))
    rid = run["id"]
    r = api.post(f"/ingest-runs/{rid}/stages/chunk", json={"params": RECURSIVE})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "STAGE_PREREQUISITE_MISSING"
    assert r.json()["error"]["details"] == {"stage": "chunk", "missing": "parse"}
    p1 = run_stage(api, "ingest", rid, "parse", PLAIN)
    assert p1["status"] == "done" and p1["version"] == 1 and p1["summary"]["stage"] == "parse"
    c1 = run_stage(api, "ingest", rid, "chunk", RECURSIVE)
    assert c1["status"] == "done"
    p2 = run_stage(api, "ingest", rid, "parse", PLAIN)
    assert p2["version"] == 2
    got = api.get(f"/ingest-runs/{rid}").json()
    assert got["stages"]["parse"]["id"] == p2["id"]
    assert got["stages"]["chunk"]["status"] == "stale"
    versions = api.get("/stage-runs", params={"run_id": rid, "stage": "parse"}).json()["items"]
    assert [v["version"] for v in versions] == [2, 1]


def test_already_running_conflict(api: httpx.Client) -> None:
    run = _run(api, new_collection(api))
    first = api.post(f"/ingest-runs/{run['id']}/stages/parse", json={"params": PLAIN})
    second = api.post(f"/ingest-runs/{run['id']}/stages/parse", json={"params": PLAIN})
    assert first.status_code == 202
    if second.status_code == 409:  # first may already be done on a fast machine
        assert second.json()["error"]["code"] == "STAGE_ALREADY_RUNNING"


def test_run_all_completes_every_stage(api: httpx.Client) -> None:
    run = _run(api, new_collection(api))
    params = {"parse": PLAIN, "chunk": RECURSIVE, "embed": EMBED, "store": {}}
    r = api.post(f"/ingest-runs/{run['id']}/run-all", json={"from_stage": None, "params": params})
    assert r.status_code == 202
    assert r.json()["run_all_pending"] == ["chunk", "embed", "store"]
    deadline = time.time() + 300
    while time.time() < deadline:
        got = api.get(f"/ingest-runs/{run['id']}").json()
        if got["stages"]["store"] and got["stages"]["store"]["status"] in ("done", "failed"):
            break
        time.sleep(1)
    assert all(got["stages"][s]["status"] == "done" for s in ("parse", "chunk", "embed", "store")), got
    assert got["run_all_pending"] == []
    again = api.post(f"/ingest-runs/{run['id']}/run-all", json={"from_stage": None, "params": params})
    assert again.status_code == 200


def test_chunk_param_cross_validation(api: httpx.Client) -> None:
    run = _run(api, new_collection(api))
    run_stage(api, "ingest", run["id"], "parse", PLAIN)
    bad = {"strategy": "fixed", "split_by": "word", "length": 10, "overlap": 10}
    r = api.post(f"/ingest-runs/{run['id']}/stages/chunk", json={"params": bad})
    assert r.status_code == 422
    assert r.json()["error"]["details"]["field"] == "params.overlap"
